from __future__ import annotations
import json,subprocess,sys
from pathlib import Path
from optimize_season_saves_18343 import HELPER,MARK

def jsfunc(source,needle):
    a=source.find(needle)
    if a<0:raise RuntimeError('Missing source routine: '+needle)
    opening=source.find('{',a)
    level=0;quote=None;escaped=False
    for i in range(opening,len(source)):
        c=source[i]
        if quote:
            if escaped:escaped=False
            elif c=='\\':escaped=True
            elif c==quote:quote=None
        else:
            if c in ('"', "'", chr(96)):quote=c
            elif c=='{':level+=1
            elif c=='}':
                level-=1
                if level==0:return source[a:i+1]
    raise RuntimeError('Unbalanced source routine: '+needle)

TEST=r'''
const assert=require('node:assert/strict');
const crypto=require('node:crypto').webcrypto;
const {performance}=require('node:perf_hooks');
const vm=require('node:vm');
const clone=x=>x===undefined?undefined:structuredClone(x);
async function uiTest(){
 const db=new Map(),writes={n:0,by:{},fail:false};
 const FORMAT='GFC_SHARDED_171',KEY='CAREER';
 const SHARDS=['v538CareerArchive','v555CareerArchive','scorerArchive','history','transfers','retirements','internationalHistory','v735NationalArchive','players'];
 const state={year:2026,day:1,seasonDone:true};
 const ctx={crypto,TextEncoder,Map,Set,ArrayBuffer,Uint8Array,
  performance,Math,Date,Promise,setTimeout,FORMAT,KEY,SHARDS,state,window:{},
  v18121NewSeasonPreparation:false,v53Sim:{},v53PaintStatus(){},
  stats:{playerChunksWritten:0,fullSaves:0,employmentSaves:0},
  v18191mPlayerFormat:'synthetic',v18191mEncodePlayerChunk:async x=>clone(x),
  shardKey:(...p)=>p.join('|'),rawRead:async key=>clone(db.get(key)),
  rawDelete:async key=>db.delete(key),
  keysOf:m=>new Set(Object.values(m?.collections||{}).flatMap(spec=>spec.keys||[])),
  cleanupManifest:async(m,keep)=>{
   if(m?.format!==FORMAT)return;
   for(const spec of Object.values(m.collections||{}))
    for(const k of spec.keys||[])if(!keep.has(k))db.delete(k);
  },
  commitManifest:async(m,old,meta)=>{
   if(writes.fail)throw Error('Disk failure');
   if(old)db.set(KEY+':previous',clone(old));
   db.set(KEY,clone(m));db.set(KEY+':meta',clone(meta));
  },
  v18183DbWriteMany:async entries=>{
   if(writes.fail)throw Error('Disk failure');
   for(const e of entries){
    writes.n++;db.set(e.key,clone(e.value));
    const group=e.key.split('|')[1];
    writes.by[group]=(writes.by[group]||0)+1;
   }
  }
 };
 vm.runInNewContext(globalThis.UICODE,ctx);
 const save=()=>vm.runInNewContext('saveSharded(state)',ctx);
 const a={};
 for(let i=0;i<640;i++){
  const key='p'+i;
  a[key]={id:key,name:'Atleta '+i,goals:i%30,assists:i%12,allTime:{
   career:[{season:2026,club:'c'+(i%30),goals:i%27}]},extras:{star:i%7===0}};
 }
 state.v538CareerArchive=a;
 state.v555CareerArchive=clone(a);
 state.scorerArchive=[{year:2026,players:{p1:{goals:15}}}];
 state.players={p1:{id:'p1',age:26,goals:12}};
 state.history=[{year:2026,champion:'c1'}];
 state.internationalHistory=[{year:2026,champion:'BRA'}];
 state.transfers=[{player:'p1',from:'a',to:'b'}];
 state.retirements=[{player:'p0',year:2026}];
 state.v735NationalArchive=[{year:2026,BRA:{points:5}}];
 db.set(KEY,{format:FORMAT,year:2025,day:365,revision:1,
  root:{},collections:{v538CareerArchive:{isArray:false,keys:[],length:0}}});
 await save();let first=clone(db.get(KEY));
 assert.equal(first.collections.v538CareerArchive.keys.length,20,'32-record historical grouping');
 assert.equal(first.collections.v555CareerArchive.keys.length,20);
 assert.equal(first.collections.scorerArchive.keys.length,1,'scorer years isolated');
 assert.ok(first.collections.v538CareerArchive.hashes.every(h=>h.length===64),'SHA-256 hashes');
 function load(manifest,key){
  const target=manifest.collections[key].isArray?[]:{};
  for(const id of manifest.collections[key].keys){
   const data=db.get(id);
   assert.ok(data,'missing archived shard '+id);
   for(const [k,value] of data)target[k]=clone(value);
  }
  return target;
 }
 assert.deepEqual(load(first,'v538CareerArchive'),clone(a));
 state.year=2027;
 a.p640={id:'p640',name:'Novo',goals:2,allTime:{career:[{season:2027,goals:2}]}};
 state.v555CareerArchive.p640=clone(a.p640);
 state.scorerArchive.push({year:2027,players:{p4:{goals:20}}});
 const before=writes.by.v538CareerArchive;
 await save();let second=clone(db.get(KEY));
 assert.equal(writes.by.v538CareerArchive-before,1,'Only the appended historical shard must be written');
 assert.equal(second.collections.v538CareerArchive.keys[0],first.collections.v538CareerArchive.keys[0]);
 assert.equal(second.collections.scorerArchive.keys[0],first.collections.scorerArchive.keys[0]);
 assert.deepEqual(load(second,'scorerArchive'),clone(state.scorerArchive));
 assert.deepEqual(load(second,'v538CareerArchive'),clone(a));
 state.year=2028;a.p3.goals+=1;
 const beforeChange=writes.by.v538CareerArchive;
 await save();let third=clone(db.get(KEY));
 assert.equal(writes.by.v538CareerArchive-beforeChange,1,'Edited history forces re-encode');
 assert.notEqual(third.collections.v538CareerArchive.keys[0],second.collections.v538CareerArchive.keys[0]);
 assert.equal(third.collections.v538CareerArchive.keys[1],second.collections.v538CareerArchive.keys[1]);
 const manifest=JSON.stringify(db.get(KEY));
 state.year=2029;a.p5.goals+=1;writes.fail=true;
 await assert.rejects(save(),/Disk failure/);
 writes.fail=false;
 assert.equal(JSON.stringify(db.get(KEY)),manifest,'Failed save cannot change committed checkpoint');
 assert.equal(load(db.get(KEY),'v538CareerArchive').p5.goals,a.p5.goals-1);
 await save();
 assert.equal(load(db.get(KEY),'v538CareerArchive').p5.goals,a.p5.goals);
 return {ok:true,yearRange:'2026-2029',entries:641,chunks:20,
  unchangedChunksReused:true,changedHistoryRewritten:true,
  previousSnapshotRemainsRecoverable:true,scorerRowsPreserved:true};
}
async function workerTest(){
 const db=new Map();let writes=0;
 const STORE='S',V171_FORMAT='GFC_SHARDED_171';
 const ctx={crypto,TextEncoder,Map,Set,ArrayBuffer,Uint8Array,
  performance,Math,Date,Promise,setTimeout,
  STORE,V171_FORMAT,V171_SHARDS:['v538CareerArchive','scorerArchive','players'],
  diskRevision:1,checkpoint:null,hostStorage:true,
  safe:id=>id!=='__proto__',v171ShardKey:(...p)=>p.join('|'),
  v18191wPlayerFormat:'test',v18191wEncodePlayerChunk:async x=>clone(x),
  read:async k=>clone(db.get(k)),
  v18181RawWriteMany:async entries=>{for(const e of entries){writes++;db.set(e.key,clone(e.value));}},
  v171DropManifest:async (m,keep)=>{
   if(m?.format!==V171_FORMAT)return;
   for(const spec of Object.values(m.collections||{}))
    for(const k of spec.keys||[])if(!keep.has(k))db.delete(k);
  }
 };
 vm.runInNewContext(globalThis.WORKERCODE,ctx);
 const save=s=>{ctx.s=s;return vm.runInNewContext('save(s)',ctx)};
 const rows={};
 for(let i=0;i<640;i++)rows['p'+i]={goals:i%22,byYear:{2026:i%12}};
 const s={year:2026,day:1,seasonDone:true,v538CareerArchive:rows,
  scorerArchive:[{year:2026,p1:{goals:4}}],players:{p1:{age:20}}};
 await save(s);const first=clone(db.get(STORE));
 assert.equal(first.collections.v538CareerArchive.keys.length,20);
 s.year=2027;s.v538CareerArchive={...rows,p640:{goals:13}};
 s.scorerArchive=[...s.scorerArchive,{year:2027,p2:{goals:9}}];
 const before=writes;
 await save(s);const second=clone(db.get(STORE));
 assert.equal(first.collections.v538CareerArchive.keys[0],second.collections.v538CareerArchive.keys[0]);
 assert.equal(first.collections.scorerArchive.keys[0],second.collections.scorerArchive.keys[0]);
 assert.ok(writes-before<=7,'Worker writes only changed archive chunks');
 const restored={};
 for(const k of second.collections.v538CareerArchive.keys)
  for(const [id,v] of db.get(k))restored[id]=v;
 assert.equal(Object.keys(restored).length,641);
 assert.equal(restored.p640.goals,13);
 return {ok:true,entries:641,hashBasedReuse:true,allRowsPersist:true,additionalWriteOperations:writes-before};
}
(async()=>{
 const ui=await uiTest(),worker=await workerTest();
 console.log(JSON.stringify({ok:true,version:'18.343',ui,worker,
  userSavesUntouched:true,archivalDataPreserved:true}));
})().catch(e=>{console.error(e.stack||e);process.exit(1)});
'''

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_season_saves_18343.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src/index.html').read_text(encoding='utf-8')
    if html.count(MARK)!=2:raise RuntimeError('Both worker and UI SHA-256 helpers are required')
    ui=jsfunc(html,'async function writeCollection(token,key,value,limit,previous=null){')
    save=jsfunc(html,"async function saveSharded(s,mode='full'){")
    worker=jsfunc(html,'async function save(s){')
    if 'v18343Fingerprint' not in ui or 'v18343Fingerprint' not in worker:
        raise RuntimeError('Archive hash not enabled for both persistence engines')
    if 'writeCollection(token,key,value,v18343HistoricalLimit(key,limit)' not in save:
        raise RuntimeError('Archive history reuse not wired into commit')
    js='globalThis.UICODE='+json.dumps(HELPER+'\n'+ui+'\n'+save)+';\n'
    js+='globalThis.WORKERCODE='+json.dumps(HELPER+'\n'+worker)+';\n'+TEST
    path=root/'test-season-save-18343.cjs'
    path.write_text(js,encoding='utf-8')
    try:
        check=subprocess.run(['node','--check',str(path)],capture_output=True,text=True,timeout=30)
        if check.returncode:raise RuntimeError('JavaScript syntax: '+check.stderr[-4000:])
        run=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=120)
        if run.returncode:raise RuntimeError('Synthetic 2026-2029 integrity: '+(run.stderr or run.stdout)[-7000:])
        result=json.loads(run.stdout.splitlines()[-1])
    finally:
        path.unlink(missing_ok=True)
    if not result['ok']:raise RuntimeError('Long-career save regression did not pass')
    (root/'season-save-18343-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
