"""Append-only prior-season FBS reference features observed before target kickoff."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import hashlib
import json
import re

import sports_expansion_observer as source
import sports_expansion_audit as provider_audit
import sports_expansion_historical_capture as history
import sports_historical_college_features as reference_features
import sports_ncaa_espn_identity as identity
import sports_ncaa_espn_crosswalk_receipts as receipts
import sports_ncaa_official_source as ncaa

ROOT = Path('benchmarks/fbs_pregame_reference_features_v1/records')
PROTOCOL = {'schema': 'fbs-pregame-reference-feature-protocol-v1', 'league': 'NCAAF_FBS',
    'target_season': 2026, 'reference_season': 2025, 'reference_split': 'validation',
    'reference_games_per_team': 4, 'maximum_schedule_source_age_hours': 12,
    'target_season_stage': 2, 'reference_scope': 'LAST_FOUR_CORROBORATED_PREVIOUS_SEASON_RESULTS_AVAILABLE_AT_FREEZE',
    'team_identity': 'EXACT_ESPN_TEAM_ID_AND_NORMALIZED_PROVIDER_DISPLAY_NAME',
    'feature_fields': ['prior_games', 'mean_points_for', 'mean_points_against', 'mean_margin', 'days_since_latest_prior_start'],
    'not_a_prediction': True, 'current_season_form_not_modeled': True,
    'prior_season_roster_and_coach_changes_not_modeled': True}
PROTOCOL_SHA256 = '230e8833affe1346fe2e349e92f2c3bc64ac1db85fe5b16bb236ab8d9cde721e'


class IneligibleSourceGame(ValueError): pass


def digest(value): return hashlib.sha256(source.canonical(value)).hexdigest()


def _read(path, limit=8_500_000):
    if path.parent.is_symlink() or path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError('Missing or invalid bounded FBS source file')
    return path.read_bytes()


def _reference(base, now):
    raw = _read(base/ROOT.parent/'protocol.json', 1_000_000)
    if digest(PROTOCOL) != PROTOCOL_SHA256 or hashlib.sha256(raw).hexdigest() != PROTOCOL_SHA256:
        raise ValueError('FBS feature protocol differs from frozen cohort')
    report = reference_features.build(base, league='NCAAF_FBS', split='validation', now=now)
    cache = {}; named = {}
    for key, item in report['source_game_index'].items():
        row = item['source_record']; names = []
        for ref in row['source_agreement']['espn_receipts']:
            day = ref['source_date']
            if day not in cache:
                path = base/history.ROOT/'sources/NCAAF_FBS/validation'/(day+'.receipt.json')
                content = _read(path); saved = json.loads(content)
                cache[day] = (hashlib.sha256(content).hexdigest(), saved)
            sha, saved = cache[day]
            if sha != ref['receipt_sha256'] or saved['original_response_sha256'] != ref['response_sha256']:
                raise ValueError('Original FBS reference receipt changed during replay')
            matches = [e for e in saved['parsed_provider_scoreboard']['games'] if e['game_id'] == key]
            if len(matches) != 1:
                raise ValueError('Missing original FBS reference team name source')
            e = matches[0]
            if any(e[side+'_team_id'] != row[side+'_team_id'] for side in ('home', 'away')):
                raise ValueError('FBS reference team ID changed during replay')
            names.append({side: e[side+'_name'] for side in ('home', 'away')})
        if not names or any(n != names[0] for n in names[1:]):
            raise ValueError('Original FBS reference provider name changed')
        named[key] = {**row, 'provider_team_names': names[0]}
    return {'source_feature_report_sha256': digest(report), 'source_records': named,
            'historical_school_identity_manifest_sha256': report['school_identity_manifest_sha256']}


def _snapshot(base, stamp):
    if not isinstance(stamp, str) or not receipts.STAMP.fullmatch(stamp):
        raise ValueError('Invalid FBS crosswalk capture identifier')
    first = _read(base/identity.ROOT/'captures'/stamp/'manifest.json')
    declared = json.loads(first)
    for kind, root in (('ncaa', ncaa.ROOT), ('espn', source.ROOT)):
        linked = declared[kind+'_capture']
        if not isinstance(linked, str) or not receipts.STAMP.fullmatch(linked):
            raise ValueError('Invalid linked FBS source capture')
        folder = base/root/'captures'/linked
        manifest = json.loads(_read(folder/'manifest.json'))
        for snap in manifest['snapshots']:
            filename = snap['source_file' if kind == 'ncaa' else 'compressed_file']
            if (not isinstance(filename, str) or Path(filename).name != filename
                    or '..' in filename or not filename.endswith('.json.gz')):
                raise ValueError('Invalid bounded FBS source response filename')
            _read(folder/filename)
    receipts.verify(base, stamp)
    path = base/identity.ROOT/'captures'/stamp/'manifest.json'
    raw = _read(path); saved = json.loads(raw)
    if raw != first: raise ValueError('FBS crosswalk changed during replay')
    at = source.utc(saved['recorded_at_utc'])
    if at.strftime('%Y%m%dT%H%M%S%fZ') != stamp or type(saved.get('actual_wagers')) is not int:
        raise ValueError('Invalid FBS crosswalk chronology or guard type')
    manifests = {}; rows = {}; statuses = {}
    for kind, root in (('ncaa', ncaa.ROOT), ('espn', source.ROOT)):
        folder = base/root/'captures'/saved[kind+'_capture']
        original = _read(folder/'manifest.json'); manifest = json.loads(original)
        if hashlib.sha256(original).hexdigest() != saved[kind+'_manifest_sha256']:
            raise ValueError('FBS linked source changed during replay')
        if (manifest.get('NO_BET') is not True or type(manifest.get('actual_wagers')) is not int
                or manifest['actual_wagers'] != 0 or any(manifest.get(k) is not False
                    for k in ('forecasting_enabled', 'model_training_enabled', 'promotion_allowed'))):
            raise ValueError('FBS source research guards changed')
        observed = source.utc(manifest['recorded_at_utc'])
        if observed.strftime('%Y%m%dT%H%M%S%fZ') != folder.name or observed > at:
            raise ValueError('FBS linked source follows original crosswalk')
        if kind == 'ncaa':
            for snap in manifest['snapshots']:
                if snap['league'] != 'NCAAF_FBS': continue
                if not re.fullmatch(r'week-\d{2}', snap['window']):
                    raise ValueError('Invalid FBS current NCAA request week')
                if snap['source_url'] != ncaa.graph_url('NCAAF_FBS', year=2026, week=int(snap['window'][5:])):
                    raise ValueError('FBS source crossed fixed target season')
            games = identity.verify_ncaa(folder, manifest)
            rows[kind] = {r['ncaa_game_id']: r for r in games if r['league'] == 'NCAAF_FBS'}
        else:
            provider_audit.audit_capture(folder/'manifest.json')
            games = identity.verify_espn(folder, manifest)
            for snap in manifest['snapshots']:
                if snap['league'] != 'NCAAF_FBS': continue
                raw_events = provider_audit.bounded_gzip_read(_read(folder/snap['compressed_file']))
                for event in json.loads(raw_events)['events']:
                    statuses.setdefault(str(event['id']), set()).add(event.get('status', {}).get('type', {}).get('name'))
            rows[kind] = {r['espn_game_id']: r for r in games if r['league'] == 'NCAAF_FBS'}
        manifests[kind] = manifest
    return {'stamp': stamp, 'manifest': saved, 'manifest_sha256': hashlib.sha256(raw).hexdigest(),
            'source_manifests': manifests, 'rows': rows, 'espn_status_names': statuses}


def _record(snapshot, matched, reference, freeze):
    manifest = snapshot['manifest']; n = snapshot['rows']['ncaa'][matched['ncaa_game_id']]
    e = snapshot['rows']['espn'][matched['espn_game_id']]
    for value in (n['ncaa_game_id'], e['espn_game_id'], e['home_team_id'], e['away_team_id']):
        if not isinstance(value, str) or not re.fullmatch(r'[1-9][0-9]{0,11}', value):
            raise ValueError('Invalid positive FBS source identity')
    matches = [r for r in manifest['report']['matched'] if r['league'] == 'NCAAF_FBS']
    if (sum(r['ncaa_game_id'] == n['ncaa_game_id'] for r in matches) != 1
            or sum(r['espn_game_id'] == e['espn_game_id'] for r in matches) != 1):
        raise IneligibleSourceGame('NON_BIJECTIVE_SOURCE_GAME_IDENTITY')
    starts = [datetime.fromtimestamp(int(n['source_start_time_epoch']), timezone.utc), source.utc(e['scheduled_start_utc'])]
    if not all(datetime(2026, 8, 1, tzinfo=timezone.utc) <= s < datetime(2027, 2, 1, tzinfo=timezone.utc) for s in starts):
        raise IneligibleSourceGame('OUTSIDE_FIXED_FBS_TARGET_SEASON')
    if n['source_state'] != 'P' or n['provider_reported_final'] is not False or e['state'] != 'pre' or e['provider_completed'] is not False:
        raise IneligibleSourceGame('BOTH_SOURCES_NOT_PREGAME')
    if snapshot['espn_status_names'].get(e['espn_game_id']) != {'STATUS_SCHEDULED'}:
        raise IneligibleSourceGame('PROVIDER_STATUS_NOT_EXPLICITLY_SCHEDULED')
    if e['season_stage'] != PROTOCOL['target_season_stage']:
        raise IneligibleSourceGame('NOT_REGULAR_SEASON_TARGET')
    if freeze >= min(starts): raise IneligibleSourceGame('SOURCE_SAVED_START_ALREADY_REACHED')
    observed = [source.utc(snapshot['source_manifests'][kind]['recorded_at_utc']) for kind in ('ncaa', 'espn')]
    if max(*observed, source.utc(manifest['recorded_at_utc'])) > freeze:
        raise ValueError('FBS source or crosswalk observed after feature freeze')
    if any(freeze-t > timedelta(hours=PROTOCOL['maximum_schedule_source_age_hours']) for t in observed):
        raise IneligibleSourceGame('SCHEDULE_SOURCE_TOO_OLD_AT_FREEZE')
    summaries = {}
    for side in ('home', 'away'):
        team_id = e[side+'_team_id']; selected = []
        for row in reference['source_records'].values():
            if team_id not in (row['home_team_id'], row['away_team_id']): continue
            if row['league'] != 'NCAAF_FBS' or row['split'] != 'validation':
                raise ValueError('FBS reference crossed fixed sport/season split')
            early, late, available = reference_features._event(row, 'NCAAF_FBS', 'validation')
            if available > freeze or late >= freeze: continue
            selected.append((early, row['espn_game_id'], row))
        selected = sorted(selected)[-PROTOCOL['reference_games_per_team']:]
        if len(selected) != PROTOCOL['reference_games_per_team']:
            raise IneligibleSourceGame('INSUFFICIENT_CORROBORATED_REFERENCE_HISTORY')
        if len({r['espn_game_id'] for _, _, r in selected}) != len(selected):
            raise ValueError('Duplicate original FBS reference game')
        points = []
        for _, _, row in selected:
            own = 'home' if row['home_team_id'] == team_id else 'away'; other = 'away' if own == 'home' else 'home'
            name = row['provider_team_names'][own]
            if not isinstance(name, str) or identity.name(name) != identity.name(e[side+'_name']):
                raise IneligibleSourceGame('REFERENCE_PROVIDER_NAME_DIFFERS_FROM_CURRENT_TEAM_ID')
            points.append((row[own+'_score'], row[other+'_score']))
        count = len(selected)
        summaries[side] = {'team_id': team_id, 'provider_team_name': e[side+'_name'], 'prior_games': count,
            'mean_points_for': sum(a for a, _ in points)/count,
            'mean_points_against': sum(b for _, b in points)/count,
            'mean_margin': sum(a-b for a, b in points)/count,
            'days_since_latest_prior_start': (min(starts)-selected[-1][0]).total_seconds()/86400,
            'reference_source_rows': [{'source_row_sha256': digest(r), 'source_row': r} for _, _, r in selected]}
    return {'schema': 'tyler-fbs-pregame-reference-feature-observation-v1', 'league': 'NCAAF_FBS',
            'target_season': 2026, 'ncaa_game_id': n['ncaa_game_id'], 'espn_game_id': e['espn_game_id'],
            'frozen_at_utc': freeze.isoformat(), 'ncaa_saved_start_utc': starts[0].isoformat(),
            'espn_saved_start_utc': starts[1].isoformat(), 'scheduled_start_utc': min(starts).isoformat(),
            'home_team_id': e['home_team_id'], 'away_team_id': e['away_team_id'],
            'crosswalk_capture': snapshot['stamp'], 'crosswalk_manifest_sha256': snapshot['manifest_sha256'],
            'ncaa_capture': manifest['ncaa_capture'], 'espn_capture': manifest['espn_capture'],
            'ncaa_manifest_sha256': manifest['ncaa_manifest_sha256'], 'espn_manifest_sha256': manifest['espn_manifest_sha256'],
            'current_ncaa_source_row_sha256': digest(n), 'current_espn_source_row_sha256': digest(e),
            'protocol_sha256': PROTOCOL_SHA256, 'reference_report_sha256': digest(reference),
            'reference_features': summaries, 'not_a_prediction': True,
            'independent_publication_time_attested': False, 'institutional_membership_certified': False,
            'current_season_form_not_modeled': True, 'prior_season_roster_and_coach_changes_not_modeled': True,
            'forecasting_enabled': False, 'model_training_enabled': False, 'historical_evaluation_enabled': False,
            'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


def _existing(base, now, reference, snapshots):
    existing = {}; ncaa_ids = set(); root = base/ROOT
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or (path.is_file() and path.parent != root):
            raise ValueError('Unplanned FBS feature record input')
        if not path.is_file(): continue
        if not re.fullmatch(r'[1-9][0-9]{0,11}\.json', path.name):
            raise ValueError('Invalid FBS feature record filename')
        raw = _read(path, 1_000_000); saved = json.loads(raw); row = saved['record']
        if raw != source.canonical(saved) or saved.get('record_sha256') != digest(row) or path.stem != row['espn_game_id']:
            raise ValueError('FBS feature content digest or identity changed')
        freeze = source.utc(row['frozen_at_utc'])
        if freeze > now: raise ValueError('Future-dated FBS feature freeze')
        stamp = row['crosswalk_capture']
        if stamp not in snapshots: snapshots[stamp] = _snapshot(base, stamp)
        snapshot = snapshots[stamp]
        matches = [m for m in snapshot['manifest']['report']['matched'] if m['league'] == 'NCAAF_FBS'
                   and m['espn_game_id'] == row['espn_game_id'] and m['ncaa_game_id'] == row['ncaa_game_id']]
        if len(matches) != 1: raise ValueError('FBS feature lacks original unique crosswalk')
        if source.canonical(_record(snapshot, matches[0], reference, freeze)) != source.canonical(row):
            raise ValueError('FBS feature differs from original source replay')
        if row['ncaa_game_id'] in ncaa_ids: raise ValueError('Duplicate original FBS NCAA identity')
        existing[row['espn_game_id']] = row; ncaa_ids.add(row['ncaa_game_id'])
    return existing


def inspect(base=Path('.'), *, now=None, collect=False):
    base = Path(base); now = now or datetime.now(timezone.utc)
    if now.tzinfo is None or type(collect) is not bool:
        raise ValueError('Aware FBS audit clock and explicit collection mode required')
    reference = _reference(base, now); snapshots = {}; existing = _existing(base, now, reference, snapshots)
    prepared = []; pending = []; captures = sorted((base/identity.ROOT/'captures').glob('*/manifest.json'))
    if collect and captures:
        stamp = captures[-1].parent.name
        if stamp not in snapshots: snapshots[stamp] = _snapshot(base, stamp)
        snapshot = snapshots[stamp]; enrolled_ncaa = {r['ncaa_game_id'] for r in existing.values()}
        for matched in snapshot['manifest']['report']['matched']:
            if matched['league'] != 'NCAAF_FBS' or matched['espn_game_id'] in existing: continue
            try:
                if matched['ncaa_game_id'] in enrolled_ncaa:
                    raise IneligibleSourceGame('ORIGINAL_NCAA_ID_ALREADY_ENROLLED')
                row = _record(snapshot, matched, reference, now)
            except IneligibleSourceGame as error:
                pending.append({'espn_game_id': matched['espn_game_id'], 'ncaa_game_id': matched['ncaa_game_id'], 'reason': str(error)})
                continue
            prepared.append(row); enrolled_ncaa.add(row['ncaa_game_id'])
    for row in prepared:
        path = base/ROOT/(row['espn_game_id']+'.json'); path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream: stream.write(source.canonical({'record': row, 'record_sha256': digest(row)}))
    return {'schema': 'tyler-fbs-pregame-reference-feature-status-v1', 'verified_existing': len(existing),
            'new_feature_observations': len(prepared), 'not_enrolled': pending,
            'collection_requested': collect, 'source_available': bool(captures), 'not_a_prediction': True,
            'forecasting_enabled': False, 'model_training_enabled': False, 'historical_evaluation_enabled': False,
            'promotion_allowed': False, 'NO_BET': True, 'actual_wagers': 0}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--collect', action='store_true')
    args = parser.parse_args(); print(json.dumps(inspect(collect=args.collect), sort_keys=True, indent=2))
