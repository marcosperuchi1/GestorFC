from __future__ import annotations

import json, sys
from pathlib import Path

MARK='FUTBR_JOBWAIT_SEASON_RECOVERY_18356'

def one(src,old,new,label):
    n=src.count(old)
    if n!=1:raise RuntimeError(f'18.356 {label}: expected one anchor, got {n}')
    return src.replace(old,new,1)

HELPER=r"""
/* FUTBR_JOBWAIT_SEASON_RECOVERY_18356
   After a dismissal at year end, the new season can be authoritative in
   memory while its first checkpoint is deliberately deferred (18.168).
   The old 18.334 audit cannot match the previous year's disk checkpoint.
   Only release obsolete dismissal/UI flags after the rollover has finished,
   the Worker has no active operation, and the career identity is unchanged.
   The first dayfast Worker must then receive this new live world, not the
   previously committed 2026 disk save. */
function v18356Unemployed(s=state){
 return !!s&&s.userEmployed===false&&!s.v640National?.userTeam&&
  !s.seasonDone&&!s.live&&!s.vacation?.active;
}
function v18356NoRealWorker(){
 return !v53Sim?.finished&&
  !(typeof v53RPC!=='undefined'&&v53RPC?.size>0)&&
  !v53Creating&&!v52Processing&&
  !(typeof v18326AdvanceBusy!=='undefined'&&v18326AdvanceBusy)&&
  !(typeof v18121NewSeasonPreparation!=='undefined'&&v18121NewSeasonPreparation)&&
  !(typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)&&
  !(typeof v168RolloverRunning!=='undefined'&&v168RolloverRunning)&&
  !(typeof v91RolloverActive!=='undefined'&&v91RolloverActive);
}
function v18356ReconcileRollover(){
 if(!v18356Unemployed()||!v168DeferredRolloverSave||v89JobWait.active||
    !v18356NoRealWorker()||v53Sim?.starting)return false;
 const previousYear=Number(v18112Dismissal.year)||0;
 const sameCareer=!v18112Dismissal.careerId||
    String(v18112Dismissal.careerId)===String(state.v1903CareerId||'');
 if(v18112Dismissal.pending&&(!sameCareer||Number(state.year)<=previousYear))return false;
 // The season was already advanced by E.nextSeason. Any previous vacation
 // Worker was stopped as part of that completed rollover.
 if(v53Sim?.active)v53Sim.active=false;
 v53Sim.syncing=false;v53Sim.patching=false;
 v18112Dismissal.pending=false;v18112Dismissal.ready=true;
 return true;
}
function v18356CanUseJobButtons(){
 return v18356Unemployed()&&!v89JobWait.active&&!v18112Dismissal.pending&&
  !v53Sim?.active&&!v53Sim?.starting&&!v53Sim?.syncing&&!v53Sim?.patching&&
  v18356NoRealWorker();
}
const v18356BaseChrome=v555UpdateChrome;
v555UpdateChrome=function(root){
 v18356ReconcileRollover();
 const result=v18356BaseChrome(root);
 if(v18356CanUseJobButtons()){
  for(const el of root?.querySelectorAll?.('[data-action="v89-job-wait"],[data-action="advance"]')||[]){
   el.disabled=false;el.removeAttribute('aria-busy');
   if(el.dataset?.action==='v89-job-wait')el.title='Avançar até o fim da temporada ou próxima proposta';
  }
 }
 return result;
};
const v18356BasePrepare=v53Prepare;
v53Prepare=async function(op,...args){
 const year=Number(state?.year)||0;
 const result=await v18356BasePrepare(op,...args);
 if(op==='next'&&state&&Number(state.year)>year){
  // v168 renders while v53Creating is still true. Refresh ONLY the chrome
  // after the async finally has cleared the busy flags.
  queueMicrotask(()=>{
   try{v18356ReconcileRollover();v555UpdateChrome(document.querySelector('#app')||document);}
   catch(e){console.warn('[18.356] unemployed chrome refresh',e);}
  });
 }
 return result;
};
window.GestorFC.unemployedSeason18356={
 version:'18.356',liveNewSeasonWorker:true,previousSavePreserved:true,
 status:()=>({year:state?.year,day:state?.day,eligible:v18356Unemployed(),
  busy:!v18356NoRealWorker(),deferred:!!v168DeferredRolloverSave,
  pendingDismissal:!!v18112Dismissal.pending,mayAdvance:v18356CanUseJobButtons()})
};
"""

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_jobwait_18356.py <project>')
    root=Path(sys.argv[1]).resolve()
    target=root/'src'/'index.html'
    s=target.read_text(encoding='utf-8')
    if MARK in s:raise RuntimeError('18.356 already applied')
    for required in ('FUTBR_UNEMPLOYED_RESUME_18334_BEGIN','FUTBR_UNEMPLOYED_TURBO_18327',
      'FUTBR_JOB_SAVE_EXIT_18355','v18311LiveVacation','v168DeferredRolloverSave'):
        if required not in s:raise RuntimeError('Missing stable baseline '+required)

    s=one(s,
     "const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=mode==='vacation'&&!!options?.liveStateNoPreSave;",
     """const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=!!options?.liveStateNoPreSave&&
      (mode==='vacation'||((mode==='day'||mode==='dayfast')&&
       state?.userEmployed===false&&!state?.v640National?.userTeam));""",
     'live unemployed first day worker')
    s=one(s,
     "useResident:mode==='day'||mode==='dayfast'||mode==='nationaljump'||mode==='nextmatch',",
     "useResident:!v18311LiveVacation&&(mode==='day'||mode==='dayfast'||mode==='nationaljump'||mode==='nextmatch'),",
     'never reuse old season resident Worker')
    s=one(s,
     "if(v168DeferredRolloverSave&&state&&mode==='vacation'){",
     """if(v168DeferredRolloverSave&&state&&(mode==='vacation'||
       ((mode==='day'||mode==='dayfast')&&state.userEmployed===false&&
        !state.v640National?.userTeam))){""",
     'reuse safe live-state rollover route for unemployed manual or fast day')
    # The 18.311 wrapper sets liveStateNoPreSave and transfers state, retains
    # the old disk checkpoint, and restores deferred status if Worker fails.
    s=one(s,
     'function v18334ShouldWait(){',
     'function v18334ShouldWait(){\n v18356ReconcileRollover();',
     'release stale year-end dismissal flag before computing button disabled')
    s=one(s,
     'async function v89RunJobWait(){',
     'async function v89RunJobWait(){\n v18356ReconcileRollover();',
     'allow original Turbo job wait to resume on the new authoritative season')
    anchor='/* FUTBR_UNEMPLOYED_RESUME_18334_END */'
    s=one(s,anchor,anchor+'\n'+HELPER,'restore UI only after fully completed rollover')
    s=one(s,"const EDITION='18.355.0';","const EDITION='18.356.0';",'visual edition')
    s=one(s,"window.GestorFC.version='18.355.0';window.GestorFC.visualVersion='18.355.0';",
            "window.GestorFC.version='18.356.0';window.GestorFC.visualVersion='18.356.0';",
            'runtime edition')
    target.write_text(s,encoding='utf-8')
    report={'ok':True,'version':'18.356.0','newSeasonUnemployedJobWaitRestored':True,
     'sameSeasonDismissalAuditPreserved':True,'noRealWorkerGuard':True,
     'firstDayWorkerUsesAuthoritativeLiveState':True,'noPreviousYearReplayed':True,
     'oldCheckpointPreservedUntilWorkerSave':True,'manualAndAutomaticAdvance':True,
     'keepsEmployedAndNationalModesUnchanged':True}
    (root/'jobwait-season-18356-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
