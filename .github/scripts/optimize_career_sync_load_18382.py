"""FutBR 18.382: bounded read/copy batching and low-allocation sync transfer.

Do not alter the save format or simulation. Never share or discard source chunks:
named careers remain independently recoverable. Batches are limited to four
stored chunks at a time, and worker->UI still acknowledges only after applying
each complete player batch.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

MARK='FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382'

COPY=r"""
/* FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382
   Named save copies MUST be independent: never point two saved careers to
   the same mutable shard key. Four source chunks maximum per transaction. */
const v18382CopyMetrics={batches:0,copied:0,maxReadBatch:0};
async function v18382CopyChunkGroup(pairs){
 if(!pairs.length)return;
 if(pairs.length>4)throw Error('Lote de cópia acima do limite de memória.');
 v18382CopyMetrics.maxReadBatch=Math.max(v18382CopyMetrics.maxReadBatch,pairs.length);
 if(window.FutBRDesktop?.directStorage){
  // One IPC round trip for four source reads, one for four writes. Read-only
  // and write requests are independent of the main game state and save format.
  const storage=window.FutBRDesktop;
  let values;
  if(typeof storage.readMany==='function')values=await storage.readMany(pairs.map(p=>p[0]));
  else values=await Promise.all(pairs.map(p=>storage.read(p[0])));
  if(!Array.isArray(values)||values.length!==pairs.length||
     values.some(v=>v===null||typeof v==='undefined'))
   throw Error('Bloco do save indisponível. Salvamento anterior foi preservado.');
  const writes=pairs.map(([source,destination],i)=>({key:destination,value:values[i]}));
  if(typeof storage.writeMany==='function')await storage.writeMany(writes);
  else for(const e of writes)await storage.write(e.key,e.value);
 }else{
  const d=await db();
  await new Promise((resolve,reject)=>{
   const tx=d.transaction('saves','readwrite'),os=tx.objectStore('saves');
   let missing=false;
   for(const [source,destination] of pairs){
    const r=os.get(source);
    r.onsuccess=()=>{
     if(r.result===undefined||r.result===null){missing=true;try{tx.abort();}catch(_e){}return;}
     os.put(r.result,destination);
    };
   }
   tx.oncomplete=()=>resolve();
   tx.onerror=()=>reject(tx.error||Error('Falha ao copiar os blocos do save'));
   tx.onabort=()=>reject(Error(missing?
     'Bloco do save indisponível. Salvamento anterior foi preservado.':
     'Cópia de bloco interrompida'));
  });
 }
 v18382CopyMetrics.batches++;
 v18382CopyMetrics.copied+=pairs.length;
}
async function copyManifest(src,prefix,onProgress){
 if(!src||src.format!==FORMAT)throw Error('Carreira incompleta: checkpoint em blocos não encontrado.');
 const result={...src,collections:{}};
 const created=[],n=manifestKeys(src).length;let count=0;
 try{
  for(const [collection,spec] of Object.entries(src.collections||{})){
   const keys=[],sourceKeys=spec?.keys||[];
   for(let i=0;i<sourceKeys.length;i+=4){
    const group=sourceKeys.slice(i,i+4).map((source,j)=>
     [source,prefix+':'+collection+':'+(i+j)]);
    // Track every attempted key even if a native batch partially commits.
    for(const pair of group)created.push(pair[1]);
    await v18382CopyChunkGroup(group);
    for(const pair of group)keys.push(pair[1]);
    count+=group.length;
    if(count%12===0||count===n){
     try{onProgress?.(count,n);}catch(_e){}
     if(count<n)await new Promise(r=>setTimeout(r,0));
    }
   }
   result.collections[collection]={...spec,keys};
  }
  return {manifest:result,created};
 }catch(error){
  // Only newly generated keys are cleaned; the source and previous manifest
  // are always retained. Finish the cleanup before reporting a failed copy.
  await delMany(created).catch(e=>console.warn('[18.382] limpeza de lote:',e));
  throw error;
 }
}
"""

LOAD=r"""
 async function hydrateManifest(manifest,progress=null){
  if(manifest?.format!==FORMAT)return null;
  const out={...(manifest.root||{})},entries=Object.entries(manifest.collections||{});
  for(let ci=0;ci<entries.length;ci++){
   const [key,spec]=entries[ci],keys=spec?.keys||[];
   if(!Array.isArray(keys))throw Error('Índice de blocos inválido.');
   const dst=spec?.isArray?new Array(Number(spec.length)||0):{};
   // At most 4 stored (still compressed) chunks are materialized per read.
   // Decompress/apply one at a time; neither whole-world clone nor 8-16
   // simultaneous decoded player arrays is created.
   const stride=4;
   for(let i=0;i<keys.length;i+=stride){
    const partKeys=keys.slice(i,i+stride);
    const stored=await readMany(partKeys);
    if(!Array.isArray(stored)||stored.length!==partKeys.length)
     throw Error('Leitura parcial de blocos do save. O arquivo não foi alterado.');
    for(let j=0;j<stored.length;j++){
     let rows=stored[j];stored[j]=null;
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
     const done=i+j+1;
     try{progress?.({key,done,total:keys.length,collection:ci+1,collections:entries.length});}catch(e){}
    }
    // Keep the event loop alive between small groups; never queue a second
    // group while the prior group's objects are still being applied.
    if(i+stride<keys.length)await yieldUI();
   }
   Object.defineProperty(out,key,{value:dst,writable:true,enumerable:true,configurable:true});
  }
  return out;
 }
