"""Separate prospective NBA daily source receipts; no feature or forecast writes."""
from datetime import datetime, timedelta, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re

import sports_expansion_observer as espn
import sports_expansion_audit as audit
import sports_nba_games_page as page
import sports_nba_official_schedule_audit as nba
from sports_nba_historical_owned import HEADERS
import requests

ROOT = Path('benchmarks/nba_owned_daily_v1/captures')
SCHEMA = 'tyler-nba-owned-daily-prospective-observation-v1'
MAX_AGE = timedelta(hours=12)
STAMP = r'\d{8}T\d{12}Z'


def fetch_page(url, *, get=None):
    if not isinstance(url, str) or not re.fullmatch(r'https://www\.nba\.com/games\?date=20\d{2}-\d{2}-\d{2}', url):
        raise ValueError('Unexpected NBA daily source endpoint')
    with (get or requests.get)(url, headers=dict(HEADERS), timeout=(10, 20),
                              allow_redirects=False, stream=True) as response:
        if type(response.status_code) is not int or response.status_code != 200:
            raise ValueError('NBA daily source did not return HTTP 200')
        parts = []; size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > page.MAX_BYTES: raise ValueError('Oversized NBA daily response')
            parts.append(chunk)
        return b''.join(parts)


def _clock(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError('Aware NBA daily clock required')
    return value.astimezone(timezone.utc)


def _provider(base, stamp):
    if not isinstance(stamp, str) or not re.fullmatch(STAMP, stamp):
        raise ValueError('Invalid linked daily ESPN capture')
    path = base/espn.ROOT/'captures'/stamp/'manifest.json'
    audit.audit_capture(path)
    raw = path.read_bytes(); manifest = json.loads(raw)
    return raw, manifest, nba.espn_games(manifest, path.parent)


def _build(raw, provider_raw, provider, *, started, received, day, season, stamp, offset):
    started = _clock(started); received = _clock(received)
    if (type(offset) is not int or not 0 <= offset <= 3 or received < started
            or received-started > timedelta(minutes=5)
            or day != (started.astimezone(page.EASTERN).date()+timedelta(days=offset)).isoformat()):
        raise ValueError('NBA daily request/receipt chronology mismatch')
    em = json.loads(provider_raw); et = espn.utc(em['recorded_at_utc'])
    if not et <= started <= received or received-et > MAX_AGE:
        raise ValueError('NBA daily linked provider is stale or future')
    parsed = page.parse(raw, requested_date=day, season=season, observed_at=received)
    selected = {key: value for key, value in provider.items()
                if espn.utc(value['scheduled_start_utc']).astimezone(page.EASTERN).date().isoformat() == day}
    report = nba.compare(parsed['games'], selected)
    matched = []; withheld = list(report['unverified'])
    uses = {}
    for row in report['matched']:
        key = row['nba_official_game_id']; uses[key] = uses.get(key, 0)+1
    for row in report['matched']:
        e = selected[row['espn_game_id']]
        if (uses[row['nba_official_game_id']] != 1 or e['season_stage'] != 2
                or e['provider_completed'] is not False or e['state'] != 'pre'
                or received >= espn.utc(e['scheduled_start_utc'])):
            withheld.append({**row, 'reason': 'NOT_UNIQUE_CORROBORATED_PREGAME'})
        else: matched.append(row)
    return {'schema': SCHEMA, 'collection_started_at_utc': started.isoformat(),
        'recorded_at_utc': received.isoformat(), 'requested_date': day,
        'requested_days_ahead': offset, 'season': season,
        'nba_source_url': 'https://www.nba.com/games?date='+day,
        'nba_raw_file': 'nba_games.html.gz', 'nba_raw_sha256': hashlib.sha256(raw).hexdigest(),
        'nba_raw_bytes': len(raw), 'espn_capture': stamp,
        'espn_manifest_sha256': hashlib.sha256(provider_raw).hexdigest(),
        'parsed_daily_page': parsed, 'matched': matched, 'withheld': withheld,
        'strict_pregame_correlated': len(matched),
        'espn_other_date_games_not_covered': len(provider)-len(selected),
        'source_scope_complete': False, 'full_season_schedule_verified': False,
        'source_origin_independently_attested': False, 'receipt_clock_independently_attested': False,
        'official_final_results_verified': False, 'actual_tipoff_time_attested': False,
        'feature_collection_enabled': False, 'forecasting_enabled': False,
        'model_training_enabled': False, 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def replay(base, stamp, *, now=None):
    base = Path(base); now = _clock(now or datetime.now(timezone.utc))
    if not isinstance(stamp, str) or not re.fullmatch(STAMP, stamp):
        raise ValueError('Invalid NBA daily receipt identifier')
    folder = base/ROOT/stamp
    if {p.name for p in folder.iterdir()} != {'manifest.json', 'nba_games.html.gz'}:
        raise ValueError('Unexpected NBA daily archive file')
    for name in ('manifest.json', 'nba_games.html.gz'):
        p = folder/name
        if p.is_symlink() or not p.is_file() or p.stat().st_size > page.MAX_BYTES:
            raise ValueError('NBA daily archive must be bounded regular files')
    original = (folder/'manifest.json').read_bytes(); saved = json.loads(original)
    received = espn.utc(saved['recorded_at_utc'])
    if received > now or received.strftime('%Y%m%dT%H%M%S%fZ') != stamp:
        raise ValueError('NBA daily archive time/folder disagreement')
    raw = audit.bounded_gzip_read((folder/'nba_games.html.gz').read_bytes())
    provider_raw, _, provider = _provider(base, saved['espn_capture'])
    expected = _build(raw, provider_raw, provider,
        started=espn.utc(saved['collection_started_at_utc']), received=received,
        day=saved['requested_date'], season=saved['season'], stamp=saved['espn_capture'],
        offset=saved['requested_days_ahead'])
    if original != espn.canonical(expected):
        raise ValueError('NBA daily receipt differs from exact source replay')
    return {'schema': 'tyler-nba-owned-daily-replay-v1', 'capture': stamp,
        'source_replay_verified': True, 'strict_pregame_correlated': expected['strict_pregame_correlated'],
        'current_source_age_hours': (now-received).total_seconds()/3600,
        'source_currently_fresh': now-received <= MAX_AGE,
        'feature_collection_enabled': False, 'forecasting_enabled': False, 'NO_BET': True, 'actual_wagers': 0}


def collect(base=Path('.'), *, days_ahead=1, fetch=None, clock=None):
    base = Path(base)
    if type(days_ahead) is not int or not 0 <= days_ahead <= 3:
        raise ValueError('NBA daily days-ahead must be an integer from zero through three')
    clock = clock or (lambda: datetime.now(timezone.utc))
    started = _clock(clock())
    replay_all(base, now=started)
    latest = sorted((base/espn.ROOT/'captures').glob('*/manifest.json'))
    if not latest: raise ValueError('No retained ESPN capture for NBA daily source')
    stamp = latest[-1].parent.name
    provider_raw, _, provider = _provider(base, stamp)
    et = espn.utc(json.loads(provider_raw)['recorded_at_utc'])
    if et > started or started-et > MAX_AGE:
        raise ValueError('NBA daily linked provider is stale or future')
    day = (started.astimezone(page.EASTERN).date()+timedelta(days=days_ahead)).isoformat()
    year = int(day[:4]) if int(day[5:7]) >= 7 else int(day[:4])-1
    season = str(year)+'-'+str((year+1) % 100).zfill(2)
    raw = (fetch or fetch_page)('https://www.nba.com/games?date='+day)
    received = _clock(clock()) # Read after the complete body has returned.
    manifest = _build(raw, provider_raw, provider, started=started, received=received,
                      day=day, season=season, stamp=stamp, offset=days_ahead)
    capture = received.strftime('%Y%m%dT%H%M%S%fZ'); dest = base/ROOT/capture
    # Validate everything before creating an append-only destination.
    dest.mkdir(parents=True, exist_ok=False)
    with (dest/'nba_games.html.gz').open('xb') as stream:
        stream.write(gzip.compress(raw, mtime=0))
    with (dest/'manifest.json').open('xb') as stream:
        stream.write(espn.canonical(manifest))
    replay(base, capture, now=received)
    return manifest


def replay_all(base=Path('.'), *, now=None):
    base = Path(base); now = _clock(now or datetime.now(timezone.utc)); root = base/ROOT
    reports = []
    if root.exists():
        if root.is_symlink() or not root.is_dir(): raise ValueError('Invalid NBA daily archive root')
        for folder in sorted(root.iterdir()):
            if folder.is_symlink() or not folder.is_dir(): raise ValueError('Unexpected NBA daily archive entry')
            reports.append(replay(base, folder.name, now=now))
    return {'schema': 'tyler-nba-owned-daily-archive-audit-v1', 'receipts_replayed': len(reports),
        'reports': reports, 'feature_collection_enabled': False, 'forecasting_enabled': False,
        'NO_BET': True, 'actual_wagers': 0}


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
