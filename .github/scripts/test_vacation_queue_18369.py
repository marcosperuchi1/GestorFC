from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path

# These are queue/transport regressions, not a replacement for the browser
# integration with the original Engine and actual simulation Worker.
FIXTURE=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}},document={hidden:false,querySelector:()=>header};
let header={hidden:false,dataset:{},innerHTML:''};
let state=null,saved=null,view='dashboard',v53PatchScheduled=false;
let v53PatchQueue=[],v53Sim={},v53Worker=null,v53WorkerReady=null;
let v53Creating=false,v125VacIncoming=null,v52SavePromise=null;
let v131PendingVacationAck=0,v143PostRankPending=false,v92SeasonReviewSync=false;
let v52Processing=false,v52PendingState=null,v52MarketIndex=null,vacationLoop=false;
let v18119SeasonTransfer={active:false},v18112Dismissal={pending:false};
let v53Stats={patches:0,playerUpdates:0},v131RankSnapshotCache=null;
let v131VacationPaintTick=0,v93VacCheckpointValid=false,v81RankCacheHold=null;
let posts=[],failures=[],terminations=0,settlements=0,dayWrites=0;
let throwStatus=false,throwHeader=false,throwRefresh=false,throwToast=false,throwData=false;
let v53DrainPatches;
const E={invalidateMarket(){},human(){return {balance:0}}};
function v53PaintStatus(){if(throwStatus)throw Error('TEST_STATUS_PAINT');}
function v624VacationHeaderHTML(){if(throwHeader)throw Error('TEST_HEADER_PAINT');return '';}
function v53RefreshView(){if(throwRefresh)throw Error('TEST_FULL_REPAINT');}
function toast(){if(throwToast)throw Error('TEST_ERROR_TOAST');}
function v18112MarkDismissal(){}
function v18359OnWorkerFinished(){}
function v18119CompleteSeasonTransfer(){v18119SeasonTransfer.active=false;}
function v18119FailSeasonTransfer(){v18119SeasonTransfer.active=false;}
function v18360SyncEnd(){}
function v18360SyncFinish(){}
function v18360SyncStart(){}
function v18360SyncCollection(){}
function v18360SyncBatch(){}
function v18360SyncPart(){}
function v18360PaintSync(){}
function v82ApplyRankLiveDelta(){}
function v624PaintVacationHeader(){}
function v208PaintVacationLiveDay(){}
function v208RefreshVacationMetrics(){if(throwRefresh)throw Error('TEST_VACATION_REPAINT');}
function v81IncrementalCompetitionUpdate(){}
function v1882RefreshTransferActivityDOM(){}
function v53ApplyRow(dst,id,data){if(throwData)throw Error('TEST_DATA_APPLICATION');dst[id]=data;}
function reset(mode='nextmatch'){
 header={hidden:false,dataset:{},innerHTML:''};
 state={v1903CareerId:'queue-regression',year:2026,day:2,user:'t0',
  userEmployed:true,vacation:{active:false,paused:true},players:{p:{}},
  teams:[{id:'t0'}],schedule:[{fixtures:[]}]};
 view='dashboard';v53PatchScheduled=false;v53PatchQueue=[];
 v53Sim={session:7,mode,active:true,starting:false,syncing:false,patching:false,finished:null};
 v125VacIncoming=null;v53Creating=false;v52SavePromise=null;
 v131PendingVacationAck=0;v143PostRankPending=false;v18119SeasonTransfer.active=false;
 v18112Dismissal.pending=false;v53Stats={patches:0,playerUpdates:0};
 posts=[];failures=[];terminations=0;settlements=0;dayWrites=0;
 throwStatus=false;throwHeader=false;throwRefresh=false;throwToast=false;throwData=false;
 v18369VacationReturn=null;
 Object.assign(v18369ResumeStats,{captured:0,paintErrors:0,queueErrors:0});
 const worker={postMessage:m=>posts.push(m),terminate(){terminations++;},
  onerror(event){
   // Observe routing to the original Worker's failure boundary. No retry or
   // successful completion is allowed after data application fails.
   failures.push({message:event.message,hadPending:!!v53Sim.finished,active:v53Sim.active});
   const finish=v53Sim.finished;v53Sim.finished=null;
   v53Sim.active=false;v53Sim.starting=false;v53PatchQueue.length=0;
   this.terminate();v53Worker=null;v53WorkerReady=null;
   finish?.reject(Error(event.message));
  }};
 v53Worker=worker;v53WorkerReady=Promise.resolve(worker);
}
function operation(){
 return new Promise((resolve,reject)=>{
  v53Sim.finished={resolve:s=>{settlements++;resolve(s);},reject:e=>{settlements++;reject(e);}};
 });
}
function send(...messages){
 for(const m of messages)v53PatchQueue.push({session:7,...m});
 v53DrainPatches();
}
const tick=()=>new Promise(r=>setTimeout(r,5));
async function idle(){
 for(let i=0;i<200;i++){if(!v53PatchScheduled&&!v53PatchQueue.length)return;await tick();}
 throw Error('queue did not become idle');
}
async function bounded(p){
 let timeout;
 try{return await Promise.race([p,new Promise((_,reject)=>{timeout=setTimeout(()=>reject(Error('completion Promise remained pending')),1200);})]);}
 finally{clearTimeout(timeout);}
}
"""

TEST=r"""
(async()=>{
 // Reproduce the original permanent stall: one vac-live message, an optional
 // full redraw throws, and the Worker must still receive its final live ACK.
 reset('vacation');throwRefresh=true;
 send({kind:'vac-live',seq:41,root:{day:3},playerRows:[['p',{rating:77}]]});
 await idle();
 assert.equal(state.day,3);assert.equal(state.players.p.rating,77);
 assert.deepEqual(posts,[{op:'vac-live-ack',seq:41}]);
 assert.equal(v131PendingVacationAck,0);assert.equal(v53PatchScheduled,false);
 assert.equal(v18369ResumeStats.queueErrors,0);assert.equal(v18369ResumeStats.paintErrors,1);
 send({kind:'vac-live',seq:42,root:{day:4},playerRows:[['p',{rating:78}]]});
 await idle();
 assert.equal(state.day,4);assert.equal(posts.length,2);
 assert.equal(posts[1].seq,42,'a later message must be accepted after the failed repaint');

 // Genuine terminal delivery settles once even though its final repaint throws.
 reset('vacation');throwRefresh=true;
 const vacation=operation();
 send({kind:'finished'});
 assert.equal(await bounded(vacation),state);await idle();
 assert.equal(settlements,1);assert.equal(terminations,1);
 assert.equal(v53Sim.finished,null);assert.equal(v53Sim.active,false);
 assert.equal(v18369ResumeStats.captured,1,'a terminal event must never replay');
 assert.equal(v18369ResumeStats.queueErrors,0);

 // An error toast is presentation. It cannot steal the original rejection.
 reset();throwToast=true;
 const errored=operation();
 send({kind:'finished',error:'EXPECTED_ENGINE_FAILURE'});
 await assert.rejects(()=>bounded(errored),/EXPECTED_ENGINE_FAILURE/);await idle();
 assert.equal(settlements,1);assert.equal(v53Sim.finished,null);
 assert.equal(v18369ResumeStats.queueErrors,0);

 // A next-match progress header can fail before the authoritative sync arrives.
 // The sync mutation and final settlement must each run exactly once.
 reset();throwStatus=true;throwHeader=true;
 let actualDay=2;
 Object.defineProperty(state,'day',{get:()=>actualDay,set:v=>{dayWrites++;actualDay=v;},enumerable:true});
 const nextmatch=operation();
 send({kind:'nextmatch-day',day:3,steps:1},
      {kind:'nextmatch-sync',day:3,year:2026,steps:1,user:'t0',userEmployed:true},
      {kind:'finished'});
 assert.equal(await bounded(nextmatch),state);await idle();
 assert.equal(state.day,3);assert.equal(dayWrites,1);assert.equal(settlements,1);
 assert.ok(v18369ResumeStats.paintErrors>=2);assert.equal(failures.length,0);

 // Never treat a broken data delta as a cosmetic problem or ACK/drop it and
 // continue to a success event. Route to native recovery and reject instead.
 reset('vacation');throwData=true;
 const broken=operation();
 send({kind:'patch-part',key:'players',rows:[['p',{rating:90}]]},
      {kind:'vac-live',seq:99,root:{day:9}},
      {kind:'finished'});
 await assert.rejects(()=>bounded(broken),/TEST_DATA_APPLICATION/);await idle();
 assert.equal(failures.length,1);assert.equal(failures[0].hadPending,true);
 assert.equal(settlements,1);assert.equal(state.players.p.rating,undefined);
 assert.equal(posts.length,0,'failed data must not be acknowledged');
 assert.equal(v18369ResumeStats.queueErrors,1);
 assert.equal(v53PatchQueue.length,0);assert.equal(v53PatchScheduled,false);

 // Old sessions cannot complete a current operation.
 reset();const current=operation();
 send({kind:'finished',session:6},{kind:'nextmatch-sync',day:3},{kind:'finished'});
 assert.equal(await bounded(current),state);await idle();
 assert.equal(settlements,1);assert.equal(state.day,3);
 console.log(JSON.stringify({ok:true,version:'18.369.0',originalFinalDrainExecuted:true,
  vacLiveAckSurvivesPaintException:true,nextMatchSyncSurvivesPaintException:true,
  finishedPromiseSettlesOnce:true,errorToastCannotLoseRejection:true,
  appliedMessagesNeverReplayed:true,realDataFailureRejectsWithoutAck:true,
  dataFailureRoutesToOriginalRecovery:true,queueOwnershipAlwaysReleased:true,
  staleSessionIgnored:true,transportFixtureNotGameEngine:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
"""

def run(root: Path):
 s=(root/'src/index.html').read_text(encoding='utf-8')
 assert 'FUTBR_VACATION_RESUME_HANDOFF_18369' in s
 a=s.index('/* FUTBR_VACATION_RESUME_HANDOFF_18369')
 b=s.index('const v18366BaseVacationHeader=v624VacationHeaderHTML;',a)
 runtime=s[a:b]
 a=s.rindex('v53DrainPatches=function(){')
 b=s.index('async function v722CatchUpAfterFocus(){',a)
 drain=s[a:b]
 assert 'v18369PaintOnly' in drain and 'v18369FailPatchDelivery' in drain
 assert 'v53PatchQueue.unshift(' not in drain
 assert '}finally{' in drain
 with tempfile.TemporaryDirectory() as tmp:
  script=Path(tmp)/'original-final-drain-regression.js'
  script.write_text(FIXTURE+'\n'+runtime+'\n'+drain+'\n'+TEST,encoding='utf-8')
  result=subprocess.run(['node',str(script)],capture_output=True,text=True,timeout=25)
  if result.returncode:
   raise RuntimeError('18.369 original final queue regression failed:\n'+result.stderr[-12000:]+'\n'+result.stdout[-4000:])
  report=json.loads(result.stdout.strip().splitlines()[-1])
 (root/'vacation-queue-18369-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
 return report

if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: test_vacation_queue_18369.py <project>')
 run(Path(sys.argv[1]))
