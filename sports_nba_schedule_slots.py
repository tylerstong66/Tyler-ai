"""Retain narrowly typed future NBA Cup TBD slots, never game identities.

Strict legacy parsers stay unchanged. Every other malformed source record
fails the complete response; original source bytes are never rewritten.
"""
from datetime import datetime,timezone
import hashlib
import json
import re

import sports_nba_official_schedule_audit as nba
import sports_expansion_observer as source

POLICY='FUTURE_NBA_CUP_BOTH_TEAMS_UNASSIGNED_V1'


def parse(raw,*,observed_at):
    observed=source.utc(observed_at)
    payload=json.loads(raw);schedule=payload['leagueSchedule']
    season=schedule.get('seasonYear')
    if (schedule.get('leagueId')!='00' or not isinstance(season,str)
            or not re.fullmatch(r'20\d{2}-\d{2}',season)
            or int(season[-2:])!=(int(season[:4])+1)%100):
        raise ValueError('NBA slot source league/season identity invalid')
    groups=schedule['gameDates']
    if not isinstance(groups,list) or len(groups)<50:
        raise ValueError('NBA slot source lacks full season calendar')
    filtered=[];quarantined=[];seen=set()
    for block in groups:
        games=[]
        for item in block['games']:
            identifier=str(item['gameId'])
            if not re.fullmatch(r'[0-9]{10}',identifier) or identifier in seen:
                raise ValueError('Duplicate or invalid NBA slot source game ID')
            seen.add(identifier)
            if identifier[:3] not in nba.ALLOWED_KINDS:
                games.append(item);continue
            home=item['homeTeam'];away=item['awayTeam']
            if not home.get('teamTricode') or not away.get('teamTricode'):
                tip=source.utc(item['gameDateTimeUTC'])
                if (identifier[:3]!='002' or int(identifier[3:5])!=int(season[2:4])
                        or type(item.get('gameStatus')) is not int or item['gameStatus']!=1
                        or tip<=observed or item.get('gameLabel')!='Emirates NBA Cup'
                        or item.get('gameSubLabel') not in ('Quarterfinal','Semifinal')
                        or any(type(t.get('teamId')) is not int or t['teamId']!=0
                               or any(t.get(k) is not None for k in
                                      ('teamName','teamCity','teamTricode','teamSlug'))
                               or type(t.get('score')) is not int or t['score']!=0
                               for t in (home,away))):
                    raise ValueError('Incomplete NBA opponent is not a permitted future Cup slot')
                quarantined.append({'nba_game_id':identifier,'tipoff_utc':tip.isoformat(),
                    'reason':'FUTURE_NBA_CUP_TEAMS_UNASSIGNED',
                    'original_game_sha256':hashlib.sha256(source.canonical(item)).hexdigest(),
                    'eligible_for_identity_match':False,'eligible_for_result_agreement':False})
            else:games.append(item)
        filtered.append({**block,'games':games})
    known=nba.official_games(source.canonical({**payload,'leagueSchedule':{**schedule,'gameDates':filtered}}))
    for game in known:
        tip=source.utc(game['tipoff_utc'])
        year=tip.year if tip.month>=7 else tip.year-1
        if year!=int(season[:4]) or int(game['nba_game_id'][3:5])!=year%100:
            raise ValueError('NBA current source game outside stated season')
        if game['nba_status']==3 and observed<=tip:
            raise ValueError('NBA current final observed before scheduled start')
    return known,quarantined
