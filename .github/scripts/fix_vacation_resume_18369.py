from __future__ import annotations
import json,sys
from pathlib import Path

VERSION='18.369.0'
MARK='FUTBR_VACATION_RESUME_HANDOFF_18369'

def once(text,old,new,reason):
    n=text.count(old)
    if n!=1:raise RuntimeError(f'18.369 {reason}: expected one original source occurrence, got {n}')
    return text.replace(old,new,1)

RUNTIME=r"""
/* FUTBR_VACATION_RESUME_HANDOFF_18369
   A completed vacation sends an authoritative, fully rebuilt career back to
   the UI. Its preceding full save can still be on the OLD day, because the
   vacation saves via a checkpoint. Do not run a new Worker from that stale
   old-day save or start a huge pre-save before next-match / one-day advance.
   The next action will use THIS authenticated, synchronized live world once.
   Never release a partially streamed world, a busy Worker or another career. */
let v18369VacationReturn=null;
// A completed-world identity must not keep the 185k-player world alive while
// the next vacation releases state and streams its replacement into the UI.
const v18369ReturnedWorlds=new WeakMap();
const v18369ResumeStats={captured:0,liveStarts:0,invalid:0,consumed:0,queueErrors:0,lastQueueError:'',
 paintErrors:0,lastPaintError:'',
 last:'idle',startedDay:null,returnedDay:null};
function v18369PaintOnly(paint){
 try{return paint();}
 catch(error){
  v18369ResumeStats.paintErrors++;
  v18369ResumeStats.lastPaintError=String(error?.message||error);
  console.warn('[18.369] Optional simulation repaint failed',error);
 }
}
function v18369FailPatchDelivery(error,pendingFinish){
 // Data-application errors are not repaint errors. Do not acknowledge a
 // partial delta, retry an already applied mutation, or pretend it finished.
 v18369ResumeStats.queueErrors++;
 v18369ResumeStats.lastQueueError=String(error?.message||error);
 v18369ResumeStats.last='worker-data-delivery-failed';
 v18369VacationReturn=null;
 v131PendingVacationAck=0;
 const finish=v53Sim.finished||pendingFinish,worker=v53Worker;
 // The finished branch may have tentatively cleared active before a core
 // finalization failed. Restore only its still-pending request so the existing
 // Worker failure handler can recover the last committed save and reject it.
 if(finish){v53Sim.finished=finish;v53Sim.active=true;}
 try{
  if(worker&&typeof worker.onerror==='function'){
   worker.onerror({message:error?.message||String(error)});
   return;
  }
 }catch(recoveryError){console.error('[18.369] Original Worker recovery failed',recoveryError);}
 // Defensive fallback when no original Worker handler exists: keep the
 // partially received world locked and reject, rather than expose it as ready.
 v53PatchQueue.length=0;
 v53Sim.active=false;v53Sim.starting=false;v53Sim.finished=null;
 v53Sim.syncing=true;v53Sim.patching=true;v53Creating=true;
 try{worker?.terminate();}catch(_){}
 if(v53Worker===worker){v53Worker=null;v53WorkerReady=null;}
 finish?.reject(error instanceof Error?error:Error(String(error)));
}
function v18369CaptureVacationReturn(s=state,m=null){
 const session=Number(v53Sim?.session);
 if(!Number.isSafeInteger(session)||session<0||
    (m?.session!=null&&Number(m.session)!==session)){
  v18369VacationReturn=null;
  v18369ResumeStats.last='cannot-capture-wrong-session';
  return false;
 }
 if(!s||!s.players||!Array.isArray(s.teams)||!s.teams.length||
    !Array.isArray(s.schedule)||!s.schedule.length||
    s.vacation?.active||v125VacIncoming||v53Sim?.syncing||
    v53Sim?.patching||v53Sim?.active||v53Sim?.starting||
    !String(s.v1903CareerId||'')){
  v18369VacationReturn=null;
  v18369ResumeStats.last='cannot-capture-incomplete-vacation';
  return false;
 }
 v18369VacationReturn={careerId:String(s.v1903CareerId),
   year:Number(s.year),day:Number(s.day),session,at:Date.now()};
 v18369ReturnedWorlds.set(s,v18369VacationReturn);
 v18369ResumeStats.captured++;
 v18369ResumeStats.returnedDay=Number(s.day);
 v18369ResumeStats.last='vacation-world-returned';
 return true;
}
function v18369CanStartFromReturnedVacation(mode,s=state){
 if(mode!=='day'&&mode!=='dayfast'&&mode!=='nextmatch')return false;
 const x=v18369VacationReturn;
 if(!x)return false;
 const sameIdentity=!!s&&v18369ReturnedWorlds.get(s)===x&&
   Number(v53Sim?.session)===x.session;
 const matches=sameIdentity&&
   String(s.v1903CareerId||'')===x.careerId&&
   Number(s.year)===x.year&&Number(s.day)===x.day&&
   !s.seasonDone&&!s.vacation?.active&&
   !!s.players&&Array.isArray(s.teams)&&!!s.teams.length&&
   Array.isArray(s.schedule)&&!!s.schedule.length&&
   !v53Sim?.active&&!v53Sim?.syncing&&
   !v53Sim?.patching&&!v125VacIncoming&&!v53Creating&&
   !v52SavePromise;
 if(!matches){
  // An actual save, season rollover or career change invalidates the token.
  // A real in-flight save remains protected: the old safe fallback is used.
  if(!sameIdentity||Number(s?.year)!==x.year||Number(s?.day)!==x.day||
     String(s?.v1903CareerId||'')!==x.careerId){
   v18369VacationReturn=null;
   v18369ResumeStats.invalid++;
  }
  return false;
 }
 v18369ResumeStats.last='live-post-vacation-start-'+mode;
 v18369ResumeStats.liveStarts++;
 v18369ResumeStats.startedDay=Number(s.day);
 return true;
}
// Called only after postMessage succeeds. A failed Worker boot/dispatch must
// not consume the pending handoff before ownership was actually transferred.
function v18369ConsumeVacationReturn(){
 if(!v18369VacationReturn)return false;
 v18369VacationReturn=null;
 v18369ResumeStats.consumed++;
 return true;
}
window.GestorFC=window.GestorFC||{};
window.GestorFC.vacationResume18369={status:()=>({
 version:'18.369.0',ready:!!v18369VacationReturn,careerId:v18369VacationReturn?.careerId||'',
 year:v18369VacationReturn?.year??null,day:v18369VacationReturn?.day??null,
 workerActive:!!v53Sim?.active,workerStarting:!!v53Sim?.starting,
 syncing:!!v53Sim?.syncing,patching:!!v53Sim?.patching,
 incoming:!!v125VacIncoming,fullSaveActive:!!v52SavePromise,
 queueScheduled:!!v53PatchScheduled,queueLength:v53PatchQueue.length,
 ...v18369ResumeStats
})};
"""

