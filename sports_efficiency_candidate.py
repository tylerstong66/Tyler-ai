"""Offline opponent-adjusted NFL candidate; no production or ledger writes."""
import csv
import heapq
import json
import math
from collections import defaultdict, deque
from datetime import timedelta
from pathlib import Path
import sports_historical_benchmark as b

VERSION = 'nfl-efficiency-v2'
FEATURES = (*b.FEATURES, 'adjusted_offense_difference', 'adjusted_defense_difference')


def read_stats(path, games):
    expected = {g.identifier: g for g in games}
    stats = {}
    with Path(path).open(newline='') as stream:
        records = list(csv.DictReader(stream))
    for r in records:
        identifier = r['game_id']
        if identifier not in expected:
            raise ValueError('Stats game missing from pinned schedule')
        g = expected[identifier]
        team = b.TEAM_ALIASES.get(r['team'], r['team'])
        opponent = b.TEAM_ALIASES.get(r['opponent_team'], r['opponent_team'])
        if {team, opponent} != {g.home, g.away} or int(r['season']) != g.season or int(r['week']) != g.week:
            raise ValueError('Stats identity mismatch')
        key = (identifier, team)
        if key in stats:
            raise ValueError('Duplicate team-game stats')
        plays = sum(int(r[k]) for k in ('attempts', 'sacks_suffered', 'carries'))
        epa = float(r['passing_epa']) + float(r['rushing_epa'])
        if plays <= 0 or not math.isfinite(epa):
            raise ValueError('Invalid efficiency observation')
        stats[key] = (epa, plays)
    if set(stats) != {(g.identifier, t) for g in games for t in (g.home, g.away)}:
        raise ValueError('Incomplete historical stats coverage')
    return stats


class EfficiencyState:
    def __init__(self):
        self.offense = defaultdict(lambda: deque(maxlen=16))
        self.defense = defaultdict(lambda: deque(maxlen=16))

    @staticmethod
    def rating(history):
        # 200 zero-EPA pseudo plays shrink sparse history toward neutral.
        return sum(epa for epa, plays in history) / (200 + sum(plays for epa, plays in history))

    def ratings(self, team):
        return self.rating(self.offense[team]), self.rating(self.defense[team])

    def apply(self, game, stats):
        # Snapshot both opponents BEFORE either side is updated.
        ratings = {t: self.ratings(t) for t in (game.home, game.away)}
        for team, opponent in ((game.home, game.away), (game.away, game.home)):
            epa, plays = stats[(game.identifier, team)]
            _, opp_def = ratings[opponent]
            self.offense[team].append((epa - opp_def * plays, plays))
            self.defense[opponent].append((epa - ratings[team][0] * plays, plays))


def features(games, stats, delay=48):
    if delay < 48:
        raise ValueError('Historical stats delay must be at least 48h')
    rows = b.chronological_features(games)
    state, pending = EfficiencyState(), []
    for row in rows:
        g = row['game']; cutoff = b.utc(row['cutoff'])
        while pending and pending[0][0] <= cutoff:
            _, _, prior = heapq.heappop(pending)
            state.apply(prior, stats)
        ho, hd = state.ratings(g.home); ao, ad = state.ratings(g.away)
        row['x'] += [ho - ao, ad - hd]  # Better defense means lower EPA allowed.
        row['efficiency_prior_games'] = len(state.offense[g.home]), len(state.offense[g.away])
        heapq.heappush(pending, (g.kickoff + timedelta(hours=delay), g.identifier, g))
    return rows


def availability(records, game_id, team, cutoff):
    """Accept only source-backed, actually retrieved pregame observations.

    Practice designation never implies inactive, and unknown never means healthy.
    These records remain audit inputs: no injury coefficient has been estimated.
    """
    accepted = []
    for r in b.verified_observations(records, game_id, cutoff):
        if r.get('team') != team:
            raise ValueError('Availability team mismatch')
        if r.get('kind') not in {'practice_status', 'game_designation', 'official_inactive', 'confirmed_starting_qb'}:
            raise ValueError('Unsupported availability evidence')
        if not r.get('player_id') or not r.get('status'):
            raise ValueError('Player identity and explicit status required')
        digest = r.get('source_sha256', '')
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Retained source snapshot hash required')
        accepted.append(r)
    return {'observations': accepted, 'coverage': 'verified_observations' if accepted else 'unknown', 'injury_effect_enabled': False}


