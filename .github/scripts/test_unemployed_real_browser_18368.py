from __future__ import annotations
import json,os,re,shutil,sys
from pathlib import Path
from playwright.sync_api import sync_playwright

HOOK=r"""
/* TEST ONLY: injected into ephemeral HTML, not shipped in release */
window.__futbr18368Real={
 result:null,working:false,notices:[],
 prepare(){
  const club='t0'; // E.createCareer assigns t0, t1... regardless of catalog IDs
  const s=E.createCareer({club,manager:'Integration Worker Test',difficulty:'normal',seed:183682026});
  if(!s||!s.players||!Array.isArray(s.teams)||!s.teams.length||!s.schedule?.length)
   throw Error('Engine did not create a complete playable world');
  // The test runs in an authless browser. Keep the game Engine and Worker
  // real, but suppress only the login-dependent full-page renderer.
  render=()=>document.getElementById('app');
  state=s;saved=null;view='career';
  this.notices=[];
  const oldToast=toast;
  toast=(...args)=>{this.notices.push(args.map(String).join(' '));return oldToast(...args);};
  if(!state.v1903CareerId)state.v1903CareerId='real-engine-browser-test-2026';
  try{v636CoachState(state);}catch(e){throw Error('Coach state invalid: '+e.message);}
  state.userEmployed=false;state.v640National=null;state.live=null;
  if(!state.vacation)state.vacation={};
  state.vacation.active=false;state.vacation.paused=true;state.vacation.remaining=0;
  v89JobWait.active=false;v89JobWait.stop=false;v89JobWait.days=0;
  v53Sim.active=false;v53Sim.starting=false;v53Sim.finished=null;
  v53Sim.patching=false;v53Sim.syncing=false;
  v52SavePromise=null;v52PendingState=null;v52SaveDirty=false;
  saveOK=true;
  return {start:state.day,year:state.year,teams:state.teams.length,
   players:Object.keys(state.players).length,career:state.v1903CareerId,
   user:state.user,schedule:state.schedule.length};
 },
 start(){
  if(this.working)throw Error('Real Worker test already running');
  this.working=true;this.result=null;
  const start=Number(state.day),year=Number(state.year),career=String(state.v1903CareerId);
  const old=v53StartSimulation;
  let rounds=0;
  v53StartSimulation=async function(mode,...args){
   const out=await old(mode,...args);
   if(mode==='dayfast'){
    rounds++;
    if(rounds>=2)v89JobWait.stop=true;
   }
   return out;
  };
  (async()=>{
   try{
    await v89RunJobWait();
    this.result={ok:Number(state.day)>=start+2&&rounds>=2,
      start,after:Number(state.day),year,rounds,
      confirmed:Number(v89JobWait.days)||0,
      workerMode:v53Sim?.mode||'',careerUnchanged:String(state.v1903CareerId)===career,
      unemployed:state.userEmployed===false,
      running:!!v89JobWait.active,
      hasRealWorker:!!v53Worker,
      notices:[...this.notices].slice(-12),
      simulationStatus:window.GestorFC.unemployedWorker18368?.status?.()};
   }catch(e){this.result={ok:false,error:String(e),stack:String(e?.stack||'').slice(0,3000),
       start,day:state?.day,rounds,notices:[...this.notices].slice(-12)};}
   finally{v53StartSimulation=old;this.working=false;}
  })();
  return true;
 }
};
"""

def chrome():
 for exe in ('chrome','chrome.exe','msedge','msedge.exe','chromium','chromium.exe'):
  f=shutil.which(exe)
  if f:return f
 for env in ('PROGRAMFILES','ProgramFiles','PROGRAMFILES(X86)','ProgramFiles(x86)'):
  if os.environ.get(env):
   for path in (Path(os.environ[env])/'Google/Chrome/Application/chrome.exe',
                Path(os.environ[env])/'Microsoft/Edge/Application/msedge.exe'):
    if path.exists():return str(path)
 for path in ('/usr/bin/chromium','/usr/bin/google-chrome'):
  if Path(path).exists():return str(path)
 return None

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_unemployed_real_browser_18368.py <project>')
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 assert 'FUTBR_UNEMPLOYED_WORKER_REAL_PROGRESS_18368' in html
 i=html.index('let state=null,saved=null')
 end=html.index('</script>',i)
 anchor=html.rfind('})();',i,end)
 if not (0<i<anchor<end):raise RuntimeError('Could not insert ephemeral real-engine smoke in production IIFE')
 test_html=html[:anchor]+'\n'+HOOK+'\n'+html[anchor:]
 browser_path=chrome()
 if not browser_path:raise RuntimeError('Real browser unavailable, cannot claim actual Engine simulation')
 errors=[]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=browser_path,headless=True,
   args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
  context=browser.new_context(viewport={'width':1280,'height':800})
  page=context.new_page()
  page.on('pageerror',lambda e:errors.append(str(e)[:800]))
  def route_handler(route):
   if route.request.resource_type=='document' and route.request.url.startswith('http://localhost:8732/'):
    route.fulfill(status=200,content_type='text/html; charset=utf-8',body=test_html)
   else:route.abort()
  page.route('**/*',route_handler)
  page.goto('http://localhost:8732/',wait_until='domcontentloaded',timeout=150000)
  page.wait_for_function("() => !!window.__futbr18368Real",timeout=120000)
  # Let 18.366's existing login/bootstrap microtasks settle before injecting
  # the ephemeral career, so account-init doesn't overwrite the state to null.
  page.wait_for_timeout(2200)
  setup=page.evaluate("() => window.__futbr18368Real.prepare()")
  print('18.368 ORIGINAL ENGINE TEST SETUP: '+json.dumps(setup,ensure_ascii=False),flush=True)
  page.evaluate("() => window.__futbr18368Real.start()")
  page.wait_for_function("() => window.__futbr18368Real.result!==null",timeout=180000)
  result=page.evaluate("() => window.__futbr18368Real.result")
  context.close();browser.close()
 report={'ok':bool(result.get('ok')), 'version':'18.368.0',
  'originalEngineRealBrowser':True,'playwrightChromium':browser_path,
  'authlessEphemeralCareer':True,'originalWorkerExecuted':result.get('hasRealWorker'),
  'twoRealEngineJornadas':result.get('rounds',0)>=2,
  'twoActualDaysAdvanced':result.get('after',0)>=result.get('start',0)+2,
  'careerIdentityPreserved':result.get('careerUnchanged',False),
  'unemployedStayedUnemployed':result.get('unemployed',False),
  'didNotLeaveJobWaitActive':not result.get('running',True),
  'setup':setup,'result':result,'pageErrors':errors[:8],
  'testHookNotShipped':True}
 (root/'unemployed-browser-18368-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('18.368 ORIGINAL ENGINE TEST RESULT: '+json.dumps(report,ensure_ascii=False),flush=True)
 if not all(report.get(k) for k in ('ok','originalWorkerExecuted','twoRealEngineJornadas',
  'twoActualDaysAdvanced','careerIdentityPreserved','unemployedStayedUnemployed','didNotLeaveJobWaitActive')):
  raise RuntimeError('18.368 real unemployed browser game Engine failed to advance at least two journeys')
if __name__=='__main__':main()
