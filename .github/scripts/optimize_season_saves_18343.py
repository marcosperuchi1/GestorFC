from __future__ import annotations
import json
import sys
from pathlib import Path

VERSION='18.343'
MARK='FUTBR_ARCHIVE_COPY_ON_WRITE_18343'

# This helper runs in both the main process and the vacation worker. A
# cryptographic content hash, never object identity, permits reusing an
# unchanged historical archive shard. Without Web Crypto, use full writes.
HELPER=r'''
/* FUTBR_ARCHIVE_COPY_ON_WRITE_18343
   Retain the manifest's immutable historical chunks by SHA-256 fingerprint.
   Never reuse a changed record or infer equality from year, id or reference.
   The old checkpoint remains valid until a new manifest is atomically committed. */
const v18343HistoricalKeys=new Set([
 'v538CareerArchive','v555CareerArchive','scorerArchive','transfers',
 'retirements','history','internationalHistory','v735NationalArchive'
]);
const v18343ArchiveStats={version:'18.343',reused:0,written:0,hashed:0,
  reusedByKey:{},writtenByKey:{},lastSaveMs:0};
function v18343HistoricalLimit(key,previousLimit){
 if(key==='v538CareerArchive'||key==='v555CareerArchive')return 32;
 // Scorer years can contain large player tables; never merge multiple years.
 if(key==='scorerArchive')return 1;
 return previousLimit;
}
async function v18343Fingerprint(rows){
 if(!globalThis.crypto?.subtle||typeof TextEncoder!=='function')return null;
 let text;
 try{
  text=JSON.stringify(rows,(key,value)=>{
   // Not all structured-clone values have a faithful JSON representation.
   // Fail closed: no hash-based reuse on unsupported historical structures.
   if(typeof value==='undefined'||(typeof value==='number'&&!Number.isFinite(value)))
    throw Error('non-JSON archive scalar');
   if(value&&typeof value==='object'&&
      (value instanceof ArrayBuffer||ArrayBuffer.isView(value)||
       value instanceof Map||value instanceof Set))
    throw Error('non-JSON archived record');
   return value;
  });
 }catch(e){return null;}
 if(typeof text!=='string')return null;
 const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));
 return Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
}
function v18343ArchiveWritten(key,reused){
 const map=reused?v18343ArchiveStats.reusedByKey:v18343ArchiveStats.writtenByKey;
 if(reused)v18343ArchiveStats.reused++;else v18343ArchiveStats.written++;
 map[key]=(map[key]||0)+1;
}
'''

UI_WRITE=r'''async function writeCollection(token,key,value,limit,previous=null){
 const isArray=Array.isArray(value),keys=[],history=v18343HistoricalKeys.has(key),
  oldSpec=history&&previous&&!!previous.isArray===isArray?previous:null,
  hashes=history?[]:null;
 let rows=[],idx=0,writes=0,pending=[];
 const commit=async(force=false)=>{
  if(!pending.length)return;
  const target=key==='players'?(Number(state?.year)>=2029?2:4):4;
  if(!force&&pending.length<target)return;
  const batch=pending.splice(0,pending.length);
  await v18183DbWriteMany(batch);
  await new Promise(r=>setTimeout(r,0));
 };
 const flush=async()=>{
  if(!rows.length)return;
  const raw=rows;rows=[];
  const index=idx++,fingerprint=history?await v18343Fingerprint(raw):null;
  if(history){hashes.push(fingerprint);if(fingerprint)v18343ArchiveStats.hashed++;}
  if(fingerprint&&oldSpec?.hashes?.[index]===fingerprint&&oldSpec.keys?.[index]){
   keys.push(oldSpec.keys[index]);
   v18343ArchiveWritten(key,true);
   return;
  }
  const payload=key==='players'?await v18191mEncodePlayerChunk(raw):raw,
   ck=shardKey(token,key,index);
  keys.push(ck);pending.push({key:ck,value:payload});writes++;
  if(history)v18343ArchiveWritten(key,false);
  if(key==='players')stats.playerChunksWritten++;
  if(v18121NewSeasonPreparation&&(key!=='players'||writes===1||writes%10===0)){
   v53Sim.progress=key==='players'?'Salvando jogadores compactados · bloco '+writes:'Salvando '+key+' da nova temporada';
   try{v53PaintStatus();}catch(e){}
  }
  await commit(false);
 };
 for(const id in (value||{})){
  rows.push([id,value[id]]);
  if(rows.length>=limit)await flush();
 }
 await flush();await commit(true);
 return {isArray,length:isArray?value.length:0,keys,
  ...(history?{hashes,archiveHash:'sha256-json-v1'}:null),
  ...(key==='players'?{encoding:v18191mPlayerFormat}:null)};
}
'''

