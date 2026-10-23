from __future__ import annotations
import json, re, sys
from pathlib import Path

VERSION='18.310'

def once(src,old,new,label):
    n=src.count(old)
    if n!=1:raise RuntimeError(f'{label}: expected 1 anchor, got {n}')
    return src.replace(old,new,1)

def section(src,start,end,label):
    a=src.find(start)
    b=src.find(end,a+len(start)) if a>=0 else -1
    if a<0 or b<0:raise RuntimeError(label+': boundaries missing')
    return a,b

PACK_VACATION=r'''
async function v18310PackVacationRows(rows,checkpointNeeded=true){
 const packed=rows.map(([id,p])=>v18191wPackPlayer(p,id));
 const text=JSON.stringify(packed),bytes=new TextEncoder().encode(text).buffer;
 let stored=null;
 if(!checkpointNeeded)return {bytes,stored};
 if(typeof CompressionStream==='function'){
  const gz=await new Response(new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();
  stored={format:v18191wPlayerFormat,encoding:'gzip-base64',data:v18191wArrayBufferToBase64(gz),count:packed.length};
 }else stored={format:v18191wPlayerFormat,encoding:'json',data:text,count:packed.length};
 return {bytes,stored};
}
const v18310SyncWaiters=new Map();
function v18310ResolveSyncAck(seq){
 v18117SyncAck=Math.max(v18117SyncAck,Number(seq)||0);
 for(const [wanted,entry] of v18310SyncWaiters){
  if(wanted<=v18117SyncAck){clearTimeout(entry.timer);v18310SyncWaiters.delete(wanted);entry.resolve();}
 }
}
async function v18310WorkerDeleteMany(keys){
 if(!keys.length)return;
 const db=await database();
 for(let i=0;i<keys.length;i+=160){
  const batch=keys.slice(i,i+160);
  if(!db){await hostRequest('raw-delete-many',{keys:batch});continue;}
  await new Promise((resolve,reject)=>{
   const tx=db.transaction('saves','readwrite'),store=tx.objectStore('saves');
   for(const key of batch)store.delete(key);
   tx.oncomplete=()=>resolve(true);
   tx.onerror=()=>reject(tx.error||Error('Falha na limpeza do checkpoint'));
   tx.onabort=()=>reject(tx.error||Error('Limpeza interrompida'));
  });
 }
}
'''

