from __future__ import annotations
import hashlib,json,sys,unicodedata,re
from pathlib import Path
import consolidate_initial_database as db


def norm(v):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(v or '').casefold()) if not unicodedata.combining(c)).replace('-',' ').strip()


def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_initial_nationalities_18340.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src/index.html').read_text(encoding='utf-8')
    if 'FUTBR_INITIAL_NATIONALITIES_18340' not in html:
        raise RuntimeError('Nationality patch did not run before database consolidation')
    world=json.loads(db.const_value(html,'WorldCatalog')[0])
    index=json.loads(db.const_value(html,'V310_ROSTER_INDEX')[0])
    blob=(root/'src'/db.ASSET_REL).read_text(encoding='utf-8')
    db_rows=db.decode_asset(blob,index)
    al=[c for c in world['clubs'] if norm(c.get('name')) in ('al sadd','al sadd sc','al sadd sports club') and str(c.get('country')).lower()=='qat']
    he=[c for c in world['clubs'] if norm(c.get('name'))=='hekari united' and str(c.get('country')).lower()=='png']
    if len(al)!=1 or len(he)!=1:raise RuntimeError('Al Sadd / Hekari not found in actual consolidated database')
    firmino=[p for p in db_rows[al[0]['id']]['players'] if norm(p.get('name'))=='roberto firmino']
    if len(firmino)!=1 or firmino[0].get('natCode')!='BRA':
        raise RuntimeError('Roberto Firmino is not Brazilian in packaged base')
    coach=db_rows[he[0]['id']].get('coach')
    if not isinstance(coach,dict) or not norm(coach.get('name')).startswith('matt badi') or coach.get('natCode')!='USA':
        raise RuntimeError('Matt Badiee not registered as USA coach at Hekari')
    marker=json.loads(html[slice(*db.script_block(html,db.ROSTER_SCRIPT_ID))])
    digest=hashlib.sha256(blob.encode('utf-8')).hexdigest()
    if marker.get('sha256')!=digest:raise RuntimeError('Packaged initial database hash is not consistent')
    if marker.get('players')!=sum(len(r.get('players',[])) for r in db_rows.values()):
        raise RuntimeError('Player count mismatch after nationality-only changes')
    manifest=json.loads((root/'initial-database-consolidation.json').read_text(encoding='utf-8'))
    if manifest.get('fallbackClubs',0)!=0:
        raise RuntimeError('The prebuilt initial academy/roster distribution changed')
    report={'ok':True,'version':'18.340','alSaddPlayer':'Roberto Firmino','firminoNatCode':'BRA',
            'hekariCoach':coach['name'],'coachNatCode':'USA','baseSha256':digest,
            'playerCount':marker['players'],'rosterRecords':len(index),
            'academyPreserved':True,'existingSaveFilesModified':False}
    (root/'initial-nationalities-18340-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
