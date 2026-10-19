from __future__ import annotations
import subprocess, sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def once(text, old, new, label):
    if old not in text:
        fail(label + ': ancora nao encontrada')
    return text.replace(old, new, 1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: optimize_long_career_memory.py <project-dir>')
    path=Path(sys.argv[1]).resolve()/'src'/'index.html'
    html=path.read_text(encoding='utf-8')

    # 1) Historical collections must not travel inside the monolithic root object.
    old="const SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','crestOverrides'];"
    new="const SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive','crestOverrides'];"
    html=once(html,old,new,'long-career UI sharded histories')
    old="const V171_FORMAT='GFC_SHARDED_171',V171_SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','crestOverrides'];"
    new="const V171_FORMAT='GFC_SHARDED_171',V171_SHARDS=['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats','v538CareerArchive','v555CareerArchive','scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive','crestOverrides'];"
    html=once(html,old,new,'long-career worker sharded histories')

    # 2) Bound the per-season league-table cache even before rollover.
    old="const rows=v540RawTable(s,c,d);m.set(token,rows.slice());return rows;"
    new="const rows=v540RawTable(s,c,d);m.set(token,rows.slice());if(m.size>48)m.delete(m.keys().next().value);return rows;"
    html=once(html,old,new,'bounded table cache')

    # 3) Preserve every historical scorer row. Memory is reduced only by stripping
    # redundant fields; no player/statistical record is discarded.
    start=html.find('function v94CompactScorerArchive(stats){')
    if start<0: fail('v94CompactScorerArchive ausente')
    end=html.find('\nfunction v94PackCurrentCareerArchive',start)
    if end<0: fail('fim v94CompactScorerArchive ausente')
    compact=r"""function v94CompactScorerArchive(stats){
 const out={};
 for(const [key,rows] of Object.entries(stats||{})){
  let kept=null;
  for(const [pid,r] of Object.entries(rows||{})){
   const goals=Number(r?.goals)||0,assists=Number(r?.assists)||0;
   if(goals<=0&&assists<=0)continue;
   (kept??={})[pid]={id:r.id||pid,name:r.name||'',natCode:r.natCode||'UNK',real:!!r.real,star:!!r.star,goals,assists,apps:Number(r?.apps)||0,minutes:Number(r?.minutes)||0,clubs:r.clubs||{},byClub:r.byClub||{}};
  }
  if(kept)out[key]=kept;
 }
 return out;
}"""
    html=html[:start]+compact+html[end:]

    # 4) Batch native desktop writes. The previous path performed one Tauri IPC
    # call per shard chunk; a season checkpoint could issue hundreds of calls.
    ui_start=html.find(" async function writeCollection(token,key,value,limit){")
    if ui_start<0: ui_start=html.find("async function writeCollection(token,key,value,limit){")
    ui_end=html.find(" async function saveSharded(",ui_start)
    if ui_end<0: ui_end=html.find("async function saveSharded(",ui_start)
    if ui_start<0 or ui_end<0: fail('writeCollection UI ausente')
    ui_write=r"""async function v18183DbWriteMany(entries){
  if(!entries?.length)return true;
  if(window.FutBRDesktop?.directStorage){await window.FutBRDesktop.writeMany(entries);return true;}
  const db=await openDB();
  return new Promise((resolve,reject)=>{
   const tx=db.transaction('saves','readwrite'),os=tx.objectStore('saves');
   for(const entry of entries)os.put(entry.value,entry.key);
   tx.oncomplete=()=>resolve(true);
   tx.onerror=()=>reject(tx.error||Error('Falha ao gravar lote de shards'));
   tx.onabort=()=>reject(tx.error||Error('Lote de shards interrompido'));
  });
 }
 async function writeCollection(token,key,value,limit){
  const isArray=Array.isArray(value),keys=[];let rows=[],idx=0,writes=0,pending=[];
  const commit=async(force=false)=>{
   if(!pending.length)return;
   const target=key==='players'?4:key==='allTimeStats'?8:6;
   if(!force&&pending.length<target)return;
   const batch=pending.splice(0,pending.length);
   await v18183DbWriteMany(batch);
   await new Promise(r=>setTimeout(r,0));
  };
  const flush=async()=>{
   if(!rows.length)return;const payload=rows;rows=[];const ck=shardKey(token,key,idx++);keys.push(ck);pending.push({key:ck,value:payload});writes++;
   if(key==='players')stats.playerChunksWritten++;
   if(v18121NewSeasonPreparation&&(key!=='players'||writes===1||writes%10===0)){v53Sim.progress=key==='players'?'Salvando jogadores · bloco '+writes:'Salvando '+key+' da nova temporada';try{v53PaintStatus();}catch(e){}}
   await commit(false);
  };
  for(const id in (value||{})){rows.push([id,value[id]]);if(rows.length>=limit)await flush();}
  await flush();await commit(true);return {isArray,length:isArray?value.length:0,keys};
 }
 """
    html=html[:ui_start]+ui_write+html[ui_end:]

    # Historical archives are immutable during an active season. After the first
    # checkpoint of a new year, reuse their shard keys instead of rewriting them
    # on every ordinary save.
    save_ui=html.find("async function saveSharded(s,mode='full'){")
    if save_ui<0: fail('saveSharded UI ausente')
    loop_start=html.find("for(const key of SHARDS){",save_ui)
    loop_end=html.find("const meta=",loop_start)
    if loop_start<0 or loop_end<0: fail('loop SHARDS UI ausente')
    new_loop="const stableSeasonShards=new Set(['v538CareerArchive','v555CareerArchive','scorerArchive']);for(const key of SHARDS){const value=s[key];if(value==null)continue;const employmentReuse=mode==='employment'&&old?.format===FORMAT&&!['teams','coaches'].includes(key)&&old.collections?.[key],seasonReuse=old?.format===FORMAT&&Number(old.year)===Number(s.year)&&!s.seasonDone&&stableSeasonShards.has(key)&&old.collections?.[key];if(employmentReuse||seasonReuse){collections[key]=old.collections[key];continue;}const limit=key==='players'?2400:key==='teams'?420:key==='coaches'?520:key==='schedule'?4:key==='competitionStats'?4:key==='allTimeStats'?700:(key==='v538CareerArchive'||key==='v555CareerArchive'||key==='scorerArchive'?1:120);collections[key]=await writeCollection(token,key,value,limit);} "
    html=html[:loop_start]+new_loop+html[loop_end:]

    # Worker bridge supports batched writes too, avoiding hundreds of UI<->Rust
    # round-trips during vacation checkpoints.
    old="async function v93RawWrite(key,value){const d=await database();if(!d)return hostRequest('raw-write',{key,value});return new Promise((res,rej)=>{const tx=d.transaction('saves','readwrite');tx.objectStore('saves').put(value,key);tx.oncomplete=()=>res(true);tx.onerror=()=>rej(tx.error||Error('Falha no checkpoint'));tx.onabort=()=>rej(tx.error||Error('Checkpoint interrompido'));});}"
    new=old+chr(10)+" async function v18181RawWriteMany(entries){if(!entries?.length)return true;const d=await database();if(!d)return hostRequest('raw-write-many',{entries});return new Promise((res,rej)=>{const tx=d.transaction('saves','readwrite'),os=tx.objectStore('saves');for(const e of entries)os.put(e.value,e.key);tx.oncomplete=()=>res(true);tx.onerror=()=>rej(tx.error||Error('Falha no lote de checkpoint'));tx.onabort=()=>rej(tx.error||Error('Lote de checkpoint interrompido'));});}"
    html=once(html,old,new,'worker batch helper')

    bridge="if(m.operation==='raw-write'){await window.FutBRDesktop.write(m.key,m.value);return true;}"
    insert="if(m.operation==='raw-write'){await window.FutBRDesktop.write(m.key,m.value);return true;}\n  if(m.operation==='raw-write-many'){await window.FutBRDesktop.writeMany(m.entries||[]);return true;}"
    html=once(html,bridge,insert,'desktop worker batch bridge')
    bridge="if(m.operation==='raw-write')return new Promise((res,rej)=>{const tx=d.transaction('saves','readwrite');tx.objectStore('saves').put(m.value,m.key);tx.oncomplete=()=>res(true);tx.onerror=()=>rej(tx.error||Error('Erro de armazenamento'));tx.onabort=()=>rej(tx.error||Error('Gravação interrompida'));});"
    insert=bridge+"\n if(m.operation==='raw-write-many')return new Promise((res,rej)=>{const tx=d.transaction('saves','readwrite'),os=tx.objectStore('saves');for(const e of m.entries||[])os.put(e.value,e.key);tx.oncomplete=()=>res(true);tx.onerror=()=>rej(tx.error||Error('Erro de armazenamento em lote'));tx.onabort=()=>rej(tx.error||Error('Gravação em lote interrompida'));});"
    html=once(html,bridge,insert,'browser worker batch bridge')

    # Worker full saves use the same same-season archive reuse and batched writes.
    save_worker=html.find("async function save(s){")
    if save_worker<0: fail('save worker ausente')
    loop_start=html.find("for(const key of V171_SHARDS){",save_worker)
    loop_end=html.find("const manifest=",loop_start)
    if loop_start<0 or loop_end<0: fail('loop V171_SHARDS worker ausente')
    new_loop="const v18181Stable=new Set(['v538CareerArchive','v555CareerArchive','scorerArchive']);for(const key of V171_SHARDS){const value=s[key];if(value==null)continue;const sameSeason=old?.format===V171_FORMAT&&Number(old.year)===Number(s.year)&&!s.seasonDone&&v18181Stable.has(key)&&old.collections?.[key];if(sameSeason){collections[key]=old.collections[key];continue;}const isArray=Array.isArray(value),keys=[],limit=key==='players'?2200:key==='teams'?380:key==='coaches'?500:key==='schedule'?4:key==='competitionStats'?4:key==='allTimeStats'?650:(key==='v538CareerArchive'||key==='v555CareerArchive'||key==='scorerArchive'?1:120);let rows=[],chunk=0,done=0,pending=[];const commit=async(force=false)=>{if(!pending.length)return;const target=key==='players'?2:key==='allTimeStats'?6:4;if(!force&&pending.length<target)return;await v18181RawWriteMany(pending.splice(0,pending.length));await new Promise(r=>setTimeout(r,0));};const flush=async()=>{if(!rows.length)return;const payload=rows;rows=[];const ck=v171ShardKey(token,key,chunk++);keys.push(ck);pending.push({key:ck,value:payload});done++;await commit(false);};for(const id in value){if(!safe(id))continue;rows.push([id,value[id]]);if(rows.length>=limit)await flush();}await flush();await commit(true);collections[key]={isArray,length:isArray?value.length:0,keys};} "
    html=html[:loop_start]+new_loop+html[loop_end:]

    # scorerArchive is immutable during vacation and already exists in the saved
    # base. Never clone it into the vacation root again.
    vac_marker="key==='v555CareerArchive'||key==='crestOverrides'"
    vac_repl="key==='v555CareerArchive'||key==='scorerArchive'||key==='crestOverrides'"
    html=once(html,vac_marker,vac_repl,'vacation immutable scorer archive')

    # 4) Avoid allocating a filtered transfers array once for every player while
    # building the annual career archive.
    old="const names={},packed={};\n  const append="
    new="const names={},packed={},lastTransferTo=new Map();for(const m of s.transfers||[])if(Number(m?.year)===Number(year)&&m?.id&&m?.to)lastTransferTo.set(m.id,m.to);\n  const append="
    html=once(html,old,new,'career archive transfer index')
    old="last=(s.transfers||[]).filter(m=>Number(m.year)===Number(year)&&m.id===pid&&m.to).at(-1)?.to||null"
    new="last=lastTransferTo.get(pid)||null"
    html=once(html,old,new,'career archive transfer lookup')

    # 5) Drop known transient state before and after the rollover. These objects can
    # otherwise coexist with the newly-created schedule during peak allocation.
    old="const tNext=performance.now();E.nextSeason(state);v168Stats.nextSeasonMs=performance.now()-tNext;"
    new="v168DropStateCaches(state);v168StopBackground();try{if(typeof v53PatchQueue!=='undefined')v53PatchQueue.length=0;}catch(e){}const tNext=performance.now();E.nextSeason(state);v168Stats.nextSeasonMs=performance.now()-tNext;"
    html=once(html,old,new,'pre-rollover transient purge')

    # 6) v169 is the final rollover authority. Purge caches/workers BEFORE its
    # E.nextSeason call too, otherwise the old derived world can coexist with the
    # freshly-created calendar at the exact peak that caused the OOM.
    old="try{G.v168?.stop?.();}catch(e){}try{G.v100?.repair?.stopBackground?.(true);}catch(e){}"
    new="try{G.v168?.stop?.();G.v168?.purge?.();}catch(e){}try{G.v170?.release?.();}catch(e){}try{G.v100?.repair?.stopBackground?.(true);}catch(e){}"
    html=once(html,old,new,'v169 pre-rollover purge')

    # 7) Expose diagnostics for long-career testing.
    marker="window.GestorFC.v168={"
    if marker not in html: fail('v168 diagnostics ausente')
    diag=r"""
window.GestorFC.longCareerMemory={
 version:'18.181-long-career-fast-checkpoint',
 scorerArchiveLimitPerCompetition:null,
 tableCacheEntries:48,
  desktopBatchWrites:true,
  indexedDbBatchTransaction:true,
  playerShardTransactionBatch:4,
  sameSeasonHistoricalShardReuse:true,
 shardedHistories:['scorerArchive','transfers','retirements','history','internationalHistory','v735NationalArchive'],
 snapshot:()=>({
  year:state?.year||0,day:state?.day||0,
  players:Object.keys(state?.players||{}).length,
  scorerYears:state?.scorerArchive?.length||0,
  scorerRows:(state?.scorerArchive||[]).reduce((n,a)=>n+Object.values(a?.competitions||{}).reduce((m,db)=>m+Object.keys(db||{}).length,0),0),
  careerYears:Object.keys(state?.v555CareerArchive||{}).length,
  transfers:state?.transfers?.length||0,
  retirements:state?.retirements?.length||0,
  nationalArchive:state?.v735NationalArchive?.length||0,
  heapMiB:performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null,
  workerResident:!!v53Worker
 })
};
"""
    html=html.replace(marker,diag+marker,1)

    create_checkpoint=r"""
<script id="futbr-single-create-checkpoint">
(()=>{
 let consolidating=false,forceFlush=false;
 const basePersist=persist,baseFlush=v52FlushSave,basePrepare=v53Prepare;
 persist=function(notify=false){
  if(consolidating&&state){
   try{E.invalidateMarket(state);}catch(e){}
   try{v52MarketIndex=null;}catch(e){}
   v52SaveStats.requests++;v52PendingState=state;v52SaveDirty=true;v52NotifySave||=notify;
   try{updateSaveStatus();}catch(e){}
   return Promise.resolve(true);
  }
  return basePersist(notify);
 };
 v52FlushSave=async function(...args){
  if(consolidating&&!forceFlush)return null;
  return baseFlush(...args);
 };
 async function finalCreateCheckpoint(){
  if(!state)return;
  v52PendingState=state;v52SaveDirty=true;
  forceFlush=true;
  try{await baseFlush();if(v52SavePromise)await v52SavePromise;}
  finally{forceFlush=false;}
  if(!saveOK)throw Error('Nao foi possivel concluir o checkpoint da nova carreira.');
 }
 v53Prepare=async function(op,params={}){
  if(op!=='create')return basePrepare(op,params);
  // Preserve an older mounted career before entering create consolidation.
  await baseFlush();if(v52SavePromise)await v52SavePromise;
  consolidating=true;
  try{
   const out=await basePrepare(op,params);
   if(state)await finalCreateCheckpoint();
   return out;
  }finally{consolidating=false;}
 };
 if(typeof v643PrepareNationalCareer==='function'){
  const baseNational=v643PrepareNationalCareer;
  v643PrepareNationalCareer=async function(options={}){
   await baseFlush();if(v52SavePromise)await v52SavePromise;
   consolidating=true;
   try{
    const out=await baseNational(options);
    if(state)await finalCreateCheckpoint();
    return out;
   }finally{consolidating=false;}
  };
 }
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.createCheckpointOptimization={
  version:'18.185-single-create-checkpoint',
  oneAuthoritativeCheckpoint:true,
  intermediatePersistCoalesced:true,
  previousCareerFlushedBeforeCreate:true
 };
})();
</script>
"""
    if 'futbr-single-create-checkpoint' not in html:
        html=html.replace('</body>',create_checkpoint+'\n</body>',1)

    path.write_text(html,encoding='utf-8')

    relational = Path(__file__).with_name('add_relational_history_storage.py')
    if not relational.exists():
        fail('add_relational_history_storage.py ausente')
    subprocess.run([sys.executable, str(relational), str(Path(sys.argv[1]).resolve())], check=True)

    print('Long-career memory optimization applied with relational history foundation.')

if __name__=='__main__':
    main()