VACATION_STREAM=r'''
async function streamVacationWorld125(destructive=true,skipCheckpoint=false){
 if(!world)return;
 const started=performance.now(),finalDay=world.day,finalYear=world.year,collections=[...shards],root={};
 for(const [key,value] of Object.entries(world)){
  if(!safe(key)||key==='v538CareerArchive'||key==='v555CareerArchive'||key==='scorerArchive'||key==='crestOverrides'||key==='v81ClubRank'||collections.includes(key))continue;
  root[key]=value;
 }
 let checkpointMeta=null,checkpointOK=false,pending=[],writes=0,playerBytes=0,playerCount=0;
 const checkpointError=e=>{
  checkpointMeta=null;pending.length=0;
  self.postMessage({kind:'vac-checkpoint-error',session,error:e?.message||String(e)});
 };
 const commitPending=async(force=false)=>{
  if(!checkpointMeta||!pending.length||(!force&&pending.length<8))return;
  const entries=pending;pending=[];
  try{await v18181RawWriteMany(entries);writes++;}catch(e){checkpointError(e);}
 };
 if(!skipCheckpoint)try{
  const token=String(finalYear)+'-'+String(finalDay)+'-'+String(session)+'-'+String(Date.now()),rootKey=V93_VAC_PREFIX+token+':root';
  checkpointMeta={format:'GFC_VAC_CHECKPOINT_93',token,year:Number(finalYear)||0,day:Number(finalDay)||0,rootKey,collections:{},at:Date.now()};
  await v93RawWrite(rootKey,root);
 }catch(e){checkpointError(e);}
 const startSeq=++v18117SyncSeq;
 self.postMessage({kind:'vac-sync-start',session,syncSeq:startSeq,root,collections,day:finalDay,year:finalYear});
 await v18117WaitSyncAck(startSeq);
 for(const key of collections){
  const value=world[key]||(['teams','schedule'].includes(key)?[]:{}),isArray=Array.isArray(value),originalLength=isArray?value.length:0;
  const limit=key==='players'?900:key==='competitionStats'?1:key==='schedule'?2:key==='teams'?250:260;
  let total=originalLength;if(key==='players'){total=0;for(const id in value)if(safe(id))total++;}
  self.postMessage({kind:'vac-sync-collection-start',session,key,isArray,length:originalLength,total});
  let rows=[],ids=[],done=0,chunk=0;
  const flush=async()=>{
   if(!rows.length)return;
   const payload=rows,drop=ids;rows=[];ids=[];
   const syncSeq=++v18117SyncSeq;
   let stored=payload;
   if(key==='players'){
    const packed=await v18310PackVacationRows(payload,!!checkpointMeta);stored=packed.stored;
    playerBytes+=packed.bytes.byteLength;playerCount+=payload.length;
    self.postMessage({kind:'vac-sync-part',session,key,done,total,syncSeq,format:'player-packed-buffer-v1',bytes:packed.bytes},[packed.bytes]);
   }else self.postMessage({kind:'vac-sync-part',session,key,rows:payload,done,total,syncSeq});
   if(checkpointMeta){
    pending.push({key:v93CheckpointKey(checkpointMeta.token,key,chunk++),value:stored});
    await commitPending(false);
   }
   if(destructive&&key==='players')for(const id of drop)delete value[id];
   await v18117WaitSyncAck(syncSeq);
  };
  for(const id in value){if(!safe(id))continue;rows.push([id,value[id]]);ids.push(id);done++;if(rows.length>=limit)await flush();}
  await flush();await commitPending(true);
  if(checkpointMeta)checkpointMeta.collections[key]={isArray,length:originalLength,chunks:chunk,...(key==='players'?{encoding:v18191wPlayerFormat}:null)};
  self.postMessage({kind:'vac-sync-collection-end',session,key,done});
  if(destructive)world[key]=null;
  await new Promise(r=>setTimeout(r,0));
 }
 if(checkpointMeta)try{await v93RawWrite(V93_VAC_META,checkpointMeta);checkpointOK=true;}catch(e){checkpointError(e);}
 if(destructive)world.v538CareerArchive=null;
 self.postMessage({kind:'vac-sync-end',session,day:finalDay,year:finalYear,checkpoint:checkpointOK,checkpointToken:checkpointMeta?.token||null,performance18310:{ms:Math.round(performance.now()-started),writes,playerBytes,playerCount,maxPendingChunks:8}});
}
'''

WAIT_ACK=r'''
async function v18117WaitSyncAck(seq){
 if(v18117SyncAck>=seq)return;
 await new Promise((resolve,reject)=>{
  const timer=setTimeout(()=>{
   v18310SyncWaiters.delete(seq);
   reject(Error('Sincronizacao de ferias: a interface nao confirmou o lote; retome do ultimo save.'));
  },40000);
  v18310SyncWaiters.set(seq,{resolve,reject,timer});
  if(v18117SyncAck>=seq)v18310ResolveSyncAck(v18117SyncAck);
 });
}
'''

UI_ROWS=r'''function v18310VacationRows(m){
 if(m.format==='player-packed-buffer-v1'&&m.bytes instanceof ArrayBuffer){
  const packed=JSON.parse(new TextDecoder().decode(m.bytes));m.bytes=null;
  return packed.map(r=>{const p=v18191uUnpackPlayer(r);return [p.id,p];});
 }
 if(m.format==='json-buffer'&&m.bytes instanceof ArrayBuffer){
  const rows=JSON.parse(new TextDecoder().decode(m.bytes));m.bytes=null;return rows;
 }
 return m.rows||[];
}
'''

