from __future__ import annotations
import json,os,shutil,sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HOOK=r"""
/* TEST ONLY: real Engine/Worker vacation -> manual stop -> normal nextmatch. */
window.__vacResume369={
 working:false,result:null,progress:null,notices:[],
 async snapshot(){
   const snapshot={working:this.working,
     year:state?.year,day:state?.day,employed:state?.userEmployed,
     vacationActive:!!state?.vacation?.active,vacationPaused:!!state?.vacation?.paused,
     remaining:state?.vacation?.remaining,completed:state?.vacation?.completed,
     workerExists:!!v53Worker,workerReady:!!v53WorkerReady,
     sim:{mode:v53Sim?.mode,active:!!v53Sim?.active,starting:!!v53Sim?.starting,
       syncing:!!v53Sim?.syncing,patching:!!v53Sim?.patching,
       pause:!!v53Sim?.pause,pauseMode:v53Sim?.pauseMode,
       progress:v53Sim?.progress,done:v53Sim?.done,total:v53Sim?.total,
       finishedPending:!!v53Sim?.finished,session:v53Sim?.session},
     incoming:!!v125VacIncoming,
     queue:{scheduled:!!v53PatchScheduled,length:v53PatchQueue.length,
       firstKinds:v53PatchQueue.slice(0,5).map(x=>x.kind),
       lastKinds:v53PatchQueue.slice(-5).map(x=>x.kind)},
     saveActive:!!v52SavePromise,saveDirty:!!v52SaveDirty,
     career:window.GestorFC.vacationResume18369?.status?.(),
     stage:(state?.schedule?.[Number(state?.day)||0]||null)?.type||null,
     stageFixtures:state?.schedule?.[Number(state?.day)||0]?.fixtures?.length||0,
     notices:this.notices.slice(-6)};
   // The original Worker check RPC works while it simulates: determine
   // whether the day advanced internally, or the Engine is CPU-bound.
   try{
    snapshot.workerCheck=await Promise.race([
      v53Call('check'),
      new Promise((resolve)=>setTimeout(()=>resolve({timeout:true}),1800))
    ]);
   }catch(err){snapshot.workerCheck={error:String(err)}}
   return snapshot;
 },

 makeCareer(){
  // The actual 18.x game has ~185k players and over five thousand clubs.
  // Keep all sports/world logic real; only bypass the auth-dependent renderer.
  const s=E.createCareer({club:'t0',manager:'Vacation Handoff Integration',seed:183692026,
    difficulty:'normal'});
  render=()=>document.getElementById('app');
  this.notices=[];
  const baseToast=toast;toast=(...args)=>{this.notices.push(args.map(String).join(' '));
    try{return baseToast(...args);}catch(e){return undefined;}};
  state=s;saved=null;view='vacation';
  state.userEmployed=true;
  if(!state.v1903CareerId)state.v1903CareerId='real-vacation-18369';
  v636CoachState(state);
  // Use exactly the same Engine.startVacation setup as a player clicking Férias.
  // It initializes startDay, startBalance, assistant lineup, delegation, and limits.
  E.startVacation(state,24,false);
  state.live=null;
  v53Sim.active=false;v53Sim.starting=false;v53Sim.syncing=false;
  v53Sim.patching=false;v53Sim.finished=null;
  saveOK=true;v52SavePromise=null;v52SaveDirty=false;v52PendingState=null;
  return {career:String(state.v1903CareerId),year:state.year,day:state.day,
     user:state.user,teams:state.teams.length,players:Object.keys(state.players).length};
 },
 start(){
  if(this.working)throw Error('Running');
  this.working=true;this.result=null;
  // Never retain the 185k-player old world across vacation sync: the game deliberately releases it.
  const career=String(state.v1903CareerId),startDay=Number(state.day);
  const reports={startDay,career,stages:[],notices:this.notices,
    terminalPaintFaults:0,terminalPaintFaultPromiseSettled:false};
  this.progress=reports;
  // The active final drain settles its finished Promise before the tail
  // repaint. A throw in that repaint could still skip ACK/scheduler cleanup
  // and starve the next Worker session. Inject one harmless UI exception,
  // then require the next genuine command to complete through the same pump.
  // Engine, Worker messages, state transfer and ACKs stay original.
  const originalRefresh=v53RefreshView;
  v53RefreshView=function(...args){
   if(!reports.terminalPaintFaults&&v53Sim.mode==='vacation'&&
      !v53Sim.active&&!v53Sim.starting&&!v53Sim.finished&&state){
    reports.terminalPaintFaults++;
    reports.terminalPaintFaultState={mode:v53Sim.mode,active:v53Sim.active,
      starting:v53Sim.starting,finishedPending:!!v53Sim.finished,
      queueScheduled:v53PatchScheduled,queueLength:v53PatchQueue.length};
    throw Error('TEST_ONLY_18369_TERMINAL_PAINT_FAILURE');
   }
   return originalRefresh.apply(this,args);
  };
  (async()=>{
   let pauseTimer=null,stopSent=false,interval=null;
   try{
    const vacation=v53StartSimulation('vacation',{liveStateNoPreSave:true});
    interval=setInterval(()=>{
     if(stopSent||!v53Sim.active||v53Sim.mode!=='vacation'||!v53Worker)return;
     // The stop request must happen AFTER the first genuine Worker day:
     // sending it during startup can be reset by simulate()'s pause=null.
     const seenDay=Math.max(Number(v53Sim.day)||startDay,Number(state?.day)||startDay);
     if(seenDay<=startDay)return;
     // User presses "Encerrar férias" after a completed jornada. The original
     // Worker must receive END, stream the full world and settle.
     // Exercise the SAME function used by pointer/keyboard actions. Do not
     // manufacture the pause flags or the Worker command in the harness.
     stopSent=v723RequestVacationControl('end')===true;
    },1000);
    await vacation;
    reports.terminalPaintFaultPromiseSettled=reports.terminalPaintFaults===1;
    clearInterval(interval);interval=null;
    reports.stages.push('original-vacation-promise-settled');
    reports.afterVacation={year:state?.year,day:state?.day,stopped:stopSent,
      sameCareer:String(state?.v1903CareerId)===career,
      employed:state?.userEmployed===true,
      active:!!state?.vacation?.active,
      workerActive:!!v53Sim?.active,workerSyncing:!!v53Sim?.syncing,
      marker:window.GestorFC.vacationResume18369?.status?.(),
      teams:state?.teams?.length,
      players:Object.keys(state?.players||{}).length};
    if(!stopSent)throw Error('Vacation ended without the manual end command being accepted');
    if(!reports.terminalPaintFaultPromiseSettled)
      throw Error('Terminal repaint fault was not exercised during the completed vacation');
    if(!state||state.userEmployed!==true||state.vacation?.active||v53Sim.active||v53Sim.syncing||
       !state.players||!state.schedule?.length||
       !window.GestorFC.vacationResume18369?.status?.().ready)
      throw Error('Vacation did not return an authoritative complete world');
    // Match the normal screen the player uses after returning to the club.
    // The authenticated renderer remains isolated; Engine/Worker are original.
    view='dashboard';

    // Create one controlled non-match day after the real vacation. This avoids
    // a correctly disabled Next Match button if a human fixture is already
    // scheduled today. The simulation of all other clubs remains genuine.
    const before=Number(state.day);
    const cur=E.upcoming(state);
    const stage=state.schedule?.[before];
    if(cur&&stage&&Array.isArray(stage.fixtures)){
      stage.fixtures=stage.fixtures.filter(f=>f.home!==state.user&&f.away!==state.user);
      stage.prepared=true;
    }
    if(E.upcoming(state))throw Error('Could not prepare a no-match test day');
    reports.stages.push('idle-day-ready-after-vacation');
    await v1891AdvanceToNextMatch(); // Exactly the user-facing command.
    reports.stages.push('real-nextmatch-command-settled');
    reports.afterNext={before,after:Number(state.day),year:Number(state.year),
      mode:v53Sim.mode,nextSteps:v53Sim.nextMatchSteps,
      employed:state.userEmployed,careerId:String(state.v1903CareerId),
      marker:window.GestorFC.vacationResume18369?.status?.()};
    reports.ok=stopSent&&reports.terminalPaintFaultPromiseSettled&&reports.afterVacation.employed&&
      reports.afterVacation.sameCareer&&Number(state.day)>before&&state.userEmployed===true&&
      String(state.v1903CareerId)===career&&!v53Sim.active&&!v53Sim.syncing;
   }catch(e){reports.ok=false;reports.error=String(e);
     reports.stack=String(e?.stack||'').slice(0,2100);
     reports.inflight={mode:v53Sim?.mode,active:v53Sim?.active,starting:v53Sim?.starting,
       syncing:v53Sim?.syncing,worker:!!v53Worker,day:state?.day,
       vacation:state?.vacation?.active,marker:window.GestorFC.vacationResume18369?.status?.()};}
   finally{
    if(interval)clearInterval(interval);
    v53RefreshView=originalRefresh;
    this.result=reports;this.working=false;
   }
  })();
  return true;
 }
};
"""

