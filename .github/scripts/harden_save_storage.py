from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: esperado 1, encontrado {n}")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: harden_save_storage.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index = project / "src" / "index.html"
    html = index.read_text(encoding="utf-8")

    start = html.find(" async function writeCollection(token,key,value,limit){")
    end = html.find(" async function saveSharded", start)
    if start < 0 or end < 0:
        fail("Bloco writeCollection/saveSharded nao encontrado")

    hardened = r''' async function writeCollection(token,key,value,limit){
  const isArray=Array.isArray(value),keys=[];let rows=[],idx=0,writes=0;
  const finishWrite=async(ck,batch)=>{
   await dbWrite(ck,batch);keys.push(ck);
   if(key==='players')stats.playerChunksWritten++;
   writes++;
   if(v18121NewSeasonPreparation&&(key!=='players'||writes===1||writes%10===0)){
    v53Sim.progress=key==='players'?'Salvando jogadores · bloco '+writes:'Salvando '+key+' da nova temporada';
    try{v53PaintStatus();}catch(e){}
   }
   if(writes%6===0)await new Promise(r=>setTimeout(r,0));
  };
  const jsonSafe=batch=>{
   try{return JSON.parse(JSON.stringify(batch,(k,v)=>{
    if(typeof v==='function'||typeof v==='symbol')return undefined;
    if(typeof v==='number'&&!Number.isFinite(v))return null;
    return v;
   }));}catch(e){return null;}
  };
  const writeBatch=async batch=>{
   if(!batch.length)return;
   const ck=shardKey(token,key,idx);
   try{
    await finishWrite(ck,batch);idx++;return;
   }catch(e){
    const name=String(e?.name||'');
    if(batch.length>120&&(key==='players'||name==='DataCloneError'||name==='QuotaExceededError'||name==='UnknownError')){
     const mid=Math.ceil(batch.length/2);
     await writeBatch(batch.slice(0,mid));
     await writeBatch(batch.slice(mid));
     return;
    }
    if(name==='DataCloneError'){
     const safe=jsonSafe(batch);
     if(safe){
      try{await finishWrite(ck,safe);idx++;return;}catch(e2){e=e2;}
     }
    }
    const first=Array.isArray(batch[0])?batch[0][0]:null;
    const prefix=key==='players'?'Falha ao gravar a base de jogadores':'Falha ao gravar '+key;
    throw Error(prefix+(first?' a partir de '+first:'')+': '+(e?.message||e));
   }
  };
  const flush=async()=>{
   if(!rows.length)return;
   const batch=rows;rows=[];
   await writeBatch(batch);
  };
  for(const id in (value||{})){
   rows.push([id,value[id]]);
   if(rows.length>=limit)await flush();
  }
  await flush();
  return {isArray,length:isArray?value.length:0,keys};
 }
'''
    html = html[:start] + hardened + html[end:]

    old_head = "async function saveSharded(s,mode='full'){if(!s)return null;const t0=performance.now(),old=await rawRead(KEY),oldPrev=await rawRead(KEY+':previous'),token=[s.year,s.day,Date.now(),Math.random().toString(36).slice(2,7)].join('-'),set=new Set(SHARDS),root={};for(const [k,v] of Object.entries(s))if(!set.has(k))root[k]=v;const collections={};"
    new_head = """async function saveSharded(s,mode='full'){if(!s)return null;const t0=performance.now(),old=await rawRead(KEY),oldPrev=await rawRead(KEY+':previous'),token=[s.year,s.day,Date.now(),Math.random().toString(36).slice(2,7)].join('-'),set=new Set(SHARDS),root={};for(const [k,v] of Object.entries(s))if(!set.has(k))root[k]=v;const collections={};
  // Libera a geracao mais antiga ANTES de escrever uma nova copia completa.
  // O checkpoint atual continua intacto ate o commit final, portanto uma falha
  // de gravacao nunca apaga a carreira valida que o usuario ja possuia.
  if(oldPrev?.format===FORMAT){
   try{
    await cleanupManifest(oldPrev,keysOf(old));
    await rawDelete(KEY+':previous');
   }catch(e){console.warn('[18.161] pre-limpeza de save antigo:',e?.message||e);}
  }"""
    html = replace_once(html, old_head, new_head, "pre-clean old previous snapshot")

    html = replace_once(
        html,
        "const limit=key==='players'?2400:key==='teams'?420:key==='coaches'?520:key==='schedule'?4:key==='competitionStats'?4:key==='allTimeStats'?700:120;",
        "const limit=key==='players'?1000:key==='teams'?420:key==='coaches'?520:key==='schedule'?4:key==='competitionStats'?4:key==='allTimeStats'?700:120;",
        "smaller player save chunks"
    )

    marker = "</body>"
    runtime = r'''
<script id="futbr-desktop-save-hardening">
(()=>{
 try{navigator.storage?.persist?.().catch(()=>{});}catch(_){}
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.desktopSaveHardening={
  version:'18.161',
  playerChunkSize:1000,
  preCleanupPrevious:true,
  adaptiveShardRetry:true,
  immutableCareerState:true
 };
})();
</script>
'''
    if 'futbr-desktop-save-hardening' not in html:
        if marker not in html:
            fail("body close not found")
        html = html.replace(marker, runtime + marker, 1)

    if "key==='players'?2400" in html:
        fail("player chunk size antigo ainda existe")
    if "pre-limpeza de save antigo" not in html:
        fail("pre-clean patch missing")
    if "adaptiveShardRetry:true" not in html:
        fail("runtime marker missing")

    index.write_text(html, encoding="utf-8")
    print("save hardening applied")

if __name__ == "__main__":
    main()
