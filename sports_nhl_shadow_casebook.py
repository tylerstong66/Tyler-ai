"""Audited descriptive NHL challenger settled-game score comparisons.

This view only reads already verified frozen NHL research records. It never
creates original forecasts, settles games, fits weights, or suggests wagers.
"""
import sports_benchmark_review as review

SOURCES = ('model', 'fixed_elo', 'market')
METRICS = ('brier', 'log_loss', 'accuracy')


def recent_verified(rows, shadows, originals, max_games=25):
    if isinstance(max_games, bool) or not isinstance(max_games, int) or max_games <= 0:
        raise ValueError('NHL postgame casebook requires positive display limit')
    examples = []
    for row in rows:
        identifier = row['game_id']
        shadow = shadows[identifier]
        original = originals[identifier]
        if original['sha256'] != shadow['source_prediction_sha256']:
            raise ValueError('NHL postgame casebook original forecast digest mismatch')
        if row['outcome'] not in ('home', 'away'):
            raise ValueError('NHL postgame casebook requires a verified two-way final')
        by_baseline = {}
        for baseline in SOURCES:
            if row[baseline] is None:
                by_baseline[baseline] = None
                continue
            by_baseline[baseline] = {
                metric: row['candidate'][metric] - row[baseline][metric]
                for metric in METRICS
            }
        examples.append({
            'game_id': identifier,
            'event_id': original['event_id'],
            'away': original['away'],
            'home': original['home'],
            'scheduled_start_utc': original['kickoff'],
            'final_verified_at_utc': row['verified_at'],
            'verified_winner': original[row['outcome']],
            'verified_winner_side': row['outcome'],
            'original_forecast_sha256': original['sha256'],
            'challenger_forecast_sha256': shadow['sha256'],
            'home_win_probabilities': row['home_probabilities'],
            'proper_scores': {name: row[name] for name in
                              ('candidate', 'model', 'fixed_elo', 'market')},
            'challenger_minus_baseline': by_baseline,
            'saved_market_provider': (original['market'].get('provider')
                                      if original.get('market') else None),
            'saved_market_observed_at_utc': (
                original.get('market_observed_at')
                if original.get('market') else None),
            'live_odds': False,
        })
    # Latest verified final first, deterministic ID tie-break, never selected
    # by candidate performance. Entire population remains in aggregate scoring.
    examples.sort(key=lambda row: (review.utc(row['final_verified_at_utc']),
                                   row['game_id']), reverse=True)
    return {
        'scope': 'all_already_verified_nhl_challenger_finals',
        'total_settled_shadow_games': len(examples),
        'shown': min(len(examples), max_games),
        'selection': 'latest final verified_at UTC first, then game_id; not chosen by performance',
        'proper_score_interpretation': (
            'challenger minus baseline: lower Brier/log loss favors challenger; '
            'positive accuracy difference favors challenger'),
        'caveat': 'Descriptive game-level audit, not independent evidence of profitability or a wagering signal.',
        'NO_BET': True,
        'actual_wagers': 0,
        'games': examples[:max_games],
    }
