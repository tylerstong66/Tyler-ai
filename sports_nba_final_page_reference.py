"""Read-only cross-source agreement for the pinned historical NBA page fixture."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

import sports_expansion_historical_capture as history
import sports_expansion_observer as source
import sports_historical_content_seal as seal
import sports_nba_final_games_page as page
import sports_nba_final_receipts as finals
import sports_nba_official_schedule_audit as nba
from sports_expansion_audit import archive_path, bounded_gzip_read

DAY = '2026-04-10'
SPLIT = 'validation'


def provider_reference(base, *, observed_by):
    """Replay existing sealed ESPN originals; never fetch or enroll outcomes."""
    if not isinstance(observed_by, datetime) or observed_by.tzinfo is None:
        raise ValueError('Aware reference observation clock required')
    base = Path(base)
    seal.verify(base)
    if not history.verify_existing(base, 'NBA', SPLIT, DAY, as_of=observed_by):
        raise ValueError('Missing sealed ESPN reference day')
    root = base/history.ROOT/'sources'/'NBA'/SPLIT
    receipt_raw = archive_path(root/(DAY+'.receipt.json')).read_bytes()
    receipt = json.loads(receipt_raw)
    raw = bounded_gzip_read(archive_path(root/(DAY+'.json.gz')).read_bytes())
    if hashlib.sha256(raw).hexdigest() != receipt['original_response_sha256']:
        raise ValueError('ESPN reference body changed during replay')
    events = json.loads(raw)['events']; by_id = {str(e['id']): e for e in events}
    if len(by_id) != len(events): raise ValueError('Duplicate ESPN reference event ID')
    provider = {}
    for row in receipt['parsed_provider_scoreboard']['games']:
        key = row['game_id']; sides = {}
        if key in provider: raise ValueError('Duplicate ESPN normalized reference ID')
        for side in by_id[key]['competitions'][0]['competitors']:
            role = side['homeAway']; team = side['team']
            if role not in ('home', 'away') or role in sides:
                raise ValueError('Ambiguous ESPN reference side')
            if str(team['id']) != row[role+'_team_id']:
                raise ValueError('ESPN reference team ID differs from original normalization')
            sides[role] = nba.tricode(team['abbreviation'])
        if set(sides) != {'home', 'away'} or sides['home'] == sides['away']:
            raise ValueError('Missing ESPN reference opponents')
        provider[key] = {**row, 'espn_game_id': key,
            'home_tricode': sides['home'], 'away_tricode': sides['away']}
    return provider, {'source_url': receipt['source_url'],
        'receipt_sha256': hashlib.sha256(receipt_raw).hexdigest(),
        'original_body_sha256': receipt['original_response_sha256'],
        'observed_at_utc': receipt['recorded_at_utc']}


def build(base=Path('.')):
    original = page.replay_reference(base)
    at = source.utc(original['observed_at_utc'])
    provider, proof = provider_reference(base, observed_by=at)
    report = finals.classify(original['games'], provider,
        nba_observed_at=original['observed_at_utc'], espn_observed_at=proof['observed_at_utc'])
    return {**report, 'schema': 'tyler-nba-final-page-historical-reference-agreement-v1',
        'reference_day': DAY, 'season': original['season'],
        'nba_page_manifest_sha256': original['fixture_manifest_sha256'],
        'nba_page_body_sha256': original['original_body_sha256'], 'espn_source': proof,
        'reference_fixture_only': True, 'fresh_source_observation': False,
        'current_season_results_verified': False,
        'available_at_historical_pregame_freeze': False, 'actual_tipoff_time_attested': False,
        'receipt_clock_independently_attested': False, 'source_origin_independently_attested': False,
        'settlement_enabled': False, 'new_outcomes_enrolled': 0,
        'limitation': 'Archived postgame source agreement only; no prospective prediction, current-season final certification or historical model evaluation.'}


if __name__ == '__main__':
    print(json.dumps(build(), sort_keys=True, indent=2))
