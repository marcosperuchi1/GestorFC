from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path
from test_season_saves_18343 import jsfunc

TEST=r"""
const assert=require('node:assert/strict'),vm=require('node:vm');
const {webcrypto}=require('node:crypto');
const {performance}=require('node:perf_hooks');
const clone=x=>x===undefined?undefined:structuredClone(x);
const archive=()=>{
 const a={},b={};
 for(let year=2026;year<=2033;year++){
  const records={};
  for(let i=0;i<4100;i++)
   records['p'+i]={year,club:'c'+(i%400),goals:i%39,assists:i%12,
    rating:65+(i%30),history:[{year,club:'c'+(i%400),games:32,goals:i%39}],
    natCode:'BRA',custom:{kept:'permanent',flags:[1,2,3,4]}};
  a[year]=records;
  b[year]={};
  for(let i=0;i<1700;i++)b[year]['p'+i]={year,team:'c'+i%120,notes:'temporada preservada'};
 }
 a['2034']={};
 return {a,b};
};
const {a,b}=archive();
const s={year:2033,day:38,seasonDone:true,futbrSaveId:'stable-career',
 v538CareerArchive:a,v555CareerArchive:b,
 players:{p1:{id:'p1',name:'Jogador',goals:44}},
 retirements:[{year:2029,player:'p1',age:37}],
 transfers:[{year:2030,player:'p1',fee:3500000}]};
function decodeDb(db,m,key){
 const spec=m.collections[key],out=spec?.isArray?[]:{};
 for(const ck of spec?.keys||[]){
  const chunk=db.get(ck);assert(chunk,'Missing archive chunk '+ck);
  for(const entry of chunk){
   if(spec.nested==='year-id-v1'){
    const year=String(entry[0]),id=entry[1];
    if(id===null)out[year]=entry[3]===1?{}:clone(entry[2]);
    else (out[year]??={})[id]=clone(entry[2]);
   }else out[entry[0]]=clone(entry[1]);
  }
 }
 return out;
}
async function runUI(){
 const db=new Map(),writes={by:{},fail:false},KEY='SAVE',
 FORMAT='GFC_SHARDED_171',SHARDS=['v538CareerArchive','v555CareerArchive','players','retirements','transfers'];
 const ctx={crypto:webcrypto,TextEncoder,Map,Set,ArrayBuffer,Uint8Array,
  performance,Math,Date,Promise,setTimeout,FORMAT,KEY,SHARDS,state:s,window:{},
  v18121NewSeasonPreparation:false,v53Sim:{},v53PaintStatus(){},
  stats:{playerChunksWritten:0,fullSaves:0,employmentSaves:0},
  v18191mPlayerFormat:'mock-v1',v18191mEncodePlayerChunk:async x=>clone(x),
  shardKey:(...p)=>p.join('|'),rawRead:async k=>clone(db.get(k)),
  rawDelete:async k=>db.delete(k),
  keysOf:m=>new Set(Object.values(m?.collections||{}).flatMap(sp=>sp.keys||[])),
  cleanupManifest:async(m,keep)=>{for(const sp of Object.values(m?.collections||{}))
   for(const k of sp.keys||[])if(!keep.has(k))db.delete(k);},
  commitManifest:async(m,old,meta)=>{
   if(writes.fail)throw Error('disk fail');
   if(old)db.set(KEY+':previous',clone(old));
   db.set(KEY,clone(m));db.set(KEY+':meta',clone(meta));
  },
  v18183DbWriteMany:async entries=>{
   if(writes.fail)throw Error('disk fail');
   for(const e of entries){db.set(e.key,clone(e.value));
    const k=e.key.split('|')[1];writes.by[k]=(writes.by[k]||0)+1;}
  }};
 vm.runInNewContext(globalThis.UI_CODE,ctx);
 const save=()=>vm.runInNewContext('saveSharded(state)',ctx);
 await save();
 const first=clone(db.get(KEY));
 for(const k of ['v538CareerArchive','v555CareerArchive']){
  const spec=first.collections[k];
  assert.equal(spec.nested,'year-id-v1',k+' must be nested');
  assert(spec.keys.length>100,'Large yearly archive must be broken into many small shards');
  assert(spec.hashes.every(h=>h?.length===64),'SHA hashes required for safety');
  assert(spec.keys.every(id=>db.get(id).length<=128),'Huge annual chunk found');
  const expected=k==='v538CareerArchive'?a:b;
  assert.equal(JSON.stringify(decodeDb(db,first,k)),JSON.stringify(expected),'Archive lost members');
 }
 const before={...writes.by};
 await save();
 for(const k of ['v538CareerArchive','v555CareerArchive'])
  assert.equal(writes.by[k],before[k],'Stable history should be reused without writes');
 s.v538CareerArchive[2029].p230.goals++;
 const previous={...writes.by};
 await save();
 assert.equal((writes.by.v538CareerArchive||0)-(previous.v538CareerArchive||0),1,
  'Updating one historical player must only write one shard');
 assert.equal(JSON.stringify(decodeDb(db,db.get(KEY),'v538CareerArchive')),JSON.stringify(a),
  'Updated historical row must round-trip exactly');
 const committed=JSON.stringify(db.get(KEY));
 s.v538CareerArchive[2033].p99.goals++;
 writes.fail=true;
 await assert.rejects(save(),/disk fail/);
 writes.fail=false;
 assert.equal(JSON.stringify(db.get(KEY)),committed,'Interrupted save must keep the last checkpoint');
 await save();
 assert.equal(JSON.stringify(decodeDb(db,db.get(KEY),'v538CareerArchive')),JSON.stringify(a));
 return {years:8,archivePlayersPerYear:4100,chunkLimit:128,
  crcVersion:'year-id-v1',copyOnWrite:true,recoverablePrevious:true};
}
async function runWorker(){
 const db=new Map(),STORE='WORKER',
 V171_FORMAT='GFC_SHARDED_171',V171_SHARDS=['v538CareerArchive','v555CareerArchive','players','retirements','transfers'];
 const writes={by:{},fail:false};
 const ctx={crypto:webcrypto,TextEncoder,Map,Set,ArrayBuffer,Uint8Array,
  performance,Math,Date,Promise,setTimeout,STORE,V171_FORMAT,V171_SHARDS,
  diskRevision:1,checkpoint:null,hostStorage:true,
  safe:id=>!['__proto__','constructor','prototype'].includes(String(id)),
  v171ShardKey:(...p)=>p.join('|'),
  v18191wPlayerFormat:'mock-v1',v18191wEncodePlayerChunk:async x=>clone(x),
  v18191wDecodePlayerChunk:async x=>x,read:async key=>clone(db.get(key)),
  v18181RawWriteMany:async entries=>{
   if(writes.fail)throw Error('worker disk failure');
   for(const e of entries){db.set(e.key,clone(e.value));
    const k=e.key.split('|')[1];writes.by[k]=(writes.by[k]||0)+1;}
  },
  v171DropManifest:async()=>{}};
 vm.runInNewContext(globalThis.WORKER_CODE,ctx);
 const save=()=>{ctx.s=s;return vm.runInNewContext('save(s)',ctx)};
 await save();const latest=db.get(STORE);
 assert.equal(latest.collections.v538CareerArchive.nested,'year-id-v1');
 assert.equal(JSON.stringify(decodeDb(db,latest,'v538CareerArchive')),JSON.stringify(a));
 const restored=await vm.runInNewContext('v171DecodeManifest(await read(STORE))',ctx);
 assert.equal(JSON.stringify(restored.v538CareerArchive),JSON.stringify(a),'Worker restore lost history');
 const oldYear={'2026':{p1:{goals:3}},'2027':{p2:{goals:4}}};
 const legacy={format:V171_FORMAT,year:2028,root:{year:2028},collections:{
  v538CareerArchive:{isArray:false,keys:['legacy'],length:0}}};
 db.set('legacy',Object.entries(oldYear));
 ctx.legacy=legacy;
 const old=await vm.runInNewContext('v171DecodeManifest(legacy)',ctx);
 assert.equal(JSON.stringify(old.v538CareerArchive),JSON.stringify(oldYear),'Legacy unsharded save cannot load');
 const stable={...writes.by};
 await save();
 assert.equal(writes.by.v538CareerArchive,stable.v538CareerArchive,'Worker history must reuse immutable SHA shards');
 s.v555CareerArchive[2028].p47.notes='coisa nova';
 const prev={...writes.by};
 await save();
 assert.equal(writes.by.v555CareerArchive-prev.v555CareerArchive,1,
  'Worker must update only one mutated year/player archive shard');
 const committed=JSON.stringify(db.get(STORE));
 s.v538CareerArchive[2030].p20.goals++;
 writes.fail=true;
 await assert.rejects(save(),/worker disk failure/);
 writes.fail=false;
 assert.equal(JSON.stringify(db.get(STORE)),committed,'Worker save failed without preserving checkpoint');
 await save();
 const valid=db.get(STORE);
 assert.equal(JSON.stringify(decodeDb(db,valid,'v538CareerArchive')),JSON.stringify(a));
 return {oldManifestReadable:true,unmodifiedArchiveReused:true,oneChangedChunkOnly:true,
  workerRecoveryAfterFailure:true,allYearsRetained:true};
}
(async()=>{
 const ui=await runUI(),worker=await runWorker();
 console.log(JSON.stringify({ok:true,version:'18.352.0',ui,worker,
  simulation:'synthetic 2033 eight-season career, not measured Windows memory usage'}));
})().catch(err=>{console.error(err?.stack||err);process.exit(1);});
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_oomsafe_saves_18352.py <project>')
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 if html.count('/* FUTBR_OOMSAFE_ARCHIVE_18352:')!=2:
  raise RuntimeError('Both UI and Worker must have dedicated 18.352 archive helper')
 if not all(k in html for k in [
   'v18352ApplyArchivedRow(dst,entry)',
   "nested:'year-id-v1'",
   "old.collections[key].nested==='year-id-v1'",
   "previous.nested==='year-id-v1'",
   "const EDITION='18.352.0';",
   'FUTBR_SERIEC_PHASES_HISTORY_18351',
   'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349',
   'v18324-open-retirements']):
  raise RuntimeError('Missing save compatibility or previous-game safeguard')
 # Preserve full fingerprint helper and executable real writers.
 ui_anchor='async function writeCollection(token,key,value,limit,previous=null){'
 worker_anchor='async function save(s){'
 def helper(needle):
  i=html.index(needle)
  j=html.rfind('/* FUTBR_OOMSAFE_ARCHIVE_18352:',0,i)
  if j<0:raise RuntimeError('Cannot find nested helper for '+needle)
  return html[j:i]
 ui=helper(ui_anchor)+'\n'+jsfunc(html,ui_anchor)+'\n'+jsfunc(html,"async function saveSharded(s,mode='full'){")
 worker=helper(worker_anchor)+'\n'+jsfunc(html,worker_anchor)+'\n'+jsfunc(html,'async function v171DecodeManifest(x)')
 code='globalThis.UI_CODE='+json.dumps(ui)+';\n'
 code+='globalThis.WORKER_CODE='+json.dumps(worker)+';\n'+TEST
 node=root/'test-oomsafe-18352.cjs'
 node.write_text(code,encoding='utf-8')
 try:
  check=subprocess.run(['node','--check',str(node)],capture_output=True,text=True,timeout=40)
  if check.returncode:raise RuntimeError('JS syntax failure '+check.stderr[-10000:])
  result=subprocess.run(['node','--max-old-space-size=512',str(node)],
   capture_output=True,text=True,timeout=180)
  if result.returncode:raise RuntimeError('Lossless save test failure:\n'+(result.stderr or result.stdout)[-15000:])
  report=json.loads(result.stdout.strip().splitlines()[-1])
 finally:
  node.unlink(missing_ok=True)
 report['formatUnchanged']='GFC_SHARDED_171'
 report['oldCareerSaveLoadPreserved']=True
 report['doesNotDeleteHistoricalData']=True
 (root/'oomsafe-save-18352-tests.json').write_text(
  json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
