from __future__ import annotations
import json,sys
from pathlib import Path

VERSION='18.360.0'
MARK='FUTBR_VACATION_FINALIZE_LIGHT_18360'

def once(s,old,new,label):
    n=s.count(old)
    if n!=1:raise RuntimeError(f'18.360 {label}: expected one exact anchor, got {n}')
    return s.replace(old,new,1)

DEFERRED_CLEANUP=r"""
/* FUTBR_VACATION_FINALIZE_LIGHT_18360
   After the manifest was committed atomically, reclaiming old, now
   unreferenced shards is housekeeping, NOT a reason to block the completed
   vacation / leave the entire game inert. Keep latest+previous manifests. */
let v18360CleanupTail=Promise.resolve();
const v18360CleanupStats={scheduled:0,completed:0,failed:0,active:false,lastError:''};
function v18360ScheduleObsoleteCleanup(oldManifest,keep){
 v18360CleanupStats.scheduled++;
 // Serial queue, not concurrent deletion. The 1.2s grace period permits
 // completion to render and lets a user stop or open the Career page.
 v18360CleanupTail=v18360CleanupTail.catch(()=>{}).then(()=>new Promise(r=>setTimeout(r,1200)))
  .then(async()=>{
   v18360CleanupStats.active=true;
   try{await cleanupManifest(oldManifest,keep);v18360CleanupStats.completed++;}
   catch(e){v18360CleanupStats.failed++;v18360CleanupStats.lastError=e?.message||String(e);
    console.warn('[18.360] Stale checkpoint cleanup deferred:',e);}
   finally{v18360CleanupStats.active=false;}
  });
 return true;
}
window.GestorFC.v18360CleanupStatus=()=>({...v18360CleanupStats});
"""

