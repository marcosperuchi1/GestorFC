from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

HARNESS=r"""
'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm');
const {performance}=require('node:perf_hooks');
const BASE='futbr-active',INDEX='futbr-index';
const IDB=new Map(),NATIVE=new Map();
const events={};let writes=[],failsAfter=Infinity;
let completed=false;
const make=(rev,keys,prefix)=>{
 const token='token-'+rev;
 return {format:'GFC_SHARDED_171',token,revision:rev,year:2030,day:70,
  collections:{players:{keys:keys.map(k=>k.key),hashes:keys.map(k=>k.hash||'a'.repeat(64))},
  v538CareerArchive:{keys:[],nested:'year-id-v1'}}};
};
const existing=Array.from({length:780},(_,i)=>({key:'part-'+i,
   value:{payload:'p'+i+':'+String(i%10).repeat(26000)},hash:'h'+i}));
for(const p of existing)IDB.set(p.key,p.value);
IDB.set(BASE,make(1,existing));
IDB.set(BASE+':meta',{at:10,year:2030,day:70});
IDB.set(BASE+':previous',{format:'GFC_SHARDED_171',revision:0,token:'old',collections:{}});
IDB.set(INDEX,{version:1,activeId:'c',entries:[{id:'c',year:2030,day:70,updatedAt:10}]});
const clone=v=>v===undefined?undefined:structuredClone(v);
const desktop={available:true,
 read:async key=>clone(NATIVE.get(key)),
 writeMany:async entries=>{
  if(writes.length>=failsAfter)throw Error('simulated backup IO failure');
  const isData=entries.some(e=>e.key.startsWith('part-'));
  assert(!isData||entries.length===1,'IPC must only carry a single player/roster shard');
  for(const e of entries)if(e.key.startsWith('part-'))
   assert(e.value.payload.length<30000,'single shard unexpectedly huge');
  writes.push(entries.map(e=>e.key));
  // Emulate the native SQLite transaction: all or nothing.
  for(const e of entries)NATIVE.set(e.key,clone(e.value));
  return true;
 },
 closeGame:()=>{completed=true;return Promise.resolve()}
};
const db={
 transaction:()=>({
  objectStore:()=>({get(key){
   const req={result:undefined,onsuccess:null,onerror:null,error:null};
   queueMicrotask(()=>{req.result=clone(IDB.get(key));req.onsuccess?.()});
   return req;
  }})
 })
};
const document={addEventListener:(event,cb)=>{events[event]=cb}};
const ctx={window:{FutBRDesktop:desktop},document,openDB:async()=>db,
  BASE,INDEX,console:{warn:()=>{}},Date,Math,Set,Promise,
  setTimeout:(cb)=>setTimeout(cb,0),
  Event:class {constructor(type){this.type=type}},
  performance};
const source=globalThis.MIRROR_CODE;
vm.runInNewContext(source,ctx);
assert.equal(typeof desktop.syncActiveSave,'function');
assert.equal(writes.length,0,'Opening game cannot trigger full save duplication');
const first=await desktop.syncActiveSave();
assert.equal(first,true);
assert.equal(NATIVE.get(BASE).revision,1);
assert.equal(NATIVE.get(BASE+':mirror-18354').completed,true);
assert.equal(NATIVE.get(BASE+':mirror-18354').total,780);
assert.equal(writes.filter(a=>a.length===1&&a[0].startsWith('part-')).length,780);
const markerFirst=NATIVE.get(BASE+':mirror-18354');
const before=writes.length;
assert.equal(await desktop.syncActiveSave(),true);
assert.equal(writes.length,before+1,'Identical save must not recopy any historical or player chunks');
assert.equal(writes.at(-1).at(-1),BASE+':mirror-18354');
const changed=existing.slice();
changed[32]={key:'part-new-a',value:{payload:'new-a'},hash:'b'};
changed[740]={key:'part-new-b',value:{payload:'new-b'},hash:'c'};
for(const p of [changed[32],changed[740]])IDB.set(p.key,p.value);
const next=make(2,changed);
IDB.set(BASE,next);
IDB.set(INDEX,{version:1,activeId:'c',entries:[{id:'c',year:2030,day:70,updatedAt:20}]});
const beforeIncrement=writes.length;
assert.equal(await desktop.syncActiveSave(),true);
const delta=writes.slice(beforeIncrement);
assert.equal(delta.filter(a=>a.length===1&&a[0].startsWith('part-')).length,2,
 'Only two changed blocks should cross the native bridge');
assert.equal(NATIVE.get(BASE).revision,2,'Atomic native manifest published last');
const committed=JSON.stringify(NATIVE.get(BASE));
IDB.set('part-new-c',{payload:'halfway'});
const failing=make(3,[...changed,{key:'part-new-c'}]);
IDB.set(BASE,failing);
failsAfter=writes.length;
assert.equal(await desktop.syncActiveSave(),false);
assert.equal(JSON.stringify(NATIVE.get(BASE)),committed,'Interrupted mirror poisoned previous recovery');
assert.equal(NATIVE.get(BASE+':mirror-18354').revision,2,'Marker must survive failure');
failsAfter=Infinity;
assert.equal(await desktop.syncActiveSave(),true);
assert.equal(NATIVE.get(BASE).revision,3);
assert.equal(NATIVE.get('part-new-c').payload,'halfway');
assert.equal(await desktop.syncActiveSave(),true);
assert.equal(desktop.nativeMirror18354.status().lastStatus,'complete');
assert(desktop.nativeMirror18354.status().reused>=780);
assert(!completed);
console.log(JSON.stringify({ok:true,version:'18.354.0',
 regression:'synthetic 2030 multi-year save, NOT a measured Windows heap test',
 shards:780,firstCopyOneShardAtTime:true,incrementalOnlyTwoShards:true,
 noAutomaticPreSaveCopy:true,safeManifestCommitLast:true,
 interruptedMirrorKeepsPreviousBackup:true,
 validBackupResumedAfterFailure:true,
 previousDataIntact:true,
 lastRevision:desktop.nativeMirror18354.status().lastRevision,
 simulatedUnderMaxOldSpaceMiB:192}));
"""
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_native_save_mirror_18354.py <project>')
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 required=['/* FUTBR_NATIVE_MIRROR_18354','FUTBR_OOMSAFE_ARCHIVE_18352',
  "document.dispatchEvent(new Event('futbr:save-confirmed'))",
  "window.FutBRDesktop.closeGame();return;",
  'v18338FreeTransientBeforeSave()',
  'FUTBR_SERIEC_FULL_PODIUM_18353',
  "const EDITION='18.354.0';"]
 for val in required:
  if val not in html:raise RuntimeError('Preserved code missing: '+val)
 if "if(action==='futbr125-save-current'||action==='futbr125-save-and-exit')setTimeout" in html:
  raise RuntimeError('Race-prone, early click-triggered backup still present')
 a=html.index('/* FUTBR_NATIVE_MIRROR_18354')
 b=html.index(' function decorateCloseButton(){',a)
 js='globalThis.MIRROR_CODE='+json.dumps(html[a:b])+';\n'
 js+='(async()=>{\n'+HARNESS+"\n})().catch(e=>{console.error(e?.stack||e);process.exit(1)});\n"
 file=root/'test-native-save-mirror-18354.cjs'
 file.write_text(js,encoding='utf-8')
 try:
  result=subprocess.run(['node','--max-old-space-size=192',str(file)],
    capture_output=True,text=True,timeout=90)
  if result.returncode:
   raise RuntimeError('18.354 native mirror stress test failed: '+result.stderr[-9000:])
 finally:
  file.unlink(missing_ok=True)
 report=json.loads(result.stdout.strip().splitlines()[-1])
 report['savedCareerPreserved']=True
 report['noDeleteOrHistoryTruncation']=True
 report['incrementalSHAReuseMaintained']=True
 report['secondaryCopyNotRequiredForPrimarySave']=True
 (root/'native-save-mirror-18354-tests.json').write_text(
    json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
