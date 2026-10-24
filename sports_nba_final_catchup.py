"""Bounded missing-native-final retries; default is a read-only collection plan."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re

import sports_nba_native_v2_retained_finals as history
from sports_expansion_audit import strict_json_loads

post = history.daily.post
source = history.daily.features.source
EASTERN = post.shared.page.EASTERN
SCHEMA = 'tyler-nba-native-v2-missing-final-catchup-v1'


def build_plan(base=Path('.'), *, now=None):
    now = history.daily.features._clock(now or datetime.now(timezone.utc))
    audit = history.build(base, now=now)
    day = now.astimezone(EASTERN).date()
    requests = {}; outside = []
    for row in audit['rows']:
        if (row['quarantined'] or row['result_observation'] is not None
                or row['reason'] != 'NO_RETAINED_NATIVE_FINAL_FOR_FROZEN_GAME'):
            continue
        starts = [source.utc(row[field]) for field in ('nba_saved_start_utc', 'espn_saved_start_utc')]
        dates = {start.astimezone(EASTERN).date() for start in starts}
        if len(dates) != 1 or now < max(starts):
            continue
        original_day = dates.pop(); back = (day-original_day).days
        if back in (2, 3):
            item = requests.setdefault(back, {'days_back': back, 'requested_date': original_day.isoformat(), 'nba_game_ids': []})
            item['nba_game_ids'].append(row['nba_game_id'])
        elif back > 3:
            outside.append(row['nba_game_id'])
    return {'schema': SCHEMA, 'checked_at_utc': now.isoformat(),
        'reference_eastern_date': day.isoformat(), 'default_yesterday_collection_unchanged': True,
        'requests': [requests[key] for key in sorted(requests)],
        'outside_retry_window_game_ids': sorted(outside), 'captures': [],
        'collection_requested': False, 'outcomes_enrolled': 0,
        'settlement_enabled': False, 'forecasting_enabled': False,
        'model_training_enabled': False, 'promotion_allowed': False,
        'NO_BET': True, 'actual_wagers': 0}


def collect(base=Path('.'), *, clock=None, fetch=None):
    clock = clock or (lambda: datetime.now(timezone.utc))
    plan = build_plan(base, now=clock())

    def guarded_clock():
        value = history.daily.features._clock(clock())
        if value.astimezone(EASTERN).date().isoformat() != plan['reference_eastern_date']:
            raise ValueError('NBA catchup plan crossed Eastern midnight; rebuild before collection')
        return value

    for request in plan['requests']:
        receipt = post.collect(base, days_back=request['days_back'], fetch=fetch, clock=guarded_clock)
        stamp = source.utc(receipt['recorded_at_utc']).strftime('%Y%m%dT%H%M%S%fZ')
        if receipt['requested_date'] != request['requested_date']:
            raise ValueError('NBA catchup receipt differs from planned date')
        plan['captures'].append({'capture': stamp, 'requested_date': receipt['requested_date']})
    plan['collection_requested'] = True
    publication_paths(base, plan)  # Replay every selected original before reporting success.
    return plan


def publication_paths(base, report):
    """Only successful, explicitly listed and replayed captures may be staged."""
    if (report['schema'] != SCHEMA or report['collection_requested'] is not True
            or report['NO_BET'] is not True
            or any(type(report[key]) is not int or report[key] != 0 for key in ('actual_wagers', 'outcomes_enrolled'))
            or any(report[key] is not False for key in ('settlement_enabled', 'forecasting_enabled', 'model_training_enabled', 'promotion_allowed'))):
        raise ValueError('Invalid NBA catchup publication gates')
    requests = report['requests']; captures = report['captures']
    reference = history.daily.features._clock(datetime.fromisoformat(report['checked_at_utc'])).astimezone(EASTERN).date()
    if (reference.isoformat() != report['reference_eastern_date'] or len(requests) > 2
            or len(captures) != len(requests)
            or len({r['days_back'] for r in requests}) != len(requests)
            or len({c['capture'] for c in captures}) != len(captures)):
        raise ValueError('Invalid bounded NBA catchup capture set')
    paths = []
    for request, capture in zip(requests, captures):
        back = request['days_back']; stamp = capture['capture']
        if (type(back) is not int or back not in (2, 3)
                or not isinstance(stamp, str) or re.fullmatch(r'[0-9]{8}T[0-9]{12}Z', stamp) is None
                or capture['requested_date'] != request['requested_date']
                or (reference-datetime.fromisoformat(request['requested_date']).date()).days != back):
            raise ValueError('Unplanned NBA catchup capture')
        post.replay(base, stamp)
        folder = post.ROOT/stamp
        manifest = strict_json_loads((Path(base)/folder/'manifest.json').read_bytes())
        if (manifest['requested_date'] != request['requested_date'] or manifest['requested_days_back'] != back
                or source.utc(manifest['collection_started_at_utc']).astimezone(EASTERN).date() != reference):
            raise ValueError('NBA catchup original receipt differs from plan')
        paths.append(folder.as_posix())
    return paths


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--collect', action='store_true')
    actions.add_argument('--publication-paths', type=Path)
    parser.add_argument('--base', type=Path, default=Path('.'))
    args = parser.parse_args()
    if args.publication_paths:
        print('\n'.join(publication_paths(args.base, strict_json_loads(args.publication_paths.read_bytes()))))
    else:
        print(json.dumps(collect(args.base) if args.collect else build_plan(args.base), indent=2, sort_keys=True, allow_nan=False))
