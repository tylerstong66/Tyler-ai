"""Read-only, source-linked pregame comparison for the NHL challenger shadow.

Does not retrieve live odds, re-fit forecasts, score outcomes, or recommend bets.
Returns up to the earliest 25 *future* shadow forecasts by saved game start.
"""
import sports_benchmark_review as review


def upcoming(shadow, originals, at, limit=25):
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        raise ValueError('Positive NHL preview limit required')
    selected = []
    all_future = []
    for game_id, frozen in shadow.items():
        source = originals.get(game_id)
        if source is None or frozen['source_prediction_sha256'] != source['sha256']:
            raise ValueError('NHL shadow preview source identity mismatch')
        kickoff = review.utc(frozen['kickoff'])
        if kickoff <= at:
            continue
        if (frozen['game_id'] != source['game_id'] or
                frozen['event_id'] != source['event_id'] or
                frozen['kickoff'] != source['kickoff']):
            raise ValueError('NHL shadow preview game identity mismatch')
        market = source.get('market')
        price = market['conditional_home_probability'] if market else None
        if market is not None and review.utc(source['market_observed_at']) > review.utc(source['generated_at']):
            raise ValueError('NHL shadow preview contains post-forecast odds')
        probabilities = {
            'challenger': review.probability(frozen['home_probability']),
            'original_model': review.probability(source['model']['home']),
            'fixed_elo': review.probability(source['fixed_elo']['home']),
            'saved_market': review.probability(price) if price is not None else None,
        }
        selected.append({
            'game_id': game_id,
            'event_id': frozen['event_id'],
            'away': source['away'],
            'home': source['home'],
            'scheduled_start_utc': source['kickoff'],
            'archived_forecast_recorded_at_utc': frozen['recorded_at'],
            'source_generated_at_utc': source['generated_at'],
            'source_forecast_sha256': source['sha256'],
            'shadow_forecast_sha256': frozen['sha256'],
            'home_win_probabilities': probabilities,
            'saved_market_provider': market.get('provider') if market else None,
            'saved_market_observed_at_utc': source.get('market_observed_at') if market else None,
            'live_market_quote': False,
            'result_eligible_to_score_now': False,
        })
    selected.sort(key=lambda row: (review.utc(row['scheduled_start_utc']), row['game_id']))
    all_future = selected
    return {
        'scope': 'earliest_future_frozen_nhl_challenger_games',
        'total_future_enrolled': len(all_future),
        'shown': min(len(all_future), limit),
        'selection': 'scheduled_start_utc ascending, then game_id; never based on result or model confidence',
        'probability_convention': 'probability of home team winning including overtime or shootout',
        'quote_warning': 'Market probability is a saved pregame quote from the original forecast, NOT current odds or a verified closing line.',
        'NO_BET': True,
        'actual_wagers': 0,
        'games': all_future[:limit],
    }
