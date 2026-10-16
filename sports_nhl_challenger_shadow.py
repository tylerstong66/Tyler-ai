"""Forward-only NHL challenger shadow cohort; no fitting, source requests, wagers or promotion.

Reads previously frozen, source-linked NHL forecasts and their immutable official
settlements. The experimental challenger uses pinned 2024-season weights selected
from 2025 historical development; only genuinely future games may enroll.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import sports_benchmark_review as review
import sports_historical_benchmark as b
import sports_prospective_test as n

ROOT = Path('benchmarks/nhl_challenger_shadow_v1')
LIVE = Path('benchmarks/two_way_prospective/nhl')
SOURCE = Path('benchmarks/two_way_challenger_v1/nhl_report.json')


def protocol_and_weights(base):
    policy = json.loads((base / ROOT / 'protocol.json').read_text())
    source = json.loads((base / SOURCE).read_text())
    if (policy.get('candidate') != 'ridge_recipe'
            or policy.get('source_report') != str(SOURCE)
            or policy.get('review_checkpoint') != 100
            or policy.get('NO_BET') is not True
            or policy.get('actual_wagers') != 0
            or policy.get('promotion_allowed') is not False
            or source.get('NO_BET') is not True
            or source.get('promotion_allowed') is not False
            or source.get('sport') != 'NHL'
            or source.get('selected_development_candidate') != 'ridge_recipe'
            or source.get('training_season') != 2024
            or source.get('validation_season') != 2025
            or source.get('protocol_sha256') != policy.get('source_protocol_sha256')
            or source.get('score_rows_sha256') != policy.get('source_score_rows_sha256')):
        raise ValueError('NHL shadow provenance or frozen protocol mismatch')
    weights = source['models_fit_on_training_only']['ridge_recipe']['weights']
    if (weights != policy.get('weights') or len(weights) != 2
            or not all(isinstance(v, (float, int)) and not isinstance(v, bool)
                       and math.isfinite(v) for v in weights)):
        raise ValueError('Pinned challenger weights changed')
    activation = review.utc(policy['activation_utc'])
    return policy, weights, activation


def verified_live_forecast(path):
    pred = json.loads(path.read_text())
    if pred.get('sha256') != review.digest({k: v for k, v in pred.items() if k != 'sha256'}):
        raise ValueError('Frozen NHL original forecast digest mismatch')
    if (pred.get('sport') != 'NHL' or pred.get('NO_BET') is not True
            or pred.get('actual_wagers') != 0 or path.stem != pred.get('game_id')):
        raise ValueError('Not a valid paper NHL pregame forecast')
    if not (review.utc(pred['generated_at']) <= review.utc(pred['recorded_at'])
            < review.utc(pred['kickoff'])):
        raise ValueError('Original NHL forecast not recorded before kickoff')
    x = pred['features']
    if (not isinstance(x, list) or len(x) != 2 or x[0] != 1
            or any(isinstance(v, bool) or not isinstance(v, (int, float))
                   or not math.isfinite(v) for v in x)):
        raise ValueError('Invalid original NHL frozen Elo feature vector')
    for model in ('model', 'fixed_elo'):
        review.distribution(pred[model], ('home', 'away'))
    if pred['market'] is not None:
        review.probability(pred['market']['conditional_home_probability'])
    return pred


def evaluate(base=Path('.'), at=None):
    base = Path(base)
    now = at if at is not None else datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Timezone-aware audit clock required')
    now = now.astimezone(timezone.utc)
    policy, weights, activation = protocol_and_weights(base)
    root = base / ROOT
    live = base / LIVE
    shadow_dir = root / 'predictions'
    original_dir = live / 'predictions'
    shadow_dir.mkdir(parents=True, exist_ok=True)
    enrolled = []
    # Every new forecast is written only while its game remains in the future.
    # A frozen source forecast from before activation never becomes a shadow.
    for path in sorted(original_dir.glob('*.json')):
        pred = verified_live_forecast(path)
        shadow_path = shadow_dir / path.name
        if shadow_path.exists():
            continue
        if not (activation <= review.utc(pred['generated_at'])
                <= review.utc(pred['recorded_at']) <= now
                < review.utc(pred['kickoff'])):
            continue
        p = b.sigmoid(b.dot(weights, pred['features']))
        record = {
            'version': 'nhl-forward-challenger-shadow-v1',
            'game_id': pred['game_id'],
            'event_id': pred['event_id'],
            'kickoff': pred['kickoff'],
            'source_prediction_sha256': pred['sha256'],
            'source_generated_at': pred['generated_at'],
            'source_recorded_at': pred['recorded_at'],
            'source_model_sha256': pred['model_sha256'],
            'candidate': 'ridge_recipe_2024_fit_2025_development_selected',
            'protocol_sha256': review.digest(policy),
            'home_probability': p,
            'recorded_at': now.isoformat(),
            'NO_BET': True,
            'actual_wagers': 0,
        }
        record['sha256'] = review.digest(record)
        n.write_json(shadow_path, record, exclusive=True)
        enrolled.append(pred['game_id'])
    # Verify every existing shadow and independently recompute stored probability.
    # Never silently update past shadow predictions when input history changes.
    shadow = {}
    for path in sorted(shadow_dir.glob('*.json')):
        item = json.loads(path.read_text())
        if item.get('sha256') != review.digest({k: v for k, v in item.items() if k != 'sha256'}):
            raise ValueError('Shadow forecast digest mismatch')
        identifier = path.stem
        if identifier != item.get('game_id') or identifier in shadow:
            raise ValueError('Shadow forecast filename or ID mismatch')
        pred = verified_live_forecast(original_dir / path.name)
        p = b.sigmoid(b.dot(weights, pred['features']))
        if (item['source_prediction_sha256'] != pred['sha256']
                or item['source_model_sha256'] != pred['model_sha256']
                or item['source_generated_at'] != pred['generated_at']
                or item['source_recorded_at'] != pred['recorded_at']
                or item['event_id'] != pred['event_id']
                or item['kickoff'] != pred['kickoff']
                or item['candidate'] != 'ridge_recipe_2024_fit_2025_development_selected'
                or item['protocol_sha256'] != review.digest(policy)
                or item['NO_BET'] is not True or item['actual_wagers'] != 0
                or not math.isclose(item['home_probability'], p, abs_tol=1e-12)
                or review.utc(item['recorded_at']) < activation
                or not (review.utc(pred['generated_at']) <= review.utc(pred['recorded_at'])
                        <= review.utc(item['recorded_at']) < review.utc(pred['kickoff']))):
            raise ValueError('Shadow record differs from frozen source or enrollment policy')
        shadow[identifier] = item
    # Existing prospective validator independently checks source/result hashes,
    # score arithmetic, betting flags, timings and event-to-result linkage.
    _, settled_rows = review.load_rows(live, 'NHL', ('model', 'fixed_elo'))
    scores = []
    for row in settled_rows:
        item = shadow.get(row['game_id'])
        if item is None:
            continue
        outcome = row['outcome']
        if outcome not in ('home', 'away'):
            raise ValueError('NHL shadow settlement is not a two-outcome final')
        score = review.binary_scores(item['home_probability'], outcome)
        scores.append({'game_id': row['game_id'],
                       'block': review.utc(item['kickoff']).astimezone(
                           ZoneInfo('America/New_York')).date().isoformat(),
                       'candidate': score, 'model': row['binary']['model'],
                       'fixed_elo': row['binary']['fixed_elo'],
                       'market': row['binary'].get('market')})
    paired = [row for row in scores if row['market'] is not None]
    def metrics(rows, names):
        return {name: review.estimates([
            {'block': row['block'], **row[name]} for row in rows]) for name in names}
    names = ('candidate', 'model', 'fixed_elo', 'market')
    scored_games = [s['game_id'] for s in scores]
    selection = sorted(shadow.values(), key=lambda s:(review.utc(s['recorded_at']),s['game_id']))[:100]
    first_100_ids = {s['game_id'] for s in selection}
    status = {
        'version': 'nhl-forward-challenger-shadow-v1',
        'as_of_utc': now.isoformat(),
        'activation_utc': activation.isoformat(),
        'source_report': str(SOURCE),
        'source_report_protocol_sha256': policy['source_protocol_sha256'],
        'candidate': 'ridge_recipe',
        'enrolled': len(shadow),
        'newly_enrolled': len(enrolled),
        'scored': len(scores),
        'pending': len(shadow)-len(scores),
        'same_game_priced_count': len(paired),
        'all_scored_unpriced_and_priced': metrics(scores, names[:3]),
        'same_game_priced': metrics(paired, names),
        'first_100_enrolled': {
            'selected': len(selection),
            'settled_selected': len(first_100_ids.intersection(scored_games)),
            'target': 100,
            'status': 'ready_for_human_review' if (
                len(selection) == 100 and first_100_ids.issubset(scored_games))
                else 'collecting_or_awaiting_selected_finals',
        },
        'input_digest': review.digest({
            'shadow': {key: shadow[key]['sha256'] for key in sorted(shadow)},
            'scored': scores,
        }),
        'selection_warning': '2025 retrospective model selection was not blind; only post-activation NHL shadow games are prospective.',
        'limitation': 'Research only; all results are descriptive. No candidate selection, model promotion, bets, odds backfills or claims of an edge.',
        'promotion_allowed': False,
        'NO_BET': True,
        'actual_wagers': 0,
    }
    n.write_json(root / 'scoreboard.latest.json', status)
    return status


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='.')
    args = parser.parse_args()
    report = evaluate(args.base)
    print(json.dumps({k: report[k] for k in ('enrolled', 'newly_enrolled', 'scored', 'pending', 'same_game_priced_count', 'NO_BET')}))
