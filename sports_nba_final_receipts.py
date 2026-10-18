"""Replay agreeing NBA/ESPN finals as postgame research observations only."""
from collections import Counter
from pathlib import Path
import hashlib
import json

import sports_expansion_observer as espn
import sports_expansion_audit as audit
import sports_nba_official_schedule_audit as nba
import sports_nba_schedule_receipts as receipts


def classify(official, provider, *, nba_observed_at, espn_observed_at=None,
             espn_observed_by_game=None):
    """No scores or winner affect which independently identified game is joined."""
    nt = espn.utc(nba_observed_at)
    if espn_observed_by_game is not None:
        if (espn_observed_at is not None or not isinstance(espn_observed_by_game, dict)
                or set(espn_observed_by_game) != set(provider)):
            raise ValueError('Exact per-game ESPN observation provenance required')
        observed = {key:espn.utc(value) for key,value in espn_observed_by_game.items()}
    else:
        at = espn.utc(espn_observed_at)
        observed = {key:at for key in provider}
    report = nba.compare(official, provider)
    by_id = {row['nba_game_id']: row for row in official}
    if len(by_id) != len(official):
        raise ValueError('Duplicate official NBA game identity')
    uses = Counter(row['nba_official_game_id'] for row in report['matched'])
    rows = []; pending = list(report['unverified'])
    for matched in report['matched']:
        n = by_id[matched['nba_official_game_id']]
        e = provider[matched['espn_game_id']]
        et = observed[matched['espn_game_id']]
        base = {'league': 'NBA', 'nba_game_id': n['nba_game_id'],
                'espn_game_id': e['espn_game_id'],
                'nba_scheduled_start_utc': n['tipoff_utc'],
                'espn_scheduled_start_utc': e['scheduled_start_utc']}
        reason = None
        tip = espn.utc(n['tipoff_utc'])
        season_year = tip.year if tip.month >= 7 else tip.year - 1
        if uses[n['nba_game_id']] != 1:
            reason = 'NON_BIJECTIVE_GAME_IDENTITY'
        elif int(n['nba_game_id'][3:5]) != season_year % 100:
            reason = 'NBA_GAME_ID_SEASON_MISMATCH'
        elif n['nba_postponed_status'] not in (None, '', 'N'):
            reason = 'POSTPONED_OR_UNKNOWN_NBA_STATUS'
        elif e['season_stage'] != (2 if n['kind'] == 'regular' else 3):
            reason = 'NBA_ESPN_SEASON_STAGE_MISMATCH'
        elif n['nba_status'] != 3 or e['provider_completed'] is not True:
            reason = 'BOTH_SOURCES_NOT_FINAL'
        elif (n['nba_home_score'], n['nba_away_score']) != (e['home_score'], e['away_score']):
            reason = 'CONFLICTING_FINAL_SCORES_NO_GRADE'
        elif min(nt, et) <= max(espn.utc(n['tipoff_utc']), espn.utc(e['scheduled_start_utc'])):
            reason = 'FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START'
        if reason:
            pending.append({**base, 'reason': reason})
            continue
        # Parsers already validate exact integers, but keep the pure classifier
        # fail-closed when used with malformed direct inputs as well.
        scores = (n['nba_home_score'], n['nba_away_score'], e['home_score'], e['away_score'])
        if any(type(value) is not int or value < 0 for value in scores) or scores[0] == scores[1]:
            raise ValueError('Invalid NBA final score')
        rows.append({**base, 'home_tricode': n['home_tricode'], 'away_tricode': n['away_tricode'],
                     'espn_home_team_id': e['home_team_id'], 'espn_away_team_id': e['away_team_id'],
                     'home_score': scores[0], 'away_score': scores[1],
                     'nba_source_observed_at_utc': nt.isoformat(),
                     'espn_source_observed_at_utc': et.isoformat(),
                     'corroboration_available_at_utc': max(nt, et).isoformat(),
                     'source_agreement': 'NBA_AND_ESPN_REPORTED_SAME_FINAL',
                     'result_observation_chronology_verified': True,
                     'pregame_feature_chronology_verified': False})
    return {'schema': 'tyler-nba-final-research-v1', 'two_source_final_agreements': len(rows),
            'corroborated_research_only': rows, 'pending_or_quarantined': len(pending), 'pending': pending,
            'source_scope_complete': False, 'independent_official_final_certification_complete': False,
            'historical_evaluation_enabled': False, 'model_training_enabled': False,
            'forecasting_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def _timestamp(folder, obj, field):
    at = espn.utc(obj[field])
    if at.strftime('%Y%m%dT%H%M%S%fZ') != folder.name:
        raise ValueError('Capture folder differs from immutable timestamp')
    return at


def build(root, stamp):
    root = Path(root)
    receipts.verify(root, stamp)
    folder = root / nba.ROOT / 'captures' / stamp
    raw = (folder / 'manifest.json').read_bytes(); saved = json.loads(raw)
    if saved['nba_official_source_url'] != nba.NBA_URL:
        raise ValueError('Unexpected official NBA source URL')
    if {p.name for p in folder.iterdir()} != {'manifest.json', 'nba_schedule.json.gz'}:
        raise ValueError('Unexpected NBA source archive file')
    nt = _timestamp(folder, saved, 'created_at_utc')
    ef = root / espn.ROOT / 'captures' / saved['espn_capture']
    eraw = (ef / 'manifest.json').read_bytes(); es = json.loads(eraw)
    et = _timestamp(ef, es, 'recorded_at_utc')
    if et > nt:
        raise ValueError('Linked ESPN source was captured after NBA receipt')
    audit.audit_capture(ef / "manifest.json")
    original = audit.bounded_gzip_read((folder / 'nba_schedule.json.gz').read_bytes(), limit=nba.MAX_BYTES)
    result = classify(nba.official_games(original), nba.espn_games(es, ef),
                      nba_observed_at=nt.isoformat(), espn_observed_at=et.isoformat())
    return {**result, 'nba_capture': stamp,
            'nba_manifest_sha256': hashlib.sha256(raw).hexdigest(),
            'nba_response_sha256': saved['nba_raw_sha256'],
            'espn_capture': ef.name, 'espn_manifest_sha256': hashlib.sha256(eraw).hexdigest(),
            'source_archive_sha256_verified': True}


def main():
    files = sorted((nba.ROOT / 'captures').glob('*/manifest.json'))
    if files:
        result = build(Path('.'), files[-1].parent.name)
    else:
        result = {'schema': 'tyler-nba-final-research-unavailable-v1',
                  'reason': 'NO_ARCHIVED_INDEPENDENT_NBA_SOURCE',
                  'source_archive_sha256_verified': False,
                  'two_source_final_agreements': 0,
                  'historical_evaluation_enabled': False, 'model_training_enabled': False,
                  'forecasting_enabled': False, 'promotion_allowed': False,
                  'NO_BET': True, 'actual_wagers': 0}
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