WORKER_LOOP=r'''const v18181Stable=new Set(['v538CareerArchive','v555CareerArchive','scorerArchive']);
 for(const key of V171_SHARDS){
  const value=s[key];if(value==null)continue;
  const sameSeason=old?.format===V171_FORMAT&&Number(old.year)===Number(s.year)&&
   !s.seasonDone&&v18181Stable.has(key)&&old.collections?.[key];
  if(sameSeason){collections[key]=old.collections[key];continue;}
  const history=v18343HistoricalKeys.has(key),isArray=Array.isArray(value),keys=[],
   oldSpec=history&&old?.format===V171_FORMAT&&old?.collections?.[key]&&
    !!old.collections[key].isArray===isArray?old.collections[key]:null,
   hashes=history?[]:null,
   baseLimit=key==='players'?(Number(s.year)>=2029?800:1600):
    key==='teams'?380:key==='coaches'?500:key==='schedule'?4:
    key==='competitionStats'?4:key==='allTimeStats'?650:
    (key==='v538CareerArchive'||key==='v555CareerArchive'||key==='scorerArchive'?1:120),
   limit=v18343HistoricalLimit(key,baseLimit);
  let rows=[],chunk=0,done=0,pending=[];
  const commit=async(force=false)=>{
   if(!pending.length)return;
   const target=key==='players'?(Number(s.year)>=2029?2:4):4;
   if(!force&&pending.length<target)return;
   await v18181RawWriteMany(pending.splice(0,pending.length));
   await new Promise(r=>setTimeout(r,0));
  };
  const flush=async()=>{
   if(!rows.length)return;
   const raw=rows;rows=[];
   const index=chunk++,fingerprint=history?await v18343Fingerprint(raw):null;
   if(history){hashes.push(fingerprint);if(fingerprint)v18343ArchiveStats.hashed++;}
   if(fingerprint&&oldSpec?.hashes?.[index]===fingerprint&&oldSpec.keys?.[index]){
    keys.push(oldSpec.keys[index]);
    v18343ArchiveWritten(key,true);
    return;
   }
   const payload=key==='players'?await v18191wEncodePlayerChunk(raw):raw,
    ck=v171ShardKey(token,key,index);
   keys.push(ck);pending.push({key:ck,value:payload});done++;
   if(history)v18343ArchiveWritten(key,false);
   await commit(false);
  };
  for(const id in value){
   if(!safe(id))continue;
   rows.push([id,value[id]]);
   if(rows.length>=limit)await flush();
  }
  await flush();await commit(true);
  collections[key]={isArray,length:isArray?value.length:0,keys,
   ...(history?{hashes,archiveHash:'sha256-json-v1'}:null),
   ...(key==='players'?{encoding:v18191wPlayerFormat}:null)};
 }
'''

