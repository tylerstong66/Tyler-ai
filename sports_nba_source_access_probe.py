"""Bounded diagnostics for fixed public NBA endpoints; never trusted source evidence."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import gzip
import hashlib
import json

import requests
from sports_nba_historical_owned import HEADERS, ENDPOINT
from sports_nba_official_schedule_audit import NBA_URL

MAX_BYTES = 8_000_000


def endpoints(now):
    day = now.astimezone(ZoneInfo('America/New_York')).date()
    return [('season_schedule', NBA_URL),
            ('daily_scoreboard', 'https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json'),
            ('official_games_page', 'https://www.nba.com/games?date='+day.isoformat()),
            ('official_next_games_page', 'https://www.nba.com/games?date='+(day+timedelta(days=1)).isoformat()),
            ('official_reference_final_page', 'https://www.nba.com/games?date=2026-04-10'),
            ('target_stats_season_schedule_2026_27', ENDPOINT+'?LeagueID=00&Season=2026-27'),
            ('official_all_calendar_schedule_page', 'https://www.nba.com/schedule?cal=all&pd=false&region=1')]


def run(output_dir, *, now=None, get=None):
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware NBA diagnostic clock required')
    now = now.astimezone(timezone.utc); output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    get = get or requests.get; observations = []
    for name, url in endpoints(now):
        row = {'endpoint': name, 'url': url, 'http_status': None,
               'payload_complete': False, 'payload_archived': False,
               'source_payload_validated': False, 'error_type': None}
        try:
            with get(url, headers=dict(HEADERS), timeout=(10, 20),
                     stream=True, allow_redirects=False) as response:
                code = response.status_code
                if type(code) is not int or not 100 <= code <= 599:
                    raise ValueError('Invalid HTTP diagnostic status')
                row['http_status'] = code
                if code != 200:
                    observations.append(row)
                    continue
                parts = []; size = 0
                for part in response.iter_content(65536):
                    size += len(part)
                    if size > MAX_BYTES:
                        raise ValueError('Oversized NBA diagnostic response')
                    parts.append(part)
                raw = b''.join(parts); digest = hashlib.sha256(raw).hexdigest()
                filename = name+'_'+digest+'.response.gz'
                with (output/filename).open('xb') as stream:
                    stream.write(gzip.compress(raw, mtime=0))
                try:
                    value = json.loads(raw)
                    kind = type(value).__name__
                    keys = sorted(value)[:20] if isinstance(value, dict) else []
                except (ValueError, UnicodeError):
                    kind = 'NON_JSON'; keys = []
                row.update(payload_complete=True, payload_archived=True,
                    response_body_sha256=digest, response_body_bytes=len(raw),
                    archive_file=filename, json_top_level_type=kind, json_object_keys=keys,
                    nba_next_data_marker_present=b'__NEXT_DATA__' in raw)
        except (requests.RequestException, ValueError) as error:
            # Do not expose proxy credentials, headers or exception messages.
            row['error_type'] = type(error).__name__
        observations.append(row)
    report = {'schema': 'tyler-nba-public-endpoint-access-diagnostic-v1',
        'probe_started_at_utc': now.isoformat(), 'requests': observations,
        'probe_requested': True, 'http_200_is_not_source_verification': True,
        'source_payload_validated': False, 'independent_nba_schedule_verified': False,
        'official_final_results_verified': False, 'feature_collection_enabled': False,
        'receipt_clock_independently_attested': False, 'forecasting_enabled': False,
        'model_training_enabled': False, 'promotion_allowed': False,
        'NO_BET': True, 'actual_wagers': 0}
    (output/'report.json').write_text(json.dumps(report, sort_keys=True, indent=2)+'\n')
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', action='store_true')
    parser.add_argument('--output-dir', type=Path, default=Path('nba-source-access-probe'))
    args = parser.parse_args()
    report = run(args.output_dir) if args.probe else {
        'probe_requested': False, 'source_payload_validated': False,
        'forecasting_enabled': False, 'NO_BET': True, 'actual_wagers': 0}
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == '__main__': main()
