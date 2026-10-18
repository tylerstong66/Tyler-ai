"""Append-only NCAA-owned D1 men's historical daily responses; no model use."""
from pathlib import Path
from datetime import datetime, timezone, date, timedelta
import gzip
import hashlib
import json

import sports_ncaa_official_source as ncaa
import sports_ncaa_historical_owned as common
import sports_expansion_historical_capture as history
import sports_expansion_observer as source
from sports_expansion_audit import bounded_gzip_read, MAX_BLOB_SIZE

ROOT = history.ROOT / 'ncaa_owned' / 'NCAAM_D1'
YEARS = dict(common.YEARS)
DATES = {part:tuple(days) for part,days in history.dates_by_league()['NCAAM_D1'].items()}


def _scope(split, day):
    if split not in YEARS or not isinstance(day, str) or day not in DATES[split]:
        raise ValueError('Invalid NCAA D1 historical day scope')
    return day


def _rows(raw, split, day, observed):
    rows = common._rows(raw, split, observed, league='NCAAM_D1')
    requested = date.fromisoformat(day)
    for row in rows:
        at = datetime.fromtimestamp(int(row['source_start_time_epoch']), timezone.utc)
        if not requested <= at.date() <= requested + timedelta(days=1):
            raise ValueError('NCAA D1 event outside requested day or next UTC day')
    return rows



def _parse_with_quarantine(raw, split, day, observed):
    """Retain a malformed tied final as evidence, never an eligible result.

    All other source/schema failures still fail the complete batch. A tied
    final must independently pass the existing non-result identity/date
    checks before it can enter this narrowly defined quarantine.
    """
    try:
        return _rows(raw, split, day, observed), []
    except ncaa.TiedNcaaFinalError:
        pass
    payload = json.loads(raw)
    rows = []; quarantined = []; seen = set()
    for contest in payload['data']['contests']:
        game_id = ncaa._positive_id(contest.get('contestId'), 'contest ID')
        if game_id in seen:
            raise ValueError('Repeated NCAA contest identity')
        seen.add(game_id)
        single = source.canonical({'data': {'contests': [contest]}})
        try:
            rows.extend(_rows(single, split, day, observed))
        except ncaa.TiedNcaaFinalError:
            # This copy validates identity and date only. Its synthetic P
            # state is never retained as a source observation or result.
            pending = {**contest, 'gameState': 'P'}
            structural = _rows(source.canonical({'data': {'contests': [pending]}}),
                               split, day, observed)[0]
            at = datetime.fromtimestamp(int(structural['source_start_time_epoch']), timezone.utc)
            if observed <= at:
                raise ValueError('Malformed NCAA final observed before scheduled start')
            quarantined.append({'ncaa_game_id': game_id,
                'home_name': structural['home_name'], 'away_name': structural['away_name'],
                'source_start_date': structural['source_start_date'],
                'source_start_time_epoch': structural['source_start_time_epoch'],
                'original_source_state': contest['gameState'],
                'original_home_score': next(t['score'] for t in contest['teams'] if t['isHome']),
                'original_away_score': next(t['score'] for t in contest['teams'] if not t['isHome']),
                'reason': 'INVALID_TIED_NCAA_REPORTED_FINAL',
                'original_contest_sha256': hashlib.sha256(source.canonical(contest)).hexdigest(),
                'eligible_for_result_agreement': False})
    return rows, quarantined


def verify(base, split, day, *, now=None):
    day = _scope(split, day); now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware NCAA D1 audit clock required')
    folder = Path(base) / ROOT / split
    blob = folder / (day + '.json.gz'); path = folder / (day + '.receipt.json')
    if not blob.exists() and not path.exists():
        return None
    if not blob.exists() or not path.exists():
        raise ValueError('Missing NCAA D1 sealed source component')
    saved = json.loads(path.read_bytes())
    if (saved.get('schema') not in ('tyler-ncaa-owned-d1-history-day-v1',
                                         'tyler-ncaa-owned-d1-history-day-v2')
            or saved.get('league') != 'NCAAM_D1' or saved.get('split') != split
            or saved.get('source_date') != day or saved.get('season_year') != YEARS[split]
            or saved.get('source_url') != ncaa.graph_url('NCAAM_D1', year=YEARS[split], day=day)
            or saved.get('NO_BET') is not True or type(saved.get('actual_wagers')) is not int
            or saved.get('actual_wagers') != 0 or saved.get('promotion_allowed') is not False
            or saved.get('model_training_enabled') is not False
            or saved.get('forecasting_enabled') is not False
            or saved.get('official_result_grading_enabled') is not False):
        raise ValueError('NCAA D1 source identity or research guard changed')
    observed = source.utc(saved['recorded_at_utc'])
    if observed > now:
        raise ValueError('NCAA D1 source observation is future-dated')
    if blob.stat().st_size > MAX_BLOB_SIZE:
        raise ValueError('Oversized compressed NCAA D1 source')
    raw = bounded_gzip_read(blob.read_bytes(), limit=ncaa.MAX_BYTES)
    if hashlib.sha256(raw).hexdigest() != saved['original_response_sha256']:
        raise ValueError('NCAA D1 original response digest mismatch')
    if saved['schema']=='tyler-ncaa-owned-d1-history-day-v2':
        rows, quarantined = _parse_with_quarantine(raw, split, day, observed)
        if not quarantined or quarantined != saved.get('quarantined_ncaa_contests'):
            raise ValueError('NCAA D1 source quarantine differs from original')
    else:
        rows = _rows(raw, split, day, observed)
        if saved.get('quarantined_ncaa_contests'):
            raise ValueError('Legacy NCAA D1 source cannot contain unverified quarantine')
    if rows != saved['parsed_ncaa_games']:
        raise ValueError('NCAA D1 original normalization changed')
    return saved


