"""Immutable first-100-enrolled NHL challenger review, research only."""
import json

import sports_benchmark_review as review
import sports_prospective_test as paper

TARGET = 100
VERSION = 'nhl-shadow-first-100-enrolled-v1'
RELATIVE_PATH = 'checkpoints/first_100_enrolled/REVIEW.json'


def calibration_diagnostics(rows, names):
    """Fixed-bin reliability and probability sharpness on a declared sample.

    Descriptive only. Wilson intervals are not time-block uncertainty tests.
    The caller must supply identical game rows for every compared source.
    """
    sources = {}
    for name in names:
        pairs = [(row['home_probabilities'][name], row['outcome'] == 'home')
                 for row in rows]
        values = [review.probability(p) for p, _ in pairs]
        count = len(values)
        sources[name] = {
            'calibration': review.calibration(pairs),
            'spread': {
                'games': count,
                'mean_distance_from_even': (
                    sum(abs(p-.5) for p in values)/count if count else None),
                'share_between_40_and_60_percent': (
                    sum(.4 <= p <= .6 for p in values)/count if count else None),
            },
        }
    return {
        'sources': sources,
        'limitation': ('Fixed-bin descriptive reliability; small bins are unstable. '
                       'Wilson intervals assume independent games; no edge, promotion or wagering inference.'),
    }


def preserve(root, selection, scored_rows, protocol_digest, paired_differences):
    """Freeze a reproducible report only after the first 100 forecasts settle.

    Later game outcomes cannot substitute for earlier pending selected games.
    Existing saved checkpoints are independently recomputed and never rewritten.
    """
    if len(selection) > TARGET:
        raise ValueError('First-100 selection exceeds frozen protocol')
    ids = [item['game_id'] for item in selection]
    if len(set(ids)) != len(ids):
        raise ValueError('Repeated NHL shadow forecast ID in checkpoint')
    by_id = {row['game_id']: row for row in scored_rows}
    if len(by_id) != len(scored_rows):
        raise ValueError('Repeated NHL shadow result in checkpoint')
    chosen = [by_id[key] for key in ids if key in by_id]
    ready = len(ids) == TARGET and len(chosen) == TARGET
    checkpoint_path = root / RELATIVE_PATH
    result = {
        'selected': len(ids),
        'settled_selected': len(chosen),
        'target': TARGET,
        'status': 'collecting_forecasts' if len(ids) < TARGET
                  else 'awaiting_selected_results',
        'path': None,
        'checkpoint_sha256': None,
    }

    expected = None
    if ready:
        def metrics(rows, names):
            return {name: review.estimates([
                {'block': row['block'], **row[name]} for row in rows])
                for name in names}
        priced = [row for row in chosen if row['market'] is not None]
        expected = {
            'version': VERSION,
            'selection_rule': 'First 100 by saved shadow recorded_at UTC and game ID; no replacement by result order.',
            'game_ids': ids,
            'input_sha256': review.digest({
                'protocol': protocol_digest,
                'forecast_sha256': [item['sha256'] for item in selection],
                'scored_rows': chosen,
            }),
            'protocol_sha256': protocol_digest,
            'selected': TARGET,
            'settled': TARGET,
            'all_games': metrics(chosen, ('candidate', 'model', 'fixed_elo')),
            'priced_same_games': metrics(
                priced, ('candidate', 'model', 'fixed_elo', 'market')),
            'paired_differences': paired_differences(chosen),
            'all_games_calibration': calibration_diagnostics(
                chosen, ('candidate', 'model', 'fixed_elo')),
            'same_game_priced_calibration': calibration_diagnostics(
                priced, ('candidate', 'model', 'fixed_elo', 'market')),
            'note': '2025 challenger selection was retrospective and not blind; scores descriptive only.',
            'promotion_allowed': False,
            'NO_BET': True,
            'actual_wagers': 0,
        }
        expected['checkpoint_sha256'] = review.digest(expected)

    if checkpoint_path.exists():
        saved = json.loads(checkpoint_path.read_text())
        if expected is None or saved != expected:
            raise ValueError('Frozen NHL first-100 checkpoint or selected inputs changed')
        result.update(status='preserved', path=RELATIVE_PATH,
                      checkpoint_sha256=expected['checkpoint_sha256'])
    elif expected is not None:
        paper.write_json(checkpoint_path, expected, exclusive=True)
        result.update(status='preserved', path=RELATIVE_PATH,
                      checkpoint_sha256=expected['checkpoint_sha256'])
    return result
