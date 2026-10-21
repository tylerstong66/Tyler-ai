"""Separate opt-in NBA Final-break page receipts; no settlement or grading.

The v1/v2 archive roots and parser contracts are unchanged. This defaults to
read-only operation and retains bounded, append-only original v3 bytes.
"""
import argparse
import json
from pathlib import Path

import sports_nba_final_games_page_v3 as final
import sports_nba_postgame_observation as shared

ROOT = Path('benchmarks/nba_postgame_daily_v3/captures')
PROTOCOL = shared._ReceiptProtocol(
    ROOT, 'tyler-nba-recent-postgame-final-break-source-observation-v3',
    'tyler-nba-postgame-final-break-source-replay-v3', final.parse)


def collect(base=Path('.'), *, days_back=1, fetch=None, clock=None):
    return shared.collect(base, days_back=days_back, fetch=fetch, clock=clock,
                          _protocol=PROTOCOL)


def replay(base, stamp, *, now=None):
    return shared.replay(base, stamp, now=now, _protocol=PROTOCOL)


def replay_all(base=Path('.'), *, now=None):
    return shared.replay_all(base, now=now, _protocol=PROTOCOL)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--collect', action='store_true')
    actions.add_argument('--audit', action='store_true')
    actions.add_argument('--replay')
    parser.add_argument('--days-back', type=int, default=1)
    parser.add_argument('--base', type=Path, default=Path('.'))
    args = parser.parse_args()
    report = (collect(args.base, days_back=args.days_back) if args.collect else
              replay_all(args.base) if args.audit else
              replay(args.base, args.replay) if args.replay else
              {'collection_requested': False, 'settlement_enabled': False,
               'forecasting_enabled': False, 'NO_BET': True, 'actual_wagers': 0})
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
