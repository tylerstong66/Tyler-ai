"""Opt-in native null-envelope NBA pregame reader; diagnostic use only.

No source bytes are rewritten. A null UI flag is unknown, never an assertion
that the date override is active. All route/date/calendar/game checks still
apply. No existing v1 receipt collector imports this module.
"""
import sports_nba_games_page as v1


def document(raw, *, requested_date, season, observed_at):
    """Accept explicitly present null only; missing/true/false are rejected."""
    return v1._document(raw, requested_date=requested_date, season=season,
                        observed_at=observed_at, null_override=True)


def parse(raw, *, requested_date, season, observed_at):
    result = v1._parse(raw, requested_date=requested_date, season=season,
                      observed_at=observed_at, document_reader=document)
    result['schema'] = 'tyler-nba-owned-daily-pregame-page-null-envelope-v2'
    result['date_override_active_attested'] = False
    result['date_override_field_state'] = 'EXPLICIT_NULL'
    result['reader_scope'] = 'OPT_IN_DIAGNOSTIC_ONLY'
    return result