def patch_final_drain(drain):
 # Preserve data mutations exactly once. Only presentation is best-effort;
 # acknowledgements and queue ownership are finalized even if painting fails.
 drain=once(drain,
  "channel.port1.onmessage=()=>{\n  const start=performance.now(),budget=document.hidden?14:30;",
  "channel.port1.onmessage=()=>{\n  let v18369PendingFinish=null,v18369DataFailed=false;\n  try{\n  const start=performance.now(),budget=document.hidden?14:30;",
  'guard original MessageChannel data application')
 drain=once(drain,
  "const m=v53PatchQueue.shift();if(m.session!==v53Sim.session)continue;",
  "const m=v53PatchQueue.shift();if(m.session!==v53Sim.session)continue;v18369PendingFinish=v53Sim.finished;",
  'retain pending completion while applying the current message')
 old_header="""    const slot=document.querySelector('#v624-vac-header');
    if(slot&&!slot.hidden&&typeof v624VacationHeaderHTML==='function'){slot.innerHTML=v624VacationHeaderHTML();delete slot.dataset.sig;}"""
 new_header="""    v18369PaintOnly(()=>{
     const slot=document.querySelector('#v624-vac-header');
     if(slot&&!slot.hidden&&typeof v624VacationHeaderHTML==='function'){slot.innerHTML=v624VacationHeaderHTML();delete slot.dataset.sig;}
    });"""
 drain=once(drain,old_header,new_header,'isolate nextmatch header from delivery')
 # All these calls only paint. Match only this active final drain, never
 # rewrite the definitions or the Engine. A throw cannot swallow a delta.
 if drain.count('v53PaintStatus();')<5:
  raise RuntimeError('18.369 final status paint sites changed')
 drain=drain.replace('v53PaintStatus();','v18369PaintOnly(()=>v53PaintStatus());')
 # 18.360 progress counters also touch the overlay DOM. They do not apply
 # world data, and an optional counter repaint must not abort a received batch.
 for metric in ('v18360SyncStart();','v18360SyncCollection(m);',
    'v18360SyncUpdate(Math.max(0,(Number(m.done)||0)-v18360SyncMetrics.players));',
    'v18360SyncEnd();'):
  if metric in drain:
   drain=once(drain,metric,'v18369PaintOnly(()=>'+metric[:-1]+');','isolate stream progress counters')
 drain=once(drain,"if(!automaticallyRecoverable)toast(m.error,'error');\n     finish?.reject(Error(m.error));",
  "finish?.reject(Error(m.error));\n     if(!automaticallyRecoverable)v18369PaintOnly(()=>toast(m.error,'error'));",
  'reject terminal error before its optional toast')
 # A completed terminal message is never retried. Save its settlement before
 # entering the optional batch repaint and clear the local completion handle.
 terminal_end="""    }else if(state)finish?.resolve(state);else finish?.reject(Error('A simulação terminou sem sincronizar a carreira.'));
    continue;"""
 terminal_new="""    }else if(state)finish?.resolve(state);else finish?.reject(Error('A simulação terminou sem sincronizar a carreira.'));
    v18369PendingFinish=null;
    continue;"""
 drain=once(drain,terminal_end,terminal_new,'never retain a settled terminal promise')
 # rank snapshots can request a full redraw before the ordinary batch tail.
 rank_old="if(['clubrankings','rankings','coaches','nationalrankings'].includes(view)&&!document.hidden)v53RefreshView(true);"
 rank_new="if(['clubrankings','rankings','coaches','nationalrankings'].includes(view)&&!document.hidden)v18369PaintOnly(()=>v53RefreshView(true));"
 drain=once(drain,rank_old,rank_new,'isolate rank snapshot paint')
 tail="  if(competitionLiveDirty&&!document.hidden&&view==='competitions'){"
 drain=once(drain,tail,"  v18369PendingFinish=null;\n  v18369PaintOnly(()=>{\n"+tail,'separate batch presentation from state delivery')
 old_end="""  if(v131PendingVacationAck){try{v53Worker?.postMessage({op:'vac-live-ack',seq:v131PendingVacationAck});}catch(e){}v131PendingVacationAck=0;}
  if(v53PatchQueue.length)channel.port2.postMessage(0);else{v53PatchScheduled=false;channel.port1.close();channel.port2.close();}
 };
 channel.port2.postMessage(0);"""
 new_end="""  });
  }catch(error){
   v18369DataFailed=true;
   v18369FailPatchDelivery(error,v18369PendingFinish);
  }finally{
   // Only applied data may be acknowledged. Optional repaint errors cannot
   // skip this ACK, even when it was the last queued vacation message.
   if(!v18369DataFailed&&v131PendingVacationAck){
    try{v53Worker?.postMessage({op:'vac-live-ack',seq:v131PendingVacationAck});}catch(e){}
    v131PendingVacationAck=0;
   }
   if(!v18369DataFailed&&v53PatchQueue.length)channel.port2.postMessage(0);
   else{v53PatchScheduled=false;channel.port1.close();channel.port2.close();}
  }
 };
 channel.port2.postMessage(0);"""
 drain=once(drain,old_end,new_end,'always finalize successful ACK and pump ownership')
 if 'v53PatchQueue.unshift(' in drain:
  raise RuntimeError('18.369 data messages must never be replayed after application')
 return drain

