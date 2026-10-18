"""Bounded append-only NCAA-owned historical FBS source acquisition, no models."""
from datetime import datetime, timezone, date, timedelta
from pathlib import Path
import gzip
import hashlib
import json

import sports_ncaa_official_source as ncaa
import sports_expansion_historical_capture as history
import sports_expansion_observer as source
from sports_expansion_audit import bounded_gzip_read, MAX_BLOB_SIZE

ROOT = history.ROOT / 'ncaa_owned' / 'NCAAF_FBS'
YEARS = {'train': 2024, 'validation': 2025}
WEEKS = tuple(range(1, 22))


def _scope(split, week):
    if split not in YEARS or type(week) is not int or week not in WEEKS:
        raise ValueError('Invalid independent NCAA historical source scope')
    return f'week-{week:02d}'


def _rows(raw, split, observed):
    rows = ncaa.official_scoreboard(raw, 'NCAAF_FBS')
    low, high = history.SEASONS['NCAAF_FBS'][split]
    for row in rows:
        value = row['source_start_time_epoch']
        if isinstance(value, bool) or not str(value).isdigit():
            raise ValueError('Missing NCAA historical kickoff identity')
        kickoff = datetime.fromtimestamp(int(value), timezone.utc)
        if not date.fromisoformat(low) <= kickoff.date() <= date.fromisoformat(high) + timedelta(days=1):
            raise ValueError('NCAA historical event outside declared source season')
        if row['provider_reported_final'] and observed <= kickoff:
            raise ValueError('NCAA historical final observed before saved kickoff')
    return rows


def verify(base, split, week, *, now=None):
    stem = _scope(split, week)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware NCAA historical receipt audit clock required')
    root = Path(base) / ROOT / split
    blob = root / (stem + '.json.gz'); path = root / (stem + '.receipt.json')
    if not blob.exists() and not path.exists():
        return None
    if not blob.exists() or not path.exists():
        raise ValueError('Missing sealed NCAA historical archive component')
    saved = json.loads(path.read_bytes())
    if (saved.get('schema') != 'tyler-ncaa-owned-history-week-v1'
            or saved.get('league') != 'NCAAF_FBS' or saved.get('split') != split
            or saved.get('season_year') != YEARS[split] or saved.get('week') != week
            or saved.get('source_url') != ncaa.graph_url('NCAAF_FBS', year=YEARS[split], week=week)
            or saved.get('NO_BET') is not True or type(saved.get('actual_wagers')) is not int
            or saved.get('actual_wagers') != 0 or saved.get('promotion_allowed') is not False
            or saved.get('forecasting_enabled') is not False
            or saved.get('model_training_enabled') is not False
            or saved.get('official_result_grading_enabled') is not False):
        raise ValueError('NCAA historical source identity or research guard changed')
    observed = source.utc(saved['recorded_at_utc'])
    if observed > now:
        raise ValueError('NCAA historical observation is future-dated')
    if blob.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError('Oversized compressed NCAA historical source')
    raw = bounded_gzip_read(blob.read_bytes(), limit=ncaa.MAX_BYTES)
    if hashlib.sha256(raw).hexdigest() != saved['original_response_sha256']:
        raise ValueError('NCAA historical original response digest mismatch')
    if _rows(raw, split, observed) != saved['parsed_ncaa_games']:
        raise ValueError('NCAA historical normalization differs from raw archive')
    return saved


def capture(fetch, *, base=Path('.'), split='train', per_run=3, now=None):
    if split not in (*YEARS, 'auto') or type(per_run) is not int or not 1 <= per_run <= 3:
        raise ValueError('Historical NCAA fetch budget is 1..3 weeks')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware NCAA historical observation clock required')
    base = Path(base)
    known = {(part, f'week-{week:02d}' + suffix) for part in YEARS for week in WEEKS
             for suffix in ('.json.gz', '.receipt.json')}
    for path in (base / ROOT).rglob('*'):
        if path.is_file() and path.relative_to(base / ROOT).parts not in known:
            raise ValueError('Unplanned independent NCAA historical archive')
    existing = {}
    # Validate all retained independent seasons before any fetch or new write.
    for part in YEARS:
        for week in WEEKS:
            existing[(part, week)] = verify(base, part, week, now=now)
    if split == 'auto':
        split = next((part for part in YEARS
                      if any(existing[(part, week)] is None for week in WEEKS)), 'validation')
    selected = [week for week in WEEKS if existing[(split, week)] is None][:per_run]
    prepared = []
    for week in selected:
        url = ncaa.graph_url('NCAAF_FBS', year=YEARS[split], week=week)
        raw = fetch(url)
        if not isinstance(raw, bytes) or not raw or len(raw) > ncaa.MAX_BYTES:
            raise ValueError('Independent NCAA historical response missing or oversized')
        rows = _rows(raw, split, now)
        saved = {'schema': 'tyler-ncaa-owned-history-week-v1', 'league': 'NCAAF_FBS',
                 'split': split, 'season_year': YEARS[split], 'week': week, 'source_url': url,
                 'recorded_at_utc': now.astimezone(timezone.utc).isoformat(),
                 'original_response_sha256': hashlib.sha256(raw).hexdigest(),
                 'parsed_ncaa_games': rows, 'official_result_grading_enabled': False,
                 'model_training_enabled': False, 'forecasting_enabled': False,
                 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}
        prepared.append((week, raw, saved))
    folder = base / ROOT / split
    for week, raw, saved in prepared:
        folder.mkdir(parents=True, exist_ok=True)
        stem = _scope(split, week)
        with (folder / (stem + '.json.gz')).open('xb') as stream:
            stream.write(gzip.compress(raw, mtime=0))
        with (folder / (stem + '.receipt.json')).open('xb') as stream:
            stream.write(source.canonical(saved))
    return {'schema': 'tyler-ncaa-owned-history-capture-status-v1', 'split': split,
            'new_source_weeks': len(prepared), 'retained_source_weeks':
                sum(existing[(split, week)] is not None for week in WEEKS) + len(prepared),
            'source_week_completeness_certified': False,
            'independent_result_crosscheck_complete': False,
            'model_training_enabled': False, 'forecasting_enabled': False,
            'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def main():
    import requests
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--split', choices=(*YEARS, 'auto'), default='auto')
    args = parser.parse_args()
    def fetch(url):
        response = requests.get(url, timeout=18, headers={
            'Accept': 'application/json', 'User-Agent': 'TylerAI-Historical-Research-NoBets/1.0'})
        response.raise_for_status()
        return response.content
    print(json.dumps(capture(fetch, split=args.split), sort_keys=True))


if __name__ == '__main__':
    main()
