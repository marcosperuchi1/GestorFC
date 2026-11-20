from __future__ import annotations
import json,os,re,shutil,subprocess,sys,tempfile
from pathlib import Path

MARK='FUTBR_SCOPE_REPAIR_18366'
TEST_HOOK=r"""
// TEST ONLY. Injected into an ephemeral browser copy; never shipped.
window.__futbr18366Test={
 messages:[],jobStarts:0,
 setup(){
  state={
   v1903CareerId:'scope-fixture-2026',year:2026,day:35,seasonDone:false,
   user:'chapecoense',userEmployed:false,v640National:null,live:null,
   vacation:{active:true,paused:false,remaining:110,untilSeason:true,completed:35},
   players:{p1:{id:'p1',name:'Synthetic player'}},
   teams:[{id:'chapecoense',name:'Chapecoense',roster:['p1'],academy:[],proReserve:[]}],
   schedule:Array.from({length:156},()=>({fixtures:[]}))
  };
  v53Sim.active=true;v53Sim.starting=false;v53Sim.finished=null;
  v53Sim.mode='vacation';v53Sim.session=123;v53Sim.syncing=false;
  v53Sim.patching=false;v53Sim.pause=false;v53Sim.pauseMode='';
  v53Worker={postMessage:m=>window.__futbr18366Test.messages.push(m)};
  v18359VacationPromise=Promise.resolve();
  v18362VacationOrigin={careerId:state.v1903CareerId,employed:true};
  v125VacIncoming=null;v52SavePromise=null;v53Creating=false;
  v89JobWait.active=false;v89JobWait.stop=false;
  v18112Dismissal.pending=false;
  v18365Job.pending=false;v18365Job.requested=0;
  v18365Job.duplicateClicks=0;v18365Job.started=0;
  v18365Job.timer=null;v18365Job.last='test-start';
  this.messages=[];this.jobStarts=0;
  v89RunJobWait=async()=>{this.jobStarts++;return true;};
  render=()=>document.getElementById('app');
  return window.GestorFC.scope18366.status();
 },
 syncCareer(){
  v53Sim.syncing=true;
  const html=careerPage();
  v53Sim.syncing=false;
  return html;
 },
 async settle(){
  v53Sim.active=false;v53Sim.finished=null;
  v53Sim.syncing=false;v53Sim.patching=false;
  v18359VacationPromise=null;v18362VacationOrigin=null;
  state.vacation.active=false;state.vacation.remaining=0;
  return await v18365FinishHandoff(true);
 }
};
"""
def browser_executable():
    for exe in ('chrome','chrome.exe','chromium','chromium.exe','msedge','msedge.exe'):
        found=shutil.which(exe)
        if found:return found
    for base in ('PROGRAMFILES','ProgramFiles','PROGRAMFILES(X86)','ProgramFiles(x86)'):
        if os.environ.get(base):
            for path in (
                Path(os.environ[base])/'Google/Chrome/Application/chrome.exe',
                Path(os.environ[base])/'Microsoft/Edge/Application/msedge.exe',
            ):
                if path.exists():return str(path)
    for path in ('/usr/bin/chromium','/usr/bin/google-chrome'):
        if Path(path).exists():return path
    return None

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_unemployed_scope_18366.py <project>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src/index.html').read_text(encoding='utf-8')
    assert html.count('/* FUTBR_SCOPE_REPAIR_18366')==1
    for sid in ('futbr-mls-vacation-18201-ui','futbr-jobwait-state-18363','futbr-vacation-handoff-18364','futbr-dismissal-source-18365'):
        assert not re.search(r'<script\s+id=["\\x27]'+sid,html),sid
    i=html.index('let state=null,saved=null')
    end=html.find('</script>',i)
    anchor=html.rfind('})();',i,end)
    assert 0<i<anchor<end and not html[anchor+5:end].strip(), "Original IIFE closing not found"
    scope=html[i:anchor]
    for marker in (
      'v18201RecoverNotice',
      'v18201Decorate',
      'FUTBR_JOBWAIT_STATE_CORE_18363',
      'FUTBR_VACATION_JOB_HANDOFF_18364',
      'FUTBR_DISMISSAL_SOURCE_18365',
      'FUTBR_SCOPE_REPAIR_18366',
      'const v18363BaseChrome=v555UpdateChrome',
      'const v18364BaseChrome=v555UpdateChrome',
      'const v18365BaseChrome=v555UpdateChrome',
      'v18365HandleClick(el))return',
      "v53Worker?.postMessage({op:'pause',end:true,reason:'dismissal'})",
    ):
        assert marker in scope,marker
    assert html.count('/* FUTBR_JOBWAIT_STATE_CORE_18363')==1
    assert html.count('/* FUTBR_VACATION_JOB_HANDOFF_18364')==1
    assert html.count('/* FUTBR_DISMISSAL_SOURCE_18365')==1
    assert "const EDITION='18.366.0';" in html
    assert "window.GestorFC.version='18.366.0';window.GestorFC.visualVersion='18.366.0';" in html
    assert 'body.v636-career-view .main{height:auto!important' in html
    # Syntax-check the COMPLETE real main game script, not an isolated mock.
    script_open=html.rfind('<script',0,i)
    js=html[html.index('>',script_open)+1:end] # entire active main script
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'game-18366.js';path.write_text(js,encoding='utf-8')
        res=subprocess.run(['node','--check',str(path)],capture_output=True,text=True,timeout=75)
        if res.returncode:raise RuntimeError('18.366 complete in-scope JS syntax error: '+res.stderr[-6000:])
    report={'ok':True,'version':'18.366.0',
      'scriptInOriginalLexicalScope':True,'detachedControllersRemoved':True,
      'realMainGameScriptSyntaxValid':True,'privateStateAndWorkerNotDuplicated':True,
      'actualClickAndCareerEntryInSameScope':True}
    # First phase can run in build environments without a browser.
    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        raise RuntimeError('18.366 needs browser regression: Playwright unavailable') from e
    executable=browser_executable()
    if not executable:raise RuntimeError('18.366 needs real Chrome or Chromium')
    # Add an internal test fixture ONLY to the ephemeral browser HTML. No
    # setter or fake Worker is added to the user's actual Windows build.
    test_html=html[:anchor]+'\n'+TEST_HOOK+'\n'+html[anchor:]
    errors=[];console=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=executable,headless=True,
           args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
        page=browser.new_page(viewport={'width':1600,'height':900})
        page.on('pageerror',lambda e:errors.append({'message':str(e),'stack':str(getattr(e,'stack',''))[:3000]}))
        page.on('console',lambda m:console.append({'message':m.text,'location':m.location}) if m.type=='error' else None)
        page.set_content(test_html,wait_until='domcontentloaded',timeout=150000)
        page.wait_for_timeout(1800)
        startup_errors=len(errors);startup_console=len(console)
        probe=page.evaluate("""() => {
          const g=window.GestorFC||{};
          let diagnostic=null,old=null,previous=null;
          try{diagnostic=g.scope18366?.status?.()||null;}catch(e){diagnostic={error:String(e)};}
          try{old=g.jobHandoff18365?.status?.()||null;}catch(e){old={error:String(e)};}
          try{previous=g.vacationHandoff18364?.status?.()||null;}catch(e){previous={error:String(e)};}
          return {diagnostic,old,previous,
            loginVisible:!!document.querySelector('#v548-login-form'),
            mlsVersion:g.mlsVacationUI18201?.version||''};
        }""")
        if not probe.get('diagnostic',{}).get('sameGameScope'):
            raise RuntimeError('18.366 game scope unavailable in real Chromium: '+str(probe))
        if not probe.get('old') or 'error' in probe['old']:
            raise RuntimeError('18.365 legacy scope still failing: '+str(probe))
        if not probe.get('previous') or 'error' in probe['previous']:
            raise RuntimeError('18.364 scope still failing: '+str(probe))
        if probe.get('mlsVersion')!='18.201':
            raise RuntimeError('18.201 MLS next-match control did not relocate in-scope: '+str(probe))
        pre=page.evaluate("""() => {
          window.__futbr18366Test.setup();
          let b=document.getElementById('scope-test-18366');
          if(!b){b=document.createElement('button');b.id='scope-test-18366';
           b.type='button';b.dataset.action='v89-job-wait';
           b.textContent='Até o fim / proposta';document.body.appendChild(b);}
          b.disabled=false;b.click();
          return {first:window.GestorFC.scope18366.status(),
            messages:[...window.__futbr18366Test.messages],
            label:b.textContent,disabled:b.disabled};
        }""")
        if not (pre['first'].get('pendingJobHandoff') and pre['first'].get('queuedClicks')==1
                and any(m.get('op')=='pause' and m.get('end') is True for m in pre['messages'])
                and 'Encerrando' in pre['label']):
            raise RuntimeError('18.366 real DOM first click failed: '+str(pre))
        second=page.evaluate("""() => {
          const b=document.getElementById('scope-test-18366');
          b.disabled=false;b.click();
          return {status:window.GestorFC.scope18366.status(),
            jobStarts:window.__futbr18366Test.jobStarts,
            messages:window.__futbr18366Test.messages.length};
        }""")
        if not (second['status'].get('pendingJobHandoff') and
                second['status'].get('repeatedClicks')==1 and
                second['jobStarts']==0):
            raise RuntimeError('18.366 second DOM click unexpectedly canceled or raced Worker: '+str(second))
        waiting=page.evaluate("window.__futbr18366Test.syncCareer()")
        if 'Sincronizando a jornada' not in waiting:
            raise RuntimeError('18.366 career read-only sync placeholder missing')
        after=page.evaluate("""async () => {
          await window.__futbr18366Test.settle();
          return {status:window.GestorFC.scope18366.status(),
            jobStarts:window.__futbr18366Test.jobStarts};
        }""")
        if not (after['jobStarts']==1 and
                not after['status'].get('pendingJobHandoff')):
            raise RuntimeError('18.366 post-checkpoint offer search not reached: '+str(after))
        browser.close()
    def is_scope_error(e):
        v=(e.get('message','')+' '+e.get('stack','')).lower()
        return ('state is not defined' in v or
          (('v18365' in v or 'v18364' in v) and
           ('not defined' in v or 'referenceerror' in v)))
    bad=[e for e in errors+console if is_scope_error(e)]
    if bad:
        info={'beforeFixture':sum(is_scope_error(e) for e in errors[:startup_errors]+console[:startup_console]),
          'afterFixture':sum(is_scope_error(e) for e in errors[startup_errors:]+console[startup_console:]),
          'sourceStacks':[{'message':e.get('message',''),'stack':e.get('stack',''),
             'location':e.get('location',{})} for e in bad[:12]],
          'allPageErrorCount':len(errors),'allConsoleErrorCount':len(console)}
        print('18.366 TRACE SCOPE ERRORS: '+json.dumps(info,ensure_ascii=False)[:24000],flush=True)
        raise RuntimeError('18.366 browser ReferenceError requires source correction; see TRACE SCOPE ERRORS above')
    report.update({
       'browser':executable,'realChromiumBootAndScopeChecked':True,
       'legacy18363And18364ScopeCallable':True,
       'legacyMLSVacationScopeCallable':True,
       'actualDOMClickSendsOriginalWorkerEnd':True,
       'secondDOMClickKeepsRequest':True,
       'synchronizingCareerReadOnlyView':True,
       'postCheckpointStartsJobOnce':True,
       'stateReferenceErrors':0,
       'allCapturedPageErrors':len(errors),
       'allCapturedConsoleErrors':len(console),
       'syntheticFixtureNotShipped':True,
    })
    (root/'scope-repair-18366-tests.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
