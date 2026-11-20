from __future__ import annotations
import json,sys
from pathlib import Path
VERSION='18.365.0'
MARK='FUTBR_DISMISSAL_SOURCE_18365'

def once(src,old,new,label):
 n=src.count(old)
 if n!=1: raise RuntimeError(f'18.365 {label}: expected one source anchor, got {n}')
 return src.replace(old,new,1)

CORE=r"""
/* FUTBR_DISMISSAL_SOURCE_18365
   Actual click routing and the original vacation Worker are authoritative.
   v18364 allowed a second click to CANCEL a queued job search with no visible
   label change. This state machine is idempotent: a second click keeps the
   same request, displays progress, and never starts a concurrent Worker.
   Dismissal automatically requests an end from its existing vacation Worker.
   Only the resolved original Promise + streaming checkpoint releases job wait.
*/
const v18365Job={pending:false,careerId:'',session:0,requested:0,
 duplicateClicks:0,workerStopSent:0,started:0,failed:0,last:'idle',
 timer:null,lastStop:0,queuedAt:0,warningShown:false};
function v18365Unemployed(s=state){
 return !!s&&s.userEmployed===false&&!s.v640National?.userTeam;
}
function v18365RealWorkerBusy(){
 return !!(v53Sim?.active||v53Sim?.starting||v53Sim?.finished||
  v125VacIncoming||v53Creating||v52SavePromise||
  (typeof v18359VacationPromise!=='undefined'&&v18359VacationPromise)||
  (typeof v18362VacationOrigin!=='undefined'&&v18362VacationOrigin)||
  (typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)||
  (typeof v18121NewSeasonPreparation!=='undefined'&&v18121NewSeasonPreparation)||
  (typeof v168RolloverRunning!=='undefined'&&v168RolloverRunning));
}
function v18365RequestVacStop(){
 if(!v18365Unemployed()||!v53Sim||v53Sim.mode!=='vacation'||
    !v53Sim.active||!v53Worker)return false;
 try{
  v53Sim.pause=true;v53Sim.pauseMode='end';
  v53Worker.postMessage({op:'pause',end:true,source:'jobwait-18365'});
  v18365Job.workerStopSent++;
  v18365Job.lastStop=Date.now();
  return true;
 }catch(e){v18365Job.last='worker-stop-send-failed';
  console.warn('[18.365] original vacation Worker pause:',e);return false;}
}
function v18365CareerMatch(){
 return v18365Unemployed()&&
  String(state.v1903CareerId||'')===v18365Job.careerId&&
  (!v18365Job.session||!v53Sim?.session||
   Number(v53Sim.session)===v18365Job.session);
}
function v18365Paint(root=document){
 if(!root||!v18365Unemployed())return;
 if(v18365Job.pending){
  for(const b of root.querySelectorAll?.('[data-action="v89-job-wait"]')||[]){
   b.disabled=false;b.removeAttribute('disabled');b.removeAttribute('aria-busy');
   b.textContent='Encerrando férias · buscando proposta...';
   b.title='A solicitação já foi registrada. Aguarde a sincronização segura da jornada em andamento.';
   b.setAttribute('aria-live','polite');
  }
 }
 // Career navigation always remains readable while the old vacation is
 // committing. The page itself shows a bounded read-only sync banner.
 for(const b of root.querySelectorAll?.('[data-action="nav"][data-view="career"]')||[]){
  b.disabled=false;b.removeAttribute('disabled');b.removeAttribute('aria-busy');
  b.title='Minha carreira e histórico do treinador';
 }
}
function v18365Schedule(){
 if(!v18365Job.pending||v18365Job.timer!==null)return;
 v18365Job.timer=setTimeout(()=>{
  v18365Job.timer=null;
  if(!v18365Job.pending)return;
  if(!v18365CareerMatch()){
   v18365Job.pending=false;v18365Job.last='career-changed';
   return;
  }
  if(v53Sim?.mode==='vacation'&&v53Sim.active){
   if(Date.now()-v18365Job.lastStop>2800)v18365RequestVacStop();
   if(!v18365Job.warningShown&&Date.now()-v18365Job.queuedAt>16000){
    v18365Job.warningShown=true;
    toast('Finalizando a jornada e seus dados. A busca continuará após a sincronização; nenhum segundo Worker foi iniciado.','warn');
   }
  }else if(!v18365RealWorkerBusy()){
   void v18365FinishHandoff(true);return;
  }
  v18365Paint(document);
  v18365Schedule();
 },1200);
}
async function v18365FinishHandoff(success){
 if(!v18365Job.pending)return false;
 if(!v18365CareerMatch()){
  v18365Job.pending=false;v18365Job.last='career-changed';return false;
 }
 if(!success){
  v18365Job.pending=false;v18365Job.failed++;
  v18365Job.last='original-vacation-failed';
  toast('O Worker não concluiu o retorno da carreira. O salvamento anterior foi mantido; não iniciamos outro Worker.','error');
  return false;
 }
 // This is called after the 18.362 original Promise resolved, not while its
 // final streaming chunks are still being received.
 if(v18365RealWorkerBusy()){
  v18365Job.last='waiting-for-original-checkpoint';
  v18365Schedule();return false;
 }
 if(state?.vacation?.active){
  if(!v18364RepairOrphan()){
   v18365Job.last='waiting-for-original-vacation-state';
   v18365Schedule();return false;
  }
 }
 if(!v18363CanUseJobWait()){
  v18365Job.last='job-safety-check-waiting';
  v18365Schedule();return false;
 }
 v18365Job.pending=false;v18365Job.started++;
 v18365Job.last='job-search-started';
 view='career';
 try{render();}catch(e){console.warn('[18.365] career redraw:',e);}
 try{await v89RunJobWait();return true;}
 catch(e){v18365Job.failed++;v18365Job.last='job-search-error';
  toast('A busca automática foi interrompida: '+(e?.message||e),'error');return false;}
}
function v18365OnVacationSettled(origin,success){
 if(!v18365Job.pending)return false;
 if(!origin||String(origin.careerId||'')!==v18365Job.careerId){
  v18365Job.pending=false;v18365Job.last='origin-changed';return false;
 }
 void v18365FinishHandoff(success);
 return true;
}
function v18365HandleClick(el){
 if(!v18365Unemployed())return false;
 if(v89JobWait?.active){
  void v89RunJobWait();return true;
 }
 if(v18365Job.pending){
  v18365Job.duplicateClicks++;
  v18365Job.last='existing-request-reused';
  v18365RequestVacStop();
  v18365Schedule();v18365Paint(document);
  return true; // Never cancel a registered request on a hidden second click.
 }
 if(!v18365RealWorkerBusy()&&!state.vacation?.active){
  void v89RunJobWait().catch(e=>toast(e?.message||String(e),'error'));
  return true;
 }
 v18365Job.pending=true;v18365Job.requested++;
 v18365Job.careerId=String(state.v1903CareerId||'');
 v18365Job.session=v53Sim?.active?(Number(v53Sim.session)||0):0;
 v18365Job.queuedAt=Date.now();
 v18365Job.warningShown=false;
 v18365Job.last='queued-after-dismissal';
 v18365RequestVacStop();
 v18365Schedule();
 try{v555UpdateChrome(document);}catch(e){v18365Paint(document);}
 toast('Encerrando as férias e preservando a última jornada. A busca de propostas será iniciada automaticamente.','warn');
 return true;
}
const v18365BaseChrome=v555UpdateChrome;
v555UpdateChrome=function(root){
 const out=v18365BaseChrome(root);
 v18365Paint(root||document);
 return out;
};
const v18365BaseCareer=careerPage;
careerPage=function(...args){
 if(v18365Unemployed()&&
    (v125VacIncoming||v53Sim?.syncing||
     (typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active))){
  return '<section class="panel v18365-sync-panel" role="status"><div class="panel-body"><h2>Minha carreira</h2><p>Sincronizando a jornada da demissão e o histórico do treinador. A leitura da carreira voltará quando o Worker concluir o envio.</p></div></section>';
 }
 const html=v18365BaseCareer(...args);
 if(!v18365Unemployed())return html;
 const message=v18365Job.pending?
  'Contrato encerrado. Encerrando as férias e preparando a busca por propostas.':
  'Treinador livre. O histórico permanece disponível e você pode aguardar novas propostas.';
 const notice='<div class="v18365-career-note" role="status">'+message+'</div>';
 return html.replace(/(<div class="v636-career-page"[^>]*>)/, '$1'+notice);
};
window.GestorFC=window.GestorFC||{};
window.GestorFC.jobHandoff18365={
 version:'18.365',status:()=>({
  pending:v18365Job.pending,last:v18365Job.last,
  unemployed:v18365Unemployed(),requestCount:v18365Job.requested,
  repeatedClicks:v18365Job.duplicateClicks,
  stopSent:v18365Job.workerStopSent,started:v18365Job.started,
  failed:v18365Job.failed,year:state?.year,day:state?.day,
  vacationActive:!!state?.vacation?.active,
  workerActive:!!v53Sim?.active,workerMode:v53Sim?.mode,
  outerVacationPending:!!v18359VacationPromise
 }),
 click:()=>v18365HandleClick(null)
};
"""
CSS=r"""
<style id="futbr-career-readable-18365">
body.v636-career-view .main{height:auto!important;min-height:0!important;overflow-y:auto!important;display:block!important;padding-bottom:20px!important}
body.v636-career-view #v555-page{height:auto!important;flex:none!important;min-height:0!important}
body.v636-career-view .v636-career-page{height:auto!important;min-height:0!important}
body.v636-career-view .v636-career-head{height:auto!important}
body.v636-career-view .v636-career-table{height:auto!important}
.v18365-career-note{padding:10px 12px;border:1px solid var(--line);border-radius:9px;color:var(--text);font-size:12px;line-height:1.45;background:var(--panel);margin-bottom:6px}
.v18365-sync-panel{max-width:100%;min-height:110px}
</style>
"""
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_dismissal_source_18365.py <project>')
 root=Path(sys.argv[1]);p=root/'src/index.html'
 s=p.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.365 already applied')
 for t in ('FUTBR_VACATION_JOB_HANDOFF_18364','FUTBR_JOBWAIT_STATE_CORE_18363',
           'FUTBR_CORE_LIFECYCLE_18362','v18112MarkDismissal(m);',
           'v18364OnVacationSettled(origin,v18364Succeeded);'):
  if t not in s:raise RuntimeError('18.365 missing required source '+t)
 s=once(s,
  "if(el&&!el.disabled){try{if(!(typeof v125DirectAction==='function'&&v125DirectAction(el)))act(el);}",
  "if(el&&!el.disabled){try{if(el.dataset.action==='v89-job-wait'&&typeof v18365HandleClick==='function'&&v18365HandleClick(el))return;if(!(typeof v125DirectAction==='function'&&v125DirectAction(el)))act(el);}",
  'real global click route, not a later overwritten act wrapper')
 # Locate this event by its kind, not by the following status paint:
 # old releases insert additional 18.112/18.119 hooks between these lines.
 event_start=s.index("if(m.kind==='vac-dismissed'){")
 event_end=s.index('continue;',event_start)+len('continue;')
 event_block=s[event_start:event_end]
 mark='v18112MarkDismissal(m);'
 if event_block.count(mark)!=1:
  raise RuntimeError('18.365 original dismissed Worker event missing unique marker')
 event_block=event_block.replace(mark,mark+"""
     // Contract ended: stop the SAME vacation Worker after the safe day.
     // Do not start the next job Worker until its original checkpoint returns.
     if(v53Sim?.active&&v53Sim?.mode==='vacation'){
      v53Sim.pause=true;v53Sim.pauseMode='end';
      try{v53Worker?.postMessage({op:'pause',end:true,reason:'dismissal'});}
      catch(e){console.warn('[18.365] dismissal safe stop',e);}
     }
""",1)
 s=s[:event_start]+event_block+s[event_end:]
 s=once(s,
  "if(v53Sim.syncing)throw Error('Sincronizando a carreira após as férias. Aguarde alguns instantes.');",
  "if(v53Sim.syncing&&!(a==='nav'&&(el.dataset.view==='career'||el.dataset.view==='vacation')))throw Error('Sincronizando a carreira após as férias. Aguarde alguns instantes.');",
  'keep read-only career navigation possible during vacation synchronization')
 s=once(s,
  "queueMicrotask(()=>{void v18364OnVacationSettled(origin,v18364Succeeded);});",
  """queueMicrotask(()=>{void v18364OnVacationSettled(origin,v18364Succeeded);});
   if(typeof v18365OnVacationSettled==='function')
    queueMicrotask(()=>v18365OnVacationSettled(origin,v18364Succeeded));""",
  'continue job search only after real original vacation Promise')
 s=once(s,
  "const status=v.active?'Em execução':v.remaining?'Pausadas':'No comando';",
  "const status=v.active?(state?.userEmployed===false?'Encerrando férias':'Em execução'):v.remaining?'Pausadas':'No comando';",
  'vacation UI says closing after dismissed, not still running normally')
 s=once(s,'</body>',CSS+'<script id="futbr-dismissal-source-18365">\n'+CORE+'\n</script>\n</body>',
  'safe source-linked controller and smaller career page')
 s=once(s,"const EDITION='18.364.0';","const EDITION='18.365.0';",'version')
 s=once(s,
  "window.GestorFC.version='18.364.0';window.GestorFC.visualVersion='18.364.0';",
  "window.GestorFC.version='18.365.0';window.GestorFC.visualVersion='18.365.0';",
  'runtime version')
 p.write_text(s,encoding='utf-8')
 report={'ok':True,'version':VERSION,'actualGlobalClickDispatcherPatched':True,
   'originalVacationWorkerStopsOnDismissal':True,
   'repeatedClickKeepsSearchPending':True,'explicitPendingLabel':True,
   'keepsCareerReadOnlyDuringSync':True,'preventsLargeBlankCareerPanel':True,
   'onlyUsesOriginalWorkerAndSafeCompletion':True,
   'noDoubleWorkers':True,'noHistoryOrSaveCodecChanges':True}
 (root/'dismissal-source-18365-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
