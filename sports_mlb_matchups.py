"""Source-aware MLB batter/pitcher matchup *research*, not betting probabilities.

No network calls, model promotion, wagering, or changes to existing paper ledgers.
All source data is caller supplied and remains explicitly unverified.
"""
import ipaddress
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit


def _time(value, field):
    if not isinstance(value, str):
        raise ValueError(field + ' must be an ISO8601 timestamp with timezone.')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        raise ValueError(field + ' must be an ISO8601 timestamp with timezone.') from None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(field + ' requires a timezone.')
    return parsed.astimezone(timezone.utc)


def _positive_id(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(field + ' must be a positive integer MLB player ID.')
    return value


def _count(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(field + ' must be a nonnegative integer.')
    return value


def _person(raw, field):
    if not isinstance(raw, dict):
        raise ValueError(field + ' must be an object.')
    person_id = _positive_id(raw.get('id'), field + '.id')
    name = raw.get('name')
    if not isinstance(name, str) or not name.strip():
        raise ValueError(field + '.name is required.')
    return {'id': person_id, 'name': name.strip()}


def _source(row, as_of, field):
    url = row.get('source_url')
    if not isinstance(url, str):
        raise ValueError(field + '.source_url must be an HTTPS URL.')
    try:
        parsed = urlsplit(url)
        host = parsed.hostname
        if parsed.scheme != 'https' or not host or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError()
        if host.lower() in {'localhost'} or host.lower().endswith(('.localhost', '.local', '.internal')):
            raise ValueError()
        try:
            if not ipaddress.ip_address(host).is_global:
                raise ValueError()
        except ValueError:
            # Distinguish rejected literal IP addresses from ordinary domains.
            if all(c in '0123456789.:' for c in host):
                raise ValueError()
    except ValueError:
        raise ValueError(field + '.source_url requires a public HTTPS host.') from None
    retrieved = _time(row.get('retrieved_at'), field + '.retrieved_at')
    through = _time(row.get('data_through'), field + '.data_through')
    if retrieved > as_of or through > retrieved or through > as_of:
        raise ValueError(field + ' contains evidence dated after the analysis cutoff.')
    return {'source_url': url, 'retrieved_at': retrieved.isoformat(), 'data_through': through.isoformat(),
            'independently_verified': False}


def _rate(numerator, denominator):
    return round(numerator / denominator, 4) if numerator is not None and denominator else None


def analyze(snapshot):
    """Review a single hitter against one listed starter and possible relievers.

    Returns descriptive historical rates and source/coverage warnings only.
    Does not claim a matchup predicts an upcoming hit or home run.
    """
    if not isinstance(snapshot, dict):
        raise ValueError('snapshot must be an object.')
    game_id = snapshot.get('game_id')
    if not isinstance(game_id, str) or not game_id.isascii() or not game_id.isdigit() or not 5 <= len(game_id) <= 10:
        raise ValueError('game_id must be an official-style MLB game identifier.')
    cutoff = _time(snapshot.get('as_of'), 'as_of')
    event_start = _time(snapshot.get('event_start'), 'event_start')
    if cutoff >= event_start:
        raise ValueError('Pregame research cutoff must precede the scheduled first pitch.')
    hitter = _person(snapshot.get('hitter'), 'hitter')
    starter_raw = snapshot.get('starter')
    starter = _person(starter_raw, 'starter')
    status = starter_raw.get('status', 'unknown')
    if status not in ('probable', 'announced', 'unknown'):
        raise ValueError('starter.status must be probable, announced, or unknown.')
    starter['status'] = status
    bullpen_raw = snapshot.get('bullpen_candidates', [])
    if not isinstance(bullpen_raw, list) or len(bullpen_raw) > 15:
        raise ValueError('bullpen_candidates must be a list of at most 15 pitchers.')
    candidates = {}
    for i, row in enumerate(bullpen_raw):
        p = _person(row, 'bullpen_candidates[' + str(i) + ']')
        availability = row.get('availability', 'unknown')
        if availability not in ('available', 'limited', 'unavailable', 'unknown'):
            raise ValueError('Invalid bullpen availability status.')
        if p['id'] == starter['id'] or p['id'] in candidates:
            raise ValueError('Pitcher IDs must be distinct within a game.')
        p['availability'] = availability
        candidates[p['id']] = p
    matchup_rows = snapshot.get('matchups', [])
    if not isinstance(matchup_rows, list) or len(matchup_rows) > 16:
        raise ValueError('matchups must be a list of at most 16 rows.')
    known_ids = {starter['id'], *candidates}
    seen = set()
    summaries = {}
    for i, row in enumerate(matchup_rows):
        label = 'matchups[' + str(i) + ']'
        if not isinstance(row, dict):
            raise ValueError(label + ' must be an object.')
        if _positive_id(row.get('hitter_id'), label + '.hitter_id') != hitter['id']:
            raise ValueError(label + ' references the wrong hitter.')
        pitcher_id = _positive_id(row.get('pitcher_id'), label + '.pitcher_id')
        if pitcher_id not in known_ids or pitcher_id in seen:
            raise ValueError(label + ' references an unknown or duplicate pitcher.')
        seen.add(pitcher_id)
        pa = _count(row.get('pa'), label + '.pa')
        ab = _count(row.get('ab'), label + '.ab')
        hits = _count(row.get('hits'), label + '.hits')
        hr = _count(row['home_runs'], label + '.home_runs') if 'home_runs' in row else None
        if not hits <= ab <= pa or (hr is not None and hr > hits):
            raise ValueError(label + ' contains inconsistent official counting stats.')
        source = _source(row, cutoff, label)
        summaries[pitcher_id] = {
            'pitcher': starter if pitcher_id == starter['id'] else candidates[pitcher_id],
            'plate_appearances': pa, 'at_bats': ab, 'hits': hits, 'home_runs': hr,
            'historical_batting_average': _rate(hits, ab),
            'historical_hr_per_pa': _rate(hr, pa),
            'small_sample_under_25_pa': pa < 25,
            'source': source,
        }
    def missing(p):
        return {'pitcher': p, 'plate_appearances': None, 'at_bats': None, 'hits': None,
                'home_runs': None, 'historical_batting_average': None,
                'historical_hr_per_pa': None, 'small_sample_under_25_pa': None,
                'source': None}
    starter_view = summaries.get(starter['id'], missing(starter))
    relief = [summaries.get(k, missing(v)) for k, v in candidates.items()]
    observed = sum(x['source'] is not None for x in [starter_view, *relief])
    limitations = [
        'RESEARCH ONLY / NO BET. No event probability, expected value, or wager recommendation is calculated.',
        'Source URLs and timestamps were supplied by the caller, not independently fetched or verified.',
        'Historical batter-versus-pitcher rates are descriptive, often small-sample, and not a calibrated forecast.',
        'Starter status is not a verified first-pitch appearance; reliever candidates are not confirmed participants.',
        'Bullpen exposure, handedness, pitch mix, expected lineup position and weather require separate verified inputs.',
    ]
    if starter_view['source'] is None:
        limitations.append('Missing starter matchup data; no rate inferred.')
    if not candidates:
        limitations.append('No bullpen candidates supplied; relief-pitcher matchups are unknown.')
    elif any(x['source'] is None for x in relief):
        limitations.append('Missing one or more reliever matchup records; their rates remain unknown.')
    return {
        'game_id': game_id, 'as_of': cutoff.isoformat(), 'event_start': event_start.isoformat(),
        'hitter': hitter, 'starter_matchup': starter_view, 'reliever_matchups': relief,
        'coverage': {'expected_pitchers': 1 + len(candidates), 'pitchers_with_sourced_stats': observed},
        'decision': 'RESEARCH ONLY - NO BET', 'estimated_hit_probability': None,
        'estimated_home_run_probability': None, 'joint_parlay_probability': None,
        'expected_value': None, 'limitations': limitations,
    }


def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Offline sourced MLB matchup research; NO BET')
    parser.add_argument('--input', required=True, help='Path to JSON snapshot (not a live feed)')
    args = parser.parse_args()
    with open(args.input, encoding='utf-8') as handle:
        snapshot = json.load(handle)
    json.dump(analyze(snapshot), sys.stdout, indent=2, allow_nan=False)
    print()


if __name__ == '__main__':
    main()