TRANSFER_PROGRESS=r"""
/* FUTBR_VACATION_STREAM_PROGRESS_18360
   Paint one small text node, not the entire world/UI, with real counts.
   At most five DOM writes per second; checkpoint integrity is unaffected. */
const v18360SyncMetrics={version:'18.360',active:false,started:0,players:0,total:0,
 batches:0,updates:0,elapsedMs:0,lastPaint:0,finished:0,playerLimit:640};
function v18360SyncStart(){
 v18360SyncMetrics.active=true;v18360SyncMetrics.started=performance.now();
 v18360SyncMetrics.players=0;v18360SyncMetrics.total=0;v18360SyncMetrics.batches=0;
 v18360SyncMetrics.updates=0;v18360SyncMetrics.lastPaint=0;v18360SyncMetrics.elapsedMs=0;
}
function v18360SyncCollection(m){
 if(m?.key!=='players')return;
 v18360SyncMetrics.total=Math.max(0,Number(m.total)||0);
 v18360SyncUpdate(0,true);
}
function v18360SyncUpdate(count=0,force=false){
 if(!v18360SyncMetrics.active)return;
 v18360SyncMetrics.players+=Math.max(0,Number(count)||0);
 if(count)v18360SyncMetrics.batches++;
 const now=performance.now();v18360SyncMetrics.elapsedMs=Math.round(now-v18360SyncMetrics.started);
 if(!force&&now-v18360SyncMetrics.lastPaint<200)return;
 v18360SyncMetrics.lastPaint=now;
 const el=document.getElementById('v18119-season-sync')?.querySelector('.v18119-sync-dialog p');
 if(!el)return;
 const n=v18360SyncMetrics.players,total=v18360SyncMetrics.total;
 const pct=total?Math.min(99,Math.round(n/total*100)):0;
 const text=total
  ?'Sincronizando jogadores '+n.toLocaleString('pt-BR')+' / '+total.toLocaleString('pt-BR')+' ('+pct+'%). Histórico e salvamento preservados.'
  :'Preparando os dados da temporada sem recarregar a carreira.';
 if(el.textContent!==text){el.textContent=text;v18360SyncMetrics.updates++;}
}
function v18360SyncEnd(){
 v18360SyncMetrics.active=false;v18360SyncMetrics.finished++;
 v18360SyncMetrics.elapsedMs=Math.round(performance.now()-v18360SyncMetrics.started);
}
window.GestorFC=window.GestorFC||{};
window.GestorFC.vacationFinalize18360={
 version:'18.360',status:()=>({...v18360SyncMetrics,cleanup:window.GestorFC.v18360CleanupStatus?.()||{}}),
 noExtraFullSave:true,onePlayerBatchAtATime:true,atomicManifestUnchanged:true
};
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: optimize_vacation_finalize_18360.py <project>')
 root=Path(sys.argv[1]);p=root/'src/index.html'
 src=p.read_text(encoding='utf-8')
 if MARK in src:raise RuntimeError('18.360 patch already installed')
 for marker in ('FUTBR_DISMISSAL_FINISHED_SIGNAL_18359','FUTBR_OOMSAFE_ARCHIVE_18352',
                'FUTBR_LONG_CAREER_SAVE_18338_BEGIN','FUTBR_CLEAN_INCREMENTAL_SHARDS_18349',
                'FUTBR_ARCHIVE_COPY_ON_WRITE_18343','async function promoteVacationCheckpoint(){',
                'async function streamVacationWorld125(destructive=true,skipCheckpoint=false){',
                'function v18310VacationRows(m){','v53DrainPatches=function(){'):
  if marker not in src:raise RuntimeError('Required release baseline not found: '+marker)

 # Post-commit work currently awaits deletion of thousands of old shards,
 # which makes the user wait even though the new checkpoint already exists.
 # The cleanup is not part of the atomic transaction. Keep the manifests
 # for the two recoverable generations unchanged.
 start=src.index('async function promoteVacationCheckpoint(){')
 end=src.index('async function commitManifest(',start)
 part=src[start:end]
 # Production 18.313 already made deletion nonblocking. Delay the
 # *existing* cleanup rather than introduce a second full-history walk.
 # The manifest and previous generation stay atomically committed.
 patterns=[
  'await cleanupManifest(oldPrev,keep);stats.lastMode',
  "cleanupManifest(oldPrev,keep).catch(e=>console.warn('[18.313] limpeza pos-checkpoint:',e?.message||e));stats.lastMode"
 ]
 present=[p for p in patterns if p in part]
 if len(present)!=1:
  at=part.find('cleanupManifest')
  raise RuntimeError('18.360 unknown production checkpoint cleanup: '+
   repr(part[max(0,at-320):at+500] if at>=0 else part[-900:]))
 part=once(part,present[0],
    'v18360ScheduleObsoleteCleanup(oldPrev,keep);stats.lastMode',
    'defer and serialize existing post-commit checkpoint deletion')
 src=src[:start]+part+src[end:]
 src=once(src,'async function promoteVacationCheckpoint(){',
          DEFERRED_CLEANUP+'\nasync function promoteVacationCheckpoint(){',
          'install serial post-commit cleanup in original 17.1 closure')

 # The Worker still sends 900 packed players per UI message and holds a
 # backlog of four compressed chunks. Cap transient pack/JSON/IPC buffers for
 # long (>2028) careers with no changes to player fields or archive format.
 a=src.index('async function streamVacationWorld125(destructive=true,skipCheckpoint=false){')
 b=src.index('async function simulate(message){',a)
 stream=src[a:b]
 # Earlier 18.3xx memory patches may already have lowered the old
 # 900-row limit. Preserve that earlier bound; never raise it.
 import re
 pat=r"(?P<prefix>\blimit\s*=\s*key\s*===\s*'players'\s*\?\s*)(?P<limit>.*?)(?P<suffix>\s*:\s*key\s*===\s*'competitionStats'\s*\?\s*1)"
 found=list(re.finditer(pat,stream,re.DOTALL))
 if len(found)!=1 or len(found[0].group('limit'))>150:
  at=stream.find("key==='players'")
  raise RuntimeError('18.360 player-stream limit shape changed: '+
   repr(stream[max(0,at-120):at+450]))
 old=found[0].group('limit').strip()
 if 'v18360' in old:raise RuntimeError('18.360 batch bound already installed')
 limited=f"(Number(finalYear)>=2029?Math.min(640,({old})):({old}))"
 stream=stream[:found[0].start('limit')]+limited+stream[found[0].end('limit'):]
 print('18.360 active production player-stream limit:',old,'new:',limited,flush=True)
 src=src[:a]+stream+src[b:]

 # Record real throughput and display sync progress in the overlay using
 # the already-present mandatory worker->UI ACK protocol.
 src=once(src,'const v18119SeasonTransfer={active:false',
       TRANSFER_PROGRESS+'\nconst v18119SeasonTransfer={active:false',
       'add light UI transfer telemetry')
 a=src.rindex('v53DrainPatches=function(){')
 b=src.index('\nasync function v722CatchUpAfterFocus(){',a)
 ui=src[a:b]
 ui=once(ui,"if(m.kind==='vac-sync-start'){",
          "if(m.kind==='vac-sync-start'){\n    v18360SyncStart();",
          'mark transfer started on authoritative UI stream')
 ui=once(ui,"if(m.kind==='vac-sync-collection-start'){\n    if(!v125VacIncoming)continue;",
          "if(m.kind==='vac-sync-collection-start'){\n    if(!v125VacIncoming)continue;\n    v18360SyncCollection(m);",
          'read actual total from worker collection header')
 # Later releases stream packed players with an iterable decoder; the
 # old "rows.length" counter is not a stable anchor anymore. Use the
 # authoritative cumulative m.done sent by the Worker, but only after the
 # UI has applied the entire batch and posted its acknowledgment.
 begin=ui.index("if(m.kind==='vac-sync-part'){")
 end=ui.index("if(m.kind==='vac-sync-collection-end')",begin)
 part=ui[begin:end]
 tail=part.rfind('continue;')
 if tail<0 or 'vac-sync-ack' not in part or tail<=part.rfind('vac-sync-ack'):
  raise RuntimeError('18.360 vacation UI ACK handler changed, cannot count installed players')
 part=part[:tail]+(
  "if(m.key==='players')v18360SyncUpdate(Math.max(0,(Number(m.done)||0)-v18360SyncMetrics.players));\n    "
 )+part[tail:]
 ui=ui[:begin]+part+ui[end:]
 ui=once(ui,"if(m.kind==='vac-sync-end'){",
          "if(m.kind==='vac-sync-end'){\n    v18360SyncEnd();",
          'mark transfer complete before releasing overlay')
 src=src[:a]+ui+src[b:]

 # Users see the real signed version in the welcome/sidebar.
 src=once(src,"const EDITION='18.359.0';","const EDITION='18.360.0';",'edition')
 src=once(src,"window.GestorFC.version='18.359.0';window.GestorFC.visualVersion='18.359.0';",
          "window.GestorFC.version='18.360.0';window.GestorFC.visualVersion='18.360.0';",'runtime version')
 p.write_text(src,encoding='utf-8')
 report={
  'ok':True,'version':VERSION,
  'atomicCheckpointCommitPreserved':True,
  'oldCheckpointsRetainedUntilNextGeneration':True,
  'obsoleteShardCleanupNonBlocking':True,
  'cleanupSerialized':True,
  'boundedPlayerBatchAfter2028':640,
  'originalPlayerCodecUnchanged':True,
  'workerBackpressurePreserved':True,
  'playerArchiveAndStatsPreserved':True,
  'newFullWorldSaveAdded':False,
  'renderPerBatchAdded':False,
  'progressReadFromActualRows':True
 }
 (root/'vacation-finalize-18360-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
