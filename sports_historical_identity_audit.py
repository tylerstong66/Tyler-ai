"""Audit provider-history game identity and split leakage without model access."""
from collections import defaultdict, Counter
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
import hashlib
import json

import sports_expansion_historical_capture as history
import sports_expansion_observer as source
from sports_expansion_audit import archive_path, bounded_gzip_read, strict_json_loads, MAX_BLOB_SIZE

MIN_TEAM_START_SEPARATION = timedelta(hours=4)

FIELDS = ('scheduled_start_utc', 'home_team_id', 'away_team_id',
          'season_stage', 'state', 'neutral_site', 'provider_completed', 'home_score', 'away_score')


def _near_start_conflicts(team_timelines):
    """Find all ambiguous game IDs in O(n log n) per team, not quadratic.

    A game ID is implicated by any distinct ID less than four hours away.
    For sorted starts, every such pair has an adjacent different-ID boundary
    within that interval; checking adjacent observations is therefore enough
    to mark *both IDs*, even with repeated observations of one provider ID.
    """
    conflicts = set()
    for (league, _), observations in team_timelines.items():
        ordered = sorted((source.utc(start), game_id)
                         for start, game_id in observations)
        for (first_start, first_id), (next_start, next_id) in zip(
                ordered, ordered[1:]):
            if (first_id != next_id
                    and next_start - first_start < MIN_TEAM_START_SEPARATION):
                conflicts.add((league, first_id))
                conflicts.add((league, next_id))
    return conflicts


