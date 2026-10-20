"""Separate bounded recent-date NBA page captures; no result enrollment or grading."""
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

from sports_expansion_audit import archive_path, bounded_gzip_read
from sports_expansion_observer import canonical
from sports_nba_owned_daily_observation import fetch_page
import sports_nba_final_games_page as final
import sports_nba_games_page as page

ROOT = Path('benchmarks/nba_postgame_daily_v1/captures')
SCHEMA = 'tyler-nba-recent-postgame-source-observation-v1'


def _clock(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Aware NBA postgame clock required')
    return value.astimezone(timezone.utc)


def _build(raw, *, started, received, days_back):
    started = _clock(started); received = _clock(received)
    if (type(days_back) is not int or not 0 <= days_back <= 3
            or not started <= received <= started+timedelta(minutes=5)):
        raise ValueError('Invalid bounded NBA postgame date/receipt interval')
    if not isinstance(raw, bytes) or not raw or len(raw) > page.MAX_BYTES:
        raise ValueError('Missing or oversized NBA postgame response')
    day = started.astimezone(page.EASTERN).date()-timedelta(days=days_back)
    year = day.year if day.month >= 7 else day.year-1
    season = f'{year}-{(year+1)%100:02d}'
    try:
        parsed = final.parse(raw, requested_date=day.isoformat(), season=season, observed_at=received)
        status = ('SUPPORTED_REGULATION_FINAL_PAGE_SOURCE_ONLY' if parsed['daily_game_count'] else
                  'EMPTY_DAY_NO_FINAL_EVIDENCE')
    except ValueError:
        # Preserve opaque originals for separate source-shape inspection. No
        # partial finals may escape a page rejected by the strict parser.
        parsed = None; status = 'UNSUPPORTED_OR_NOT_COMPLETE_FINAL_PAGE'
    return {'schema': SCHEMA, 'collection_started_at_utc': started.isoformat(),
        'recorded_at_utc': received.isoformat(), 'requested_days_back': days_back,
        'requested_date': day.isoformat(), 'season': season,
        'source_url': 'https://www.nba.com/games?date='+day.isoformat(),
        'raw_file': 'nba_games.html.gz', 'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'raw_bytes': len(raw), 'page_status': status, 'parsed_final_page': parsed,
        'supported_final_game_count': parsed['daily_game_count'] if parsed else 0,
        'source_scope': 'ONE_RECENT_EASTERN_DATE_ONLY',
        'full_season_schedule_verified': False, 'independent_final_agreement_verified': False,
        'official_final_results_verified': False, 'source_origin_independently_attested': False,
        'receipt_clock_independently_attested': False, 'outcomes_enrolled': 0,
        'feature_backfill_allowed': False, 'feature_collection_enabled': False,
        'forecasting_enabled': False, 'settlement_enabled': False,
        'historical_evaluation_enabled': False, 'model_training_enabled': False,
        'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def replay(base, stamp, *, now=None):
    if not isinstance(stamp, str) or not re.fullmatch(r'\d{8}T\d{12}Z', stamp):
        raise ValueError('Invalid NBA postgame receipt identifier')
    now = _clock(now or datetime.now(timezone.utc))
    folder = archive_path(Path(base)/ROOT/stamp, directory=True)
    if {p.name for p in folder.iterdir()} != {'manifest.json', 'nba_games.html.gz'}:
        raise ValueError('Unexpected NBA postgame capture files')
    paths = [archive_path(folder/name) for name in ('manifest.json', 'nba_games.html.gz')]
    if any(not p.is_file() or p.stat().st_size > page.MAX_BYTES for p in paths):
        raise ValueError('Invalid bounded NBA postgame archive')
    original = paths[0].read_bytes(); manifest = json.loads(original)
    started = _clock(datetime.fromisoformat(manifest['collection_started_at_utc']))
    received = _clock(datetime.fromisoformat(manifest['recorded_at_utc']))
    if received > now or received.strftime('%Y%m%dT%H%M%S%fZ') != stamp:
        raise ValueError('NBA postgame receipt clock/folder disagreement')
    raw = bounded_gzip_read(paths[1].read_bytes(), page.MAX_BYTES)
    expected = _build(raw, started=started, received=received, days_back=manifest['requested_days_back'])
    if original != canonical(expected):
        raise ValueError('NBA postgame receipt differs from original source replay')
    return {'schema': 'tyler-nba-postgame-source-replay-v1', 'capture': stamp,
        'source_bytes_replayed': True, 'recorded_at_utc': received.isoformat(),
        'page_status': expected['page_status'],
        'supported_final_game_count': expected['supported_final_game_count'],
        'source_age_hours': (now-received).total_seconds()/3600,
        'fresh_source_observation': False, 'official_final_results_verified': False,
        'outcomes_enrolled': 0, 'settlement_enabled': False, 'forecasting_enabled': False,
        'NO_BET': True, 'actual_wagers': 0}


def replay_all(base=Path('.'), *, now=None):
    root = archive_path(Path(base)/ROOT, directory=True, allow_missing=True)
    folders = sorted(root.iterdir()) if root.exists() else []
    if len(folders) > 5000:
        raise ValueError('Unbounded NBA postgame capture inventory')
    reports = [replay(base, p.name, now=now) for p in folders]
    return {'receipts_replayed': len(reports), 'reports': reports, 'outcomes_enrolled': 0,
            'settlement_enabled': False, 'forecasting_enabled': False, 'NO_BET': True, 'actual_wagers': 0}


def collect(base=Path('.'), *, days_back=1, fetch=None, clock=None):
    if type(days_back) is not int or not 0 <= days_back <= 3:
        raise ValueError('NBA postgame lookback must be zero through three days')
    clock = clock or (lambda: datetime.now(timezone.utc))
    started = _clock(clock())
    replay_all(base, now=started) # Validate destination ancestors and all retained evidence first.
    day = started.astimezone(page.EASTERN).date()-timedelta(days=days_back)
    raw = (fetch or fetch_page)('https://www.nba.com/games?date='+day.isoformat())
    received = _clock(clock()) # Capture only after the entire response returned.
    manifest = _build(raw, started=started, received=received, days_back=days_back)
    stamp = received.strftime('%Y%m%dT%H%M%S%fZ')
    folder = archive_path(Path(base)/ROOT/stamp, directory=True, allow_missing=True)
    folder.mkdir(parents=True, exist_ok=False)
    with (folder/'nba_games.html.gz').open('xb') as stream:
        stream.write(gzip.compress(raw, mtime=0))
    with (folder/'manifest.json').open('xb') as stream:
        stream.write(canonical(manifest))
    replay(base, stamp, now=received)
    return manifest


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument('--collect', action='store_true')
    actions.add_argument('--audit', action='store_true')
    actions.add_argument('--replay')
    parser.add_argument('--days-back', type=int, default=1)
    parser.add_argument('--base', type=Path, default=Path('.'))
    args = parser.parse_args()
    result = (collect(args.base, days_back=args.days_back) if args.collect else
              replay_all(args.base) if args.audit else
              replay(args.base, args.replay) if args.replay else
              {'collection_requested': False, 'settlement_enabled': False, 'NO_BET': True, 'actual_wagers': 0})
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__': main()
