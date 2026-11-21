"""Reuse equal player chunks across UI, ordinary Worker saves and vacations.

Every current batch is hashed again. Reuse is proved by the canonical packed
player bytes, never inferred from a date, object reference or metadata edit.
Apply after the 18.373 bounded vacation boot and storage/jobwait patches.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MARK = 'FUTBR_PLAYER_CHECKPOINT_REUSE_18373'
HASH_FORMAT = 'sha256-player-packed-json-v1'


def once(source, old, new, label):
    if source.count(old) != 1:
        raise RuntimeError(f'18.373 player reuse {label}: expected one anchor, got {source.count(old)}')
    return source.replace(old, new, 1)


def legacy_unpacker(prefix):
    return (f'function {prefix}UnpackPlayer(r){{const [id,lo,hi,vals,extra]=r,p={{id:String(id)}};'
            f'for(let i=0;i<{prefix}PlayerFields.length;i++){{const has=i<32?((lo>>>i)&1):((hi>>>(i-32))&1);'
            f'if(has)p[{prefix}PlayerFields[i]]=vals[i];}}'
            "if(extra&&typeof extra==='object')Object.assign(p,extra);return p;}")


def fast_unpacker(prefix):
    return f'''function {prefix}UnpackPlayer(r){{
 /* FUTBR_PLAYER_FAST_SHAPES_18373: preserve only present fields. Building the
    final object at once avoids a dictionary backing for every decoded player.
    Extra keys retain their last-write precedence; __proto__ stays own data. */
 const [id,lo,hi,vals,extra]=r,entries=[['id',String(id)]];
 for(let i=0;i<{prefix}PlayerFields.length;i++){{
  const has=i<32?((lo>>>i)&1):((hi>>>(i-32))&1);
  if(has)entries.push([{prefix}PlayerFields[i],vals[i]]);
 }}
 if(extra&&typeof extra==='object')for(const key of Reflect.ownKeys(extra))
  if(Object.prototype.propertyIsEnumerable.call(extra,key))entries.push([key,extra[key]]);
 return Object.fromEntries(entries);
}}'''


def patch_unpackers(source):
    for prefix in ('v18191w', 'v18191u', 'v18191m'):
        old, new = legacy_unpacker(prefix), fast_unpacker(prefix)
        if new in source:
            continue
        source = once(source, old, new, prefix + ' fast player decode')
    return source


WORKER = r'''
/* FUTBR_PLAYER_CHECKPOINT_REUSE_18373_WORKER
   Known player fields have a fixed packed order; the expanded object's order
   changes on unpack. Hash the representation that is actually persisted. */
const v18373PlayerHashFormat='sha256-player-packed-json-v1';
const v18373WorkerHashRetain=4*1024*1024;
let v18373WorkerHashEncoder=null,v18373WorkerHashScratch=null;
function v18373WorkerHashInput(text){
 v18373WorkerHashEncoder??=new TextEncoder();
 if(typeof v18373WorkerHashEncoder.encodeInto==='function'&&text.length<=v18373WorkerHashRetain){
  let capacity=v18373WorkerHashScratch?.byteLength||0;
  const needed=Math.max(65536,text.length);
  while(capacity<needed)capacity=Math.min(v18373WorkerHashRetain,Math.max(65536,capacity*2));
  for(;;){
   if(!v18373WorkerHashScratch||v18373WorkerHashScratch.byteLength<capacity)
    v18373WorkerHashScratch=new Uint8Array(capacity);
   const encoded=v18373WorkerHashEncoder.encodeInto(text,v18373WorkerHashScratch);
   if(encoded.read===text.length)return v18373WorkerHashScratch.subarray(0,encoded.written);
   if(capacity>=v18373WorkerHashRetain)break;
   capacity=Math.min(v18373WorkerHashRetain,capacity*2);
  }
 }
 // The ceiling limits retained scratch, not supported player data.
 return v18373WorkerHashEncoder.encode(text);
}
function v18373PreparePackedPlayers(rows){
 const packed=rows.map(([id,p])=>v18191wPackPlayer(p,id));let hashable=true;
 const text=JSON.stringify(packed,(key,value)=>{
  if(typeof value==='undefined'||typeof value==='bigint'||typeof value==='function'||
     typeof value==='symbol'||typeof value==='number'&&!Number.isFinite(value)||
     value&&typeof value==='object'&&(value instanceof ArrayBuffer||ArrayBuffer.isView(value)||
      value instanceof Map||value instanceof Set))hashable=false;
  return value;
 });
 return {packed,text,hashable};
}
async function v18373PackedPlayerHash(prepared,bytes=null){
 if(!prepared.hashable||!globalThis.crypto?.subtle)return null;
 // A vacation already owns its transferable bytes. Hash those BEFORE sending
 // them; the reusable scratch below is never exposed or transferred.
 const input=bytes||v18373WorkerHashInput(prepared.text);
 const digest=await globalThis.crypto.subtle.digest('SHA-256',input);
 return Array.from(new Uint8Array(digest),v=>v.toString(16).padStart(2,'0')).join('');
}
'''


def patch(source):
    if MARK in source:
        return patch_unpackers(source)
    for required in ('FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN', 'FUTBR_VACATION_BOUNDED_BOOT_18373',
                     'FUTBR_JOBWAIT_SINGLE_OWNER_18373'):
        if required not in source:
            raise RuntimeError('Missing prerequisite ' + required)

    a = source.index('function v53WorkerMain(){')
    b = source.index('\n\n\nconst v18191uPlayerFields=', a)
    worker = source[a:b]
    worker = once(worker, 'const v18343HistoricalKeys=new Set([', WORKER + '\nconst v18343HistoricalKeys=new Set([', 'worker helpers')
    worker = once(worker,
        "const digest=await globalThis.crypto.subtle.digest('SHA-256',new TextEncoder().encode(text));",
        "const digest=await globalThis.crypto.subtle.digest('SHA-256',v18373WorkerHashInput(text));",
        'reuse worker fingerprint buffer')
    worker = once(worker,
        'async function v18191wEncodePlayerChunk(rows){const packed=rows.map(([id,p])=>v18191wPackPlayer(p,id)),text=JSON.stringify(packed);',
        'async function v18191wEncodePlayerChunk(rows,prepared18373=null){const packed=prepared18373?.packed||rows.map(([id,p])=>v18191wPackPlayer(p,id)),text=prepared18373?.text??JSON.stringify(packed);',
        'reuse already prepared player encoding')
    worker = once(worker,
        "(key!=='players'||old.collections[key].encoding===v18191wPlayerFormat)&&(!nested||old.collections[key].nested===nestedFormat)?",
        "(key!=='players'||old.collections[key].encoding===v18191wPlayerFormat&&old.collections[key].archiveHash===v18373PlayerHashFormat)&&(!nested||old.collections[key].nested===nestedFormat)?",
        'ordinary worker compatible hash scheme')
    worker = once(worker, "baseLimit=key==='players'?(Number(s.year)>=2029?800:1600):",
        "baseLimit=key==='players'?(Number(s.year)>=2029?512:768):", 'ordinary worker player boundaries')
    worker = once(worker,
        'const index=chunk++,fingerprint=history?await v18343Fingerprint(raw):null;',
        "const index=chunk++,prepared18373=key==='players'?v18373PreparePackedPlayers(raw):null,\n    fingerprint=history?(prepared18373?await v18373PackedPlayerHash(prepared18373):await v18343Fingerprint(raw)):null;",
        'ordinary worker canonical hash')
    worker = once(worker,
        "const payload=key==='players'?await v18191wEncodePlayerChunk(raw):raw,",
        "const payload=key==='players'?await v18191wEncodePlayerChunk(raw,prepared18373):raw,",
        'ordinary worker prepared compression')
    worker = once(worker, "...(history?{hashes,archiveHash:'sha256-json-v1'}:null),",
        "...(history?{hashes,archiveHash:key==='players'?v18373PlayerHashFormat:'sha256-json-v1'}:null),",
        'ordinary worker explicit hash tag')

    # Vacation chunks already supply packed bytes to both transfer and gzip.
    # Their fingerprint reuses those bytes before postMessage detaches them.
    start = worker.index(' async function v18310PackVacationRows(')
    end = worker.index('const v18310SyncWaiters=', start)
    pack = worker[start:end]
    pack = once(pack,
        'const packed=rows.map(([id,p])=>v18191wPackPlayer(p,id));\n const text=JSON.stringify(packed),bytes=new TextEncoder().encode(text).buffer;',
        'const prepared18373=v18373PreparePackedPlayers(rows),packed=prepared18373.packed;\n const text=prepared18373.text,bytes=new TextEncoder().encode(text).buffer;', 'prepare streamed canonical bytes')
    pack = once(pack, 'if(!checkpointNeeded)return {bytes,stored};',
        'if(!checkpointNeeded)return {bytes,stored};\n const hash=await v18373PackedPlayerHash(prepared18373,bytes);', 'hash existing transferable bytes')
    pack = once(pack, 'return {bytes,stored};\n}', 'return {bytes,stored,hash};\n}', 'return bounded fingerprint')
    worker = worker[:start] + pack + worker[end:]
    worker = once(worker,
        "const limit=key==='players'?(Number(finalYear)>=2029?Math.min(768,(2400)):(2400)):",
        "const limit=key==='players'?(Number(finalYear)>=2029?512:768):", 'vacation player boundaries')
    worker = once(worker, 'let rows=[],ids=[],done=0,chunk=0;',
        "let rows=[],ids=[],done=0,chunk=0;const playerHashes18373=key==='players'?[]:null;", 'vacation fingerprint metadata')
    worker = once(worker,
        'const packed=await v18310PackVacationRows(payload,!!checkpointMeta);stored=packed.stored;',
        'const packed=await v18310PackVacationRows(payload,!!checkpointMeta);stored=packed.stored;\n    if(checkpointMeta)playerHashes18373.push(packed.hash);', 'vacation fingerprint capture')
    worker = once(worker,
        "checkpointMeta.collections[key]={isArray,length:originalLength,chunks:chunk,...(key==='players'?{encoding:v18191wPlayerFormat}:null)};",
        "checkpointMeta.collections[key]={isArray,length:originalLength,chunks:chunk,...(key==='players'?{encoding:v18191wPlayerFormat,hashes:playerHashes18373,archiveHash:v18373PlayerHashFormat}:null)};",
        'vacation checkpoint hash tag')
    worker = once(worker, '...(spec.nested?{nested:spec.nested}:null)};',
        '...(spec.nested?{nested:spec.nested}:null),\n     ...(key===\'players\'&&spec.archiveHash===v18373PlayerHashFormat&&Array.isArray(spec.hashes)&&spec.hashes.length===count?{hashes:spec.hashes,archiveHash:spec.archiveHash}:null)};',
        'promote exact vacation hashes')
    source = source[:a] + worker + source[b:]

    a = source.index('/* FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN')
    b = source.index('/* FUTBR_SAVE_MEMORY_RUNTIME_18373_END */', a)
    runtime = source[a:b]
    runtime = once(runtime, ' async function writeCollection(token,key,value,previous,check){',
        " /* FUTBR_PLAYER_CHECKPOINT_REUSE_18373_UI */\n const playerHashFormat18373='sha256-player-packed-json-v1';\n async function writeCollection(token,key,value,previous,check){", 'UI explicit hash scheme')
    runtime = once(runtime, "(key!=='players'||previous.encoding===v18191uPlayerFormat)?previous:null;",
        "(key!=='players'||previous.encoding===v18191uPlayerFormat&&previous.archiveHash===playerHashFormat18373)?previous:null;", 'UI compatible fingerprints')
    runtime = once(runtime, 'const at=index++,hash=await fingerprint(raw);hashes.push(hash);',
        "const at=index++,hash=await fingerprint(key==='players'?raw.map(([id,p])=>v18191uPackPlayer(p,id)):raw);hashes.push(hash);", 'UI recomputes every current packed batch')
    runtime = once(runtime, "return {isArray,length:isArray?value.length:0,keys,hashes,archiveHash:'sha256-json-v1',",
        "return {isArray,length:isArray?value.length:0,keys,hashes,archiveHash:key==='players'?playerHashFormat18373:'sha256-json-v1',", 'UI canonical hash tag')
    return patch_unpackers(source[:a] + runtime + source[b:])


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: fix_player_checkpoint_reuse_18373.py <project>')
    root = Path(sys.argv[1])
    path = root / 'src/index.html'
    path.write_text(patch(path.read_text(encoding='utf-8')), encoding='utf-8')
    report = {'ok': True, 'version': '18.373.0',
              'canonicalPackedPlayerHash': True, 'threeWritersUseAlignedPlayerChunks': True,
              'vacationManifestCarriesPlayerHashes': True, 'currentContentVerifiedBeforeReuse': True,
              'legacyHashSchemesFailClosed': True, 'workerScratchNeverTransferred': True,
              'threeUnpackersBuildFastPlayerObjects': True,
              'packedPresenceAndExtraPrecedencePreserved': True,
              'prototypeKeysDecodedAsSafeOwnData': True}
    (root / 'player-checkpoint-reuse-18373-install.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
