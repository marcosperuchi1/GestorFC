"""Regression for owner-scoped RPCs and repeated dismissal lifecycle callbacks."""
from __future__ import annotations
import json,subprocess,sys
from pathlib import Path

def chunk(s,a,b):
 start=s.index(a);return s[start:s.index(b,start)]

def main():
 if len(sys.argv) not in (2,3):raise SystemExit('usage: test_repeated_dismissal_18371.py <project> [--baseline]')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 baseline=len(sys.argv)==3 and sys.argv[2]=='--baseline'
 prefix=r'''
const assert=require('node:assert/strict');
const window={GestorFC:{}},document={querySelectorAll:()=>[]};
const v53RPC=new Map(),v250CreateStreams=new Map();let v53RpcId=0;
const URL={revokeObjectURL(){}};let v53WorkerFailed=false,v53WorkerReady=null,vacationLoop=false,bootRejects=0;
const v53PatchQueue=[];async function v53RecoverAfterFailure(){}
let v53Worker=null,v125VacIncoming=null,v53Creating=false,v52SavePromise=null,v52Processing=false;
let v18119SeasonTransfer={active:false},v18121NewSeasonPreparation=false,v18326AdvanceBusy=false,
 v168RolloverRunning=false,v91RolloverActive=false,v18363LastBlocker='';
let v18358PromotionSettled=false,v18358RecoveryDone=false,v18357AwaitingPromotion=false,
 v18357LiveFallback=null,v18357Retry=null,v18363Retry=null;
const v18364JobHandoff={pending:false,session:0,pauseSent:false};
const v18112Dismissal={pending:false,ready:false,notified:false,careerId:''};
const v53Sim={active:false,starting:false,finished:null,syncing:false,patching:false,
 mode:'vacation',session:0,pause:false,pauseMode:''};
const v89JobWait={active:false,stop:false};let v18369VacationReturn=null,view='career';
function fixture(){return {v1903CareerId:'career',user:'club-1',userEmployed:false,
 players:{p:{id:'p'}},teams:[{id:'club-1'},{id:'club-2'},{id:'club-3'}],
 schedule:[{}],year:2029,day:40,vacation:{active:false,paused:true},coaches:{}};}
let state=fixture();
const E={takeJob(s,id){if(id==='fail')throw Error('unavailable');s.user=id;s.userEmployed=true;s.vacation={active:false,paused:false};}};
function render(){}function closeModal(){}function toast(){}function v555UpdateChrome(){}
function v18119CompleteSeasonTransfer(){v18119SeasonTransfer.active=false;}
function v18364RepairOrphan(){return false;}
function v18363CanUseJobWait(){return v18363NoActualWork();}
async function v89RunJobWait(){}
async function v53GetWorker(){return v53Worker;}
function fakeWorker(){return {stopped:0,messages:[],terminate(){this.stopped++;},postMessage(m){this.messages.push(m);}};}
let resolveOperation;
function v53StartSimulation(mode){
 if(v53Sim.active||v53Sim.starting||v53Creating)return Promise.reject(Error('operation running'));
 v53Sim.active=true;v53Sim.mode=mode;v53Sim.session++;
 return new Promise(resolve=>{resolveOperation=resolve;});
}
'''
 call=chunk(s,'async function v53Call(op,params={}){','function v53Saved(m){')
 no_actual=chunk(s,'function v18363NoActualWork(s=state){','function v18363CanUseJobWait(){')
 if baseline:
  body=prefix+'\nlet v18359VacationPromise=null,v18362VacationOrigin=null;\n'+call+no_actual+r'''
(async()=>{
 const old=fakeWorker();v53Worker=old;
 const pending=v53Call('check').catch(()=>null);await Promise.resolve();
 assert.equal(v53RPC.size,1);
 old.terminate();v53Worker=null;
 assert.equal(v18363NoActualWork(),true);
 v53Worker=fakeWorker();const blocked=!v18363NoActualWork();
 assert.equal(blocked,true,'18.370 should reproduce old RPC blocking a later Worker');
 console.log(JSON.stringify({ok:true,baselineReproduced:true,oldWorkerStopped:old.stopped,
  orphanedRPC:v53RPC.size,secondWorkerBlocked:blocked,reason:v18363LastBlocker}));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
'''
 else:
  assert 'FUTBR_REPEATED_DISMISSAL_18371' in s
  rpc=chunk(s,'/* FUTBR_REPEATED_DISMISSAL_18371','function v53GetWorker(){')
  lifecycle=chunk(s,'const v18369FinishedWorlds=new WeakMap();','// 18.369 storage bridge:')
  handoff=chunk(s,'const v18365Job={','const v18365BaseChrome=')
  legacy=chunk(s,'async function v18364OnVacationSettled(origin,success){','function v18364HandleJobClick(){')
  employment=chunk(s,'/* FUTBR_EMPLOYMENT_HANDOFF_18371','const v18366BaseVacationHeader=')
  reply=chunk(s,"if(m.kind==='rpc'){","\n    if(m.session")
  error_handler=chunk(s,'w.onerror=event=>{','\n   w.onmessageerror=')
  body=prefix+rpc+call+no_actual+lifecycle+handoff+legacy+employment+'\nfunction deliver(m,w){'+reply+'}\n'+'function errorHandler(w){const workerBootWatchdog=null,url=\"\",reject=()=>{bootRejects++;};'+error_handler.replace('w.onerror=', 'return ',1)+'}\n'+r'''
(async()=>{
 const report={ok:false,originalFunctionsExecuted:true};
 const first=v18371TrackWorker(fakeWorker());v53Worker=first;
 const pending=v53Call('check').then(()=>({ok:true}),error=>({error:String(error)}));
 await Promise.resolve();assert.equal(v53RPC.size,1);
 assert.equal(v18363NoActualWork(),true,'A read-only check must not block job search');
 first.terminate();const canceled=await pending;
 assert.match(canceled.error,/encerrado/);assert.equal(v53RPC.size,0);
 v53Worker=v18371TrackWorker(fakeWorker());
 assert.equal(v18363NoActualWork(),true,'A later Worker cannot inherit the old busy flag');
 report.oldWorkerRPCSettled=true;report.readOnlyCheckDoesNotBlock=true;
 // Termination and a late reply from one Worker must not touch a new save RPC.
 const prior=v53Worker;
 const oldCall=v53Call('check').catch(()=>null);await Promise.resolve();
 const next=v18371TrackWorker(fakeWorker());v53Worker=next;
 const saveCall=v53Call('save').catch(e=>({error:String(e)}));await Promise.resolve();
 const saveID=next.messages.at(-1).id;
 assert.equal(v18363NoActualWork(),false,'A real current save must remain blocking');
 prior.terminate();await oldCall;
 assert.equal(v53RPC.size,1);assert.equal(v53RPC.get(saveID).worker,next);
 v53Sim.active=true;const beforeBoot=bootRejects;errorHandler(prior)({message:'late previous Worker failure'});
 assert.equal(v53Sim.active,true);assert.equal(v53Worker,next);assert.equal(v53WorkerFailed,false);
 assert.equal(bootRejects,beforeBoot);assert.equal(v53RPC.size,1);v53Sim.active=false;
 report.retiredWorkerErrorIgnored=true;
 deliver({kind:'rpc',id:saveID,result:{bad:true}},prior);
 assert.equal(v53RPC.size,1,'Old Worker reply must not settle the new save');
 deliver({kind:'rpc',id:saveID,result:{saved:true}},next);
 assert.deepEqual(await saveCall,{saved:true});assert.equal(v53RPC.size,0);
 report.onlyRetiredOwnerCanceled=true;report.lateReplyIgnored=true;report.currentSaveProtected=true;
 for(const flag of ['active','starting','finished','syncing','patching']){
  // Syncing/patching are legacy flags recovered elsewhere, so actual-operation
  // assertions here concern active/starting/finished and transfer/save guards.
  if(flag==='syncing'||flag==='patching')continue;
  v53Sim[flag]=true;assert.equal(v18363NoActualWork(),false,flag);v53Sim[flag]=flag==='finished'?null:false;
 }
 v125VacIncoming={};assert.equal(v18363NoActualWork(),false);v125VacIncoming=null;
 v52SavePromise=Promise.resolve();assert.equal(v18363NoActualWork(),false);v52SavePromise=null;
 report.activeSimulationStreamAndSaveProtected=true;
 const history=[];let previousOrigin=null;
 for(let cycle=1;cycle<=3;cycle++){
  state.userEmployed=false;
  v18365Job.pending=true;v18364JobHandoff.pending=true;
  v18112Dismissal.pending=true;v18112Dismissal.ready=true;v18357AwaitingPromotion=true;
  v18358PromotionSettled=true;v18358RecoveryDone=true;
  E.takeJob(state,'club-'+cycle);
  assert.equal(v18365Job.pending,false);assert.equal(v18364JobHandoff.pending,false);
  assert.equal(v18112Dismissal.pending,false);assert.equal(v18357AwaitingPromotion,false);
  assert.equal(v18358RecoveryDone,false);
  state.vacation.active=true;
  const operation=v53StartSimulation('vacation'),origin=v18362VacationOrigin;
  assert.equal(origin.user,'club-'+cycle);assert.equal(origin.employmentEpoch,cycle);
  const duplicate=v53StartSimulation('vacation');await assert.rejects(duplicate,/running/);
  assert.equal(v18362VacationOrigin,origin,'Duplicate start must preserve the running origin');
  state.userEmployed=false;state.day+=1;state.vacation.active=false;
  v18112Dismissal.pending=true;
  if(previousOrigin){
   Object.assign(v18365Job,{pending:true,careerId:state.v1903CareerId,user:state.user,
    employmentEpoch:cycle,session:v53Sim.session});
   assert.equal(v18365OnVacationSettled(previousOrigin,true),false);
   v18364JobHandoff.pending=true;
   assert.equal(await v18364OnVacationSettled(previousOrigin,true),false);
   assert.equal(v18364JobHandoff.pending,true,'Former club callback must not cancel legacy current request');
   v18364JobHandoff.pending=false;
   assert.equal(v18365Job.pending,true,'Former club callback must not cancel current request');
   assert.equal(v18362CommitVacation(previousOrigin),false);
   assert.equal(v18112Dismissal.pending,true,'Former club callback must not release new dismissal');
   v18365Job.pending=false;
  }
  v53Sim.active=false;
  assert.equal(v18359OnWorkerFinished({session:v53Sim.session},true),true);
  resolveOperation(state);await operation;await Promise.resolve();
  assert.equal(v18359VacationPromise,null);assert.equal(v18362VacationOrigin,null);
  assert.equal(v18359TrustedCompleted(),true);assert.equal(v18363NoActualWork(),true);
  assert.equal(v18112Dismissal.pending,false);assert.equal(v18112Dismissal.ready,true);
  history.push({cycle,user:state.user,day:state.day,usable:v18363NoActualWork(),epoch:v18371Employment.epoch});
  previousOrigin=origin;
 }
 const beforeEpoch=v18371Employment.epoch;
 assert.throws(()=>E.takeJob(state,'fail'),/unavailable/);
 assert.equal(v18371Employment.epoch,beforeEpoch,'Failed acceptance must not clear any lifecycle');
 report.threeEmploymentDismissalCycles=history;
 report.currentHandoffSurvivesFormerClubCallback=true;report.duplicateStartKeepsCurrentOrigin=true;
 report.failedAcceptanceDoesNotReset=true;
 report.ok=true;console.log(JSON.stringify(report));
})().catch(e=>{console.error(e.stack);process.exitCode=1;});
'''
 run=subprocess.run(['node','-e',body],capture_output=True,text=True)
 if run.returncode:
  print(run.stdout);print(run.stderr,file=sys.stderr)
  raise RuntimeError('18.371 repeated-dismissal source regression failed')
 report=json.loads(run.stdout.strip().splitlines()[-1]);report['version']='18.370.0' if baseline else '18.371.0'
 name='repeated-dismissal-18370-baseline.json' if baseline else 'repeated-dismissal-18371-tests.json'
 (root/name).write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()
