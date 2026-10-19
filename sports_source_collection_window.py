"""Bounded UTC source retrieval windows; never pregame backfill authority."""
from datetime import timezone


def bounds(days_ahead, days_back):
    if (type(days_ahead) is not int or not 0 <= days_ahead <= 7
            or type(days_back) is not int or not 0 <= days_back <= 3):
        raise ValueError('Source horizon exceeds bounds: 0-7 forward days and 0-3 lookback days required')


def policy(now, days_ahead, days_back):
    bounds(days_ahead, days_back)
    if now.tzinfo is None or days_back == 0:
        raise ValueError('Lookback policy requires an aware clock and positive bounded lookback')
    return {'schema': 'tyler-bounded-source-collection-window-v1',
            'anchor_utc_date': now.astimezone(timezone.utc).date().isoformat(),
            'days_ahead': days_ahead, 'days_back': days_back,
            'source_observations_only': True, 'pregame_feature_backfill_allowed': False}


def verify(saved, now):
    if not isinstance(saved, dict): raise ValueError('Invalid source collection window')
    expected = policy(now, saved.get('days_ahead'), saved.get('days_back'))
    # Canonical field types matter: booleans must not impersonate integer bounds.
    if (set(saved) != set(expected) or saved != expected
            or saved.get('source_observations_only') is not True
            or saved.get('pregame_feature_backfill_allowed') is not False):
        raise ValueError('Source collection window differs from original observation clock')
    return expected
