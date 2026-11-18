from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from test_season_saves_18343 import jsfunc

MARK='FUTBR_CLEAN_INCREMENTAL_SHARDS_18349'

TEST=r"""
const assert=require('node:assert/strict');
const {webcrypto}=require('node:crypto');
const {performance}=require('node:perf_hooks');
const vm=require('node:vm');
const clone=x=>x===undefined?undefined:structuredClone(x);
function buildPlayers(n){
 const out={};
 for(let i=0;i<n;i++)out['p'+i]={
  id:'p'+i,age:18+i%27,clubId:'c'+i%32,goals:i%39,assists:i%17,
  career:{season:[{year:2030,goals:i%22,assists:i%12}]},
  awards:[{year:2029,title:'liga'}],extras:{fitness:95-i%20}};
 return out;
}
const clubs=()=>Array.from({length:70},(_,i)=>({id:'c'+i,balance:123000+i,
 roster:['p'+i],history:[{season:2029,titles:i%3}]}));
const rounds=()=>Array.from({length:137},(_,i)=>({type:'league',round:i+1,
 fixtures:[{id:'m'+i,home:'c'+i%32,away:'c'+(i+1)%32,result:i<30?{home:1,away:2}:null}]}));
const game=()=>({year:2031,day:3,seasonDone:false,players:buildPlayers(6501),
 teams:clubs(),coaches:{c0:{name:'Silva',job:[2029]}},
 schedule:rounds(),competitionStats:{'2031':{p1:{goals:10,assists:3}}},
 allTimeStats:{p1:{goals:79,assists:21}},
 v538CareerArchive:{'2030':{p0:{goals:22,clubs:['c0']}}},
 v555CareerArchive:{'2030':{c0:{titles:3}}},
 scorerArchive:[{year:2030,players:{p4:{goals:19}}}],
 retirements:[{year:2029,player:'p12',age:39}],
 transfers:[{year:2029,player:'p3',fee:75000}]});
function restore(db,manifest,key){
 const spec=manifest.collections[key],out=spec.isArray?[]:{};
 assert(spec,'Missing collection '+key);
 for(const chunkKey of spec.keys){
  const item=db.get(chunkKey);assert(item,'Missing shard '+chunkKey);
  for(const [id,value] of item?.rows||item)out[id]=clone(value);
 }
 return out;
}
async function uiTest(){
 const db=new Map(),writes={n:0,by:{},fail:false};
 const FORMAT='GFC_SHARDED_171',KEY='CURRENT';
 const SHARDS=['players','teams','coaches','schedule','competitionStats','allTimeStats',
  'v538CareerArchive','v555CareerArchive','scorerArchive','retirements','transfers'];
 const state=game(),ctx={crypto:webcrypto,TextEncoder,Map,Set,ArrayBuffer,Uint8Array,
  performance,Math,Date,Promise,setTimeout,FORMAT,KEY,SHARDS,state,window:{},
  v18121NewSeasonPreparation:false,v53Sim:{},v53PaintStatus(){},
  stats:{playerChunksWritten:0,fullSaves:0,employmentSaves:0},
  v18191mPlayerFormat:'ui-v1',
  v18191mEncodePlayerChunk:async raw=>({encoding:'ui-v1',rows:clone(raw)}),
  shardKey:(...p)=>p.join('|'),
  rawRead:async k=>clone(db.get(k)),rawDelete:async k=>db.delete(k),
  keysOf:m=>new Set(Object.values(m?.collections||{}).flatMap(spec=>spec.keys||[])),
  cleanupManifest:async(m,keep)=>{
   if(m?.format!==FORMAT)return;
   for(const spec of Object.values(m.collections||{}))
    for(const key of spec.keys||[])if(!keep.has(key))db.delete(key);
  },
  commitManifest:async(m,old,meta)=>{
   if(writes.fail)throw Error('Disk failure');
   if(old)db.set(KEY+':previous',clone(old));
   db.set(KEY,clone(m));db.set(KEY+':meta',clone(meta));
  },
  v18183DbWriteMany:async entries=>{
   if(writes.fail)throw Error('Disk failure');
   for(const e of entries){db.set(e.key,clone(e.value));writes.n++;
    const key=e.key.split('|')[1];writes.by[key]=(writes.by[key]||0)+1;}
  }};
 vm.runInNewContext(globalThis.UI_CODE,ctx);
 const save=()=>vm.runInNewContext('saveSharded(state)',ctx);
 await save();const first=clone(db.get(KEY)),num=first.collections.players.keys.length;
 assert.equal(num,9);
 assert(first.collections.players.hashes.every(h=>h&&h.length===64),'SHA-256 fingerprints must be stored');
 assert.equal(JSON.stringify(restore(db,first,'players')),JSON.stringify(state.players));
 const initial=writes.n;
 await save();const second=clone(db.get(KEY));
 assert.equal(writes.n,initial,'Unchanged UI save must reuse all live shards');
 assert.deepEqual(first.collections.players.keys,second.collections.players.keys);
 state.day=4;state.players.p11.goals++;state.players.p11.career.season.push({year:2031,goals:8});
 state.teams[0].balance++;state.schedule[50].fixtures[0].result={home:2,away:0};
 state.allTimeStats.p1.goals++;
 const prev={...writes.by};await save();const changed=clone(db.get(KEY));
 for(const k of ['players','teams','schedule','allTimeStats'])
  assert.equal((writes.by[k]||0)-(prev[k]||0),1,'Exactly one changed '+k+' chunk');
 for(const k of ['retirements','transfers','scorerArchive'])
  assert.equal((writes.by[k]||0)-(prev[k]||0),0,'History '+k+' stays immutable');
 assert.equal(JSON.stringify(restore(db,changed,'players')),JSON.stringify(state.players));
 assert.equal(JSON.stringify(restore(db,changed,'schedule')),JSON.stringify(state.schedule));
 assert.equal(JSON.stringify(restore(db,changed,'retirements')),JSON.stringify(state.retirements));
 const bogus=clone(db.get(KEY));bogus.collections.players.encoding='worker-v1';db.set(KEY,bogus);
 const beforeCodec=writes.by.players;await save();
 assert.equal(writes.by.players-beforeCodec,num,'Codec mismatch must fully rewrite UI player chunks');
 const committed=JSON.stringify(db.get(KEY));
 state.day++;state.players.p22.assists++;writes.fail=true;
 await assert.rejects(save(),/Disk failure/);
 writes.fail=false;
 assert.equal(JSON.stringify(db.get(KEY)),committed,'Previous checkpoint remains valid after failure');
 await save();assert.equal(restore(db,db.get(KEY),'players').p22.assists,state.players.p22.assists);
 state.players.p0.optionalProperty=undefined;
 const beforeUnsupported=writes.by.players;await save();
 assert(writes.by.players-beforeUnsupported>=1,'Unhashable chunks conservatively rewrite');
 return {players:6501,chunks:num,firstSaveChunks:num,unchangedSaveChunks:0,
  oneChangedPlayerChunks:1,historyPreserved:true,previousCheckpointPreserved:true,
  codecGuard:true,unsupportedValuesFallback:true};
}
async function workerTest(){
 const db=new Map(),writes={n:0,by:{},fail:false};
 const STORE='WORKER',V171_FORMAT='GFC_SHARDED_171';
 const V171_SHARDS=['players','teams','coaches','schedule','competitionStats','allTimeStats',
  'v538CareerArchive','v555CareerArchive','scorerArchive','retirements','transfers'];
 const ctx={crypto:webcrypto,TextEncoder,Map,Set,ArrayBuffer,Uint8Array,
  performance,Math,Date,Promise,setTimeout,STORE,V171_FORMAT,V171_SHARDS,
  diskRevision:1,checkpoint:null,hostStorage:true,
  safe:id=>id!=='__proto__',v171ShardKey:(...p)=>p.join('|'),
  v18191wPlayerFormat:'worker-v1',
  v18191wEncodePlayerChunk:async raw=>({encoding:'worker-v1',rows:clone(raw)}),
  read:async k=>clone(db.get(k)),
  v18181RawWriteMany:async entries=>{
   if(writes.fail)throw Error('Worker disk failure');
   for(const e of entries){db.set(e.key,clone(e.value));writes.n++;
    const key=e.key.split('|')[1];writes.by[key]=(writes.by[key]||0)+1;}
  },
  v171DropManifest:async(m,keep)=>{
   if(m?.format!==V171_FORMAT)return;
   for(const sp of Object.values(m.collections||{}))
    for(const k of sp.keys||[])if(!keep.has(k))db.delete(k);
  }};
 vm.runInNewContext(globalThis.WORKER_CODE,ctx);
 const save=s=>{ctx.s=s;return vm.runInNewContext('save(s)',ctx)};
 const s=game();await save(s);
 const first=clone(db.get(STORE)),num=first.collections.players.keys.length;
 assert.equal(num,9);
 const initial=writes.n;await save(s);
 assert.equal(writes.n,initial,'Unchanged worker state must produce zero new shards');
 s.day++;s.players.p3.goals++;s.schedule[70].fixtures[0].result={home:1,away:1};
 const prev=writes.by.players||0;
 await save(s);const changed=clone(db.get(STORE));
 assert.equal((writes.by.players||0)-prev,1,'Changed worker player only one chunk');
 assert.equal(JSON.stringify(restore(db,changed,'players')),JSON.stringify(s.players));
 assert.equal(JSON.stringify(restore(db,changed,'retirements')),JSON.stringify(s.retirements));
 const bogus=clone(db.get(STORE));bogus.collections.players.encoding='ui-v1';db.set(STORE,bogus);
 const beforeCodec=writes.by.players;await save(s);
 assert.equal(writes.by.players-beforeCodec,num,'Codec mismatch must fully rewrite worker player chunks');
 const committed=JSON.stringify(db.get(STORE));
 s.day++;s.players.p10.goals++;writes.fail=true;
 await assert.rejects(save(s),/Worker disk failure/);
 writes.fail=false;
 assert.equal(JSON.stringify(db.get(STORE)),committed,'Previous worker checkpoint preserved on failure');
 await save(s);assert.equal(restore(db,db.get(STORE),'players').p10.goals,s.players.p10.goals);
 return {players:6501,chunks:num,unchangedSaveWrites:0,oneChangedPlayerChunks:1,
  codecsSafe:true,historyPreserved:true,crashSafe:true};
}
(async()=>{
 const ui=await uiTest(),worker=await workerTest();
 console.log(JSON.stringify({ok:true,version:'18.349',ui,worker,saveFormatUnchanged:true,
  historyPreserved:true,source:'real production save fragments with synthetic 2031 career'}));
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
"""

