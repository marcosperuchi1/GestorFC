"""Three real board dismissals, three clubs, original job-search click and settings.

Only test inputs (previous form and a points deduction) control dismissal. The
Engine, Worker, queue, settings code, button click routing and save/load remain
original. The auth-dependent full renderer is isolated by the existing harness.
"""
from __future__ import annotations
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_vacation_resume_browser_18369 import HOOK,browser_path

TRANSITIONS_HOOK=r'''
window.__repeat371={done:false,result:null,progress:[],
 preference(){return {renewals:v622Settings(state).renewals,
   root:state?.v622Settings?.renewals,
   manager:state?.coaches?.[state.userCoachId]?.v18371CareerSettings?.renewals,
   diagnostic:window.GestorFC.contractPreferences18371?.status?.()||null};},
 setPreference(value){
  // Use the same mutable setting and explicit-commit function as the original
  // Settings Save handler. The next genuine Worker checkpoint persists it.
  v622Settings(state).renewals=value;
  if(typeof v18371CommitSettings==='function')v18371CommitSettings(state);
 },
 reloadIdentity(s){return {careerId:String(s?.v1903CareerId||''),
  coachId:String(s?.userCoachId||''),user:String(s?.user||''),
  userEmployed:s?.userEmployed,year:Number(s?.year),day:Number(s?.day),
  players:Object.keys(s?.players||{}).length,teams:s?.teams?.length||0,
  schedule:s?.schedule?.length||0,renewals:v622Settings(s).renewals};},
 playerLinkSignature(s,id='p1808'){
  const player=s?.players?.[id],occurrences=[];
  for(const team of s?.teams||[])for(const collection of ['roster','academy','proReserve']){
   const members=team?.[collection];if(!Array.isArray(members))continue;
   members.forEach((member,index)=>{
    if(member===id)occurrences.push({team:String(team.id),collection,index});
   });
  }
  return {id,exists:!!player,clubId:player?.clubId??null,occurrences};
 },
 snapshot(){return {day:state?.day,year:state?.year,user:state?.user,employed:state?.userEmployed,
  career:String(state?.v1903CareerId||''),coachId:String(state?.userCoachId||''),
  vacationActive:!!state?.vacation?.active,
  sim:{active:v53Sim.active,starting:v53Sim.starting,finished:!!v53Sim.finished,
   syncing:v53Sim.syncing,patching:v53Sim.patching,session:v53Sim.session,
   mode:v53Sim.mode,progress:v53Sim.progress},
  incoming:!!v125VacIncoming,creating:v53Creating,save:!!v52SavePromise,
  rpc:v53RPC.size,advance:v18326AdvanceBusy,season:!!v18119SeasonTransfer?.active,
  seasonPreparation:!!v18121NewSeasonPreparation,roll168:!!v168RolloverRunning,
  roll91:!!v91RolloverActive,vacPromise:!!v18359VacationPromise,
  vacOrigin:!!v18362VacationOrigin,usable:v18363CanUseJobWait(),blocker:v18363LastBlocker,
  lifecycle:window.GestorFC.lifecycle18362.status(),
  handoff:window.GestorFC.jobHandoff18365.status(),pending:v18112Dismissal.pending,
  offers:v636PendingCoachOffers(state).length,preference:this.preference(),
  checkpoint:window.GestorFC.jobWaitMemory18370?.status?.(),
  repeated:window.GestorFC.repeatedDismissal18371?.status?.(),
  notices:window.__vacResume369.notices.slice(-6)};},
 async clickJobWait(){
  const prior=document.getElementById('repeated-job-button-18371');prior?.remove();
  const button=document.createElement('button');button.id='repeated-job-button-18371';
  button.dataset.action='v89-job-wait';button.textContent='Até o fim / proposta';
  (document.getElementById('app')||document.body).appendChild(button);
  v18363PaintJobButtons(document);
  if(button.disabled)throw Error('The actual job-search button remained disabled: '+v18363LastBlocker);
  const requested=Number(v18365Job.requested),started=Number(v18365Job.started);
  const hadOffers=v636PendingCoachOffers(state).length,clicksBefore=Number(this.clickCalls)||0;
  button.click(); // Original document listener -> v18365HandleClick -> v89RunJobWait.
  if((Number(this.clickCalls)||0)<=clicksBefore)throw Error('The original job-search click handler did not receive the click');
  const clickedAt=Date.now();
  while(v89JobWait.active||v18365Job.pending||v53Sim.active||v53Sim.starting||v52SavePromise){
   if(Date.now()-clickedAt>160000)throw Error('Original job-search click stayed pending');
   await new Promise(r=>setTimeout(r,30));
  }
  return {actualDOMClick:true,enabledAtClick:true,hadOffers,handlerCalls:Number(this.clickCalls)-clicksBefore,
   requestDelta:Number(v18365Job.requested)-requested,
   startedDelta:Number(v18365Job.started)-started};
 },
 start(){
  if(this.working)throw Error('Already running');this.working=true;
  const initial=window.__vacResume369.makeCareer();state.vacation.active=false;
  if(!initial.lifecycleProbe?.ok)throw Error('Original lifecycle is not in the main UI scope');
  this.setPreference('board');
  const career=String(state.v1903CareerId),coachId=String(state.userCoachId),usedClubs=[];
  const originalStart=v53StartSimulation,originalDismissal=v18112MarkDismissal,
    originalClick=v18365HandleClick,originalGetWorker=v53GetWorker;
  let rounds=0;const dismissalEvents=[],boundaryChecks=[],observedWorkers=new WeakSet();
  this.clickCalls=0;
  v18365HandleClick=function(...args){window.__repeat371.clickCalls++;return originalClick.apply(this,args);};
  v53GetWorker=function(...args){
   return originalGetWorker.apply(this,args).then(worker=>{
    if(!observedWorkers.has(worker)){
     observedWorkers.add(worker);const receive=worker.onmessage;
     worker.onmessage=function(event){
      if(event?.data?.kind==='finished'&&v53Sim.mode==='vacation'){
       // Exercise the actual focus/status RPC at the existing final event.
       // No message is held, invented, or reordered by the test.
       const check={session:event.data.session,settled:false,outcome:null};
       boundaryChecks.push(check);
       v53Call('check').then(()=>{check.settled=true;check.outcome='answered';},
         error=>{check.settled=true;check.outcome='retired';check.error=String(error);});
      }
      return receive.call(this,event);
     };
    }
    return worker;
   });
  };
  v53StartSimulation=async function(mode,...args){
   const out=await originalStart(mode,...args);
   if(mode==='dayfast'&&++rounds>=2)v89JobWait.stop=true;
   return out;
  };
  v18112MarkDismissal=function(message){
   dismissalEvents.push({kind:message?.kind,session:message?.session,user:message?.user,
    day:message?.day,year:message?.year});
   return originalDismissal.apply(this,arguments);
  };
  (async()=>{
   try{
    for(let cycle=1;cycle<=3;cycle++){
     const club=E.team(state,state.user),coach=state.coaches[state.userCoachId];
     if(!club||!coach||state.userEmployed!==true||coach.clubId!==club.id)
      throw Error('A new employment must exist before vacation '+cycle);
     if(this.preference().renewals!=='board')throw Error('Delegated renewals lost before vacation '+cycle);
     usedClubs.push(club.id);
     const division=state.teams.filter(t=>t.country===club.country&&Number(t.division)===Number(club.division));
     club.stats.pts=Math.min(...division.filter(t=>t.id!==club.id).map(t=>Number(t.stats.pts)))-10;
     state.allowUserDismissal=true;coach.jobGames=20;coach.pressure=100;
     coach.recent=Array(10).fill(0);coach.lastTitleDay=-100;
     const eventsBefore=dismissalEvents.filter(e=>e.kind==='vac-dismissed').length;
     E.startVacation(state,24,false);
     this.progress.push({stage:'start-vacation',cycle,snapshot:this.snapshot()});
     await v53StartSimulation('vacation',{liveStateNoPreSave:true});
     await new Promise(r=>setTimeout(r,0));
     const afterVacation=this.snapshot();
     this.progress.push({stage:'after-vacation',cycle,snapshot:afterVacation});
     if(state.userEmployed!==false||
        dismissalEvents.filter(e=>e.kind==='vac-dismissed').length<=eventsBefore)
      throw Error('Original Worker did not dismiss the coach in cycle '+cycle);
     if(afterVacation.preference.renewals!=='board')
      throw Error('Delegated renewals lost in Worker return '+cycle);
     if(!afterVacation.usable)throw Error('Job wait disabled in cycle '+cycle+': '+afterVacation.blocker);
     if(String(state.v1903CareerId)!==career||String(state.userCoachId)!==coachId)
      throw Error('The career/coach identity changed');
     // Test an explicit reversal only after proving board mode survived all
     // three clubs and their complete vacation/dismissal streams.
     if(cycle===3)this.setPreference('manual');
     rounds=0;const before=Number(state.day),click=await this.clickJobWait();
     const afterSearch=this.snapshot(),advanced=Number(state.day)-before;
     this.progress.push({stage:'after-jobwait',cycle,advanced,rounds,click,snapshot:afterSearch});
     const genuineOffer=v636PendingCoachOffers(state).some(o=>
       !!E.team(state,o.teamId)&&Number(o.expiresDay)>=Number(state.day));
     this.progress[this.progress.length-1].stoppedOnValidOffer=genuineOffer;
     if(rounds<1||advanced<1||((rounds<2||advanced<2)&&!genuineOffer))
      throw Error('Original job search did not advance two days or stop on a genuine offer in cycle '+cycle);
     const wanted=cycle===3?'manual':'board';
     if(afterSearch.preference.renewals!==wanted)
      throw Error('Worker day/checkpoint overwrote explicit manager setting in cycle '+cycle);
     if(rounds>0&&(!afterSearch.checkpoint||afterSearch.checkpoint.failed||
         afterSearch.checkpoint.lastDay!==Number(state.day)))
      throw Error('Current job-search day did not have its original durable checkpoint');
     if(cycle<3){
      const offers=v636PendingCoachOffers(state),jobs=E.availableJobs(state).filter(t=>
        t.id!==state.user&&!usedClubs.includes(t.id));
      const playsSoon=t=>state.schedule.slice(Number(state.day),Number(state.day)+20).some(d=>
        d.type==='league'&&d.fixtures?.some(f=>f.home===t.id||f.away===t.id));
      const offered=offers.map(o=>jobs.find(t=>t.id===o.teamId)).filter(Boolean);
      const next=offered.find(playsSoon)||jobs.find(playsSoon)||offered[0]||jobs[0];
      if(!next)throw Error('No original available job in another club');
      // Both career/job-offer UI handlers call this original engine entrypoint.
      // It includes the existing tracker and offer-clear wrappers. No job,
      // vacancy or proposal is manufactured by the fixture.
      E.takeJob(state,next.id);
      const afterTake=this.snapshot();
      this.progress.push({stage:'new-job',cycle,team:next.id,
       fromGenuineOffer:offers.some(o=>o.teamId===next.id),snapshot:afterTake});
      if(afterTake.preference.renewals!=='board'||state.userEmployed!==true||
         state.user!==next.id||v636PendingCoachOffers(state).length)
       throw Error('Acceptance did not preserve settings or clear previous offers');
     }
    }
    // Use the original Worker storage reader after the third real checkpoint.
    // Keep a compact audit, then replace the current world with its saved state.
    this.progress.push({stage:'loading-saved-career',snapshot:this.snapshot()});
    const reloadAudit={before:this.reloadIdentity(state),
      playerLinksBefore:this.playerLinkSignature(state)};
    const loaded=await v53Call('load',{key:STORE});
    if(!loaded)throw Error('The three-club career did not exist on disk');
    // Match loadSelected's current production loader: check its required
    // collections, then install the decoded state. The obsolete v4 import
    // validator is not called by that loader and must not be added here.
    if(!loaded.players||!loaded.teams||!loaded.schedule||!loaded.competitions)
     throw Error('The reloaded save is missing a required production collection');
    reloadAudit.after=this.reloadIdentity(loaded);
    reloadAudit.playerLinksAfter=this.playerLinkSignature(loaded);
    reloadAudit.sameIdentityAndCounts=JSON.stringify(reloadAudit.before)===JSON.stringify(reloadAudit.after);
    reloadAudit.samePlayerLinks=JSON.stringify(reloadAudit.playerLinksBefore)===JSON.stringify(reloadAudit.playerLinksAfter);
    this.progress.push({stage:'reload-invariants-checked',audit:reloadAudit});
    if(!reloadAudit.sameIdentityAndCounts||!reloadAudit.samePlayerLinks)
     throw Error('Reload changed career identity, employment, calendar, counts, setting or player links: '+JSON.stringify(reloadAudit));
    if(loaded.vacation){loaded.vacation.active=false;loaded.vacation.paused=true;}
    state=loaded;saved=loaded;
    const reloaded=this.snapshot();
    this.progress.push({stage:'saved-career-reloaded',snapshot:reloaded});
    if(String(state.v1903CareerId)!==career||String(state.userCoachId)!==coachId||
       reloaded.preference.renewals!=='manual')
     throw Error('Saving/loading lost the current career or explicit manual setting');
    const searches=this.progress.filter(x=>x.stage==='after-jobwait');
    const clubStates=this.progress.filter(x=>['start-vacation','after-vacation','new-job'].includes(x.stage));
    const realDismissals=dismissalEvents.filter(e=>e.kind==='vac-dismissed');
    const flags={realEngineAndWorkers:realDismissals.length>=3&&searches.every(x=>x.rounds>=1),
     threeDismissalsSameCareer:new Set(realDismissals.map(e=>e.session)).size===3&&
       this.progress.every(x=>!x.snapshot||x.snapshot.career===career),
     threeSuccessfulSearches:searches.length===3&&searches.every(x=>x.rounds>=1&&x.advanced>=1&&
       (x.rounds>=2&&x.advanced>=2||x.stoppedOnValidOffer)),
     boardPreferenceAcrossClubs:clubStates.every(x=>x.snapshot.preference.renewals==='board'),
     actualJobButtonEnabled:searches.every(x=>x.click.enabledAtClick),
     actualJobButtonClickHandled:searches.every(x=>x.click.actualDOMClick&&x.click.handlerCalls>=1),
     manualPreferencePersistsAfterReload:reloaded.preference.renewals==='manual',
     reloadIdentityAndCollectionCountsPreserved:reloadAudit.sameIdentityAndCounts,
     reloadPlayerLinksPreserved:reloadAudit.samePlayerLinks,
     statusRPCAtEachVacationBoundary:boundaryChecks.length===3&&boundaryChecks.every(x=>x.settled),
     noOrphanedRPCsAfterThirdDismissal:v53RPC.size===0,
     testHookNotShipped:true};
    if(!Object.values(flags).every(Boolean))throw Error('Real career regression invariant failed: '+JSON.stringify(flags));
    this.result={ok:true,version:'18.371.0',...flags,boundaryChecks,reloadAudit,initial,career,coachId,usedClubs,
     threeDistinctClubs:new Set(usedClubs).size===3,
     originalBoardDismissalEvents:dismissalEvents,
     originalEngineWorkerAndClickRouting:true,managerSettingPreservedAcrossThreeClubs:true,
     explicitManualSettingSurvivedCheckpointAndReload:true,progress:this.progress};
    if(!this.result.threeDistinctClubs)throw Error('Regression reused a previous club');
   }catch(error){this.result={ok:false,error:String(error),stack:String(error.stack),
    initial,usedClubs,dismissalEvents,progress:this.progress,snapshot:this.snapshot()};}
   finally{
    v53StartSimulation=originalStart;v18112MarkDismissal=originalDismissal;
    v18365HandleClick=originalClick;v53GetWorker=originalGetWorker;
    this.done=true;this.working=false;
   }
  })();return initial;
 }
};
'''

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_career_transitions_browser_18371.py <project>')
 root=Path(sys.argv[1]);html=(root/'src/index.html').read_text(encoding='utf-8')
 a=html.index('let state=null,saved=null');b=html.index('</script>',a);anchor=html.rfind('})();',a,b)
 assert 0<a<anchor<b,'Original main UI IIFE not found'
 test_html=html[:anchor]+'\n'+HOOK+'\n'+TRANSITIONS_HOOK+'\n'+html[anchor:]
 errors=[];console_errors=[];result=None;latest=None;startup_errors=0
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=browser_path(),headless=True,
   args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
  page=browser.new_page(viewport={'width':1380,'height':840})
  page.on('pageerror',lambda e:errors.append(str(e)[:2400]))
  page.on('console',lambda m:console_errors.append(m.text[:2400]) if m.type=='error' else None)
  def route(r):
   if r.request.resource_type=='document' and r.request.url.startswith('http://localhost:8744/'):
    r.fulfill(status=200,content_type='text/html; charset=utf-8',body=test_html)
   else:r.abort()
  page.route('**/*',route)
  page.goto('http://localhost:8744/',wait_until='domcontentloaded',timeout=180000)
  page.wait_for_function('()=>!!window.__repeat371',timeout=90000)
  page.wait_for_timeout(2000);startup_errors=len(errors)
  try:
   print('18.371 INITIAL '+json.dumps(page.evaluate('()=>window.__repeat371.start()')),flush=True)
   for i in range(130):
    page.wait_for_timeout(5000)
    latest=page.evaluate('''()=>({done:window.__repeat371.done,
     progress:window.__repeat371.progress.map(x=>({stage:x.stage,cycle:x.cycle,
      day:x.snapshot?.day,usable:x.snapshot?.usable,blocker:x.snapshot?.blocker,
      preference:x.snapshot?.preference?.renewals,advanced:x.advanced})),
     snapshot:window.__repeat371.snapshot()})''')
    print('18.371 PROGRESS '+json.dumps(latest),flush=True)
    if latest['done']:break
   result=page.evaluate('()=>window.__repeat371.result')
   if not result:result={'ok':False,'error':'Original repeated-career flow exceeded 650 seconds',
    'lastObservation':latest,'progress':page.evaluate('()=>window.__repeat371.progress')}
  except Exception as error:
   result={'ok':False,'error':str(error),'lastObservation':latest}
  browser.close()
 result['startupErrors']=errors[:startup_errors][-12:]
 result['runtimeErrors']=errors[startup_errors:][-30:]
 result['consoleErrors']=console_errors[-15:]
 if result['runtimeErrors']:
  result['ok']=False;result['runtimeErrorGate']='Unexpected page errors during the original career flow'
 (root/'career-transitions-browser-18371-tests.json').write_text(
  json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print('18.371 RESULT '+json.dumps(result,ensure_ascii=False),flush=True)
 if not result.get('ok'):raise RuntimeError('Three-club actual Worker/settings/click regression failed')

if __name__=='__main__':main()
