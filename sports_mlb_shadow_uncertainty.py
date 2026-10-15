"""Game-cluster-aware uncertainty for MLB hitter shadow scoring.

A cluster is one official MLB game, not an individual player-game outcome.
Bootstrap intervals describe historical score differences vs fixed priors,
NOT model calibration, prospective time attestation or a betting edge.
"""
import random
from collections import defaultdict

MIN_DISTINCT_GAMES=30
MIN_PLAYER_GAMES=150
BOOTSTRAP_REPLICATES=600
SEED=314159


def clustered_brier_difference(rows, *, reference_probability):
    """Positive Brier difference (prior - model) favors experimental baseline.

    Refuse inferential intervals until a minimum number of distinct *games*
    and at-bat-eligible player-games have accrued. Within-game player
    outcomes are resampled together to avoid naive independence assumptions.
    """
    if (isinstance(reference_probability,bool) or
            not isinstance(reference_probability,(int,float)) or
            not 0<reference_probability<1):
        raise ValueError("Invalid fixed reference probability.")
    groups=defaultdict(list)
    for row in rows:
        if not isinstance(row,dict):
            raise ValueError("Invalid shadow outcome row.")
        gid=row.get("game_id")
        p=row.get("probability")
        y=row.get("outcome")
        if (isinstance(gid,bool) or not isinstance(gid,int) or gid<=0 or
                isinstance(p,bool) or not isinstance(p,(float,int)) or
                not 0<p<1 or isinstance(y,bool) or y not in (0,1)):
            raise ValueError("Invalid immutable game-cluster outcome or event probability.")
        diff=(reference_probability-y)**2-(p-y)**2
        groups[gid].append(diff)
    game_count=len(groups)
    observations=sum(len(v) for v in groups.values())
    differences=[x for arr in groups.values() for x in arr]
    observed=round(sum(differences)/observations,6) if observations else None
    ready=game_count>=MIN_DISTINCT_GAMES and observations>=MIN_PLAYER_GAMES
    result={
        "eligible_player_games":observations,
        "distinct_official_games_with_scored_players":game_count,
        "preregistered_minimum_games":MIN_DISTINCT_GAMES,
        "preregistered_minimum_player_games":MIN_PLAYER_GAMES,
        "mean_fixed_minus_model_brier":observed,
        "interval_method":"game_cluster_bootstrap_percentile_95pct" if ready else None,
        "bootstrap_replicates":BOOTSTRAP_REPLICATES if ready else 0,
        "bootstrap_ci_lower":None,
        "bootstrap_ci_upper":None,
        "interval_excludes_zero_in_model_favor":None,
        "minimum_sample_gate_met":ready,
        "prospective_publication_attested":False,
        "calibrated_prediction_model":False,
        "profitable_betting_edge_proven":False,
        "limitations":[
            "Same-game hitters are clustered; repeated players across different games may still be dependent.",
            "The minimum count gate does not establish representative sampling, calibration or a sportsbook edge.",
            "Intervals compare only with a fixed exploratory probability and cannot stand in for real sportsbook prices.",
            "Publication and pregame timing remain independently reviewable outside this statistical report.",
        ],
    }
    if not ready:
        return result
    rng=random.Random(SEED)
    sample_groups=[groups[k] for k in sorted(groups)]
    means=[]
    for _ in range(BOOTSTRAP_REPLICATES):
        total=0.0
        n=0
        for _ in range(game_count):
            selected=sample_groups[rng.randrange(game_count)]
            total+=sum(selected)
            n+=len(selected)
        means.append(total/n)
    means.sort()
    low=means[int(0.025*(BOOTSTRAP_REPLICATES-1))]
    high=means[int(0.975*(BOOTSTRAP_REPLICATES-1))]
    result["bootstrap_ci_lower"]=round(low,6)
    result["bootstrap_ci_upper"]=round(high,6)
    result["interval_excludes_zero_in_model_favor"]=low>0
    return result
