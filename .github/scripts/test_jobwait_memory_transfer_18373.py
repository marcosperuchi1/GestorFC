"""Exercise the shipped UI handoff and original Worker in separate VM scopes.

The world fixtures are synthetic 2029 histories, not simulated past seasons.
The browser gate separately advances real fixtures with the complete Engine.
"""
from __future__ import annotations
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def between(s, start, end):
    a=s.index(start)
    return s[a:s.index(end,a)]


HARNESS = r'''
const assert=require('node:assert/strict'),vm=require('node:vm'),crypto=require('node:crypto').webcrypto;
const {MessageChannel}=require('node:worker_threads');
const payload=JSON.parse(require('node:fs').readFileSync(process.argv[2],'utf8'));
const clone=x=>structuredClone(x);
const window={GestorFC:{v172:{_finishJobWait(){window.__gfcV172JobWait=false;}}}},
 document={hidden:false,querySelector(){return null;},querySelectorAll(){return [];},getElementById(){return null;},activeElement:null},
 performance=require('node:perf_hooks').performance;
let state=null,saved=null,view='career',saveOK=true,saveStamp='',vacationLoop=false,vacationDelay=5,
 v53Creating=false,v143PostRankPending=false,v143NationalRepairToken=0,v143NationalRepairRunning=false,
 v53Sim={active:false,starting:false,session:0},v53Worker=null,v53WorkerReady=null,v53RPC=new Map(),
 v53PatchQueue=[],v53PatchScheduled=false,v125VacIncoming=null,v52Processing=false,
 v52SavePromise=null,v52SaveTimer=null,v52SaveDirty=false,v52PendingState=null,
 v52NotifySave=false,v52SaveWaiters=[],v52MarketIndex=null,v53PlayerIndex=null,
 v158ManualPrimePromise=null,v158ManualPrimeDay=-1,v158ManualPrimeYear=-1,
 v93VacCheckpointValid=true,v93VacCheckpointDay=-1,v93VacCheckpointYear=-1,v93CoachSaveTimer=0,
 v168DeferredRolloverSave=false,v18369VacationReturn=null,v18359FinishedWorld=null,v18357LiveFallback=null,
 v18119SeasonTransfer={active:false},v92SeasonReviewSync=false,v81RankCacheHold=null,
 v547SeasonIndexCache=new WeakMap(),v555CoachCache={},v555ShellState=null,v260ShellLockedState=null,
 v555MarketWarmJob=null,v555MarketWarmListJob=null,v555MarketWarmScheduled=false,v555DecorFrame=0,
 v5RenderedView=null,v131PendingVacationAck=0,v131VacationPaintTick=0,v131RankSnapshotCache=null,
 v18360SyncMetrics={players:0},v53Stats={patches:0,playerUpdates:0},v86RankCache={dirty:false},
 v18112Dismissal={pending:false},v89JobWait={active:false,stop:false,days:0};
const v555Perf={archiveYearsPacked:0,archivePlayersPacked:0};
const v168Stats={};
const STORE='gestor_fc_mundo_v205_clean',V171_FORMAT='GFC_SHARDED_171';
let disk=new Map(),owner=null,notices=[],messages=[],workers=[],apiCounts={},sequences=[],
 failStream=false,killAfterDay=0,stopAtDay=0,enableOffers=false,offerOpened=0,
 preparationGate=null,staleBoot=false,wrongBootCareer=false,dayGate=null,workerFailures=[],nextRpc=0;
const E={team:(s,id)=>(s.teams||[]).find(t=>String(t.id)===String(id)),
 human:s=>(s.teams||[]).find(t=>t.id===s.user),strength:(s,t)=>t.ovr??t.base,
 clamp:(x,a,b)=>Math.max(a,Math.min(b,x)),news:(s,title,body,kind)=>{s.news??=[];s.news.unshift({title,body,kind});},
 invalidateMarket(){},applyManagerSettings18371(s,envelope){if(envelope)s.v622Settings={...envelope.settings};},
 promotionOfferEnvelope18372:()=>null,validPromotionOffer18372:()=>false,
 adoptLegacyPromotionOffers18372(){},promotionProfile18372:()=>({eligible:false}),normName:x=>String(x||'')};
function v18371SettingsEnvelope(s=state){return s?{settings:s.v622Settings||{}}:null;}
function v18369CanStartFromReturnedVacation(){return false;}
function v18369ConsumeVacationReturn(){v18369VacationReturn=null;}
function v148EnsureNationalReady(){if(state?.v18373JobWaitPartial)throw Error('Maintenance on partial state');return false;}
function v5CrestsOut(){}function stopTimer(){}function render(){}function v53PaintStatus(){}
function v89PaintJobWait(){}function v555UpdateChrome(){}function v53RefreshView(){}
function v18356ReconcileRollover(){}function v18358SafeJobButtons(){return false;}
function v18363CanUseJobWait(){return true;}function v89HasNationalJob(){return !!state?.v640National?.userTeam;}
function v636CoachState(s){s.v636CoachOffers??=[];s.v636CoachOfferMeta??={lastOfferDay:-99,rejected:{}};return s;}
function v636PendingCoachOffers(s){if(!s)return [];return (s.v636CoachOffers||[]).filter(o=>o.status==='pending'&&o.year===s.year&&o.expiresDay>=s.day&&E.team(s,o.teamId));}
function v636CleanCoachOffers(s){s.v636CoachOffers=v636PendingCoachOffers(s);}
function v636ClubOVR(s,t){return v56ClubOverall(s,t);}
function v636OfferHash(text){return v56Hash(text);}
function v636CoachOfferModal(){assert.ok(!v18373JobMemory.partial);assert.ok(Object.keys(state.players).length>0);offerOpened++;}
function v93ScheduleCoachDecisionSave(){}function toast(text){notices.push(String(text));}
function persist(){assert.ok(!v18373JobMemory.partial,'UI may never persist its light mirror');return Promise.resolve();}
function v52FlushSave(){throw Error('Unexpected full save in first-day start');}
async function v53Prepare(){throw Error('Unexpected rollover');}
function v53Saved(){saveOK=true;}
function v18360SyncStart(){}function v18360SyncCollection(){}function v18360SyncUpdate(){}
function v18360SyncEnd(){}function v82FinalizeRankAfterSync(){}function v18359OnWorkerFinished(){}
function v18119BeginSeasonTransfer(){v18119SeasonTransfer.active=true;}
function v18119CompleteSeasonTransfer(){v18119SeasonTransfer.active=false;}
function v18119FailSeasonTransfer(message){notices.push('TRANSFER_FAIL '+message);}
function v18369PaintOnly(fn){return fn();}
function v18369CaptureVacationReturn(){}function v18112MarkDismissal(){}
function v18369FailPatchDelivery(error,finish){workerFailures.push(String(error));
 const w=v53Worker;w?.terminate();v53Worker=null;v53WorkerReady=null;
 v53Sim.active=false;v53Sim.starting=false;v53Sim.finished=null;v53PatchQueue.length=0;
 finish?.reject(error);
}
/* INJECT_REAL_UI_CODE */
const rawStart=v53StartSimulation;
v53StartSimulation=async function(mode,opts){
 const result=await rawStart(mode,opts);
 if(enableOffers)v636GenerateCoachOffer(state,false);
 if(stopAtDay&&state.day>=stopAtDay)v89JobWait.stop=true;
 if(killAfterDay&&state.day>=killAfterDay){v53Worker?.terminate();v53Worker=null;v53WorkerReady=null;killAfterDay=0;}
 return result;
};
const decodeStored=new Function('read',payload.workerPlayerCodec+'\n'+payload.workerArchiveCodec+'\n'+payload.workerLegacyArchive+'\n'+payload.workerReader+'\nreturn decode;')(
 async key=>clone(disk.get(key)));

function fixture(){
 const s={v1903CareerId:'career-2029-owner',futbrSaveId:'save-2029',userCoachId:'me',user:'old',
  userEmployed:false,year:2029,day:12,lastDay:11,seed:103,seasonDone:false,manager:'Fixture',
  players:{},teams:[],coaches:{me:{id:'me',clubId:null,reputation:70,unemployedSince:{year:2029,day:10},jobs:[{club:'old',year:2026}]}},
  schedule:Array.from({length:80},(_,i)=>({type:'league',label:'J'+i,fixtures:[]})),
  competitions:{league:{id:'league',stats:{}}},competitionStats:{league:{}},allTimeStats:{},
  v538CareerArchive:{},v555CareerArchive:{},scorerArchive:[],transfers:[],retirements:[],history:[],
  internationalHistory:[],v735NationalArchive:{},crestOverrides:{old:'data:image/png;base64,'+'Ab12/'.repeat(25000)},v640National:{userTeam:null,teams:{}},
  v622Settings:{renewals:'board',offerPopup:false,matchSpeed:'90',revision18371:9},
  v548Access:{plan:'premium'},v636CoachOffers:[],v636CoachOfferMeta:{lastOfferDay:-99,rejected:{}},
  v636CoachCareer:[{year:2026,clubId:'old',games:38,points:70}],v636CareerTracker:null,
  vacation:{active:false,paused:true,remaining:0},news:[],unknownFutureHistory:{years:{}},unknownLongText:'archive text '.repeat(5000),live:null};
 for(let n=0;n<1400;n++){
  const id='p'+n;s.players[id]={id,name:'Player '+n,age:25,clubId:'old',apps:n%30,goals:n%12,skills:{pace:61,finish:68},honors538:[{year:2026,kind:'league'}]};
  s.competitionStats.league[id]={apps:n%30,goals:n%12};s.allTimeStats[id]={apps:n+30,goals:n%45};
 }
 for(let y=2026;y<=2028;y++){
  s.v538CareerArchive[y]={};s.v555CareerArchive[y]={n:['Old Club','Other'],p:{}};
  const scores={year:y,competitions:{league:{}}};
  for(let n=0;n<1400;n++){
   const id='p'+n;s.v538CareerArchive[y][id]=[{teamId:'old',teamName:'Old Club',apps:30,goals:n%9}];
   s.v555CareerArchive[y].p[id]='old|30|'+(n%9)+'|7|2|0';
   scores.competitions.league[id]={apps:30,goals:n%9,assists:7};
  }
  s.scorerArchive.push(scores);s.unknownFutureHistory.years[y]={rows:{}};
  for(let n=0;n<1000;n++)s.unknownFutureHistory.years[y].rows['future'+n]={score:n,title:'Unknown historical field '+n};
 }
 s.unknownFutureHistory.emptyObject={};s.unknownFutureHistory.sparse=new Array(7);s.unknownFutureHistory.sparse[3]='kept';
 Object.defineProperty(s.unknownFutureHistory,'__proto__',{value:{literal:true},enumerable:true,writable:true,configurable:true});
 for(let i=0;i<25;i++)s.teams.push({id:i?'club'+i:'old',name:i?'Club '+i:'Old Club',short:'C'+i,
  country:'bra',division:i%3+1,base:60+i%8,ovr:62+i%10,fanPressure:i*3,stats:{p:12,w:4,d:3,l:5},
  roster:Array.from({length:35},(_,j)=>'p'+((i*35+j)%1400)),academy:['p900'],balance:123456+i});
 return s;
}
function buildManifest(s){
 const root={},collections={},keys=new Set(['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats',
  'v538CareerArchive','v555CareerArchive','scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive','crestOverrides']);
 for(const key in s)if(!keys.has(key))root[key]=clone(s[key]);
 for(const key of keys){const value=s[key];if(value==null)continue;const chunks=[];let rows=[];
  for(const id in value)if(Object.prototype.hasOwnProperty.call(value,id)){
   rows.push([id,clone(value[id])]);if(rows.length>=90){const ck='fixture:'+key+':'+chunks.length;disk.set(ck,rows);chunks.push(ck);rows=[];}
  }
  if(rows.length){const ck='fixture:'+key+':'+chunks.length;disk.set(ck,rows);chunks.push(ck);}
  collections[key]={isArray:Array.isArray(value),length:Array.isArray(value)?value.length:0,keys:chunks};
 }
 const m={format:V171_FORMAT,version:1,revision:7,token:'fixture-2029-day12',year:s.year,day:s.day,root,collections};
 disk.set(STORE,m);return m;
}
function tokenFrom(m){return {...v18373JobIdentity(m.root),token:m.token,revision:m.revision};}
function installRuntime(){
 window.GestorFC.memoryStorage18373={
  async ensureCheckpoint(){apiCounts.ensure++;sequences.push('ensure');if(preparationGate)await preparationGate;
   const token=tokenFrom(disk.get(STORE));assert.equal(token.day,state.day);return token;},
  releaseIdleWorker(reason){sequences.push('release:'+reason);if(v53Sim.active||v53Sim.starting||v53Sim.syncing||v53Sim.patching)return false;
   v53Worker?.terminate();v53Worker=null;v53WorkerReady=null;return true;},
  setWorkerOwner(token){assert.equal(state.day,token.day);assert.equal(Object.keys(state.players).length,1400);assert.equal(owner,null);
   owner=clone(token);sequences.push('owner');return true;},
  clearWorkerOwner(token){assert.deepEqual(token,owner);assert.ok(!state.v18373JobWaitPartial);owner=null;sequences.push('clear-owner');return true;},
  async restoreOwnerCheckpoint(token){assert.deepEqual(token,owner);apiCounts.recovery++;
   this.releaseIdleWorker('restore-owner');const m=disk.get(STORE);assert.ok(m.year>=token.year&&m.day>=token.day);
   assert.equal(m.root.v1903CareerId,token.careerId);return decodeStored(clone(m));}
 };
 window.GestorFC.v170={release:()=>window.GestorFC.memoryStorage18373.releaseIdleWorker('legacy-release')};
 // Keep the actual legacy cleanup chain. It cancels queues and terminates an
 // idle simulation Worker, so it cannot run during the new return RPC.
 window.GestorFC.v100={repair:{stopBackground:()=>v100StopBackground(true)}};
 window.GestorFC.v168={purge:()=>{apiCounts.legacyPurge++;v168StopBackground();return v168DropStateCaches(state);}};
}
function handleWorkerMessage(w,m){
 if(w.closed)return;
 if(m.kind==='storage-request'){
  Promise.resolve().then(()=>{
   let result=null;
   if(m.operation==='read'){
    result=clone(disk.get(m.key));
    if(m.key===STORE&&w.firstStoreRead){w.firstStoreRead=false;
     if(staleBoot)result.token='wrong-token';if(wrongBootCareer)result.root.v1903CareerId='other-career';}
   }else if(m.operation==='raw-write')disk.set(m.key,clone(m.value));
   else if(m.operation==='raw-write-many')for(const e of m.entries)disk.set(e.key,clone(e.value));
   else if(m.operation==='raw-delete')disk.delete(m.key);
   else if(m.operation==='raw-delete-many')for(const key of m.keys)disk.delete(key);
   else throw Error('Unhandled storage operation '+m.operation);
   w.deliver({op:'storage-reply',id:m.id,result:result??null});
  }).catch(e=>w.deliver({op:'storage-reply',id:m.id,error:String(e)}));return;
 }
 if(m.kind==='rpc'){
  const p=v53RPC.get(m.id);if(p){v53RPC.delete(m.id);m.error?p.reject(Error(m.error)):p.resolve(m.result);}return;
 }
 if(m.kind==='ready')return;
 if(m.kind==='saved'){v53Saved(m);return;}
 if(m.kind==='save-error'){notices.push('SAVE_ERROR '+m.error);return;}
 if(m.session!==v53Sim.session)return;
 if(m.kind.startsWith('vac-sync-')||m.kind==='jobwait-progress-18373'||m.kind==='finished'||m.kind==='vac-checkpoint-error'){
  v53PatchQueue.push(m);v53DrainPatches();return;
 }
}
function spawnWorker(){
 assert.equal(Object.keys(state.players).length,0,'UI players must be released before Worker construction');
 assert.equal(state.v538CareerArchive,undefined);assert.equal(state.v555CareerArchive,undefined);assert.equal(state.scorerArchive,undefined);
 assert.ok(owner);sequences.push('boot');
 const worker={closed:false,firstStoreRead:true,context:null,deliver(m){
  if(this.closed)return;this.context.__message=m;
  vm.runInContext('self.onmessage({data:__message})',this.context);
 },postMessage(m){
  if(this.closed)throw Error('Worker closed');
  if(m.op==='simulate'){
   assert.equal('state' in m,false,'No first or later job day may clone state');
   assert.equal(m.mode,'dayfast');assert.equal(m.jobWaitAuto,true);
   messages.push(clone(m));
  }
  this.deliver(m);
 },terminate(){
  this.closed=true;sequences.push('terminate');
   for(const [id,p] of v53RPC)if(p.worker===this){v53RPC.delete(id);p.reject(Error('O Worker desta consulta foi encerrado.'));}
 }};
 let retainedNational=null;
 const engine={...E,
  applyPromotionOfferEnvelope18372(){},applyManagerSettings18371(){},
  availableJobs:s=>enableOffers?s.teams.filter(t=>t.id!==s.user).slice(0,18):[],
  async advanceDayAsync(s){if(dayGate)await dayGate;s.lastDay=s.day;s.day++;s.seed++;
   s.players.p0.apps++;s.allTimeStats.p0.apps++;s.competitionStats.league.p0.apps++;
   s.unknownFutureHistory.lastAdvance=s.day;if(s.day>=s.schedule.length)s.seasonDone=true;},
  syncEligibility(){},clamp:E.clamp};
 const context=vm.createContext({console,performance,Engine:engine,
  National:{before(s){retainedNational=s;return null;},after(){},release(){retainedNational=null;apiCounts.nationalRelease++;}},
  setTimeout,clearTimeout,TextEncoder,TextDecoder,Blob,Response,CompressionStream,DecompressionStream,
  crypto,btoa,atob,self:{postMessage(m,transfer=[]){
   if(worker.closed)return;
   if(failStream&&m.kind==='vac-sync-part'&&m.key==='players'){failStream=false;throw Error('INTENTIONAL_STREAM_FAILURE');}
   const copied=structuredClone(m,{transfer});
   if(copied.kind==='vac-sync-part'){
    apiCounts.streamParts++;apiCounts.maxRows=Math.max(apiCounts.maxRows,copied.rows?.length||0);
    apiCounts.maxBytes=Math.max(apiCounts.maxBytes,copied.bytes?.byteLength||0);
   }
   queueMicrotask(()=>handleWorkerMessage(worker,copied));
  }}});
 worker.context=context;workers.push(worker);v53Worker=worker;
 vm.runInContext(payload.worker+'\nv53WorkerMain();',context);
 return worker;
}
async function v53GetWorker(){return v53Worker||spawnWorker();}
async function v53Call(op,params={}){
 const w=await v53GetWorker(),id=++nextRpc;
 assert.ok(!('state' in params),'No full state RPC');
 return new Promise((resolve,reject)=>{v53RPC.set(id,{resolve,reject,worker:w,op});w.postMessage({op,id,...params});});
}
function reset(){
 for(const w of workers)w.terminate();workers=[];disk=new Map();state=fixture();saved=state;buildManifest(state);
 state.v538CareerArchive=clone(state.v538CareerArchive);owner=null;
 notices=[];messages=[];sequences=[];apiCounts={ensure:0,recovery:0,nationalRelease:0,streamParts:0,maxRows:0,maxBytes:0,legacyPurge:0};
 v53Worker=null;v53WorkerReady=null;v53RPC=new Map();v53PatchQueue=[];v53PatchScheduled=false;
 v53Sim={active:false,starting:false,session:0};v125VacIncoming=null;v52Processing=false;v53Creating=false;
 v89JobWait={active:false,stop:false,days:0};v18119SeasonTransfer.active=false;v53Stats={patches:0,playerUpdates:0};
 v52SaveDirty=false;v52SavePromise=null;v52PendingState=null;saveOK=true;
 v18373JobMemory.phase='idle';v18373JobMemory.partial=false;v18373JobMemory.token=null;v18373JobMemory.lastError='';
 v18370JobSave.commits=0;v18370JobSave.failed=0;v18370JobSave.busy=false;
 failStream=false;killAfterDay=0;stopAtDay=21;enableOffers=false;offerOpened=0;preparationGate=null;staleBoot=false;wrongBootCareer=false;dayGate=null;workerFailures=[];
 installRuntime();
}
async function waitUntil(predicate){const until=Date.now()+10000;while(!predicate()){if(Date.now()>until)throw Error('Timed out waiting for fixture');await new Promise(r=>setTimeout(r,1));}}
function compareHistory(original,restored){
 for(const key of ['v538CareerArchive','v555CareerArchive','scorerArchive','history','internationalHistory','v735NationalArchive','crestOverrides'])assert.deepEqual(restored[key],original[key],key+' must retain every historical row');
 assert.deepEqual(restored.unknownFutureHistory.years,original.unknownFutureHistory.years);
 assert.equal(restored.unknownFutureHistory.sparse.length,7);assert.equal(0 in restored.unknownFutureHistory.sparse,false);
 assert.deepEqual(restored.unknownFutureHistory.__proto__,{literal:true});
 assert.deepEqual(restored.v622Settings,original.v622Settings);
 assert.equal(restored.unknownLongText,original.unknownLongText);
}
(async()=>{
 // Reproduce the legacy helper's exact ownership mismatch: dayfast has
 // settled, but the Worker is still the sole owner during the return RPC.
 reset();const retiredByLegacy={closed:false,terminate(){this.closed=true;}};
 v53Worker=retiredByLegacy;v18373JobMemory.phase='returning';
 v18310ReleaseOldVacationState();
 assert.equal(retiredByLegacy.closed,true,'Actual legacy purge retires a non-simulating return owner');
 assert.equal(apiCounts.legacyPurge,1);
 // Ordinary vacation still performs its original cleanup while active.
 reset();const vacationWorker={closed:false,terminate(){this.closed=true;}};
 v53Worker=vacationWorker;v53Sim.active=true;v18310ReleaseOldVacationState();
 assert.equal(vacationWorker.closed,false);assert.equal(apiCounts.legacyPurge,1);
 assert.equal(Object.keys(state.players).length,0);v53Sim.active=false;
 reset();let original=clone(state);const old={closed:false,terminate(){this.closed=true;sequences.push('old-worker-terminated');}};v53Worker=old;
 await v89RunJobWait();
 assert.equal(apiCounts.recovery,0,'Return must complete through its stream, never hide cleanup failure with recovery');
 assert.equal(apiCounts.legacyPurge,0,'A partial mirror needs no legacy world/Worker purge');
 assert.equal(state.day,21);assert.equal(v89JobWait.days,9);assert.equal(messages.length,9);
 assert.equal(apiCounts.ensure,1);assert.equal(v18370JobSave.commits,3);
 assert.equal(messages[0].loadSaved,true);assert.equal(messages[0].useResident,false);
 assert.ok(messages.slice(1).every(m=>m.useResident&&m.jobWaitResident&&!m.loadSaved));
 assert.ok(old.closed);assert.ok(sequences.indexOf('old-worker-terminated')<sequences.indexOf('boot'));
 assert.ok(sequences.indexOf('owner')<sequences.indexOf('boot'));assert.equal(owner,null);
 assert.equal(v18373JobMemory.partial,false);assert.equal(workers.length,1);assert.ok(workers[0].closed);
 assert.equal(state.players.p0.apps,9);assert.equal(state.allTimeStats.p0.apps,39);
 assert.equal(state.unknownFutureHistory.lastAdvance,21);compareHistory(original,state);
 assert.ok(apiCounts.maxRows<=64);assert.ok(v18373JobMemory.lastReturn.maxRows<=384);
 assert.ok(apiCounts.nationalRelease>0);assert.equal(workerFailures.length,0);
 const normal={days:messages.length,checkpointDays:[16,20,21],maxRows:apiCounts.maxRows,maxPlayerBytes:apiCounts.maxBytes};
 const durable=await decodeStored(clone(disk.get(STORE)));assert.equal(durable.day,21);compareHistory(original,durable);

 // Skipping destructive legacy cleanup is allowed only for the exact owned
 // mirror; ordinary vacation and mismatched return packets cannot use it.
 reset();const returnRoot={v1903CareerId:state.v1903CareerId,userCoachId:state.userCoachId,
  user:state.user,futbrSaveId:state.futbrSaveId,userEmployed:false,year:state.year,day:state.day},
  returnStart={jobwait18373:true,root:returnRoot,year:state.year,day:state.day};
 assert.equal(v18373ReturningOwnMirror({}),false);
 assert.throws(()=>v18373ReturningOwnMirror(returnStart),/posse atuais/);
 v18373JobMemory.token=tokenFrom(disk.get(STORE));v18373JobMemory.partial=true;
 v18373JobMemory.phase='returning';state.v18373JobWaitPartial=true;
 assert.equal(v18373ReturningOwnMirror(returnStart),true);
 for(const key of ['v1903CareerId','userCoachId','user','futbrSaveId','year','day','userEmployed']){
  const wrong={...returnStart,root:{...returnRoot,[key]:key==='userEmployed'?true:typeof returnRoot[key]==='number'?returnRoot[key]+1:'other'}};
  assert.throws(()=>v18373ReturningOwnMirror(wrong),/posse atuais/,key+' mismatch must reject');
 }
 assert.throws(()=>v18373ReturningOwnMirror({...returnStart,day:state.day+1}),/posse atuais/);
 v18373JobMemory.phase='worker';assert.throws(()=>v18373ReturningOwnMirror(returnStart),/posse atuais/);
 v18373JobMemory.phase='returning';delete state.v18373JobWaitPartial;
 assert.throws(()=>v18373ReturningOwnMirror(returnStart),/posse atuais/);

 // Use the original OVR sorting and unemployed offer policy on a complete
 // fixture and on the tiny Worker mirror; choose exactly the same offer.
 reset();const full=clone(state),light=clone(state);full.day=18;light.day=18;
 const raw=full.teams.filter(t=>t.id!==full.user).slice(0,18);
 const expectJobs=raw.slice().sort((a,b)=>{
  const salt=full.year*997+full.day*131;
  return (v56ClubOverall(full,b)+(b.fanPressure||0)*.035+(v56Hash(b.id+'|'+salt)%1000)/500)-
   (v56ClubOverall(full,a)+(a.fanPressure||0)*.035+(v56Hash(a.id+'|'+salt)%1000)/500);
 }).slice(0,6).map(t=>t.id);
 light.v18373JobWaitPartial=true;light.v18373JobCandidates=raw.map(t=>t.id);light.v18373JobOVR={};
 for(const t of full.teams)light.v18373JobOVR[t.id]=v56ClubOverall(full,t);
 light.teams=light.teams.map(v18373LightTeam);light.players={};
 assert.deepEqual(v56AvailableJobs(light).map(t=>t.id),expectJobs);
 for(let day=14;day<40;day++){
  full.day=light.day=day;full.v636CoachOffers=[];light.v636CoachOffers=[];
  v636GenerateCoachOffer(full,false);v636GenerateCoachOffer(light,false);
  assert.deepEqual(light.v636CoachOffers,full.v636CoachOffers,'Full and partial policy must issue identical offers');
 }
 reset();enableOffers=true;stopAtDay=0;original=clone(state);
 await v89RunJobWait();await new Promise(r=>setTimeout(r,45));
 assert.ok(state.v636CoachOffers.length);assert.equal(offerOpened,1);assert.ok(messages.length>=2&&messages.length<10);
 assert.equal(disk.get(STORE).day,state.day);assert.equal(state.v636CoachOffers[0].expiresDay,state.v636CoachOffers[0].day+4);
 compareHistory(original,state);

 // Refusing a card schedules its old UI save for later. Its compact decision
 // must still beat a same-day manifest when search starts immediately.
 reset();stopAtDay=13;
 disk.get(STORE).root.v636CoachOffers=[{id:'old-invitation',teamId:'club1',year:2029,day:12,expiresDay:16,status:'pending'}];
 state.v636CoachOffers=[];state.v636CoachOfferMeta.rejected.club1=12;
 state.news.unshift({title:'Recent UI decision',text:'No delayed full save was required'});
 await v89RunJobWait();
 assert.equal(state.v636CoachOffers.length,0);assert.equal(state.v636CoachOfferMeta.rejected.club1,12);
 assert.equal(state.news[0].title,'Recent UI decision');assert.equal(apiCounts.recovery,0);

 // STOP can interrupt preparation before memory ownership or a new Worker.
 reset();let release;preparationGate=new Promise(r=>{release=r;});const preparing=v89RunJobWait();
 await waitUntil(()=>v18373JobMemory.phase==='preparing');await v89RunJobWait();release();await preparing;
 assert.equal(messages.length,0);assert.equal(workers.length,0);assert.equal(owner,null);assert.equal(Object.keys(state.players).length,1400);

 // Stop/save waits for the actual in-flight day and the complete return.
 reset();let advance;dayGate=new Promise(r=>{advance=r;});const running=v89RunJobWait();
 await waitUntil(()=>v18373JobMemory.partial&&messages.length===1);
 assert.equal(v18373GuardJobAction({dataset:{action:'player'}}),true);
 assert.equal(v18373GuardJobAction({dataset:{action:'v89-job-wait'}}),false);
 assert.equal(v18373GuardJobAction({dataset:{action:'nav',view:'competitions'}}),true);
 let saveReady=false;const joined=v18373FinishForSave().then(()=>{saveReady=true;assert.ok(Object.keys(state.players).length===1400);});
 assert.equal(saveReady,false);advance();await running;await joined;assert.equal(state.day,13);assert.equal(owner,null);

 // Wrong manifest token/career cannot be decoded or replay an old day.
 for(const which of ['staleBoot','wrongBootCareer']){
  reset();original=clone(state);if(which==='staleBoot')staleBoot=true;else wrongBootCareer=true;
  await v89RunJobWait();assert.equal(state.day,12);assert.equal(v89JobWait.days,0);assert.equal(apiCounts.recovery,1);
  assert.equal(owner,null);assert.equal(v18373JobMemory.partial,false);compareHistory(original,state);
  assert.ok(notices.some(t=>t.includes('checkpoint da busca')));
 }

 // A failed destructive stream restores the last complete checkpoint by the
 // direct reader, never exposing an empty or partially received UI world.
 reset();original=clone(state);stopAtDay=13;failStream=true;
 await v89RunJobWait();assert.equal(state.day,13);assert.equal(apiCounts.recovery,1);assert.equal(owner,null);
 compareHistory(original,state);assert.equal(state.players.p0.apps,1);assert.equal(v125VacIncoming,null);
 reset();original=clone(state);killAfterDay=13;
 await v89RunJobWait();assert.equal(apiCounts.recovery,1);assert.equal(state.day,12);compareHistory(original,state);
 assert.equal(owner,null);assert.equal(v53RPC.size,0);

 // An old migration may be suspended between its 1,200-record batches when
 // jobwait trims the SAME root. It must release its captured season instead
 // of recreating a packed archive (or throwing on the deleted old container).
 reset();const legacy={};for(let i=0;i<1201;i++)legacy['legacy'+i]=[{teamId:'old',teamName:'Old Club',apps:30,goals:4}];
 state.v538CareerArchive={2025:legacy};state.v555CareerArchive={};
 const migration=v555MigrateArchivesAsync();
 state.v18373JobWaitPartial=true;delete state.v538CareerArchive;delete state.v555CareerArchive;
 v18373JobMemory.partial=true;v18373JobMemory.phase='worker';
 await migration;
 assert.equal(state.v555CareerArchive,undefined);assert.equal(v555ArchiveMigration,null);
 assert.equal(v555ArchiveMigrationTimer,0);assert.equal(v555Perf.archiveYearsPacked,0);
 v18373JobMemory.partial=false;v18373JobMemory.phase='preparing';
 delete state.v18373JobWaitPartial;state.v538CareerArchive={2025:legacy};state.v555CareerArchive={};
 assert.equal(await v555MigrateArchivesAsync(),false);v555ScheduleArchiveMigration(0);
 assert.equal(v555ArchiveMigrationTimer,0);assert.equal(state.v555CareerArchive[2025],undefined);
 v18373JobMemory.phase='idle';await v555MigrateArchivesAsync();
 assert.equal(Object.keys(state.v555CareerArchive[2025].p).length,1201);
 assert.equal(state.v538CareerArchive[2025],undefined);assert.equal(v555Perf.archiveYearsPacked,1);
 reset();state.v538CareerArchive={2025:legacy};state.v555CareerArchive={};
 const oldMigration=v555MigrateArchivesAsync(),baseEnsure=window.GestorFC.memoryStorage18373.ensureCheckpoint;
 let ensuredAfterMigration=false;
 window.GestorFC.memoryStorage18373.ensureCheckpoint=async function(){
  assert.equal(v555ArchiveMigration,null,'Captured archive must settle before checkpoint/worker boot');
  ensuredAfterMigration=true;return baseEnsure.call(this);
 };
 v89JobWait.stop=true;await v18373BeginJobWait();await oldMigration;
 assert.equal(ensuredAfterMigration,true);assert.equal(workers.length,0);
 assert.equal(state.v555CareerArchive[2025],undefined);await v18373EndJobWait();v18373JobWaitSettled();

 console.log(JSON.stringify({ok:true,version:'18.373.0',
  actualBaseStartAndLoopExecuted:true,originalWorkerInSeparateScope:true,
  zeroFullWorldJobwaitMessages:true,uiReleasedBeforeWorkerBoot:true,verifiedExactCheckpointToken:true,
  residentNineDayLoop:true,boundedFourDayCheckpoints:true,singleCompleteWorldOwner:true,
  exactOfferPolicyPreserved:true,fullWorldRestoredBeforeOffer:true,losslessHistoricalReturn:true,
  unsavedCoachDecisionsPreserved:true,
  oldAndPackedArchiveYearsPreserved:true,scorerAndUnknownTreesBounded:true,partialUIGuarded:true,
  stopDuringPreparationAndSimulation:true,saveJoinAwaitsCompleteReturn:true,
  mismatchedTokenAndCareerRejected:true,failedStreamRecoversDurableWorld:true,
  lostWorkerRecoveryDoesNotCloneWorld:true,inFlightArchiveMigrationCannotRebuildMirror:true,
  archiveMigrationResumesAfterReturn:true,archiveMigrationJoinedBeforeWorkerBoot:true,
  actualLegacyCleanupChainExecuted:true,returnOwnerSurvivesLegacyCleanup:true,
  exactOwnedMirrorRequiredAtReturn:true,normalReturnUsesNoRecovery:true,ordinaryVacationCleanupPreserved:true,normal}));
})().catch(error=>{console.error(error?.stack||String(error));console.error(JSON.stringify({phase:v18373JobMemory.phase,
 notices,sequences,workerFailures,queue:v53PatchQueue.length,sim:v53Sim,owner}));process.exit(1);});
'''


