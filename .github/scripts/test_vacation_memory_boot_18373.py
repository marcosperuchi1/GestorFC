"""Exercise vacation boot with the shipped writer, start command and Worker.

Only the isolated storage/transport boundary, rendering and sporting fixture
step are substituted. Synthetic historical rows do not represent played years.
The boot assertions also run on an unpatched source, so the old world transfer
fails behaviorally instead of merely failing a marker check.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def between(source, start, end):
    begin = source.index(start)
    return source[begin:source.index(end, begin)]


NODE = r'''
'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),
 crypto=require('node:crypto'),performance=require('node:perf_hooks').performance;
const code=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const KEY='gestor_fc_mundo_v205_clean',clone=x=>structuredClone(x),
 digest=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const historyKeys=['v538CareerArchive','v555CareerArchive','scorerArchive','history','internationalHistory','v735NationalArchive'];
function history(s){return Object.fromEntries(historyKeys.map(k=>[k,digest(s[k])]));}
function fixture({year=2029,day=8,national=''}={}){
 const s={v1903CareerId:'vacation-boot-career',futbrSaveId:'vacation-named-save',user:'t1',userCoachId:'me',
  userEmployed:!national,year,day,lastDay:day-1,seed:123,seasonDone:false,manager:'Fixture',
  players:{},teams:[{id:'t1',name:'Club One',coachId:'me',base:70,balance:100000,fanPressure:40,
   stats:{p:8,w:3,d:2,l:3},roster:[],academy:[],lineup:['p0','p1']},
   {id:'t2',name:'Club Two',coachId:'other',base:68,balance:90000,stats:{p:8,w:3,d:2,l:3},roster:[],academy:[]}],
  coaches:{me:{id:'me',clubId:national?null:'t1',pressure:10,reputation:60},other:{id:'other',clubId:'t2',reputation:50}},
  schedule:Array.from({length:30},(_,i)=>({type:'league',fixtures:[{id:'f'+i,home:'t1',away:'t2',competition:'league'}]})),
  competitions:{league:{id:'league',name:'Fixture League'}},competitionStats:{league:{}},allTimeStats:{},
  vacation:{active:false,paused:true,remaining:0,completed:0},news:[],transfers:[],coachMoves:[],
  history:[{year:2026,champion:'t1'}],internationalHistory:[{year:2027,winner:'t2'}],
  v538CareerArchive:{2025:{p0:[{goals:2,apps:15,teamId:'t1'}]}},v555CareerArchive:{},scorerArchive:[],
  v735NationalArchive:{2027:{winner:'BRA'}},crestOverrides:{},
  v640National:{userTeam:national||null,teams:national?{[national]:{code:national,name:national,coach:{id:'me'},roster:['p0']}}:{},playerStats:{}},
  v622Settings:{renewals:'board',offerPopup:true},v636CoachOffers:[],v636CoachOfferMeta:{rejected:{}},
  v636CoachCareer:[],v636CareerTracker:null};
 for(let i=0;i<160;i++){
  const id='p'+i;s.players[id]={id,name:'Player '+i,age:23,clubId:i<80?'t1':'t2',skills:{pace:68,finish:64},
   contract:2031,fitness:100,apps:i%15,goals:i%4,unknown:{keep:i}};
  s.teams[i<80?0:1].roster.push(id);s.allTimeStats[id]={apps:80+i,goals:i%17};
  s.competitionStats.league[id]={id,apps:8,goals:i%4,clubs:{t1:'Club One'}};
 }
 for(const y of [2026,2027,2028]){
  const packed={n:['Club One','Club Two'],p:{}},scorers={};
  for(let i=0;i<120;i++){packed.p['p'+i]='0|30|'+(i%5);scorers['p'+i]={apps:30,goals:i%5,clubs:{t1:'Club One'}};}
  s.v555CareerArchive[y]=packed;s.scorerArchive.push({year:y,competitions:{league:scorers}});
 }
 return s;
}

function environment(options={}){
 const disk=new Map(),events=[],messages=[],workers=[],probes=[],notices=[];
 let failCommit=false,failShard=false,beforeWrite=null,mutateMessage=null,mutateWorkerManifest=null,
  captureOnly=false,ui=null,workerId=0,holdNextYield=false,heldYield=null;
 function uiSetTimeout(callback,delay,...args){
  if(holdNextYield&&delay===0){holdNextYield=false;heldYield={callback,args};
   events.push({kind:'migration-yield-held'});return heldYield;}
  return setTimeout(callback,delay,...args);
 }
 function uiClearTimeout(id){if(id!==heldYield)clearTimeout(id);}
 const storage={directStorage:true,
  read:async key=>clone(disk.get(key)),readMany:async keys=>keys.map(k=>clone(disk.get(k))),
  writeMany:async entries=>{
   events.push({kind:'ui-chunks',count:entries.length});
   if(beforeWrite){const fn=beforeWrite;beforeWrite=null;fn();}
   if(failShard)throw Error('Injected bounded shard failure');
   for(const {key,value} of entries)disk.set(key,clone(value));return true;
  },
  commitManifest:async(key,manifest,old,meta)=>{
   if(failCommit)throw Error('Injected atomic manifest failure');
   disk.set(key+':previous',clone(old));disk.set(key,clone(manifest));disk.set(key+':meta',clone(meta));
   events.push({kind:'ui-commit',token:manifest.token,year:manifest.year,day:manifest.day});return true;
  },removeMany:async keys=>{for(const key of keys)disk.delete(key);return true;}};

 function makeWorker(){
  const w={id:++workerId,closed:false,reads:[],stepReads:null,context:null,
   postMessage(message){
    if(this.closed)throw Error('Worker already terminated');
    let m=message;
    if(m.op==='simulate'){
     if(mutateMessage)m=mutateMessage({...m,vacationBoot18373:m.vacationBoot18373?{...m.vacationBoot18373}:undefined});
     messages.push({op:m.op,mode:m.mode,loadSaved:m.loadSaved,useResident:m.useResident,keys:Object.keys(m),
      vacationCheckpoint:m.vacationCheckpoint,token:m.vacationBoot18373?clone(m.vacationBoot18373):null,
      jobWaitResident:m.jobWaitResident,jobWaitAuto:m.jobWaitAuto,jobToken:m.jobWaitCheckpoint18373,
      hasState:Object.prototype.hasOwnProperty.call(m,'state')});
     events.push({kind:'simulate',mode:m.mode,hasState:Object.prototype.hasOwnProperty.call(m,'state')});
     if(captureOnly){queueMicrotask(()=>ui.finish({}));return;}
    }
    this.deliver(clone(m));
   },
   deliver(m){if(this.closed)return;this.context.__message=m;vm.runInContext('self.onmessage({data:__message})',this.context);},
   terminate(){this.closed=true;events.push({kind:'terminate',worker:this.id});}};
  const before=ui.audit();events.push({kind:'worker-constructed',players:before.players,history:before.history,day:before.day});
  const E={team:(s,id)=>s.teams.find(t=>t.id===id),human:s=>s.teams.find(t=>t.id===s.user),
   invalidateMarket(){},syncEligibility(){},coachRating:c=>c.reputation||0,
   applyManagerSettings18371(){},applyPromotionOfferEnvelope18372(){},boardRenewals18371(){},
   clamp:(n,a,b)=>Math.max(a,Math.min(b,n)),availableJobs:()=>[],
   async vacationStepAsync(s){
    w.stepReads=w.reads.length;
    probes.push({point:{careerId:s.v1903CareerId,coachId:s.userCoachId,user:s.user,saveId:s.futbrSaveId,
     year:s.year,day:s.day,national:s.v640National?.userTeam,employed:s.userEmployed},
     pressure:s.coaches.me.pressure,lineup:clone(s.teams[0].lineup),balance:s.teams[0].balance,
     vacation:clone(s.vacation),players:Object.keys(s.players).length,history:history(s),
     stale:s.staleVacationSentinel||null,calendar:s.schedule.length,ui:ui.audit()});
    s.lastDay=s.day;s.day++;s.vacation.completed++;s.vacation.remaining=0;s.vacation.active=false;s.vacation.paused=true;
   },async advanceDayAsync(s){s.lastDay=s.day;s.day++;}};
  function output(m){
   if(w.closed)return;
   if(m.kind==='storage-request'){
    Promise.resolve().then(()=>{
     let result=null;
     if(m.operation==='read'){
      w.reads.push(m.key);result=clone(disk.get(m.key));
      if(m.key===KEY&&mutateWorkerManifest)result=mutateWorkerManifest(result);
     }else if(m.operation==='raw-write')disk.set(m.key,clone(m.value));
     else if(m.operation==='raw-write-many')for(const e of m.entries)disk.set(e.key,clone(e.value));
     else if(m.operation==='raw-delete')disk.delete(m.key);
     else if(m.operation==='raw-delete-many')for(const key of m.keys)disk.delete(key);
     else throw Error('Unexpected storage operation '+m.operation);
     w.deliver({op:'storage-reply',id:m.id,result:result??null});
    }).catch(error=>w.deliver({op:'storage-reply',id:m.id,error:error.message}));return;
   }
   // The separate browser/return gates exercise the actual UI drainer. This
   // boot test acknowledges the genuine stream and checks the committed disk.
   if(m.kind==='vac-live'){w.deliver({op:'vac-live-ack',seq:m.seq});return;}
   if(m.kind.startsWith('vac-sync-')&&m.syncSeq){w.deliver({op:'vac-sync-ack',seq:m.syncSeq});return;}
   if(m.kind==='rpc'){ui.rpcReply(m);return;}
   if(m.kind==='finished'){events.push({kind:'finished',error:m.error||null});ui.finish(m);return;}
   if(m.kind==='save-error'||m.kind==='vac-checkpoint-error')notices.push(m.error);
  }
  const context={console,performance,Engine:E,National:{before:()=>null,after(){},release(){}},
   setTimeout,clearTimeout,TextEncoder,TextDecoder,Blob,Response,CompressionStream,DecompressionStream,
   crypto:crypto.webcrypto,btoa,atob,ArrayBuffer,Uint8Array,
   self:{postMessage(m,transfer=[]){const copy=structuredClone(m,{transfer});queueMicrotask(()=>output(copy));}}};
  w.context=vm.createContext(context);workers.push(w);
  vm.runInContext(code.worker+'\nv53WorkerMain();',w.context);return w;
 }
 const context={console,performance,TextEncoder,TextDecoder,Blob,Response,CompressionStream,DecompressionStream,
  crypto:crypto.webcrypto,btoa,atob,setTimeout:uiSetTimeout,clearTimeout:uiClearTimeout,queueMicrotask,structuredClone,ArrayBuffer,Uint8Array,
  window:{FutBRDesktop:storage,GestorFC:{parallel:{},patch52:{},jobWaitMemory18373:{status:()=>({ownsWorld:false})}}},
  document:{hidden:false},__read:key=>storage.read(key),__spawn:makeWorker,
  __toast:message=>notices.push(String(message)),__history:history};
 vm.createContext(context);
 vm.runInContext(`
 const STORE='gestor_fc_mundo_v205_clean';
 const E={team:(s,id)=>s.teams.find(t=>t.id===id),human:s=>s.teams.find(t=>t.id===s.user),
  invalidateMarket(){},promotionOfferEnvelope18372:()=>null};
 let state=null,saved=null,saveOK=true,saveStamp='',view='vacation',vacationLoop=false,vacationDelay=5;
 let v52SaveTimer=null,v52SavePromise=null,v52SaveDirty=false,v52NotifySave=false,v52SaveWaiters=[],v52PendingState=null;
 const v52SaveStats={requests:0,writes:0,failed:0};
 const v53Sim={active:false,starting:false,syncing:false,patching:false,session:0,mode:''};
 let v53Worker=null,v53WorkerReady=null,v53WorkerFailed=false,v125VacIncoming=null,v52Processing=false,v53Creating=false;
 let v53PatchQueue=[],v143PostRankPending=false,v143NationalRepairToken=0,v143NationalRepairRunning=false;
 let v158ManualPrimePromise=null,v158ManualPrimeDay=-1,v158ManualPrimeYear=-1,v168DeferredRolloverSave=false;
 let v52MarketIndex=null,v555CoachCache={},v555MarketWarmJob=null,v555MarketWarmListJob=null,v555ShellState=null,v260ShellLockedState=null;
 let v93CoachSaveTimer=0,modalKind='',v93VacCheckpointValid=false;
 const v89JobWait={active:false},v18119SeasonTransfer={active:false},v18370JobSave={busy:false},v53RPC=new Map();
 const v555Perf={archiveYearsPacked:0,archivePlayersPacked:0};
 const v18373JobMemory={partial:false,token:null};let nextRpc=0;
 function v168DropStateCaches(){return 0;}
 function v18371BlockingWorkerRequest(){return [...v53RPC.values()].some(p=>p.op!=='check');}
 async function v53GetWorker(){if(!v53Worker)v53Worker=__spawn();return v53Worker;}
 async function v53Call(op,params={}){const w=await v53GetWorker(),id=++nextRpc;
  return new Promise((resolve,reject)=>{v53RPC.set(id,{worker:w,op,resolve,reject});w.postMessage({op,id,...params});});}
 let v158PrimeManualWorker=async()=>true;
 const v52ReadRaw=async key=>__read(key);let dbRead=async key=>__read(key);
 function updateSaveStatus(){}function toast(m){__toast(m);}function v5CrestsOut(){}
 function v53PaintStatus(){}function stopTimer(){}function render(){}
 function v148EnsureNationalReady(){return false;}
 function v18369CanStartFromReturnedVacation(){return false;}function v18369ConsumeVacationReturn(){}
 function v18371SettingsEnvelope(s){return {settings:s?.v622Settings||{}};}
 function v53Saved(m){saveOK=true;v52SaveStats.writes++;}
 let persist=()=>Promise.resolve(),v52FlushSave=async()=>{};
 `+[code.persist,code.deferredPersist,code.playerCodec,code.jobIdentity,code.migrationPause,code.migration,
  code.bootUI,code.baseStart,code.rolloverWrapper,code.runtime].join('\n')+`
 globalThis.fixture={
  set(s){state=s;saved=s;},get:()=>state,
  audit:()=>({players:Object.keys(state?.players||{}).length,history:state?__history(state):null,
   year:state?.year,day:state?.day,partial:!!state?.v18373JobWaitPartial,migrationPending:!!v555ArchiveMigration}),
  persist:()=>persist(false),flush:()=>v52FlushSave(),start:(mode,options)=>v53StartSimulation(mode,options),
  pending:()=>({dirty:v52SaveDirty,saving:!!v52SavePromise,active:v53Sim.active,starting:v53Sim.starting,
   persistRequests:v52SaveStats.requests,migration:!!v555ArchiveMigration}),
  migrate:()=>v555MigrateArchivesAsync(),migrationStats:()=>({...v555Perf}),
  setDeferred(value){v168DeferredRolloverSave=value;},worker:()=>v53Worker,
  setWorker(w){v53Worker=w;v53WorkerReady=Promise.resolve(w);},
  setJob(token){v18373JobMemory.partial=!!token;v18373JobMemory.token=token;},
  finish(m){const f=v53Sim.finished;v53Sim.finished=null;v53Sim.active=false;v53Sim.starting=false;vacationLoop=false;
   m.error?f?.reject(Error(m.error)):f?.resolve(state);},
  rpcReply(m){const p=v53RPC.get(m.id);v53RPC.delete(m.id);m.error?p?.reject(Error(m.error)):p?.resolve(m.result);},
  clear(){clearTimeout(v52SaveTimer);clearTimeout(v93CoachSaveTimer);clearTimeout(v555ArchiveMigrationTimer);v53Worker?.terminate();v53Worker=null;},
  bootStatus:()=>window.GestorFC.vacationBoot18373?.status?.()||null,
  memory:()=>window.GestorFC.memoryStorage18373.status(),
  load:()=>window.GestorFC.v171.loadDirect(),
  verify:(stored,token,message)=>v18373VerifyVacationBoot(stored,token,message)
 };
 `,context);
 ui=context.fixture;
 return {ui,disk,events,messages,workers,probes,notices,context,
  async seed(s){ui.set(s);const pending=ui.persist();await ui.flush();await pending;assert.equal(ui.pending().dirty,false);},
  failSave(where){if(where==='chunks')failShard=true;else failCommit=true;},
  beforeWrite(fn){beforeWrite=fn;},alterMessage(fn){mutateMessage=fn;},alterManifest(fn){mutateWorkerManifest=fn;},
  holdMigrationYield(){holdNextYield=true;},releaseMigrationYield(){assert.ok(heldYield);const held=heldYield;heldYield=null;
   events.push({kind:'migration-yield-released'});held.callback(...held.args);},
  captureOnly(){captureOnly=true;},close:()=>ui.clear()};
}
function edits(s){s.coaches.me.pressure=87;s.teams[0].lineup=['p17','p3'];s.teams[0].balance=765432;
 s.vacation={active:true,paused:false,remaining:1,completed:0,includeTransfers:true,fixtureDecision:'fresh'};}
function seedOldVacation(env,old){
 const token='old-same-day',rootKey=KEY+':v93vac:'+token+':root',root=clone(old),collections={};
 root.staleVacationSentinel='old-checkpoint';
 for(const key of ['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats']){
  const value=root[key];delete root[key];diskWrite(KEY+':v93vac:'+token+':'+key+':0',Object.entries(value));
  collections[key]={isArray:Array.isArray(value),length:Array.isArray(value)?value.length:0,chunks:1};
 }
 diskWrite(rootKey,root);diskWrite(KEY+':v93vac:meta',{format:'GFC_VAC_CHECKPOINT_93',token,rootKey,year:old.year,day:old.day,collections});
 function diskWrite(k,v){env.disk.set(k,clone(v));}
}
async function runGood(config={}){
 const env=environment(),s=fixture(config);await env.seed(s);const oldToken=env.disk.get(KEY).token;
 seedOldVacation(env,clone(s));edits(s);const expected=history(s),start=env.events.length;
 if(config.rollover)env.ui.setDeferred(true);
 await env.ui.start('vacation',{liveStateNoPreSave:true,vacationCheckpoint:true});
 const msg=env.messages[0],events=env.events.slice(start),probe=env.probes[0],w=env.workers[0];
 assert.equal(msg?.hasState,false,'Vacation boot must not postMessage the complete world');
 assert.equal(msg.loadSaved,true);assert.equal(msg.useResident,false);assert.equal(msg.vacationCheckpoint,false);
 assert.ok(msg.token?.token&&msg.token.token!==oldToken);assert.ok(msg.token.revision>=2);
 const committed=events.findIndex(e=>e.kind==='ui-commit'),boot=events.findIndex(e=>e.kind==='worker-constructed');
 assert.ok(committed>=0&&boot>committed,'Bounded fresh save must commit before Worker construction');
 assert.equal(events[boot].players,160);assert.deepEqual(events[boot].history,expected);
 assert.equal(probe.pressure,87);assert.deepEqual(probe.lineup,['p17','p3']);assert.equal(probe.balance,765432);
 assert.equal(probe.vacation.fixtureDecision,'fresh');assert.equal(probe.vacation.remaining,1);
 assert.equal(probe.players,160);assert.deepEqual(probe.history,expected);assert.equal(probe.stale,null);
 assert.equal(probe.ui.players,160);assert.equal(probe.ui.partial,false);assert.deepEqual(probe.ui.history,expected);
 assert.equal(w.reads.slice(0,w.stepReads).some(k=>k.includes(':v93vac:')),false,'Fresh boot must never apply a stale same-day vacation overlay');
 assert.equal(probe.point.year,config.year||2029);assert.equal(probe.point.day,config.day??8);
 assert.equal(probe.point.national,config.national||null);assert.equal(msg.token.nationalCode,config.national||'');
 const saved=await env.ui.load();assert.deepEqual(history(saved),expected);assert.equal(saved.day,(config.day??8)+1);
 assert.equal(saved.coaches.me.pressure,87);assert.deepEqual(saved.teams[0].lineup,['p17','p3']);
 assert.equal(env.ui.bootStatus().checkpoints,1);assert.equal(env.ui.bootStatus().failures,0);
 assert.equal(env.notices.length,0);env.close();return {year:probe.point.year,day:probe.point.day,national:probe.point.national,
  playerCount:probe.players,checkpointBeforeWorker:true,workerReadsBeforeStep:w.stepReads};
}

(async()=>{
 const normal=await runGood();
 const national=await runGood({national:'BRA'});
 const rollover=await runGood({year:2029,day:0,rollover:true});
 {
  // Start the actual historical migration, suspend its first real batch yield,
  // then start vacation. No timer delay or synthetic migration Promise is used.
  const env=environment(),s=fixture();await env.seed(s);const legacy={};
  for(let i=0;i<1201;i++)legacy['past'+i]=[{teamId:'t1',teamName:'Club One',apps:30,goals:i%5}];
  s.v538CareerArchive={2025:legacy};edits(s);const expected=history(s);
  env.holdMigrationYield();const migration=env.ui.migrate();
  assert.equal(env.ui.pending().migration,true);
  const requests=env.ui.pending().persistRequests,start=env.events.length,
   vacation=env.ui.start('vacation',{liveStateNoPreSave:true});
  assert.equal(env.ui.pending().starting,true);assert.equal(env.ui.pending().saving,false);
  assert.equal(env.ui.pending().persistRequests,requests);assert.equal(env.workers.length,0);
  assert.equal(env.events.slice(start).some(e=>e.kind==='ui-commit'||e.kind==='ui-chunks'),false);
  env.releaseMigrationYield();await migration;await vacation;
  assert.equal(env.ui.migrationStats().archiveYearsPacked,0,'Preparation must preserve the unfinished legacy year');
  assert.equal(env.probes[0].ui.migrationPending,false);assert.deepEqual(env.probes[0].history,expected);
  assert.deepEqual(history(await env.ui.load()),expected);
  const events=env.events.slice(start),released=events.findIndex(e=>e.kind==='migration-yield-released'),
   firstChunk=events.findIndex(e=>e.kind==='ui-chunks'),boot=events.findIndex(e=>e.kind==='worker-constructed');
  assert.ok(released>=0&&firstChunk>released&&boot>firstChunk);env.close();
 }
 for(const location of ['chunks','commit']){
  const env=environment(),s=fixture();await env.seed(s);const old=clone(env.disk.get(KEY));edits(s);env.failSave(location);
  await assert.rejects(env.ui.start('vacation',{liveStateNoPreSave:true}),/salvamento|checkpoint|carreira/i);
  assert.equal(env.messages.length,0);assert.equal(env.workers.length,0);assert.equal(env.probes.length,0);
  assert.equal(env.ui.get(),s);assert.equal(env.ui.audit().players,160);assert.equal(env.ui.pending().starting,false);
  assert.equal(env.disk.get(KEY).token,old.token);assert.equal(env.ui.bootStatus().failures,1);env.close();
 }
 {
  const env=environment(),s=fixture();await env.seed(s);edits(s);
  env.beforeWrite(()=>{env.ui.set({...s,v1903CareerId:'changed-career'});});
  await assert.rejects(env.ui.start('vacation',{}),/carreira|salvamento/i);
  assert.equal(env.workers.length,0);env.close();
 }
 const cases={token:'wrong-token',revision:999,careerId:'other-career',coachId:'other-coach',user:'t2',
  futbrSaveId:'other-save',userEmployed:false,year:2030,day:9,seasonDone:true,nationalCode:'ARG'};
 for(const [key,value] of Object.entries(cases)){
  const env=environment(),s=fixture();await env.seed(s);edits(s);
  env.alterMessage(m=>({...m,vacationBoot18373:{...m.vacationBoot18373,[key]:value}}));
  await assert.rejects(env.ui.start('vacation',{}),/checkpoint|carreira|férias/i);
  assert.equal(env.probes.length,0);assert.deepEqual(env.workers[0].reads,[KEY],key+' must reject before decoding any collection');env.close();
 }
 for(const kind of ['missing-core','manifest-date','manifest-career','forbidden-overlay','forbidden-world']){
  const env=environment(),s=fixture();await env.seed(s);edits(s);
  if(kind==='missing-core')env.alterManifest(m=>{delete m.collections.players;return m;});
  if(kind==='manifest-date')env.alterManifest(m=>({...m,day:m.day+1}));
  if(kind==='manifest-career')env.alterManifest(m=>({...m,root:{...m.root,v1903CareerId:'other'}}));
  if(kind==='forbidden-overlay')env.alterMessage(m=>({...m,vacationCheckpoint:true}));
  if(kind==='forbidden-world')env.alterMessage(m=>({...m,state:{year:2029,day:8}}));
  await assert.rejects(env.ui.start('vacation',{}),/checkpoint|carreira|férias/i);
  assert.equal(env.probes.length,0);assert.ok(env.workers[0].reads.every(k=>k===KEY));env.close();
 }
 // Existing non-vacation dispatch remains untouched. The jobwait unit covers
 // its actual resident loop; here the original shared start command is used.
 for(const mode of ['day','dayfast']){
  const env=environment(),s=fixture();await env.seed(s);env.captureOnly();const before=env.events.length;
  await env.ui.start(mode,{});const msg=env.messages[0];
  assert.equal(msg.mode,mode);assert.equal(msg.loadSaved,true);assert.equal(msg.hasState,false);assert.equal(msg.token,null);
  assert.equal(env.events.slice(before).filter(e=>e.kind==='ui-commit').length,0);env.close();
 }
 {
  const env=environment(),s=fixture();s.userEmployed=false;await env.seed(s);env.captureOnly();
  const m=env.disk.get(KEY),token={careerId:s.v1903CareerId,coachId:s.userCoachId,user:s.user,futbrSaveId:s.futbrSaveId,
   userEmployed:false,year:s.year,day:s.day,seasonDone:false,token:m.token,revision:m.revision};env.ui.setJob(token);
  await env.ui.start('dayfast',{jobWaitAuto:true,jobWaitResident:false});
  const first=env.messages[0];assert.equal(first.hasState,false);assert.equal(first.loadSaved,true);assert.equal(first.token,null);
  assert.equal(first.jobWaitAuto,true);assert.equal(first.jobToken.token,token.token);
  await env.ui.start('dayfast',{jobWaitAuto:true,jobWaitResident:true});
  const resident=env.messages[1];assert.equal(resident.hasState,false);assert.equal(resident.loadSaved,false);
  assert.equal(resident.useResident,true);assert.equal(resident.jobWaitResident,true);env.close();
 }
 console.log(JSON.stringify({ok:true,version:'18.373.0',actualBaseStartAndWorkerExecuted:true,
  actualBoundedStorageRuntimeExecuted:true,boundedWriterBeforeWorkerBoot:true,zeroFullWorldVacationMessages:true,
  completeUiPreservedForVacationQueries:true,currentUnpersistedEditsReachWorker:true,
  staleSameDayVacationOverlayIgnored:true,failedSaveBlocksWorkerBoot:true,careerChangeDuringSaveAborts:true,
  actualInFlightMigrationJoinedBeforeSave:true,
  mismatchedManifestRejectedBeforeDecode:true,nationalAndRolloverHistoryPreserved:true,
  nonVacationDispatchPreserved:true,normal,national,rollover,rejectedTokenCases:Object.keys(cases).length+5}));
})().catch(error=>{console.error(error?.stack||String(error));process.exit(1);});
'''


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_vacation_memory_boot_18373.py <project>')
    root = Path(sys.argv[1])
    source = (root / 'src/index.html').read_text(encoding='utf-8')
    assert 'FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN' in source
    worker = between(source, 'function v53WorkerMain(){', '\n\n\nconst v18191uPlayerFields=')
    runtime = between(source, '/* FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN', '/* FUTBR_SAVE_MEMORY_RUNTIME_18373_END */')
    codec = between(source, 'const v18191uPlayerFields=', '// 5.3: one authoritative simulation')
    base = between(source, 'async function v53StartSimulation(mode,options={}){', '\nrunVacation=async function()')
    marker = '/* FUTBR_VACATION_BOUNDED_BOOT_18373 */'
    boot_ui = between(source, marker, 'async function v53StartSimulation(mode,options={}){') if marker in source else ''
    persist_start = source.index('// No career payload is written to LocalStorage.')
    persist = between(source[persist_start:], 'persist=function(notify=false){', '\nv52FlushSave=async function()')
    deferred_persist = between(source, 'const v168BasePersist=persist;', 'const v168BaseStartSimulation=')
    rollover = between(source, 'const v168BaseStartSimulation=v53StartSimulation;', '\nconst v168BasePrepare=')
    job_identity = between(source, 'function v18373JobIdentity(s=state){', 'function v18373LightTeam(')
    migration_pause = between(source, 'function v18373ArchiveMigrationPaused(){', 'window.GestorFC.jobWaitMemory18373=')
    migration = between(source, 'let v555ArchiveMigration=null,v555ArchiveMigrationTimer=0;', 'const v555BaseActualClubsByYear=')
    payload = {'worker': worker, 'runtime': runtime, 'playerCodec': codec,
               'baseStart': base, 'bootUI': boot_ui, 'persist': persist,
               'deferredPersist': deferred_persist, 'rolloverWrapper': rollover,
               'jobIdentity': job_identity, 'migrationPause': migration_pause, 'migration': migration}
    scripts = [m[2] for m in re.finditer(r'<script\b([^>]*)>([\s\S]*?)</script\s*>', source, re.I)
               if not re.search(r'type\s*=\s*["\'](?:application/[^"\']+|importmap)', m[1], re.I)]
    with tempfile.TemporaryDirectory() as folder:
        work = Path(folder)
        (work / 'payload.json').write_text(json.dumps(payload), encoding='utf-8')
        (work / 'test.js').write_text(NODE, encoding='utf-8')
        (work / 'scripts.json').write_text(json.dumps(scripts), encoding='utf-8')
        syntax = subprocess.run(['node', '-e', "const fs=require('fs'),vm=require('vm');for(const s of JSON.parse(fs.readFileSync(process.argv[1])))new vm.Script(s)", str(work / 'scripts.json')],
                                text=True, capture_output=True, timeout=45)
        if syntax.returncode:
            raise RuntimeError(syntax.stderr)
        run = subprocess.run(['node', str(work / 'test.js'), str(work / 'payload.json')],
                             text=True, capture_output=True, timeout=150)
        if run.returncode:
            raise RuntimeError(run.stderr[-12000:] + '\n' + run.stdout[-3000:])
        report = json.loads(run.stdout.strip().splitlines()[-1])
    report['inlineScriptsParsed'] = len(scripts)
    (root / 'vacation-memory-boot-18373-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
