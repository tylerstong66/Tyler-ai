"""Read-only coverage audit from saved official schedules and pregame evidence."""
import csv
import hashlib
import io
import json
from collections import defaultdict
from datetime import timedelta
from pathlib import Path
import sports_benchmark_review as r
import sports_market_evidence as m

VERSION = 'prospective-coverage-v1'
LIMITATION = ('Coverage is limited to retained official schedule snapshots since each cohort began; '
              'it cannot prove that a source returned every game or recover uncaptured runs. '
              'Capture gaps are observed intervals, not proof of scheduler failure. '
              'Later archived pregame prices are evidence only: they never backfill saved forecasts '
              'or enrollment-time market metrics. New follow-up quotes must be recorded before start, '
              'remain separate, and are not added to existing scored comparisons. NO BET / actual wagers $0.')


def pregame_readiness(schedule, predictions, events, followups, as_of):
    """Check the next 24h against only the latest audited capture's scoreboard.

    Historical quotes cannot make a missing latest event look ready. This is
    read-only snapshot evidence, not live availability or forecast enrollment.
    """
    rows = []
    for identifier, item in sorted(schedule.items()):
        game = item['game']; kickoff = r.utc(game['kickoff'])
        if not as_of < kickoff <= as_of+timedelta(hours=24):
            continue
        pred = predictions.get(identifier); issues = []
        if game.get('state') != 'pre': issues.append('official_game_not_pregame')
        frozen_start_discrepancy = None
        if pred is None:
            issues.append('forecast_not_enrolled')
        else:
            frozen_start = r.utc(pred['kickoff'])
            start_changed = frozen_start != kickoff
            team_changed = any(
                pred.get(side+'_id', pred[side]) != game.get(side+'_id', game[side])
                for side in ('home', 'away'))
            if start_changed or team_changed:
                issues.append('official_identity_differs_from_forecast')
            if start_changed:
                issues.append('saved_start_differs_from_latest_official_start')
                frozen_start_discrepancy = {
                    'saved_forecast_start_utc': frozen_start.isoformat(),
                    'latest_official_start_utc': kickoff.isoformat(),
                    'latest_minus_saved_minutes': (kickoff-frozen_start).total_seconds()/60,
                    'action': 'no_regrade_or_rewrite_of_frozen_forecast',
                }
            if team_changed:
                issues.append('saved_teams_differ_from_latest_official_teams')
        matches = [(at, event) for at, event in events if
                   (event['event_id'] == pred['event_id'] if pred else
                    r.utc(event['kickoff']) == kickoff and all(
                        event.get(side+'_name', event[side]) == game.get(side+'_name', game[side])
                        for side in ('home', 'away')))]
        quote_at = None; priced_now = False
        if len(matches) != 1:
            issues.append('latest_scoreboard_event_missing_or_ambiguous')
        else:
            at, event = matches[0]; quote_at = at.isoformat()
            if event.get('state') != 'pre' or event.get('completed') is not False:
                issues.append('latest_scoreboard_not_pregame')
            if r.utc(event['kickoff']) != kickoff or (pred and any(event[side] != pred[side] for side in ('home', 'away'))):
                issues.append('latest_scoreboard_identity_conflict')
            if event.get('odds'):
                m.market(event['odds'][0])
                priced_now = True
            else: issues.append('latest_scoreboard_market_pair_missing')
        enrollment_priced = pred is not None and pred.get('market') is not None
        followup = identifier in followups
        if pred and not enrollment_priced and not followup:
            issues.append('pregame_market_evidence_not_recorded')
        rows.append({'game_id': identifier, 'home': game.get('home_name', game['home']),
                     'away': game.get('away_name', game['away']), 'kickoff': game['kickoff'],
                     'enrolled': pred is not None, 'enrollment_priced': enrollment_priced,
                     'separate_followup_recorded': followup, 'latest_scoreboard_priced': priced_now,
                     'latest_scoreboard_observed_at': quote_at,
                     'saved_vs_latest_official_start': frozen_start_discrepancy,
                     'issues': issues, 'ready': not issues})
    return {'as_of_evidence_at': as_of.isoformat(), 'window_hours': 24,
            'observed_games': len(rows), 'ready_games': sum(row['ready'] for row in rows),
            'status': ('no_upcoming_games_observed' if not rows else
                       'ready_as_of_snapshot' if all(row['ready'] for row in rows) else 'attention'),
            'games': rows, 'limitation': 'Latest audited capture only; source changes after retrieval are unknown. This does not certify future collection or wagering readiness.'}


