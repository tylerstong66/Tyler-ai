"""Pregame odds diagnostics and append-only follow-up quotes; no forecast edits."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path
import sports_benchmark_review as r


def parse_odds(records):
    """Read paired current moneylines only; opening/spread prices are not substitutes."""
    quotes, issues = [], []
    for record in records or []:
        ml = record.get('moneyline') or {}
        pair = [((ml.get(side) or {}).get('close') or {}).get('odds') for side in ('home', 'away')]
        if any(value is None for value in pair):
            issues.append('paired_current_moneyline_missing')
            continue
        try:
            values = [int(str(value)) for value in pair]
            if any(abs(value) < 100 for value in values):
                raise ValueError('Invalid American moneyline')
        except (ValueError, TypeError):
            issues.append('invalid_current_moneyline')
            continue
        quotes.append({'provider': (record.get('provider') or {}).get('name'),
                       'home_moneyline': values[0], 'away_moneyline': values[1],
                       'quote_kind': 'observed_current_quote_not_verified_closing_line'})
    return quotes, {'provider_records': len(records or []), 'usable_pairs': len(quotes),
                    'status': 'usable' if quotes else 'no_provider_odds' if not records else 'no_usable_current_pair',
                    'issues': issues}


def market(quote):
    values = [quote[side+'_moneyline'] for side in ('home', 'away')]
    if any(isinstance(p, bool) or not isinstance(p, int) or abs(p) < 100 for p in values):
        raise ValueError('Invalid American moneyline')
    h, a = [-p/(100-p) if p < 0 else 100/(p+100) for p in values]
    return {**quote, 'conditional_home_probability': h/(h+a)}


def verify_quote(data, pred, base=Path('.')):
    saved = data.get('sha256')
    if saved != r.digest({k: v for k, v in data.items() if k != 'sha256'}):
        raise ValueError('Follow-up quote hash mismatch')
    if data['prediction_sha256'] != pred['sha256'] or data['game_id'] != pred['game_id']:
        raise ValueError('Follow-up quote forecast linkage mismatch')
    for field in ('event_id', 'home', 'away', 'kickoff'):
        if data[field] != pred[field]:
            raise ValueError('Follow-up quote identity differs from saved forecast')
    if not (r.utc(pred['recorded_at']) <= r.utc(data['observed_at']) <= r.utc(data['recorded_at']) < r.utc(pred['kickoff'])):
        raise ValueError('Follow-up quote was not observed and recorded before start')
    if data.get('NO_BET') is not True or data.get('actual_wagers') != 0:
        raise ValueError('Paper-only quote required')
    source = data['source_snapshot']
    if 'scoreboard' not in source['source_url'] or source['retrieved_at'] != data['observed_at']:
        raise ValueError('Matching scoreboard timestamp required')
    path = base / source['path']
    content = path.read_bytes()
    import hashlib
    if hashlib.sha256(content).hexdigest() != source['sha256']:
        raise ValueError('Follow-up quote source hash mismatch')
    events = [e for e in json.loads(content) if e['event_id'] == pred['event_id']]
    if len(events) != 1:
        raise ValueError('Unique saved event required')
    event = events[0]
    if (event['state'] != 'pre' or event.get('completed') is not False
            or any(event[field] != pred[field] for field in ('home', 'away', 'kickoff'))):
        raise ValueError('Exact unstarted saved matchup required')
    if data.get('market') not in [market(q) for q in event.get('odds', [])]:
        raise ValueError('Follow-up quote absent from matching source snapshot')
    expected = market(data['market'])
    if not math.isclose(expected['conditional_home_probability'], data['market']['conditional_home_probability'], abs_tol=1e-12):
        raise ValueError('Follow-up market probability mismatch')
    return data


def collect_followups(root, capture, events, clock=None):
    """First usable later quote per unpriced forecast, saved separately before start.

    Never replay old captures to backfill quotes. Existing enrollment-time market
    fields, forecasts, results and benchmark scores remain immutable.
    """
    clock = clock or (lambda: datetime.now(timezone.utc))
    new, errors = [], []
    for path in sorted((root/'predictions').glob('*.json')):
        pred = json.loads(path.read_text())
        destination = root/'market_followups'/path.name
        if pred.get('market') is not None or destination.exists() or clock() >= r.utc(pred['kickoff']):
            continue
        try:
            if pred['sha256'] != r.digest({k: v for k, v in pred.items() if k != 'sha256'}):
                raise ValueError('Saved forecast hash mismatch')
            matches = [e for e in events if e['event_id'] == pred['event_id']]
            if len(matches) != 1:
                raise ValueError('Unique saved event required for follow-up quote')
            event = matches[0]
            if not event.get('odds'):
                continue
            # Find the actual retained scoreboard containing this exact event;
            # never use the first scoreboard date's timestamp for another day.
            sources = []
            for source in capture.evidence:
                if 'scoreboard' not in source['source_url']:
                    continue
                rows = json.loads(Path(source['path']).read_text())
                if event in rows:
                    sources.append(source)
            if len(sources) != 1:
                raise ValueError('Unique matching scoreboard snapshot required')
            if r.utc(sources[0]['retrieved_at']) < r.utc(pred['recorded_at']):
                continue
            data = {key: pred[key] for key in ('game_id', 'event_id', 'home', 'away', 'kickoff')}
            data.update({'prediction_sha256': pred['sha256'], 'market': market(event['odds'][0]),
                         'observed_at': sources[0]['retrieved_at'], 'recorded_at': clock().isoformat(),
                         'source_snapshot': sources[0], 'NO_BET': True, 'actual_wagers': 0,
                         'policy': 'first_usable_followup_quote_separate_from_enrollment_metrics_v1'})
            data['sha256'] = r.digest(data)
            verify_quote(data, pred)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open('x') as stream:
                stream.write(json.dumps(data, sort_keys=True, indent=2, allow_nan=False)+'\n')
            new.append(pred['game_id'])
        except (ValueError, KeyError, TypeError, OSError) as error:
            errors.append({'game_id': pred['game_id'], 'stage': 'market_followup', 'error': str(error)})
    return new, errors
