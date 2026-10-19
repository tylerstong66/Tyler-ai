"""Join verified 2024/2025 FBS source archives under strict historical identity."""
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import sports_ncaa_historical_owned as owned
import sports_expansion_historical_capture as history
import sports_historical_identity_audit as historical_audit
import sports_expansion_observer as espn
import sports_ncaa_espn_identity as identity
import sports_college_dual_source_finals as finals
from sports_expansion_audit import bounded_gzip_read


def _owned_sources(base, league, split, now):
    if league == 'NCAAF_FBS':
        for week in owned.WEEKS:
            saved = owned.verify(base, split, week, now=now)
            if saved is not None:
                yield saved, base/owned.ROOT/split/f'week-{week:02d}.receipt.json', {'week': week}
    else:
        import sports_ncaa_d1_historical_owned as d1
        for day in d1.DATES[split]:
            saved = d1.verify(base, split, day, now=now)
            if saved is not None:
                yield saved, base/d1.ROOT/split/(day+'.receipt.json'), {'source_date': day}


def build(base=Path('.'), *, split='train', now=None, league='NCAAF_FBS', verified_school_aliases=False):
    if league not in ('NCAAF_FBS', 'NCAAM_D1'):
        raise ValueError('Unsupported historical independent-source league')
    if split not in owned.YEARS:
        raise ValueError('Unsupported historical FBS source split')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware crosscheck clock required')
    base = Path(base)
    audit = historical_audit.audit(base, now=now)
    excluded_provider_ids = {row['game_id'] for row in audit['quarantined']
                             if row['league'] == league}
    official = defaultdict(list); nrefs = defaultdict(list); source_quarantines = []
    for saved, path, period in _owned_sources(base, league, split, now):
        ref = {**period, 'receipt_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
               'response_sha256': saved['original_response_sha256'],
               'observed_at_utc': saved['recorded_at_utc']}
        source_quarantines.extend({**row, 'league':league, 'source_receipt':ref}
                                  for row in saved.get('quarantined_ncaa_contests',[]))
        for row in saved['parsed_ncaa_games']:
            official[row['ncaa_game_id']].append({'league': league, **row})
            nrefs[row['ncaa_game_id']].append(ref)
    ncaa_conflicts = {game_id for game_id, rows in official.items()
                      if any(row != rows[0] for row in rows[1:])}
    quarantined_ncaa_ids = {row['ncaa_game_id'] for row in source_quarantines}
    ncaa_rows = [rows[0] for game_id, rows in sorted(official.items())
                 if game_id not in ncaa_conflicts and game_id not in quarantined_ncaa_ids]
    provider = defaultdict(list); erefs = defaultdict(list)
    for day in history.dates_by_league()[league][split]:
        if not history.verify_existing(base, league, split, day, as_of=now):
            continue
        folder = base / history.ROOT / 'sources' / league / split
        path = folder / (day + '.receipt.json'); raw_receipt = path.read_bytes()
        saved = json.loads(raw_receipt)
        raw = bounded_gzip_read((folder / (day + '.json.gz')).read_bytes())
        if hashlib.sha256(raw).hexdigest() != saved['original_response_sha256']:
            raise ValueError('ESPN historical response changed during crosscheck')
        events = {str(row['id']): row for row in json.loads(raw)['events']}
        ref = {'source_date': day, 'receipt_sha256': hashlib.sha256(raw_receipt).hexdigest(),
               'response_sha256': saved['original_response_sha256'],
               'observed_at_utc': saved['recorded_at_utc']}
        for row in saved['parsed_provider_scoreboard']['games']:
            game_id = row['game_id']
            if game_id in excluded_provider_ids:
                continue
            names = {}
            for team in events[game_id]['competitions'][0]['competitors']:
                school = team['team'].get('location')
                names[team['homeAway']] = identity.name(school) if school else None
            if set(names) != {'home', 'away'}:
                raise ValueError('Missing historical ESPN school identity')
            provider[game_id].append({**row, 'league': league,
                                      'espn_game_id': game_id, 'school_names': names})
            erefs[game_id].append(ref)
    provider_conflicts = {game_id for game_id, rows in provider.items()
                          if any(row != rows[0] for row in rows[1:])}
    espn_rows = [rows[0] for game_id, rows in sorted(provider.items()) if game_id not in provider_conflicts]
    policy = None
    if verified_school_aliases:
        if league=='NCAAF_FBS':
            import sports_historical_school_identities as schools
        else:
            import sports_historical_d1_school_identities as schools
        policy = schools.load(base,league=league,split=split,now=now)
        ncaa_rows = [{**row, **{side+'_name':policy['aliases'].get(
                         identity.name(row[side+'_name']),row[side+'_name'])
                         for side in ('home','away')}} for row in ncaa_rows]
    report = finals.classify(ncaa_rows, espn_rows, use_curated_fbs_aliases=False)
    ncaa_by_id = {row['ncaa_game_id']: row for row in ncaa_rows}
    output = []; pending = list(report['pending'])
    for row in report['corroborated_research_only']:
        nr = nrefs[row['ncaa_game_id']]; er = erefs[row['espn_game_id']]
        nt = min(espn.utc(ref['observed_at_utc']) for ref in nr)
        et = min(espn.utc(ref['observed_at_utc']) for ref in er)
        nc = ncaa_by_id[row['ncaa_game_id']]
        nstart = datetime.fromtimestamp(int(nc['source_start_time_epoch']), timezone.utc)
        if min(nt, et) <= max(nstart, espn.utc(row['scheduled_start_utc'])):
            pending.append({**row, 'reason': 'FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START'})
            continue
        output.append({**row, 'ncaa_receipts': nr, 'espn_receipts': er,
                       'corroboration_available_at_utc': max(nt, et).isoformat(),
                       'postgame_source_chronology_verified': True,
                       'historical_pregame_features_verified': False})
    result = {'schema': ('tyler-historical-fbs-source-crosscheck-v1' if league=='NCAAF_FBS'
                       else 'tyler-historical-d1-source-crosscheck-v1'), 'split': split,
            'school_identity_policy': 'EXACT_NORMALIZED_SCHOOL_NAMES_NO_2026_ALIASES',
            'independent_ncaa_source_available': bool(official),
            'ncaa_source_game_ids': len(official), 'espn_source_game_ids': len(provider),
            'conflicting_ncaa_game_ids': sorted(ncaa_conflicts),
            'conflicting_espn_school_observations': sorted(provider_conflicts),
            'excluded_provider_game_ids': sorted(excluded_provider_ids),
            'two_source_final_agreements': len(output), 'corroborated_research_only': output,
            'pending_or_quarantined': len(pending), 'pending': pending,
            'source_scope_complete': False, 'independent_final_certification_complete': False,
            'training_allowed': False, 'historical_evaluation_enabled': False,
            'forecasting_enabled': False, 'promotion_allowed': False,
            'NO_BET': True, 'actual_wagers': 0}
    if source_quarantines:
        result.update(schema=('tyler-historical-d1-source-crosscheck-v2' if league=='NCAAM_D1'
                              else 'tyler-historical-fbs-source-crosscheck-v2'),
                      quarantined_ncaa_source_game_ids=sorted(quarantined_ncaa_ids),
                      quarantined_ncaa_source_observations=source_quarantines)
    if policy is not None:
        result.update(schema=('tyler-historical-fbs-reviewed-identity-crosscheck-v2' if league=='NCAAF_FBS'
                              else 'tyler-historical-d1-reviewed-identity-crosscheck-v3'),
                      school_identity_policy=policy['policy'],
                      school_identity_manifest_sha256=policy['manifest_sha256'],
                      reviewed_school_spellings=policy['reviewed_school_spellings'])
        if league=='NCAAM_D1':
            result.update(division_one_membership_verified=False,institutional_identity_certified=False)
    return result


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--league',choices=('NCAAF_FBS','NCAAM_D1'),default='NCAAF_FBS')
    parser.add_argument('--split',choices=tuple(owned.YEARS),default='train')
    parser.add_argument('--verified-school-aliases',action='store_true',
                        help='Opt into separately reviewed and replayed historical school spelling evidence')
    args=parser.parse_args()
    print(json.dumps(build(league=args.league,split=args.split,verified_school_aliases=args.verified_school_aliases), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
