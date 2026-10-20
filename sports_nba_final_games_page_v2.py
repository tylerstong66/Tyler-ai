"""Opt-in native null-envelope regulation finals; diagnostic only, never grading."""
import sports_nba_final_games_page as v1
import sports_nba_games_page_v2 as envelope


def parse(raw, *, requested_date, season, observed_at):
    result = v1._parse(raw, requested_date=requested_date, season=season,
                      observed_at=observed_at, document_reader=envelope.document)
    result['schema'] = 'tyler-nba-owned-daily-regulation-final-null-envelope-page-v2'
    result['date_override_field_state'] = 'EXPLICIT_NULL'
    result['date_override_active_attested'] = False
    result['reader_scope'] = 'OPT_IN_DIAGNOSTIC_ONLY'
    return result
