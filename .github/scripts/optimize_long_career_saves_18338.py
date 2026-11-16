from __future__ import annotations
import json
import sys
from pathlib import Path

VERSION = "18.338"

def once(text: str, old: str, new: str, label: str) -> str:
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f"18.338 {label}: expected exactly one source anchor, got {count}")
    return text.replace(old,new,1)

OLD_ENSURE = """async function ensureSaved(){
  if(v53Sim?.active||v53Sim?.starting||v53Creating||v52Processing)throw Error('Aguarde a simulação terminar ou pause as férias para salvar.');
  let x=await get(BASE).catch(()=>null);const clean=!!state&&!v52SavePromise&&!v52SaveDirty&&!v52PendingState&&x?.format===FORMAT&&Number(x.year)===Number(state.year)&&Number(x.day)===Number(state.day);
  if(state&&!clean){const p=persist(false);await v52FlushSave();await p;if(v52SavePromise)await v52SavePromise;x=await get(BASE).catch(()=>null);}
  if(x?.format!==FORMAT||!saveOK)throw Error('O salvamento ainda não foi confirmado. Aguarde e tente novamente.');
  return x;
}"""

NEW_ENSURE = """/* FUTBR_LONG_CAREER_SAVE_18338_BEGIN
   Trust only the committed checkpoint. A pending-state reference is not dirty
   state: previous versions kept it forever, causing a 200k-player rewrite
   every time "Salvar e sair" was clicked. Verify the save identity, career,
   year, day and season closure before reusing an already durable checkpoint. */
const v18338SaveAudit={version:'18.338',reused:0,rewritten:0,last:'',preservesStats:true};
async function ensureSaved(){
  if(v53Sim?.active||v53Sim?.starting||v53Creating||v52Processing||v53Sim?.syncing||v53Sim?.patching)
   throw Error('Aguarde a simulação ou a sincronização terminar antes de salvar.');
  if(!state)throw Error('Nenhuma carreira aberta para salvar.');
  const matches=x=>x?.format===FORMAT&&Number(x.year)===Number(state.year)&&
   Number(x.day)===Number(state.day)&&
   String(x.root?.v1903CareerId||'')===String(state.v1903CareerId||'')&&
   String(x.root?.futbrSaveId||'')===String(state.futbrSaveId||'')&&
   !!x.root?.seasonDone===!!state.seasonDone;
  let x=await get(BASE).catch(()=>null);
  // Never reuse the previous season when the 16.8/18.311 deferred save is pending.
  const clean=matches(x)&&saveOK&&!v52SaveDirty&&!v52SavePromise&&!v168DeferredRolloverSave;
  if(!clean){
   const p=persist(false);
   await v52FlushSave();
   await p;
   if(v52SavePromise)await v52SavePromise;
   x=await get(BASE).catch(()=>null);
   v18338SaveAudit.rewritten++;
   v18338SaveAudit.last='new-atomic-checkpoint';
  }else{
   // Old versions left v52PendingState pointing to the last saved state.
   if(v52PendingState===state)v52PendingState=null;
   v18338SaveAudit.reused++;
   v18338SaveAudit.last='verified-existing-checkpoint';
  }
  if(!matches(x)||!saveOK||v52SaveDirty||v52SavePromise)
   throw Error('O salvamento não corresponde à carreira e à jornada atuais. A cópia anterior foi preservada; tente salvar novamente.');
  // A successful explicit save also finishes a 16.8 deferred rollover.
  if(v168DeferredRolloverSave)v168DeferredRolloverSave=false;
  return x;
}
/* FUTBR_LONG_CAREER_SAVE_18338_END */
window.GestorFC=window.GestorFC||{};
window.GestorFC.longCareerSave18338={
 version:'18.338',status:()=>({...v18338SaveAudit,
  year:Number(state?.year)||0,day:Number(state?.day)||0,
  dirty:!!v52SaveDirty,saving:!!v52SavePromise,
  deferred:!!v168DeferredRolloverSave,worker:!!v53Worker})
};"""

