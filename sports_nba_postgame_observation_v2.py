"""Isolated recent-date native null-envelope NBA source captures; no grading."""
from pathlib import Path
import json
import sports_nba_postgame_observation as shared
import sports_nba_final_games_page_v2 as final

ROOT = Path('benchmarks/nba_postgame_daily_v2/captures')
PROTOCOL = shared._ReceiptProtocol(
    ROOT, 'tyler-nba-recent-postgame-null-envelope-source-observation-v2',
    'tyler-nba-postgame-null-envelope-source-replay-v2', final.parse)


def collect(base=Path('.'), *, days_back=1, fetch=None, clock=None):
    return shared.collect(base, days_back=days_back, fetch=fetch, clock=clock,
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
    actions.add_argument('--audit', action='store_true')
    actions.add_argument('--replay')
    parser.add_argument('--days-back', type=int, default=1)
    args = parser.parse_args()
    result = (collect(days_back=args.days_back) if args.collect else replay_all() if args.audit else
              replay(Path('.'), args.replay) if args.replay else
              {'collection_requested': False, 'settlement_enabled': False, 'NO_BET': True, 'actual_wagers': 0})
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__': main()