def patch_html(html):
    html=once(html,'async function streamVacationWorld125(destructive=true,skipCheckpoint=false){',PACK_VACATION+'\nasync function streamVacationWorld125(destructive=true,skipCheckpoint=false){','vacation helpers')
    a,b=section(html,'async function streamVacationWorld125(destructive=true,skipCheckpoint=false){','async function simulate(message){','vacation stream')
    html=html[:a]+VACATION_STREAM+'\n '+html[b:]
    a,b=section(html,'async function v18117WaitSyncAck(', 'async function v18310PackVacationRows(', 'ack wait')
    html=html[:a]+WAIT_ACK+'\n '+html[b:]
    html=once(html,"if(m.op==='vac-sync-ack'){v18117SyncAck=Math.max(v18117SyncAck,Number(m.seq)||0);return;}","if(m.op==='vac-sync-ack'){v18310ResolveSyncAck(m.seq);return;}",'resolve ack without polling')
    html=once(html,'const v53Base={render,renderWelcome,act,persist,guardManage,loadLocal,helpPage,vacationPage,commitDay,downloadFile};',UI_ROWS+'\nconst v53Base={render,renderWelcome,act,persist,guardManage,loadLocal,helpPage,vacationPage,commitDay,downloadFile};','UI vacation decoder')
    old="rows=m.format==='json-buffer'&&m.bytes instanceof ArrayBuffer?JSON.parse(new TextDecoder().decode(m.bytes)):(m.rows||[])"
    n=html.count(old)
    if n!=2:raise RuntimeError(f'Expected both vacation decoders, got {n}')
    html=html.replace(old,'rows=v18310VacationRows(m)')
    html=once(html,'const archive538=state?.v538CareerArchive,archive555=state?.v555CareerArchive,overrides=state?.crestOverrides;', 'const archive538=state?.v538CareerArchive,archive555=state?.v555CareerArchive,scorers=state?.scorerArchive,overrides=state?.crestOverrides;','retain scorer archive reference')
    html=once(html,'v125VacIncoming={...(m.root||{}),v538CareerArchive:archive538||{},v555CareerArchive:archive555||{},crestOverrides:overrides||{}};', 'v125VacIncoming={...(m.root||{}),v538CareerArchive:archive538||{},v555CareerArchive:archive555||{},scorerArchive:scorers||[],crestOverrides:overrides||{}};','reattach immutable scorer history')
    old="async function v171DropManifest(manifest,keep=new Set()){if(manifest?.format!==V171_FORMAT)return;for(const spec of Object.values(manifest.collections||{}))for(const key of spec?.keys||[])if(key&&!keep.has(key))try{await v93RawDelete(key);}catch(e){}}"
    new="async function v171DropManifest(manifest,keep=new Set()){if(manifest?.format!==V171_FORMAT)return;const stale=[];for(const spec of Object.values(manifest.collections||{}))for(const key of spec?.keys||[])if(key&&!keep.has(key))stale.push(key);try{await v18310WorkerDeleteMany(stale);}catch(e){console.warn('[18.310] cleanup deferred',e?.message||e);}}"
    html=once(html,old,new,'batch worker obsolete shards')
    html=once(html,"await v93RawWrite(STORE+':previous',old);await v93RawWrite(STORE,manifest);await v93RawWrite(STORE+':meta',meta);", "await v18181RawWriteMany([{key:STORE+':previous',value:old},{key:STORE,value:manifest},{key:STORE+':meta',value:meta}]);",'atomic worker manifest')
    desktop="if(m.operation==='raw-write-many'){await window.FutBRDesktop.writeMany(m.entries||[]);return true;}"
    html=once(html,desktop,desktop+"\n  if(m.operation==='raw-delete-many'){await window.FutBRDesktop.removeMany(m.keys||[]);return true;}",'native cleanup bridge')
    browser="if(m.operation==='raw-write-many')return new Promise((res,rej)=>{const tx=d.transaction('saves','readwrite'),os=tx.objectStore('saves');for(const e of m.entries||[])os.put(e.value,e.key);tx.oncomplete=()=>res(true);tx.onerror=()=>rej(tx.error||Error('Erro de armazenamento em lote'));tx.onabort=()=>rej(tx.error||Error('Grava\u00e7\u00e3o em lote interrompida'));});"
    html=once(html,browser,browser+"\n if(m.operation==='raw-delete-many')return new Promise((res,rej)=>{const tx=d.transaction('saves','readwrite'),os=tx.objectStore('saves');for(const key of m.keys||[])os.delete(key);tx.oncomplete=()=>res(true);tx.onerror=()=>rej(tx.error||Error('Falha na limpeza'));tx.onabort=()=>rej(tx.error||Error('Limpeza interrompida'));});",'browser cleanup bridge')
    return html

