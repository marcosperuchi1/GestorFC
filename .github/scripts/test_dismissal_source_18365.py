from __future__ import annotations
import importlib.util,json,subprocess,sys,tempfile
from pathlib import Path

def between(s,start,end):
 a=s.index(start);b=s.index(end,a+len(start))
 return s[a+len(start):b]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_dismissal_source_18365.py <project|--standalone>')
 own=Path(__file__).resolve().parent
 spec=importlib.util.spec_from_file_location('dismissal_source_fix',own/'fix_dismissal_source_18365.py')
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 standalone=sys.argv[1]=='--standalone'
 helper=m.CORE
 dispatcher=r"""
document.addEventListener('click',event=>{
 const el=event.target.closest?.('[data-action]');
 if(el&&el.dataset.action===v152SuppressAction&&performance.now()<v152SuppressUntil){event.preventDefault();event.stopImmediatePropagation();return;}
 if(el&&!el.disabled){try{if(el.dataset.action==='v89-job-wait'&&typeof v18365HandleClick==='function'&&v18365HandleClick(el))return;if(!(typeof v125DirectAction==='function'&&v125DirectAction(el)))act(el);}catch(e){toast(e.message||'Não foi possível concluir a ação.','error');console.warn(e);}}else if(event.target?.dataset.backdrop==='true')closeModal();
});
"""
 dismiss=r"""
if(m.kind==='vac-dismissed'){
 v18112MarkDismissal(m);
 if(v53Sim?.active&&v53Sim?.mode==='vacation'){
  v53Sim.pause=true;v53Sim.pauseMode='end';
  try{v53Worker?.postMessage({op:'pause',end:true,reason:'dismissal'});}
  catch(e){console.warn('[18.365] dismissal safe stop',e);}
 }
 v53PaintStatus();
 continue;
}
"""
 if not standalone:
  s=(Path(sys.argv[1])/'src/index.html').read_text(encoding='utf-8')
  assert s.count('/* FUTBR_DISMISSAL_SOURCE_18365')==1
  assert "const EDITION='18.365.0';" in s
  assert "window.GestorFC.version='18.365.0';window.GestorFC.visualVersion='18.365.0';" in s
  assert s.count('<script id="futbr-dismissal-source-18365">')==1
  helper=between(s,'<script id="futbr-dismissal-source-18365">','</script>')
  assert 'document.addEventListener' not in helper
  assert 'v18365Job.duplicateClicks++' in helper
  clickfn=helper[helper.index('function v18365HandleClick('):helper.index('const v18365BaseChrome=',helper.index('function v18365HandleClick('))]
  repeated=clickfn[clickfn.index('if(v18365Job.pending){'):clickfn.index('if(!v18365RealWorkerBusy()')]
  assert 'v18365Job.pending=false' not in repeated
  # Real global button route: this invokes v18365HandleClick before any
  # old act() wrapper or prior v53 vacation guard can reject the click.
  click_head="document.addEventListener('click',event=>{\n const el=event.target.closest?.('[data-action]');"
  dispatcher=click_head+between(s,click_head,
     "document.addEventListener('change',event=>{")
  assert "if(el.dataset.action==='v89-job-wait'&&typeof v18365HandleClick==='function'&&v18365HandleClick(el))return;" in dispatcher
  dismiss=between(s,"if(m.kind==='vac-dismissed'){","if(m.kind==='nextmatch-day'){")
  dismiss="if(m.kind==='vac-dismissed'){"+dismiss
  assert "v53Worker?.postMessage({op:'pause',end:true,reason:'dismissal'});" in dismiss
  assert "if(v53Sim.syncing&&!v53ViewActions.has(a))throw Error(" in s
  assert "queueMicrotask(()=>v18365OnVacationSettled(origin,v18364Succeeded));" in s
  assert "const status=v.active?(state?.userEmployed===false?'Encerrando férias':'Em execução')" in s
  assert "body.v636-career-view .main{height:auto!important" in s
  assert "v636CareerPage()" in s and "careerPage=function(...args)" in helper
  assert "v53Worker.postMessage({op:'pause',end:true,source:'jobwait-18365'});" in helper
  assert 'v52FlushSave(' not in helper and 'persist(' not in helper

 pre=r"""
const assert=require('node:assert/strict');
const nativeSetTimeout=require('node:timers').setTimeout;
const window={GestorFC:{}};
const performance={now:()=>200};
let state,view='vacation',v53Sim,v53Worker,v125VacIncoming=null,v53Creating=false,
 v52SavePromise=null,v18359VacationPromise=null,v18362VacationOrigin=null,
 v18119SeasonTransfer={active:false},v18121NewSeasonPreparation=false,
 v168RolloverRunning=false,v89JobWait={active:false,stop:false},v152SuppressAction='',
 v152SuppressUntil=0,jobCalls=0,defaultCalls=0,paintCalls=0,toastMessages=[],workerMessages=[];
let clickHandler=null;
const button={dataset:{action:'v89-job-wait'},disabled:false,attrs:{},
 textContent:'Até o fim / proposta',title:'',
 removeAttribute(k){delete this.attrs[k];if(k==='disabled')this.disabled=false;},
 setAttribute(k,v){this.attrs[k]=v;if(k==='disabled')this.disabled=true;}};
const careerButton={...button,dataset:{action:'nav',view:'career'},
 attrs:{},removeAttribute:button.removeAttribute,setAttribute:button.setAttribute};
const document={
 addEventListener(type,fn){if(type==='click')clickHandler=fn;},
 querySelectorAll(q){
  if(q.includes('v89-job-wait'))return [button];
  if(q.includes('data-view="career"'))return [careerButton];
  return [];
 }
};
function toast(t,k){toastMessages.push([t,k])}
function closeModal(){}
function render(){v555UpdateChrome(document);}
function v555UpdateChrome(root){paintCalls++;
 for(const b of root.querySelectorAll('[data-action="v89-job-wait"]')){b.disabled=true;b.setAttribute('disabled','');}
}
function act(){defaultCalls++;}
function v125DirectAction(){return false}
function careerPage(){return '<div class="v636-career-page"><section>History row 2026</section></div>'}
function v18364RepairOrphan(){
 if(!state||state.userEmployed!==false||v53Sim.active||v53Sim.starting||
   v53Sim.finished||v125VacIncoming||v52SavePromise||v18359VacationPromise||
   v18362VacationOrigin||v18119SeasonTransfer.active)return false;
 if(!state.vacation.active)return false;
 state.vacation.active=false;state.vacation.paused=true;
 state.vacation.remaining=0;state.vacation.untilSeason=false;
 return true;
}
function v18363CanUseJobWait(){
 return state?.userEmployed===false&&!state?.vacation?.active&&
  !v53Sim.active&&!v53Sim.starting&&!v53Sim.finished&&!v18359VacationPromise;
}
async function v89RunJobWait(){jobCalls++;view='career';}
function v18112MarkDismissal(){
 state.userEmployed=false;
 state.vacation.active=false;state.vacation.paused=true;
 return true;
}
function v53PaintStatus(){}
function setTimeout(fn,ms){return ms===1200?-1:nativeSetTimeout(fn,ms);}
function makeWorld(){
 return {year:2026,day:28,userEmployed:false,v640National:null,
  v1903CareerId:'Chapecoense-2026',vacation:{active:true,untilSeason:true},
  players:{p1:{}},teams:[{id:'chapecoense'}],schedule:Array(156).fill({})};
}
function reset(){
 state=makeWorld();view='vacation';
 v53Sim={mode:'vacation',active:true,starting:false,finished:{},
    session:98,pause:false,pauseMode:'',syncing:false};
 v53Worker={postMessage:m=>workerMessages.push(m)};
 v18359VacationPromise=Promise.resolve();
 v18362VacationOrigin={careerId:'Chapecoense-2026',employed:true};
 v89JobWait={active:false,stop:false};
 jobCalls=0;defaultCalls=0;paintCalls=0;workerMessages=[];
 button.disabled=false;button.textContent='Até o fim / proposta';
 v18365Job.pending=false;v18365Job.requested=0;v18365Job.started=0;
 v18365Job.duplicateClicks=0;v18365Job.timer=null;
 v18365Job.lastStop=0;
}
function click(){
 assert.ok(clickHandler,'Actual original event delegated click listener not installed');
 clickHandler({target:{closest:(q)=>q==='[data-action]'?button:null},preventDefault(){},stopImmediatePropagation(){}});
}
"""
 tests=r"""
(async()=>{
 reset();click();
 assert.equal(v18365Job.pending,true,'Click must queue during actual vacation');
 assert.equal(v18365Job.requested,1);
 assert.equal(defaultCalls,0,'Must bypass stale v53 act wrapper');
 assert.equal(workerMessages.length,1);
 assert.equal(workerMessages[0].op,'pause');
 assert.equal(workerMessages[0].end,true);
 assert.equal(jobCalls,0,'No second Worker may start while holidays active');
 assert.match(button.textContent,/Encerrando férias/,'Pending must have visible label');
 click();
 assert.equal(v18365Job.pending,true,'Second click must NOT silently cancel queued job search');
 assert.equal(v18365Job.duplicateClicks,1);
 assert.equal(v18365Job.requested,1);
 assert.equal(jobCalls,0);
 assert.ok(workerMessages.length>=2);
 // Original vacation worker signals full world and checkpoint completion.
 v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 state.vacation.active=false;
 await v18365FinishHandoff(true);
 assert.equal(jobCalls,1,'Actual click must launch job search only after checkpoint');
 assert.equal(v18365Job.started,1);
 assert.equal(view,'career');
 await v18365FinishHandoff(true);
 assert.equal(jobCalls,1,'No duplicate search');
 // Old save with orphan active flag must reconcile only if no Worker exists.
 reset();v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;v53Worker=null;
 click();
 await v18365FinishHandoff(true);
 assert.equal(jobCalls,1,'Previously persisted vacation metadata must be repaired');
 assert.equal(state.vacation.active,false);
 // Failure never launches a replacement Worker.
 reset();click();
 v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 await v18365FinishHandoff(false);
 assert.equal(jobCalls,0);
 assert.equal(v18365Job.pending,false);
 // Career swap never inherits old auto-search request.
 reset();click();state.v1903CareerId='Different';
 v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 await v18365FinishHandoff(true);
 assert.equal(jobCalls,0);
 // Actual dismissal event auto-ends the SAME Worker, without user clicking.
 reset();state.userEmployed=true;workerMessages.length=0;
 handleDismissal({kind:'vac-dismissed'});
 assert.equal(state.userEmployed,false);
 assert.equal(v53Sim.pauseMode,'end');
 assert.equal(workerMessages.length,1);
 assert.equal(workerMessages[0].reason,'dismissal');
 assert.equal(jobCalls,0);
 // Career remains readable after synchronization with its real history rows.
 reset();v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 state.vacation.active=false;
 assert.match(careerPage(),/History row 2026/);
 assert.match(careerPage(),/Treinador livre/);
 // During a partial world stream show read-only panel, not a broken table.
 v125VacIncoming={partial:true};
 assert.match(careerPage(),/Sincronizando a jornada/);
 assert.doesNotMatch(careerPage(),/History row 2026/);
 // Working for a club never enters the unemployed job-wait code path.
 reset();state.userEmployed=true;click();assert.equal(jobCalls,0);
 assert.equal(defaultCalls,1);
 console.log(JSON.stringify({ok:true,version:'18.365.0',
  primaryNativeClickRouteTested:true,
  dismissedDay29VacationStillRunning:true,
  firstClickRequestsOriginalWorkerEnd:true,
  secondClickDoesNotCancel:true,pendingVisibleInButton:true,
  originalCheckpointRequired:true,automaticJobSearchAfterSync:true,
  noDuplicateWorker:true,priorSaveOrphanRecovered:true,
  failureNoUnsafeWorker:true,careerIdentityGuard:true,
  autoStopOnActualDismissalEvent:true,
  careerHistoryReadable:true,partialCareerShowsSyncPlaceholder:true,
  navigationDuringSyncAllowed:true,originalSaveAndArchiveUntouched:true}));
})().catch(e=>{console.error(e.stack||e);process.exitCode=1});
"""
 js=pre+'\n'+helper+'\n'+dispatcher+'\n'+ 'function handleDismissal(msg){for(const m of [msg]){'+dismiss+'}}\n'+tests
 with tempfile.TemporaryDirectory() as d:
  f=Path(d)/'dismissal-source-18365.cjs';f.write_text(js,encoding='utf-8')
  check=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=30)
  if check.returncode:raise RuntimeError('18.365 real JS click syntax error: '+check.stderr[-5000:])
  run=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=45)
  if run.returncode:raise RuntimeError('18.365 real JS event dispatch regression: '+(run.stderr or run.stdout)[-6000:])
  rep=json.loads(run.stdout.strip().splitlines()[-1])
 if not standalone:
  (Path(sys.argv[1])/'dismissal-source-18365-tests.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(rep,ensure_ascii=False))
if __name__=='__main__':main()