def stamp(folder):
    from datetime import datetime, timezone
    return datetime.strptime(folder.name, '%Y%m%dT%H%M%S%fZ').replace(tzinfo=timezone.utc)


def audit(root, sport, models, base=Path('.')):
    predictions, results = r.load_rows(root, sport, models)
    result_ids = {row['game_id'] for row in results}
    start_file = root/('config.json' if sport == 'NFL' else 'model.json')
    start = r.utc(json.loads(start_file.read_text())['started_at' if sport == 'NFL' else 'frozen_at'])
    snapshots, schedule, timeline = {}, {}, defaultdict(list)
    captures, exclusions, errors, input_files = [], [], [], []
    latest_decisions = []; saved_decisions = {}; latest_events = []; audited_paths = []
    observed, schedule_times = [], []

    def read_source(source):
        path = base/source['path']
        if path not in snapshots:
            content = path.read_bytes()
            snapshots[path] = (hashlib.sha256(content).hexdigest(), content)
        digest, content = snapshots[path]
        if digest != source['sha256']:
            raise ValueError('Retained snapshot hash mismatch: '+str(path))
        return content

    manifests = sorted((root/'captures').glob('*/manifest.json'))
    if not manifests:
        raise ValueError('No retained collection manifests')
    for path in manifests:
        manifest = json.loads(path.read_text())
        # Ignore explicitly incomplete snapshots; do not claim them as completed.
        if manifest.get('collection_completed') is False:
            errors.append({'capture': path.parent.name, 'error': 'collection_incomplete'})
            continue
        capture_time = stamp(path.parent)
        audited_paths.append(path); latest_events = []
        captures.append(capture_time)
        input_files.append({'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        enrollment = path.parent/'enrollment.json'
        records = manifest.get('excluded', [])
        if enrollment.exists():
            latest_decisions = json.loads(enrollment.read_text()).get('decisions', [])
            for decision in latest_decisions:saved_decisions[str(decision['game_id'])] = decision
            records = list({r.digest(record):record for record in records+json.loads(enrollment.read_text()).get('excluded', [])}.values())
            input_files.append({'path': str(enrollment.relative_to(root)), 'sha256': hashlib.sha256(enrollment.read_bytes()).hexdigest()})
        exclusions += [{**record, 'capture': path.parent.name} for record in records]
        errors += [{**record, 'capture': path.parent.name} for record in manifest.get('errors', [])]
        for source in manifest.get('sources', []):
            url, at = source['source_url'], r.utc(source['retrieved_at'])
            observed.append(at)
            if 'scoreboard' in url:
                rows = json.loads(read_source(source))
                for event in rows:
                    timeline[str(event['event_id'])].append((at, event, source))
                    latest_events.append((at, event))
                continue
            is_nfl = sport == 'NFL' and '/nfldata/' in url and source['path'].endswith('.csv')
            is_two_way = sport != 'NFL' and ('api-web.nhle.com/v1/schedule/' in url or
                         'club-schedule-season/' in url or 'statsapi.mlb.com/api/v1/schedule?' in url)
            if not (is_nfl or is_two_way):
                continue
            content = read_source(source)
            schedule_times.append(at)
            if is_nfl:
                # The retained CSV already excludes preseason from the cohort.
                from sports_prospective_test import game_from_row
                rows = []
                for row in csv.DictReader(io.StringIO(content.decode())):
                    if row['game_type'] != 'REG':
                        continue
                    game = game_from_row(row)
                    rows.append({'game_id': game.identifier, 'home': game.home, 'away': game.away,
                                 'kickoff': game.kickoff.isoformat(),
                                 'state': 'post' if row['home_score'] != '' and row['away_score'] != '' else 'pre'})
            else:
                rows = json.loads(content)
            for game in rows:
                identifier = str(game['game_id'])
                item = schedule.setdefault(identifier, {'observations': []})
                item['observations'].append((at, game))
                if 'seen_at' not in item or at >= item['seen_at']:
                    item.update({'game': game, 'seen_at': at})
    if not observed or not schedule_times:
        raise ValueError('Official schedule evidence unavailable')
    as_of = max(observed)
    games, market_gaps = [], []
    for identifier, item in sorted(schedule.items()):
        game = item['game']; kickoff = r.utc(game['kickoff'])
        if kickoff < start or kickoff > as_of+timedelta(hours=24):
            continue
        pred = predictions.get(identifier)
        opportunities = sorted({at for at, seen in item['observations']
                                if max(start, r.utc(seen['kickoff'])-timedelta(hours=24)) <= at < r.utc(seen['kickoff'])
                                and seen.get('state') == 'pre'})
        reasons = sorted({entry['reason'] for entry in exclusions if str(entry.get('game_id')) == identifier})
        if pred:
            status = 'enrolled'
        elif saved_decisions.get(identifier, {}).get('decision') == 'frozen_100_forecast_cap':
            status = 'outside_frozen_100_forecast_cap'
        elif kickoff > as_of:
            status = 'awaiting_enrollment'
        elif game.get('state') not in ('pre', 'post'):
            status = 'unverified_or_not_normally_scheduled'
        elif opportunities:
            status = 'missed_despite_pregame_schedule_observation'
        else:
            status = 'missed_without_pregame_schedule_observation_in_window'
        games.append({'game_id': identifier, 'home': game.get('home_name', game['home']),
                      'away': game.get('away_name', game['away']), 'kickoff': game['kickoff'], 'status': status,
                      'started_by_as_of': kickoff <= as_of, 'pregame_schedule_observations_in_window': len(opportunities),
                      'first_observed_in_window': opportunities[0].isoformat() if opportunities else None,
                      'recorded_at': pred['recorded_at'] if pred else None,
                      'lead_hours': (kickoff-r.utc(pred['recorded_at'])).total_seconds()/3600 if pred else None,
                      'exclusion_reasons': reasons, 'latest_saved_decision': saved_decisions.get(identifier)})
    for identifier, pred in sorted(predictions.items()):
        if pred.get('market') is not None:
            continue
        events = timeline[pred['event_id']]
        def matches(event):
            return all(event.get(key) == pred[key] for key in ('event_id', 'home', 'away', 'kickoff'))
        enrollment = [(at, e, s) for at, e, s in events if at == r.utc(pred['market_observed_at']) and matches(e)]
        # Archived reduced snapshots do not expose raw bookmaker schema. Do not
        # invent a provider outage or assume raw prices were absent.
        diagnosis = (enrollment[0][1].get('odds_diagnostics', {'status': 'no_usable_pair_in_reduced_snapshot_raw_schema_unavailable'})
                     if len(enrollment) == 1 else {'status': 'enrollment_scoreboard_evidence_unavailable_or_ambiguous'})
        later = sorted([(at, e, s) for at, e, s in events
                        if r.utc(pred['recorded_at']) <= at < r.utc(pred['kickoff']) and matches(e)
                        and e['state'] == 'pre' and e.get('completed') is False and e.get('odds')], key=lambda x: x[0])
        row = {'game_id': identifier, 'home': pred['home'], 'away': pred['away'], 'kickoff': pred['kickoff'],
               'settled': identifier in result_ids, 'forecast_recorded_at': pred['recorded_at'],
               'enrollment_diagnosis': diagnosis, 'later_archived_pregame_quote': None}
        if later:
            at, event, source = later[0]
            row['later_archived_pregame_quote'] = {'observed_at': at.isoformat(), 'market': m.market(event['odds'][0]),
                                                  'source_snapshot': source, 'usage': 'historical_evidence_only_not_backfilled'}
        market_gaps.append(row)
    followups = []
    for path in sorted((root/'market_followups').glob('*.json')):
        data = json.loads(path.read_text())
        if data['game_id'] not in predictions or predictions[data['game_id']].get('market') is not None:
            raise ValueError('Follow-up requires a saved unpriced forecast')
        if path.stem != data['game_id']:
            raise ValueError('Follow-up filename differs from game ID')
        m.verify_quote(data, predictions[data['game_id']], base)
        followups.append({'game_id': data['game_id'], 'observed_at': data['observed_at'], 'recorded_at': data['recorded_at']})
    capture_gaps = sorted([{'from': a.isoformat(), 'to': b.isoformat(), 'hours': (b-a).total_seconds()/3600}
                           for a, b in zip(captures, captures[1:])], key=lambda x: x['hours'], reverse=True)
    due = [g for g in games if g['started_by_as_of']]
    missing = [g for g in due if g['status'].startswith('missed_')]
    # Include failed attempts explicitly; they cannot prove successful completion.
    failed_attempts = [json.loads(p.read_text()) for p in sorted((root/'errors').glob('*.json'))]
    settled_priced = sum(identifier in result_ids and pred.get('market') is not None for identifier, pred in predictions.items())
    decisive_paired = sum(row['game_id'] in predictions and row['outcome'] != 'tie' and predictions[row['game_id']].get('market') is not None for row in results)
    leads = [g['lead_hours'] for g in games if g['lead_hours'] is not None]
    readiness = pregame_readiness(schedule, predictions, latest_events,
                                  {row['game_id'] for row in followups}, as_of)
    return {'sport': sport, 'input_integrity': 'verified', 'report_version': VERSION,
            'cohort_started_at': start.isoformat(), 'as_of_evidence_at': as_of.isoformat(),
            'latest_official_schedule_observed_at': max(schedule_times).isoformat(),
            'saved': len(predictions), 'settled': len(results), 'pending': len(predictions)-len(results),
            'enrollment_priced': sum(p.get('market') is not None for p in predictions.values()),
            'settled_enrollment_priced': settled_priced, 'decisive_market_paired': decisive_paired,
            'settled_ties_with_prices': settled_priced-decisive_paired,
            'followup_quotes_separate_from_original_metrics': followups,
            'started_schedule_games_in_scope': len(due),
            'started_schedule_games_enrolled': sum(g['status'] == 'enrolled' for g in due),
            'observed_missing_started_games': missing, 'games': games, 'market_gaps': market_gaps,
            'pregame_readiness': readiness,
            'capture_count': len(captures), 'largest_capture_intervals': capture_gaps[:5],
            'minimum_forecast_lead_hours': min(leads) if leads else None,
            'latest_capture': audited_paths[-1].parent.name, 'latest_attempted_capture': manifests[-1].parent.name,
            'latest_enrollment_decisions': latest_decisions, 'saved_exclusions': exclusions,
            'saved_collector_errors': errors, 'saved_failed_attempts': failed_attempts,
            'completion_note': 'Saved NFL manifests before coverage-v1 lack a completion flag; successful workflow corroboration remains required.' if sport == 'NFL' else 'Only manifests without an explicit incomplete state are audited; legacy manifests are retained.',
            'input_digest': r.digest({'files': input_files, 'predictions': {k: v['sha256'] for k, v in predictions.items()},
                                     'results': results, 'followups': followups}),
            'NO_BET': True, 'actual_wagers': 0, 'limitation': LIMITATION}


def render(data):
    lines = ['# '+data['sport']+' forecast and odds coverage', '', '**NO BET — actual wagers $0.**', '']
    if data['input_integrity'] != 'verified':
        return '\n'.join(lines+['Audit unavailable: '+data['error'], '', LIMITATION, ''])
    lines += [f"Evidence through **{data['as_of_evidence_at']}**; cohort began {data['cohort_started_at']}.", '',
              '| Coverage | Games |', '|---|---:|',
              f"| Recorded / settled / pending | {data['saved']} / {data['settled']} / {data['pending']} |",
              f"| Started games in retained official schedules / enrolled | {data['started_schedule_games_in_scope']} / {data['started_schedule_games_enrolled']} |",
              f"| Observed missing started games | {len(data['observed_missing_started_games'])} |",
              f"| Enrollment-time priced forecasts | {data['enrollment_priced']} / {data['saved']} |",
              f"| Settled with enrollment prices / decisive market-paired | {data['settled_enrollment_priced']} / {data['decisive_market_paired']} |",
              f"| Separate later quotes recorded prospectively | {len(data['followup_quotes_separate_from_original_metrics'])} |", '',
              *(['A priced NFL tie is excluded only from binary decisive market comparisons.', ''] if data['sport'] == 'NFL' else []),
              '## Missing enrollment-time prices', '',
              '| Game | Matchup | Settled | Enrollment evidence | First later archived pregame pair (UTC) |',
              '|---|---|---|---|---|']
    for row in data['market_gaps']:
        later = row['later_archived_pregame_quote']
        lines.append(f"| {row['game_id']} | {row['away']} at {row['home']} | {row['settled']} | {row['enrollment_diagnosis']['status'].replace('_', ' ')} | {later['observed_at'] if later else 'Unavailable'} |")
    if not data['market_gaps']:
        lines += ['| None | — | — | — | — |']
    lines += ['', 'Later archived pairs explain timing gaps; they are not retrospectively inserted into forecasts or scored market comparisons.', '',
              '## Next 24-hour pregame readiness', '',
              f"As of retained evidence: {data['pregame_readiness']['as_of_evidence_at']}. "
              f"Ready: {data['pregame_readiness']['ready_games']} / {data['pregame_readiness']['observed_games']} observed games. "
              f"Status: {data['pregame_readiness']['status']}.", '',
              '| Game | Matchup | Enrollment priced | Separate follow-up | Latest pair | Issues |',
              '|---|---|---|---|---|---|']
    for row in data['pregame_readiness']['games']:
        lines.append(f"| {row['game_id']} | {row['away']} at {row['home']} | {row['enrollment_priced']} | {row['separate_followup_recorded']} | {row['latest_scoreboard_priced']} | {', '.join(row['issues']) or 'None'} |")
    lines += ['', data['pregame_readiness']['limitation'], '',
              '## Schedule audit', '', '| Game | Matchup | Start (UTC) | Decision | Exclusion evidence |', '|---|---|---|---|---|']
    for row in data['games']:
        lines.append(f"| {row['game_id']} | {row['away']} at {row['home']} | {row['kickoff']} | {row['status'].replace('_', ' ')} | {', '.join(row['exclusion_reasons']) or '—'} |")
    lines += ['', '## Capture freshness', '', f"Audited capture manifests: {data['capture_count']}. Latest: `{data['latest_capture']}`.", '',
              '| From (UTC) | To (UTC) | Hours between audited captures |', '|---|---|---:|']
    for gap in data['largest_capture_intervals']:
        lines.append(f"| {gap['from']} | {gap['to']} | {gap['hours']:.2f} |")
    lines += ['', 'Historical exclusions and collector errors, including resolved ones, are retained in [COVERAGE.json](COVERAGE.json); these are not all current errors.', '',
              '[Scoring review](REVIEW.md) · [Machine-readable coverage](COVERAGE.json)', '', LIMITATION, '']
    return '\n'.join(lines)


def run(base=Path('.')):
    base = Path(base); reports = []
    for sport, (folder, models) in r.COHORTS.items():
        root = base/folder
        try:
            data = audit(root, sport, models, base)
        except (ValueError, KeyError, TypeError, OSError) as error:
            data = {'sport': sport, 'input_integrity': 'error', 'report_version': VERSION, 'error': str(error), 'NO_BET': True, 'actual_wagers': 0}
        r.write(root/'COVERAGE.json', data)
        (root/'COVERAGE.md').write_text(render(data)); reports.append(data)
    lines = ['# Forecast and odds coverage audit', '', '**NO BET — actual wagers $0.**', '',
             '| Cohort | Saved | Settled | Market-paired | Observed missing started games | Upcoming ready / observed | Report |', '|---|---:|---:|---:|---:|---|---|']
    links = {'NFL': '../nfl_prospective_v2/COVERAGE.md', 'NHL': 'nhl/COVERAGE.md', 'MLB': 'mlb/COVERAGE.md'}
    for data in reports:
        if data['input_integrity'] == 'verified':
            ready = data.get('pregame_readiness')
            cell = f"{ready['ready_games']} / {ready['observed_games']} ({ready['status']})" if ready else 'Unavailable'
            lines.append(f"| {data['sport']} | {data['saved']} | {data['settled']} | {data['decisive_market_paired']} | {len(data['observed_missing_started_games'])} | {cell} | [Audit]({links[data['sport']]}) |")
        else:
            lines.append(f"| {data['sport']} | Unavailable | Unavailable | Unavailable | Unavailable | Unavailable | [Integrity error]({links[data['sport']]}) |")
    lines += ['', 'Upcoming checks cover the next 24 hours as of each report\'s retained evidence timestamp; they do not certify live source availability or wagering readiness.', '', LIMITATION, '', '[Scoring reviews](REVIEW_ALL.md) · [Coverage methodology](COVERAGE_METHOD.md)', '']
    (base/'benchmarks/two_way_prospective/COVERAGE_ALL.md').write_text('\n'.join(lines))
    return reports


if __name__ == '__main__':
    reports = run()
    print(json.dumps([{'sport': d['sport'], 'integrity': d['input_integrity'], 'error': d.get('error')} for d in reports]))
    raise SystemExit(0 if all(d['input_integrity'] == 'verified' for d in reports) else 1)
