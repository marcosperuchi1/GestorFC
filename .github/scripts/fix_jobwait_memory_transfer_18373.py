"""Transfer job-search ownership without cloning a second complete career.

Apply after the 18.373 durable checkpoint and storage runtime patches.  The
normal match/vacation engine is reused; only the automatic unemployed search
keeps its UI as a small mirror while the worker owns players and all archives.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

MARK = 'FUTBR_JOBWAIT_SINGLE_OWNER_18373'


def once(s, old, new, label):
    if s.count(old) != 1:
        raise RuntimeError(f'18.373 jobwait {label}: expected one anchor, found {s.count(old)}')
    return s.replace(old, new, 1)


TREE_CODEC = r'''
/* Bounded lossless return of arbitrary saved fields. A packed career year,
   current competition or unknown future field is never one giant row. */
function v18373SmallTree(value){
 let count=0,chars=0;
 const visit=(x,depth)=>{
  if(++count>192||depth>16)return false;
  if(typeof x==='string'){chars+=x.length;return chars<=24576;}
  if(!x||typeof x!=='object')return true;
  if(ArrayBuffer.isView(x)||x instanceof ArrayBuffer)return x.byteLength<=24576;
  if(Object.prototype.toString.call(x)!=='[object Object]'&&!Array.isArray(x))return false;
  for(const k in x)if(Object.prototype.hasOwnProperty.call(x,k)){
   chars+=k.length;if(chars>24576||!visit(x[k],depth+1))return false;
  }
  return true;
 };
 return visit(value,0);
}
function* v18373TreeRows(value,path=[]){
 for(const key in value){
  if(!Object.prototype.hasOwnProperty.call(value,key))continue;
  const row=value[key],next=[...path,key];
  if(next.length>64)throw Error('Profundidade de dados inesperada; o checkpoint permanece preservado.');
  if(v18373SmallTree(row))yield [next,row,'v'];
  else if(typeof row==='string'){
   yield [next,row.length,'s'];
   for(let offset=0;offset<row.length;offset+=16384)yield [next,row.slice(offset,offset+16384),'+'];
  }
  else if(row&&typeof row==='object'&&(Array.isArray(row)||Object.prototype.toString.call(row)==='[object Object]')){
   yield [next,Array.isArray(row)?row.length:null,Array.isArray(row)?'a':'o'];
   yield* v18373TreeRows(row,next);
  }else throw Error('Campo incompatível com a transferência limitada: '+next.join('.'));
  // The already-sent row is held only by the current bounded batch. Deleting
  // from the original graph releases it as the receiver installs each ACK.
  delete value[key];
 }
}
function v18373ApplyTreeRow(dst,entry){
 if(!Array.isArray(entry)||entry.length!==3||!Array.isArray(entry[0])||
    !entry[0].length||entry[0].length>64)throw Error('Bloco de retorno inválido.');
 const [path,value,kind]=entry;
 if(path.some(k=>typeof k!=='string')||!['v','a','o','s','+'].includes(kind))throw Error('Caminho de retorno inválido.');
 if(kind==='a'&&(!Number.isSafeInteger(value)||value<0||value>4294967295))throw Error('Comprimento de retorno inválido.');
 let parent=dst;
 for(let i=0;i<path.length-1;i++){
  const key=path[i];
  if(!Object.prototype.hasOwnProperty.call(parent,key)||!parent[key]||typeof parent[key]!=='object')throw Error('Contêiner de retorno ausente.');
  parent=parent[key];
 }
 const last=path[path.length-1];
 if(kind==='+'&&(!Object.prototype.hasOwnProperty.call(parent,last)||typeof parent[last]!=='string'||typeof value!=='string'))throw Error('Fragmento de texto sem início.');
 Object.defineProperty(parent,last,{value:kind==='a'?new Array(value):kind==='o'?{}:kind==='s'?'':kind==='+'?parent[last]+value:value,
  writable:true,enumerable:true,configurable:true});
}
'''

WORKER = r'''
/* FUTBR_JOBWAIT_SINGLE_OWNER_18373_WORKER */
let v18373JobWaitWorker=false,v18373JobWaitToken=null;
function v18373WorkerIdentity(s){return {careerId:String(s?.v1903CareerId||''),
 coachId:String(s?.userCoachId||''),user:String(s?.user||''),futbrSaveId:String(s?.futbrSaveId||''),
 year:Number(s?.year),day:Number(s?.day),userEmployed:!!s?.userEmployed,seasonDone:!!s?.seasonDone};}
function v18373WorkerSameJob(a,b){return !!a&&!!b&&!!a.careerId&&a.careerId===b.careerId&&
 a.coachId===b.coachId&&a.user===b.user&&a.futbrSaveId===b.futbrSaveId&&a.userEmployed===b.userEmployed;}
function v18373VerifyJobCheckpoint(stored,token,message){
 const id=v18373WorkerIdentity(stored?.root);
 if(stored?.format!==V171_FORMAT||!token?.token||!Number.isSafeInteger(Number(token.revision))||
    String(stored.token)!==String(token.token)||Number(stored.revision)!==Number(token.revision)||
    !v18373WorkerSameJob(id,token)||id.userEmployed||stored.root?.v640National?.userTeam||
    id.year!==Number(token.year)||id.day!==Number(token.day)||id.seasonDone!==!!token.seasonDone||
    id.year!==Number(message.year)||id.day!==Number(message.day)||
    id.careerId!==String(message.v1903CareerId)||id.user!==String(message.v1903User)||
    Number(stored.year)!==id.year||Number(stored.day)!==id.day||
    !['players','teams','coaches','schedule'].every(k=>stored.collections?.[k]))
  throw Error('O checkpoint da busca não corresponde à carreira e à jornada atuais. Nenhum estado antigo foi simulado.');
 return true;
}
function v18373ApplyJobCoachDelta(delta){
 if(!delta||JSON.stringify(delta).length>160000||!Array.isArray(delta.offers)||
    !Array.isArray(delta.career)||!Array.isArray(delta.news)||!delta.offerMeta||typeof delta.offerMeta!=='object')
  throw Error('Delta de decisões da carreira inválido.');
 world.v636CoachOffers=delta.offers;world.v636CoachOfferMeta=delta.offerMeta;
 world.v636CareerTracker=delta.tracker||null;world.v636CoachCareer=delta.career;world.news=delta.news;
}
function v18373JobTeam(t){
 const row={};for(const k of ['id','name','short','country','division','base','fanPressure','coachId','color','color2','primary','secondary'])
  if(t?.[k]!=null)row[k]=t[k];
 if(t?.stats)row.stats={...t.stats};return row;
}
function v18373JobOverall(t){
 // The active UI uses v704/v702's weighted roster OVR (70/20/10), with
 // base as its empty-roster fallback; the old 5.6 blended formula is obsolete.
 let strength=Math.round(Number(t?.base)||55);try{strength=Number(E.strength(world,t))||strength;}catch(e){}
 return Math.round(strength);
}
function v18373PublishJobProgress(){
 if(!world||!v18373JobWaitWorker)return;
 const jobs=(E.availableJobs(world)||[]).slice(0,18),previous=E.team(world,world.user),ovr={};
 for(const t of jobs)ovr[t.id]=v18373JobOverall(t);
 if(previous)ovr[previous.id]=v18373JobOverall(previous);
 self.postMessage({kind:'jobwait-progress-18373',session,identity:v18373WorkerIdentity(world),
  root:{year:world.year,day:world.day,lastDay:world.lastDay,seed:world.seed,seasonDone:!!world.seasonDone,
   userEmployed:!!world.userEmployed,board:world.board,vacation:world.vacation,news:world.news||[],
   v636CoachOffers:world.v636CoachOffers||[],v636CoachOfferMeta:world.v636CoachOfferMeta||{},
   v636CareerTracker:world.v636CareerTracker||null,v636CoachCareer:world.v636CoachCareer||[]},
  coach:world.coaches?.[world.userCoachId]||null,
  candidates:jobs.map(v18373JobTeam),previous:previous?v18373JobTeam(previous):null,ovr,
  scheduleLength:Number(world.schedule?.length)||0});
}
function v18373ReleaseWorkerGraph(){
 world=null;baseline=null;checkpoint=null;v126TeamSig=v126RosterSig=v126CoachSig=v126CompSig=v126AllSig=v126CompetitionSig=null;
 v126LiveYear=null;v131TeamIndex=null;v128LiveSeq=0;v128LiveAck=0;v131TransferCursor=0;v131CoachMoveCursor=0;v131LiveCounter=0;
 try{National.release?.();}catch(e){}
}
async function v18373ReturnJobWorld(m){
 const point=v18373WorkerIdentity(world),token=m.token;
 if(running||!v18373JobWaitWorker||!world||!v18373WorkerSameJob(point,token)||
    !v18373WorkerSameJob(v18373JobWaitToken,token)||token.token!==v18373JobWaitToken.token||
    Number(token.revision)!==Number(v18373JobWaitToken.revision)||point.userEmployed||
    point.day!==Number(m.day)||point.year!==Number(m.year))
  throw Error('A posse do mundo mudou antes do retorno da busca.');
 if(v150ManualSavePromise)await v150ManualSavePromise;
 const root={},collections=[],totals={players:0,fields:0,batches:0,maxRows:0,maxPlayerBytes:0};
 for(const key in world)if(Object.prototype.hasOwnProperty.call(world,key)){
  const value=world[key];if(value&&typeof value==='object'||typeof value==='string'&&value.length>24576)collections.push(key);else root[key]=value;
 }
 const first=++v18117SyncSeq;
 self.postMessage({kind:'vac-sync-start',session,syncSeq:first,root,collections,
  day:point.day,year:point.year,jobwait18373:true});
 await v18117WaitSyncAck(first);
 for(const key of collections){
  const scalarString=typeof world[key]==='string',value=scalarString?{value:world[key]}:world[key],isArray=Array.isArray(value),length=isArray?value.length:0;
  let total=0;if(key==='players')for(const id in value)if(Object.prototype.hasOwnProperty.call(value,id))total++;
  self.postMessage({kind:'vac-sync-collection-start',session,key,isArray,length,total,jobwait18373:true});
  let rows=[],ids=[],done=0;
  const flush=async()=>{
   if(!rows.length)return;
   let payload=rows;const drop=ids;rows=[];ids=[];const seq=++v18117SyncSeq;
   totals.batches++;totals.maxRows=Math.max(totals.maxRows,payload.length);
   if(key==='players'){
    const packed=await v18310PackVacationRows(payload,false);
    totals.maxPlayerBytes=Math.max(totals.maxPlayerBytes,packed.bytes.byteLength);
    self.postMessage({kind:'vac-sync-part',session,key,done,total,syncSeq:seq,
     format:'player-packed-buffer-v1',bytes:packed.bytes,jobwait18373:true},[packed.bytes]);
    for(const id of drop)delete value[id];
   }else self.postMessage({kind:'vac-sync-part',session,key,rows:payload,done,total,
     syncSeq:seq,format:'tree-path-v1',jobwait18373:true});
   payload=null;
   await v18117WaitSyncAck(seq);
  };
  if(key==='players'){
   for(const id in value)if(Object.prototype.hasOwnProperty.call(value,id)){
    rows.push([id,value[id]]);ids.push(id);done++;
    if(rows.length>=384)await flush();
   }
   totals.players=done;
  }else for(const row of v18373TreeRows(value)){
   rows.push(row);done++;if(rows.length>=64)await flush();
  }
  await flush();world[key]=null;totals.fields++;
  self.postMessage({kind:'vac-sync-collection-end',session,key,done,jobwait18373:true,scalarString});
 }
 // Clear every owning reference before the UI is allowed to render/accept a
 // job or start another worker; do not depend on an arbitrary GC delay.
 v18373ReleaseWorkerGraph();v18373JobWaitWorker=false;v18373JobWaitToken=null;
 const last=++v18117SyncSeq;
 self.postMessage({kind:'vac-sync-end',session,syncSeq:last,day:point.day,year:point.year,
  checkpoint:false,jobwait18373:true,identity:point,totals});
 await v18117WaitSyncAck(last);
 return {ok:true,...point,...totals,released:true};
}
'''

UI = r'''
/* FUTBR_JOBWAIT_SINGLE_OWNER_18373
   The worker is the only complete world while unemployed dates advance.
   The UI holds just the information required by the existing offer policy. */
const v18373JobMemory={phase:'idle',partial:false,token:null,done:null,settle:null,
 starts:0,restores:0,recoveries:0,blocked:0,packets:0,fullStateMessages:0,
 lastError:'',lastReturn:null,uiPlayers:0,uiArchiveYears:0};
function v18373JobIdentity(s=state){return {careerId:String(s?.v1903CareerId||''),
 coachId:String(s?.userCoachId||''),user:String(s?.user||''),futbrSaveId:String(s?.futbrSaveId||''),
 userEmployed:!!s?.userEmployed,year:Number(s?.year),day:Number(s?.day),seasonDone:!!s?.seasonDone};}
function v18373SameJob(a,b){return !!a&&!!b&&!!a.careerId&&a.careerId===b.careerId&&
 a.coachId===b.coachId&&a.user===b.user&&a.futbrSaveId===b.futbrSaveId&&a.userEmployed===b.userEmployed;}
function v18373LightTeam(t){
 const row={};for(const k of ['id','name','short','country','division','base','fanPressure','coachId','color','color2','primary','secondary'])
  if(t?.[k]!=null)row[k]=t[k];
 if(t?.stats)row.stats={...t.stats};return row;
}
function v18373DropUIWorld(){
 if(!state||!v18373JobMemory.token)throw Error('Checkpoint de posse ausente.');
 const me=state.coaches?.[state.userCoachId],teams=(state.teams||[]).map(v18373LightTeam),
  schedule=(state.schedule||[]).map(d=>({type:d?.type,label:d?.label,fixtures:[]})),keep={};
 for(const key of ['v548Access','v622Settings','v636CoachOffers','v636CoachOfferMeta',
  'v636CareerTracker','v636CoachCareer','vacation','news','marketPulse'])
  if(Object.prototype.hasOwnProperty.call(state,key))keep[key]=state[key];
 // Mutate the existing root so old promise/shell references cannot retain
 // players, annual histories, national stats or a former full-world graph.
 for(const key of Object.keys(state))if(state[key]&&typeof state[key]==='object')delete state[key];
 Object.assign(state,keep,{teams,schedule,coaches:me?{[state.userCoachId]:me}:{},players:{},
  competitionStats:{},allTimeStats:{},competitions:{},v640National:{userTeam:null},
  v18373JobWaitPartial:true,v18373JobCandidates:[],v18373JobOVR:{}});
 saved=state;v52PendingState=null;v52MarketIndex=null;v125VacIncoming=null;
 v158ManualPrimePromise=null;v158ManualPrimeDay=-1;v158ManualPrimeYear=-1;
 v93VacCheckpointValid=false;v168DeferredRolloverSave=false;
 v18369VacationReturn=null;v18359FinishedWorld=null;v18357LiveFallback=null;
 try{if(typeof v53PlayerIndex!=='undefined')v53PlayerIndex=null;}catch(e){}
 v18373JobMemory.uiPlayers=0;v18373JobMemory.uiArchiveYears=0;
}
async function v18373BeginJobWait(){
 const runtime=window.GestorFC?.memoryStorage18373;
 if(!runtime?.ensureCheckpoint||!runtime?.setWorkerOwner||!runtime?.restoreOwnerCheckpoint)
  throw Error('O armazenamento seguro da busca não está disponível.');
 v18373JobMemory.phase='preparing';v18373JobMemory.lastError='';
 v18373JobMemory.done=new Promise(resolve=>{v18373JobMemory.settle=resolve;});
 const before=v18373JobIdentity();
 // A migration already between batches still owns its captured old season.
 // Preparing pauses it at the next real yield; join that work before boot.
 if(typeof v555ArchiveMigration!=='undefined'&&v555ArchiveMigration)await v555ArchiveMigration;
 const token=await runtime.ensureCheckpoint(),after=v18373JobIdentity();
 if(!v18373SameJob(before,after)||!v18373SameJob(after,token)||after.userEmployed||
    state?.v640National?.userTeam||after.year!==Number(token.year)||after.day!==Number(token.day)||
    after.seasonDone!==!!token.seasonDone||!token.token||!Number.isSafeInteger(Number(token.revision)))
  throw Error('A carreira mudou durante a preparação da busca. Nenhuma jornada foi iniciada.');
 if(v89JobWait.stop)return false;
 if(!runtime.releaseIdleWorker('jobwait-owner-transfer-18373'))
  throw Error('O salvamento anterior ainda está em andamento.');
 if(!runtime.setWorkerOwner(token))throw Error('Não foi possível assumir o checkpoint da carreira.');
 v18373JobMemory.token={...token};v18373JobMemory.partial=true;v18373JobMemory.starts++;
 v18373DropUIWorld();v18373JobMemory.phase='worker';return true;
}
function v18373ApplyJobProgress(m){
 if(!v18373JobMemory.partial||!state?.v18373JobWaitPartial||
    !v18373SameJob(m.identity,v18373JobMemory.token)||m.identity.userEmployed||
    Number(m.identity.year)<Number(state.year)||
    Number(m.identity.year)===Number(state.year)&&Number(m.identity.day)<Number(state.day))
  throw Error('Pacote de busca de outra carreira ou jornada.');
 Object.assign(state,m.root||{});
 if(m.coach)state.coaches[state.userCoachId]=m.coach;
 const changed=[...(m.candidates||[]),...(m.previous?[m.previous]:[])];
 for(const row of changed){const ix=state.teams.findIndex(t=>t.id===row.id);if(ix>=0)state.teams[ix]=row;else state.teams.push(row);}
 state.v18373JobCandidates=(m.candidates||[]).map(t=>t.id);
 state.v18373JobOVR=m.ovr||{};
 if(Number.isSafeInteger(m.scheduleLength)&&m.scheduleLength>=0)state.schedule.length=m.scheduleLength;
 v53Sim.day=Number(state.day);v18373JobMemory.packets++;v53Stats.patches++;
}
function v18373ReturningOwnMirror(m){
 if(m?.jobwait18373!==true)return false;
 const point=v18373JobIdentity(),incoming=v18373JobIdentity(m.root),token=v18373JobMemory.token;
 if(!v18373JobMemory.partial||v18373JobMemory.phase!=='returning'||!state?.v18373JobWaitPartial||
    !v18373SameJob(point,token)||!v18373SameJob(incoming,token)||
    point.year!==Number(m.year)||point.day!==Number(m.day)||
    incoming.year!==point.year||incoming.day!==point.day)
  throw Error('A devolução não corresponde ao espelho e à posse atuais da carreira.');
 return true;
}
async function v18373RestoreJobCheckpoint(){
 const runtime=window.GestorFC?.memoryStorage18373,token=v18373JobMemory.token;
 v18373JobMemory.phase='recovering';
 v53Sim.active=false;v53Sim.starting=false;v53Sim.syncing=false;v53Sim.patching=false;
 v53Sim.finished=null;v53PatchQueue.length=0;v125VacIncoming=null;v52Processing=false;v53Creating=false;
 // The incomplete stream is never displayed or persisted. Its previous DOM
 // remains mounted while the direct loader reconstructs the durable world.
 v18119CompleteSeasonTransfer();
 if(state){for(const key of Object.keys(state))if(state[key]&&typeof state[key]==='object')delete state[key];}
 state=null;saved=null;v52PendingState=null;
 const restored=await runtime.restoreOwnerCheckpoint(token);
 if(!restored||!v18373SameJob(v18373JobIdentity(restored),token)||!restored.players||
    !Array.isArray(restored.teams)||!Array.isArray(restored.schedule))
  throw Error('Não foi possível recuperar o checkpoint desta carreira.');
 state=restored;saved=restored;v18373JobMemory.recoveries++;
 return true;
}
async function v18373EndJobWait(){
 if(!v18373JobMemory.partial){v18373JobMemory.phase='idle';return true;}
 const runtime=window.GestorFC.memoryStorage18373,token=v18373JobMemory.token;
 try{
  if(!v53Worker)throw Error('O Worker da busca foi encerrado.');
  v18373JobMemory.phase='returning';
  const point=v18373JobIdentity(),result=await v53Call('jobwait-return-18373',{
   token,year:point.year,day:point.day});
  if(!result?.ok||!result.released||!v18373SameJob(v18373JobIdentity(),token)||
     state?.v18373JobWaitPartial||Number(state?.year)!==point.year||Number(state?.day)!==point.day||
     !state.players||!Array.isArray(state.teams)||!Array.isArray(state.schedule))
   throw Error('A devolução completa da carreira não foi confirmada.');
  v18373JobMemory.lastReturn=result;v18373JobMemory.restores++;
 }catch(error){
  v18373JobMemory.lastError=String(error?.message||error);
  await v18373RestoreJobCheckpoint();
  toast('A busca foi pausada e o último checkpoint completo foi recuperado.','warn');
 }
 if(!runtime.clearWorkerOwner(token))throw Error('A posse da carreira não foi liberada.');
 v18373JobMemory.partial=false;v18373JobMemory.phase='idle';v18373JobMemory.token=null;
 runtime.releaseIdleWorker('jobwait-world-returned-18373');
 return true;
}
function v18373JobWaitSettled(){
 const settle=v18373JobMemory.settle;v18373JobMemory.settle=null;settle?.(!v18373JobMemory.partial);
 v18373JobMemory.done=null;
}
async function v18373FinishForSave(){
 if(v89JobWait.active){v89JobWait.stop=true;v89PaintJobWait();}
 const done=v18373JobMemory.done;if(done)await done;
 if(v18373JobMemory.partial)throw Error('A carreira ainda está recuperando seus dados completos.');
 return true;
}
function v18373GuardJobAction(el){
 if(!v18373JobMemory.partial&&v18373JobMemory.phase!=='preparing')return false;
 const action=el?.dataset?.action;
 if(action==='v89-job-wait'||action==='close')return false;
 if(action==='nav'&&el?.dataset?.view==='career'){v89PaintJobWait();return true;}
 v18373JobMemory.blocked++;
 toast('Pare o avanço para abrir os dados completos da carreira. A jornada atual será preservada.','warn');return true;
}
function v18373ArchiveMigrationPaused(){
 const flow=window.GestorFC?.jobWaitMemory18373?.status?.();
 return !!(state?.v18373JobWaitPartial||flow?.ownsWorld||flow?.phase==='preparing');
}
window.GestorFC.jobWaitMemory18373={status:()=>({version:'18.373',phase:v18373JobMemory.phase,
 ownsWorld:v18373JobMemory.partial,starts:v18373JobMemory.starts,restores:v18373JobMemory.restores,
 recoveries:v18373JobMemory.recoveries,blocked:v18373JobMemory.blocked,packets:v18373JobMemory.packets,
 fullStateMessages:v18373JobMemory.fullStateMessages,uiPlayers:v18373JobMemory.uiPlayers,
 uiArchiveYears:v18373JobMemory.uiArchiveYears,lastError:v18373JobMemory.lastError,
 lastReturn:v18373JobMemory.lastReturn,year:state?.year,day:state?.day}),finishForSave:v18373FinishForSave};
'''

UI_GUARDS = r'''
/* FUTBR_JOBWAIT_PARTIAL_UI_GUARDS_18373 */
const v18373BaseClubOverall=v56ClubOverall;
v56ClubOverall=function(s,t){
 if(!t)return 0;
 if(s?.v18373JobWaitPartial){
  const exact=s.v18373JobOVR?.[t.id];
  if(Number.isFinite(exact))return exact;
  throw Error('OVR do Worker indisponível para a busca.');
 }
 return v18373BaseClubOverall(s,t);
};
const v18373BaseAct=act;
act=function(el){
 if(v18373GuardJobAction(el))return;
 return v18373BaseAct(el);
};
const v18373BaseRender=render;
render=function(...args){
 if(v18373JobMemory.partial){v89PaintJobWait();v53PaintStatus();return;}
 return v18373BaseRender(...args);
};
const v18373BaseOfferModal=v636CoachOfferModal;
v636CoachOfferModal=function(...args){if(v18373JobMemory.partial)return;return v18373BaseOfferModal(...args);};
const v18373BaseRecoverTransfer=v18119RecoverLastSave;
v18119RecoverLastSave=async function(){
 if(!v18373JobMemory.partial)return v18373BaseRecoverTransfer();
 try{await v18373RestoreJobCheckpoint();
  if(!window.GestorFC.memoryStorage18373.clearWorkerOwner(v18373JobMemory.token))throw Error('Posse de checkpoint divergente.');
  v18373JobMemory.partial=false;v18373JobMemory.phase='idle';v18373JobMemory.token=null;
  v18119CompleteSeasonTransfer();view='career';render();
 }catch(error){v18119BeginSeasonTransfer();v18119FailSeasonTransfer(error?.message||String(error));}
};
// The named-save script registers its capture listener after this in-scope
// block. Guard it before it can clear state or load another career mid-search.
document.addEventListener('click',event=>{
 const el=event.target?.closest?.('[data-action]');
 if(!el||!v18373GuardJobAction(el))return;
 event.preventDefault();event.stopImmediatePropagation();
},true);
document.addEventListener('change',event=>{
 if(!v18373JobMemory.partial&&v18373JobMemory.phase!=='preparing')return;
 event.preventDefault();event.stopImmediatePropagation();
 toast('Pare o avanço antes de alterar a carreira.','warn');
},true);
window.GestorFC.render=render;
'''


def install(s):
    if MARK in s:
        return s, {'alreadyInstalled': True}
    if 'FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN' not in s:
        raise RuntimeError('18.373 jobwait requires the in-scope bounded storage runtime first')
    s=once(s,' async function simulate(message){',TREE_CODEC+WORKER+'\n async function simulate(message){','worker helpers')
    s=once(s,' async function v126PublishVacationLive(waitAck=true){',
        ' async function v126PublishVacationLive(waitAck=true){\n  if(v18373JobWaitWorker){v18373PublishJobProgress();return;}','compact live path')
    s=once(s,"if(!residentManual&&message.loadSaved){\n   const stored=await read(STORE);\n   if(!stored)throw Error('Ainda nao existe jornada salva para processar.');\n   world=await decode(stored);",
        "if(message.jobWaitAuto===true){\n   if(message.state||message.mode!=='dayfast'||(!residentManual&&!message.loadSaved))throw Error('Busca de propostas exige posse exclusiva e checkpoint verificado.');\n   if(residentManual&&(!v18373JobWaitWorker||!v18373WorkerSameJob(v18373WorkerIdentity(world),v18373JobWaitToken)))throw Error('A posse do Worker de propostas foi perdida.');\n  }\nif(!residentManual&&message.loadSaved){\n   let stored=await read(STORE);\n   if(!stored)throw Error('Ainda nao existe jornada salva para processar.');\n   if(message.jobWaitAuto===true){v18373VerifyJobCheckpoint(stored,message.jobWaitCheckpoint18373,message);v18373JobWaitToken={...message.jobWaitCheckpoint18373};}\n   world=await decode(stored);stored=null;",'verified load')
    s=once(s,"  if(!world)throw Error('Estado da carreira indisponivel no Worker.');",
        "  if(!world)throw Error('Estado da carreira indisponivel no Worker.');\n  v18373JobWaitWorker=message.jobWaitAuto===true;",'ownership mode')
    s=once(s,"  if(nationalJump){\n   const context=message.nationalContext||{},code=String(context.code||'').toUpperCase(),root=world.v640National;",
        "  if(message.jobWaitAuto===true){\n   if(Number(world.year)!==Number(message.year)||Number(world.day)!==Number(message.day)||!v18373WorkerSameJob(v18373WorkerIdentity(world),v18373JobWaitToken))throw Error('Decisões de outra carreira/jornada foram bloqueadas.');\n   v18373ApplyJobCoachDelta(message.jobWaitCoachDelta18373);\n  }\n  if(nationalJump){\n   const context=message.nationalContext||{},code=String(context.code||'').toUpperCase(),root=world.v640National;",'current coach decisions')
    s=once(s," async function handle(m){", " async function handle(m){\n  if(m.op==='jobwait-return-18373')return v18373ReturnJobWorld(m);",'return rpc')
    s=once(s,"   running=false;\n   self.postMessage({kind:'finished',session,error:failure,day:finalDay,year:finalYear,rankPending,",
        "   running=false;\n   if(lowMemoryVacation){message.state=null;v18373ReleaseWorkerGraph();}\n   self.postMessage({kind:'finished',session,error:failure,day:finalDay,year:finalYear,rankPending,",'release before finish')
    # The National toolkit otherwise strongly retains the last world even after world=null.
    s=once(s,'return {before,after,prepare,simulateFixture};',
        'return {before,after,prepare,simulateFixture,release:()=>{current=null;}};','national graph release')
    s=once(s,"const v18370JobSave={interval:4",TREE_CODEC+UI+"\nconst v18370JobSave={interval:4",'in-scope ui')
    s=once(s,"async function v53StartSimulation(mode,options={}){\n", "async function v53StartSimulation(mode,options={}){\n if(v18373JobMemory.partial&&!(mode==='dayfast'&&options?.jobWaitAuto===true))throw Error('Pare a busca antes de iniciar outra simulação.');\n",'partial simulation guard')
    s=once(s,'  const nationalChanged=v148EnsureNationalReady(state);',
        "  const v18373OwnedJob=mode==='dayfast'&&options?.jobWaitAuto===true&&v18373JobMemory.partial;\n  const nationalChanged=v18373OwnedJob?false:v148EnsureNationalReady(state);",'avoid partial national maintenance')
    s=once(s,"  }else if(v18311LiveVacation){clearTimeout(v52SaveTimer);",
        "  }else if(v18373OwnedJob){\n   if(!v18373SameJob(v18373JobIdentity(),v18373JobMemory.token))throw Error('Posse da carreira divergente.');\n  }else if(v18311LiveVacation){clearTimeout(v52SaveTimer);",'skip owned pre-save')
    s=once(s,"  if(!v18311LiveVacation&&state?.v1903CareerId&&!saveOK)",
        "  if(!v18373OwnedJob&&!v18311LiveVacation&&state?.v1903CareerId&&!saveOK)",'owned saved state guard')
    s=once(s,"  const canLoadSaved=!v18311LiveVacation&&!!saveOK&&", "  const canLoadSaved=v18373OwnedJob?!options?.jobWaitResident:!v18311LiveVacation&&!!saveOK&&",'checkpoint first boot')
    s=once(s,"     if(!canLoadSaved&&!(mode==='dayfast'&&options?.jobWaitResident===true))msg.state=state;",
        "     if(v18373OwnedJob){\n      msg.useResident=options?.jobWaitResident===true;msg.jobWaitCheckpoint18373={...v18373JobMemory.token};\n      msg.jobWaitCoachDelta18373={offers:state.v636CoachOffers||[],offerMeta:state.v636CoachOfferMeta||{},tracker:state.v636CareerTracker||null,career:state.v636CoachCareer||[],news:state.news||[]};\n     }else if(!canLoadSaved&&!(mode==='dayfast'&&options?.jobWaitResident===true))msg.state=state;",'never clone owned state')
    s=once(s,"   w.onmessage=event=>{const m=event.data;\n", "   w.onmessage=event=>{if(v53Worker!==w||v18371RetiredWorkers.has(w))return;const m=event.data;\n",'retired worker messages')
    s=once(s,"||m.kind==='vac-live'||m.kind==='vac-dismissed'", "||m.kind==='vac-live'||m.kind==='jobwait-progress-18373'||m.kind==='vac-dismissed'",'queue compact packet')
    s=once(s,"v53Worker=null;v53WorkerReady=null;if(active){v53Creating=true;v53RecoverAfterFailure()",
        "v53Worker=null;v53WorkerReady=null;if(active&&v18373JobMemory.partial){finish?.reject(error);return;}if(active){v53Creating=true;v53RecoverAfterFailure()",'single owner recovery')
    # Change only the final active drainer, not the superseded historical one.
    anchor="   if(m.kind==='vac-checkpoint-error'){v93VacCheckpointValid=false;console.warn('[v93] checkpoint de férias:',m.error||'falhou');continue;}"
    s=once(s,anchor,anchor+"\n   if(m.kind==='jobwait-progress-18373'){v18373ApplyJobProgress(m);v18369PaintOnly(()=>v89PaintJobWait());continue;}",'apply compact packet')
    # This mirror already released all heavy fields before Worker creation.
    # The old purge also terminates an idle simulation Worker and clears its
    # queue, but the return RPC still owns that Worker after dayfast settled.
    s=once(s,"overrides=state?.crestOverrides;v18310ReleaseOldVacationState();",
        "overrides=state?.crestOverrides;\n    if(!v18373ReturningOwnMirror(m))v18310ReleaseOldVacationState();",'preserve return owner and sync queue')
    s=once(s,"state=null;saved=null;v125VacIncoming={...(m.root||{}),v538CareerArchive:archive538||{},v555CareerArchive:archive555||{},scorerArchive:scorers||[],crestOverrides:overrides||{}};",
        "state=null;saved=null;v125VacIncoming=m.jobwait18373?{...(m.root||{})}:{...(m.root||{}),v538CareerArchive:archive538||{},v555CareerArchive:archive555||{},scorerArchive:scorers||[],crestOverrides:overrides||{}};",'return archive roots')
    old="if(m.kind==='vac-sync-part'){if(!v125VacIncoming)continue;const dst=v125VacIncoming[m.key]||(v125VacIncoming[m.key]={}),rows=v18310VacationRows(m);m.bytes=null;for(const [id,row] of rows){if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;}"
    new="if(m.kind==='vac-sync-part'){if(!v125VacIncoming)continue;const dst=v125VacIncoming[m.key]||(v125VacIncoming[m.key]={}),rows=v18310VacationRows(m);m.bytes=null;if(m.format==='tree-path-v1'){for(const row of rows)v18373ApplyTreeRow(dst,row);}else for(const [id,row] of rows){if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;}"
    s=once(s,old,new,'bounded tree receiver')
    drainer=s.index('v53DrainPatches=function(){')
    pre,tail_part=s[:drainer],s[drainer:]
    tail_part=once(tail_part,"   if(m.kind==='vac-sync-collection-end')continue;",
        "   if(m.kind==='vac-sync-collection-end'){if(m.jobwait18373&&m.scalarString&&v125VacIncoming)v125VacIncoming[m.key]=v125VacIncoming[m.key]?.value;continue;}",'root string reassembly')
    s=pre+tail_part
    s=once(s,"v53Sim.progress='Sincronização concluída';refresh=true;forceRefresh=true;continue;",
        "v53Sim.progress='Sincronização concluída';\n    if(m.jobwait18373){\n     if(!v18373SameJob(v18373JobIdentity(),v18373JobMemory.token)||Number(state?.day)!==Number(m.day)||Number(state?.year)!==Number(m.year))throw Error('Retorno de outra carreira/jornada.');\n     v53Worker?.postMessage({op:'vac-sync-ack',seq:Number(m.syncSeq)||0});\n    }\n    refresh=true;forceRefresh=true;continue;",'ack complete returned world')
    s=once(s," const raw=v56OriginalAvailableJobs(s)||[];", " const raw=s?.v18373JobWaitPartial?(s.v18373JobCandidates||[]).map(id=>E.team(s,id)).filter(Boolean):(v56OriginalAvailableJobs(s)||[]);",'original offer candidates')
    s=once(s,"  window.__gfcV172JobWait=true;render();v89PaintJobWait();", "  window.__gfcV172JobWait=true;view='career';render();v89PaintJobWait();",'visible search ui')
    s=once(s,"  try{\n  while(state&&!state.userEmployed&&!state.seasonDone&&!v89JobWait.stop&&!v89HasNationalJob())", "  try{\n  await v18373BeginJobWait();\n  while(state&&!state.userEmployed&&!state.seasonDone&&!v89JobWait.stop&&!v89HasNationalJob())",'checkpoint ownership entry')
    s=once(s,"   // First round sends the authoritative live world exactly once; every\n   // subsequent round uses the resident Worker with matching career/year/day.\n   // Never wait for an entire-world pre-save before the first journey.\n   await v53StartSimulation('dayfast',{\n      liveStateNoPreSave:true,jobWaitResident:v18368SameWorker,jobWaitAuto:true\n   });",
        "   // First round decodes the exact durable token after the UI released all\n   // heavy collections. Later rounds reuse the same complete Worker world.\n   await v53StartSimulation('dayfast',{\n      jobWaitResident:v18368SameWorker,jobWaitAuto:true,jobWaitCheckpoint18373:v18373JobMemory.token\n   });",'no first full-world postmessage')
    end="  v89JobWait.stage='idle';v89JobWait.active=false;try{window.GestorFC?.v170?.release?.();}"
    s=once(s,end,"  try{await v18373EndJobWait();}\n  catch(error){\n   v18373JobMemory.phase='failed';v18373JobMemory.lastError=String(error?.message||error);\n   v89JobWait.stage='recovery-required';v89JobWait.active=false;v89JobWait.stop=true;\n   v18119BeginSeasonTransfer();v18119FailSeasonTransfer(error?.message||String(error));\n   v18373JobWaitSettled();return;\n  }\n  v18373JobWaitSettled();\n"+end,'restore before offers/navigation')
    s=once(s,"function v125DirectAction(el){\n const a=el?.dataset?.action;if(!a)return false;", "function v125DirectAction(el){\n const a=el?.dataset?.action;if(!a)return false;\n if(v18373GuardJobAction(el))return true;",'direct route guard')
    # Bounded mirror must not feed delayed academy/rank builders between rounds.
    s=once(s,"function v91YouthStep(deadline){\n v91YouthTask=0;", "function v91YouthStep(deadline){\n if(v18373JobMemory.partial)return;\n v91YouthTask=0;",'deferred academy guard')
    s=once(s,"function v127RunRankWarm(expectedKey){\n v127RankWarmHandle=0;", "function v127RunRankWarm(expectedKey){\n if(v18373JobMemory.partial)return false;\n v127RankWarmHandle=0;",'rank warm guard')
    # Clearing only the timer does not cancel an already-yielding migration.
    # It holds its old season/ids/packed rows even after the UI root is trimmed.
    a=s.index('let v555ArchiveMigration=null,v555ArchiveMigrationTimer=0;')
    b=s.index('const v555BaseActualClubsByYear=',a)
    migration=s[a:b]
    migration=once(migration,'if(!state||v555ArchiveMigration||v555ArchiveMigrationTimer||v53Sim?.active)return;',
        'if(!state||v555ArchiveMigration||v555ArchiveMigrationTimer||v53Sim?.active||v18373ArchiveMigrationPaused())return;','migration scheduling guard')
    migration=once(migration,'if(!state||v555ArchiveMigration||v53Sim?.active)return false;',
        'if(!state||v555ArchiveMigration||v53Sim?.active||v18373ArchiveMigrationPaused())return false;','migration entry guard')
    if migration.count('if(state!==target||v53Sim?.active)')!=2:
        raise RuntimeError('18.373 migration must have both original yield guards')
    migration=migration.replace('if(state!==target||v53Sim?.active)',
        'if(state!==target||v53Sim?.active||v18373ArchiveMigrationPaused())')
    migration=once(migration,'}target.v555CareerArchive??={};',
        '}if(state!==target||v53Sim?.active||v18373ArchiveMigrationPaused())return changed;target.v555CareerArchive??={};','migration commit guard')
    migration=once(migration,'if(changed&&state===target){',
        'if(changed&&state===target&&!v18373ArchiveMigrationPaused()){','migration persistence guard')
    migration=once(migration,'if(state&&!v53Sim?.active)v555ScheduleArchiveMigration(1200);',
        'if(state&&!v53Sim?.active&&!v18373ArchiveMigrationPaused())v555ScheduleArchiveMigration(1200);','migration reschedule guard')
    s=s[:a]+migration+s[b:]
    tail="\n})();\n</script>\n\n\n\n\n<!-- v43 clean: v130 ranking warmup removed -->"
    s=once(s,tail,'\n'+UI_GUARDS+tail,'last in-scope routes')
    return s, {'alreadyInstalled':False,'sameGameScope':True,'verifiedCheckpointBoot':True,
        'fullWorldJobwaitMessages':0,'singleCompleteWorldOwner':True,'losslessBoundedReturn':True,
        'residentDaysAndFourDayCheckpoints':True,'fullWorldBeforeOffersAndNavigation':True,
        'noHistoryTruncation':True,'inFlightArchiveMigrationGuarded':True,
        'returnOwnerSurvivesLegacyCleanup':True}


def main():
    root=Path(sys.argv[1]);path=root/'src/index.html'
    s,report=install(path.read_text(encoding='utf-8'))
    path.write_text(s,encoding='utf-8')
    report={'ok':True,'version':'18.373.0',**report}
    (root/'jobwait-memory-transfer-18373-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()
