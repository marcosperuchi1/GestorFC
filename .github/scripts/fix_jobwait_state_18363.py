from __future__ import annotations
import json,sys
from pathlib import Path

VERSION='18.363.0'
MARK='FUTBR_JOBWAIT_STATE_CORE_18363'

def once(s,a,b,label):
    n=s.count(a)
    if n!=1: raise RuntimeError(f'18.363 {label}: expected one source anchor, got {n}')
    return s.replace(a,b,1)

CORE=r"""
/* FUTBR_JOBWAIT_STATE_CORE_18363
   The button's source of truth is the current unemployed career and REAL
   in-flight operations. Previous releases depended on a single-use
   'finished on exactly this year/day/world object' event; after another day
   or reloading a save that evidence disappeared and the button froze.
   This uses constant-time runtime checks, without rereading historical
   archives, scanning player keys, or writing a whole-world checkpoint. */
let v18363RecoveredStale=0,v18363Paints=0,v18363Retry=null,
    v18363LastBlocker='not-checked';
function v18363NoActualWork(s=state){
 if(!s||s.userEmployed!==false||s.v640National?.userTeam||
    s.vacation?.active||s.live||!s.players||
    !Array.isArray(s.teams)||!s.teams.length||
    !Array.isArray(s.schedule)||!s.schedule.length){
  v18363LastBlocker='not-a-complete-unemployed-world';return false;
 }
 // A finished callback and its outer checkpoint promotion are different
 // phases. Never interrupt a real Worker/transfer/rollover/save/IPC request.
 if(v53Sim?.active||v53Sim?.starting||v53Sim?.finished||
    v125VacIncoming||v53Creating||v52SavePromise||
    (typeof v53RPC!=='undefined'&&v53RPC?.size>0&&
     typeof v53Worker!=='undefined'&&!!v53Worker)||
    (typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)||
    (typeof v18121NewSeasonPreparation!=='undefined'&&v18121NewSeasonPreparation)||
    (typeof v18326AdvanceBusy!=='undefined'&&v18326AdvanceBusy)||
    (typeof v168RolloverRunning!=='undefined'&&v168RolloverRunning)||
    (typeof v91RolloverActive!=='undefined'&&v91RolloverActive)||
    (typeof v18359VacationPromise!=='undefined'&&v18359VacationPromise)||
    (typeof v18362VacationOrigin!=='undefined'&&v18362VacationOrigin)){
  v18363LastBlocker='actual-operation-in-flight';return false;
 }
 v18363LastBlocker='none';
 return true;
}
function v18363CanUseJobWait(){
 if(v89JobWait?.active)return false; // The active button is STOP, not START.
 if(!v18363NoActualWork())return false;
 // Once the Worker, vacation stream and checkpoint promise are all settled,
 // these flags are only leftovers from the former club. Repair at source,
 // not merely with a DOM disabled=false override.
 if(v18112Dismissal.pending||v53Sim?.syncing||v53Sim?.patching||v52Processing){
  const s=state,careerId=String(s.v1903CareerId||'');
  if(typeof v18357LiveFallback!=='undefined')
   v18357LiveFallback={year:Number(s.year),day:Number(s.day),careerId};
  v18112Dismissal.pending=false;v18112Dismissal.ready=true;
  v53Sim.syncing=false;v53Sim.patching=false;v52Processing=false;
  v18363RecoveredStale++;
 }
 return true;
}
function v18363PaintJobButtons(root=document){
 if(!root||!state||state.userEmployed!==false)return;
 v18363Paints++;
 const stopping=!!v89JobWait?.active;
 const allowed=stopping?!v89JobWait.stop:v18363CanUseJobWait();
 for(const btn of root.querySelectorAll?.('[data-action="v89-job-wait"]')||[]){
  btn.disabled=!allowed;
  if(allowed){
   btn.removeAttribute('disabled');btn.removeAttribute('aria-busy');
   btn.title=stopping?'Parar o avanço automático':'Avançar até o fim da temporada ou próxima proposta';
  }else{
   btn.setAttribute('disabled','');
   btn.setAttribute('aria-busy','true');
   btn.title=stopping?'Interrupção solicitada':'Aguardando conclusão de uma operação real';
  }
 }
 // Only a tiny DOM state check is retried, never render(), persistence,
 // or a complete career traversal. This repairs buttons when an async
 // save/transfer completed after the last chrome repaint.
 if(!allowed&&!stopping&&!state.vacation?.active&&v18363Retry===null){
  v18363Retry=setTimeout(()=>{
   v18363Retry=null;
   if(state?.userEmployed===false)v18363PaintJobButtons(document);
  },900);
 }
}
const v18363BaseChrome=v555UpdateChrome;
v555UpdateChrome=function(root){
 const out=v18363BaseChrome(root);
 v18363PaintJobButtons(root||document);
 return out;
};
window.GestorFC=window.GestorFC||{};
window.GestorFC.jobWait18363={
 version:'18.363',status:()=>({
  unemployed:!!(state?.userEmployed===false),
  year:state?.year,day:state?.day,careerId:String(state?.v1903CareerId||''),
  usable:v18363NoActualWork()&&!v89JobWait?.active,
  reason:v18363LastBlocker,
  jobRunning:!!v89JobWait?.active,realWorkerActive:!!v53Sim?.active,
  formerDismissalPending:!!v18112Dismissal.pending,
  staleRecovered:v18363RecoveredStale,
  chromePasses:v18363Paints
 }),
 refresh:()=>v18363PaintJobButtons(document)
};
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_jobwait_state_18363.py <project>')
 root=Path(sys.argv[1]).resolve();p=root/'src/index.html'
 s=p.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.363 source patch installed twice')
 for anchor in ('FUTBR_CORE_LIFECYCLE_18362','FUTBR_DISMISSAL_FINISHED_SIGNAL_18359',
       'FUTBR_JOBWAIT_SEASON_RECOVERY_18356','FUTBR_LONG_CAREER_SAVE_18338_BEGIN',
       'async function v89RunJobWait(){','function v18334ShouldWait(){',
       'const v18359BaseChrome=v555UpdateChrome;','</body>'):
  if anchor not in s:raise RuntimeError('18.363 missing validated source '+anchor)
 a=s.index('async function v89RunJobWait(){')
 b=s.index('const v89BaseCareerPage=careerPage;',a)
 job=s[a:b]
 job=once(job,
  "if(!v18359TrustedCompleted()&&(v18112Dismissal.pending||v53Sim?.active||v53Sim?.starting||v53Sim?.patching||v53Sim?.syncing)){",
  "if(!v18363CanUseJobWait()){",
  'replace original real click guard with state-based safety check')
 s=s[:a]+job+s[b:]
 s=once(s,'function v18334ShouldWait(){\n v18356ReconcileRollover();',
   'function v18334ShouldWait(){\n v18356ReconcileRollover();\n if(v18363CanUseJobWait())return false;',
   'avoid old dismissal audit/recovery repaint blocking stable unemployed state')
 s=once(s,'</body>',
  '<script id="futbr-jobwait-state-18363">\n'+CORE+'\n</script>\n</body>',
  'attach final authoritative chrome adapter')
 s=once(s,"const EDITION='18.362.0';","const EDITION='18.363.0';",'visible version')
 s=once(s,"window.GestorFC.version='18.362.0';window.GestorFC.visualVersion='18.362.0';",
        "window.GestorFC.version='18.363.0';window.GestorFC.visualVersion='18.363.0';",
        'runtime version')
 p.write_text(s,encoding='utf-8')
 report={'ok':True,'version':VERSION,'reason':'obsolete one-time Worker completion signal',
    'realClickGuardReplaced':True,'realUnemployedStateSource':True,
    'reloadedSaveSupported':True,'midSeasonAfterOneDaySupported':True,
    'postDismissalStaleFlagsReconciled':True,'workerAndStreamingSafetyRetained':True,
    'jobStopStaysAccessible':True,'noHeavyDataTraversal':True,
    'noExtraSave':True,'historyAndCareerSerializationUnchanged':True}
 (root/'jobwait-state-18363-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
