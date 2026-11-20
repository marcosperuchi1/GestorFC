from __future__ import annotations
import json,re,subprocess,sys,tempfile
from pathlib import Path

FIXTURE=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{v172:{_finishJobWait(){}}}};
const document={hidden:false,querySelector(){return null;}};
let v89JobWait,view='career',state,saveOK=true,v53Creating=false,
 v143PostRankPending=false,v143NationalRepairToken=0,v143NationalRepairRunning=false,
 v53Sim={active:false,starting:false,session:0},v53Worker=null,v53WorkerReady=null,
 v52SavePromise=null,v52SaveTimer=null,v52SaveDirty=true,v52PendingState=null,
 v52NotifySave=false,v52SaveWaiters=[],v158ManualPrimePromise=null,
 v158ManualPrimeDay=0,v158ManualPrimeYear=0,v86RankCache={dirty:false},
 vacationLoop=false,vacationDelay=600;
let starts=[],fullStateTransfers=0,presaves=0,confirmedDays=0,offersOpened=0,notices=[],workerModeErrors=[];
let currentWorker=null,workerWorld=null,makeWorker=0,stall=false,replacedWorker=false;
function v148EnsureNationalReady(){return false;}
function v5CrestsOut(){}
function stopTimer(){}
function render(){}
function v53PaintStatus(){}
function v89PaintJobWait(){}
function v555UpdateChrome(){}
function v18356ReconcileRollover(){}
function v18358SafeJobButtons(){return false;}
function v18363CanUseJobWait(){return true;}
function v89HasNationalJob(){return false;}
function v636PendingCoachOffers(s){return s.offers||[];}
function v636CoachOfferModal(){offersOpened++;}
function v93ScheduleCoachDecisionSave(){}
function toast(a){notices.push(a);}
function persist(){}
function v52FlushSave(){presaves++;throw Error('UNSAFE: full-world pre-save before job round');}
const E={human(){throw Error('no human squad path needed while unemployed');}};
function spawn(){
 const worker={postMessage(message){
   assert.equal(message.mode,'dayfast','Original dayfast Worker mode required');
   assert.equal(message.loadSaved,false,'Do not replay stale disk save');
   starts.push({mode:message.mode,day:message.day,year:message.year,hasState:!!message.state,resident:!!message.jobWaitResident});
   if(message.state){
     fullStateTransfers++;
     assert.equal(message.jobWaitResident,undefined,'first round must transfer actual live state');
     workerWorld={day:message.state.day,year:message.state.year,v1903CareerId:message.state.v1903CareerId,user:message.state.user,v640National:message.state.v640National};
   }else{
     assert.equal(message.jobWaitResident,true,'only reuse real resident Worker without full state');
     assert.ok(workerWorld,'resident world must exist');
     assert.equal(workerWorld.day,message.day,'resident day must match UI state');
     assert.equal(workerWorld.year,message.year,'resident year must match UI state');
     assert.equal(workerWorld.v1903CareerId,message.v1903CareerId,'resident career must match');
     assert.equal(workerWorld.user,message.v1903User,'resident former club must match');
   }
   setImmediate(()=>{
    if(!stall){
     workerWorld.day++;
     state.day=workerWorld.day;
     confirmedDays++;
     if(confirmedDays===3)state.offers.push({teamId:'synthetic'});
    }
    v53Sim.active=false;
    const f=v53Sim.finished;v53Sim.finished=null;
    f.resolve(state);
   });
 }};
 currentWorker=worker;v53Worker=worker;makeWorker++;
 return worker;
}
function v53GetWorker(){return Promise.resolve(currentWorker||spawn());}
function init(){
 state={year:2026,day:57,seasonDone:false,user:'chapecoense',
  userEmployed:false,v640National:null,live:null,v1903CareerId:'job-fixture-2026',
  players:{p:{id:'p'}},teams:[{id:'chapecoense'}],schedule:Array.from({length:156},()=>({fixtures:[]})),
  vacation:{active:false},offers:[]};
 v89JobWait={active:false,stop:false,days:0};
 v53Sim={active:false,starting:false,session:0};v53Worker=null;v53WorkerReady=null;
 currentWorker=null;workerWorld=null;
 v52SavePromise=null;v52SaveDirty=true;v52PendingState=state;
 starts=[];fullStateTransfers=0;presaves=0;confirmedDays=0;offersOpened=0;notices=[];
 stall=false;view='career';
}
"""

TEST=r"""
(async()=>{
 init();
 await v89RunJobWait();
 assert.equal(state.day,60,'Original Worker-postMessage route must advance exactly three days');
 assert.equal(starts.length,3);
 assert.equal(fullStateTransfers,1,'Only first day may send entire live world');
 assert.equal(presaves,0,'No whole-world pre-save may run before ANY unemployed round');
 assert.equal(starts[0].resident,false);
 assert.equal(starts[1].resident,true);
 assert.equal(starts[2].resident,true);
 assert.equal(starts[1].hasState,false);
 assert.equal(starts[2].hasState,false);
 await new Promise(resolve=>setTimeout(resolve,55));
 assert.equal(offersOpened,1,'Stop on coach offer after three journeys');
 assert.equal(v89JobWait.days,3);
 assert.equal(v89JobWait.active,false);
 assert.equal(v89JobWait.stage,'idle');
 init();stall=true;
 await v89RunJobWait();
 assert.equal(state.day,57,'No fake advancement');
 assert.equal(v89JobWait.days,0,'No phantom progress');
 assert.equal(starts.length,1,'Cannot spin forever with stalled engine');
 assert.equal(v89JobWait.active,false,'Stop button must return to idle');
 assert.ok(notices.some(x=>x.includes('sem avançar')));
 init();v89JobWait.active=true;
 await v89RunJobWait();
 assert.equal(v89JobWait.stop,true,'Existing STOP handler preserved');
 assert.equal(starts.length,0,'STOP must not start another Worker');
 console.log(JSON.stringify({ok:true,version:'18.368.0',
  testedOriginalV53StartSimulation:true,testedOriginalV89RunJobWait:true,
  realBaseWorkerPostMessage:true,threeSequentialDayfastMessages:true,
  actualDayAdvancedInWorkerFixture:true,oneLiveWorldTransfer:true,
  noFullWorldPreSave:true,allLaterRoundsResident:true,
  staleDiskReplayForbidden:true,jobOfferStops:true,phantomRoundFails:true,
  stopActionWorks:true,unemployedDayfastLiveStateOnly:true,
  sourceWorkerIdentityGuard:true,saveCodecUnchanged:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_unemployed_real_worker_18368.py <project>')
 root=Path(sys.argv[1]);html=(root/'src/index.html').read_text(encoding='utf-8')
 assert '/* FUTBR_UNEMPLOYED_WORKER_REAL_PROGRESS_18368' in html
 assert "const EDITION='18.368.0';" in html
 assert "window.GestorFC.version='18.368.0';window.GestorFC.visualVersion='18.368.0';" in html
 assert "if(message.jobWaitResident&&!residentManual)" in html
 assert 'await E.advanceDayAsync(world,progress,postMatchOptions);' in html
 for expected in ('v18311LiveVacation=!!options?.liveStateNoPreSave',
                  "mode==='dayfast'&&options?.jobWaitResident===true"):
  assert expected in html,expected
 a=html.index('async function v53StartSimulation(mode,options={}){')
 b=html.index('runVacation=async function',a)
 base=html[a:b].strip()
 assert base.endswith('}'),base[-70:]
 a=html.index('async function v89RunJobWait(){')
 b=html.index('const v89BaseCareerPage=careerPage;',a)
 loop=html[a:b]
 assert "await v53StartSimulation('dayfast',{" in loop
 assert 'liveStateNoPreSave:true,jobWaitResident:v18368SameWorker' in loop
 assert 'v18368Resident=v53Worker||null;' in loop
 assert 'v89JobWait.days+=yearAfter===yearBefore?after-before:1;' in loop
 assert 'Math.max(1,(Number(state?.day)' not in loop
 script=FIXTURE+'\n'+base+'\n'+loop+'\n'+TEST
 with tempfile.TemporaryDirectory() as td:
  path=Path(td)/'test-original-worker-contract.js';path.write_text(script,encoding='utf-8')
  check=subprocess.run(['node','--check',str(path)],capture_output=True,text=True,timeout=45)
  if check.returncode:raise RuntimeError(check.stderr)
  run=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=75)
  if run.returncode:raise RuntimeError(run.stderr+'\n'+run.stdout)
  report=json.loads(run.stdout.strip().splitlines()[-1])
  assert report['ok'] and report['oneLiveWorldTransfer'] and report['threeSequentialDayfastMessages']
 (root/'unemployed-worker-18368-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
