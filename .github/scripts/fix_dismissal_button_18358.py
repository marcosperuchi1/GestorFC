from __future__ import annotations
import json,sys
from pathlib import Path

VERSION='18.358.0'
MARK='FUTBR_DISMISSAL_BUTTON_RECOVERY_18358'

def once(s,old,new,name):
    n=s.count(old)
    if n!=1:raise RuntimeError(f'18.358 {name}: expected 1 anchor, got {n}')
    return s.replace(old,new,1)

HELPER=r"""
/* FUTBR_DISMISSAL_BUTTON_RECOVERY_18358
   18.357 could leave "Aguardando a sincronizacao da demissao" indefinitely
   after the vacation promise + 17.1 checkpoint had ALREADY settled:
   v52Processing, a stale season-overlay flag or an unrelated RPC prevented
   the post-Worker dismissal callback from ever releasing the buttons.
   Only a finished, fully received Worker world is trusted here. */
let v18358PromotionSettled=false,v18358RecoveryDone=false,
    v18358RecoveryCount=0,v18358LastBlocker='';
function v18358WorldReady(){
 const s=state;
 return !!s&&s.userEmployed===false&&!s.v640National?.userTeam&&
  !!s.players&&Array.isArray(s.teams)&&Array.isArray(s.schedule)&&
  !v53Sim?.active&&!v53Sim?.starting&&!v53Sim?.finished&&
  !v125VacIncoming&&
  (!v18112Dismissal.careerId||
   String(v18112Dismissal.careerId)===String(s.v1903CareerId||''));
}
function v18358HandoffReady(){
 return v18358PromotionSettled&&v18357AwaitingPromotion&&
  !!v18112Dismissal.pending&&v18358WorldReady();
}
function v18358CompleteOldOverlay(){
 if(!v18358HandoffReady())return false;
 // An ended Worker cannot still be importing player/history chunks.
 // Transfer/paint flags from its old UI shell must not outlive that event.
 if(typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active){
  try{v18119CompleteSeasonTransfer();}catch(e){
   console.warn('[18.358] season overlay release:',e);
  }
 }
 v53Sim.syncing=false;v53Sim.patching=false;
 v18358RecoveryCount++;
 return true;
}
function v18358SafeJobButtons(){
 return v18358RecoveryDone&&v18358WorldReady()&&
  !v89JobWait.active&&!state?.vacation?.active&&!state?.live;
}
window.GestorFC.dismissalButton18358={
 version:'18.358',postVacationWorkerSignalRequired:true,
 noForceCloseOfActiveWorker:true,usesExistingCheckpoints:true,
 status:()=>({year:state?.year,day:state?.day,seasonDone:!!state?.seasonDone,
  dismissalPending:!!v18112Dismissal.pending,
  promotionSettled:v18358PromotionSettled,eligible:v18358WorldReady(),
  recovered:v18358RecoveryDone,recoveries:v18358RecoveryCount,
  lastBlocker:v18358LastBlocker,transferActive:!!v18119SeasonTransfer?.active,
  uiSyncing:!!v53Sim?.syncing,workerRunning:!!v53Sim?.active}),
};
"""

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_dismissal_button_18358.py <project>')
    root=Path(sys.argv[1]);p=root/'src/index.html'
    src=p.read_text(encoding='utf-8')
    if MARK in src:raise RuntimeError('18.358 patched twice')
    for text in ('FUTBR_DISMISSAL_HANDOFF_18357','FUTBR_JOBWAIT_SEASON_RECOVERY_18356',
        'FUTBR_JOB_SAVE_EXIT_18355','function v18357NoPendingWorldTransfer()',
        'const baseStart171=v53StartSimulation;'):
        if text not in src:raise RuntimeError('Required 18.357 source missing: '+text)
    src=once(src,'/* FUTBR_DISMISSAL_HANDOFF_18357',
        HELPER+'\n/* FUTBR_DISMISSAL_HANDOFF_18357','install trusted completion marker')
    src=once(src,'function v18357NoPendingWorldTransfer(){',
        """function v18357NoPendingWorldTransfer(){
 if(v18358HandoffReady())return true;
""",'do not wait for stale non-worker postvacation flags')
    src=once(src,' const current=state,year=Number(current.year),day=Number(current.day),',
        """ if(v18358HandoffReady())v18358CompleteOldOverlay();
 const current=state,year=Number(current.year),day=Number(current.day),""",
        'release completed season overlay before manifest audit')
    src=once(src," v18357AwaitingPromotion=false;\n if(v18357Retry!==null)",
        " v18357AwaitingPromotion=false;\n v18358RecoveryDone=true;v18358LastBlocker='none';\n if(v18357Retry!==null)",
        'mark actual completed dismissal and released controls')
    src=once(src,"  v18357LastStatus='waiting-for-real-worker-or-checkpoint';",
        """  v18357LastStatus='waiting-for-real-worker-or-checkpoint';
  v18358LastBlocker=v53Sim?.active?'worker-active':
   v53Sim?.finished?'worker-unfinished':
   v125VacIncoming?'world-transfer-running':
   v53Sim?.syncing?'legacy-sync-flag':
   v52Processing?'legacy-save-flag':'old-ui-guard';""",
        'report actual reason when Worker is not yet finished')
    src=once(src,"const v18357Live=v18357WantsLiveJobState(mode);",
        """if(mode==='vacation'){v18358PromotionSettled=false;v18358RecoveryDone=false;}
  const v18357Live=v18357WantsLiveJobState(mode);""",
        'reset trusted signal at start of a different vacation')
    src=once(src,
        "if(mode==='vacation'&&v18357AwaitingPromotion&&v18112Dismissal.pending){\n   await v18357FinalizeDismissal();",
        """if(mode==='vacation'&&v18357AwaitingPromotion&&v18112Dismissal.pending){
   // Runs ONLY after the original 17.1 promotion try/finally completed.
   v18358PromotionSettled=true;
   await v18357FinalizeDismissal();""",
        'release only after completed checkpoint promotion')
    # Legacy UI checks treated a finished vacation as busy because the
    # old shell still held unrelated UI flags. Never ignore an active Worker.
    src=once(src,"function v18334ShouldWait(){\n v18356ReconcileRollover();",
        """function v18334ShouldWait(){
 v18356ReconcileRollover();
 if(v18358SafeJobButtons()&&!v89JobWait.active)return false;""",
        'unblock old dismissal UI guard on completed Worker')
    src=once(src,"function v18356NoRealWorker(){",
        """function v18356NoRealWorker(){
 if(v18358SafeJobButtons())return true;""",
        'preserve UI buttons after verified dismissal')
    src=once(src,
        "async function v89RunJobWait(){\n v18356ReconcileRollover();",
        """async function v89RunJobWait(){
 v18356ReconcileRollover();
 if(v18358SafeJobButtons()){v53Sim.syncing=false;v53Sim.patching=false;}
""",
        'click guard agrees with post-dismissal chrome')
    # At the season's last round the old UI explicitly hid the button,
    # even though the requested goal is "until proposal". Continue into
    # the next season on user action; the existing 18.356 first-day Worker
    # routing prevents reloading last year's checkpoint.
    src=once(src,
      "if(state&&!state.userEmployed&&!v89HasNationalJob()&&!state.seasonDone){",
      "if(state&&!state.userEmployed&&!v89HasNationalJob()){",
      'show unemployed until-proposal button at season end too')
    src=once(src,"const disabled=state.seasonDone?'disabled':'';",
      "const disabled='';",
      'do not show an inert season-end unemployed button')
    src=once(src,
      "if(!state||state.userEmployed||v89HasNationalJob())return;if(state.seasonDone){toast('A temporada já terminou. Inicie a próxima temporada para continuar aguardando propostas.','warn');return;}",
      """if(!state||state.userEmployed||v89HasNationalJob())return;
 if(state.seasonDone){
  try{await v53Prepare('next');}
  catch(e){toast('Não foi possível iniciar a próxima temporada: '+(e?.message||e),'error');return;}
  if(!state||state.seasonDone)return;
 }""",
      'wait for offers across ended seasons instead of leaving button disabled')
    src=once(src,"const EDITION='18.357.0';","const EDITION='18.358.0';",'sidebar version')
    src=once(src,
      "window.GestorFC.version='18.357.0';window.GestorFC.visualVersion='18.357.0';",
      "window.GestorFC.version='18.358.0';window.GestorFC.visualVersion='18.358.0';",
      'runtime version')
    p.write_text(src,encoding='utf-8')
    report={'ok':True,'version':VERSION,'dismissalButtonRestored':True,
     'finishedWorkerRequired':True,'realWorldArraysRequired':True,
     'staleUIMarkersDoNotBlock':True,'seasonEndOffersContinueNextSeason':True,
     'firstDayUsesOriginal18356Safety':True,'checkpointsAndCareerIdentityPreserved':True}
    (root/'dismissal-button-18358-install.json').write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
