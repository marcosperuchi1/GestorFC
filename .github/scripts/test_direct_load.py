from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def die(msg): raise RuntimeError(msg)

def function_block(src,name):
    m=re.search(r'(?:async\s+)?function\s+'+re.escape(name)+r'\s*\(',src)
    if not m: die(name+' ausente')
    b=src.find('{',m.end());depth=0;quote=None;esc=False
    for i in range(b,len(src)):
        ch=src[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
            continue
        if ch in ("'",'"','`'): quote=ch;continue
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0:return src[m.start():i+1]
    die(name+' nao fechada')

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_direct_load.py <project-dir>')
    root=Path(sys.argv[1]).resolve();html=(root/'src'/'index.html').read_text(encoding='utf-8')

    ca=html.find('const v18191mPlayerFields=')
    cb=html.find('async function v18183DbWriteMany',ca)
    if ca<0 or cb<ca: die('codec principal ausente')
    codec=html[ca:cb]
    hydrate=function_block(html,'v18194HydrateManifest')

    if html.count("view=loaded?.v640National?.userTeam?'national':'squad';") < 2:
        die('uma das rotas de continuar carreira nao abre direto no elenco')
    if "noWorkerWorldCloneOnLoad:true" not in html:
        die('marcador de carregamento direto ausente')
    if "rosterPreloadedDuringAuth:true" not in html or "welcomeRosterGate:true" not in html:
        die('base consolidada nao esta preparada antes da tela inicial')
    if "base local no login:" in html or "base local durante load:" in html:
        die('continuar carreira ainda dispara preload da base inicial')

    js=r"""
const assert=require('assert');
const {performance}=require('perf_hooks');
const FORMAT='GFC_SHARDED_171';
"""+codec+"\n"+hydrate+r"""
(async()=>{
 const players={};
 for(let i=0;i<37;i++){
  const id='p'+i;
  players[id]={id,name:'Jogador '+i,pos:i%7===0?'GOL':'ATA',age:18+(i%17),skills:{att:50+i%30,def:30+i%20,pas:40+i%25,pace:45+i%35,gk:i%7===0?70:8},potential:60+i%31,fitness:80+i%20,morale:50+i%45,contract:1+i%5,wage:1000+i*13,injury:0,ban:0,yellows:i%4,reds:0,cardCount:i%4,listed:false,xp:i/10,goals:i%9,assists:i%7,apps:i%20,real:i%2===0,clubId:'t'+(i%3),natCode:i%2?'BRA':'ARG',nationalityKnown:true,customExtra:{x:i,arr:[i,i+1]}};
 }
 const state={
  year:2034,day:87,user:'t0',userCoachId:'c1',difficulty:'normal',
  players,
  teams:[
   {id:'t0',name:'Flamengo',roster:Object.keys(players).slice(0,12),academy:['p30','p31']},
   {id:'t1',name:'Palmeiras',roster:Object.keys(players).slice(12,24)},
   {id:'t2',name:'Athletico-PR',roster:Object.keys(players).slice(24,36)}
  ],
  coaches:{c1:{id:'c1',name:'Treinador',clubId:'t0'}},
  schedule:[{day:1,home:'t0',away:'t1',played:true,hg:2,ag:1},{day:2,home:'t2',away:'t0',played:false}],
  competitions:{league:{id:'league',name:'Liga'}},
  competitionStats:{league:{p0:{apps:3,goals:2,assists:1}}},
  allTimeStats:{p0:{apps:123,goals:45,assists:21}},
  v538CareerArchive:{2033:{p0:[{teamId:'t0',apps:30,goals:12,assists:7}]}},
  v555CareerArchive:{2033:{p:{p0:1}}},
  scorerArchive:[{year:2033,competitions:{league:{p0:{id:'p0',apps:30,goals:12,assists:7}}}}],
  transfers:[{id:'p1',year:2033,from:'t1',to:'t0',fee:1000000}],
  retirements:[{id:'p9',year:2032,clubId:'t2'}],
  history:[{year:2033,league:'t0'}],
  internationalHistory:[{year:2033,champion:'BRA'}],
  v735NationalArchive:[{year:2033,code:'BRA'}],
  crestOverrides:{t0:'crest'}
 };
 const SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive','crestOverrides'];
 const root={};for(const [k,v] of Object.entries(state))if(!SHARDS.includes(k))root[k]=v;
 const storage=new Map(),collections={},token='test';
 for(const key of SHARDS){
  const value=state[key];if(value==null)continue;
  const isArray=Array.isArray(value),keys=[];let rows=[],idx=0;
  const limit=key==='players'?11:4;
  const flush=async()=>{if(!rows.length)return;const ck='k:'+key+':'+idx++;keys.push(ck);storage.set(ck,key==='players'?await v18191mEncodePlayerChunk(rows):rows);rows=[];};
  for(const id in value){rows.push([id,value[id]]);if(rows.length>=limit)await flush();}
  await flush();collections[key]={isArray,length:isArray?value.length:0,keys};
 }
 const manifest={format:FORMAT,version:1,revision:1,token,at:Date.now(),year:state.year,day:state.day,root,collections};
 let calls=0,maxBatch=0;
 const readMany=async keys=>{calls++;maxBatch=Math.max(maxBatch,keys.length);return keys.map(k=>storage.get(k));};
 const loaded=await v18194HydrateManifest(manifest,null,readMany);
 assert.deepStrictEqual(loaded,state);
 for(const t of loaded.teams)for(const id of t.roster||[])assert.ok(loaded.players[id],t.name+' sem '+id);
 const result={ok:true,players:Object.keys(loaded.players).length,teams:loaded.teams.length,readBatches:calls,maxBatch,clubLanding:'squad',nationalLanding:'national',historiesPreserved:true};
 console.log(JSON.stringify(result));
})().catch(e=>{console.error(e);process.exit(1);});
"""
    tmp=root/'.direct-load-test.js';tmp.write_text(js,encoding='utf-8')
    try:r=subprocess.run(['node',str(tmp)],capture_output=True,text=True,timeout=45)
    finally:tmp.unlink(missing_ok=True)
    if r.returncode: die('Teste de carregamento direto falhou: '+(r.stderr or r.stdout)[-3000:])
    result=json.loads(r.stdout.strip().splitlines()[-1])
    (root/'direct-load-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
