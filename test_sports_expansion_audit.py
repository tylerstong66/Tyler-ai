"""Saved ESPN observations are reproducible, provenance-linked and no bet."""
import gzip
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import sports_expansion_audit as audit
import sports_expansion_observer as obs


def fake_event(id_):
    return {
        "id":str(id_), "date":"2026-10-20T19:00:00Z",
        "season":{"type":2},
        "status":{"type":{"state":"pre","completed":False}},
        "competitions":[{"neutralSite":False,"competitors":[
            {"homeAway":"home","team":{"id":"1","displayName":"Home"}},
            {"homeAway":"away","team":{"id":"2","displayName":"Away"}}]}],
    }


class SourceArchiveAuditTests(unittest.TestCase):
    now=datetime(2026,10,17,14,0,tzinfo=timezone.utc)

    def build(self,root):
        def fetch(url):
            return json.dumps({"count":1,"events":[fake_event(123)]}).encode()
        obs.capture(fetch,now=self.now,base=root,days_ahead=0)
        path=root/obs.ROOT/"captures"/"20261017T140000000000Z"
        return path

    def test_complete_source_replay_finds_two_separate_leagues(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.build(root)
            result=audit.audit(root)
            self.assertEqual(result["captures_verified"],1)
            self.assertEqual(result["source_responses_verified"],2)
            self.assertEqual(result["cohort_source_coverage"]["NCAAF_FBS"]["snapshot_days"],1)
            self.assertEqual(result["cohort_source_coverage"]["NBA"]["snapshot_days"],1)
            self.assertEqual(result["cohort_source_coverage"]["NCAAM_D1"]["snapshot_days"],0)
            self.assertEqual(result["total_provider_conflicts_in_captures"],0)
            self.assertTrue(result["not_yet_eligible_for_prediction"])
            self.assertTrue(result["no_official_independent_final_claim"])
            self.assertTrue(result["NO_BET"])

    def test_duplicate_manifest_keys_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            capture=self.build(root)
            path=capture/"manifest.json"
            raw=path.read_text()
            path.write_text('{"NO_BET":false,' + raw.lstrip()[1:])
            with self.assertRaises(ValueError):
                audit.audit_capture(path)

    def test_duplicate_original_json_keys_fail_closed_even_with_updated_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            capture=self.build(root)
            path=capture/"manifest.json"
            manifest=json.loads(path.read_text())
            snap=manifest["snapshots"][0]
            blob=capture/snap["compressed_file"]
            raw=gzip.decompress(blob.read_bytes())
            altered=raw.replace(b'"count": 1', b'"count": 999, "count": 1', 1)
            self.assertNotEqual(altered,raw)
            blob.write_bytes(gzip.compress(altered))
            snap["original_response_sha256"]=hashlib.sha256(altered).hexdigest()
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                audit.audit_capture(path)

    def test_original_raw_source_tampering_fails_integrity(self):
        for variation in ("compressed_response","normalized_snapshot","quarantine",
                          "no_bet_flag","untracked_file","receipt_sha"):
            with self.subTest(variation=variation),tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                capture=self.build(root)
                path=capture/"manifest.json"
                data=json.loads(path.read_text())
                if variation=="compressed_response":
                    target=capture/"NBA_2026-10-17.json.gz"
                    raw=gzip.decompress(target.read_bytes())
                    target.write_bytes(gzip.compress(raw+b" ",mtime=0))
                elif variation=="normalized_snapshot":
                    data["snapshots"][0]["parsed"]["games"][0]["home_team_id"]="999"
                elif variation=="quarantine":
                    data["quarantined_provider_games"].append({"fake":"conflict"})
                elif variation=="no_bet_flag":
                    data["forecasting_enabled"]=True
                elif variation=="untracked_file":
                    (capture/"scratch.txt").write_text("not expected")
                elif variation=="receipt_sha":
                    data["snapshots"][0]["original_response_sha256"]="0"*64
                if variation not in ("compressed_response","untracked_file"):
                    path.write_text(json.dumps(data))
                with self.assertRaises((ValueError,KeyError)):
                    audit.audit(root)

    def test_reject_forged_wager_type_or_enabled_league_roster(self):
        for field, value in (
            ("actual_wagers", False),
            ("actual_wagers", 0.0),
            ("enabled_leagues", ["NBA"]),
            ("enabled_leagues", list(reversed(obs.LEAGUES))),
        ):
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                capture = self.build(root)
                path = capture / "manifest.json"
                saved = json.loads(path.read_text())
                saved[field] = value
                path.write_text(json.dumps(saved))
                with self.assertRaisesRegex(ValueError, "safety or immutable protocol"):
                    audit.audit_capture(path)

    def test_time_and_url_mismatches_fail_closed(self):
        for fault in ("day","url","time","name","file"):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);capture=self.build(root)
                path=capture/"manifest.json"
                data=json.loads(path.read_text())
                if fault=="day":
                    data["snapshots"][0]["day"]="2026-10-18"
                elif fault=="url":
                    data["snapshots"][0]["url"]="https://other.example/scoreboard"
                elif fault=="time":
                    data["recorded_at_utc"]="2026-10-17T14:00:01+00:00"
                elif fault=="name":
                    data["snapshots"][0]["compressed_file"]="renamed.json.gz"
                elif fault=="file":
                    (capture/data["snapshots"][0]["compressed_file"]).unlink()
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):
                    audit.audit(root)

    def test_bounded_gzip_rejects_expansion_bomb_and_truncation(self):
        oversized = gzip.compress(b'x' * 8_000_001, mtime=0)
        with self.assertRaisesRegex(ValueError, 'exceeds maximum'):
            audit.bounded_gzip_read(oversized)
        valid = gzip.compress(b'valid', mtime=0)
        self.assertEqual(audit.bounded_gzip_read(valid), b'valid')
        with self.assertRaisesRegex(ValueError, 'Corrupt or incomplete'):
            audit.bounded_gzip_read(valid[:-5])

    def test_expansion_bomb_in_capture_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            capture = self.build(root)
            target = capture / 'NBA_2026-10-17.json.gz'
            target.write_bytes(gzip.compress(b'x' * 8_000_001, mtime=0))
            with self.assertRaisesRegex(ValueError, 'exceeds maximum'):
                audit.audit(root)

    def test_no_existing_captures_does_not_claim_completeness(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,"Missing or unexpectedly many"):
                audit.audit(Path(directory))

    def test_symlinked_capture_components_and_files_rejected(self):
        for target_kind in ('root', 'captures', 'capture', 'manifest', 'blob'):
            with self.subTest(target=target_kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); capture = self.build(root)
                target = {'root': root/obs.ROOT, 'captures': capture.parent,
                          'capture': capture, 'manifest': capture/'manifest.json',
                          'blob': capture/'NBA_2026-10-17.json.gz'}[target_kind]
                outside = root/'relocated'; target.rename(outside)
                target.symlink_to(outside, target_is_directory=outside.is_dir())
                with self.assertRaisesRegex(ValueError, 'Symlink'):
                    audit.audit_capture(capture/'manifest.json')
                with self.assertRaisesRegex(ValueError, 'Symlink'):
                    audit.audit(root)


if __name__=="__main__":
    unittest.main()
