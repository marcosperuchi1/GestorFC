"""Keep Worker requests and dismissal handoffs scoped to their actual owner."""
from __future__ import annotations
import json,sys
from pathlib import Path

MARK='FUTBR_REPEATED_DISMISSAL_18371'
RPC=r'''/* FUTBR_REPEATED_DISMISSAL_18371
   A status RPC can still be queued when a vacation Worker sends finished.
   Its termination must settle its own requests; an old request must never
   become a permanent busy flag when another club starts another Worker. */
const v18371RPCStats={retiredRequests:0,workersTracked:0};
const v18371RetiredWorkers=new WeakSet();
function v18371RetireWorkerRequests(worker,error=Error('O Worker desta consulta foi encerrado.')){
 if(!worker)return 0;
 let retired=0;
 for(const [id,pending] of v53RPC){
  if(pending.worker!==worker)continue;
  v53RPC.delete(id);v250CreateStreams.delete(id);retired++;
  try{pending.reject(error);}catch(e){}
 }
 v18371RPCStats.retiredRequests+=retired;
 return retired;
}
function v18371TrackWorker(worker){
 const terminate=worker.terminate.bind(worker);
 worker.terminate=function(){
  v18371RetiredWorkers.add(worker);
  v18371RetireWorkerRequests(worker);
  return terminate();
 };
 v18371RPCStats.workersTracked++;
 return worker;
}
function v18371BlockingWorkerRequest(){
 if(!v53Worker)return false;
 for(const pending of v53RPC.values()){
  // Unowned records are conservatively busy. All new calls below carry an
  // owner. A read-only status check cannot mutate the world or its save.
  if((!pending.worker||pending.worker===v53Worker)&&pending.op!=='check')return true;
 }
 return false;
}
'''
EMPLOYMENT=r'''/* FUTBR_EMPLOYMENT_HANDOFF_18371
   A career can contain many employment spells. Career ID alone does not
   identify the club whose vacation/dismissal callback is completing. */
const v18371Employment={epoch:0,resets:0,lastClub:'',lastCareer:''};
function v18371SameEmployment(origin,s=state){
 return !!origin&&!!s&&origin.careerId===String(s.v1903CareerId||'')&&
  origin.user===String(s.user||'')&&origin.employmentEpoch===v18371Employment.epoch;
}
function v18371NewEmployment(s=state){
 if(s!==state||!s?.userEmployed||!s.user)return false;
 v18371Employment.epoch++;v18371Employment.resets++;
 v18371Employment.lastClub=String(s.user);v18371Employment.lastCareer=String(s.v1903CareerId||'');
 // Remove only the previous job's queued UI work. The simulation, save and
 // incoming stream guards continue to protect actual operations.
 if(v18365Job.timer!==null){clearTimeout(v18365Job.timer);v18365Job.timer=null;}
 if(v18363Retry!==null){clearTimeout(v18363Retry);v18363Retry=null;}
 if(v18357Retry!==null){clearTimeout(v18357Retry);v18357Retry=null;}
 v18365Job.pending=false;v18365Job.session=0;v18365Job.last='new-employment';
 v18364JobHandoff.pending=false;v18364JobHandoff.session=0;
 v18364JobHandoff.pauseSent=false;v18364JobHandoff.last='new-employment';
 v18359FinishedWorld=null;v18369VacationReturn=null;v18357LiveFallback=null;
 v18357AwaitingPromotion=false;v18358PromotionSettled=false;v18358RecoveryDone=false;
 Object.assign(v18112Dismissal,{pending:false,ready:false,notified:false,
  year:0,day:0,careerId:String(s.v1903CareerId||'')});
 if(!v53Sim?.active&&!v53Sim?.starting&&!v53Sim?.finished&&
    !v53Sim?.syncing&&!v53Sim?.patching&&!v125VacIncoming&&!v52SavePromise){
  v18359VacationPromise=null;v18362VacationOrigin=null;
 }
 return true;
}
const v18371BaseTakeJob=E.takeJob;
E.takeJob=function(s,id,...args){
 const result=v18371BaseTakeJob.call(this,s,id,...args);
 if(s?.userEmployed&&String(s.user)===String(id))v18371NewEmployment(s);
 return result;
};
window.GestorFC.repeatedDismissal18371={status:()=>({version:'18.371.0',
 ...v18371Employment,...v18371RPCStats,
 currentWorkerRequests:[...v53RPC.values()].filter(p=>p.worker===v53Worker).length,
 blockingWorkerRequest:v18371BlockingWorkerRequest(),
 pendingHandoff:!!v18365Job.pending,year:state?.year,day:state?.day})};
'''

def once(s,old,new,label):
 n=s.count(old)
 if n!=1:raise RuntimeError(f'18.371 {label}: expected one anchor, got {n}')
 return s.replace(old,new,1)

