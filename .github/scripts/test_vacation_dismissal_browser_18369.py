"""Complementary real-Worker regression: board dismissal during a vacation.

The controlled input is poor prior coach form plus a four-point starting penalty.
No dismissal function, Worker message, match engine, save, or safety gate is mocked.
Run only in the CI browser environment, alongside the employed-return regression.
"""
from __future__ import annotations
import json,re,sys
from pathlib import Path
from playwright.sync_api import sync_playwright,TimeoutError as PwTimeout
from test_vacation_resume_browser_18369 import HOOK as EMPLOYED_HOOK,browser_path

DISMISSAL_HOOK=r"""
/* TEST ONLY: input fixture for original board decision inside vacation Worker. */
window.__vacDismiss369={working:false,result:null,progress:null,
 prepare(){
  const initial=window.__vacResume369.makeCareer();
  if(!initial.lifecycleProbe?.ok)throw Error('Scoped lifecycle probe failed: '+JSON.stringify(initial.lifecycleProbe));
  const club=E.team(state,state.user),coach=state.coaches?.[state.userCoachId];
  if(!club||!coach||coach.clubId!==club.id||club.coachId!==coach.id)
    throw Error('Original career does not have its employed coach');
  const division=state.teams.filter(t=>t.country===club.country&&Number(t.division)===Number(club.division));
  const leagueDays=state.schedule.map((stage,index)=>({stage,index})).filter(x=>
    x.stage.type==='league'&&x.stage.fixtures?.some(f=>f.home===club.id||f.away===club.id));
  const firstLeague=leagueDays.find(x=>x.index>=Number(state.day));
  if(!firstLeague||firstLeague.index-Number(state.day)>=24)
    throw Error('No original league round within the bounded vacation scenario');
  // Keep the original calendar and every fixture. A controlled starting
  // points deduction guarantees last place even after a win; poor prior-job
  // form provides the original Engine's severe-crisis inputs. No current
  // match result or dismissal is manufactured, and no calendar day is skipped.
  const lowestOtherPoints=Math.min(...division.filter(t=>t.id!==club.id).map(t=>Number(t.stats.pts)));
  const pointsBefore=Number(club.stats.pts);
  club.stats.pts=lowestOtherPoints-4;
  const startingPointsPenalty=pointsBefore-club.stats.pts;
  state.allowUserDismissal=true;
  coach.jobGames=10;coach.pressure=100;coach.recent=Array(10).fill(0);
  coach.lastTitleDay=-100;
  const rows=E.table(state,club.country,club.division),position=rows.findIndex(t=>t.id===club.id)+1;
  // Even a win in the upcoming original simulation must leave this club last.
  const nearestPoints=Math.min(...rows.filter(t=>t.id!==club.id).map(t=>Number(t.stats.pts)));
  if(position!==rows.length||nearestPoints<=club.stats.pts+3)
    throw Error('Crisis is not robust to the next genuine match result');
  E.startVacation(state,24,false);
  if(state.userEmployed!==true||Number(state.day)!==initial.day)
    throw Error('Fixture must enter the Worker employed without skipping the calendar');
  this.setup={...initial,day:state.day,year:state.year,employedBeforeWorker:true,
    crisis:{country:club.country,division:club.division,club:club.id,coach:coach.id,
      day:state.day,firstLeagueDay:firstLeague.index,firstLeagueRound:firstLeague.stage.round,
      position,total:rows.length,pointsBefore,points:club.stats.pts,startingPointsPenalty,nearestPoints,
      inputKind:'controlled-starting-points-penalty-and-prior-coach-form',
      calendarUnchanged:true,fixturesUnchanged:true,
      coachGames:coach.jobGames,pressure:coach.pressure,recent:coach.recent.slice(),
      lastTitleDay:coach.lastTitleDay},
    fixtureOnly:true,originalBoardDecisionRequired:true};
  return this.setup;
 },
 start(){
  if(this.working)throw Error('Dismissal regression is already running');
  this.working=true;this.result=null;window.__vacResume369.working=true;
  const reports={ok:false,startDay:Number(state.day),career:String(state.v1903CareerId),
    coachId:state.userCoachId,clubId:state.user,stages:[],dismissalEvents:[],lifecycleCallbacks:[],
    employmentTransition:{beforeWorker:state.userEmployed,afterWorker:null},
    jobRounds:0,notices:window.__vacResume369.notices};
  this.progress=reports;
  const originalStart=v53StartSimulation,originalDismissal=v18112MarkDismissal,
    originalFinished=v18359OnWorkerFinished;
  // Observation delegates every call unchanged. No synthetic messages or state
  // changes are used to produce or complete the dismissal.
  v18112MarkDismissal=function(message){
   reports.dismissalEvents.push({kind:message?.kind,year:message?.year,day:message?.day,
     session:message?.session,careerId:message?.careerId});
   return originalDismissal.apply(this,arguments);
  };
  v18359OnWorkerFinished=function(message,wasVacation){
   const call={wasVacation:!!wasVacation,employed:state?.userEmployed,
     session:message?.session,liveSession:v53Sim.session,day:state?.day};
   reports.lifecycleCallbacks.push(call);
   try{call.result=originalFinished.apply(this,arguments);return call.result;}
   catch(error){call.error=String(error);call.stack=String(error?.stack||'').slice(0,5000);throw error;}
  };
  v53StartSimulation=async function(mode,...args){
   const result=await originalStart(mode,...args);
   if(mode==='dayfast'&&++reports.jobRounds>=2)v89JobWait.stop=true;
   return result;
  };
  (async()=>{
   try{
    await v53StartSimulation('vacation',{liveStateNoPreSave:true});
    reports.stages.push('original-dismissal-vacation-promise-settled');
    reports.employmentTransition.afterWorker=state?.userEmployed;
    reports.afterVacation={year:state?.year,day:state?.day,employed:state?.userEmployed,
      coachClub:state?.coaches?.[reports.coachId]?.clubId,
      replacementCoach:E.team(state,reports.clubId)?.coachId,
      active:!!state?.vacation?.active,workerActive:!!v53Sim.active,
      syncing:!!v53Sim.syncing,patching:!!v53Sim.patching,
      career:String(state?.v1903CareerId),teams:state?.teams?.length,
      players:Object.keys(state?.players||{}).length,
      marker:window.GestorFC.vacationResume18369.status(),
      lifecycle:window.GestorFC.lifecycle18362.status(),
      finished:window.GestorFC.dismissalFinished18359.status(),
      dismissal:{pending:v18112Dismissal.pending,ready:v18112Dismissal.ready,
        awaitingPromotion:v18357AwaitingPromotion}};
    const returned=reports.afterVacation;
    if(reports.employmentTransition.beforeWorker!==true||
       reports.employmentTransition.afterWorker!==false)
      throw Error('Original vacation did not transition an employed coach to unemployed');
    if(returned.marker.queueErrors)throw Error('Original delivery failed: '+returned.marker.lastQueueError);
    if(!reports.dismissalEvents.some(e=>e.kind==='vac-dismissed'))
      throw Error('Original vacation Worker did not emit vac-dismissed');
    if(reports.lifecycleCallbacks.length!==1||reports.lifecycleCallbacks[0].result!==true||
       reports.lifecycleCallbacks[0].employed!==false)
      throw Error('Original final handler did not register the dismissed authoritative world');
    if(returned.employed!==false||returned.active||returned.workerActive||returned.syncing||returned.patching||
       returned.career!==reports.career||returned.coachClub||
       !returned.replacementCoach||returned.replacementCoach===reports.coachId||
       returned.teams!==this.setup.teams||returned.players<180000||
       returned.dismissal.pending||!returned.dismissal.ready||returned.dismissal.awaitingPromotion||
       !returned.lifecycle.promoted||returned.lifecycle.settled<1||returned.lifecycle.released<1)
      throw Error('Original dismissal did not complete its full-world lifecycle');
    view='career';
    const before=Number(state.day);
    await v89RunJobWait();
    reports.stages.push('original-job-search-settled-after-dismissal');
    reports.afterJobSearch={before,after:Number(state?.day),year:Number(state?.year),
      confirmed:Number(v89JobWait.days)||0,active:!!v89JobWait.active,
      employed:state?.userEmployed,career:String(state?.v1903CareerId),
      workerActive:!!v53Sim.active,syncing:!!v53Sim.syncing,
      marker:window.GestorFC.vacationResume18369.status(),
      progress:window.GestorFC.unemployedWorker18368?.status?.()};
    const after=reports.afterJobSearch;
    reports.ok=reports.jobRounds>=2&&after.after>=before+2&&after.confirmed>=2&&
      after.employed===false&&after.career===reports.career&&!after.active&&
      !after.workerActive&&!after.syncing;
    if(!reports.ok)throw Error('Original unemployed job search did not advance two actual days after dismissal');
   }catch(error){reports.ok=false;reports.error=String(error);
    reports.stack=String(error?.stack||'').slice(0,5000);
    reports.inflight={day:state?.day,employed:state?.userEmployed,
      marker:window.GestorFC.vacationResume18369.status(),
      lifecycle:window.GestorFC.lifecycle18362.status()};}
   finally{
    v53StartSimulation=originalStart;v18112MarkDismissal=originalDismissal;
    v18359OnWorkerFinished=originalFinished;
    this.result=reports;this.working=false;window.__vacResume369.working=false;
   }
  })();
  return true;
 }
};
"""


