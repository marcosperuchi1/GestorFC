from __future__ import annotations
import json
import sys
from pathlib import Path

VERSION='18.364.0'
MARK='FUTBR_VACATION_JOB_HANDOFF_18364'

def one(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'18.364 {label}: expected 1 original anchor, found {n}')
 return s.replace(a,b,1)

CORE=r"""
/* FUTBR_VACATION_JOB_HANDOFF_18364
   A coach fired DURING holidays can be unemployed while the vacation Worker
   is still advancing/sending its final checkpoint. 18.363 accidentally
   painted the job-search button but the actual action rejected it as busy.
   This handoff requests the EXISTING Worker pause(end=true), waits for its
   original final world and atomic checkpoint, then starts job search once.
   Never terminate a running Worker or open a second Worker in parallel. */
const v18364JobHandoff={pending:false,careerId:'',session:0,requested:0,
 resumed:0,canceled:0,last:'idle',pauseSent:false};
function v18364Unemployed(){
 return !!state&&state.userEmployed===false&&!state.v640National?.userTeam;
}
function v18364HolidaysInFlight(){
 return !!v53Sim&&v53Sim.mode==='vacation'&&
  !!(v53Sim.active||v53Sim.starting||
      (typeof v18359VacationPromise!=='undefined'&&v18359VacationPromise)||
      (typeof v18362VacationOrigin!=='undefined'&&v18362VacationOrigin));
}
function v18364CanRepairOrphan(){
 if(!v18364Unemployed()||!state.vacation?.active||v18364HolidaysInFlight()||
    v53Sim?.active||v53Sim?.starting||v53Sim?.finished||
    v125VacIncoming||v53Creating||v52SavePromise||
    (typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)||
    (typeof v18121NewSeasonPreparation!=='undefined'&&v18121NewSeasonPreparation)||
    (typeof v168RolloverRunning!=='undefined'&&v168RolloverRunning))return false;
 return !!state.players&&Array.isArray(state.teams)&&state.teams.length>0&&
  Array.isArray(state.schedule)&&state.schedule.length>0;
}
function v18364RepairOrphan(){
 if(!v18364CanRepairOrphan())return false;
 state.vacation.active=false;state.vacation.paused=true;
 state.vacation.remaining=0;state.vacation.untilSeason=false;
 state.vacation.reason='Contrato encerrado. Aguardando propostas.';
 const careerId=String(state.v1903CareerId||'');
 if(typeof v18357LiveFallback!=='undefined')
  v18357LiveFallback={year:Number(state.year),day:Number(state.day),careerId};
 v18364JobHandoff.last='recovered-orphan-vacation';
 return true;
}
function v18364RequestWorkerPause(){
 if(!v18364JobHandoff.pending||v18364JobHandoff.pauseSent||
    !v18364HolidaysInFlight()||!v53Sim?.active||!v53Worker)return false;
 if(String(state?.v1903CareerId||'')!==v18364JobHandoff.careerId)return false;
 if(v18364JobHandoff.session&&Number(v53Sim.session)!==v18364JobHandoff.session)return false;
 try{
  v53Sim.pause=true;v53Sim.pauseMode='end';
  v53Worker.postMessage({op:'pause',end:true});
  v18364JobHandoff.pauseSent=true;
  v18364JobHandoff.last='requested-original-worker-end';
  return true;
 }catch(e){
  v18364JobHandoff.last='pause-send-error';
  console.warn('[18.364] vacation Worker end request',e);
  return false;
 }
}
function v18364QueueHandoff(){
 if(!v18364Unemployed())return false;
 if(v18364JobHandoff.pending){
  v18364JobHandoff.pending=false;v18364JobHandoff.canceled++;
  v18364JobHandoff.last='user-canceled-auto-search';
  toast('Busca automática cancelada. O encerramento seguro das férias continuará.','warn');
  try{v555UpdateChrome(document);}catch(e){}
  return true;
 }
 if(!v18364HolidaysInFlight())return false;
 v18364JobHandoff.pending=true;
 v18364JobHandoff.careerId=String(state.v1903CareerId||'');
 v18364JobHandoff.session=v53Sim?.active?(Number(v53Sim.session)||0):0;
 v18364JobHandoff.pauseSent=false;
 v18364JobHandoff.requested++;
 v18364JobHandoff.last='waiting-for-original-vacation-world';
 v18364RequestWorkerPause();
 toast('Encerrando as férias e sincronizando a carreira. A busca por propostas começará automaticamente após o retorno seguro do Worker.','warn');
 try{v555UpdateChrome(document);}catch(e){}
 return true;
}
async function v18364OnVacationSettled(origin,success){
 if(!v18364JobHandoff.pending)return false;
 const careerId=v18364JobHandoff.careerId,session=v18364JobHandoff.session;
 if(!origin||origin.careerId!==careerId||
    !state||String(state.v1903CareerId||'')!==careerId||
    (session&&Number(v53Sim?.session)!==session)){
  v18364JobHandoff.pending=false;
  v18364JobHandoff.last='career-or-session-changed';
  return false;
 }
 v18364JobHandoff.pending=false;
 if(!success){
  v18364JobHandoff.last='original-vacation-failed';
  toast('O encerramento das férias encontrou um erro. A carreira anterior foi preservada; tente salvar e retomar.','error');
  try{v555UpdateChrome(document);}catch(e){}
  return false;
 }
 // No Worker may be running after the original vacation Promise has settled.
 // If only its UI vacation flag remains from a partial/stale repaint, clear
 // the flag without reserializing any historical collection.
 if(state.vacation?.active)v18364RepairOrphan();
 if(!v18363CanUseJobWait()){
  v18364JobHandoff.last='post-vacation-safety-guard';
  toast('A carreira terminou as férias, mas ainda há uma sincronização ativa. Não foi iniciada outra simulação.','warn');
  try{v555UpdateChrome(document);}catch(e){}
  return false;
 }
 v18364JobHandoff.resumed++;
 v18364JobHandoff.last='starting-job-search';
 view='career';
 try{render();}catch(e){console.warn('[18.364] job-search view',e);}
 // The Promise and checkpoint are already settled; this starts dayfast using
 // the same authoritative career, and honors the old stop/offer behavior.
 try{await v89RunJobWait();return true;}
 catch(e){v18364JobHandoff.last='job-search-exception';toast('Não foi possível procurar propostas: '+(e?.message||e),'error');return false;}
}
function v18364HandleJobClick(){
 if(!v18364Unemployed())return false;
 if(v89JobWait?.active){void v89RunJobWait();return true;}
 if(v18364QueueHandoff())return true;
 if(state.vacation?.active){
  if(!v18364RepairOrphan()){
   toast('Aguardando a transferência segura dos dados da última jornada.','warn');
   return true;
  }
 }
 if(v53Sim?.active||v53Sim?.starting||v53Sim?.finished||v125VacIncoming){
  toast('Outra simulação está concluindo a transferência de dados.','warn');return true;
 }
 void v89RunJobWait().catch(e=>toast('Não foi possível avançar: '+(e?.message||e),'error'));
 return true;
}
function v18364RefreshJobButton(root=document){
 if(!root||!v18364Unemployed())return;
 const join=v18364HolidaysInFlight()||v18364CanRepairOrphan()||v18364JobHandoff.pending;
 if(!join)return;
 if(v18364JobHandoff.pending&&!v18364JobHandoff.pauseSent)v18364RequestWorkerPause();
 for(const btn of root.querySelectorAll?.('[data-action="v89-job-wait"]')||[]){
  btn.disabled=false;btn.removeAttribute('disabled');btn.removeAttribute('aria-busy');
  btn.title=v18364JobHandoff.pending?'Cancelar busca automática após as férias':
   'Concluir as férias em andamento e buscar uma nova proposta';
 }
}
const v18364BaseChrome=v555UpdateChrome;
v555UpdateChrome=function(root){
 const result=v18364BaseChrome(root);
 v18364RefreshJobButton(root||document);
 return result;
};
const v18364BaseAct=act;
act=function(el){
 if(el?.dataset?.action==='v89-job-wait'&&v18364Unemployed()){
  v18364HandleJobClick();return;
 }
 return v18364BaseAct(el);
};
window.GestorFC=window.GestorFC||{};
window.GestorFC.vacationHandoff18364={
 version:'18.364',status:()=>({
  ...v18364JobHandoff,
  unemployed:v18364Unemployed(),holidayInFlight:v18364HolidaysInFlight(),
  vacationActive:!!state?.vacation?.active,workerActive:!!v53Sim?.active,
  workerMode:v53Sim?.mode,session:Number(v53Sim?.session)||0,
  year:state?.year,day:state?.day
 }),
 request:()=>v18364HandleJobClick(),
 refresh:()=>v18364RefreshJobButton(document)
};
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_vacation_job_handoff_18364.py <project>')
 root=Path(sys.argv[1]).resolve()
 path=root/'src/index.html'
 src=path.read_text(encoding='utf-8')
 if MARK in src:raise RuntimeError('18.364 handoff applied twice')
 for mark in ('FUTBR_VACATION_JOB_HANDOFF_18364','FUTBR_JOBWAIT_STATE_CORE_18363',
              'FUTBR_CORE_LIFECYCLE_18362','async function v89RunJobWait(){'):
  if mark!='FUTBR_VACATION_JOB_HANDOFF_18364' and mark not in src:
   raise RuntimeError('18.364 required source missing '+mark)
 # Patch the actual vacation execution Promise in 18.362, not a painter.
 src=one(src,
  "  try{\n   const result=await p;\n   v18362Transitions.settled++;",
  "  let v18364Succeeded=false;\n  try{\n   const result=await p;\n   v18362Transitions.settled++;",
  'outer original vacation completion declaration')
 src=one(src,
  "   v18362CommitVacation(origin);\n   return result;",
  "   v18362CommitVacation(origin);\n   v18364Succeeded=true;\n   return result;",
  'mark only fulfilled vacation Promise as successful')
 src=one(src,
  "   if(v18362VacationOrigin===origin)v18362VacationOrigin=null;\n  }\n }\n if((mode==='day'||mode==='dayfast')",
  """   if(v18362VacationOrigin===origin)v18362VacationOrigin=null;
   // Handoff is triggered only AFTER the original Worker, patch stream,
   // 17.1 checkpoint promotion and 18.362 finalization all returned.
   if(typeof v18364OnVacationSettled==='function')
    queueMicrotask(()=>{void v18364OnVacationSettled(origin,v18364Succeeded);});
  }
 }
 if((mode==='day'||mode==='dayfast')""",
  'same original Worker completed Promise: handoff')
 src=one(src,'</body>',
  '<script id="futbr-vacation-handoff-18364">\n'+CORE+'\n</script>\n</body>',
  'authoritative last click and chrome adapter')
 src=one(src,"const EDITION='18.363.0';","const EDITION='18.364.0';",'version label')
 src=one(src,
  "window.GestorFC.version='18.363.0';window.GestorFC.visualVersion='18.363.0';",
  "window.GestorFC.version='18.364.0';window.GestorFC.visualVersion='18.364.0';",
  'version runtime')
 path.write_text(src,encoding='utf-8')
 rep={'ok':True,'version':VERSION,
  'actualVacWorkerPauseEnd':True,'originalPromiseAndCheckpointAwaited':True,
  'noParallelWorker':True,'jobSearchStartsAfterVacPromoted':True,
  'reloadedUnemployedVacationStateHandled':True,'stopCancelHandled':True,
  'careerAndWorkerSessionGuard':True,'originalHistoricalSaveUnchanged':True,
  'avoidsFullSaveDuringActiveVacation':True}
 (root/'vacation-handoff-18364-install.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(rep,ensure_ascii=False))

if __name__=='__main__':main()