def capture(fetch, *, base=Path('.'), split='auto', per_run=20, now=None):
    if split not in (*YEARS, 'auto') or type(per_run) is not int or not 1 <= per_run <= 20:
        raise ValueError('NCAA D1 acquisition budget is 1..20 days')
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Aware NCAA D1 acquisition clock required')
    base = Path(base); root = base / ROOT
    known = {(part, day + suffix) for part, days in DATES.items() for day in days
             for suffix in ('.json.gz', '.receipt.json')}
    for path in root.rglob('*'):
        if path.is_file() and path.relative_to(root).parts not in known:
            raise ValueError('Unplanned NCAA D1 historical source file')
    existing = {(part, day): verify(base, part, day, now=now)
                for part, days in DATES.items() for day in days}
    if split == 'auto':
        split = next((part for part, days in DATES.items()
                      if any(existing[(part, day)] is None for day in days)), 'validation')
    selected = [day for day in DATES[split] if existing[(split, day)] is None][:per_run]
    if any(date.fromisoformat(day) >= now.astimezone(timezone.utc).date() for day in selected):
        raise ValueError('NCAA D1 historical request day is not closed')
    prepared = []
    for day in selected:
        url = ncaa.graph_url('NCAAM_D1', year=YEARS[split], day=day)
        raw = fetch(url)
        if not isinstance(raw, bytes) or not raw or len(raw) > ncaa.MAX_BYTES:
            raise ValueError('Missing or oversized NCAA D1 original response')
        rows, quarantined = _parse_with_quarantine(raw, split, day, now)
        saved = {'schema': 'tyler-ncaa-owned-d1-history-day-v1', 'league': 'NCAAM_D1',
                 'split': split, 'source_date': day, 'season_year': YEARS[split], 'source_url': url,
                 'recorded_at_utc': now.astimezone(timezone.utc).isoformat(),
                 'original_response_sha256': hashlib.sha256(raw).hexdigest(),
                 'parsed_ncaa_games': rows, 'official_result_grading_enabled': False,
                 'model_training_enabled': False, 'forecasting_enabled': False,
                 'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}
        if quarantined:
            saved.update(schema='tyler-ncaa-owned-d1-history-day-v2',
                         quarantined_ncaa_contests=quarantined)
        prepared.append((day, raw, saved))
    folder = root / split
    for day, raw, saved in prepared:
        folder.mkdir(parents=True, exist_ok=True)
        with (folder/(day+'.json.gz')).open('xb') as stream:
            stream.write(gzip.compress(raw, mtime=0))
        with (folder/(day+'.receipt.json')).open('xb') as stream:
            stream.write(source.canonical(saved))
    return {'schema':'tyler-ncaa-owned-d1-history-capture-status-v1', 'split':split,
            'new_source_days':len(prepared), 'retained_source_days':
                sum(existing[(split, day)] is not None for day in DATES[split])+len(prepared),
            'quarantined_source_game_ids': sorted({q['ncaa_game_id']
                for saved in [s for (part, _), s in existing.items() if part==split and s is not None]
                             + [saved for _, _, saved in prepared]
                for q in saved.get('quarantined_ncaa_contests', [])}),
            'official_source_completeness_certified':False,
            'independent_result_crosscheck_complete':False, 'model_training_enabled':False,
            'forecasting_enabled':False, 'promotion_allowed':False, 'NO_BET':True, 'actual_wagers':0}


def main():
    import requests
    def fetch(url):
        response = requests.get(url, timeout=18, headers={
            'Accept':'application/json', 'User-Agent':'TylerAI-Historical-Research-NoBets/1.0'})
        response.raise_for_status()
        return response.content
    print(json.dumps(capture(fetch), sort_keys=True))


if __name__ == '__main__':
    main()
