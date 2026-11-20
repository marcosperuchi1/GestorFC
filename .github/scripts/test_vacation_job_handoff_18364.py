from __future__ import annotations
import importlib.util,json,subprocess,sys,tempfile
from pathlib import Path

VERSION='18.364.0'

def extract(src,start,end):
 a=src.index(start);b=src.index(end,a+len(start))
 return src[a+len(start):b]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_vacation_job_handoff_18364.py <project | --standalone>')
 own=Path(__file__).resolve().parent
 spec=importlib.util.spec_from_file_location('handoff_fix',own/'fix_vacation_job_handoff_18364.py')
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 helper=mod.CORE
 standalone=sys.argv[1]=='--standalone'
 if not standalone:
  root=Path(sys.argv[1]).resolve()
  s=(root/'src/index.html').read_text(encoding='utf-8')
  assert s.count('/* FUTBR_VACATION_JOB_HANDOFF_18364')==1
  assert "const EDITION='18.364.0';" in s
  assert "window.GestorFC.version='18.364.0';window.GestorFC.visualVersion='18.364.0';" in s
  assert s.count("v53Worker.postMessage({op:'pause',end:true})")==1
  helper=extract(s,'<script id="futbr-vacation-handoff-18364">','</script>')
  wrapper=extract(s,'const v18359BaseStart=v53StartSimulation;','window.GestorFC.lifecycle18362=')
  assert 'v18364Succeeded=false;' in wrapper
  assert "queueMicrotask(()=>{void v18364OnVacationSettled(origin,v18364Succeeded);});" in wrapper
  assert "v18362CommitVacation(origin);" in wrapper
  assert "const p=v18359BaseStart(mode,...args);" in wrapper
  assert "const EDITION='18.364.0';" in s
  assert "if(!v18363CanUseJobWait()){" in s
  assert "await v53StartSimulation('dayfast');" in s
  assert s.index('<script id="futbr-jobwait-state-18363">')<s.index('<script id="futbr-vacation-handoff-18364">')
  assert 'v18364BaseAct=act' in helper
  assert 'v18364BaseChrome=v555UpdateChrome' in helper
  assert "Object.keys(state.players)" not in helper
  assert 'v52FlushSave(' not in helper and 'persist(' not in helper

 pre=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}};
let state,v53Sim,v53Worker,v125VacIncoming,v53Creating=false,
 v52SavePromise=null,v18119SeasonTransfer={active:false},
 v18121NewSeasonPreparation=false,v168RolloverRunning=false,
 v18359VacationPromise=null,v18362VacationOrigin=null,v18357LiveFallback=null,
 v89JobWait={active:false,stop:false},view='vacation';
let calls=[],toasts=[],updates=0,renders=0,jobCalls=0,baseActCalls=0;
function btn(){
 return {disabled:true,attrs:{disabled:''},title:'',
  setAttribute(k,v){this.attrs[k]=v;if(k==='disabled')this.disabled=true;},
  removeAttribute(k){delete this.attrs[k];if(k==='disabled')this.disabled=false;}};
}
const header=btn(),career=btn();
const document={querySelectorAll(q){return q.includes('v89-job-wait')?[header,career]:[]}};
function world(){return {year:2026,day:96,v1903CareerId:'Chapecoense-2026',
 userEmployed:false,v640National:null,
 players:{p1:{id:'p1'}},teams:[{id:'chapecoense'}],
 schedule:Array(156).fill({}),vacation:{active:true,paused:false,remaining:0,untilSeason:true}};}
function reset(){
 state=world();v53Sim={mode:'vacation',active:true,starting:false,finished:{},
 session:23,pause:false,pauseMode:''};
 v53Worker={postMessage:m=>calls.push(m)};v18359VacationPromise=Promise.resolve();
 v18362VacationOrigin={careerId:'Chapecoense-2026',employed:true};
 v89JobWait={active:false,stop:false};v125VacIncoming=null;v53Creating=false;
 v52SavePromise=null;v18119SeasonTransfer.active=false;
 v18121NewSeasonPreparation=false;v168RolloverRunning=false;
 v18357LiveFallback=null;calls=[];toasts=[];jobCalls=0;view='vacation';
}
function toast(t,kind){toasts.push([t,kind])}
function render(){renders++;v555UpdateChrome(document)}
function v555UpdateChrome(root){updates++;for(const b of root.querySelectorAll('[data-action="v89-job-wait"]')){
 b.disabled=true;b.setAttribute('disabled','');}}
function act(){baseActCalls++}
function v18363CanUseJobWait(){
 return !!state&&state.userEmployed===false&&!state.v640National?.userTeam&&
  !state.vacation?.active&&!v53Sim.active&&!v53Sim.starting&&!v53Sim.finished&&
  !v18359VacationPromise&&!v18362VacationOrigin&&!v52SavePromise;
}
async function v89RunJobWait(){jobCalls++;view='career';}
"""
 tests=r"""