def main():
 if len(sys.argv)!=2: raise SystemExit('usage: fix_vacation_resume_18369.py <project>')
 root=Path(sys.argv[1]).resolve()
 file=root/'src/index.html'
 s=file.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.369 already installed')
 for a in ('FUTBR_UNEMPLOYED_WORKER_REAL_PROGRESS_18368',
           'FUTBR_CORE_LIFECYCLE_18362',
           'v53DrainPatches=function(){',
           'const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=',
           'const v18366BaseVacationHeader=v624VacationHeaderHTML;'):
  if a not in s: raise RuntimeError('18.369 missing preserved source: '+a)
 # Base simulator: preserve the existing 18.311 fast path and its 18.368
 # resident-Worker protection. Reuse it once after a successful vacation
 # WITHOUT waiting for an outdated full save or loading old day from disk.
 bs=s.index('async function v53StartSimulation(mode,options={}){')
 be=s.index('runVacation=async function',bs)
 base=s[bs:be]
 flag='const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation='
 a=base.index(flag)
 end=base.index(';',a+len(flag))
 prior=base[a:end+1]
 if "mode==='vacation'" not in prior or "options?.liveStateNoPreSave" not in prior:
  raise RuntimeError('18.369 existing authoritative live-state condition changed')
 if 'v18369CanStartFromReturnedVacation' in prior:
  raise RuntimeError('18.369 live-state condition already modified')
 modified=prior[:-1]+'||v18369CanStartFromReturnedVacation(mode,state);'
 base=once(base,prior,modified,'reuse the existing safe live-state branch')
 if 'if(!v18311LiveVacation&&state?.v1903CareerId&&!saveOK)' not in base:
  raise RuntimeError('18.369 original live-state save protection lost')
 if 'const canLoadSaved=!v18311LiveVacation&&' not in base:
  raise RuntimeError('18.369 live state would incorrectly load old save')
 if 'if(!canLoadSaved&&!(mode===\'dayfast\'&&options?.jobWaitResident===true))msg.state=state;' not in base:
  raise RuntimeError('18.369 live state Worker transfer is missing')
 # Every accepted simulation dispatch invalidates the previous vacation token,
 # including a new vacation whose existing fast path short-circuits the predicate.
 # Keep this after postMessage, so a thrown dispatch cannot consume the token.
 base=once(base,'    w.postMessage(msg);',
    '    w.postMessage(msg);\n    v18369ConsumeVacationReturn();',
    'consume completed vacation identity only after accepted Worker dispatch')
 s=s[:bs]+base+s[be:]
 # 18.369: the actual next-match Worker formerly showed 'Partidas: 16/16'
 # indefinitely. Report the REAL post-match stages, without changing sporting
 # decisions or replaying the round. One short message per stage; no world clone.
 eng_start=s.index('async function advanceDayAsync(s,onProgress=()=>{},options=null){')
 eng_end=s.index('async function vacationStepAsync(',eng_start)
 engine=s[eng_start:eng_end]
 phase_marks=[
  ("    const played=new Set(matches.flatMap",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Recuperando os elencos');\\n    const played=new Set(matches.flatMap"),
  ("    for(const {f,m} of matches){applyIntlResult(s,f,m);",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Aplicando resultados e disciplina');\\n    for(const {f,m} of matches){applyIntlResult(s,f,m);"),
  ("    if(stage.type!=='world'&&stage.type!=='national')for(const t of s.teams){stageFinances",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Processando financas');\\n    if(stage.type!=='world'&&stage.type!=='national')for(const t of s.teams){stageFinances"),
  ("    if(delegatedDepthEmergency||stage.type==='league'){const q=",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Avaliando mercado de transferencias');\\n    if(delegatedDepthEmergency||stage.type==='league'){const q="),
  ("    if(stage.type==='league'||delegatedDepthEmergency){const q=",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Avaliando mercado de tecnicos');\\n    if(stage.type==='league'||delegatedDepthEmergency){const q="),
  ("    const uf=stage.fixtures.find(f=>f.home===s.user||f.away===s.user);",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Consolidando estatisticas da rodada');\\n    const uf=stage.fixtures.find(f=>f.home===s.user||f.away===s.user);"),
  ("    s.lastDay=s.day;s.day++;s.live=null;delete s.liveCompanions;",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Concluindo jornada no calendario');\\n    s.lastDay=s.day;s.day++;s.live=null;delete s.liveCompanions;")
 ]
 for old,new in phase_marks:
  engine=once(engine,old,new.replace('\\n','\n'),'trace authoritative original Engine phase')
 s=s[:eng_start]+engine+s[eng_end:]
 # Only the active, final patch-drain handler may declare vacation fully
 # returned. The first legacy definition no longer owns the 18.360 stream.
 ds=s.rindex('v53DrainPatches=function(){')
 de=s.index('async function v722CatchUpAfterFocus(){',ds)
 drain=s[ds:de]
 anchor='v53Sim.active=false;v53Sim.patching=false;v53Sim.syncing=false;vacationLoop=false;v52Processing=false;'
 replacement=anchor+"""
    if(wasVacation){
     if(!m.error)v18369CaptureVacationReturn(state,m);
     else{v18369VacationReturn=null;v18369ResumeStats.last='vacation-failed';}
    }"""
 drain=once(drain,anchor,replacement,'capture after last completed vacation Worker event')
 drain=patch_final_drain(drain)
 s=s[:ds]+drain+s[de:]
 s=once(s,'const v18366BaseVacationHeader=v624VacationHeaderHTML;',
    RUNTIME+'\nconst v18366BaseVacationHeader=v624VacationHeaderHTML;',
    'insert inside original private game IIFE')
 s=once(s,"const EDITION='18.368.0';","const EDITION='18.369.0';",'version')
 s=once(s,"window.GestorFC.version='18.368.0';window.GestorFC.visualVersion='18.368.0';",
    "window.GestorFC.version='18.369.0';window.GestorFC.visualVersion='18.369.0';",'runtime version')
 file.write_text(s,encoding='utf-8')
 report={
  'ok':True,'version':VERSION,
  'rootCause':'First advance after vacation could read stale pre-vacation save or wait for entire-world pre-save',
  'commonHandoffForEmployedAndUnemployed':True,
  'captureOnlyAfterRealFullWorkerSync':True,
  'normalDayAfterVacationUsesLiveWorld':True,
  'nextMatchAfterVacationUsesLiveWorld':True,
  'noOldSaveReplay':True,
  'noNewFullPreSaveBeforeFirstAdvance':True,
  'unemployedResidentWorkerUnchanged':True,
  'careerIdentityAndSessionGuard':True,
  'noStrongVacationWorldReference':True,
  'returnedWorldTokenConsumedOnDispatch':True,
  'noNewWorkerDuringStreaming':True,
  'checkpointAndHistoricDataUnchanged':True,
  'realEnginePhaseTelemetry':True,
  'queueErrorCannotPermanentlyFreezeAdvance':True,
  'terminalWorldAndFinishedMessagesPreserved':True,
  'paintErrorsCannotLoseVacationAck':True,
  'stateMessagesAppliedExactlyOnce':True,
  'dataApplicationFailureUsesOriginalRecovery':True}
 (root/'vacation-resume-18369-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()