def main():
    root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
    assert 'FUTBR_JOBWAIT_SINGLE_OWNER_18373' in s
    worker=between(s,'function v53WorkerMain(){','\n\n\nconst v18191uPlayerFields=')
    tree=between(worker,'/* Bounded lossless return','/* FUTBR_JOBWAIT_SINGLE_OWNER_18373_WORKER')
    ui=between(s,'/* FUTBR_JOBWAIT_SINGLE_OWNER_18373\n','const v18370JobSave=')
    loop=between(s,'const v18370JobSave={','const v89BaseCareerPage=careerPage;')
    drainer=between(s,'v53DrainPatches=function(){','\nasync function v722CatchUpAfterFocus(')
    base=between(s,'async function v53StartSimulation(mode,options={}){','runVacation=async function')
    jobs=between(s,'function v56ClubOverall(s,t){','E.availableJobs=v56AvailableJobs;')+'\nE.availableJobs=v56AvailableJobs;'
    jobs='const v56OriginalAvailableJobs=s=>s.teams.filter(t=>t.id!==s.user).slice(0,18);\n'+jobs
    final_ovr="v56ClubOverall=function(s,t){return t?E.strength(s,t):0;};"
    assert s.rindex(final_ovr)<s.index('const v18373BaseClubOverall=')
    assert s.count('E.availableJobs=v56AvailableJobs;')==1
    jobs+='\n'+final_ovr+'\n'+between(s,'const v18373BaseClubOverall=','const v18373BaseAct=')
    create=between(s,'function v636CreateCoachOffer(s,t,reason){','function v636GenerateCoachOffer(')
    generator=between(s,'v636GenerateCoachOffer=function(s,afterUserMatch=false){', '// Display the last completed vacation cash change')
    generator='let v636GenerateCoachOffer;const v93BaseGenerateCoachOffer=()=>0;\n'+generator
    codec=between(s,'const v18191uPlayerFields=','// 5.3: one authoritative simulation')
    vacation_rows=between(s,'function v18310VacationRows(m){','function v18310ReleaseOldVacationState(){')
    release_old=between(s,'function v18310ReleaseOldVacationState(){','\nconst v53Base=')
    cleanup168=between(s,'function v168CancelIdle(handle){','function v168AcademyTarget(')
    cleanup100=between(s,' function v100CancelIdleHandle(x){',' const v100BaseNationalRepair=')
    migration=between(s,'let v555ArchiveMigration=null,v555ArchiveMigrationTimer=0;','const v555BaseActualClubsByYear=')
    worker_codec=between(worker,'const v18191wPlayerFields=',' const V171_FORMAT=')
    archive_codec=between(worker,'/* FUTBR_PACKED_ARCHIVE_PATHS_18373','const v18352NestedArchiveKeys=')
    archive_legacy=between(worker,'function v18352ApplyArchivedRow(dst,entry){','const v18343HistoricalKeys=')
    reader="const V171_FORMAT='GFC_SHARDED_171';\n"+between(worker,' async function v171DecodeManifest(x){',' \n/* FUTBR_ARCHIVE_COPY_ON_WRITE_18343')
    assert base.index('v18373OwnedJob?false:v148EnsureNationalReady')<base.index('const w=await v53GetWorker')
    assert 'msg.jobWaitCheckpoint18373={...v18373JobMemory.token}' in base
    assert worker.index('v18373VerifyJobCheckpoint(stored,')<worker.index('world=await decode(stored);stored=null;')
    release=worker.index('if(lowMemoryVacation){message.state=null;v18373ReleaseWorkerGraph();}')
    assert release<worker.index("self.postMessage({kind:'finished',session,error:failure,day:finalDay",release)
    assert "if(v53Worker!==w||v18371RetiredWorkers.has(w))return;" in s
    assert 'if(v18373GuardJobAction(el))return true;' in s
    assert 'if(active&&v18373JobMemory.partial){finish?.reject(error);return;}' in s
    assert s.index('/* FUTBR_JOBWAIT_PARTIAL_UI_GUARDS_18373')<s.index('<!-- v43 clean: v130 ranking warmup removed -->')
    data={'worker':worker,'tree':tree,'uiHelpers':ui,'uiLoop':loop,'drainer':drainer,
        'baseStart':base,'uiJobs':jobs,'offerCreate':create,'offerGenerator':generator,
        'uiPlayerCodec':codec,'uiVacationRows':vacation_rows,'workerPlayerCodec':worker_codec,
        'workerArchiveCodec':archive_codec,'workerLegacyArchive':archive_legacy,'workerReader':reader}
    # Parse each actual inline JavaScript, excluding JSON/catalog data scripts.
    scripts=[]
    for match in re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script\s*>',s,re.I):
        if re.search(r'type\s*=\s*["\'](?:application/[^"\']+|importmap)',match[1],re.I):continue
        scripts.append(match[2])
    with tempfile.TemporaryDirectory() as d:
        p=Path(d);(p/'payload.json').write_text(json.dumps(data),encoding='utf-8')
        real_ui='\n'.join([codec,vacation_rows,release_old,cleanup168,cleanup100,tree,ui,jobs,create,generator,base,loop,drainer,migration])
        (p/'test.js').write_text(HARNESS.replace('/* INJECT_REAL_UI_CODE */',real_ui),encoding='utf-8')
        (p/'scripts.json').write_text(json.dumps(scripts),encoding='utf-8')
        syntax=subprocess.run(['node','-e',"const fs=require('fs'),vm=require('vm');for(const s of JSON.parse(fs.readFileSync(process.argv[1])))new vm.Script(s)",str(p/'scripts.json')],text=True,capture_output=True,timeout=45)
        if syntax.returncode:raise RuntimeError(syntax.stderr)
        run=subprocess.run(['node',str(p/'test.js'),str(p/'payload.json')],text=True,capture_output=True,timeout=150)
        if run.returncode:raise RuntimeError(run.stderr[-12000:]+'\n'+run.stdout[-3000:])
        report=json.loads(run.stdout.strip().splitlines()[-1])
    report['inlineScriptsParsed']=len(scripts)
    (root/'jobwait-memory-transfer-18373-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