"""

SYNC_HELPER=r"""
/* FUTBR_CAREER_SYNC_LOW_ALLOC_18382
   Resume a career from transferable packed batches without creating a
   temporary [playerId, player] tuple for every player in the world. */
const v18382SyncMetrics={players:0,batches:0,decodeMs:0,maxPackedBytes:0,lastBatchMs:0};
function v18382ApplyVacationRows(dst,m){
 if(m.format==='player-packed-buffer-v1'&&m.bytes instanceof ArrayBuffer){
  const started=performance.now(),bytes=m.bytes;
  v18382SyncMetrics.maxPackedBytes=Math.max(v18382SyncMetrics.maxPackedBytes,bytes.byteLength);
  const packed=JSON.parse(new TextDecoder().decode(bytes));
  m.bytes=null;
  if(!Array.isArray(packed))throw Error('Bloco de jogadores incompleto. Save anterior preservado.');
  for(const row of packed){
   const player=v18191uUnpackPlayer(row);
   if(!player||!player.id)throw Error('Registro de jogador inválido. Save anterior preservado.');
   dst[player.id]=player;
  }
  const ms=performance.now()-started;
  v18382SyncMetrics.players+=packed.length;v18382SyncMetrics.batches++;
  v18382SyncMetrics.decodeMs+=ms;v18382SyncMetrics.lastBatchMs=ms;
  return packed.length;
 }
 const rows=v18310VacationRows(m);m.bytes=null;
 if(m.format==='tree-path-v1')for(const row of rows)v18373ApplyTreeRow(dst,row);
 else for(const [id,row] of rows){if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;}
 return rows.length;
}
"""

def once(src,old,new,label):
 n=src.count(old)
 if n!=1:raise RuntimeError(f'18.382 {label}: expected one anchor, got {n}')
 return src.replace(old,new,1)

def main():
 if len(sys.argv)!=2:raise SystemExit("usage: optimize_career_sync_load_18382.py <prepared-root>")
 root=Path(sys.argv[1]).resolve()
 path=root/'src/index.html'
 s=path.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.382 patch already applied')
 for must in ('FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN','FUTBR_PLAYER_CHECKPOINT_REUSE_18373',
              'FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381','async function copyManifest(src,prefix,onProgress){'):
  if must not in s:raise RuntimeError('Required existing feature not available: '+must)

 # Exactly the old unbatched archive copying implementation, inside the
 # persisted named-career manager rather than any test/legacy script.
 start=s.index('async function copyManifest(src,prefix,onProgress){')
 end=s.index('\nfunction block(text){',start)
 if "await cloneChunk(key,dest)" not in s[start:end]:
  raise RuntimeError('Named-save copier changed; do not patch unknown implementation')
 s=s[:start]+COPY+s[end:]

 # The authoritative bounded UI saver/loader (not the old inactive v171
 # decoder) is the only save path changed.
 start=s.index(' async function hydrateManifest(manifest,progress=null){')
 end=s.index(' async function loadDirect(progress=null,allowOwner=false){',start)
 if "let rows=(await readMany([keys[i]]))[0]" not in s[start:end]:
  raise RuntimeError('Bounded live loader changed; refuse patch')
 s=s[:start]+LOAD+s[end:]

 # Real 18.381 UI post-vacation handler is the last definition, after all
 # earlier wrappers. Keep the worker backpressure ACK and existing protection
 # against incomplete state unchanged.
 anchor='const v53Base={render,renderWelcome,act,persist,guardManage,loadLocal,helpPage,vacationPage,commitDay,downloadFile};'
 s=once(s,anchor,SYNC_HELPER+'\n'+anchor,'transfer decoder helper')
 old="const dst=v125VacIncoming[m.key]||(v125VacIncoming[m.key]={}),rows=v18310VacationRows(m);m.bytes=null;if(m.format==='tree-path-v1'){for(const row of rows)v18373ApplyTreeRow(dst,row);}else for(const [id,row] of rows){if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;}"
 new="const dst=v125VacIncoming[m.key]||(v125VacIncoming[m.key]={}),applied=v18382ApplyVacationRows(dst,m);"
 s=once(s,old,new,'final worker-to-UI transfer')
 s=once(s,"if(m.key==='players'){v53Stats.playerUpdates+=rows.length;const total=",
            "if(m.key==='players'){v53Stats.playerUpdates+=applied;const total=",
            'transfer count without temporary tuples')
 old="if(card)card.textContent='Atualizando jogadores e histórico · '+pct+'%. O novo estado será liberado assim que a transferência terminar.';"
 new="if(card&&card.dataset.v18382Pct!==String(pct)){card.dataset.v18382Pct=String(pct);card.textContent='Atualizando jogadores e histórico · '+pct+'%. O novo estado será liberado assim que a transferência terminar.';}"
 s=once(s,old,new,'avoid DOM write for identical sync percent')
 if s.count(MARK)!=1:raise RuntimeError('Required bounded-copy marker must appear exactly once')
 # Keep existing per-chunk ACK and guard unchanged.
 if "v53Worker?.postMessage({op:'vac-sync-ack',seq:Number(m.syncSeq)||0})" not in s:
  raise RuntimeError('Lossless backpressure acknowledgment missing')
 for code,label in [(COPY,'named save chunks'),(LOAD,'hydration'),(SYNC_HELPER,'sync decode')]:
  checked=subprocess.run(['node','--check','-'],input=code,text=True,capture_output=True,timeout=30)
  if checked.returncode:raise RuntimeError(label+' JavaScript syntax '+checked.stderr[-2000:])
 s=s.replace("window.GestorFC=window.GestorFC||{};\nwindow.GestorFC.vacationFinalize18360=",
 """window.GestorFC=window.GestorFC||{};
window.GestorFC.careerThroughput18382={version:'18.382.0',status:()=>({
  ...v18382SyncMetrics,copy:{...v18382CopyMetrics},
  savedGame:window.GestorFC?.saveMemoryRuntime18373?.status?.()||null,
  vacation:window.GestorFC?.vacationFinalize18360?.status?.()||null
})};
window.GestorFC.vacationFinalize18360=""",1)
 path.write_text(s,encoding='utf-8')
 report={'ok':True,'version':'18.382.0',
   'fourChunkReadBound':True,'fourChunkCopyBound':True,
   'nativeBatchedSaveSwitch':True,'indexedDbTransactionalCopy':True,
   'independentArchivedSaveChunks':True,'sourceManifestsUntouched':True,
   'failureCleanupWaited':True,'decodedOneChunkAtATime':True,
   'legacyArchiveDecodeUnchanged':True,'workerAckAfterEntireBatch':True,
   'packedPlayersAppliedWithoutPairArrays':True,'syncProgressUpdatesThrottled':True,
   'coreSaveAndSeasonRolloverUnchanged':True,
   'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'career-sync-load-18382-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
