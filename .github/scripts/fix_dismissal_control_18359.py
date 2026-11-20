from __future__ import annotations
import json
import sys
from pathlib import Path

MARK='FUTBR_DISMISSAL_FINISHED_SIGNAL_18359'

def once(src,old,new,label):
    matches=src.count(old)
    if matches!=1:
        raise RuntimeError(f'18.359 {label}: expected 1 anchor, got {matches}')
    return src.replace(old,new,1)

HELPER=r"""
/* FUTBR_DISMISSAL_FINISHED_SIGNAL_18359
  The only authoritative "vacation dismissal completed" signal is the
  *successful finished message of the same Worker session*, after its full
  world stream was received. Old 18.112/18.334/18.356/18.358 UI flags do
  not define completion and must never keep a finished Worker blocked.
  The first unemployed day always uses the live synchronized world. */
let v18359FinishedWorld=null,v18359FinishCount=0,v18359ReleaseCount=0,
    v18359VacationPromise=null,v18359BlockedReason='not-finished';
function v18359HasWorld(s=state){
 return !!s&&s.userEmployed===false&&!s.v640National?.userTeam&&
  !!s.players&&Array.isArray(s.teams)&&Array.isArray(s.schedule)&&
  !s.vacation?.active&&!v125VacIncoming;
}
function v18359TrustedCompleted(s=state){
 const x=v18359FinishedWorld;
 if(!x||!v18359HasWorld(s))return false;
 if(x.world!==s||x.year!==Number(s.year)||x.day!==Number(s.day)||
    x.careerId!==String(s.v1903CareerId||''))return false;
 if(v53Sim?.active||v53Sim?.starting||v53Sim?.finished||v125VacIncoming||
   (typeof v18326AdvanceBusy!=='undefined'&&v18326AdvanceBusy)||
   (typeof v18121NewSeasonPreparation!=='undefined'&&v18121NewSeasonPreparation))return false;
 return true;
}
function v18359RefreshButtons(root=document){
 if(!root||!state||state.userEmployed!==false)return;
 const allow=v18359TrustedCompleted()||!!v89JobWait?.active;
 if(!allow)return;
 for(const btn of root.querySelectorAll?.('[data-action="v89-job-wait"]')||[]){
  btn.disabled=false;
  btn.removeAttribute('disabled');
  btn.removeAttribute('aria-busy');
  btn.title=v89JobWait?.active?'Parar avanço automático':'Avançar até o fim da temporada ou próxima proposta';
 }
 const normal=root.querySelector?.('.v555-advance-wrap [data-action="advance"]');
 if(normal&&v18359TrustedCompleted()){
  normal.disabled=false;normal.removeAttribute('disabled');normal.removeAttribute('aria-busy');
 }
}
function v18359OnWorkerFinished(m,wasVacation){
 if(!wasVacation||m?.error||!state||!v18112Dismissal.pending||
    state.userEmployed!==false||state.v640National?.userTeam)return false;
 // The full world transfer must have finished and every Worker operation
 // be closed. Never enable against a partial player/history stream.
 if(v53Sim?.active||v53Sim?.starting||v53Sim?.finished||v125VacIncoming||
    !state.players||!Array.isArray(state.teams)||!Array.isArray(state.schedule)){
  v18359BlockedReason='world-or-worker-not-finished';
  return false;
 }
 const careerId=String(state.v1903CareerId||'');
 if(v18112Dismissal.careerId&&careerId!==String(v18112Dismissal.careerId)){
  v18359BlockedReason='wrong-career';return false;
 }
 const s=state;
 const x={world:s,year:Number(s.year),day:Number(s.day),careerId,session:v53Sim.session};
 v18359FinishedWorld=x;v18359FinishCount++;
 if(s.vacation){
  s.vacation.active=false;s.vacation.paused=true;
  s.vacation.remaining=0;s.vacation.untilSeason=false;
 }
 if(typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)
  try{v18119CompleteSeasonTransfer();}catch(e){console.warn('[18.359] season overlay:',e);}
 // This is an actual, successful Worker completion. Ignore only stale
 // indicators, not a running Worker. Never start a second full-world save.
 v53Sim.syncing=false;v53Sim.patching=false;v53Sim.pause=false;v53Sim.pauseMode='';
 v18112Dismissal.pending=false;v18112Dismissal.ready=true;
 if(typeof v18357AwaitingPromotion!=='undefined')v18357AwaitingPromotion=false;
 if(typeof v18358RecoveryDone!=='undefined')v18358RecoveryDone=true;
 // The 17.1 checkpoint promotion may still be finishing; do not load the
 // previous stored career into the first unemployed-day Worker.
 if(typeof v18357LiveFallback!=='undefined')
  v18357LiveFallback={year:x.year,day:x.day,careerId:x.careerId};
 v18359BlockedReason='none';v18359ReleaseCount++;
 view='career';
 queueMicrotask(()=>{
  if(!v18359TrustedCompleted())return;
  try{closeModal();render();v18359RefreshButtons(document);}
  catch(e){console.warn('[18.359] repaint after dismissal:',e);}
  if(!v18112Dismissal.notified){
   v18112Dismissal.notified=true;
   toast('Contrato encerrado. Busca de propostas disponível.','warn');
  }
 });
 return true;
}
const v18359BaseChrome=v555UpdateChrome;
v555UpdateChrome=function(root){
 const result=v18359BaseChrome(root);
 v18359RefreshButtons(root||document);
 return result;
};
const v18359BaseStart=v53StartSimulation;
v53StartSimulation=async function(mode,...args){
 if(mode==='vacation'){
  v18359FinishedWorld=null;v18359BlockedReason='vacation-running';
  const p=v18359BaseStart(mode,...args);
  v18359VacationPromise=p;
  try{return await p;}
  finally{if(v18359VacationPromise===p)v18359VacationPromise=null;}
 }
 if((mode==='day'||mode==='dayfast')&&v18359TrustedCompleted()){
  const promotion=v18359VacationPromise;
  if(promotion){
   let timer;
   try{
    await Promise.race([
     promotion,
     new Promise((_,reject)=>{timer=setTimeout(()=>reject(
      Error('A confirmação do checkpoint ainda está em andamento. Tente novamente; nenhuma jornada foi perdida.')),12000);})
    ]);
   }finally{clearTimeout(timer);}
  }
  // No replay of a previous-season disk snapshot, even if its async save
  // update lags behind the real, already returned vacation world.
  args[0]={...(args[0]||{}),liveStateNoPreSave:true};
 }
 return v18359BaseStart(mode,...args);
};
window.GestorFC.dismissalFinished18359={
 version:'18.359',source:'real-vacation-worker-finished-event',
 status:()=>({
  signal:!!v18359FinishedWorld,releases:v18359ReleaseCount,finishes:v18359FinishCount,
  canAdvance:v18359TrustedCompleted(),blockedReason:v18359BlockedReason,
  dismissalPending:!!v18112Dismissal.pending,
  workerActive:!!v53Sim?.active,workerFinishedPending:!!v53Sim?.finished,
  streamPending:!!v125VacIncoming,year:state?.year,day:state?.day,
  careerIdMatch:!v18112Dismissal.careerId||
   String(v18112Dismissal.careerId)===String(state?.v1903CareerId||'')
 }),
 refresh:()=>v18359RefreshButtons(document)
};
"""

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_dismissal_control_18359.py <project>')
    root=Path(sys.argv[1]);path=root/'src/index.html'
    src=path.read_text(encoding='utf-8')
    if MARK in src:raise RuntimeError('18.359 installed twice')
    for required in ('FUTBR_DISMISSAL_BUTTON_RECOVERY_18358',
                     'FUTBR_DISMISSAL_HANDOFF_18357',
                     'FUTBR_JOBWAIT_SEASON_RECOVERY_18356',
                     "if(m.kind==='finished'){",
                     'const v18112Dismissal={pending:false'):
        if required not in src:raise RuntimeError('18.359 missing baseline '+required)
    # This is the *last authoritative patch queue* (18.119), not the
    # superseded handler earlier in the 16.x/17.x script.
    i=src.index('function v18119CompleteSeasonTransfer(){')
    start=src.index("if(m.kind==='finished'){",i)
    stop=src.index('    continue;',start)+len('    continue;')
    block=src[start:stop]
    old="else if(state)finish?.resolve(state);else finish?.reject(Error('A simulação terminou sem sincronizar a carreira.'));"
    if block.count(old)!=1:
        raise RuntimeError('18.359 actual 18.119 Worker success anchor changed')
    block=block.replace(old,old+"""
    // 18.359: signal from the actual finished Worker event, after the
    // complete player/history transfer, independent of stale UI flags.
    if(wasVacation&&!m.error)v18359OnWorkerFinished(m,wasVacation);""",1)
    src=src[:start]+block+src[stop:]
    # Actual click-handler previously checked stale v18112/v53Sim flags.
    start=src.index('async function v89RunJobWait(){')
    stop=src.index('const v89BaseCareerPage=careerPage;',start)
    job=src[start:stop]
    original="if(v18112Dismissal.pending||v53Sim?.active||v53Sim?.starting||v53Sim?.patching||v53Sim?.syncing){"
    job=once(job,original,
      "if(!v18359TrustedCompleted()&&(v18112Dismissal.pending||v53Sim?.active||v53Sim?.starting||v53Sim?.patching||v53Sim?.syncing)){",
      'job-wait click must trust successful completed Worker, not stale flags')
    src=src[:start]+job+src[stop:]
    # All previous scripts wrap chrome and simulation again after 18.112.
    # Install this at the *end* of the page, so no later painter can disable
    # the released button or alter the vacation Promise tracked here.
    if src.count('</body>')!=1:
        raise RuntimeError('18.359 expected one closing body element')
    src=src.replace('</body>',
      '<script id="futbr-dismissal-finished-18359">\n'+HELPER+
      '\n</script>\n</body>',1)
    src=once(src,"const EDITION='18.358.0';","const EDITION='18.359.0';",'visible version')
    src=once(src,"window.GestorFC.version='18.358.0';window.GestorFC.visualVersion='18.358.0';",
             "window.GestorFC.version='18.359.0';window.GestorFC.visualVersion='18.359.0';",
             'runtime version')
    path.write_text(src,encoding='utf-8')
    report={'ok':True,'version':'18.359.0','realWorkerFinishedEventRequired':True,
        'sameSessionCompleteWorldRequired':True,'staleDismissalFlagsBypassed':True,
        'actualJobClickGuardPatched':True,'actualHeaderButtonPatched':True,
        'firstUnemployedDayAlwaysUsesLiveWorld':True,
        'oldSaveProtectedUntilCheckpointPromotionFinishes':True,
        'noExtraFullWorldSave':True,'preservesHistoricalState':True}
    (root/'dismissal-control-18359-install.json').write_text(
       json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
