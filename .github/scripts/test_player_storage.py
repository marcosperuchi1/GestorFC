from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def die(msg): raise RuntimeError(msg)

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_player_storage.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); html=(root/'src'/'index.html').read_text(encoding='utf-8')
    a=html.find('const v18191wPlayerFields=')
    b=html.find(" const V171_FORMAT='GFC_SHARDED_171'",a)
    if a<0 or b<a: die('Codec worker v18191 nao encontrado')
    codec=html[a:b]
    js=r"""
const assert=require('assert');
"""+codec+r"""
const rows=[
 ['p1',{id:'p1',name:'Jogador A',pos:'ATA',age:21,skills:{att:77,def:31,pas:62,pace:80,gk:12},potential:88,fitness:91,morale:73,contract:3,wage:12345,injury:0,ban:0,yellows:2,reds:0,cardCount:2,listed:false,xp:4.25,goals:7,assists:3,apps:14,cupGoals:2,totalGoals:31,totalApps:88,real:true,clubId:'t1',ageEstimated:false,positionEstimated:false,natCode:'BRA',nationalityKnown:true,star:false,starYears:0,worldGoals:1,traitSeed:123,traitAge:21,archetype:'finisher',squad:'senior',starCandidate:true,seasonRatingSum58:102.4,seasonRatingCount58:14,seasonMinutes58:1150,naturalPosition:'ATA',specificPositionEstimated:true,secondaryPositions:['MEI'],providerId:'abc',sourceOrder:4,editorOvr:78,editorOvrApplied:78,databaseOvr:78,dob:'2005-01-02',identityKey:'jogador a|2005|BRA',matchLoad545:1.25,startStreak545:3,careerMinutes:7440,lastMatchRating:7.8,performanceXP58:2.5,customFutureField:{season:2031,value:[1,2,3]}}],
 ['p2',{id:'p2',name:'Jogador B',pos:'GOL',age:18,skills:{att:12,def:70,pas:59,pace:55,gk:79},potential:94,fitness:100,morale:50,contract:2,wage:800,injury:0,ban:0,yellows:0,reds:0,cardCount:0,listed:false,xp:0,goals:0,assists:0,apps:0,cupGoals:0,totalGoals:0,totalApps:0,real:false,clubId:'t2',ageEstimated:false,positionEstimated:false,natCode:'ARG',nationalityKnown:true,star:false,starYears:0,worldGoals:0,traitSeed:999,traitAge:18,archetype:'reflexes',squad:'youth',youthOrigin:'t2',academyApps:9,academyGoals:0,development:3.2,youthStart:71,youthYear:2026,v576YouthInitialOVR:71,v576YouthModel:1,v576PotentialFixed:1,academyStarPath:true}]
];
(async()=>{
 const enc=await v18191wEncodePlayerChunk(rows);
 assert.equal(enc.format,'FUTBR_PLAYERS_PACKED_GZIP_V1');
 const out=await v18191wDecodePlayerChunk(enc);
 assert.equal(out.length,rows.length);
 for(let i=0;i<rows.length;i++){assert.equal(out[i][0],rows[i][0]);assert.deepStrictEqual(out[i][1],rows[i][1]);}
 console.log(JSON.stringify({ok:true,format:enc.format,encoding:enc.encoding,rows:out.length,encodedChars:String(enc.data||'').length}));
})().catch(e=>{console.error(e);process.exit(1);});
"""
    tmp=root/'.player-storage-test.js';tmp.write_text(js,encoding='utf-8')
    try:
        r=subprocess.run(['node',str(tmp)],capture_output=True,text=True,timeout=30)
    finally:
        tmp.unlink(missing_ok=True)
    if r.returncode: die('Round-trip do codec falhou: '+r.stderr[-1500:])
    try: result=json.loads(r.stdout.strip().splitlines()[-1])
    except Exception as e: die('Saida invalida do teste: '+r.stdout[-1000:])
    (root/'player-storage-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
