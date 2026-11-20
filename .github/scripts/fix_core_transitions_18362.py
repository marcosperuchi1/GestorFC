from __future__ import annotations
import json
import sys
from pathlib import Path

VERSION = "18.362.0"
MARK = "FUTBR_CORE_LIFECYCLE_18362"

def once(src, old, new, label):
    count = src.count(old)
    if count != 1:
        raise RuntimeError(f"18.362 {label}: expected one match, got {count}")
    return src.replace(old, new, 1)

def between(src, left, right, replacement, label):
    a = src.index(left)
    b = src.index(right, a + len(left))
    if b <= a:
        raise RuntimeError(f"18.362 {label}: invalid interval")
    return src[:a] + replacement + src[b:]

FINISH_AND_GUARDS = r"""
/* FUTBR_CORE_LIFECYCLE_18362
   Never decide that a vacation Worker has COMPLETED inside its own
   finished-event callback. At that point the worker may still be active,
   and the 17.1 atomic checkpoint promotion has not returned.
   Record the event, then release the unemployed day ONLY after the
   outer vacation promise has successfully returned the full world. */
let v18362VacationOrigin=null;
const v18362Transitions={workerEvents:0,settled:0,released:0,
 last:'idle',cleanupDeferred:0};
function v18359TrustedCompleted(s=state){
 const x=v18359FinishedWorld;
 if(!x||x.phase!=='promoted'||!v18359HasWorld(s))return false;
 if(x.world!==s||x.year!==Number(s.year)||x.day!==Number(s.day)||
    x.careerId!==String(s.v1903CareerId||''))return false;
 // v53Sim.finished is a legacy UI flag, not a running operation.
 if(v53Sim?.active||v53Sim?.starting||v125VacIncoming||
   (typeof v18326AdvanceBusy!=='undefined'&&v18326AdvanceBusy)||
   (typeof v18121NewSeasonPreparation!=='undefined'&&v18121NewSeasonPreparation))return false;
 return true;
}
"""
FINISHED_AND_PROMOTION = r"""
function v18359OnWorkerFinished(m,wasVacation){
 if(!wasVacation||m?.error||!state||state.userEmployed!==false||
    state.v640National?.userTeam)return false;
 if(v125VacIncoming||!state.players||!Array.isArray(state.teams)||
    !Array.isArray(state.schedule)){
  v18359BlockedReason='incomplete-worker-world';return false;
 }
 const careerId=String(state.v1903CareerId||'');
 if(v18112Dismissal.careerId&&careerId!==String(v18112Dismissal.careerId)){
  v18359BlockedReason='wrong-career';return false;
 }
 const origin=v18362VacationOrigin;
 if(origin&&origin.careerId!==careerId){
  v18359BlockedReason='new-career';return false;
 }
 // A finished event is evidence of the full transfer, NOT of the completed
 // promotion. v53Sim.active/finished may still be true in this callback.
 const session=Number(v53Sim?.session)||0;
 v18359FinishedWorld={world:state,year:Number(state.year),day:Number(state.day),
  careerId,session,phase:'worker-finished'};
 v18359FinishCount++;v18362Transitions.workerEvents++;
 v18359BlockedReason='awaiting-checkpoint-promotion';
 v18362Transitions.last='worker-finished-awaiting-promise';
 return true;
}
function v18362CommitVacation(origin){
 const s=state,x=v18359FinishedWorld;
 if(!origin||!s||s.userEmployed!==false||s.v640National?.userTeam||
    origin.careerId!==String(s.v1903CareerId||'')||
    !s.players||!Array.isArray(s.teams)||!Array.isArray(s.schedule)||
    v125VacIncoming||v53Sim?.active||v53Sim?.starting){
  v18362Transitions.last='incomplete-outer-vacation';
  return false;
 }
 // Only a successfully resolved original vacation Promise is allowed here.
 // The original handler has already synchronized all arrays and awaited
 // the 17.1 checkpoint promotion, with live-world fallback on save failure.
 if(x&&x.phase==='worker-finished'&&
    (x.world!==s||x.year!==Number(s.year)||x.day!==Number(s.day)||
     x.careerId!==String(s.v1903CareerId||'')||
     x.session!==(Number(v53Sim?.session)||0))){
  v18362Transitions.last='worker-world-changed';return false;
 }
 const dismissed=!!origin.employed||!!v18112Dismissal.pending;
 if(!dismissed)return false;
 if(s.vacation){s.vacation.active=false;s.vacation.paused=true;
  s.vacation.remaining=0;s.vacation.untilSeason=false;}
 if(typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)
  try{v18119CompleteSeasonTransfer();}catch(e){
   console.warn('[18.362] vacation overlay cleanup',e);
  }
 // An outer promise that returned successfully is authoritative. Clear
 // obsolete painter flags, but never clear an actually running Worker.
 v53Sim.syncing=false;v53Sim.patching=false;v53Sim.finished=null;
 v53Sim.pause=false;v53Sim.pauseMode='';
 if(dismissed){
  v18112Dismissal.pending=false;v18112Dismissal.ready=true;
  if(typeof v18357AwaitingPromotion!=='undefined')v18357AwaitingPromotion=false;
  if(typeof v18358RecoveryDone!=='undefined')v18358RecoveryDone=true;
  if(typeof v18357LiveFallback!=='undefined')
   v18357LiveFallback={year:Number(s.year),day:Number(s.day),
    careerId:String(s.v1903CareerId||'')};
 }
 v18359FinishedWorld={world:s,year:Number(s.year),day:Number(s.day),
  careerId:String(s.v1903CareerId||''),session:Number(v53Sim?.session)||0,phase:'promoted'};
 v18359BlockedReason='none';v18359ReleaseCount++;
 v18362Transitions.released++;v18362Transitions.last='successfully-promoted';
 if(dismissed)view='career';
 queueMicrotask(()=>{
  if(!v18359TrustedCompleted())return;
  try{if(dismissed)closeModal();render();v18359RefreshButtons(document);}
  catch(e){console.warn('[18.362] unemployed chrome',e);}
  if(dismissed&&!v18112Dismissal.notified){
   v18112Dismissal.notified=true;
   toast('Contrato encerrado. Avanço até proposta liberado.','warn');
  }
 });
 return true;
}
"""
START_WRAPPER=r"""
const v18359BaseStart=v53StartSimulation;
v53StartSimulation=async function(mode,...args){
 if(mode==='vacation'){
  const origin={careerId:String(state?.v1903CareerId||''),
   employed:state?.userEmployed===true};
  v18362VacationOrigin=origin;
  v18359FinishedWorld=null;v18359BlockedReason='vacation-running';
  const p=v18359BaseStart(mode,...args);
  v18359VacationPromise=p;
  try{
   const result=await p;
   v18362Transitions.settled++;
   v18362CommitVacation(origin);
   return result;
  }finally{
   if(v18359VacationPromise===p)v18359VacationPromise=null;
   if(v18362VacationOrigin===origin)v18362VacationOrigin=null;
  }
 }
 if((mode==='day'||mode==='dayfast')&&v18359TrustedCompleted()){
  // The preceding vacation promise has already finished before promotion;
  // no 12-second artificial wait, timeout, or replay of the prior save.
  args[0]={...(args[0]||{}),liveStateNoPreSave:true};
 }
 return v18359BaseStart(mode,...args);
};
"""
CLEANUP = r"""
function v18362CleanupBusy(){
 // Never run thousands of old-shard deletes immediately after a rollover,
 // while a user is logging in, or while the same world is being saved.
 return !!(v53Sim?.active||v53Sim?.starting||v53Sim?.syncing||
    v53Sim?.patching||v53Creating||v52Processing||v52SavePromise||
    v125VacIncoming||v89JobWait?.active||
    (typeof v18121NewSeasonPreparation!=='undefined'&&v18121NewSeasonPreparation));
}
function v18360ScheduleObsoleteCleanup(oldManifest,keep){
 if(!oldManifest)return false;
 v18360CleanupStats.scheduled++;
 // The current and previous manifests were committed BEFORE this function.
 // Older shards are only removed during a quiet period; safe and reversible.
 v18360CleanupTail=v18360CleanupTail.catch(()=>{}).then(async()=>{
  await new Promise(r=>setTimeout(r,15000));
  while(v18362CleanupBusy()){
   v18362Transitions.cleanupDeferred++;
   await new Promise(r=>setTimeout(r,2000));
  }
  // Yield to input/painting before starting IO housekeeping.
  await new Promise(r=>setTimeout(r,0));
  if(v18362CleanupBusy()){
   v18362Transitions.cleanupDeferred++;
   await new Promise(r=>setTimeout(r,2000));
   while(v18362CleanupBusy())await new Promise(r=>setTimeout(r,2000));
  }
  v18360CleanupStats.active=true;
  try{await cleanupManifest(oldManifest,keep);v18360CleanupStats.completed++;}
  catch(e){v18360CleanupStats.failed++;
   v18360CleanupStats.lastError=e?.message||String(e);
   console.warn('[18.362] cleanup deferred failed',e);}
  finally{v18360CleanupStats.active=false;}
 });
 return true;
}
"""
BOOT_STATUS = r"""async function v548EnterGame(){
 const el=document.getElementById('app');
 const label=el?.querySelector?.('.v548-status,.auth-status,[role="status"]');
 if(label)label.textContent='Conta conectada. Preparando os dados locais...';
 // Commit authentication feedback to the window before parsing the roster.
 if(typeof requestAnimationFrame==='function')
  await new Promise(resolve=>requestAnimationFrame(()=>resolve()));
 await v260FastLoadLocal(false);
 await v310StartRosterLoad();
 renderWelcome();
}"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_core_transitions_18362.py <project>')
 root=Path(sys.argv[1]).resolve()
 path=root/'src/index.html'
 s=path.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.362 core changes already installed')
 for anchor in ('FUTBR_DISMISSAL_FINISHED_SIGNAL_18359',
                'FUTBR_VACATION_FINALIZE_LIGHT_18360',
                'FUTBR_LONG_CAREER_SAVE_18338_BEGIN',
                "if(m.kind==='finished'){",
                "if(m.kind==='vac-sync-end'){",
                "function v18359OnWorkerFinished(m,wasVacation){"):
  if anchor not in s:raise RuntimeError('18.362 missing source '+anchor)
 s=between(s,'function v18359TrustedCompleted(s=state){',
   'function v18359RefreshButtons(root=document){',FINISH_AND_GUARDS,
   'real Worker completion guard')
 s=between(s,'function v18359OnWorkerFinished(m,wasVacation){',
   'const v18359BaseChrome=v555UpdateChrome;',FINISHED_AND_PROMOTION,
   'Worker event is no longer early UI release')
 s=between(s,'const v18359BaseStart=v53StartSimulation;',
   'window.GestorFC.dismissalFinished18359=',START_WRAPPER,
   'original Worker completion Promise handoff')
 s=between(s,'function v18360ScheduleObsoleteCleanup(oldManifest,keep){',
   'window.GestorFC.v18360CleanupStatus=',CLEANUP,
   'off-peak post-checkpoint obsolete shard deletion')
 s=once(s,"Math.min(640,(","Math.min(768,(",
   'recover ACK throughput with bounded player chunks')
 # Preserve the signed updater's 5-second check as asynchronous. The
 # verified CDN download itself remains native, signed, and off the UI loop.
 # The login window gets one paint opportunity before the installed roster.
 old="async function v548EnterGame(){await v260FastLoadLocal(false);await v310StartRosterLoad();renderWelcome();}"
 s=once(s,old,BOOT_STATUS,'login authentication paint before roster parse')
 s=once(s,"const EDITION='18.361.0';","const EDITION='18.362.0';",'edition')
 s=once(s,"window.GestorFC.version='18.361.0';window.GestorFC.visualVersion='18.361.0';",
        "window.GestorFC.version='18.362.0';window.GestorFC.visualVersion='18.362.0';",
        'runtime edition')
 # Diagnostics are bounded scalar counters; never scan player history.
 s=once(s,'window.GestorFC.dismissalFinished18359={',
    "window.GestorFC.lifecycle18362={status:()=>({...v18362Transitions,"
    "promoted:v18359TrustedCompleted(),blockedReason:v18359BlockedReason})};\n"
    "window.GestorFC.dismissalFinished18359={",
    'expose small status counters without heavy enumeration')
 path.write_text(s,encoding='utf-8')
 report={'ok':True,'version':VERSION,'patchesRealWorkerEvent':True,
  'defersUnlockUntilVacationPromiseResolved':True,'noEarlyPromotion':True,
  'noForcedWorkerStop':True,'liveFirstUnemployedDay':True,
  'originalHistoryAndSaveCodecUntouched':True,'originalAtomicCheckpointUntouched':True,
  'shardCleanupAfterQuietPeriod':True,'earlyAuthenticatedUIFeedback':True,
  'boundedPlayerStreamAfter2028':768,'signedUpdaterAndNativeDownloadUntouched':True}
 (root/'core-transitions-18362-install.json').write_text(
  json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
