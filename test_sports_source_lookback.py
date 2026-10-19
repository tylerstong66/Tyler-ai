from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
import tempfile
import unittest

import sports_source_collection_window as window
import sports_expansion_observer as provider
import sports_expansion_audit as provider_audit
import sports_ncaa_official_source as ncaa
import sports_ncaa_owned_receipts as ncaa_receipts
import sports_ncaa_espn_identity as identity
import sports_college_final_receipts as finals
import test_sports_ncaa_espn_identity as fixtures

NOW = datetime(2026, 10, 18, 5, 10, tzinfo=timezone.utc)


def fetch_provider(url):
    events = [fixtures.espn_game(completed=True)] if 'football/college-football' in url and 'dates=20261017' in url else []
    return json.dumps({'count': len(events), 'events': events}).encode()


def fetch_ncaa(url):
    return json.dumps({'data': {'contests': [fixtures.official_game(final=True)]}}).encode()


class SourceLookbackTests(unittest.TestCase):
    def test_prior_evening_final_is_retained_after_utc_rollover_and_not_backfilled_as_forecast(self):
        for back, agreements in ((0, 0), (2, 1)):
            with self.subTest(back=back), tempfile.TemporaryDirectory() as td:
                base = Path(td)
                ncaa.run(fetch_ncaa, base=base, now=NOW, days_ahead=0, days_back=back)
                manifest = provider.capture(fetch_provider, base=base, now=NOW, days_ahead=0, days_back=back)
                crosswalk = identity.run(base=base, now=NOW+timedelta(minutes=1))
                stamp = (NOW+timedelta(minutes=1)).strftime('%Y%m%dT%H%M%S%fZ')
                result = finals.build(base, stamp)
                self.assertEqual(result['two_source_final_agreements'], agreements)
                self.assertFalse(result['forecasting_enabled']); self.assertFalse(result['historical_evaluation_enabled'])
                self.assertTrue(result['NO_BET']); self.assertEqual(result['actual_wagers'], 0)
                self.assertFalse((base/'benchmarks/fbs_pregame_reference_features_v1/records').exists())
                if back:
                    self.assertEqual(manifest['collection_window']['anchor_utc_date'], '2026-10-18')
                    self.assertFalse(manifest['collection_window']['pregame_feature_backfill_allowed'])
                    self.assertEqual(result['corroborated_research_only'][0]['corroboration_available_at_utc'], NOW.isoformat())

    def test_default_and_explicit_zero_keep_identical_legacy_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as one, tempfile.TemporaryDirectory() as two:
            for module, fetch in ((provider, fetch_provider), (ncaa, fetch_ncaa)):
                a = module.capture(fetch, base=Path(one), now=NOW, days_ahead=0) if module is provider else module.run(fetch, base=Path(one), now=NOW, days_ahead=0)
                b = module.capture(fetch, base=Path(two), now=NOW, days_ahead=0, days_back=0) if module is provider else module.run(fetch, base=Path(two), now=NOW, days_ahead=0, days_back=0)
                self.assertEqual(provider.canonical(a), provider.canonical(b))
                self.assertNotIn('collection_window', a)

    def test_lookback_requests_are_utc_anchored_even_with_non_utc_clock(self):
        now = datetime(2026, 11, 1, 0, 30, tzinfo=timezone(timedelta(hours=5)))
        with tempfile.TemporaryDirectory() as td:
            manifest = provider.capture(lambda _: b'{"count":0,"events":[]}', base=Path(td), now=now, days_ahead=0, days_back=1)
            self.assertEqual(manifest['collection_window']['anchor_utc_date'], '2026-10-31')
            self.assertEqual({s['day'] for s in manifest['snapshots']}, {'2026-10-30', '2026-10-31'})
            path = next((Path(td)/provider.ROOT/'captures').glob('*/manifest.json'))
            provider_audit.audit_capture(path)

    def test_college_hoops_lookback_clips_to_declared_season_and_fbs_end_is_included(self):
        requested = ncaa.requested_windows(date(2026, 10, 31), days_ahead=1, days_back=3)
        dates = {day for league, day, _ in requested if league == 'NCAAM_D1'}
        self.assertEqual(dates, {'2026-10-30', '2026-10-31', '2026-11-01'})
        self.assertFalse(any(league == 'NCAAF_FBS' for league, _, _ in ncaa.requested_windows(date(2027, 2, 1), days_ahead=0)))
        self.assertTrue(any(league == 'NCAAF_FBS' for league, _, _ in ncaa.requested_windows(date(2027, 2, 1), days_ahead=0, days_back=2)))

    def test_invalid_or_boolean_bounds_fail_before_any_fetch(self):
        for back, ahead in ((-1, 0), (4, 0), (True, 0), (1, True), (1, 8)):
            with self.subTest(back=back, ahead=ahead), tempfile.TemporaryDirectory() as td:
                def fail(_): self.fail('Invalid horizon fetched source data')
                with self.assertRaises(ValueError): provider.capture(fail, base=Path(td), now=NOW, days_ahead=ahead, days_back=back)
                with self.assertRaises(ValueError): ncaa.run(fail, base=Path(td), now=NOW, days_ahead=ahead, days_back=back)

    def test_cross_day_conflicting_score_remains_quarantined(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            def fetch(url):
                rows = []
                if 'football/college-football' in url:
                    if 'dates=20261017' in url: rows = [fixtures.espn_game(completed=True)]
                    elif 'dates=20261018' in url:
                        event = fixtures.espn_game(completed=True)
                        event['competitions'][0]['competitors'][0]['score'] = '31'; rows = [event]
                return json.dumps({'count': len(rows), 'events': rows}).encode()
            saved = provider.capture(fetch, base=base, now=NOW, days_ahead=0, days_back=2)
            self.assertEqual(len(saved['quarantined_provider_games']), 1)
            self.assertFalse(any(r['league'] == 'NCAAF_FBS' for r in saved['undisputed_provider_games']))
            path = next((base/provider.ROOT/'captures').glob('*/manifest.json')); provider_audit.audit_capture(path)

    def test_changed_or_missing_declared_provider_day_cannot_claim_complete_request_window(self):
        for kind in ('metadata', 'missing_day'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); saved = provider.capture(fetch_provider, base=base, now=NOW, days_ahead=0, days_back=2)
                path = next((base/provider.ROOT/'captures').glob('*/manifest.json'))
                if kind == 'metadata': saved['collection_window']['days_back'] = 1
                else:
                    snap = saved['snapshots'].pop(0); (path.parent/snap['compressed_file']).unlink()
                    saved['undisputed_provider_games'], saved['quarantined_provider_games'] = provider.reconcile(saved['snapshots'])
                path.write_bytes(provider.canonical(saved))
                with self.assertRaisesRegex(ValueError, 'declared bounded source dates'): provider_audit.audit_capture(path)

    def test_ncaa_policy_metadata_and_original_request_urls_are_replayed(self):
        for kind in ('days', 'url'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td); saved = ncaa.run(fetch_ncaa, base=base, now=NOW, days_ahead=0, days_back=2)
                folder = next((base/ncaa.ROOT/'captures').iterdir()); ncaa_receipts.verify(folder)
                if kind == 'days': saved['collection_window']['days_ahead'] = 1
                else: saved['snapshots'][0]['source_url'] += '&unverified=1'
                (folder/'manifest.json').write_bytes(provider.canonical(saved))
                # Football week candidates can be identical for adjacent day bounds;
                # use a changed request URL when the day change leaves the same set.
                if kind == 'days':
                    saved['collection_window']['anchor_utc_date'] = '2026-10-17'
                    (folder/'manifest.json').write_bytes(provider.canonical(saved))
                with self.assertRaises(ValueError): ncaa_receipts.verify(folder)

    def test_window_flags_and_types_cannot_be_reinterpreted(self):
        original = window.policy(NOW, 3, 2)
        for key, value in [('days_back', True), ('days_ahead', False), ('anchor_utc_date', '2026-10-17'),
                ('source_observations_only', 1), ('pregame_feature_backfill_allowed', 0), ('extra', True)]:
            with self.subTest(key=key):
                changed = dict(original); changed[key] = value
                with self.assertRaises(ValueError): window.verify(changed, NOW)

    def test_lookback_stage_venue_and_display_name_changes_do_not_use_first_row(self):
        for kind in ('stage', 'venue', 'name'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                base = Path(td)
                def fetch(url):
                    rows = []
                    if 'football/college-football' in url and ('dates=20261017' in url or 'dates=20261018' in url):
                        event = fixtures.espn_game(completed=True)
                        if 'dates=20261018' in url:
                            if kind == 'stage': event['season']['type'] = 3
                            elif kind == 'venue': event['competitions'][0]['neutralSite'] = True
                            else: event['competitions'][0]['competitors'][0]['team']['displayName'] = 'Changed Display Name'
                        rows = [event]
                    return json.dumps({'count': len(rows), 'events': rows}).encode()
                saved = provider.capture(fetch, base=base, now=NOW, days_ahead=0, days_back=2)
                self.assertEqual(len(saved['quarantined_provider_games']), 1)
                path = next((base/provider.ROOT/'captures').glob('*/manifest.json'))
                provider_audit.audit_capture(path)
                self.assertEqual(identity.verify_espn(path.parent,saved), [])

    def test_lookback_reconciliation_policy_cannot_be_removed_or_changed(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); saved=provider.capture(fetch_provider,base=base,now=NOW,days_ahead=0,days_back=2)
            path=next((base/provider.ROOT/'captures').glob('*/manifest.json'))
            saved['source_reconciliation_policy']='TAKE_FIRST_ROW'
            path.write_bytes(provider.canonical(saved))
            with self.assertRaisesRegex(ValueError,'reconciliation policy'): provider_audit.audit_capture(path)


if __name__ == '__main__': unittest.main()
