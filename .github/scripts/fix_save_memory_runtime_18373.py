"""Install the bounded save/load runtime inside the actual career closure.

The legacy 17.0/17.1 script elements refer to private UI bindings from outside
their closure and never install. This patch deliberately installs only storage,
lossless archive codecs and guarded idle-worker disposal, not their old wrappers.
"""
from pathlib import Path
import json
import sys


MARKER = 'FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN'
ARCHIVE_CODEC = r'''/* FUTBR_PACKED_ARCHIVE_PATHS_18373
   A packed v555 year is {n:names,p:{playerId:statsString}}. Names can be an
   object or a legacy array. Its p map is
   NOT one record: persist each player and each name separately. Explicit
   container rows preserve empty objects, sparse arrays, lengths and nulls. */
function* v18373StructuredArchiveRows(value,key){
 const own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 const depth=key==='scorerArchive'?4:key==='competitionStats'?2:3;
 function* walk(path,row){
  const plain=row&&typeof row==='object'&&(Array.isArray(row)||
   Object.prototype.toString.call(row)==='[object Object]');
  if(!plain||path.length>=depth){yield [path,row,'v'];return;}
  yield [path,Array.isArray(row)?row.length:null,Array.isArray(row)?'a':'o'];
  for(const id in row)if(own(row,id))yield* walk([...path,id],row[id]);
 }
 for(const id in value)if(own(value,id))yield* walk([id],value[id]);
}
function* v18373PackedArchiveRows(value){yield* v18373StructuredArchiveRows(value,'v555CareerArchive');}
function v18373ApplyArchivePath(dst,entry){
 if(!Array.isArray(entry)||entry.length!==3||!Array.isArray(entry[0])||
    entry[0].length<1||entry[0].length>8)throw Error('Bloco de histórico inválido.');
 const [path,value,kind]=entry;
 if(!['v','a','o'].includes(kind)||path.some(k=>typeof k!=='string'))
  throw Error('Caminho de histórico inválido.');
 let parent=dst;
 for(let i=0;i<path.length-1;i++){
  const k=path[i];
  if(!Object.prototype.hasOwnProperty.call(parent,k)||!parent[k]||typeof parent[k]!=='object')
   throw Error('Contêiner do histórico ausente.');
  parent=parent[k];
 }
 if(kind==='a'&&(!Number.isSafeInteger(value)||value<0||value>4294967295))
  throw Error('Comprimento de histórico inválido.');
 const row=kind==='a'?new Array(value):kind==='o'?{}:value;
 // defineProperty treats even a literal __proto__ as data, without traversing
 // inherited properties or changing any prototype.
 Object.defineProperty(parent,path[path.length-1],{value:row,writable:true,enumerable:true,configurable:true});
}
'''


WORKER_HISTORY = r'''/* FUTBR_VACATION_HISTORY_WRITER_18373
   A deferred new season can start vacation before its previous-year archive
   reaches disk. Preserve those live histories before publishing the vacation
   manifest; reusing last year's older collection would silently lose a year. */
async function v18373WriteHistoryCollection(token,key,value,previous){
 const path=key!=='v538CareerArchive',nested=key==='v555CareerArchive'?'year-path-v1':
  path?'tree-path-v1':'year-id-v1',isArray=Array.isArray(value),keys=[],hashes=[];
 const compatible=previous?.nested===nested&&!!previous.isArray===isArray?previous:null;
 let rows=[],index=0;
 async function flush(){
  if(!rows.length)return;
  const batch=rows;rows=[];const at=index++,hash=await v18343Fingerprint(batch);hashes.push(hash);
  if(hash&&compatible?.hashes?.[at]===hash&&compatible.keys?.[at]){keys.push(compatible.keys[at]);return;}
  const ck=STORE+':v171:'+token+':'+key+':'+at;
  await v18181RawWriteMany([{key:ck,value:batch}]);keys.push(ck);
  await new Promise(resolve=>setTimeout(resolve,0));
 }
 if(path){for(const row of v18373StructuredArchiveRows(value,key)){rows.push(row);if(rows.length>=128)await flush();}}
 else for(const year in value){
  if(!Object.prototype.hasOwnProperty.call(value,year))continue;const records=value[year];
  if(records&&typeof records==='object'&&!Array.isArray(records)){
   let count=0;
   for(const id in records)if(Object.prototype.hasOwnProperty.call(records,id)){
    rows.push([year,id,records[id]]);count++;if(rows.length>=128)await flush();
   }
   if(!count)rows.push([year,null,{},1]);
  }else rows.push([year,null,records,0]);
  if(rows.length>=128)await flush();
 }
 await flush();return {isArray,length:isArray?value.length:0,keys,hashes,
  archiveHash:'sha256-json-v1',nested};
}
async function v18373WriteCheckpointHistories(s,old,token){
 const collections={},root={};
 for(const key of ['v538CareerArchive','v555CareerArchive','scorerArchive']){
  if(!Object.prototype.hasOwnProperty.call(s||{},key))continue;
  const value=s[key];
  if(value===null||typeof value!=='object'){root[key]=value;continue;}
  collections[key]=await v18373WriteHistoryCollection('vac-history-'+token,key,value,old?.collections?.[key]);
 }
 return {collections,root};
}
'''


