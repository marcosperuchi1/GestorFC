from __future__ import annotations
import json,sys
from pathlib import Path

MARK='FUTBR_DISMISSAL_HANDOFF_18357'

def one(s,old,new,label):
    hits=s.count(old)
    if hits!=1:raise RuntimeError(f'18.357 {label}: expected exactly one anchor, got {hits}')
    return s.replace(old,new,1)

HELPER=r"""
/* FUTBR_DISMISSAL_HANDOFF_18357
   Worker finishes -> vacation player/history stream ends -> 17.1 promotes
   its already-written checkpoint -> unlock unemployed UI. Do not rewrite
   the entire player universe a second time after the dismissal. */
let v18357AwaitingPromotion=false,v18357LiveFallback=null,v18357Retry=null,
    v18357LastStatus='idle',v18357ReleaseCount=0,v18357AuditCount=0;
function v18357CheckIdentity(s=state){
 const id=String(s?.v1903CareerId||'');
 return !!s&&s.userEmployed===false&&!s.v640National?.userTeam&&
  (!v18112Dismissal.careerId||v18112Dismissal.careerId===id);
}
function v18357NoPendingWorldTransfer(){
 return !!state&&!v53Sim?.active&&!v53Sim?.starting&&!v53Sim?.syncing&&
  !v53Sim?.patching&&!v53Sim?.finished&&!v53Creating&&!v52Processing&&
  !v125VacIncoming&&!(typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)&&
  !(typeof v18326AdvanceBusy!=='undefined'&&v18326AdvanceBusy)&&
  !(typeof v53RPC!=='undefined'&&v53RPC?.size>0);
}
function v18357MatchesAudit(a,s){
 return !!a&&Number(a.year)===Number(s.year)&&Number(a.day)===Number(s.day)&&
  (!s.v1903CareerId||String(a.careerId||'')===String(s.v1903CareerId))&&
  a.userEmployed===false;
}
function v18357WantsLiveJobState(mode){
 const s=state,x=v18357LiveFallback;
 return (mode==='dayfast'||mode==='day')&&!!x&&v18357CheckIdentity(s)&&
  Number(s.year)===x.year&&Number(s.day)===x.day&&
  String(s.v1903CareerId||'')===x.careerId;
}
function v18357ScheduleRecovery(){
 if(v18357Retry!==null||!v18357AwaitingPromotion)return;
 v18357Retry=setTimeout(()=>{
  v18357Retry=null;void v18357FinalizeDismissal();
 },250);
}
async function v18357FinalizeDismissal(){
 if(!v18357AwaitingPromotion||!v18112Dismissal.pending||!v18357CheckIdentity()){
  return false;
 }
 if(!v18357NoPendingWorldTransfer()){
  v18357LastStatus='waiting-for-real-worker-or-checkpoint';
  v18357ScheduleRecovery();
  return false;
 }
 const current=state,year=Number(current.year),day=Number(current.day),
  careerId=String(current.v1903CareerId||'');
 let audit=null;
 try{
  v18357AuditCount++;
  audit=await window.GestorFC?.v171?.storageAudit?.();
 }catch(e){console.warn('[18.357] checkpoint audit',e);}
 // The awaited native read can yield; do not update another career or an
 // active Worker if the user navigates or launches a new simulation meanwhile.
 if(state!==current||!v18357CheckIdentity()||!v18357NoPendingWorldTransfer()||
    Number(state.year)!==year||Number(state.day)!==day||
    String(state.v1903CareerId||'')!==careerId){
  v18357ScheduleRecovery();return false;
 }
 const verified=v18357MatchesAudit(audit,current);
 // If the existing vacation checkpoint failed, keep the previous disk save
 // and run the first unemployed day from this authoritative in-memory world.
 // The normal Worker commit after that day establishes the new checkpoint.
 v18357LiveFallback=verified?null:{year,day,careerId};
 v18357LastStatus=verified?'checkpoint-verified':'live-state-fallback';
 v18357AwaitingPromotion=false;
 if(v18357Retry!==null){clearTimeout(v18357Retry);v18357Retry=null;}
 if(current.vacation){
  current.vacation.active=false;current.vacation.paused=true;
  current.vacation.remaining=0;current.vacation.untilSeason=false;
 }
 v18112Dismissal.pending=false;v18112Dismissal.ready=true;
 v53Sim.pause=false;v53Sim.pauseMode='';
 v18357ReleaseCount++;
 view='career';
 try{closeModal();}catch(e){}
 try{render();}catch(e){console.warn('[18.357] unemployed render',e);}
 if(!v18112Dismissal.notified){
  v18112Dismissal.notified=true;
  toast(verified?
    'Contrato encerrado. Carreira sincronizada; a busca por propostas está liberada.':
    'Contrato encerrado. Avanço liberado com os dados em memória; salve a carreira para confirmar o novo checkpoint.',
    verified?'warn':'warn');
 }
 return true;
}
window.GestorFC.dismissalHandoff18357={
 version:'18.357',avoidsSecondFullWorldSave:true,firstDayUsesLiveStateOnCheckpointFailure:true,
 status:()=>({awaiting:v18357AwaitingPromotion,workerBusy:!v18357NoPendingWorldTransfer(),
  verified:v18357LastStatus==='checkpoint-verified',status:v18357LastStatus,
  year:Number(state?.year)||0,day:Number(state?.day)||0,
  fallback:!!v18357LiveFallback,releases:v18357ReleaseCount,audits:v18357AuditCount}),
 recover:()=>v18357FinalizeDismissal()
};
"""

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_dismissal_handoff_18357.py <project>')
    root=Path(sys.argv[1]).resolve();path=root/'src/index.html'
    src=path.read_text(encoding='utf-8')
    if MARK in src:raise RuntimeError('18.357 double patch')
    for old in ('FUTBR_UNEMPLOYED_RESUME_18334_BEGIN','FUTBR_JOB_SAVE_EXIT_18355',
                'FUTBR_JOBWAIT_SEASON_RECOVERY_18356','const baseStart171=v53StartSimulation;'):
        if old not in src:raise RuntimeError('Missing validated baseline '+old)
    # The 18.112 inner wrapper is invoked BEFORE 17.1's outer wrapper
    # commits the already-streamed vacation checkpoint. Its old audit was
    # therefore guaranteed to observe an obsolete snapshot and rewrite the
    # whole historical game a second time.
    start=src.index("if(mode==='vacation'&&v18112Dismissal.pending&&state?.userEmployed===false){")
    end=src.index("return result;",start)
    old=src[start:end]
    for guard in ("await persist(false);await v52FlushSave();",
                  "v18112Dismissal.pending=false;v18112Dismissal.ready=true;",
                  "view='career';closeModal();render();"):
        if guard not in old:raise RuntimeError('Legacy 18.112 dismissal stage changed: '+guard)
    replacement="""   if(mode==='vacation'&&v18112Dismissal.pending&&state?.userEmployed===false){
    // The world is back, but 17.1 has not promoted its existing checkpoint.
    // Do not reserialize players/history or release the button here.
    v18357AwaitingPromotion=true;
    if(state.vacation){
     state.vacation.active=false;state.vacation.paused=true;
     state.vacation.remaining=0;state.vacation.untilSeason=false;
    }
   }
"""
    src=src[:start]+replacement+src[end:]
    # Legacy UI retry must not launch a competing save while the 17.1
    # checkpoint is being committed.
    src=one(src,"function v18334SafeToVerify(){\n return v18334EligibleForJobWait()",
            "function v18334SafeToVerify(){\n return !v18357AwaitingPromotion&&!(v18112Dismissal.pending&&v53Sim?.mode===\'vacation\')&&v18334EligibleForJobWait()",
            'disable legacy duplicate-save recovery while promoting')
    src=one(src,"async function v18334RecoverDismissal(){\n if(v18334RecoverPromise)",
            "async function v18334RecoverDismissal(){\n if(v18357AwaitingPromotion||(v18112Dismissal.pending&&v53Sim?.mode===\'vacation\'))return false;\n if(v18334RecoverPromise)",
            'keep legacy recovery from preempting promotion')
    src=one(src,'/* FUTBR_UNEMPLOYED_RESUME_18334_END */',
            '/* FUTBR_UNEMPLOYED_RESUME_18334_END */\n'+HELPER,
            'install callback-based dismissal handoff')
    # 17.1 is OUTER relative to 18.112 and is exactly where the vacation
    # checkpoint must be promoted before enabling the job buttons.
    start=src.index('const baseStart171=v53StartSimulation;')
    end=src.index('G.v171={version:V',start)
    block=src[start:end]
    block=one(block,'const out=await baseStart171(mode,...args);',
        """const v18357Live=v18357WantsLiveJobState(mode);
  const v18357Args=v18357Live?[{...(args[0]||{}),liveStateNoPreSave:true}]:args;
  const out=await baseStart171(mode,...v18357Args);
  if(v18357Live)v18357LiveFallback=null;""",
        'route only the first missing-checkpoint unemployed day through live state')
    block=one(block,
     'finally{v53Sim.syncing=false;try{v53PaintStatus();}catch(e){}}}return out;};',
     """finally{v53Sim.syncing=false;try{v53PaintStatus();}catch(e){}}}
  if(mode==='vacation'&&v18357AwaitingPromotion&&v18112Dismissal.pending){
   await v18357FinalizeDismissal();
  }
  return out;};""",
     'finalize after 17.1 checkpoint promotion')
    src=src[:start]+block+src[end:]
    # A checkpoint audit is a small manifest read. Add identity & employment
    # to prevent accepting a previous career or an outdated employed snapshot.
    src=one(src,
       "revision:m?.revision,rootKeys:Object.keys(m?.root||{}).length,collections:",
       "revision:m?.revision,careerId:String(m?.root?.v1903CareerId||''),userEmployed:m?.root?.userEmployed,rootKeys:Object.keys(m?.root||{}).length,collections:",
       'audit manifest identity without loading players')
    src=one(src,"const EDITION='18.356.0';","const EDITION='18.357.0';",
            'visual desktop version')
    src=one(src,
        "window.GestorFC.version='18.356.0';window.GestorFC.visualVersion='18.356.0';",
        "window.GestorFC.version='18.357.0';window.GestorFC.visualVersion='18.357.0';",
        'runtime desktop version')
    path.write_text(src,encoding='utf-8')
    result={'ok':True,'version':'18.357.0','legacyFullWorldRewriteRemoved':True,
      'waitsForVacationStreamAndOriginalCheckpoint':True,
      'verifiesCareerAndEmploymentInSmallManifest':True,
      'neverOverridesRunningWorker':True,
      'unlocksAtFinalPromotion':True,'fallbackPreservesOldSaveAndUsesLiveWorld':True,
      'noSaveSchemaChange':True,'historyPlayersUntouched':True}
    (root/'dismissal-handoff-18357-install.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
