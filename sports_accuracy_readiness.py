"""Read-only cross-sport prospective accuracy snapshot; never combine cohorts."""
import argparse
import json
import math
from pathlib import Path

import sports_benchmark_review as review

VERSION = 'cross-sport-accuracy-readonly-v1'
SHADOW = Path('benchmarks/nhl_challenger_shadow_v1/scoreboard.latest.json')
HITTER = Path('benchmarks/mlb_hitter_props_shadow_v1/scoreboard.latest.json')
CAUTION = ('Descriptive, incomplete samples. Challenger NHL games overlap original NHL games; '
           'MLB hitter player-games share games. Historical reconstructed tests are excluded. '
           'Saved bookmaker prices are not verified executable or closing lines; win rate is '
           'not a profitability measure. No model promotion, betting, or ROI claims.')


def _assert_no_bet(value, label):
    if value.get('NO_BET', value.get('no_wagers')) is not True or value.get('actual_wagers', 0) != 0:
        raise ValueError(label + ': missing strict research-only/no-wager evidence')


def _read(base, path):
    file = base / path
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 2_000_000:
        raise ValueError('Missing, redirected or oversized accuracy source: ' + str(path))
    value = json.loads(file.read_text())
    if not isinstance(value, dict):
        raise ValueError('Expected object accuracy source: ' + str(path))
    return value


def _mean(metric, field):
    value = metric['mean'][field]
    if value is not None and (isinstance(value, bool) or
                              not isinstance(value, (int, float)) or not math.isfinite(value) or
                              (field == 'accuracy' and not 0 <= value <= 1)):
        raise ValueError('Invalid accuracy metric: ' + field)
    return value


def _score(metric):
    count = metric['games']
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError('Invalid game denominator')
    result = {'games': count, 'accuracy': _mean(metric, 'accuracy'),
              'brier': _mean(metric, 'brier'), 'log_loss': _mean(metric, 'log_loss'),
              'blocks': metric['blocks'], 'uncertainty_status': metric['uncertainty_status']}
    if count == 0 and any(result[name] is not None for name in ('accuracy', 'brier', 'log_loss')):
        raise ValueError('Metrics cannot claim results without games')
    if count and result['accuracy'] is not None:
        wins = round(result['accuracy'] * count)
        if not math.isclose(result['accuracy'] * count, wins, rel_tol=0, abs_tol=1e-7):
            raise ValueError('Noninteger winner-pick count from purported game accuracy')
        result['correct_picks'] = wins
    else:
        result['correct_picks'] = None
    return result