NATIVE_RELEASE = """function v18338FreeTransientBeforeSave(){
  // Worker can hold another entire 200k-player universe. Reclaim it BEFORE
  // creating compression buffers and native IPC payloads, never after.
  if(v53Sim?.active||v53Sim?.starting||v53Sim?.syncing||v53Sim?.patching||
     v53Creating||v18119SeasonTransfer?.active)return false;
  try{G.v168?.stop?.();G.v168?.purge?.();}catch(e){}
  try{
   if(v53Worker&&(!v53RPC||v53RPC.size===0)){
    v53Worker.terminate();v53Worker=null;v53WorkerReady=null;
    return true;
   }
  }catch(e){console.warn('[18.338] idle Worker release',e);}
  return false;
}
"""

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: optimize_long_career_saves_18338.py <project-dir>")
    project=Path(sys.argv[1]).resolve()
    path=project/'src'/'index.html'
    src=path.read_text(encoding='utf-8')
    if 'FUTBR_LONG_CAREER_SAVE_18338_BEGIN' in src:
        raise RuntimeError('18.338 already installed; start with a clean source')
    for marker in ('FUTBR_UNEMPLOYED_RESUME_18334_BEGIN','FUTBR_MANUAL_ADVANCE_18326_START','function v18183DbWriteMany','async function saveSharded'):
        if marker not in src:raise RuntimeError('Missing validated Windows baseline: '+marker)
    src=once(src,OLD_ENSURE,NEW_ENSURE,'named save / exit checkpoint fast path')
    # The UI save now processes at most 1600 players in one native IPC batch
    # for later seasons, rather than 17600. No players or fields are dropped.
    src=once(src,
        "const target=key==='players'?8:key==='allTimeStats'?8:6;",
        "const target=key==='players'?(Number(state?.year)>=2029?2:4):key==='allTimeStats'?4:4;",
        'bounded UI native player-write batch')
    src=once(src,
        "const limit=key==='players'?2200:key==='teams'?420",
        "const limit=key==='players'?(Number(s.year)>=2029?800:1600):key==='teams'?420",
        'bounded UI player compression chunk')
    # Worker checkpoints use the same bounded-memory strategy for old saves.
    src=once(src,
        "const target=key==='players'?8:key==='allTimeStats'?6:4;",
        "const target=key==='players'?(Number(s.year)>=2029?2:4):key==='allTimeStats'?4:4;",
        'bounded Worker native player-write batch')
    src=once(src,
        "const isArray=Array.isArray(value),keys=[],limit=key==='players'?2200",
        "const isArray=Array.isArray(value),keys=[],limit=key==='players'?(Number(s.year)>=2029?800:1600)",
        'bounded Worker player compression chunk')
    # Reading fewer compressed buffers at once protects older careers on load.
    src=once(src,
        "const stride=key==='players'?8:16;",
        "const stride=key==='players'?(Number(manifest.year)>=2029?4:8):16;",
        'read-side compressed player memory cap')
    # The save only reclaims expendable workers and memoized UI caches; not
    # historical records. Existing checkpoint/manifest commit remains atomic.
    src=once(src,
        "  const basePersist=persist;persist=function(notify=false){if(nextEmploymentPersist)",
        NATIVE_RELEASE+"  const basePersist=persist;persist=function(notify=false){if(nextEmploymentPersist)",
        'pre-save transient memory release')
    src=once(src,
        "v5CrestsOut();const result=await saveSharded(current,mode);",
        "v5CrestsOut();v18338FreeTransientBeforeSave();const result=await saveSharded(current,mode);",
        'free Worker before native save')
    src=once(src,
        "finally{v52SavePromise=null;waiters.forEach(r=>r());updateSaveStatus();try{if(v53Worker",
        "finally{if(saveOK&&!v52SaveDirty&&v52PendingState===current)v52PendingState=null;v52SavePromise=null;waiters.forEach(r=>r());updateSaveStatus();try{if(v53Worker",
        'discard stale pending reference after successful save')
    # Strong invariants: snapshots remain sharded, atomic, and retain all history.
    for marker in ('await commitManifest(manifest,old,meta)','v538CareerArchive','v555CareerArchive',
                   'scorerArchive','internationalHistory','v735NationalArchive','allTimeStats',
                   'player_career_totals','v18310VacationRows','v18181RawWriteMany'):
        if marker not in src:raise RuntimeError('History or checkpoint invariant missing: '+marker)
    path.write_text(src,encoding='utf-8')
    result={
      'ok':True,'version':VERSION,'phase':'save-exit and memory safety',
      'reusesVerifiedAlreadySavedCheckpoint':True,'checksCareerIdentity':True,
      'checksSeasonAndDay':True,'respectsDeferredSeasonSave':True,
      'workerReleasedBeforeHeavyManualSave':True,
      'playerRowsPerChunkEarly':1600,'playerRowsPerChunkYear2029Plus':800,
      'playerChunksPerIPCYear2029Plus':2,'playerReadChunksYear2029Plus':4,
      'existingAtomicManifestCommit':True,'careerHistoryRetention':'unchanged',
      'sqliteCareerTotalsRetention':'unchanged','playerFieldCodec':'unchanged',
    }
    (project/'long-career-saves-18338-install.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    main()
