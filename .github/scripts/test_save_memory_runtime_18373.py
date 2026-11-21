"""Execute the installed UI writer/loader and actual Worker save in Node.

Only the persistence boundary is substituted by an isolated in-memory disk.
No user career, production IndexedDB or browser profile is opened.
"""
from pathlib import Path
import json
import re
import subprocess
import sys


NODE = r'''
'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert/strict'),crypto=require('crypto');
const source=fs.readFileSync(process.argv[1],'utf8'),KEY='gestor_fc_mundo_v205_clean';
const marker='/* FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN',end='/* FUTBR_SAVE_MEMORY_RUNTIME_18373_END */';
assert(source.includes(marker),'runtime installed');
const runtime=source.slice(source.indexOf(marker),source.indexOf(end)+end.length);
const playerStart=source.indexOf('const v18191uPlayerFields='),playerEnd=source.indexOf('// 5.3: one authoritative simulation',playerStart);
const playerCodec=source.slice(playerStart,playerEnd);
const coachStart=source.indexOf('function v93ScheduleCoachDecisionSave(delay=60000){');
const coachEnd=source.indexOf('\n// Any actual career edit/full save',coachStart);
assert(coachStart>0&&coachEnd>coachStart);
const legacyCoachScheduler=source.slice(coachStart,coachEnd);
const namedStart=source.indexOf('async function ensureSaved(){');
const namedEnd=source.indexOf('\n/* FUTBR_LONG_CAREER_SAVE_18338_END */',namedStart);
assert(namedStart>0&&namedEnd>namedStart);const actualEnsureSaved=source.slice(namedStart,namedEnd);
const clone=x=>structuredClone(x),hash=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const disk=new Map(),events=[],rpc=[],toasts=[];
let failWrite=0,writes=0,failCommit=false,transactionMax=0,largestPackedRows=0,largestPackedBytes=0;
let largestScorerRows=0,largestScorerBytes=0,largestCompetitionRows=0;
let duringWrite=null,duringFingerprint=null,beforeCommit=null;
// Fire the actual long-delay callback at a deterministic storage boundary.
// UI yielding and real compression/fingerprints still use the normal event loop.
const longTimers=new Map();
function testSetTimeout(callback,delay,...args){
 if(delay>=10000){const id={};longTimers.set(id,{callback,delay,args});return id;}
 return setTimeout(callback,delay,...args);
}
function testClearTimeout(id){if(!longTimers.delete(id))clearTimeout(id);}
function fireTimer(id){const timer=longTimers.get(id);assert(timer,'scheduled real callback');
 longTimers.delete(id);return timer.callback(...timer.args);}
const storage={directStorage:true,
 read:async k=>clone(disk.get(k)),readMany:async ks=>ks.map(k=>clone(disk.get(k))),
 writeMany:async es=>{writes++;transactionMax=Math.max(transactionMax,es.length);
  if(failWrite===writes)throw Error('Injected shard write failure');
  if(duringWrite){const hook=duringWrite;duringWrite=null;hook();}
  for(const {key,value}of es){
   if(key.includes(':v555CareerArchive:')){
    largestPackedRows=Math.max(largestPackedRows,value.length);
    largestPackedBytes=Math.max(largestPackedBytes,Buffer.byteLength(JSON.stringify(value)));
   }
   if(key.includes(':scorerArchive:')){
    largestScorerRows=Math.max(largestScorerRows,value.length);
    largestScorerBytes=Math.max(largestScorerBytes,Buffer.byteLength(JSON.stringify(value)));
   }
   if(key.includes(':competitionStats:'))largestCompetitionRows=Math.max(largestCompetitionRows,value.length);
   disk.set(key,clone(value));
  }events.push({kind:'chunks',count:es.length});
 },
 commitManifest:async(k,m,old,meta)=>{
  if(beforeCommit){const hook=beforeCommit;beforeCommit=null;await hook();}
  if(failCommit)throw Error('Injected manifest commit failure');
  assert.equal(k,KEY);disk.set(KEY+':previous',clone(old));disk.set(KEY,clone(m));
  disk.set(KEY+':meta',clone(meta));events.push({kind:'commit',token:m.token});
 },
 removeMany:async ks=>{events.push({kind:'cleanup',keys:[...ks]});for(const k of ks)disk.delete(k);}
};
const context={console,performance,TextEncoder,TextDecoder,Blob,Response,CompressionStream,DecompressionStream,
 crypto:{subtle:{digest:async(...args)=>{const result=await crypto.webcrypto.subtle.digest(...args);
  if(duringFingerprint){const hook=duringFingerprint;duringFingerprint=null;hook();}return result;}}},
 ArrayBuffer,Map,Set,WeakMap,Date,Math,JSON,Promise,structuredClone,Uint8Array,
 btoa,atob,setTimeout:testSetTimeout,clearTimeout:testClearTimeout,queueMicrotask,
 window:{FutBRDesktop:storage,GestorFC:{parallel:{},patch52:{}}},
 __read:k=>storage.read(k),__rpc:async(op,params)=>{rpc.push({op,keys:Object.keys(params||{})});return {settled:true};},
 __toast:m=>toasts.push(m)};
vm.createContext(context);
vm.runInContext(`
 const STORE='gestor_fc_mundo_v205_clean',E={invalidateMarket(){}};
 let state=null,saved=null,saveOK=true,saveStamp='',v168DeferredRolloverSave=false;
 let v52SaveTimer=null,v52SavePromise=null,v52SaveDirty=false,v52NotifySave=false,v52SaveWaiters=[],v52PendingState=null;
 const v52SaveStats={requests:0,writes:0,failed:0};
 const v53Sim={active:false,starting:false,syncing:false,patching:false,session:0,mode:''};
 let v53Worker=null,v53WorkerReady=null,v53WorkerFailed=false,v125VacIncoming=null,v52Processing=false,v53Creating=false;
 let v53PatchQueue=[],v143PostRankPending=false,v158ManualPrimePromise=null,v158ManualPrimeDay=-1,v158ManualPrimeYear=-1;
 let v52MarketIndex=null,v555CoachCache={},v555MarketWarmJob=null,v555MarketWarmListJob=null,v555ShellState=null,v260ShellLockedState=null;
 let v93CoachSaveTimer=0,modalKind='';const v89JobWait={active:false};
 const BASE=STORE,FORMAT='GFC_SHARDED_171',get=async key=>__read(key),v18338SaveAudit={rewritten:0,reused:0,last:''};
 const v18119SeasonTransfer={active:false},v18370JobSave={busy:false},v53RPC=new Map();
 function v168DropStateCaches(){return 1;}
 function v18371BlockingWorkerRequest(){return [...v53RPC.values()].some(p=>p.op!=='check');}
 let v53Call=async(op,params)=>__rpc(op,params);
 let v158PrimeManualWorker=async()=>true,v53StartSimulation=async()=>true;
 const v52ReadRaw=async key=>__read(key);
 let dbRead=async key=>__read(key);
 function updateSaveStatus(){}
 function toast(m){__toast(m);}
 function v5CrestsOut(){}
 function v53Saved(m){saveOK=true;v52SaveStats.writes++;}
 let persist=function(notify=false){if(!state)return Promise.resolve();v52PendingState=state;v52SaveDirty=true;
  v52NotifySave||=notify;return new Promise(resolve=>v52SaveWaiters.push(resolve));};
 let v52FlushSave=async()=>{};
 `+legacyCoachScheduler+`
 const legacyScheduleCoach=v93ScheduleCoachDecisionSave;
 `+playerCodec+runtime+actualEnsureSaved+`
 globalThis.fixture={
  set(s){state=s;saved=s;},get:()=>state,flush:()=>v52FlushSave(),persist:()=>persist(),
  pending:()=>({pending:v52PendingState,dirty:v52SaveDirty,saveOK,saving:!!v52SavePromise}),
  change:fn=>fn(state),setDirty:()=>{v52PendingState=state;v52SaveDirty=true;},
  sim:v53Sim,rpcs:v53RPC,setWorker(w){v53Worker=w;v53WorkerReady=Promise.resolve(w);},
  worker:()=>v53Worker,prime:()=>v158PrimeManualWorker(),
  forceFail:()=>{saveOK=false;},call:(op,params)=>v53Call(op,params),
  clearTimers(){clearTimeout(v52SaveTimer);v52SaveTimer=null;clearTimeout(v93CoachSaveTimer);v93CoachSaveTimer=0;},
  setDeferred(v){v168DeferredRolloverSave=v;},
  ensureNamed:()=>ensureSaved(),
  scheduleCoach(legacy=false){(legacy?legacyScheduleCoach:v93ScheduleCoachDecisionSave)(60000);return v93CoachSaveTimer;},
  coachTimer:()=>v93CoachSaveTimer,
 };
 `,context);
const f=context.fixture,api=context.window.GestorFC.memoryStorage18373,loader=context.window.GestorFC.v171;
function fixture(players=2100,annualPlayers=9000){
 const s={v1903CareerId:'career-2029-memory',futbrSaveId:'named-memory',userCoachId:'coach-main',
  user:'t1',userEmployed:false,manager:'Memory Test',year:2029,day:17,seasonDone:false,
  players:{},teams:[{id:'t1',roster:['p0'],name:'Isolated Club',balance:123456}],
  coaches:{'coach-main':{id:'coach-main',clubId:null}},schedule:[{id:'d0',fixtures:[]}],
  competitions:{league:{name:'League'}},competitionStats:{},allTimeStats:{},
  v538CareerArchive:{2025:{p0:{goals:5,details:[null,0,false]}},2024:{}},
  v555CareerArchive:{},scorerArchive:[],
  transfers:[{playerId:'p0',from:'t0',to:'t1'}],retirements:[{playerId:'old0',year:2026}],
  history:[{year:2026,champion:'t0'}],internationalHistory:[],v735NationalArchive:{},crestOverrides:{},
  v622Settings:{renewals:'board',offerPopup:true,matchSpeed:4},unknownRoot:{preserve:['root',null,0,false]}};
 for(let i=0;i<players;i++)s.players['p'+i]={id:'p'+i,name:'Player '+i,pos:i%11?'MEI':'GOL',age:22,
  contract:2031,fitness:100,wage:1000,skills:{pass:70,defend:58},clubId:'t1',star:false,injury:0,
  unknownPlayer:{sentinel:i,extra:[null,false,'legacy']}};
 for(const year of [2026,2027,2028]){
  const n=year===2027?new Array(6):{t1:'Brasileirão',t2:'Copa & Europa',empty:null};
  if(Array.isArray(n)){n[0]='Brasileirão';n[3]=null;n[5]='Copa & Europa';n.extra='names-extra';}
  const p={};for(let i=0;i<annualPlayers;i++)p['p'+i]='0;'+(i%30)+';'+(i%7)+'|5;'+(i%12)+';'+year;
  s.v555CareerArchive[year]={n,p,unknownYear:{retained:true,when:year,values:[null,false,0]},flag:null};
  const scoring={};for(let i=0;i<annualPlayers;i++)scoring['p'+i]={id:'p'+i,name:'Historical '+i,
   goals:i%20,assists:i%8,apps:28,minutes:2000,clubs:{t1:'Club1'},byClub:{t1:{goals:i%20,apps:28}},extra:null};
  s.scorerArchive.push({year,competitions:{league:scoring,empty:{}},unknown:{preserve:true}});
 }
 s.competitionStats={league:{}};for(let i=0;i<players;i++)s.competitionStats.league['p'+i]={id:'p'+i,goals:i%17,clubs:{t1:'Club1'}};
 s.v555CareerArchive.empty={n:[],p:{},unknown:'kept'};s.v555CareerArchive.nil=null;
 return s;
}
function seedLegacy(s){
 disk.clear();const root=clone(s),collections={};
 for(const key of ['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats',
   'v538CareerArchive','v555CareerArchive','scorerArchive']){
  const value=root[key];delete root[key];const ck=KEY+':legacy:'+key;let rows=[];
  if(key==='v538CareerArchive'||key==='v555CareerArchive'){
   for(const year in value){const r=value[year];
    if(r&&typeof r==='object'&&!Array.isArray(r)){
     const keys=Object.keys(r);if(!keys.length)rows.push([year,null,{},1]);
     for(const id of keys)rows.push([year,id,r[id]]);
    }else rows.push([year,null,r,0]);
   }
  }else rows=Object.entries(value);
  collections[key]={isArray:Array.isArray(value),length:Array.isArray(value)?value.length:0,keys:[ck],
   ...(['v538CareerArchive','v555CareerArchive'].includes(key)?{nested:'year-id-v1'}:{})};
  disk.set(ck,clone(rows));
 }
 const m={format:'GFC_SHARDED_171',version:1,token:'legacy-token',revision:7,year:s.year,day:s.day,root,collections};
 disk.set(KEY,clone(m));disk.set(KEY+':meta',{year:s.year,day:s.day,revision:7});
 disk.set(KEY+':previous',{format:'GFC_SHARDED_171',root:{v1903CareerId:'older'},collections:{players:{keys:['obsolete-only']}}});
 disk.set('obsolete-only',[['older-player',{}]]);return m;
}
async function flushChange(){const p=f.persist();await f.flush();await p;}
function assertHistory(actual,expected){
 assert.deepEqual(clone(actual.v555CareerArchive),clone(expected.v555CareerArchive));
 assert.deepEqual(clone(actual.v538CareerArchive),clone(expected.v538CareerArchive));
 assert.deepEqual(clone(actual.scorerArchive),clone(expected.scorerArchive));
 assert.deepEqual(clone(actual.competitionStats),clone(expected.competitionStats));
 for(const y of ['2026','2027','2028']){
  const names=actual.v555CareerArchive[y].n;
  if(y==='2027'){
   assert.equal(names.length,6);assert.equal(1 in names,false);assert.equal(3 in names,true);
   assert.equal(names[3],null);assert.equal(names.extra,'names-extra');
  }else assert.equal(names.t1,'Brasileirão');
 }
}
(async()=>{
 const report={ok:false,version:'18.373.0',sameGameScope:true};
 const s=fixture(),expected=clone(s),legacy=seedLegacy(s);f.set(s);
 const legacyDecoded=await loader.loadDirect();assertHistory(legacyDecoded,expected);
 report.legacyYearIdHistoryReadable=true;
 f.set(s);f.setDirty();const token=await api.ensureCheckpoint();
 assert.equal(token.careerId,s.v1903CareerId);assert.equal(token.revision,8);
 assert.equal(rpc.some(r=>r.op==='save'||r.keys.includes('state')),false);
 assert.equal(transactionMax,1);assert(largestPackedRows<=128&&largestPackedRows>0);
 assert(largestPackedBytes<100000);assert.equal(disk.get(KEY).collections.v555CareerArchive.nested,'year-path-v1');
 assert(largestScorerRows<=128&&largestScorerRows>0);assert(largestScorerBytes<100000);
 assert(largestCompetitionRows<=128&&largestCompetitionRows>0);
 assert.equal(disk.get(KEY).collections.scorerArchive.nested,'tree-path-v1');
 assert.equal(disk.get(KEY).collections.competitionStats.nested,'tree-path-v1');
 assert.equal(disk.has('obsolete-only'),false);assert.equal(disk.get(KEY+':previous').token,legacy.token);
 assert(events.findIndex(e=>e.kind==='cleanup')>events.findIndex(e=>e.kind==='commit'));
 assert.equal(f.pending().pending,null);
 const roundtrip=await loader.loadDirect();assert.deepEqual(clone(roundtrip),expected);assertHistory(roundtrip,expected);
 report.fullRoundtrip=true;report.sparseNamesAndUnknownFieldsPreserved=true;report.threeYearsPackedHistory=true;
 report.archivePlayerRows=Object.values(s.v555CareerArchive).reduce((n,y)=>n+Object.keys(y?.p||{}).length,0);
 report.archiveChecksum=hash(roundtrip.v555CareerArchive);report.noFullWorldSaveRPC=true;
 report.boundedPackedHistory=true;report.maxPackedRows=largestPackedRows;report.maxPackedBytes=largestPackedBytes;
 report.boundedScorerHistory=true;report.maxScorerRows=largestScorerRows;report.maxScorerBytes=largestScorerBytes;
 report.boundedCompetitionStats=true;report.scorerChecksum=hash(roundtrip.scorerArchive);
 report.transactionChunks=transactionMax;report.pendingReferenceReleased=true;
 const written=api.status().chunksWritten;const reusedToken=await api.ensureCheckpoint();
 assert.equal(reusedToken.token,token.token);assert.equal(api.status().chunksWritten,written);
 assert(api.status().reusedCheckpoints>0);report.cleanCheckpointReused=true;
 await flushChange();assert(api.status().chunksReused>0);assert.equal(api.status().chunksWritten,written);
 report.unchangedChunksReused=true;
 // Editing one historical player in the same season must not reuse stale data.
 s.v555CareerArchive[2027].p.p12='new historical value';await flushChange();
 const edited=await loader.loadDirect();assert.equal(edited.v555CareerArchive[2027].p.p12,'new historical value');
 report.changedHistoryWritten=true;
 // Reproduce the CI race using the actual pre-fix 60-second callback and the
 // actual named-save ensureSaved function. The callback changes no data, yet
 // its redundant persist invalidates the writer and causes Save/Exit to fail.
 s.v622Settings.offerPopup=false;f.setDirty();
 const raceBefore=clone(disk.get(KEY)),unchangedDuringRace=hash(s),raceFailures=api.status().failed;
 const legacyTimer=f.scheduleCoach(true);duringFingerprint=()=>{fireTimer(legacyTimer);};
 await assert.rejects(()=>f.ensureNamed(),/salvamento não corresponde/);
 assert.equal(hash(s),unchangedDuringRace);assert.deepEqual(disk.get(KEY),raceBefore);
 assert.equal(api.status().failed,raceFailures+1);assert.equal(f.pending().dirty,true);
 f.clearTimers();await f.flush();assert.equal(f.pending().saveOK,true);
 report.legacyDecisionAutosaveRaceReproduced=true;
 // The patched timer was scheduled BEFORE this writer. It must join the
 // writer without a second persist, and explicit Save/Exit must await commit.
 s.v622Settings.offerPopup=true;f.setDirty();
 const joinedBefore=clone(disk.get(KEY)),joinedStats=api.status(),joinedTimer=f.scheduleCoach();
 let timerWork,namedResolved=false,enterCommit,releaseCommit;
 const commitEntered=new Promise(resolve=>{enterCommit=resolve;});
 const commitBarrier=new Promise(resolve=>{releaseCommit=resolve;});
 beforeCommit=async()=>{enterCommit();await commitBarrier;};
 duringFingerprint=()=>{timerWork=fireTimer(joinedTimer);};
 const namedSave=f.ensureNamed().then(x=>{namedResolved=true;return x;});
 await commitEntered;
 assert.equal(namedResolved,false);assert.equal(f.pending().saving,true);assert.equal(f.pending().dirty,false);
 assert.equal(api.status().coachAutosavesJoined,joinedStats.coachAutosavesJoined+1);
 assert.deepEqual(disk.get(KEY),joinedBefore);releaseCommit();
 const joinedManifest=await namedSave;await timerWork;
 assert.equal(namedResolved,true);assert.equal(joinedManifest.root.v622Settings.offerPopup,true);
 assert.equal(api.status().fullSaves,joinedStats.fullSaves+1);
 assert.equal(api.status().failed,joinedStats.failed);
 assert.equal(api.status().coachAutosavesConfirmed,joinedStats.coachAutosavesConfirmed+1);
 assert.equal(f.pending().dirty,false);assert.equal(f.pending().saving,false);
 report.actualCoachAutosaveJoinsNewerWriter=true;report.actualNamedSaveWaitsForJoinedWriter=true;
 // A joined failure is NOT confirmation: Save/Exit rejects, old data remains
 // readable and the actual timer rearms without reporting a successful save.
 s.v622Settings.offerPopup=false;f.setDirty();
 const failureBefore=clone(disk.get(KEY)),failureStats=api.status(),failureTimer=f.scheduleCoach();
 duringFingerprint=()=>{timerWork=fireTimer(failureTimer);};failCommit=true;
 await assert.rejects(()=>f.ensureNamed(),/salvamento não corresponde/);await timerWork;
 assert.deepEqual(disk.get(KEY),failureBefore);assert.equal(f.pending().saveOK,false);
 assert.equal(api.status().coachAutosavesConfirmed,failureStats.coachAutosavesConfirmed);
 assert.equal(api.status().coachAutosaveRetries,failureStats.coachAutosaveRetries+1);
 assert.equal(longTimers.get(f.coachTimer()).delay,10000);
 failCommit=false;f.clearTimers();await flushChange();
 report.joinedFailureRejectsNamedSaveAndRearms=true;
 // A real edit while writing still invalidates the generation. The autosave
 // wrapper must not weaken this guard or publish an inconsistent manifest.
 s.v622Settings.offerPopup=true;f.setDirty();
 const editBefore=clone(disk.get(KEY)),editStats=api.status(),editTimer=f.scheduleCoach();
 duringFingerprint=()=>{timerWork=fireTimer(editTimer);s.v622Settings.matchSpeed=2;f.persist();};
 await assert.rejects(()=>f.ensureNamed(),/salvamento não corresponde/);await timerWork;
 assert.deepEqual(disk.get(KEY),editBefore);assert.equal(api.status().failed,editStats.failed+1);
 assert.equal(api.status().coachAutosavesConfirmed,editStats.coachAutosavesConfirmed);
 assert.equal(f.pending().dirty,true);f.clearTimers();await f.flush();
 assert.equal((await loader.loadDirect()).v622Settings.matchSpeed,2);
 report.concurrentRealEditStillInvalidatesWriter=true;
 // If the decision is scheduled AFTER a writer captured root, that older
 // writer cannot confirm it. Queue a new save after it settles, without
 // invalidating the older writer just because the notification timer fired.
 s.v622Settings.offerPopup=false;f.setDirty();const olderStats=api.status();
 duringFingerprint=()=>{
  s.decisionScheduledDuringWriter18373={club:'t2',terms:{salary:4567,years:3}};
  timerWork=fireTimer(f.scheduleCoach());
 };
 await assert.rejects(()=>f.ensureNamed(),/salvamento não corresponde/);await timerWork;
 assert.equal(api.status().failed,olderStats.failed);
 assert.equal(api.status().coachAutosavesConfirmed,olderStats.coachAutosavesConfirmed);
 assert.equal(api.status().coachAutosavesAfterOlderWriter,olderStats.coachAutosavesAfterOlderWriter+1);
 assert.equal(disk.get(KEY).root.decisionScheduledDuringWriter18373,undefined);
 assert.equal(f.pending().dirty,true);f.clearTimers();await f.flush();
 const decisionManifest=await f.ensureNamed();
 assert.deepEqual(clone(decisionManifest.root.decisionScheduledDuringWriter18373),s.decisionScheduledDuringWriter18373);
 assert.deepEqual(clone((await loader.loadDirect()).decisionScheduledDuringWriter18373),s.decisionScheduledDuringWriter18373);
 report.decisionScheduledDuringWriterGetsNewCheckpoint=true;
 for(const mode of ['shard','manifest']){
  const before=clone(disk.get(KEY)),previous=clone(disk.get(KEY+':previous'));
  const priorChunks=[...Object.values(before.collections).flatMap(x=>x.keys),...Object.values(previous.collections).flatMap(x=>x.keys)];
  s.players.p0.name+=' failure';writes=0;failWrite=mode==='shard'?1:0;failCommit=mode==='manifest';
  await flushChange();assert.equal(f.pending().saveOK,false);
  assert.deepEqual(disk.get(KEY),before);assert.deepEqual(disk.get(KEY+':previous'),previous);
  for(const key of priorChunks)assert(disk.has(key));
  failWrite=0;failCommit=false;await flushChange();
 }
 report.failedWriteKeepsCurrentAndPrevious=true;
 const currentToken=await api.ensureCheckpoint();
 api.setWorkerOwner(currentToken);const partial=clone(s);partial.players={};partial.v555CareerArchive={};partial.v18373JobWaitPartial=true;f.set(partial);
 const beforePartial=clone(disk.get(KEY));await f.persist();await f.flush();
 await assert.rejects(()=>api.ensureCheckpoint(),/parcial|devolvendo/);
 assert.deepEqual(disk.get(KEY),beforePartial);assert.equal(api.clearWorkerOwner({...currentToken,token:'other'}),false);
 assert.equal(api.clearWorkerOwner(currentToken),false);
 assert.equal(api.releaseIdleWorker('owned-between-days'),false);
 f.set(s);assert.equal(api.clearWorkerOwner(currentToken),true);report.partialUIBlocked=true;
 report.ownerCannotBeReleasedWhilePartial=true;
 // Ownership compares the original token when the world advances, not UI day.
 const ownerToken=await api.ensureCheckpoint();api.setWorkerOwner(ownerToken);s.day++;
 assert.equal(api.clearWorkerOwner(ownerToken),true);await flushChange();
 const recoveryToken=await api.ensureCheckpoint();api.setWorkerOwner(recoveryToken);
 const advanced=clone(disk.get(KEY));advanced.root.day++;advanced.day++;advanced.revision++;
 advanced.token='worker-advanced-token';disk.set(KEY,advanced);s.day++;f.set({...s,players:{},v555CareerArchive:{}});
 const recovered=await api.restoreOwnerCheckpoint(recoveryToken);assert.equal(recovered.day,s.day);
 assert.equal(Object.keys(recovered.players).length,Object.keys(s.players).length);assertHistory(recovered,s);
 assert.equal(api.clearWorkerOwner(recoveryToken),true);f.set(recovered);report.ownerRecoveryFromAdvancedCheckpoint=true;
 // A different coach/club cannot be substituted during recovery.
 const right=clone(disk.get(KEY)),next=await api.ensureCheckpoint();api.setWorkerOwner(next);
 const wrong=clone(right);wrong.root.user='different-club';disk.set(KEY,wrong);
 await assert.rejects(()=>api.restoreOwnerCheckpoint(next),/outro vínculo/);disk.set(KEY,right);
 api.clearWorkerOwner(next);report.crossCareerRecoveryRejected=true;
 let ended=0;const worker={v18373CheckpointBusy:true,terminate(){ended++;}};f.setWorker(worker);
 assert.equal(api.releaseIdleWorker('test-pending'),false);assert.equal(ended,0);
 await flushChange();assert.equal(ended,1);assert.equal(f.worker(),null);
 assert(rpc.some(r=>r.op==='settle-storage-18373'));assert.equal(await f.prime(),false);
 report.deferredWorkerSaveSettledBeforeRelease=true;report.manualPrewarmDisabled=true;
 // The real named loader awaits a CLEAN flush before terminating its Worker.
 // Its continuation must wait for the deferred checkpoint even without a
 // pending UI state. Two callers must join one settlement RPC.
 assert.equal(f.pending().dirty,false);assert.equal(f.pending().pending,null);
 const cleanWorker={v18373CheckpointBusy:true,terminate(){events.push({kind:'clean-worker-terminated'});}};
 f.setWorker(cleanWorker);let releaseDeferred,cleanResolved=false,settleCalls=0;
 const barrier=new Promise(resolve=>{releaseDeferred=resolve;}),normalRPC=context.__rpc;
 context.__rpc=async(op,params)=>{
  if(op==='settle-storage-18373'){
   settleCalls++;await barrier;events.push({kind:'manual-checkpoint-committed'});
  }
  return normalRPC(op,params);
 };
 const cleanWrites=api.status().fullSaves;
 const cleanA=f.flush().then(()=>{cleanResolved=true;events.push({kind:'named-load-may-continue'});});
 const cleanB=f.flush();await new Promise(resolve=>setTimeout(resolve,0));
 assert.equal(cleanResolved,false);assert.equal(settleCalls,1);assert.equal(f.worker(),cleanWorker);
 assert.equal(f.pending().saving,true);releaseDeferred();await Promise.all([cleanA,cleanB]);
 assert.equal(f.worker(),null);assert.equal(api.status().fullSaves,cleanWrites);
 assert.equal(f.pending().saving,false);assert.equal(api.status().cleanWorkerSettlements,1);
 assert(events.findIndex(e=>e.kind==='manual-checkpoint-committed')<events.findIndex(e=>e.kind==='clean-worker-terminated'));
 assert(events.findIndex(e=>e.kind==='clean-worker-terminated')<events.findIndex(e=>e.kind==='named-load-may-continue'));
 context.__rpc=normalRPC;report.cleanFlushWaitsForDeferredWorkerSave=true;
 report.concurrentCleanFlushesShareSettlement=true;
 f.sim.active=true;f.setWorker({terminate(){throw Error('active Worker terminated');}});
 assert.equal(api.releaseIdleWorker('active'),false);f.sim.active=false;
 f.rpcs.set(1,{op:'save'});assert.equal(api.releaseIdleWorker('mutation'),false);f.rpcs.clear();
 f.setWorker(null);report.activeAndMutatingWorkersProtected=true;
 await assert.rejects(()=>f.call('save',{state:s}),/fragmentado/);
 // An absent history shard must fail loudly, never silently produce a partial career.
 const good=clone(disk.get(KEY)),missing=good.collections.v555CareerArchive.keys[0],savedChunk=disk.get(missing);
 disk.delete(missing);await assert.rejects(()=>loader.loadDirect(),/ausente/);disk.set(missing,savedChunk);
 report.missingShardRejected=true;
 // Exercise the actual Worker writer/decoder on a legacy packed year too.
 const start=source.indexOf('function v53WorkerMain(){'),stop=source.indexOf('const v18191uPlayerFields=',start);
 let workerSource=source.slice(start,stop).trim();
 const hook=`
 read=async key=>__read(key);
 v18181RawWriteMany=async entries=>__workerWrite(entries);
 v18310WorkerDeleteMany=async keys=>__workerDelete(keys);
 self.__fixture={save,decode,handle,applyVacation:v93ApplyVacationCheckpoint,
  setWorld:s=>{world=s;},getWorld:()=>world,setDeferredSave:p=>{v150ManualSavePromise=p;}};
 `;
 const where=workerSource.indexOf(' self.onmessage=event=>{const m=event.data;');
 assert(where>0);workerSource=workerSource.slice(0,where)+hook+workerSource.slice(where);
 const workerDisk=new Map(),workerWrites=[],workerReads=[];
 const wc={console,Engine:{},performance,TextEncoder,TextDecoder,Blob,Response,CompressionStream,DecompressionStream,
  crypto:crypto.webcrypto,ArrayBuffer,Map,Set,Date,Math,JSON,Promise,Uint8Array,btoa,atob,setTimeout,clearTimeout,
  self:{postMessage(){}},__read:async key=>{workerReads.push(key);return clone(workerDisk.get(key));},
  __workerWrite:async entries=>{for(const e of entries){workerDisk.set(e.key,clone(e.value));workerWrites.push(e);}},
  __workerDelete:async keys=>{for(const key of keys)workerDisk.delete(key);}};
 vm.createContext(wc);vm.runInContext(workerSource+'\nv53WorkerMain();',wc);
 let finishActualDeferred,actualSettled=false;
 wc.self.__fixture.setDeferredSave(new Promise(resolve=>{finishActualDeferred=resolve;}));
 const actualSettlement=wc.self.__fixture.handle({op:'settle-storage-18373'}).then(x=>{actualSettled=true;return x;});
 await new Promise(resolve=>setTimeout(resolve,0));assert.equal(actualSettled,false);
 finishActualDeferred();assert.equal((await actualSettlement).settled,true);
 report.actualWorkerSettlementWaitsForDeferredPromise=true;
 const legacyFixture=fixture(1100,6000);seedLegacy(legacyFixture);
 for(const [k,v]of disk)workerDisk.set(k,clone(v));
 await wc.self.__fixture.save(legacyFixture);
 const wm=workerDisk.get(KEY);assert.equal(wm.collections.v555CareerArchive.nested,'year-path-v1');
 const decoded=await wc.self.__fixture.decode(wm);assertHistory(decoded,legacyFixture);
 assert.equal(wm.revision,8);
 for(const {key,value}of workerWrites)if(key.includes(':v555CareerArchive:'))assert(value.length<=128);
 for(const {key,value}of workerWrites)if(key.includes(':scorerArchive:')||key.includes(':competitionStats:'))assert(value.length<=128);
 report.actualWorkerPackedHistoryRoundtrip=true;report.workerMigratesLegacyPackedHistory=true;
 report.actualWorkerScorerHistoryRoundtrip=true;
 // The exact canonical vacation must not decode its entire core world twice.
 const core=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats'];
 const overlayWorld=fixture(16,8),overlayRoot=clone(overlayWorld),overlayKeys=[];
 const vac={format:'GFC_VAC_CHECKPOINT_93',token:'overlay-proof',year:2029,day:17,
  rootKey:KEY+':v93vac:overlay-proof:root',collections:{}};
 for(const key of core){const value=overlayRoot[key];delete overlayRoot[key];
  const chunk=KEY+':v93vac:overlay-proof:'+key+':0';overlayKeys.push(chunk);
  workerDisk.set(chunk,Object.entries(value));
  vac.collections[key]={isArray:Array.isArray(value),length:Array.isArray(value)?value.length:0,chunks:1};
 }
 const canonical={format:'GFC_SHARDED_171',token:'vacation-'+vac.token,
  year:2029,day:17,root:clone(overlayRoot),collections:{}};
 workerDisk.set(KEY+':v93vac:meta',clone(vac));workerDisk.set(vac.rootKey,clone(overlayRoot));
 workerDisk.set(KEY,clone(canonical));wc.self.__fixture.setWorld(clone(overlayWorld));workerReads.length=0;
 assert.equal(await wc.self.__fixture.applyVacation(2029,17),true);
 assert.equal(workerReads.filter(k=>overlayKeys.includes(k)).length,0);
 assert.deepEqual(clone(wc.self.__fixture.getWorld()),overlayWorld);
 report.exactVacationCheckpointAvoidsCoreReread=true;
 const negatives=[];
 for(const field of ['token','v1903CareerId','userCoachId','user','futbrSaveId','year','day','incompleteWorld']){
  const altered=clone(canonical),candidate=clone(overlayWorld);
  if(field==='token')altered.token='another-vacation';
  else if(field==='incompleteWorld')candidate.players={};
  else altered.root[field]=field==='year'?2030:field==='day'?18:'different-'+field;
  workerDisk.set(KEY,altered);wc.self.__fixture.setWorld(candidate);workerReads.length=0;
  assert.equal(await wc.self.__fixture.applyVacation(2029,17),true);
  assert.equal(workerReads.filter(k=>overlayKeys.includes(k)).length,core.length,field+' must use legacy fallback');
  negatives.push(field);
 }
 report.vacationOverlayMismatchKeepsLegacyFallback=true;report.vacationOverlayNegativeCases=negatives;
 const stats=clone(api.status());delete stats.owner;report.stats=stats;
 report.runtimeTestHookNotShipped=!source.includes('TEST_ONLY_SAVE_MEMORY_18373');
 report.ok=true;f.clearTimers();process.stdout.write(JSON.stringify(report));
})().catch(error=>{f.clearTimers();console.error(error.stack);process.exit(1);});
'''


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_save_memory_runtime_18373.py <project>')
    root = Path(sys.argv[1])
    source = root / 'src' / 'index.html'
    result = subprocess.run(['node', '-e', NODE, str(source.resolve())], capture_output=True,
                            text=True, timeout=180, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr[-14000:] or result.stdout[-14000:])
    report = json.loads(result.stdout)
    (root / 'save-memory-runtime-18373-tests.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