def patch_once(s,before,after,label):
    n=s.count(before)
    if n!=1:raise RuntimeError(f'18.343 {label}: expected one anchor, found {n}')
    return s.replace(before,after,1)

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: optimize_season_saves_18343.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src/index.html'
    src=path.read_text(encoding='utf-8')
    if MARK in src:raise RuntimeError('18.343 archive patch already installed')
    if 'FUTBR_LONG_CAREER_SAVE_18338_BEGIN' not in src:
        raise RuntimeError('Lossless 18.338 save/memory protection required')
    if "const target=key==='players'?(Number(s.year)>=2029?2:4)" not in src:
        raise RuntimeError('Worker memory cap for long seasons is missing')
    if "const target=key==='players'?(Number(state?.year)>=2029?2:4)" not in src:
        raise RuntimeError('UI memory cap for long seasons is missing')
    # Helpers belong in both the inline worker string and the UI IIFE.
    worker_start=src.find('async function save(s){')
    worker_finish=src.find(' const manifest=',worker_start)
    worker_loop=src.find('const v18181Stable=new Set(',worker_start,worker_finish)
    if worker_start<0 or worker_finish<0 or worker_loop<0:
        raise RuntimeError('Worker sharded save loop not found')
    if src.count('async function save(s){')!=1:
        raise RuntimeError('Unexpected number of Worker save routines')
    src=src[:worker_loop]+WORKER_LOOP+src[worker_finish:]
    src=src[:worker_start]+HELPER+'\n'+src[worker_start:]

    ui_start=src.find('async function writeCollection(token,key,value,limit){')
    ui_finish=src.find('async function saveSharded(s,mode=',ui_start)
    if ui_start<0 or ui_finish<0 or src.count('async function writeCollection(token,key,value,limit){')!=1:
        raise RuntimeError('UI native sharded save not found')
    src=src[:ui_start]+HELPER+'\n'+UI_WRITE+'\n'+src[ui_finish:]

    old="const limit=key==='players'?(Number(s.year)>=2029?800:1600):key==='teams'?420"
    if old not in src:
        # After 18.338, the UI baseline uses s.year for compression chunk size.
        raise RuntimeError('The validated year-aware UI player chunk cap changed')
    # No dangerous unbounded player buffer or native IPC batch increase.
    call="collections[key]=await writeCollection(token,key,value,limit);"
    patched="collections[key]=await writeCollection(token,key,value,v18343HistoricalLimit(key,limit),old?.format===FORMAT?old.collections?.[key]:null);"
    src=patch_once(src,call,patched,'UI archive copy-on-write invocation')
    # Add optional diagnostics without changing any gameplay data or persistence.
    src=patch_once(src,
       "stats.lastSaveMs=Math.round(performance.now()-t0);stats.lastMode=mode;",
       "stats.lastSaveMs=Math.round(performance.now()-t0);v18343ArchiveStats.lastSaveMs=stats.lastSaveMs;stats.lastMode=mode;",
       'record UI checkpoint elapsed')
    src=patch_once(src,"await v18181RawWriteMany([{key:STORE+':previous',value:old},{key:STORE,value:manifest},{key:STORE+':meta',value:meta}]);",
       "await v18181RawWriteMany([{key:STORE+':previous',value:old},{key:STORE,value:manifest},{key:STORE+':meta',value:meta}]);v18343ArchiveStats.lastSaveMs=Math.round(performance.now()-start);",
       'record worker checkpoint elapsed')

    # Explicit fail-closed contract: a checksum match cannot allow data loss
    # if an archive member changes, because the SHA-256 digest changes.
    for name in ('v538CareerArchive','v555CareerArchive','scorerArchive',
                 'transfers','retirements','history','internationalHistory',
                 'v735NationalArchive','allTimeStats','v18183DbWriteMany',
                 'v18181RawWriteMany','commitManifest(manifest,old,meta)',
                 'await v171DropManifest(oldPrev,keep)'):
        if name not in src:raise RuntimeError('Historical/save invariant missing: '+name)
    path.write_text(src,encoding='utf-8')
    result={'ok':True,'version':VERSION,
      'historicalArchiveGrouping':32,'scorerArchiveGrouping':1,
      'historicalChunksReusedOnlyIfSha256Matches':True,
      'readsLegacyManifestsWithoutHashes':True,
      'storesMissingArchiveChunksBeforeAtomicManifestCommit':True,
      'keepsPreviousRecoverableSnapshot':True,
      'writerUIAndWorkerBothPatched':True,
      'boundedPlayerChunksPreserved':True,
      'noStatsOrHistoryTruncated':True,'nativeIPCFormatUnchanged':True}
    (root/'season-save-18343-install.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