def patch(s):
 if MARK in s:raise RuntimeError('18.371 dismissal patch applied twice')
 for marker in ('FUTBR_BOUNDED_JOBWAIT_18370','FUTBR_LIFECYCLE_SCOPE_18369_BEGIN'):
  if marker not in s:raise RuntimeError('Missing dependency '+marker)
 s=once(s,'function v53GetWorker(){',RPC+'\nfunction v53GetWorker(){','worker ownership helpers')
 s=once(s,"const w=v53Worker=new Worker(url,{name:'GestorFC-Mundo-53'});",
  "const w=v53Worker=v18371TrackWorker(new Worker(url,{name:'GestorFC-Mundo-53'}));",'track actual Worker')
 s=once(s,'v53RPC.set(id,{resolve,reject});','v53RPC.set(id,{resolve,reject,worker:w,op});','associate RPC owner')
 s=once(s,'const result=await new Promise((resolve,reject)=>{v53RPC.set(id,{resolve,reject,worker:w,op});',
  "if(w!==v53Worker||v18371RetiredWorkers.has(w)){v250CreateStreams.delete(id);throw Error('O Worker desta consulta já foi encerrado.');}\n const result=await new Promise((resolve,reject)=>{v53RPC.set(id,{resolve,reject,worker:w,op});",'do not register a late call on a retired Worker')
 s=once(s,"w.onerror=event=>{clearTimeout(workerBootWatchdog);try{URL.revokeObjectURL(url);}catch(e){}v53WorkerFailed=true;",
  "w.onerror=event=>{clearTimeout(workerBootWatchdog);try{URL.revokeObjectURL(url);}catch(e){}if(v53Worker!==w){v18371RetireWorkerRequests(w);return;}v53WorkerFailed=true;",'ignore retired Worker error')
 s=once(s,'for(const p of v53RPC.values())p.reject(error);v53RPC.clear();reject(error);',
  'v18371RetireWorkerRequests(w,error);reject(error);','error settles only its Worker requests')
 s=once(s,"if(m.kind==='rpc'){const p=v53RPC.get(m.id);if(p){",
  "if(m.kind==='rpc'){const p=v53RPC.get(m.id);if(p&&p.worker===w){",'ignore another Worker reply')
 s=once(s,"(typeof v53RPC!=='undefined'&&v53RPC?.size>0&&\n     typeof v53Worker!=='undefined'&&!!v53Worker)",
  'v18371BlockingWorkerRequest()','busy guard current Worker only')
 s=once(s,"!(typeof v53RPC!=='undefined'&&v53RPC?.size>0);",
  '!v18371BlockingWorkerRequest();','legacy handoff current Worker only')
 s=once(s,'const v18366BaseVacationHeader=v624VacationHeaderHTML;',
  EMPLOYMENT+'\nconst v18366BaseVacationHeader=v624VacationHeaderHTML;','reset on successful employment')
 s=once(s,'async function v18364OnVacationSettled(origin,success){\n if(!v18364JobHandoff.pending)return false;',
  'async function v18364OnVacationSettled(origin,success){\n if(!v18364JobHandoff.pending)return false;\n if(!v18371SameEmployment(origin))return false;', 'legacy queued callback employment identity')
 s=once(s,"if(!origin||!s||s.userEmployed!==false||s.v640National?.userTeam||\n    origin.careerId!==String(s.v1903CareerId||'')||",
  "if(!origin||!s||s.userEmployed!==false||s.v640National?.userTeam||\n    !v18371SameEmployment(origin,s)||",'late completion employment identity')
 s=once(s,"const origin={careerId:String(state?.v1903CareerId||''),\n   employed:state?.userEmployed===true};",
  """// A duplicate action must not replace the origin of an already-running
  // vacation before the original start guard rejects that duplicate.
  if(v53Sim?.active||v53Sim?.starting||v53Creating)return v18359BaseStart(mode,...args);
  const origin={careerId:String(state?.v1903CareerId||''),
   user:String(state?.user||''),employmentEpoch:v18371Employment.epoch,
   employed:state?.userEmployed===true};""",'vacation employment token')
 s=once(s,"String(state.v1903CareerId||'')===v18365Job.careerId&&\n  (!v18365Job.session",
  "String(state.v1903CareerId||'')===v18365Job.careerId&&\n  String(state.user||'')===v18365Job.user&&\n  v18365Job.employmentEpoch===v18371Employment.epoch&&\n  (!v18365Job.session",'queued request employment identity')
 s=once(s,"v18365Job.careerId=String(state.v1903CareerId||'');\n v18365Job.session=",
  "v18365Job.careerId=String(state.v1903CareerId||'');\n v18365Job.user=String(state.user||'');\n v18365Job.employmentEpoch=v18371Employment.epoch;\n v18365Job.session=",'capture queued employment')
 s=once(s,"if(!origin||String(origin.careerId||'')!==v18365Job.careerId){\n  v18365Job.pending=false;v18365Job.last='origin-changed';return false;\n }",
  """if(!v18371SameEmployment(origin)||
    String(origin.careerId||'')!==v18365Job.careerId||
    origin.user!==v18365Job.user||origin.employmentEpoch!==v18365Job.employmentEpoch){
  // A late callback from another club cannot cancel the current request.
  return false;
 }""",'ignore stale settled callback')
 s=once(s,"const EDITION='18.370.0';","const EDITION='18.371.0';",'edition')
 s=once(s,"window.GestorFC.version='18.370.0';window.GestorFC.visualVersion='18.370.0';",
  "window.GestorFC.version='18.371.0';window.GestorFC.visualVersion='18.371.0';",'visual version')
 return s

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_repeated_dismissal_18371.py <project>')
 root=Path(sys.argv[1]);file=root/'src/index.html'
 file.write_text(patch(file.read_text(encoding='utf-8')),encoding='utf-8')
 report={'ok':True,'version':'18.371.0','workerOwnedRPC':True,'retiredRequestsSettled':True,
  'statusChecksDoNotBlockJobSearch':True,'activeMutationsRemainProtected':True,
  'employmentScopedHandoff':True,'resetAfterSuccessfulClubChange':True,
  'lateFormerClubCallbacksIgnored':True}
 (root/'repeated-dismissal-18371-install.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report),flush=True)
if __name__=='__main__':main()
