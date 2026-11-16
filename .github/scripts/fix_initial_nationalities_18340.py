from __future__ import annotations
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import consolidate_initial_database as db


def normalize(value):
    txt=unicodedata.normalize('NFKD', str(value or ''))
    txt=''.join(ch for ch in txt if not unicodedata.combining(ch))
    return re.sub(r'[^a-z0-9]+',' ',txt.casefold()).strip()


def verify_matt_name(value):
    n=normalize(value)
    return n.startswith('matt ') and any(q in n for q in ('baddi','badie','bady','baddie'))


def corrected_coach(record):
    if not isinstance(record,dict):
        return False
    name=next((record.get(k) for k in ('name','coachName','managerName','trainerName') if verify_matt_name(record.get(k))),None)
    if not name:
        return False
    record['natCode']='USA'
    record['nationality']='Estados Unidos'
    record['nationalityKnown']=True
    # Existing engine/schema aliases only; never change a club's country.
    for k in ('coachNatCode','managerNatCode','trainerNatCode'):
        if k in record: record[k]='USA'
    for k in ('coachNationality','managerNationality','trainerNationality'):
        if k in record: record[k]='Estados Unidos'
    return True


def update_coaches_in_club(record):
    count=0
    def walk(node):
        nonlocal count
        if isinstance(node,dict):
            if corrected_coach(node):count+=1
            for child in tuple(node.values()):walk(child)
        elif isinstance(node,list):
            for child in node:walk(child)
    walk(record)
    return count


def update_unique(html,needle,replacement,label):
    count=html.count(needle)
    if count!=1:raise RuntimeError(f'{label}: expected one marker, found {count}')
    return html.replace(needle,replacement,1)


def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_initial_nationalities_18340.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html_file=root/'src'/'index.html'
    html=html_file.read_text(encoding='utf-8')
    asset=root/'src'/db.ASSET_REL
    if not asset.is_file():raise RuntimeError('External initial player base does not exist')
    if 'FUTBR_INITIAL_NATIONALITIES_18340' in html:raise RuntimeError('18.340 initial nationality patch already applied')

    world_raw,_,_=db.const_value(html,'WorldCatalog')
    world=json.loads(world_raw)
    clubs=world.get('clubs',[])
    alsadd=[c for c in clubs if normalize(c.get('name')) in ('al sadd','al sadd sc','al sadd sports club') and str(c.get('country')).lower() in ('qat','qatar')]
    if not alsadd:
        raise RuntimeError('No Qatar Al Sadd club found in the original catalog')
    hekari=[c for c in clubs if normalize(c.get('name'))=='hekari united' and str(c.get('country')).lower()=='png']
    if len(hekari)!=1:
        raise RuntimeError('Expected exactly one PNG Hekari United club')

    old_raw,_,_=db.const_value(html,'V310_ROSTER_INDEX')
    index=json.loads(old_raw)
    blob=asset.read_text(encoding='utf-8')
    rosters=db.decode_asset(blob,index)
    # The catalog contains two similarly named Al Sadd clubs. Identify the
    # intended team by actual Roberto Firmino roster membership, not the label.
    sadd_candidates=[(str(club['id']),player) for club in alsadd
                     for player in rosters.get(str(club['id']),{}).get('players',[])
                     if normalize(player.get('name'))=='roberto firmino']
    if len(sadd_candidates)!=1:
        raise RuntimeError('Roberto Firmino must belong to exactly one Qatar Al Sadd roster; matches: '+
                           str([(cid,p.get('name')) for cid,p in sadd_candidates]))
    sadd_id=sadd_candidates[0][0]
    hekari_id=str(hekari[0]['id'])
    if sadd_id not in rosters or hekari_id not in rosters:
        raise RuntimeError('Qatar Al Sadd or Hekari roster absent in packaged initial DB')
    firmino=[sadd_candidates[0][1]]
    if len(firmino)!=1:
        sample=[(cid,p.get('name')) for cid,rec in rosters.items() for p in rec.get('players',[]) if 'firmino' in normalize(p.get('name'))][:12]
        raise RuntimeError('Expected exactly one Roberto Firmino at Al Sadd; nearby roster matches: '+str(sample))
    original_firmino=firmino[0].get('natCode')
    firmino[0]['natCode']='BRA'
    firmino[0]['nationality']='Brasil'
    firmino[0]['nationalityKnown']=True

    # Coaches are stored with club roster metadata in the prebuilt player archive.
    # Inspect only Hekari metadata, never change a coach from an unrelated club.
    coach_count=update_coaches_in_club(rosters[hekari_id])
    world_coach_count=update_coaches_in_club(hekari[0])
    if coach_count+world_coach_count!=1:
        raise RuntimeError('Expected one Hekari coach Matt Baddie/Badiee in prebuilt records, found '+
                           str({'roster':coach_count,'catalog':world_coach_count,
                                'roster_keys':list(rosters[hekari_id])[:18],
                                'club_keys':list(hekari[0])[:18]}))

    new_blob,new_index,total=db.compact_records(rosters)
    if len(new_index)!=len(index):
        raise RuntimeError('Initial database club count changed unexpectedly')
    asset.write_text(new_blob,encoding='utf-8')
    html=update_unique(html,old_raw,json.dumps(new_index,separators=(',',':')),'roster index')
    sha=hashlib.sha256(new_blob.encode('utf-8')).hexdigest()
    st,en=db.script_block(html,db.ROSTER_SCRIPT_ID)
    marker=json.loads(html[st:en] or '{}')
    marker.update({'sha256':sha,'bytes':len(new_blob.encode('utf-8')),'records':len(new_index),'players':total})
    html=html[:st]+json.dumps(marker,separators=(',',':'))+html[en:]
    # The standalone V310 loader validates the byte size of the external base.
    pattern=r'(?P<prefix>V310_ROSTER_EXPECTED_BYTES\s*=\s*)\d+'
    if len(re.findall(pattern,html))==1:
        html=re.sub(pattern,lambda m:m.group('prefix')+str(marker['bytes']),html,count=1)
    if world_coach_count:
        new_world=json.dumps(world,ensure_ascii=False,separators=(',',':'))
        current,st,en=db.const_value(html,'WorldCatalog')
        html=html[:st]+'const WorldCatalog = '+new_world+html[en:]
    html=update_unique(html,'</head>','<!-- FUTBR_INITIAL_NATIONALITIES_18340: bundled players/coaches corrected before consolidation -->\n</head>','base verification marker')
    html_file.write_text(html,encoding='utf-8')
    report={'ok':True,'version':'18.340','alSaddTeamId':sadd_id,'hekariTeamId':hekari_id,
            'robertoFirminoNatCode':'BRA','originalFirminoCode':original_firmino,
            'hekariMattBaddieCode':'USA','coachesMatched':coach_count+world_coach_count,
            'basePlayers':total,'baseRecords':len(new_index),'sha256':sha,
            'initialBaseUpdated':True,'careerSavesModified':False}
    (root/'initial-nationalities-18340-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
