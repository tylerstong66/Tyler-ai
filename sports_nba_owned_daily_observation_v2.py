"""Isolated native null-envelope NBA prospective source receipts; no predictions."""
from pathlib import Path
import json
import sports_nba_owned_daily_observation as shared
import sports_nba_games_page_v2 as page

ROOT = Path('benchmarks/nba_owned_daily_v2/captures')
PROTOCOL = shared._ReceiptProtocol(
    ROOT, 'tyler-nba-owned-daily-null-envelope-prospective-observation-v2',
    'tyler-nba-owned-daily-null-envelope-replay-v2',
    'tyler-nba-owned-daily-null-envelope-archive-audit-v2',
    page.parse, require_exact_complete_date=True)


def collect(base=Path('.'), *, days_ahead=1, fetch=None, clock=None):
    return shared.collect(base, days_ahead=days_ahead, fetch=fetch, clock=clock,
                          _protocol=PROTOCOL)


def replay(base, stamp, *, now=None):
    return shared.replay(base, stamp, now=now, _protocol=PROTOCOL)


def replay_all(base=Path('.'), *, now=None):
    return shared.replay_all(base, now=now, _protocol=PROTOCOL)


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--collect', action='store_true')
    actions.add_argument('--replay')
    actions.add_argument('--audit', action='store_true')
    parser.add_argument('--days-ahead', type=int, default=1)
    args = parser.parse_args()
    result = collect(days_ahead=args.days_ahead) if args.collect else (
        replay(Path('.'), args.replay) if args.replay else replay_all() if args.audit else
        {'collection_requested': False, 'feature_collection_enabled': False,
         'forecasting_enabled': False, 'NO_BET': True, 'actual_wagers': 0})
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__': main()
