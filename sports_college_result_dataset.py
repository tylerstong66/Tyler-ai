"""Deduplicate replayed college result observations without modeling authority."""
from collections import defaultdict
from pathlib import Path
import json
import hashlib

import sports_college_final_receipts as receipts
import sports_expansion_observer as espn
import sports_ncaa_espn_identity as identity

IDENTITY_FIELDS = (
    'ncaa_game_id', 'scheduled_start_utc', 'ncaa_scheduled_start_utc',
    'ncaa_home_school', 'ncaa_away_school', 'espn_home_team_id', 'espn_away_team_id',
    'home_score', 'away_score',
)
CONFLICT_REASONS = frozenset((
    'CONFLICTING_FINAL_SCORES_NO_GRADE', 'NON_BIJECTIVE_GAME_IDENTITY',
    'MULTIPLE_NCAA_IDENTITIES', 'NCAA_START_CHANGED',
    'FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START',
))


def assemble(root, stamps):
    """Replay explicit captures; repeated games never increase result counts."""
    if not isinstance(stamps, list) or not stamps or len(stamps) != len(set(stamps)):
        raise ValueError('Expected nonempty unique capture identifiers')
    reports = []
    rejected = []
    for stamp in sorted(stamps):
        try:
            reports.append(receipts.build(root, stamp))
        except ValueError as exc:
            # Old crosswalks predate the current curated alias policy. Preserve
            # them unchanged and expose incompatible reports; never reinterpret
            # a saved report or include its labels under a different policy.
            if str(exc) != 'Saved college identity crosswalk differs from replay':
                raise
            raw = (Path(root) / identity.ROOT / 'captures' / stamp / 'manifest.json').read_bytes()
            rejected.append({'capture': stamp,
                             'crosswalk_manifest_sha256': hashlib.sha256(raw).hexdigest(),
                             'reason': 'SAVED_CROSSWALK_NOT_REPRODUCIBLE_UNDER_CURRENT_POLICY',
                             'included_in_result_dataset': False})
    observations = defaultdict(list)
    conflicts = defaultdict(set)
    official_ids = defaultdict(set)
    evidence = []
    nonfinal_observations = defaultdict(list)
    for report in reports:
        ref = {'capture': report['crosswalk_capture'],
               'crosswalk_manifest_sha256': report['crosswalk_manifest_sha256'],
               'ncaa_manifest_sha256': report['ncaa_manifest_sha256'],
               'espn_manifest_sha256': report['espn_manifest_sha256']}
        evidence.append(ref)
        for row in report['corroborated_research_only']:
            key = (row['league'], row['espn_game_id'])
            observations[key].append((row, ref))
            official_ids[(row['league'], row['ncaa_game_id'])].add(key)
        for row in report['pending']:
            if row['reason'] == 'BOTH_SOURCES_NOT_FINAL':
                nonfinal_observations[(row['league'], row['espn_game_id'])].append(
                    espn.utc(report['source_pair_observed_at_utc']))
            if row['reason'] in CONFLICT_REASONS:
                conflicts[(row['league'], row['espn_game_id'])].add(row['reason'])
    for keys in official_ids.values():
        if len(keys) > 1:
            for key in keys:
                conflicts[key].add('NCAA_ID_REUSED_ACROSS_CAPTURES')
    rows = []
    quarantined = []
    for key, found in sorted(observations.items()):
        first = found[0][0]
        if any(any(row[field] != first[field] for field in IDENTITY_FIELDS)
               for row, _ in found[1:]):
            conflicts[key].add('RESULT_OR_IDENTITY_CHANGED_ACROSS_CAPTURES')
        first_final = min(espn.utc(row['corroboration_available_at_utc']) for row, _ in found)
        if any(at > first_final for at in nonfinal_observations[key]):
            conflicts[key].add('SOURCE_REVERTED_TO_NONFINAL_AFTER_AGREEMENT')
        if conflicts[key]:
            continue
        earliest = min((row for row, _ in found),
                       key=lambda row: espn.utc(row['corroboration_available_at_utc']))
        rows.append({**earliest, 'verified_capture_observations': len(found),
                     'source_receipts': [ref for _, ref in found]})
    for (league, game_id), reasons in sorted(conflicts.items()):
        if reasons:
            quarantined.append({'league': league, 'espn_game_id': game_id,
                                'reasons': sorted(reasons)})
    return {
        'schema': 'tyler-college-result-observation-dataset-v1',
        'captures_examined': len(stamps), 'captures_replayed': len(reports),
        'captures_rejected': len(rejected), 'rejected_capture_receipts': rejected,
        'capture_receipts': evidence,
        'unique_corroborated_games': len(rows), 'rows': rows,
        'quarantined_games': len(quarantined), 'quarantined': quarantined,
        'pending_capture_observations': sum(r['pending_or_quarantined'] for r in reports),
        'source_scope_complete': False, 'historical_evaluation_enabled': False,
        'model_training_enabled': False, 'forecasting_enabled': False,
        'independent_official_final_certification_complete': False,
        'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0,
    }


def main():
    files = sorted((identity.ROOT / 'captures').glob('*/manifest.json'))
    report = assemble(Path('.'), [file.parent.name for file in files])
    # CI/collection can retain this read-only report as an artifact. No model,
    # historical prediction, source receipt, or prior dataset is modified here.
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
