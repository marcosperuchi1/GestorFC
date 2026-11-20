from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path

FIXTURE=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}},document={hidden:false};
let state=null,saved=null,view='career';
let v53Sim={active:false,starting:false,patching:false,syncing:false,session:0},
 v52SavePromise=null,v52SaveDirty=true,v52PendingState=null,v52SaveTimer=null,
 v52NotifySave=false,v52SaveWaiters=[],v143PostRankPending=false,
 v143NationalRepairToken=0,v143NationalRepairRunning=false,
 v53Worker=null,v53WorkerReady=null,v53Creating=false,
 v125VacIncoming=null,saveOK=true,vacationLoop=false,vacationDelay=600,
 v158ManualPrimePromise=null,v158ManualPrimeDay=0,v158ManualPrimeYear=0;
let presaves=0,workerMessages=[],started=0,dialogs=0;
function render(){}
function stopTimer(){}
function v148EnsureNationalReady(){return false}
function v5CrestsOut(){}
function v53PaintStatus(){}
function v52FlushSave(){presaves++;throw new Error('Full pre-save should NOT execute on first post-vacation round')}
const E={human(){return {balance:10}}};
function v53GetWorker(){
 const w={postMessage(m){
  workerMessages.push(m);
  assert.equal(m.loadSaved,false,'Cannot reload a pre-vacation save');
  assert.equal(m.useResident,false,'Must not trust a resident Worker from vacation');
  assert.equal(m.state,state,'Must post live synchronized full state once');
  started++;
  setImmediate(()=>{
   state.day++;
   v53Sim.active=false;
   const p=v53Sim.finished;v53Sim.finished=null;p.resolve(state);
  });
 }};
 v53Worker=w;
 return Promise.resolve(w);
}
function career(id='c1',day=16){
 return {v1903CareerId:id,year:2026,day,user:'t0',userEmployed:true,
   seasonDone:false,players:{p:{}},teams:[{id:'t0'}],
   schedule:[{fixtures:[]},{fixtures:[]}],vacation:{active:false,paused:true}};
}
function reset(day=16){
 state=career('c1',day);saveOK=true;v52SavePromise=null;v52SaveDirty=true;
 v53Sim={active:false,starting:false,patching:false,syncing:false,session:0};
 v53Worker=null;v53WorkerReady=null;v125VacIncoming=null;
 v18369VacationReturn=null;workerMessages=[];presaves=0;started=0;
}
"""

TEST=r"""
(async()=>{
 reset();
 const original=state;
 assert.equal(v18369CaptureVacationReturn(state,{session:2}),true,'Capture completed vacation');
 assert.equal(v18369VacationReturn.day,16);
 const result=await v53StartSimulation('nextmatch');
 assert.equal(result,state);
 assert.equal(state.day,17,'Nextmatch must advance');
 assert.equal(started,1);
 assert.equal(presaves,0,'Not a single blocking save before Worker');
 assert.equal(workerMessages[0].mode,'nextmatch');
 assert.equal(workerMessages[0].state,original);
 reset();
 assert.equal(v18369CaptureVacationReturn(state,{session:3}),true);
 await v53StartSimulation('day');
 assert.equal(state.day,17,'One-day command must resume');
 assert.equal(workerMessages[0].mode,'day');
 assert.equal(presaves,0);
 reset();
 const stale=state;v18369CaptureVacationReturn(state,{session:4});
 state=career('different',16);
 assert.equal(v18369CanStartFromReturnedVacation('nextmatch'),false,'Wrong career blocked');
 assert.equal(v18369VacationReturn,null,'Wrong career invalidates token');
 reset();v53Sim.active=true;
 assert.equal(v18369CaptureVacationReturn(state,{session:5}),false,'Never capture unfinished vacation');
 reset();v125VacIncoming={year:2026};
 assert.equal(v18369CaptureVacationReturn(state,{session:6}),false,'Never capture streaming incomplete world');
 reset();state.vacation.active=true;
 assert.equal(v18369CaptureVacationReturn(state,{session:7}),false,'Never treat still-running holidays as finished');
 console.log(JSON.stringify({ok:true,version:'18.369.0',realOriginalV53StartSimulation:true,
  nextMatchAfterVacationWorks:true,normalDayAfterVacationWorks:true,
  noPreSaveBeforeResume:true,noStaleDiskReload:true,noWrongResidentWorker:true,
  careerIdentityGuard:true,noEarlySyncRelease:true,oldSavePreserved:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_vacation_resume_18369.py <project>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 assert '/* FUTBR_VACATION_RESUME_HANDOFF_18369' in s
 assert "const EDITION='18.369.0';" in s
 assert "window.GestorFC.version='18.369.0';window.GestorFC.visualVersion='18.369.0';" in s
 bs=s.index('async function v53StartSimulation(mode,options={}){')
 be=s.index('runVacation=async function',bs)
 base=s[bs:be].strip()
 assert '||v18369CanStartFromReturnedVacation(mode,state);' in base
 assert 'const canLoadSaved=!v18311LiveVacation&&' in base
 assert "if(!canLoadSaved&&!(mode==='dayfast'&&options?.jobWaitResident===true))msg.state=state;" in base
 ds=s.rindex('v53DrainPatches=function(){')
 de=s.index('async function v722CatchUpAfterFocus(){',ds)
 drain=s[ds:de]
 assert "if(wasVacation){" in drain
 assert "if(!m.error)v18369CaptureVacationReturn(state,m);" in drain
 assert drain.index("v53Sim.active=false;v53Sim.patching=false;v53Sim.syncing=false;") < drain.index("if(!m.error)v18369CaptureVacationReturn(state,m);")
 a=s.index('/* FUTBR_VACATION_RESUME_HANDOFF_18369')
 b=s.index('const v18366BaseVacationHeader=v624VacationHeaderHTML;',a)
 runtime=s[a:b].strip()
 code=FIXTURE+'\n'+runtime+'\n'+base+'\n'+TEST
 with tempfile.TemporaryDirectory() as temp:
  # Validate the complete shipped JavaScript, not merely the isolated
  # simulator stub: accidental literal backslash-n makes the whole game fail boot.
  engine_start=s.index('const Engine = (() => {')
  tag=s.rfind('<script',0,engine_start)
  if tag<0:raise RuntimeError('Original main game script element not found')
  opener=s.index('>',tag)+1
  closer=s.index('</script>',engine_start)
  if closer<=opener:raise RuntimeError('Original script closing tag absent')
  full=Path(temp)/'full-original-game-18369.js'
  full.write_text(s[opener:closer],encoding='utf-8')
  fullcheck=subprocess.run(['node','--check',str(full)],capture_output=True,text=True,timeout=90)
  if fullcheck.returncode:
   raise RuntimeError('18.369 full shipped JavaScript syntax invalid: '+fullcheck.stderr[-4000:])
  path=Path(temp)/'actual-original-simulator-after-vacation.js'
  path.write_text(code,encoding='utf-8')
  check=subprocess.run(['node','--check',str(path)],capture_output=True,text=True,timeout=25)
  if check.returncode:raise RuntimeError('JS syntax: '+check.stderr)
  run=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=50)
  if run.returncode:raise RuntimeError('Actual original V53 start regression: '+run.stderr+'\n'+run.stdout)
  report=json.loads(run.stdout.strip().splitlines()[-1])
 (root/'vacation-resume-18369-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
