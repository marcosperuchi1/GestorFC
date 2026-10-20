from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        fail(f"{label}: esperado 1, encontrado {n}")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: optimize_direct_load.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index = project / "src" / "index.html"
    html = index.read_text(encoding="utf-8")

    if "18.194-direct-sharded-load" in html:
        print("direct sharded load already present")
        return

    loader = r"""
 async function v18194ReadMany(keys){
  if(!keys?.length)return [];
  if(window.FutBRDesktop?.directStorage&&typeof window.FutBRDesktop.readMany==='function'){
   return window.FutBRDesktop.readMany(keys);
  }
  const db=await openDB();
  return new Promise((resolve,reject)=>{
   const out=new Array(keys.length),tx=db.transaction('saves','readonly'),os=tx.objectStore('saves');
   keys.forEach((key,i)=>{
    const q=os.get(key);
    q.onsuccess=()=>{out[i]=q.result;};
    q.onerror=()=>reject(q.error||Error('Falha ao ler bloco do save'));
   });
   tx.oncomplete=()=>resolve(out);
   tx.onerror=()=>reject(tx.error||Error('Falha na leitura em lote do save'));
   tx.onabort=()=>reject(tx.error||Error('Leitura em lote interrompida'));
  });
 }
 async function v18194HydrateManifest(manifest,progress=null,readMany=v18194ReadMany){
  if(manifest?.format!==FORMAT)return null;
  const s={...(manifest.root||{})},entries=Object.entries(manifest.collections||{});
  for(let ci=0;ci<entries.length;ci++){
   const [key,spec]=entries[ci],dst=spec?.isArray?new Array(Number(spec.length)||0):{},keys=spec?.keys||[];
   const stride=key==='players'?8:16;
   for(let i=0;i<keys.length;i+=stride){
    const batchKeys=keys.slice(i,i+stride),chunks=await readMany(batchKeys);
    for(let rows of chunks||[]){
     if(rows==null)continue;
     if(key==='players'&&rows?.format===v18191mPlayerFormat)rows=await v18191mDecodePlayerChunk(rows);
     for(const [id,row] of rows||[]){
      if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;
     }
    }
    try{progress?.({key,done:Math.min(i+stride,keys.length),total:keys.length,collection:ci+1,collections:entries.length});}catch(e){}
    if(i+stride<keys.length)await new Promise(r=>setTimeout(r,0));
   }
   s[key]=dst;
  }
  return s;
 }
 async function v18194LoadShardedDirect(progress=null){
  const manifest=await rawRead(KEY);
  if(manifest?.format!==FORMAT)return null;
  const t0=performance.now(),out=await v18194HydrateManifest(manifest,progress);
  stats.lastLoadMs=Math.round(performance.now()-t0);
  stats.lastLoadHeapMiB=performance.memory?Math.round(performance.memory.usedJSHeapSize/1048576):null;
  return out;
 }
"""

    g_anchor = " G.v171={version:V,freshCareerOnly:true,storageKey:KEY,"
    if g_anchor not in html:
        fail("G.v171 anchor ausente")
    html = html.replace(g_anchor, loader + "\n" + g_anchor, 1)
    html = html.replace(
        "G.v171={version:V,freshCareerOnly:true,storageKey:KEY,playerStorage:",
        "G.v171={version:V,freshCareerOnly:true,storageKey:KEY,loadDirect:v18194LoadShardedDirect,hydrateManifest:v18194HydrateManifest,playerStorage:",
        1,
    )
    html = html.replace(
        "memory:{shardedSnapshots:true,",
        "memory:{shardedSnapshots:true,directIncrementalLoad:true,noWorkerWorldCloneOnLoad:true,",
        1,
    )

    old_load = "  const loaded=await v53Call('load',{key:STORE});"
    new_load = r"""  const v18194Loader=window.GestorFC?.v171?.loadDirect;
  const loaded=typeof v18194Loader==='function'
   ?await v18194Loader(p=>{if(p?.key==='players'&&(p.done===p.total||p.done%24===0))block('Abrindo '+target.name+' · jogadores '+p.done+'/'+p.total+' blocos');})
   :await v53Call('load',{key:STORE});"""
    html = once(html, old_load, new_load, "loadSelected direct loader")

    html = once(
        html,
        "  view=loaded?.v640National?.userTeam?'national':(loaded.seasonDone?'squad':'dashboard');",
        "  view=loaded?.v640National?.userTeam?'national':'squad';",
        "club save landing squad",
    )

    runtime = r"""
<script id="futbr-direct-sharded-load">
window.GestorFC=window.GestorFC||{};
window.GestorFC.directLoadOptimization={
 version:'18.194-direct-sharded-load',
 clubLoadLanding:'squad',
 dashboardSkippedOnLoad:true,
 workerWorldCloneOnLoad:false,
 incrementalManifestHydration:true,
 batchReadTransactions:true
};
</script>
"""
    html = html.replace("</body>", runtime + "\n</body>", 1)

    if "await v53Call('load',{key:STORE});" in html and "typeof v18194Loader==='function'" not in html:
        fail("loadSelected ainda depende apenas do Worker")
    if "noWorkerWorldCloneOnLoad:true" not in html:
        fail("marcador de load sem clone ausente")
    if "view=loaded?.v640National?.userTeam?'national':'squad';" not in html:
        fail("carreira de clube ainda nao abre no elenco")
    if "18.194-direct-sharded-load" not in html:
        fail("runtime marker ausente")

    index.write_text(html, encoding="utf-8")
    print("direct sharded load optimization applied")

if __name__ == "__main__":
    main()