def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_vacation_dismissal_browser_18369.py <project>')
 root=Path(sys.argv[1]);html=(root/'src/index.html').read_text(encoding='utf-8')
 a=html.index('let state=null,saved=null');b=html.index('</script>',a);anchor=html.rfind('})();',a,b)
 assert 0<a<anchor<b,'Original main UI IIFE not found'
 assert 'FUTBR_VACATION_RESUME_HANDOFF_18369' in html
 assert html[a:anchor].count('function v18359OnWorkerFinished(')==1
 assert not re.search(r'<script\b[^>]*\bid\s*=\s*[\"\']futbr-dismissal-finished-18359[\"\']',html)
 test_html=html[:anchor]+'\n'+EMPLOYED_HOOK+'\n'+DISMISSAL_HOOK+'\n'+html[anchor:]
 errors=[];console_errors=[];phase='startup';exe=browser_path();setup=None;result=None;snapshots=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=exe,headless=True,
    args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
  ctx=browser.new_context(viewport={'width':1380,'height':840});page=ctx.new_page()
  page.on('pageerror',lambda e:errors.append({'phase':phase,'message':str(e)[:1200],
    'stack':str(getattr(e,'stack',''))[:5000]}))
  page.on('console',lambda m:console_errors.append({'phase':phase,'message':m.text[:1800],
    'location':m.location}) if m.type=='error' else None)
  def route(r):
   if r.request.resource_type=='document' and r.request.url.startswith('http://localhost:8740/'):
    r.fulfill(status=200,content_type='text/html; charset=utf-8',body=test_html)
   else:r.abort()
  page.route('**/*',route)
  page.goto('http://localhost:8740/',wait_until='domcontentloaded',timeout=180000)
  page.wait_for_function('() => !!window.__vacDismiss369',timeout=90000)
  page.wait_for_timeout(2400)
  startup_error_count=len(errors)
  try:
   phase='crisis-input'
   setup=page.evaluate('() => window.__vacDismiss369.prepare()')
   print('18.369 REAL DISMISSAL SETUP '+json.dumps(setup,ensure_ascii=False),flush=True)
   phase='real-vacation-dismissal-and-job-search'
   page.evaluate('() => window.__vacDismiss369.start()')
   for cycle in range(10):
    try:
     page.wait_for_function('() => window.__vacDismiss369.result!==null',timeout=18000)
     result=page.evaluate('() => window.__vacDismiss369.result');break
    except PwTimeout:
     snap=page.evaluate('() => window.__vacResume369.snapshot()')
     snap['runtimeErrors']=errors[startup_error_count:][-8:];snapshots.append(snap)
     print('18.369 DISMISSAL PROGRESS '+json.dumps({'cycle':cycle+1,'snapshot':snap},ensure_ascii=False),flush=True)
   if result is None:
    partial=page.evaluate('() => window.__vacDismiss369.progress') or {}
    result={**partial,'ok':False,'error':'Original dismissal/job search remained pending after 180 seconds'}
  except Exception as error:
   result={'ok':False,'error':str(error),'phase':phase}
  ctx.close();browser.close()
 result['progressSnapshots']=snapshots
 report={'ok':bool(result.get('ok')),'version':'18.369.0','scenario':'vacation-board-dismissal',
  'originalEngineAndWorker':True,'testInputOnly':True,'testHookNotShipped':True,
  'realDismissalWorkerEvent':any(e.get('kind')=='vac-dismissed' for e in result.get('dismissalEvents',[])),
  'realEmployedToUnemployedTransition':result.get('employmentTransition',{}).get('beforeWorker') is True and
    result.get('employmentTransition',{}).get('afterWorker') is False,
  # "promoted" is the existing lifecycle field name. This asserts the outer
  # vacation lifecycle only; it is not proof of storage/checkpoint promotion.
  'originalLifecycleCompleted':bool(result.get('afterVacation',{}).get('lifecycle',{}).get('promoted')),
  'twoRealJobSearchDaysAfterDismissal':result.get('jobRounds',0)>=2 and bool(result.get('ok')),
  'setup':setup,'result':result,'browser':exe,
  'startupErrors':errors[:startup_error_count][-12:],'runtimeErrors':errors[startup_error_count:][-30:],
  'consoleErrors':console_errors[-20:]}
 (root/'vacation-dismissal-browser-18369-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('18.369 REAL DISMISSAL RESULT '+json.dumps(report,ensure_ascii=False),flush=True)
 if not all(report[key] for key in ('ok','realDismissalWorkerEvent','realEmployedToUnemployedTransition','originalLifecycleCompleted',
    'twoRealJobSearchDaysAfterDismissal')):
  raise RuntimeError('Original vacation dismissal -> unemployed job search failed')


if __name__=='__main__':main()
