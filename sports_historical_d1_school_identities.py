"""Load only the explicitly reviewed, digest-pinned D1 source spellings.

This opt-in policy changes source spelling reconciliation, not institutional
certification, Division I membership, result grading or model eligibility.
"""
from pathlib import Path
import hashlib
import json

import sports_expansion_historical_capture as history
import sports_expansion_observer as source
import sports_historical_d1_identity_review as review
from sports_ncaa_espn_identity import name

MANIFEST=history.ROOT/'school_identity_v1/NCAAM_D1.json'
MANIFEST_SHA256='96cf205e347080ee39ac1d799dacfd845aff4363d8a740bf452bed16358f443a'


def digest(value):return hashlib.sha256(source.canonical(value)).hexdigest()


def load(base=Path('.'),*,league='NCAAM_D1',split='train',now=None):
    if league!='NCAAM_D1' or split not in ('train','validation'):
        raise ValueError('No reviewed D1 source spelling policy for requested scope')
    path=Path(base)/MANIFEST
    if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:
        raise ValueError('Missing or invalid D1 spelling manifest')
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=MANIFEST_SHA256:
        raise ValueError('Reviewed D1 spelling manifest digest mismatch')
    saved=json.loads(raw)
    if (saved.get('schema')!='tyler-historical-d1-reviewed-source-spellings-v1'
            or saved.get('league')!=league or saved.get('NO_BET') is not True
            or type(saved.get('actual_wagers')) is not int or saved['actual_wagers']!=0
            or any(saved.get(k) is not False for k in ('institutional_identity_certified',
                'division_one_membership_certified','historical_pregame_availability_attested',
                'score_or_outcome_used_for_identity','training_allowed',
                'historical_evaluation_enabled','forecasting_enabled','promotion_allowed'))):
        raise ValueError('Reviewed D1 spelling scope or research guards changed')
    packet=review.build(base,now=now)
    if digest(packet)!=saved.get('source_review_report_sha256'):
        raise ValueError('D1 identity evidence review differs from frozen source packet')
    candidates={(c['ncaa_normalized_school'],c['espn_normalized_school'],
                 c['ncaa_seoname'],c['espn_team_id']):c for c in packet['candidate_proposals']}
    aliases={};targets=set()
    for entry in saved['entries']:
        n=name(entry['ncaa_school']);e=name(entry['espn_school'])
        if n in aliases or e in targets or n==e:
            raise ValueError('Ambiguous reviewed D1 source spelling')
        key=(n,e,entry['ncaa_seoname'],entry['espn_team_id'])
        case=candidates.get(key)
        if case is None or digest(case)!=entry['candidate_evidence_sha256']:
            raise ValueError('D1 spelling lacks its repeated original-source evidence')
        aliases[n]=entry['espn_school'];targets.add(e)
    return {'aliases':aliases,'manifest_sha256':MANIFEST_SHA256,
            'policy':saved['review_policy'],'reviewed_school_spellings':len(aliases)}
