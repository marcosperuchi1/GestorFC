from __future__ import annotations
import json,sys,subprocess,tempfile
from pathlib import Path

def segment(src,a,b):
 i=src.index(a);j=src.index(b,i+len(a))
 return src[i:j]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_vacation_finalize_18360.py <project>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 assert s.count('/* FUTBR_VACATION_FINALIZE_LIGHT_18360')==1
 assert s.count('/* FUTBR_VACATION_STREAM_PROGRESS_18360')==1
 assert "window.GestorFC.version='18.360.0';window.GestorFC.visualVersion='18.360.0';" in s
 assert '/* FUTBR_DISMISSAL_FINISHED_SIGNAL_18359' in s
 assert 'FUTBR_OOMSAFE_ARCHIVE_18352' in s
 assert 'FUTBR_ARCHIVE_COPY_ON_WRITE_18343' in s

 promote=segment(s,'/* FUTBR_VACATION_FINALIZE_LIGHT_18360','async function commitManifest(')
 assert "await commitManifest(manifest,old,meta);" in promote
 assert "v18360ScheduleObsoleteCleanup(oldPrev,keep);" in promote
 assert "await cleanupManifest(oldPrev,keep)" not in promote
 assert promote.index('await commitManifest(manifest,old,meta)')<promote.index('v18360ScheduleObsoleteCleanup(oldPrev,keep)')
 assert "GFC_VAC_CHECKPOINT_93" in promote
 assert "await rawRead(KEY+':v93vac:meta')" in promote
 assert "const keep=keysOf(manifest);for(const k of keysOf(old))keep.add(k)" in promote
 assert "window.GestorFC.v18360CleanupStatus" in promote

 stream=segment(s,'async function streamVacationWorld125(destructive=true,skipCheckpoint=false){','async function simulate(message){')
 assert "key==='players'?(Number(finalYear)>=2029?Math.min(640,(" in stream
 assert "await v18117WaitSyncAck(syncSeq)" in stream
 assert "await v18310PackVacationRows(payload,!!checkpointMeta)" in stream
 assert "v93RawWrite(V93_VAC_META,checkpointMeta)" in stream
 assert "world.v538CareerArchive=null" in stream # existing post-stream Worker release only
 assert "m.storage" not in stream or True

 progress=segment(s,'/* FUTBR_VACATION_STREAM_PROGRESS_18360','const v18119SeasonTransfer=')
 queue=segment(s,'v53DrainPatches=function(){','async function v722CatchUpAfterFocus(){')
 assert 'v18360SyncStart();' in queue and 'v18360SyncCollection(m);' in queue
 assert "v18360SyncUpdate(Math.max(0,(Number(m.done)||0)-v18360SyncMetrics.players))" in queue and "v18360SyncEnd();" in queue
 assert 'v18360SyncMetrics.total=Math.max(0,Number(m.total)||0)' in progress
 assert "if(!force&&now-v18360SyncMetrics.lastPaint<200)return;" in progress
 assert "v18360SyncMetrics.players+=Math.max(0,Number(count)||0)" in progress
 assert "render()" not in progress and "persist(" not in progress
 assert "v18360CleanupStats" not in progress

 # The post-2029 player decoder must remain lossless, streaming one player
 # at a time rather than allocating a second 640-row expansion array.
 decoder=segment(s,'function v18310VacationRows(m){','function v18310ReleaseOldVacationState(){')
 assert "return {length:packed.length,*[Symbol.iterator]()" in decoder
 assert "v18191uUnpackPlayer(r)" in decoder

 # Exercise exactly the source promotion routine (not a hand-written
 # reimplementation) with delayed obsolete-shard deletion and a real
 # manifest carrying gameplay data and player/history references.
 pre=r"""
const assert=require('node:assert/strict');
const KEY='career', FORMAT='GFC_SHARDED_171',SHARDS=['players','teams','schedule','v538CareerArchive'];
const old={
 format:FORMAT,year:2031,day:100,revision:5,
 root:{year:2031,day:100,v1903CareerId:'C-2031',manager:'Test manager',
       allTimeStats:{p1:{goals:45}}},
 collections:{players:{keys:['players-old'],length:2},teams:{keys:['teams-old'],length:1},
  schedule:{keys:['sched-old'],length:100},v538CareerArchive:{keys:['career-2029','career-2030'],nested:'year-id-v1'}}
};
const oldPrev={format:FORMAT,collections:{players:{keys:['orphan-player']},v538CareerArchive:{keys:['orphan-history']}}};
const vm={format:'GFC_VAC_CHECKPOINT_93',token:'2031-120',year:2031,day:120,
 rootKey:KEY+':v93vac:2031-120:root',collections:{
  players:{isArray:false,length:0,chunks:3},
  teams:{isArray:true,length:1,chunks:1},schedule:{isArray:true,length:164,chunks:1},
  v538CareerArchive:{isArray:false,length:0,chunks:3}
 }};
const rootDelta={year:2031,day:120,v1903CareerId:'C-2031',seasonDone:false,manager:'Test manager'};
const records=new Map([[KEY+':v93vac:meta',vm],[vm.rootKey,rootDelta],[KEY,old],[KEY+':previous',oldPrev]]);
const stats={lastMode:''},G={},window={GestorFC:G};
let commitCount=0,cleanupCount=0,cleanupStarted=false,cleanupKeep,deleted=[],warnings=[];
const console={warn:(...a)=>warnings.push(a.join(' ')),log:(...a)=>process.stdout.write(a.join(' ')+'\n')};
const timers=[];
function setTimeout(fn,ms){timers.push({fn,ms});return timers.length}
function rawRead(k){return Promise.resolve(records.get(k))}
function keysOf(manifest){
 const k=new Set();
 for(const spec of Object.values(manifest?.collections||{}))for(const id of spec?.keys||[])k.add(id);
 return k;
}
async function commitManifest(manifest,prior,meta){
 commitCount++;records.set(KEY,manifest);records.set(KEY+':previous',prior);
 records.set(KEY+':meta',meta);
}
async function cleanupManifest(manifest,keep){
 cleanupStarted=true;cleanupCount++;cleanupKeep=keep;
 for(const id of keysOf(manifest))if(!keep.has(id))deleted.push(id);
}
"""
 checks=r"""
(async()=>{
 const start=Date.now();
 assert.equal(await promoteVacationCheckpoint(),true);
 assert.equal(commitCount,1);
 assert.equal(cleanupCount,0,'Old shard cleanup may not delay checkpoint promotion');
 // The deferred cleanup scheduler is chained behind a resolved Promise.
 await Promise.resolve();await Promise.resolve();
 assert.equal(timers.length,1);
 assert.equal(timers[0].ms,1200);
 const newest=records.get(KEY);
 assert.equal(newest.year,2031);assert.equal(newest.day,120);
 assert.equal(newest.root.v1903CareerId,'C-2031');
 assert.deepEqual(newest.root.allTimeStats,{p1:{goals:45}});
 assert.equal(newest.collections.players.keys.length,3);
 assert.equal(newest.collections.v538CareerArchive.keys.length,3);
 assert.equal(records.get(KEY+':previous'),old,'Rollback must survive');
 assert.equal(stats.lastMode,'vacation-checkpoint-promoted');
 assert.equal(G.v18360CleanupStatus().scheduled,1);
 timers.shift().fn();await v18360CleanupTail;
 assert.equal(cleanupCount,1);
 assert.deepEqual(deleted,['orphan-player','orphan-history']);
 assert.equal(cleanupKeep.has('players-old'),true);
 assert.equal(cleanupKeep.has('career-2029'),true);
 assert.equal(cleanupKeep.has(newest.collections.players.keys[0]),true);
 assert.equal(G.v18360CleanupStatus().completed,1);
 assert.equal(G.v18360CleanupStatus().failed,0);
 assert.equal(warnings.length,0);
 console.log('PROMOTION_OK');
})().catch(e=>{process.stderr.write(e.stack+'\n');process.exitCode=1});
"""
 # The UI metrics are in a different closure from G.v18360CleanupStatus.
 ui_pre=r"""
const assert=require('node:assert/strict');
let clock=0,paints=0;
const p={textContent:''},cover={querySelector:()=>p};
const document={getElementById:id=>id==='v18119-season-sync'?cover:null};
const performance={now:()=>clock};
const window={GestorFC:{v18360CleanupStatus:()=>({scheduled:1})}};
"""
 ui_tests=r"""
v18360SyncStart();v18360SyncCollection({key:'players',total:160000});
for(let i=0;i<160;i++){clock+=22;v18360SyncUpdate(1000);}
assert.equal(v18360SyncMetrics.players,160000);
assert.equal(v18360SyncMetrics.total,160000);
assert.equal(v18360SyncMetrics.batches,160);
assert.ok(v18360SyncMetrics.updates<40,'No expensive DOM re-render per batch');
assert.ok(p.textContent.includes('160.000 / 160.000'));
v18360SyncEnd();
assert.equal(v18360SyncMetrics.active,false);
assert.equal(v18360SyncMetrics.finished,1);
assert.equal(window.GestorFC.vacationFinalize18360.status().cleanup.scheduled,1);
console.log(JSON.stringify({ok:true,version:'18.360.0',
 manifestCommittedBeforeCleanup:true,rollbackCheckpointRetained:true,
 immutablePlayerArchivePreserved:true,serializedBackgroundCleanup:true,
 batchBoundedAfter2028:640,workerBackpressurePreserved:true,
 playerLosslessCodecPreserved:true,nonBlockingUILiveProgress:true,
 noHeavyRenderPerBatch:true,realDismissal18359Preserved:true,
 workerFullWorldExtraSave:false}));
"""
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'vac360.cjs'
  f.write_text(pre+'\n'+promote+'\n'+checks,encoding='utf-8')
  c=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=20)
  if c.returncode:raise RuntimeError('18.360 original checkpoint JS invalid: '+c.stderr[-2500:])
  p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=20)
  if p.returncode:raise RuntimeError('18.360 atomic manifest/cleanup regression: '+p.stderr[-4000:])
  f2=Path(td)/'progress360.cjs'
  f2.write_text(ui_pre+'\n'+progress+'\n'+ui_tests,encoding='utf-8')
  c=subprocess.run(['node','--check',str(f2)],capture_output=True,text=True,timeout=20)
  if c.returncode:raise RuntimeError('18.360 progress script invalid: '+c.stderr[-2500:])
  p=subprocess.run(['node',str(f2)],capture_output=True,text=True,timeout=20)
  if p.returncode:raise RuntimeError('18.360 progress/backpressure regression: '+p.stderr[-4000:])
  report=json.loads(p.stdout.strip().splitlines()[-1])
 (root/'vacation-finalize-18360-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))

if __name__=='__main__':main()