HISTORY_BEFORE=r'''
        CREATE INDEX IF NOT EXISTS idx_pss_season_player ON player_season_stats(season,player_id);
        CREATE TEMP TABLE IF NOT EXISTS v18310_season_delta(
            player_id TEXT PRIMARY KEY,
            apps INTEGER NOT NULL, starts INTEGER NOT NULL, minutes INTEGER NOT NULL,
            goals INTEGER NOT NULL, assists INTEGER NOT NULL, yellow INTEGER NOT NULL, red INTEGER NOT NULL
        );
        DELETE FROM v18310_season_delta;
'''
HISTORY_SUBTRACT=r'''
        INSERT INTO v18310_season_delta(player_id,apps,starts,minutes,goals,assists,yellow,red)
        SELECT player_id,-SUM(apps),-SUM(starts),-SUM(minutes),-SUM(goals),-SUM(assists),-SUM(yellow),-SUM(red)
        FROM player_season_stats WHERE season=?1 GROUP BY player_id
'''
HISTORY_ADD=r'''
        INSERT INTO v18310_season_delta(player_id,apps,starts,minutes,goals,assists,yellow,red)
        SELECT player_id,SUM(apps),SUM(starts),SUM(minutes),SUM(goals),SUM(assists),SUM(yellow),SUM(red)
        FROM player_season_stats WHERE season=?1 GROUP BY player_id
        ON CONFLICT(player_id) DO UPDATE SET
            apps=apps+excluded.apps,starts=starts+excluded.starts,minutes=minutes+excluded.minutes,
            goals=goals+excluded.goals,assists=assists+excluded.assists,yellow=yellow+excluded.yellow,red=red+excluded.red
'''
HISTORY_APPLY=r'''
        INSERT INTO player_career_totals(player_id,apps,starts,minutes,goals,assists,yellow,red,updated_at)
        SELECT player_id,apps,starts,minutes,goals,assists,yellow,red,unixepoch('now')*1000
        FROM v18310_season_delta WHERE 1
        ON CONFLICT(player_id) DO UPDATE SET
            apps=apps+excluded.apps,starts=starts+excluded.starts,minutes=minutes+excluded.minutes,
            goals=goals+excluded.goals,assists=assists+excluded.assists,yellow=yellow+excluded.yellow,red=red+excluded.red,
            updated_at=excluded.updated_at;
        DELETE FROM player_career_totals
        WHERE player_id IN (SELECT player_id FROM v18310_season_delta)
          AND NOT EXISTS(SELECT 1 FROM player_season_stats s WHERE s.player_id=player_career_totals.player_id);
        DELETE FROM v18310_season_delta;
'''