UI_RUNTIME = r'''/* FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN
   This is INSIDE the original career IIFE. One UI world, bounded storage
   chunks and no full-world save RPC. A worker's post-finish save must settle
   before its memory can be released. */
(()=>{
 'use strict';
 const G=window.GestorFC=window.GestorFC||{},KEY=STORE,FORMAT='GFC_SHARDED_171';
 const SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats',
  'v538CareerArchive','v555CareerArchive','scorerArchive','transfers','retirements',
  'history','internationalHistory','v735NationalArchive','crestOverrides'];
 const SHARD_SET=new Set(SHARDS),own=(o,k)=>Object.prototype.hasOwnProperty.call(o,k);
 const stats={version:'18.373',sameGameScope:true,noFullStateSaveRPC:true,fullSaves:0,
  reusedCheckpoints:0,cleanWorkerSettlements:0,coachAutosavesJoined:0,
  coachAutosavesConfirmed:0,coachAutosaveRetries:0,coachAutosavesAfterOlderWriter:0,
  chunksWritten:0,chunksReused:0,playerChunksWritten:0,
  maxRowsPerChunk:0,maxEncodedChunkBytes:0,maxTransactionChunks:0,
  lastSaveMs:0,lastLoadMs:0,lastMode:'',workerReleases:0,cachePurges:0,
  failed:0,cleanupFailed:0,lastError:'',lastHeapMiB:null};
 let mutation=0,writeTicket=0,owner=null,loading=false,explicitEnsure=null;
 const yieldUI=()=>new Promise(resolve=>setTimeout(resolve,0));
 const heap=()=>performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null;
 const identify=s=>({careerId:String(s?.v1903CareerId||''),coachId:String(s?.userCoachId||''),
  user:String(s?.user||''),futbrSaveId:String(s?.futbrSaveId||''),userEmployed:!!s?.userEmployed,
  year:Number(s?.year),day:Number(s?.day),seasonDone:!!s?.seasonDone});
 const sameJob=(a,b)=>!!a&&!!b&&a.careerId===b.careerId&&a.coachId===b.coachId&&
  a.user===b.user&&a.futbrSaveId===b.futbrSaveId&&a.userEmployed===b.userEmployed;
 const samePoint=(a,b)=>sameJob(a,b)&&a.year===b.year&&a.day===b.day&&a.seasonDone===b.seasonDone;
 const sameOwner=(a,b)=>sameJob(a,b)&&a.token===b.token&&Number(a.revision)===Number(b.revision);
 function idle(allowStarting=false){
  return !v53Sim?.active&&(!v53Sim?.starting||allowStarting)&&!v53Sim?.syncing&&!v53Sim?.patching&&
   !v125VacIncoming&&!v52Processing&&!v53PatchQueue?.length&&
   !(typeof v18119SeasonTransfer!=='undefined'&&v18119SeasonTransfer?.active)&&
   !(typeof v18370JobSave!=='undefined'&&v18370JobSave.busy);
 }
 function purgeDerived(){
  const s=state;if(!s)return;
  try{v127CancelRankWarm();}catch(e){}
  try{clearTimeout(v91YouthTimer);v91YouthTimer=0;v168CancelIdle(v91YouthTask);v91YouthTask=0;}catch(e){}
  try{clearTimeout(v91DeferredSaveTimer);v91DeferredSaveTimer=0;v91SeasonSaveWaiting=false;}catch(e){}
  try{clearTimeout(v86RefreshTimer);v86RefreshTimer=0;v168CancelIdle(v86RankTask);v86RankTask=0;v86RankToken++;}catch(e){}
  try{clearTimeout(v88RefreshTimer);v88RefreshTimer=0;v168CancelIdle(v88RefreshTask);v88RefreshTask=0;v88RefreshToken++;}catch(e){}
  try{clearTimeout(v89RankTimer);v89RankTimer=0;clearTimeout(v89ChallengeTask);v89ChallengeTask=0;
   clearTimeout(v89BuildWatch);v89BuildWatch=0;v89ChallengeToken++;}catch(e){}
  try{clearTimeout(v555ArchiveMigrationTimer);v555ArchiveMigrationTimer=0;}catch(e){}
  // Reuse only the in-scope cache invalidator, never v168StopBackground:
  // that older stop helper can terminate a deferred storage transaction.
  try{stats.cachePurges+=v168DropStateCaches(s)||0;}catch(e){}
  try{E.invalidateMarket(s);}catch(e){}
  v52MarketIndex=null;v555CoachCache={state:null,key:'',html:''};
  v555MarketWarmJob=null;v555MarketWarmListJob=null;v555ShellState=null;v260ShellLockedState=null;
 }
 function releaseIdleWorker(reason='idle',preparing=false,recoverOwner=false){
  if(owner&&!recoverOwner||!idle(preparing)||(!preparing&&v53Creating)||v53Worker?.v18373CheckpointBusy||
     v18371BlockingWorkerRequest()||v143PostRankPending)return false;
  const worker=v53Worker;
  if(worker){
   worker.terminate();
   if(v53Worker===worker){v53Worker=null;v53WorkerReady=null;v53WorkerFailed=false;}
   stats.workerReleases++;
  }
  v158ManualPrimePromise=null;v158ManualPrimeDay=-1;v158ManualPrimeYear=-1;
  purgeDerived();stats.lastRelease=String(reason);stats.lastHeapMiB=heap();return true;
 }
 async function settleWorker(){
  const worker=v53Worker;if(!worker)return;
  if(!idle(true))throw Error('Aguarde a simulação terminar antes de salvar.');
  // This small RPC queues after simulation and awaits a deferred manual save.
  // It contains neither state nor players, and does not create a new Worker.
  await v53Call('settle-storage-18373');
  if(v53Worker!==worker)throw Error('O motor mudou durante o salvamento. Tente novamente.');
  worker.v18373CheckpointBusy=false;
  if(!releaseIdleWorker('before-sharded-save',true))
   throw Error('Uma operação da carreira ainda está em andamento.');
 }
 async function readRaw(key){return v52ReadRaw(key);}
 async function readMany(keys){
  if(!keys.length)return [];
  if(window.FutBRDesktop?.directStorage){
   if(typeof window.FutBRDesktop.readMany==='function')return window.FutBRDesktop.readMany(keys);
   const out=[];for(const key of keys)out.push(await window.FutBRDesktop.read(key));return out;
  }
  const db=await openDB();
  return new Promise((resolve,reject)=>{
   const out=new Array(keys.length),tx=db.transaction('saves','readonly'),os=tx.objectStore('saves');
   keys.forEach((key,i)=>{const req=os.get(key);req.onsuccess=()=>{out[i]=req.result;};});
   tx.oncomplete=()=>resolve(out);tx.onerror=()=>reject(tx.error||Error('Falha ao ler o save.'));
   tx.onabort=()=>reject(tx.error||Error('Leitura interrompida.'));
  });
 }
 async function writeMany(entries){
  if(!entries.length)return;
  stats.maxTransactionChunks=Math.max(stats.maxTransactionChunks,entries.length);
  if(window.FutBRDesktop?.directStorage){await window.FutBRDesktop.writeMany(entries);return;}
  const db=await openDB();
  await new Promise((resolve,reject)=>{
   const tx=db.transaction('saves','readwrite'),os=tx.objectStore('saves');
   for(const e of entries)os.put(e.value,e.key);
   tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error||Error('Falha ao gravar o bloco.'));
   tx.onabort=()=>reject(tx.error||Error('Gravação interrompida.'));
  });
 }
 async function removeMany(keys){
  if(!keys.length)return;
  if(window.FutBRDesktop?.directStorage){await window.FutBRDesktop.removeMany(keys);return;}
  const db=await openDB();
  await new Promise((resolve,reject)=>{
   const tx=db.transaction('saves','readwrite'),os=tx.objectStore('saves');
   for(const key of keys)os.delete(key);
   tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error||Error('Falha na limpeza.'));
   tx.onabort=()=>reject(tx.error||Error('Limpeza interrompida.'));
  });
 }
 function keysOf(m){
  const keys=[];if(m?.format===FORMAT)for(const spec of Object.values(m.collections||{}))
   for(const key of spec?.keys||[])keys.push(key);return keys;
 }
 async function commit(manifest,old,meta,check){
  check();
  if(window.FutBRDesktop?.directStorage){
   await window.FutBRDesktop.commitManifest(KEY,manifest,old,meta);return;
  }
  const db=await openDB();
  await new Promise((resolve,reject)=>{
   const tx=db.transaction('saves','readwrite'),os=tx.objectStore('saves'),req=os.get(KEY);
   req.onsuccess=()=>{
    try{check();}catch(error){try{tx.abort();}catch(e){}return;}
    // Never overwrite a concurrent tab's newer checkpoint.
    if(String(req.result?.token||'')!==String(old?.token||'')){
     try{tx.abort();}catch(e){}return;
    }
    os.put(old||null,KEY+':previous');os.put(manifest,KEY);os.put(meta,KEY+':meta');
   };
   tx.oncomplete=()=>resolve();tx.onerror=()=>reject(tx.error||Error('Falha ao confirmar o save.'));
   tx.onabort=()=>reject(tx.error||Error('O checkpoint mudou durante o salvamento.'));
  });
 }
 async function fingerprint(rows){
  let text;
  try{text=JSON.stringify(rows,(k,v)=>{
   if(typeof v==='undefined'||typeof v==='bigint'||typeof v==='function'||
      typeof v==='symbol'||typeof v==='number'&&!Number.isFinite(v)||
      v&&typeof v==='object'&&(v instanceof ArrayBuffer||ArrayBuffer.isView(v)||
       v instanceof Map||v instanceof Set))throw Error('non-JSON');return v;
  });}catch(e){return null;}
  stats.maxEncodedChunkBytes=Math.max(stats.maxEncodedChunkBytes,new TextEncoder().encode(text).byteLength);
  if(!globalThis.crypto?.subtle)return null;
  const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
  return Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,'0')).join('');
 }
 function applyLegacyArchive(dst,entry){
  if(!Array.isArray(entry)||entry.length<3)throw Error('Bloco de histórico legado inválido.');
  const year=String(entry[0]),id=entry[1];
  if(id===null){Object.defineProperty(dst,year,{value:entry[3]===1?{}:entry[2],
   writable:true,enumerable:true,configurable:true});return;}
  if(!own(dst,year))Object.defineProperty(dst,year,{value:{},writable:true,enumerable:true,configurable:true});
  if(!dst[year]||typeof dst[year]!=='object'||Array.isArray(dst[year]))throw Error('Ano histórico inválido.');
  Object.defineProperty(dst[year],String(id),{value:entry[2],writable:true,enumerable:true,configurable:true});
 }
 /* ARCHIVE_CODEC_INSERT */
 async function writeCollection(token,key,value,previous,check){
  const isArray=Array.isArray(value),path=['v555CareerArchive','scorerArchive','competitionStats'].includes(key),nested=key==='v538CareerArchive';
  const nestedFormat=key==='v555CareerArchive'?'year-path-v1':path?'tree-path-v1':nested?'year-id-v1':null;
  const limit=path||nested?128:key==='players'?(Number(state?.year)>=2029?512:768):
   key==='schedule'||key==='competitionStats'?2:key==='scorerArchive'||key==='v735NationalArchive'?1:
   key==='teams'||key==='coaches'?128:256;
  const compatible=previous&&!!previous.isArray===isArray&&
   (previous.nested||null)===nestedFormat&&
   (key!=='players'||previous.encoding===v18191uPlayerFormat)?previous:null;
  const keys=[],hashes=[];let rows=[],index=0;
  async function flush(){
   if(!rows.length)return;
   check();const raw=rows;rows=[];const at=index++,hash=await fingerprint(raw);hashes.push(hash);
   stats.maxRowsPerChunk=Math.max(stats.maxRowsPerChunk,raw.length);
   if(hash&&compatible?.hashes?.[at]===hash&&compatible.keys?.[at]){
    keys.push(compatible.keys[at]);stats.chunksReused++;return;
   }
   const payload=key==='players'?await v18191uEncodePlayerChunk(raw):raw;
   const ck=KEY+':v171:'+token+':'+key+':'+at;
   if(typeof payload?.data==='string')stats.maxEncodedChunkBytes=Math.max(stats.maxEncodedChunkBytes,payload.data.length);
   check();await writeMany([{key:ck,value:payload}]);keys.push(ck);stats.chunksWritten++;
   if(key==='players')stats.playerChunksWritten++;
   await yieldUI();
  }
  const push=async row=>{rows.push(row);if(rows.length>=limit)await flush();};
  if(path){for(const row of v18373StructuredArchiveRows(value,key))await push(row);}
  else if(nested){
   for(const year in value){if(!own(value,year))continue;const records=value[year];
    if(records&&typeof records==='object'&&!Array.isArray(records)){
     let count=0;for(const id in records)if(own(records,id)){await push([year,id,records[id]]);count++;}
     if(!count)await push([year,null,{},1]);
    }else await push([year,null,records,0]);
   }
  }else for(const id in value)if(own(value,id))await push([id,value[id]]);
  await flush();
  return {isArray,length:isArray?value.length:0,keys,hashes,archiveHash:'sha256-json-v1',
   ...(nestedFormat?{nested:nestedFormat}:null),...(key==='players'?{encoding:v18191uPlayerFormat}:null)};
 }
 async function saveSharded(current){
  if(owner)throw Error('O motor de propostas ainda está devolvendo o mundo completo.');
  if(loading)throw Error('Uma carreira ainda está sendo carregada.');
  const started=performance.now(),origin=identify(current),generation=mutation;
  const check=()=>{
   if(state!==current||mutation!==generation||!samePoint(identify(current),origin)||owner||!idle(true))
    throw Error('A carreira mudou durante o salvamento. O checkpoint anterior foi preservado.');
  };
  check();await settleWorker();check();purgeDerived();
  const old=await readRaw(KEY),oldMeta=await readRaw(KEY+':meta');
  // Keep only previous shard names in memory; its old root is not needed.
  const obsolete=keysOf(await readRaw(KEY+':previous'));
  const token=[origin.year,origin.day,'ui18373',Date.now(),Math.random().toString(36).slice(2,8)].join('-');
  const root={},collections={};
  for(const key in current)if(own(current,key)&&!SHARD_SET.has(key))root[key]=current[key];
  try{
   for(const key of SHARDS){
    if(!own(current,key))continue;const value=current[key];
    // Preserve null and scalar values too; do not silently omit unknown data.
    if(value===null||typeof value!=='object'){root[key]=value;continue;}
    collections[key]=await writeCollection(token,key,value,old?.format===FORMAT?old.collections?.[key]:null,check);
   }
   check();const meta={at:Date.now(),year:origin.year,day:origin.day,
    revision:Math.max(Number(old?.revision)||0,Number(oldMeta?.revision)||0)+1,format:FORMAT};
   const manifest={format:FORMAT,version:1,token,revision:meta.revision,at:meta.at,
    year:origin.year,day:origin.day,root,collections};
   await commit(manifest,old,meta,check);
   stats.fullSaves++;stats.lastSaveMs=Math.round(performance.now()-started);stats.lastMode='ui-bounded-shards';
   stats.lastHeapMiB=heap();
   const keep=new Set([...keysOf(manifest),...keysOf(old)]),stale=obsolete.filter(k=>!keep.has(k));
   // Cleanup is AFTER the new manifest and previous checkpoint commit. No
   // valid checkpoint is deleted if a shard or manifest write fails.
   for(let i=0;i<stale.length;i+=80){try{await removeMany(stale.slice(i,i+80));}catch(e){stats.cleanupFailed++;break;}await yieldUI();}
   return {...meta,token,bytes:0,ms:stats.lastSaveMs,storage:'bounded UI shards 18.373'};
  }catch(error){stats.failed++;stats.lastError=String(error?.message||error);throw error;}
 }
 async function hydrateManifest(manifest,progress=null){
  if(manifest?.format!==FORMAT)return null;
  const out={...(manifest.root||{})},entries=Object.entries(manifest.collections||{});
  for(let ci=0;ci<entries.length;ci++){
   const [key,spec]=entries[ci],keys=spec?.keys||[];
   if(!Array.isArray(keys))throw Error('Índice de blocos inválido.');
   const dst=spec?.isArray?new Array(Number(spec.length)||0):{};
   // One chunk at a time, including legacy chunks. Never materialize 8-16
   // compressed and decoded player/history chunks concurrently.
   for(let i=0;i<keys.length;i++){
    let rows=(await readMany([keys[i]]))[0];
    if(rows==null)throw Error('Bloco do save ausente: '+key+'. O arquivo não foi alterado.');
    if(key==='players'&&rows?.format===v18191uPlayerFormat)rows=await v18191uDecodePlayerChunk(rows);
    if(!Array.isArray(rows))throw Error('Bloco do save inválido: '+key+'.');
    for(const entry of rows){
     if(spec.nested==='year-path-v1'||spec.nested==='tree-path-v1'){v18373ApplyArchivePath(dst,entry);continue;}
     if(spec.nested==='year-id-v1'){applyLegacyArchive(dst,entry);continue;}
     if(!Array.isArray(entry)||entry.length<2)throw Error('Registro do save inválido.');
     Object.defineProperty(dst,String(entry[0]),{value:entry[1],writable:true,enumerable:true,configurable:true});
    }
    rows=null;
    try{progress?.({key,done:i+1,total:keys.length,collection:ci+1,collections:entries.length});}catch(e){}
    if(i+1<keys.length)await yieldUI();
   }
   Object.defineProperty(out,key,{value:dst,writable:true,enumerable:true,configurable:true});
  }
  return out;
 }
 async function loadDirect(progress=null,allowOwner=false){
  if(owner&&!allowOwner)throw Error('Aguarde o retorno completo da busca de propostas.');
  if(loading||v52SavePromise)throw Error('Aguarde o salvamento ou carregamento atual.');
  loading=true;const started=performance.now();
  try{
   if(!releaseIdleWorker('direct-load'))throw Error('O motor ainda controla a carreira.');
   const manifest=await readRaw(KEY);
   const out=await hydrateManifest(manifest,progress);stats.lastLoadMs=Math.round(performance.now()-started);
   stats.lastHeapMiB=heap();return out;
  }finally{loading=false;}
 }
 const previousRead=dbRead;
 dbRead=async function(key){
  const value=await previousRead(key);
  return value?.format===FORMAT?hydrateManifest(value):value;
 };
 function tokenFor(manifest){return {...identify(manifest.root),token:String(manifest.token||''),
  revision:Number(manifest.revision)||0};}
 async function ensureCheckpoint(){
  if(explicitEnsure)return explicitEnsure;
  const task=(async()=>{
   if(owner)throw Error('A interface parcial de propostas não pode substituir o save.');
   if(!state||!idle()||v53Creating||loading)throw Error('Aguarde a conclusão da carreira antes de salvar.');
   const current=state,origin=identify(current);
   if(!origin.careerId||!origin.coachId)throw Error('A identidade da carreira não está disponível.');
   if(v52SavePromise)await v52SavePromise;
   let manifest=await readRaw(KEY);
   const clean=manifest?.format===FORMAT&&samePoint(tokenFor(manifest),origin)&&saveOK&&
    !v52SaveDirty&&!v52SavePromise&&!v168DeferredRolloverSave;
   if(!clean){
    const pending=persist(false);await v52FlushSave();await pending;
    if(v52SavePromise)await v52SavePromise;
    manifest=await readRaw(KEY);
   }else{stats.reusedCheckpoints++;if(v52PendingState===current)v52PendingState=null;}
   if(state!==current||owner||!samePoint(identify(state),origin)||manifest?.format!==FORMAT||
      !samePoint(tokenFor(manifest),origin)||!saveOK||v52SaveDirty||v52SavePromise)
    throw Error('O checkpoint não corresponde à carreira atual. O save anterior foi preservado.');
   v168DeferredRolloverSave=false;return tokenFor(manifest);
  })();
  explicitEnsure=task;try{return await task;}finally{if(explicitEnsure===task)explicitEnsure=null;}
 }
 function setWorkerOwner(token){
  if(owner)throw Error('O motor já controla uma busca de propostas.');
  if(!token?.token||!samePoint(token,identify(state))||!idle()||v52SaveDirty||v52SavePromise)
   throw Error('Checkpoint desatualizado para assumir a carreira.');
  owner={...token};purgeDerived();return true;
 }
 function clearWorkerOwner(token){
  if(!owner||!sameOwner(owner,token)||state?.v18373JobWaitPartial||!state?.players||
     !Array.isArray(state.teams)||!Array.isArray(state.schedule))return false;
  owner=null;return true;
 }
 async function restoreOwnerCheckpoint(token,progress=null){
  if(!owner||!sameOwner(owner,token))throw Error('A posse da carreira mudou durante a recuperação.');
  if(!releaseIdleWorker('restore-owner',false,true))throw Error('O motor ainda está concluindo uma operação.');
  const manifest=await readRaw(KEY);
  if(manifest?.format!==FORMAT||!sameJob(tokenFor(manifest),owner)||
     Number(manifest.year)<owner.year||Number(manifest.year)===owner.year&&Number(manifest.day)<owner.day)
   throw Error('O checkpoint disponível pertence a outro vínculo ou é anterior à busca.');
  // The caller still owns the token and decides when the complete returned
  // world replaces its light mirror. Never clear ownership before that point.
  if(loading||v52SavePromise)throw Error('Outra leitura ou gravação está em andamento.');
  loading=true;try{return await hydrateManifest(manifest,progress);}finally{loading=false;}
 }
 const previousPersist=persist;
 persist=function(...args){
  if(owner)return Promise.resolve(false);
  mutation++;return previousPersist.apply(this,args);
 };
 // A job-search schedules this notification for 60 seconds later. The timer
 // does not edit the career. Calling persist again during an explicit save
 // would increment its mutation generation and invalidate the same save it
 // intends to confirm. Join the existing writer, checking its actual manifest
 // and result; genuine edits still pass through persist and invalidate it.
 v93ScheduleCoachDecisionSave=function(delay=60000){
  clearTimeout(v93CoachSaveTimer);
  // A decision scheduled DURING a writer may not be in its captured root.
  // Keep only its numeric ticket, never retain a career in the 60-second timer.
  const writerAtSchedule=v52SavePromise?writeTicket:0;
  v93CoachSaveTimer=setTimeout(async()=>{
   v93CoachSaveTimer=0;
   if(!state||!idle()||owner||v53Creating||v89JobWait?.active||modalKind==='coach-offers')
    return v93ScheduleCoachDecisionSave(10000);
   const pending=v52SavePromise;
   if(!pending){persist(false).catch(()=>{});return;}
   const current=state,origin=identify(current),generation=mutation;
   const olderWriter=writerAtSchedule!==0&&writerAtSchedule===writeTicket;
   stats.coachAutosavesJoined++;
   try{
    await pending;
    if(state!==current||!sameJob(identify(current),origin))return;
    if(olderWriter&&!v52SavePromise){
     stats.coachAutosavesAfterOlderWriter++;
     persist(false).catch(()=>{});return;
    }
    const manifest=await readRaw(KEY);
    if(state!==current||!sameJob(identify(current),origin))return;
    if(mutation===generation&&samePoint(identify(current),origin)&&
       manifest?.format===FORMAT&&samePoint(tokenFor(manifest),origin)&&
       saveOK&&!v52SaveDirty&&!v52SavePromise){
     stats.coachAutosavesConfirmed++;return;
    }
   }catch(error){/* A failed writer cannot confirm this autosave. */}
   if(state===current&&sameJob(identify(current),origin)){
    stats.coachAutosaveRetries++;v93ScheduleCoachDecisionSave(10000);
   }
  },Math.max(10000,Number(delay)||60000));
 };
 v52FlushSave=async function(){
  clearTimeout(v52SaveTimer);v52SaveTimer=null;
  if(v52SavePromise)return v52SavePromise;
  if(owner||loading||v53Sim?.active||v53Sim?.syncing||v53Sim?.patching||v125VacIncoming)return;
  if(!v52PendingState||!v52SaveDirty){
   if(!v53Worker?.v18373CheckpointBusy)return;
   // Named loading awaits flush before terminating the old Worker. A manual
   // day can have no UI edits while its post-finished checkpoint still writes.
   // Join that save even on a clean flush; concurrent callers share the wait.
   writeTicket++;
   const task=(async()=>{
    try{await settleWorker();stats.cleanWorkerSettlements++;}
    finally{if(v52SavePromise===task)v52SavePromise=null;updateSaveStatus();}
    // An edit made during the wait must also reach disk before a caller may
    // replace the career. Do not let a newly dirty state pass a clean flush.
    if(!owner&&v52PendingState&&v52SaveDirty)return v52FlushSave();
   })();v52SavePromise=task;return task;
  }
  const current=v52PendingState,waiters=v52SaveWaiters.splice(0),notify=v52NotifySave;
  v52NotifySave=false;v52SaveDirty=false;
  writeTicket++;
  const task=(async()=>{
   try{
    v5CrestsOut();const result=await saveSharded(current);v53Saved(result);
    if(notify)toast('Carreira salva.');
   }catch(error){saveOK=false;v52SaveStats.failed++;
    stats.lastError=String(error?.message||error);toast('Falha ao salvar: '+stats.lastError,'error');
   }finally{
    if(saveOK&&!v52SaveDirty&&v52PendingState===current)v52PendingState=null;
    v52SavePromise=null;waiters.forEach(resolve=>resolve());updateSaveStatus();
    if(v52SaveDirty&&!owner){clearTimeout(v52SaveTimer);v52SaveTimer=setTimeout(v52FlushSave,250);}
   }
  })();v52SavePromise=task;return task;
 };
 // Do not keep a second full world resident while the user plays a match.
 v158PrimeManualWorker=function(){return Promise.resolve(false);};
 const previousStart=v53StartSimulation;
 v53StartSimulation=async function(...args){
  if(v52SavePromise)await v52SavePromise;
  if(loading)throw Error('Aguarde o carregamento da carreira.');
  return previousStart.apply(this,args);
 };
 const previousCall=v53Call;
 v53Call=async function(op,params={}){
  if(op==='save')throw Error('Use o salvamento fragmentado da carreira.');
  return previousCall.call(this,op,params);
 };
 const storageAudit=async()=>{
  const m=await readRaw(KEY);return {format:m?.format||null,...(m?.format===FORMAT?tokenFor(m):{}),
   collections:Object.fromEntries(Object.entries(m?.collections||{}).map(([key,spec])=>[key,
    {chunks:spec.keys?.length||0,isArray:!!spec.isArray,length:Number(spec.length)||0,nested:spec.nested||null}])),
   heapMiB:heap(),workerResident:!!v53Worker};
 };
 G.memoryStorage18373={ensureCheckpoint,releaseIdleWorker:reason=>releaseIdleWorker(reason),
  setWorkerOwner,clearWorkerOwner,restoreOwnerCheckpoint,
  applyHistoryRow:(dst,row,format)=>format==='year-path-v1'||format==='tree-path-v1'?v18373ApplyArchivePath(dst,row):
   format==='year-id-v1'?applyLegacyArchive(dst,row):(()=>{throw Error('Formato de histórico desconhecido.');})(),
  status:()=>({...stats,owner:owner?{...owner}:null,loading,saving:!!v52SavePromise,
   dirty:!!v52SaveDirty,workerResident:!!v53Worker,heapMiB:heap()})};
 G.v171={...(G.v171||{}),version:'18.373',storageKey:KEY,loadDirect,hydrateManifest,storageAudit,
  stats:()=>G.memoryStorage18373.status(),memory:{shardedSnapshots:true,directIncrementalLoad:true,
   noWorkerWorldCloneOnLoad:true,noFullStatePostMessageOnPersist:true,packedAnnualHistoryBounded:true}};
 G.v170={...(G.v170||{}),version:'18.373',release:()=>releaseIdleWorker('manual-release')};
 if(G.parallel){G.parallel.flush=()=>v52FlushSave();G.parallel.save=()=>persist(true);G.parallel.rpc=v53Call;
  G.parallel.start=(...args)=>v53StartSimulation(...args);}
 if(G.patch52){G.patch52.flushSave=()=>v52FlushSave();G.patch52.save=()=>persist();}
})();
/* FUTBR_SAVE_MEMORY_RUNTIME_18373_END */
'''