def run(root, output):
    root, output = Path(root), Path(output)
    protocol = json.loads((root / 'protocol.json').read_text())
    data = root / 'team_stats_2010_2024.csv'
    schedule = root.parent / 'nfl_independent_v1/games_2010_2025.csv'
    if b.sha256(data.read_bytes()) != protocol['stats_sha256'] or b.sha256(schedule.read_bytes()) != protocol['schedule_sha256']:
        raise ValueError('Pinned data hash mismatch')
    games = b.read_games(schedule, last=2024)
    rows = features(games, read_stats(data, games))
    train = [r for r in rows if r['game'].game_type == 'REG' and 2014 <= r['game'].season <= 2022]
    validation = [r for r in rows if r['game'].game_type == 'REG' and 2023 <= r['game'].season <= 2024]
    dev = train + validation
    constant = sum(r['game'].outcome == 'home' for r in train) / len(train)
    results = []
    for penalty in protocol['penalties']:
        model = b.fit(train, penalty, dimension=len(FEATURES)); model['tie_probability'] = b.tie_rate(train)
        summary, _ = b.summarize(validation, model, constant)
        results.append({'penalty': penalty, 'validation': summary})
    selected = min(results, key=lambda r: r['validation']['full_three_outcome_log_loss'])
    model = b.fit(dev, selected['penalty'], dimension=len(FEATURES))
    model.update(version=VERSION, features=FEATURES, tie_probability=b.tie_rate(dev), protocol_sha256=b.sha256((root/'protocol.json').read_bytes()), frozen_at=protocol['frozen_at'], injury_effect_enabled=False)
    baseline_rows = [{**r, 'x': r['x'][:len(b.FEATURES)]} for r in train]
    baseline = b.fit(baseline_rows, .001); baseline['tie_probability'] = b.tie_rate(train)
    base_summary, _ = b.summarize([{**r, 'x': r['x'][:len(b.FEATURES)]} for r in validation], baseline, constant)
    report = {'version': VERSION, 'status': 'development_only_no_edge_claim', 'stats_team_rows': len(games)*2, 'train_games': len(train), 'validation_games': len(validation), 'selection': results, 'selected_penalty': selected['penalty'], 'v1_validation': base_summary, '2025_evaluated': False, 'prospective_predictions': 0, 'actual_wagers': 0}
    output.mkdir(parents=True, exist_ok=False)
    for name, value in [('model.json', model), ('report.json', report)]:
        (output/name).write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')
    return report


def freeze_prediction(path, model, row, generated_at, freeze_at):
    """Create an exclusive prospective artifact; never overwrite forecasts."""
    generated, frozen = b.utc(generated_at), b.utc(freeze_at)
    if frozen != b.utc(model['frozen_at']):
        raise ValueError('Freeze timestamp must match the pinned model')
    cutoff = b.utc(row['cutoff']); game = row['game']
    if not frozen <= generated <= cutoff < game.kickoff or game.kickoff <= frozen:
        raise ValueError('Prospective prediction must be frozen before kickoff')
    if len(row['x']) != len(model['features']) or not all(math.isfinite(x) for x in row['x']):
        raise ValueError('Invalid prospective features')
    evidence = row.get('source_snapshots', [])
    if not evidence:
        raise ValueError('Prospective features require retained source snapshots')
    for source in evidence:
        if not source.get('source_url', '').startswith('https://') or b.utc(source['retrieved_at']) > generated:
            raise ValueError('Source must be retrieved before generation')
        digest = source.get('sha256', '')
        if len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Source snapshot hash required')
    payload = {'game_id': game.identifier, 'kickoff': game.kickoff.isoformat(), 'generated_at': generated.isoformat(), 'cutoff': cutoff.isoformat(), 'model_sha256': b.sha256(b.canonical(model)), 'features': row['x'], 'source_snapshots': evidence, 'probabilities': b.probabilities(model['weights'], row, model['tie_probability']), 'NO_BET': True, 'actual_wagers': 0}
    payload['sha256'] = b.sha256(b.canonical(payload))
    with Path(path).open('x') as stream:
        stream.write(json.dumps(payload, sort_keys=True, indent=2)+'\n')
    return payload


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default='benchmarks/nfl_efficiency_v2')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.root, args.output), indent=2))