def get_helper(src,needle):
    at=src.find(needle)
    if at<0:raise RuntimeError('Missing save engine: '+needle)
    start=src.rfind('/* '+MARK+' */',0,at)
    if start<0:raise RuntimeError('Missing incremental helper before '+needle)
    body=src[start:at]
    if 'v18343Fingerprint' not in body:raise RuntimeError('SHA-256 helper missing')
    return body

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_incremental_saves_calendar_18349.py <project>')
    project=Path(sys.argv[1]).resolve()
    html=(project/'src/index.html').read_text(encoding='utf8')
    assert html.count('/* '+MARK+' */')==2,'Both Worker and UI engines must have the COW extension'
    checks={
      'scrollLimitedOnlyForFullSeason':"listScope==='all'?' v18349-all'" in html,
      'accessibleScrollableRegion':"tabindex='0' role='region'" in html,
      'scrollbarCss':'.v18347-calendar.v18349-all .v18347-list' in html and 'overflow-y:auto' in html,
      'previousCalendarPreserved':'FUTBR_CALENDAR_NAV_VERSION_18348' in html,
      'atomicSavePreserved':'await commitManifest(manifest,old,meta)' in html,
      'seasonsPreserved':'FUTBR_LONG_CAREER_SAVE_18338_BEGIN' in html}
    if not all(checks.values()):raise RuntimeError('Missing regression invariant: '+repr(checks))
    ui_start='async function writeCollection(token,key,value,limit,previous=null){'
    worker_start='async function save(s){'
    ui=get_helper(html,ui_start)+'\n'+jsfunc(html,ui_start)+'\n'+jsfunc(html,"async function saveSharded(s,mode='full'){")
    worker=get_helper(html,worker_start)+'\n'+jsfunc(html,worker_start)
    js='globalThis.UI_CODE='+json.dumps(ui)+';\n'
    js+='globalThis.WORKER_CODE='+json.dumps(worker)+';\n'+TEST
    path=project/'test-incremental-saves-18349.cjs'
    path.write_text(js,encoding='utf8')
    try:
        check=subprocess.run(['node','--check',str(path)],capture_output=True,text=True,timeout=40)
        if check.returncode:raise RuntimeError('JS syntax: '+check.stderr[-7000:])
        run=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=180)
        if run.returncode:raise RuntimeError('Lossless persistence regression: '+(run.stderr or run.stdout)[-15000:])
        report=json.loads(run.stdout.strip().splitlines()[-1])
    finally:
        path.unlink(missing_ok=True)
    report['calendar']=checks
    report['note']='Synthetic career, not measured real-world Windows save time'
    (project/'incremental-saves-calendar-18349-tests.json').write_text(
       json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
