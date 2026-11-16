from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

def fragment(src,start,end):
    a=src.find(start)
    b=src.find(end,a+len(start)) if a>=0 else -1
    if a<0 or b<0:raise RuntimeError('18.338 fragment missing: '+start)
    return src[a:b]

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: test_long_career_saves_18338.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    s=(root/'src/index.html').read_text(encoding='utf-8')
    body=fragment(s,'/* FUTBR_LONG_CAREER_SAVE_18338_BEGIN','/* FUTBR_LONG_CAREER_SAVE_18338_END */')+'/* FUTBR_LONG_CAREER_SAVE_18338_END */'
    write=fragment(s,'async function writeCollection(token,key,value,limit){','async function saveSharded(s,mode=')
    release=fragment(s,'function v18338FreeTransientBeforeSave(){','  const basePersist=persist;')
    anchors=[
      "const target=key==='players'?(Number(state?.year)>=2029?2:4)",
      "const limit=key==='players'?(Number(s.year)>=2029?800:1600)",
      "const target=key==='players'?(Number(s.year)>=2029?2:4)",
      "limit=key==='players'?(Number(s.year)>=2029?800:1600)",
      "stride=key==='players'?(Number(manifest.year)>=2029?4:8)",
      "if(saveOK&&!v52SaveDirty&&v52PendingState===current)v52PendingState=null",
      "v5CrestsOut();v18338FreeTransientBeforeSave();const result=await saveSharded(current,mode)",
      "await commitManifest(manifest,old,meta)",
      "v18310VacationRows(m)",
      "v538CareerArchive","v555CareerArchive","scorerArchive",
      "allTimeStats","internationalHistory","v735NationalArchive",
    ]
    for marker in anchors:
        if marker not in s: raise RuntimeError('18.338 required invariant missing: '+marker)
    harness=r"""
const vm=require('node:vm'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const mkManifest=(state)=>({format:'GFC_SHARDED_171',year:state.year,day:state.day,
 root:{v1903CareerId:state.v1903CareerId,futbrSaveId:state.futbrSaveId,seasonDone:state.seasonDone},
 collections:{players:{keys:['existing-shard']},scorerArchive:{keys:['archive-2028']}}});
const state={year:2031,day:81,seasonDone:false,live:null,
 futbrSaveId:'my-2031-save',v1903CareerId:'career-unique-2031',
 playerCareer:{totalGoals:321},scorerArchive:[{year:2030,goals:123}],
 transfers:[{year:2029,playerId:'p77'}],retirements:[{year:2028,id:'p3'}]};
const before=JSON.stringify({career:state.playerCareer,scorers:state.scorerArchive,transfers:state.transfers,retirements:state.retirements});
let checkpoint=mkManifest(state),writes=0,broken=false;
const ctx={
 state,saveOK:true,v52SavePromise:null,v52SaveDirty:false,v52PendingState:state,v52Processing:false,
 v168DeferredRolloverSave:false,v53Sim:{active:false,starting:false,syncing:false,patching:false},
 v53Creating:false,v53Worker:null,BASE:'base',FORMAT:'GFC_SHARDED_171',
 window:{GestorFC:{}},get:async()=>checkpoint,
 persist:()=>{ctx.v52SaveDirty=true;ctx.v52PendingState=ctx.state;return Promise.resolve()},
 v52FlushSave:async()=>{
  writes++;if(broken){ctx.saveOK=false;ctx.v52SaveDirty=false;return;}
  checkpoint=mkManifest(ctx.state);ctx.saveOK=true;ctx.v52SaveDirty=false;ctx.v52PendingState=null;
 }
};
const context=vm.createContext(ctx);
vm.runInContext(globalThis.PATCH,context);
const call=()=>vm.runInContext('ensureSaved()',context);
async function test(){
 assert.equal((await call()).year,2031);
 assert.equal(writes,0,'A stale pointer must not trigger 2031 full rewrite');
 assert.equal(ctx.v52PendingState,null);
 assert.equal(ctx.window.GestorFC.longCareerSave18338.status().reused,1);
 ctx.v52PendingState=state;ctx.v52SaveDirty=true;await call();
 assert.equal(writes,1,'Unsaved gameplay must still be persisted');
 state.day++;await call();assert.equal(writes,2,'New round must be committed');
 state.futbrSaveId='separate-copy';await call();assert.equal(writes,3,'New save identity must be committed');
 state.v1903CareerId='other-career';await call();assert.equal(writes,4,'Career identity must be protected');
 state.seasonDone=true;await call();assert.equal(writes,5,'Season closure must be committed');
 ctx.v168DeferredRolloverSave=true;await call();assert.equal(writes,6,'Unpersisted rollover must never be skipped');
 ctx.v168DeferredRolloverSave=false;
 const stable=JSON.stringify(checkpoint);
 state.day++;broken=true;
 await assert.rejects(call(),/não corresponde à carreira|salvamento/i);
 assert.equal(JSON.stringify(checkpoint),stable,'Failed save preserves previous durable checkpoint');
 assert.equal(ctx.saveOK,false);
 broken=false;await call();assert.equal(ctx.saveOK,true);
 assert.equal(JSON.stringify({career:state.playerCareer,scorers:state.scorerArchive,transfers:state.transfers,retirements:state.retirements}),before,'History changed during save');
 const status=ctx.window.GestorFC.longCareerSave18338.status();
 assert.equal(status.reused,1);assert.equal(status.rewritten,7);
 return {writes,reused:status.reused,rewritten:status.rewritten};
}
globalThis.TEST=test;
"""
    chunk_harness=r"""
const assert=require('node:assert/strict'),crypto=require('node:crypto');
let state={year:2031},writes=[],db=new Map();
const stats={playerChunksWritten:0};
const v18121NewSeasonPreparation=false;
const v53Sim={};
const v18191mPlayerFormat='synthetic-packed-18338';
const v18191mEncodePlayerChunk=async rows=>({format:v18191mPlayerFormat,count:rows.length,rows:rows.map(([id,p])=>[id,JSON.parse(JSON.stringify(p))])});
const v18183DbWriteMany=async entries=>{
 writes.push(entries.length);
 if(entries.length>2)throw Error('Unbounded native IPC batch');
 for(const entry of entries)db.set(entry.key,entry.value);
};
const shardKey=(token,key,i)=>[token,key,i].join('|');
const v53PaintStatus=()=>{};
"""
    chunk_tests=r"""
async function chunkTest(){
 const count=6053,players={};
 for(let i=0;i<count;i++){const id='p'+i;players[id]={id,age:18+(i%25),goals:i%37,assists:i%9,
   attrs:{ovr:45+(i%50),support:{nationality:'BRA',historicalG:i%43}},
   honors:[{year:2028,comp:'league',place:i%5}],extraField:'retained'};}
 const h=crypto.createHash('sha256').update(JSON.stringify(players)).digest('hex');
 const spec=await writeCollection('2031','players',players,800);
 assert.equal(spec.keys.length,Math.ceil(count/800));
 assert.ok(writes.every(x=>x<=2),'No large IPC payload');
 let restored={};
 for(const key of spec.keys){
  const payload=db.get(key);assert.ok(payload.count<=800);
  for(const [id,p] of payload.rows)restored[id]=p;
 }
 const digest=crypto.createHash('sha256').update(JSON.stringify(restored)).digest('hex');
 assert.equal(digest,h,'Every player, extra field and history must round-trip');
 assert.equal(stats.playerChunksWritten,spec.keys.length);
 const history={y2027:{a:{goals:12}},y2028:{a:{goals:28,assists:7}}};
 const second=await writeCollection('2031','scorerArchive',history,1);
 assert.equal(second.keys.length,2);
 assert.equal(db.get(second.keys[1])[0][1].a.assists,7);
 return {players:count,playerChunks:spec.keys.length,maxNativeBatch:Math.max(...writes),
  retainedPlayerExtras:true,retainedScorerArchive:true};
}
"""
    release_harness=r"""
const G={v168:{stop:()=>{},purge:()=>{}}};
const v53Sim={active:false,starting:false,syncing:false,patching:false};
let v53Creating=false,v18119SeasonTransfer={active:false};
const v53RPC=new Map();
let killed=0,v53Worker={terminate(){killed++;}},v53WorkerReady=Promise.resolve();
"""
    release_tests=r"""
function releaseTest(){
 assert.equal(v18338FreeTransientBeforeSave(),true);
 assert.equal(killed,1);
 v53Worker={terminate(){killed++;}};
 v53Sim.active=true;assert.equal(v18338FreeTransientBeforeSave(),false);
 assert.equal(killed,1);v53Sim.active=false;
 v53RPC.set(1,{pending:true});assert.equal(v18338FreeTransientBeforeSave(),false);
 assert.equal(killed,1);v53RPC.clear();
 v18119SeasonTransfer.active=true;assert.equal(v18338FreeTransientBeforeSave(),false);
 assert.equal(killed,1);v18119SeasonTransfer.active=false;
 assert.equal(v18338FreeTransientBeforeSave(),true);assert.equal(killed,2);
 return {releases:2,noConcurrentWorkerTermination:true};
}
"""
    node=f"""globalThis.PATCH={json.dumps(body)};
{harness}
(async()=>{{
 const save=await TEST();
 const chunk=await (async()=>{{
 {chunk_harness}
 {write}
 {chunk_tests}
 return chunkTest();
 }})();
 const release=(function(){{
 {release_harness}
 {release}
 {release_tests}
 return releaseTest();
 }})();
 console.log(JSON.stringify({{'ok':true,'version':'18.338','case':'synthetic-2031 (not actual user save)',save,chunk,release}}));
}})().catch(e=>{{console.error(e);process.exit(1)}});
"""
    test=root/'test-long-career-saves-18338.cjs'
    test.write_text(node,encoding='utf-8')
    try:
        check=subprocess.run(['node','--check',str(test)],capture_output=True,text=True,timeout=25)
        if check.returncode:raise RuntimeError('Node syntax: '+check.stderr[-4000:])
        run=subprocess.run(['node',str(test)],capture_output=True,text=True,timeout=50)
        if run.returncode:raise RuntimeError('Node runtime: '+(run.stderr or run.stdout)[-5000:])
        result=json.loads(run.stdout.strip().splitlines()[-1])
        if not result.get('ok'):raise RuntimeError('18.338 synthetic 2031 regression failed')
    finally:
        test.unlink(missing_ok=True)
    (root/'long-career-saves-18338-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