def patch_native(src):
    commands=['kv_get','kv_put','kv_delete','kv_delete_many','kv_commit_checkpoint','kv_commit_manifest','kv_put_many','history_store_season','history_player_totals','history_player_seasons','history_player_club_seasons','history_competition_ranking','history_database_info','load_player_base']
    for name in commands:
        src=once(src,'#[tauri::command]\nfn '+name+'(', '#[tauri::command(async)]\nfn '+name+'(', 'native nonblocking '+name)
    a,b=section(src,'fn history_store_season(', '#[tauri::command(async)]\nfn history_player_totals(', 'history transaction')
    fn=src[a:b]
    anchor='    let tx = conn.transaction().map_err(|e| e.to_string())?;'
    before='\n    tx.execute_batch(r#"'+HISTORY_BEFORE+'"#).map_err(|e| e.to_string())?;\n    tx.execute(r#"'+HISTORY_SUBTRACT+'"#, params![season]).map_err(|e| e.to_string())?;'
    fn=once(fn,anchor,anchor+before,'snapshot old season totals')
    start=fn.index('    tx.execute("DELETE FROM player_career_totals", [])')
    end=fn.index('    tx.commit()',start)
    replacement='    tx.execute(r#"'+HISTORY_ADD+'"#, params![season]).map_err(|e| e.to_string())?;\n    tx.execute_batch(r#"'+HISTORY_APPLY+'"#).map_err(|e| e.to_string())?;\n\n'
    fn=fn[:start]+replacement+fn[end:]
    return src[:a]+fn+src[b:]

def patch_compatibility(html):
    old="const rows=await read(v93CheckpointKey(meta.token,key,i));"
    new="let rows=await read(v93CheckpointKey(meta.token,key,i));if(key==='players'&&rows?.format===v18191wPlayerFormat)rows=await v18191wDecodePlayerChunk(rows);if(!Array.isArray(rows))throw Error('Bloco do checkpoint indisponivel: '+key);"
    html=once(html,old,new,'resume packed and legacy vacation checkpoints')
    a,b=section(html,'function v94CompactScorerArchive(', 'function v94PackCurrentCareerArchive(', 'scorer archive allocation')
    part=html[a:b]
    part=once(part,'for(const [pid,r] of Object.entries(rows||{})){','for(const pid of Object.keys(rows||{})){const r=rows[pid];','scorer archive row iteration')
    html=html[:a]+part+html[b:]
    a,b=section(html,'function v94PackCurrentCareerArchive(', 'function v95EnsureAcademyTarget(', 'career archive allocation')
    part=html[a:b]
    part=once(part,'for(const [pid,r] of Object.entries(db||{})){','for(const pid of Object.keys(db||{})){const r=db[pid];','career archive row iteration')
    html=html[:a]+part+html[b:]
    return html

def main():
    project=Path(sys.argv[1]).resolve()
    hp=project/'src/index.html';rp=project/'src-tauri/src/lib.rs'
    html=hp.read_text(encoding='utf-8');native=rp.read_text(encoding='utf-8')
    if 'async function v18310PackVacationRows(' in html:raise RuntimeError('18.310 already applied; rebuild from source')
    (project/'baseline-season-18301.html').write_text(html,encoding='utf-8')
    (project/'baseline-native-18301.rs').write_text(native,encoding='utf-8')
    patched=patch_compatibility(patch_html(html));rust=patch_native(native)
    hp.write_text(patched,encoding='utf-8');rp.write_text(rust,encoding='utf-8')
    report={'ok':True,'version':VERSION,'vacationPlayerCodec':'existing lossless packed codec','vacationCheckpointBatchLimit':8,'oneUnacknowledgedUIBatch':True,'legacyCheckpointRead':True,'immutableScorerArchivePreserved':True,'nativeStorageCommandsOffMainThread':14,'historyTotalsIncremental':True,'seasonTotalsTransactionPreserved':True,'historicalDataDeleted':False,'boundedArchiveIteration':True}
    (project/'season-sync-18310-install.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
