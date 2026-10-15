"""Join verified MLB matchup research with independent season rates and handedness.

Season-long AVG and HR per PA are descriptive context for small BvP samples,
not a formula for next-game player prop probabilities.
"""
from sports_mlb_auto_bullpen import auto_bullpen_matchup
from sports_mlb_hitter_context import hitter_season_context
from sports_mlb_sources import OfficialMlbReader, utc


def contextual_mlb_research(game_id, hitter_id, hitter_side, *, auto_select=True,
                            manual_reliever_ids=(), reader=None):
    reader=reader or OfficialMlbReader()
    research=auto_bullpen_matchup(
        game_id, hitter_id, hitter_side, auto_select=auto_select,
        manual_reliever_ids=manual_reliever_ids, reader=reader)
    event=research["matchup_research"]["event_start"]
    hitter=research["hitter"]
    starter=research["probable_starter"]
    context=hitter_season_context(
        hitter["id"],starter["id"],event,
        hitter_name=hitter["name"], starter_name=starter["name"],reader=reader)
    if (context["hitter"]["id"]!=hitter["id"] or
            context["opposing_probable_starter"]["id"]!=starter["id"] or
            utc(context["first_pitch"])!=utc(event)):
        raise ValueError("MLB season context does not match independently checked pregame identities.")
    if utc(context["as_of"])>=utc(event):
        raise ValueError("MLB hitter context was captured after first pitch.")
    current=context["season_statistics"][-1] if context["season_statistics"] else None
    if current is None:
        research["summary"].append(
            "Current-season official regular-season hitter counts were unavailable; "
            "no season average was estimated.")
    else:
        avg = current["batting_average"]
        desc="unknown" if avg is None else f"{avg:.3f}"
        research["summary"].append(
            f"Hitter {hitter['name']} regular-season {current['season']}: "
            f"{current['hits']} hits / {current['ab']} at-bats (AVG {desc}), "
            f"{current['hr']} home runs / {current['pa']} plate appearances. "
            "Descriptive background, not today's hit or home-run probability.")
    research["summary"].append(
        "Official handedness: hitter bats " + (context["hitter"]["hand"] or "unknown") +
        "; probable starter throws " + (context["opposing_probable_starter"]["hand"] or "unknown") +
        ". Handedness alone is not a modeled batter-versus-pitcher advantage.")
    research["hitter_season_context"]=context
    research["decision"]="RESEARCH ONLY - NO BET"
    research["estimated_hit_probability"]=None
    research["estimated_home_run_probability"]=None
    research["parlay_joint_probability"]=None
    research["wager_executed"]=False
    return research