def audit(base=Path('.'), *, now=None, near_start_identity=False):
    # Preserve the original v1 historical report used by frozen NBA feature
    # reference hashes. The stronger quarantine is an explicit v2 research
    # policy, not a silent change to sealed historical dependencies.
    if type(near_start_identity) is not bool:
        raise ValueError('Explicit historical near-start identity policy required')
    base = Path(base); now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware historical audit clock required')
    plan = history.dates_by_league()
    root = base / history.ROOT / 'sources'
    known = {(league, split, day + extension)
             for league, splits in plan.items() for split, days in splits.items()
             for day in days for extension in ('.json.gz', '.receipt.json')}
    for path in root.rglob('*'):
        if path.is_file() and path.relative_to(root).parts not in known:
            raise ValueError('Unplanned historical source file')
    games = defaultdict(list); counts = Counter(); receipts = []
    for league in history.ORDER:
        for split, days in plan[league].items():
            for day in days:
                if not history.verify_existing(base, league, split, day, as_of=now):
                    continue
                path = archive_path(root / league / split / (day + '.receipt.json'))
                blob = archive_path(root / league / split / (day + '.json.gz'))
                if path.stat().st_size > MAX_BLOB_SIZE or blob.stat().st_size > MAX_BLOB_SIZE:
                    raise ValueError('Historical identity audit archive exceeds bound')
                raw = path.read_bytes()
                receipt = strict_json_loads(raw)
                original = bounded_gzip_read(blob.read_bytes())
                if (receipt.get('schema') != 'college-nba-history-provider-day-v1'
                        or receipt.get('league') != league or receipt.get('split') != split
                        or receipt.get('source_date') != day
                        or receipt.get('source_url') != source.scoreboard_url(league, day)
                        or receipt.get('NO_BET') is not True
                        or type(receipt.get('actual_wagers')) is not int
                        or receipt.get('actual_wagers') != 0
                        or receipt.get('promotion_allowed') is not False
                        or receipt.get('independently_verified_official_scores') is not False
                        or receipt.get('historical_results_are_not_pregame_forecasts') is not True
                        or source.utc(receipt['recorded_at_utc']) > now):
                    raise ValueError('Historical identity receipt scope changed during audit')
                if (hashlib.sha256(original).hexdigest() != receipt['original_response_sha256']
                        or source.parse_scoreboard(strict_json_loads(original), league)
                        != receipt['parsed_provider_scoreboard']):
                    raise ValueError('Historical identity receipt or normalized source changed during audit')
                ref = {'league': league, 'split': split, 'source_date': day,
                       'receipt_sha256': hashlib.sha256(raw).hexdigest(),
                       'response_sha256': receipt['original_response_sha256']}
                receipts.append(ref); counts[(league, split)] += 1
                for row in receipt['parsed_provider_scoreboard']['games']:
                    games[(league, row['game_id'])].append((row, ref, receipt['recorded_at_utc']))
    # One real matchup at one exact UTC start cannot count as two distinct
    # provider games merely because a later source day relabelled its ID.
    # Treat swapped home/away labels as ambiguous too; never choose a winner.
    fingerprints = defaultdict(set)
    for (league, game_id), found in games.items():
        for row, _, _ in found:
            fingerprint = (league, row['scheduled_start_utc'],
                           tuple(sorted((row['home_team_id'], row['away_team_id']))))
            fingerprints[fingerprint].add(game_id)
    relabelled = set()
    for (league, _, _), ids in fingerprints.items():
        if len(ids) > 1:
            relabelled.update((league, game_id) for game_id in ids)
    # One team cannot play two distinct regular/postseason games at the same
    # exact UTC start. The opponents may differ when a provider duplicates or
    # relabels an event, so the whole-matchup fingerprint above is insufficient.
    # Scope team IDs to each league; never select a preferred provider game.
    team_slots = defaultdict(set)
    for (league, game_id), found in games.items():
        for row, _, _ in found:
            for side in ('home_team_id', 'away_team_id'):
                slot = (league, row['scheduled_start_utc'], row[side])
                team_slots[slot].add(game_id)
    simultaneous_team_ids = set()
    for (league, _, _), ids in team_slots.items():
        if len(ids) > 1:
            simultaneous_team_ids.update((league, game_id) for game_id in ids)
    near_start_team_ids = set()
    if near_start_identity:
        # Provider IDs and scheduled starts can BOTH change after a reschedule.
        # Exact-time collision checks cannot detect an event relabelled with a
        # shifted kickoff. A team cannot safely be treated as playing two separate
        # NBA/FBS/D1 games whose listed starts are less than four hours apart.
        # This is a conservative ambiguity quarantine, NOT a source correction or
        # proof that two provider records are the same actual event.
        team_timelines = defaultdict(set)
        for (league, game_id), found in games.items():
            for row, _, _ in found:
                for team_id in (row['home_team_id'], row['away_team_id']):
                    team_timelines[(league, team_id)].add(
                        (row['scheduled_start_utc'], game_id))
        near_start_team_ids = _near_start_conflicts(team_timelines)
    quarantine = []; clean = Counter(); duplicate_observations = 0
    for (league, game_id), found in sorted(games.items()):
        reasons = set(); first = found[0][0]
        if (league, game_id) in relabelled:
            reasons.add('SAME_EVENT_FINGERPRINT_MULTIPLE_GAME_IDS')
        if (league, game_id) in simultaneous_team_ids:
            reasons.add('TEAM_SCHEDULED_IN_SIMULTANEOUS_GAME_IDS')
        if near_start_identity and (league, game_id) in near_start_team_ids:
            reasons.add('TEAM_STARTS_LESS_THAN_FOUR_HOURS_APART_ACROSS_GAME_IDS')
        duplicate_observations += len(found) - 1
        if len({ref['split'] for _, ref, _ in found}) != 1:
            reasons.add('GAME_ID_PRESENT_IN_TRAIN_AND_VALIDATION')
        if any(any(row[key] != first[key] for key in FIELDS) for row, _, _ in found[1:]):
            reasons.add('CONFLICTING_ARCHIVED_GAME_OBSERVATIONS')
        for row, ref, observed in found:
            kickoff = source.utc(row['scheduled_start_utc'])
            requested = date.fromisoformat(ref['source_date'])
            if not requested <= kickoff.date() <= requested + timedelta(days=1):
                reasons.add('EVENT_DATE_OUTSIDE_REQUESTED_DAY')
            allowed = plan[league][ref['split']]
            if not (date.fromisoformat(allowed[0]) <= kickoff.date()
                    <= date.fromisoformat(allowed[-1]) + timedelta(days=1)):
                reasons.add('EVENT_OUTSIDE_DECLARED_SPLIT')
            if row['provider_completed'] and source.utc(observed) <= kickoff:
                reasons.add('FINAL_OBSERVED_AT_OR_BEFORE_SAVED_START')
        if reasons:
            quarantine.append({'league': league, 'game_id': game_id,
                               'reasons': sorted(reasons),
                               'source_receipts': [ref for _, ref, _ in found]})
        else:
            clean[(league, found[0][1]['split'])] += 1
    report = {'schema': 'tyler-historical-provider-identity-audit-v1',
            'verified_source_days': len(receipts), 'receipt_provenance': receipts,
            'unique_provider_game_ids': len(games),
            'repeated_same_game_observations': duplicate_observations,
            'quarantined_relabelled_game_ids': len(relabelled),
            'quarantined_simultaneous_team_game_ids': len(simultaneous_team_ids),
            'quarantined_game_ids': len(quarantine), 'quarantined': quarantine,
            'cohorts': {league: {split: {
                'source_dates_verified': counts[(league, split)],
                'nonconflicting_provider_game_ids': clean[(league, split)]}
                for split in ('train', 'validation')} for league in history.ORDER},
            'independently_verified_official_results': False,
            'source_scope_complete': False, 'training_allowed': False,
            'historical_evaluation_enabled': False, 'forecasting_enabled': False,
            'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}
    if near_start_identity:
        report['schema'] = 'tyler-historical-provider-identity-audit-v2'
        report['identity_policy'] = 'LEAGUE_SCOPED_TEAM_STARTS_AT_LEAST_FOUR_HOURS_APART'
        report['quarantined_near_start_team_game_ids'] = len(near_start_team_ids)
    return report


def main():
    print(json.dumps(audit(), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