def once(source, before, after, label):
    count = source.count(before)
    if count != 1:
        raise RuntimeError(f'{label}: expected one anchor, found {count}')
    return source.replace(before, after, 1)


def patch_source(source):
    if MARKER in source:
        return source
    worker_start = source.index('function v53WorkerMain(){')
    worker_end = source.index('const v18191uPlayerFields=', worker_start)
    worker = source[worker_start:worker_end]
    worker = once(worker, "const v18352NestedArchiveKeys=new Set(['v538CareerArchive','v555CareerArchive']);",
                  ARCHIVE_CODEC + WORKER_HISTORY + "const v18352NestedArchiveKeys=new Set(['v538CareerArchive','v555CareerArchive']);", 'Worker archive codec')
    worker = once(worker, "if(spec?.nested==='year-id-v1'){v18352ApplyArchivedRow(dst,entry);continue;}",
                  "if(spec?.nested==='year-path-v1'||spec?.nested==='tree-path-v1'){v18373ApplyArchivePath(dst,entry);continue;}\n"
                  "      if(spec?.nested==='year-id-v1'){v18352ApplyArchivedRow(dst,entry);continue;}", 'Worker archive decoder')
    # Bound read concurrency for players AND legacy annual archive chunks.
    worker = once(worker, 'for(let i=0;i<keys.length;i+=8){\n    const chunks=await Promise.all(keys.slice(i,i+8).map(k=>read(k)));',
                  'for(let i=0;i<keys.length;i++){\n    const chunks=[await read(keys[i])];', 'Worker single-chunk loader')
    worker = once(worker, 'if(i+8<keys.length)await new Promise(r=>setTimeout(r,0));',
                  'if(i+1<keys.length)await new Promise(r=>setTimeout(r,0));', 'Worker loader yield')
    worker = once(worker, "if(key==='players'&&rows?.format===v18191wPlayerFormat)rows=await v18191wDecodePlayerChunk(rows);\n     for(const entry of rows||[]){",
                  "if(rows==null)throw Error('Bloco do save ausente: '+key);\n     if(key==='players'&&rows?.format===v18191wPlayerFormat)rows=await v18191wDecodePlayerChunk(rows);\n     for(const entry of rows||[]){", 'Worker missing-shard guard')
    worker = once(worker,
        "  const root=await read(meta.rootKey);if(!root||typeof root!=='object')return false;Object.assign(world,root);",
        """  const root=await read(meta.rootKey);if(!root||typeof root!=='object')return false;
  /* FUTBR_SKIP_COMMITTED_VACATION_OVERLAY_18373
     The canonical save already contains this exact vacation. Re-reading its
     player chunks would temporarily retain a second complete player map.
     Keep the old delta fallback when this precise proof is unavailable. */
  const committed=await read(STORE);
  const samePoint=(a,b)=>!!a&&!!b&&!!String(a.v1903CareerId||'')&&
   !!String(a.userCoachId||'')&&!!String(a.user||'')&&
   String(a.v1903CareerId||'')===String(b.v1903CareerId||'')&&
   String(a.userCoachId||'')===String(b.userCoachId||'')&&
   String(a.user||'')===String(b.user||'')&&
   String(a.futbrSaveId||'')===String(b.futbrSaveId||'')&&
   Number(a.year)===Number(b.year)&&Number(a.day)===Number(b.day);
  const complete=!!world&&shards.every(key=>{
   const value=world[key],spec=meta.collections?.[key];
   if(!spec||!value||typeof value!=='object')return false;
   if(spec.isArray&&(!Array.isArray(value)||value.length!==Number(spec.length)))return false;
   if(!spec.isArray&&Array.isArray(value))return false;
   if(key==='players'&&Number(spec.chunks)>0){
    for(const id in value)if(Object.prototype.hasOwnProperty.call(value,id))return true;
    return false;
   }
   return true;
  });
  if(complete&&committed?.format===V171_FORMAT&&
     committed.token==='vacation-'+meta.token&&
     Number(committed.year)===Number(meta.year)&&Number(committed.day)===Number(meta.day)&&
     Number(root.year)===Number(meta.year)&&Number(root.day)===Number(meta.day)&&
     samePoint(world,root)&&samePoint(world,committed.root))return true;
  Object.assign(world,root);""", 'skip exact committed vacation overlay')
    save_start = worker.index('async function save(s){')
    save_end = worker.index(' function baselineOf(s)', save_start)
    save = worker[save_start:save_end]
    save = once(save, "!s.seasonDone&&v18181Stable.has(key)&&old.collections?.[key];",
                "!s.seasonDone&&v18181Stable.has(key)&&old.collections?.[key]&&\n"
                "   (key!=='v555CareerArchive'||old.collections[key].nested==='year-path-v1')&&\n"
                "   (key!=='scorerArchive'||old.collections[key].nested==='tree-path-v1');", 'packed archive migration')
    save = once(save, "const history=v18343HistoricalKeys.has(key),nested=v18352NestedArchiveKeys.has(key)&&value&&typeof value==='object',isArray=Array.isArray(value),keys=[],",
                "const pathArchive=['v555CareerArchive','scorerArchive','competitionStats'].includes(key),\n  nestedFormat=key==='v555CareerArchive'?'year-path-v1':pathArchive?'tree-path-v1':'year-id-v1',\n  history=v18343HistoricalKeys.has(key),nested=(pathArchive||v18352NestedArchiveKeys.has(key))&&value&&typeof value==='object',isArray=Array.isArray(value),keys=[],", 'packed archive shape')
    save = once(save, "(!nested||old.collections[key].nested==='year-id-v1')", "(!nested||old.collections[key].nested===nestedFormat)", 'packed archive hash compatibility')
    save = once(save, "if(nested){\n   for(const year in value){",
                "if(pathArchive){\n   for(const row of v18373StructuredArchiveRows(value,key)){rows.push(row);if(rows.length>=limit)await flush();}\n  }else if(nested){\n   for(const year in value){", 'packed archive subrows')
    save = once(save, "...(nested?{nested:'year-id-v1'}:null)", "...(nested?{nested:nestedFormat}:null)", 'packed archive marker')
    # Revision belongs in the manifest too, so compact ownership tokens remain
    # monotonic after normal Worker saves and UI saves alternate.
    save = once(save, "const manifest={format:V171_FORMAT,version:1,token,at:meta.at,year:s.year,day:s.day,root,collections};",
                "meta.revision=Math.max(meta.revision,Number(old?.revision||0)+1);diskRevision=meta.revision;\n"
                " const manifest={format:V171_FORMAT,version:1,token,revision:meta.revision,at:meta.at,year:s.year,day:s.day,root,collections};", 'Worker manifest revision')
    worker = worker[:save_start] + save + worker[save_end:]
    # The root patch is installed first. Keep the initial archive tests usable
    # on standalone 18.372 too; the release pipeline requires both markers.
    if 'async function v18373CommitVacationCheckpoint(' in worker:
        before = "  const collections={},nextRoot={...(same?old.root||{}:{}),...root};\n  for(const key of V171_SHARDS){"
        after = "  const collections={},nextRoot={...(same?old.root||{}:{}),...root};\n" \
            "  const freshHistory=(!same||Number(old.year)!==origin.year)?\n" \
            "   await v18373WriteCheckpointHistories(world,old,meta.token):{collections:{},root:{}};\n" \
            "  Object.assign(nextRoot,freshHistory.root);\n" \
            "  for(const key of V171_SHARDS){\n" \
            "   if(freshHistory.collections[key]){collections[key]=freshHistory.collections[key];delete nextRoot[key];continue;}\n" \
            "   if(Object.prototype.hasOwnProperty.call(freshHistory.root,key)){delete collections[key];continue;}"
        worker = once(worker, before, after, 'new-season vacation history')
    worker = once(worker, "if(m.op==='save'){", "if(m.op==='settle-storage-18373'){\n"
                  "   if(running)throw Error('A simulação ainda está ativa.');\n"
                  "   if(v150ManualSavePromise)await v150ManualSavePromise;\n"
                  "   return {settled:true};\n  }\n  if(m.op==='save'){", 'deferred save settlement')
    worker = once(worker, "self.postMessage({kind:'finished',session,error:failure,day:finalDay,year:finalYear,rankPending});",
                  "self.postMessage({kind:'finished',session,error:failure,day:finalDay,year:finalYear,rankPending,\n"
                  "    checkpointPending18373:!!((fastManualDay||nationalJump||nextMatchJump||lowMemoryDay)&&!failure&&world&&!(fastManualDay&&message.jobWaitAuto===true)||deferredFinalSave&&!failure)});", 'deferred Worker checkpoint ownership')
    source = source[:worker_start] + worker + source[worker_end:]
    source = once(source, "w.onmessage=event=>{const m=event.data;if(m.kind==='ready')",
                  "w.onmessage=event=>{const m=event.data;\n"
                  "    if(m.kind==='finished'&&m.checkpointPending18373)w.v18373CheckpointBusy=true;\n"
                  "    if(m.kind==='saved'||m.kind==='save-error')w.v18373CheckpointBusy=false;\n"
                  "    if(m.kind==='ready')", 'main Worker storage flag')
    anchor = "window.GestorFC.scope18366={"
    start = source.index(anchor)
    end = source.index('\n})();\n</script>', start)
    block = UI_RUNTIME.replace('/* ARCHIVE_CODEC_INSERT */', ARCHIVE_CODEC)
    source = source[:end] + '\n' + block + source[end:]
    return source


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: fix_save_memory_runtime_18373.py <project>')
    root = Path(sys.argv[1])
    target = root / 'src' / 'index.html'
    source = patch_source(target.read_text(encoding='utf-8'))
    target.write_text(source, encoding='utf-8')
    report = {'ok': True, 'version': '18.373.0', 'sameGameScope': MARKER in source,
              'noFullStateSaveRPC': "if(op==='save')throw Error('Use o salvamento fragmentado da carreira.');" in source,
              'packedHistoryBounded': "nestedFormat=key==='v555CareerArchive'?'year-path-v1':pathArchive?'tree-path-v1':'year-id-v1'" in source,
              'scorerHistoryBounded': "depth=key==='scorerArchive'?4:key==='competitionStats'?2:3" in source,
              'rolloverHistoryRetained': 'await v18373WriteCheckpointHistories(world,old,meta.token)' in source,
              'legacyHistoryReadable': "if(spec.nested==='year-id-v1'){applyLegacyArchive(dst,entry);continue;}" in source,
              'ownerGuard': 'setWorkerOwner,clearWorkerOwner,restoreOwnerCheckpoint' in source,
              'deferredWorkerSaveProtected': 'checkpointPending18373:' in source}
    report['committedVacationOverlaySkipped'] = 'FUTBR_SKIP_COMMITTED_VACATION_OVERLAY_18373' in source
    (root / 'save-memory-runtime-18373-install.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