def browser_path():
 for exe in ('chrome','chrome.exe','msedge','msedge.exe','chromium','chromium.exe'):
  found=shutil.which(exe)
  if found:return found
 for e in ('PROGRAMFILES','ProgramFiles','PROGRAMFILES(X86)','ProgramFiles(x86)'):
  if os.environ.get(e):
   for path in (Path(os.environ[e])/'Google/Chrome/Application/chrome.exe',
      Path(os.environ[e])/'Microsoft/Edge/Application/msedge.exe'):
    if path.exists():return str(path)
 for path in ('/usr/bin/chromium','/usr/bin/google-chrome'):
  if Path(path).exists():return str(path)
 raise RuntimeError('Cannot validate real Worker because Chrome/Edge is unavailable')

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_vacation_resume_browser_18369.py <project>')
 root=Path(sys.argv[1]);html=(root/'src/index.html').read_text(encoding='utf-8')
 assert 'FUTBR_VACATION_RESUME_HANDOFF_18369' in html
 a=html.index('let state=null,saved=null')
 b=html.index('</script>',a)
 anchor=html.rfind('})();',a,b)
 assert 0<a<anchor<b,'Real IIFE not found'
 test_html=html[:anchor]+'\n'+HOOK+'\n'+html[anchor:]
 errors=[];console_errors=[];phase='startup';exe=browser_path()
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=exe,headless=True,
   args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
  ctx=browser.new_context(viewport={'width':1380,'height':840})
  page=ctx.new_page()
  page.on('pageerror',lambda e:errors.append({
    'phase':phase,'message':str(e)[:1200],
    'stack':str(getattr(e,'stack',''))[:5000]}))
  page.on('console',lambda m:console_errors.append({
    'phase':phase,'message':m.text[:1800],'location':m.location})
    if m.type=='error' else None)
  def route(r):
   if r.request.resource_type=='document' and r.request.url.startswith('http://localhost:8739/'):
    r.fulfill(status=200,content_type='text/html; charset=utf-8',body=test_html)
   else:r.abort()
  page.route('**/*',route)
  page.goto('http://localhost:8739/',wait_until='domcontentloaded',timeout=180000)
  page.wait_for_function("() => !!window.__vacResume369",timeout=90000)
  page.wait_for_timeout(2400) # Allow the authless initial-shell tasks to settle.
  startup_error_count=len(errors)
  phase='career-setup'
  setup=page.evaluate("() => window.__vacResume369.makeCareer()")
  print('18.369 REAL VACATION TEST SETUP '+json.dumps(setup,ensure_ascii=False),flush=True)
  phase='vacation-and-resume'
  page.evaluate("() => window.__vacResume369.start()")
  from playwright.sync_api import TimeoutError as PwTimeout
  snapshots=[]
  result=None
  for cycle in range(8):
   try:
    page.wait_for_function("() => window.__vacResume369.result!==null",timeout=18000)
    result=page.evaluate("() => window.__vacResume369.result")
    break
   except PwTimeout:
    try:
     snap=page.evaluate("() => window.__vacResume369.snapshot()")
     snap['runtimeErrors']=errors[startup_error_count:][-8:]
     snapshots.append(snap)
     print('18.369 VACATION PROGRESS '+json.dumps({'cycle':cycle+1,'snapshot':snap},ensure_ascii=False),flush=True)
    except Exception as err:
     print('18.369 VACATION PAGE UNRESPONSIVE '+str(err),flush=True)
     break
  if result is None:
   partial=page.evaluate("() => window.__vacResume369.progress") or {}
   result={**partial,'ok':False,'error':'vacation-end or nextmatch remained pending after 144 seconds',
      'progressSnapshots':snapshots,
      'lastSnapshot':snapshots[-1] if snapshots else None}
  else:
   result['progressSnapshots']=snapshots
  ctx.close();browser.close()
 report={'ok':bool(result.get('ok')),'version':'18.369.0',
  'realOriginalEngine':True,'realVacationWorkerAndStream':bool(result.get('afterVacation')),
  'realNextMatchAfterManualVacationEnd':bool(result.get('afterNext')) and bool(result.get('ok')),
  'realWorkersNotMocked':True,'browser':exe,'setup':setup,'result':result,
  'originalManualEndCommandAccepted':bool(result.get('afterVacation',{}).get('stopped')),
  'terminalRepaintFailurePreservesOriginalPromise':bool(result.get('terminalPaintFaultPromiseSettled')),
  'startupErrors':errors[:startup_error_count][-12:],
  'runtimeErrors':errors[startup_error_count:][-30:],
  'consoleErrors':console_errors[-20:],
  'testHookNotShipped':True}
 (root/'vacation-resume-browser-18369-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('18.369 REAL VACATION TEST RESULT '+json.dumps(report,ensure_ascii=False),flush=True)
 if not report['ok'] or not report['realVacationWorkerAndStream'] or not report['realNextMatchAfterManualVacationEnd'] or not report['originalManualEndCommandAccepted'] or not report['terminalRepaintFailurePreservesOriginalPromise']:
  raise RuntimeError('Real vacation end -> next match still cannot advance genuine jornadas')
if __name__=='__main__':main()