def snapshot(base=Path('.')):
    base = Path(base)
    leagues = {}
    for sport, (folder, models) in review.COHORTS.items():
        data = review.review(base / folder, sport, models)
        _assert_no_bet(data, sport)
        if data['input_integrity'] != 'verified' or data['settled'] > data['recorded'] or data['pending'] != data['recorded'] - data['settled']:
            raise ValueError('Prospective cohort integrity or counts invalid: ' + sport)
        own = _score(data['all_decisive'][models[0]])
        paired = _score(data['paired_market'][models[0]])
        market = _score(data['paired_market']['market'])
        if own['games'] > data['settled'] or paired['games'] > own['games'] or paired['games'] != market['games']:
            raise ValueError('Mixed-sample market comparison: ' + sport)
        entry = {'recorded': data['recorded'], 'settled': data['settled'],
                 'pending': data['pending'], 'model_name': models[0],
                 'all_decisive_model': own, 'same_game_priced_model': paired,
                 'same_game_priced_market': market, 'review_due': data['review_due'],
                 'first_100_checkpoint': data.get('first_100_checkpoint', {}).get('status'),
                 'latest_verified_at_utc': data['latest_result_verified_at']}
        if sport == 'NFL':
            entry['all_settled_three_outcome_model'] = _score(data['all_settled_three_outcome'][models[0]])
            entry['tie_games_excluded_from_decisive'] = data['ties']
        leagues[sport] = entry

    shadow = _read(base, SHADOW)
    _assert_no_bet(shadow, 'NHL challenger')
    paired = shadow['same_game_priced']
    candidate = _score(paired['candidate'])
    market = _score(paired['market'])
    if (candidate['games'] != market['games'] or
            candidate['games'] != shadow['same_game_priced_count'] or
            shadow['scored'] + shadow['pending'] != shadow['enrolled'] or
            candidate['games'] > shadow['scored'] or shadow['scored'] > leagues['NHL']['settled']):
        raise ValueError('NHL shadow denominators disagree with primary sample')
    nhl_shadow = {'enrolled': shadow['enrolled'], 'scored': shadow['scored'],
                  'pending': shadow['pending'], 'candidate': candidate, 'market': market,
                  'overlaps_primary_nhl': True, 'separate_from_primary_total': True,
                  'first_100_status': shadow['first_100_enrolled']['status']}

    hitter = _read(base, HITTER)
    if hitter.get('no_wagers') is not True:
        raise ValueError('MLB hitter snapshot is not research-only')
    data = hitter['benchmark']
    if (data.get('no_wagers') is not True or
            data['scored'] + data['pending'] + data['ineligible'] != data['frozen_player_game_forecasts']):
        raise ValueError('MLB hitter player-game accounting inconsistent')
    for event in ('hit', 'hr'):
        if data['metrics'][event]['eligible_player_games'] != data['scored']:
            raise ValueError('MLB hitter conditional scoring count inconsistent')
    mlb_hitter = {'player_games_recorded': data['frozen_player_game_forecasts'],
                  'player_games_scored': data['scored'], 'pending': data['pending'],
                  'ineligible': data['ineligible'],
                  'independent_scored_games': data['distinct_official_game_ids_with_eligible_settlements'],
                  'market_odds_available': data['market_odds_available'],
                  'probability_brier_hit': data['metrics']['hit']['brier'],
                  'probability_brier_hr': data['metrics']['hr']['brier'],
                  'winner_pick_accuracy': None, 'profitable_betting_edge_proven': False}

    return {'version': VERSION, 'NO_BET': True, 'actual_wagers': 0,
            'primary_prospective': leagues, 'nhl_challenger_overlap': nhl_shadow,
            'mlb_hitter_conditional_props': mlb_hitter,
            'NBA': 'no verified prospective scored predictions',
            'NCAA_FBS': 'no verified prospective scored predictions',
            'NCAA_D1_men': 'no verified prospective scored predictions',
            'combined_all_sports_win_rate': None, 'ROI': None, 'limitations': CAUTION}


def render(data):
    lines = ['# Tyler AI sports prediction accuracy (read-only)', '',
             '**NO BET / actual wagers $0.**', '',
             '| Primary cohort | Decisive correct | All decisive | Model accuracy | Priced games | Priced model accuracy | Market accuracy |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for sport, row in data['primary_prospective'].items():
        a = row['all_decisive_model']; p = row['same_game_priced_model']; m = row['same_game_priced_market']
        percent = lambda x: 'N/A' if x is None else f'{x:.1%}'
        lines.append(f"| {sport} | {a['correct_picks']} | {a['games']} | {percent(a['accuracy'])} | {p['games']} | {percent(p['accuracy'])} | {percent(m['accuracy'])} |")
    shadow = data['nhl_challenger_overlap']
    lines += ['', '## Experimental NHL challenger (OVERLAPS NHL ABOVE)', '',
              f"Enrolled {shadow['enrolled']}, scored {shadow['scored']}, pending {shadow['pending']}. "
              f"Same {shadow['candidate']['games']} priced games: challenger {shadow['candidate']['correct_picks']} correct "
              f"({shadow['candidate']['accuracy']:.1%}); market {shadow['market']['accuracy']:.1%}.",
              '', '## Conditional MLB player props (NOT winner picks)', '']
    hitter = data['mlb_hitter_conditional_props']
    lines.append(f"Recorded {hitter['player_games_recorded']} player-games, scored {hitter['player_games_scored']} "
                 f"across {hitter['independent_scored_games']} official games; no bookmaker-price comparison.")
    lines += ['', 'NBA, NCAA football and NCAA men\'s basketball: prospective pick accuracy unavailable.',
              '', '**No valid combined sports accuracy or ROI can be calculated.**', '',
              data['limitations'], '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    report = snapshot(Path(args.base))
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else render(report))
