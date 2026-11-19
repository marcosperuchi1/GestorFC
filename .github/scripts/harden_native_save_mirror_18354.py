from __future__ import annotations
import json
import sys
from pathlib import Path

MARK = 'FUTBR_NATIVE_MIRROR_18354'
VERSION = '18.354.0'
MIRROR = r"""/* FUTBR_NATIVE_MIRROR_18354: low-peak, ordered, resumable SQLite mirror.
   IndexedDB remains authoritative. Only copy one shard into the IPC at a
   time, reuse shards from a verified previous native commit, and commit the
   mirror index/manifests LAST. An interrupted mirror cannot poison recovery. */
 let nativeSync=null;
 const nativeMirrorStats={version:'18.354',written:0,reused:0,failures:0,full:0,
  incremental:0,lastStatus:'idle',lastRevision:null};
 function localGet(key){return openDB().then(db=>new Promise((resolve,reject)=>{
  const r=db.transaction('saves','readonly').objectStore('saves').get(key);
  r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);
 }));}
 function manifestKeys(m){
  if(!m||m.format!=='GFC_SHARDED_171')return [];
  return Object.values(m.collections||{}).flatMap(spec=>
   Array.isArray(spec?.keys)?spec.keys:[]);
 }
 async function syncActiveSaveToDisk(){
  if(nativeSync)return nativeSync;
  nativeSync=(async()=>{
   const native=window.FutBRDesktop;
   if(!native?.available||typeof native.read!=='function'||typeof native.writeMany!=='function')
    return false;
   const manifest=await localGet(BASE);
   if(manifest?.format!=='GFC_SHARDED_171')return false;
   const token=String(manifest.token||''),revision=Number(manifest.revision||0);
   const markerKey=BASE+':mirror-18354';
   const marker=await native.read(markerKey).catch(()=>null);
   const mirrored=await native.read(BASE).catch(()=>null);
   const verified=marker?.completed===true&&marker.token===mirrored?.token&&
    Number(marker.revision)===Number(mirrored?.revision);
   const prior=new Set(verified?manifestKeys(mirrored):[]);
   const keys=[...new Set(manifestKeys(manifest))];
   nativeMirrorStats.lastStatus='copying';
   if(verified)nativeMirrorStats.incremental++;
   else nativeMirrorStats.full++;
   try{
    for(let i=0;i<keys.length;i++){
     const key=keys[i];
     if(prior.has(key)){nativeMirrorStats.reused++;continue;}
     // Exactly one IDB clone and one native IPC payload at a time. Never
     // materialize an entire roster or a 6-shard batch in the WebView heap.
     const value=await localGet(key);
     if(value===undefined)throw Error('Bloco do save indisponível: '+key);
     await native.writeMany([{key,value}]);
     nativeMirrorStats.written++;
     if(i%8===0)await new Promise(r=>setTimeout(r,0));
    }
    // Abort if the world advanced during the mirror. Existing native
    // manifest remains valid and the retry can use written immutable shards.
    const current=await localGet(BASE);
    if(String(current?.token||'')!==token||
       Number(current?.revision||0)!==revision)
     throw Error('Checkpoint atualizado durante o espelhamento; tentativa posterior necessária.');
    const index=await localGet(INDEX);
    const meta=await localGet(BASE+':meta');
    const previous=await localGet(BASE+':previous');
    // One tiny atomic native SQL transaction; marker is written last.
    const final=[{key:BASE,value:current},
      ...(meta===undefined?[]:[{key:BASE+':meta',value:meta}]),
      ...(previous===undefined?[]:[{key:BASE+':previous',value:previous}]),
      ...(index===undefined?[]:[{key:INDEX,value:index}]),
      {key:markerKey,value:{version:1,completed:true,token,revision,
       total:keys.length,at:Date.now()}}];
    await native.writeMany(final);
    nativeMirrorStats.lastRevision=revision;
    nativeMirrorStats.lastStatus='complete';
    return true;
   }catch(error){
    nativeMirrorStats.failures++;
    nativeMirrorStats.lastStatus='deferred';
    console.warn('[FutBR 18.354] Cópia SQLite adiada; save IndexedDB preservado:',
      error?.message||error);
    return false;
   }
  })().finally(()=>{nativeSync=null;});
  return nativeSync;
 }
 window.FutBRDesktop.syncActiveSave=syncActiveSaveToDisk;
 window.FutBRDesktop.nativeMirror18354={
  status:()=>({...nativeMirrorStats,active:!!nativeSync})
 };
 async function syncAfterPrimarySave(){
  // Fired only after the named save writes its final index. No polling
  // window.v52SavePromise: top-level lexical state is not a window property.
  try{return await syncActiveSaveToDisk();}
  catch(error){console.warn('[FutBR 18.354] Backup secundário:',error);return false;}
 }
 document.addEventListener('futbr:save-confirmed',()=>{void syncAfterPrimarySave();});
"""
def once(text,before,after,name):
    n=text.count(before)
    if n!=1:
        raise RuntimeError(f'18.354 {name}: expected 1 source anchor; got {n}')
    return text.replace(before,after,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: harden_native_save_mirror_18354.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    if cfg.get('version')!=VERSION:raise RuntimeError('Expected signed Windows version 18.354.0')
    path=root/'src/index.html'
    html=path.read_text(encoding='utf-8')
    if MARK in html:raise RuntimeError('18.354 patch applied twice')
    for feature in ('FUTBR_SERIEC_FULL_PODIUM_18353',
                    'FUTBR_OOMSAFE_ARCHIVE_18352',
                    'FUTBR_SERIEC_PHASES_HISTORY_18351',
                    'FUTBR_ARCHIVE_COPY_ON_WRITE_18343',
                    "let nativeSync=null;",
                    "window.FutBRDesktop.syncActiveSave=syncActiveSaveToDisk;"):
        if feature not in html:raise RuntimeError('Missing save invariant: '+feature)
    a=html.index(' let nativeSync=null;')
    b=html.index(' function decorateCloseButton(){',a)
    old=html[a:b]
    if 'document.addEventListener' not in old or 'syncAfterPrimarySave()' not in old:
        raise RuntimeError('Unexpected mirroring hook; refusing unsafe modification')
    html=html[:a]+MIRROR+html[b:]
    # The named save IIFE knows exactly when the primary checkpoint and its
    # index are committed; do not start SQLite mirroring on click capture.
    a=html.index('async function doSave(asCopy=false,exitAfter=false){')
    b=html.index('async function renameSlot(',a)
    segment=html[a:b]
    segment=once(segment,
      '   await writeIndex();\n   closeModal();',
      """   await writeIndex();
   // 18.354: trigger ONLY after a confirmed named save, not before.
   try{document.dispatchEvent(new Event('futbr:save-confirmed'));}catch(e){}
   closeModal();""",
      'actual post-save event')
    html=html[:a]+segment+html[b:]
    # Close the app without running a second full mirror. The authoritative
    # IndexedDB checkpoint has already committed and is not discarded.
    html=once(html,
      "Promise.resolve(syncActiveSaveToDisk()).catch(()=>{}).finally(()=>window.FutBRDesktop.closeGame());return;",
      "window.FutBRDesktop.closeGame();return;",
      'close without duplicate mirror')
    html=once(html,
      "const EDITION='18.353.0';","const EDITION='18.354.0';",
      'visible sidebar version')
    html=once(html,
      "window.GestorFC.version='18.353.0';window.GestorFC.visualVersion='18.353.0';",
      "window.GestorFC.version='18.354.0';window.GestorFC.visualVersion='18.354.0';",
      'runtime build version')
    path.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,'secondarySQLiteCopiesOneShardAtTime':True,
      'noMirrorBeforePrimarySave':True,'noFullRecopyForVerifiedShards':True,
      'firstMirrorCopiesLegacyBlocksSafely':True,'oldBackupManifestSurvivesFailure':True,
      'mirrorIndexCommittedOnlyAfterAllChunks':True,'savesRemainInIndexedDB':True,
      'closeDoesNotTriggerLargeDuplicateSave':True,
      'previousSaveAndLongCareerHistoryPreserved':True}
    (root/'native-save-mirror-18354-install.json').write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