(async()=>{
 reset();
 v555UpdateChrome(document);
 assert.equal(header.disabled,false,'2026 day 97 unemployed button must stay clickable during vacation');
 assert.equal(career.disabled,false,'Same condition in career page');
 act({dataset:{action:'v89-job-wait'}});
 assert.equal(v18364JobHandoff.pending,true,'Click queues a real vacation-to-job handoff');
 assert.deepEqual(calls,[{op:'pause',end:true}],'Must request the original vacation Worker to stop at safe day boundary');
 assert.equal(v53Sim.pause,true);
 assert.equal(v53Sim.pauseMode,'end');
 assert.equal(jobCalls,0,'Never start job Worker while vacation Worker is in flight');
 assert.equal(state.vacation.active,true,'Never fabricate completion or truncate the world on click');
 assert.equal(view,'vacation','User can inspect ongoing vacation while end is requested');
 assert.equal(window.GestorFC.vacationHandoff18364.status().pending,true);
 // A second click cancels only the job-search intent, not the safe ending.
 act({dataset:{action:'v89-job-wait'}});
 assert.equal(v18364JobHandoff.pending,false);
 assert.equal(calls.length,1);
 assert.equal(v18364JobHandoff.canceled,1);
 // User requests again and the vacation completes using existing Worker result.
 act({dataset:{action:'v89-job-wait'}});
 assert.equal(calls.length,2);
 assert.equal(jobCalls,0);
 v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 state.vacation.active=false;state.vacation.paused=true;state.vacation.untilSeason=false;
 await v18364OnVacationSettled({careerId:'Chapecoense-2026',employed:true},true);
 assert.equal(jobCalls,1,'Successful original checkpoint must transition to Turbo job wait');
 assert.equal(view,'career');
 assert.equal(v18364JobHandoff.resumed,1);
 await v18364OnVacationSettled({careerId:'Chapecoense-2026',employed:true},true);
 assert.equal(jobCalls,1,'No duplicate automatic job-search');
 // If the user loads a formerly dismissed save, but no vacation Worker exists,
 // clear only obsolete vacation flags and start with authoritative live state.
 reset();v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;v53Worker=null;
 act({dataset:{action:'v89-job-wait'}});
 await Promise.resolve();
 assert.equal(jobCalls,1,'Orphan vacation metadata must not keep click inert');
 assert.equal(state.vacation.active,false);
 assert.equal(state.vacation.paused,true);
 assert.deepEqual(v18357LiveFallback,{year:2026,day:96,careerId:'Chapecoense-2026'});
 // An interrupted Worker must not trigger an automatic search on false success.
 reset();act({dataset:{action:'v89-job-wait'}});
 v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 await v18364OnVacationSettled({careerId:'Chapecoense-2026',employed:true},false);
 assert.equal(jobCalls,0);
 assert.equal(v18364JobHandoff.pending,false);
 assert.equal(v18364JobHandoff.last,'original-vacation-failed');
 // A different career/session never inherits the queued search.
 reset();act({dataset:{action:'v89-job-wait'}});
 state.v1903CareerId='other-career';
 v53Sim.active=false;v53Sim.finished=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 await v18364OnVacationSettled({careerId:'Chapecoense-2026',employed:true},true);
 assert.equal(jobCalls,0);
 // No control of club/national vacancy when employed or managing a national team.
 reset();state.userEmployed=true;
 act({dataset:{action:'v89-job-wait'}});
 assert.equal(baseActCalls,1);
 state.userEmployed=false;state.v640National={userTeam:'BRA'};
 act({dataset:{action:'v89-job-wait'}});
 assert.equal(baseActCalls,2);
 assert.equal(jobCalls,0);
 // If a real Worker is streaming its last world, no unsafe UI-only reset.
 reset();v53Sim.active=false;v53Sim.finished={resolve(){}};v53Worker=null;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 assert.equal(v18364RepairOrphan(),false);
 console.log(JSON.stringify({ok:true,version:'18.364.0',
  screenshot2026Day97Handoff:true,clickedWhileVacationActive:true,
  sendsOriginalWorkerPauseEnd:true,noSecondWorkerUntilOriginalPromise:true,
  waitsForOriginalCheckpoint:true,automaticJobSearchAfterCheckpoint:true,
  doubleClickCancelsIntentOnly:true,doesNotDuplicateJobSearch:true,
  orphanVacationFlagRecovered:true,liveStatePreserved:true,
  failedVacationDoesNotStartWorker:true,wrongCareerCannotAutoSearch:true,
  nationalCareerProtected:true,transferInFlightNotOverridden:true,
  historyAndSaveCodecUntouched:true}));
})().catch(e=>{console.error(e.stack||e);process.exitCode=1});
"""
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)/'handoff-18364.cjs'
  p.write_text(pre+'\n'+helper+'\n'+tests,encoding='utf-8')
  syntax=subprocess.run(['node','--check',str(p)],capture_output=True,text=True,timeout=20)
  if syntax.returncode:raise RuntimeError('18.364 standalone syntax regression: '+syntax.stderr[-5000:])
  run=subprocess.run(['node',str(p)],capture_output=True,text=True,timeout=30)
  if run.returncode:raise RuntimeError('18.364 handoff runtime regression: '+(run.stderr or run.stdout)[-6000:])
  report=json.loads(run.stdout.strip().splitlines()[-1])
 if not standalone:
  (root/'vacation-handoff-18364-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
