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

    old_quick = "  const loaded=await v53Call('load',{key:STORE});if(!loaded)throw Error('Nenhuma carreira salva foi encontrada.');"
    new_quick = r"""  const v18194Loader=window.GestorFC?.v171?.loadDirect;
  let loaded=typeof v18194Loader==='function'?await v18194Loader():null;
  if(!loaded)loaded=await v53Call('load',{key:STORE});
  if(!loaded)throw Error('Nenhuma carreira salva foi encontrada.');"""
    html = once(html, old_quick, new_quick, "quick continue direct loader")
    html = once(
        html,
        "  state=loaded;saved=loaded;view=loaded?.v640National?.userTeam?'national':'dashboard';",
        "  state=loaded;saved=loaded;view=loaded?.v640National?.userTeam?'national':'squad';",
        "quick continue squad landing",
    )

    boot_old="const localPreload=Promise.resolve().then(()=>loadLocal(false)).catch(e=>{console.warn('[FutBR] leitura local no boot:',e?.message||e);return null;});"
    boot_new="const localPreload=Promise.resolve().then(()=>v260FastLoadLocal(false)).catch(e=>{console.warn('[FutBR] leitura local no boot:',e?.message||e);return null;});"
    html=html.replace(boot_old,boot_new,1)

    load_start=html.find("async function loadSelected(id){")
    load_end=html.find("\nasync function doSave(",load_start)
    if load_start<0 or load_end<0:
        fail("loadSelected ausente")
    segment=html[load_start:load_end]
    old_load = "  const loaded=await v53Call('load',{key:STORE});"
    new_load = r"""  const v18194Loader=window.GestorFC?.v171?.loadDirect;
  let loaded=typeof v18194Loader==='function'
   ?await v18194Loader(p=>{if(p?.key==='players'&&(p.done===p.total||p.done%24===0))block('Abrindo '+target.name+' · jogadores '+p.done+'/'+p.total+' blocos');})
   :null;
  if(!loaded)loaded=await v53Call('load',{key:STORE});"""
    segment = once(segment, old_load, new_load, "loadSelected direct loader")
    segment = once(
        segment,
        "  view=loaded?.v640National?.userTeam?'national':(loaded.seasonDone?'squad':'dashboard');",
        "  view=loaded?.v640National?.userTeam?'national':'squad';",
        "club save landing squad",
    )
    html=html[:load_start]+segment+html[load_end:]

    # Existing saves do not need the 7 MB initial roster source. Defer it until
    # loadLocal confirms there is no saved career to continue.
    auth_prefetch="try{v310StartRosterLoad?.().catch(e=>console.warn('[FutBR] base local no login:',e?.message||e));}catch(e){}"
    html=html.replace(auth_prefetch,"",1)
    enter_old="""async function v548EnterGame(){try{v310StartRosterLoad?.().catch(e=>console.warn('[FutBR] base local em segundo plano:',e?.message||e));}catch(e){}renderWelcome();await loadLocal();}"""
    enter_new="""async function v548EnterGame(){await v260FastLoadLocal(false);renderWelcome();try{if(!v260SavedMeta&&!saved&&!state)v310StartRosterLoad?.().catch(e=>console.warn('[FutBR] base local para nova carreira:',e?.message||e));}catch(e){}}"""
    html=html.replace(enter_old,enter_new,1)

    load_start=html.find("async function loadSelected(id){")
    load_end=html.find("\nasync function doSave(",load_start)
    segment=html[load_start:load_end]
    load_prefetch="  try{if(typeof v310StartRosterLoad==='function')v310StartRosterLoad().catch(e=>console.warn('[FutBR] base local durante load:',e?.message||e));}catch(e){}\n"
    segment=segment.replace(load_prefetch,"",1)
    html=html[:load_start]+segment+html[load_end:]

    runtime = r"""
<style id="futbr-obsolete-dashboard-removal">
body:not(.v128-national-career) [data-action="nav"][data-view="dashboard"]{display:none!important}
</style>
<script id="futbr-direct-sharded-load">
window.GestorFC=window.GestorFC||{};
window.GestorFC.directLoadOptimization={
 version:'18.194-direct-sharded-load',
 clubLoadLanding:'squad',
 dashboardSkippedOnLoad:true,
 dashboardRemovedForClub:true,
 workerWorldCloneOnLoad:false,
 incrementalManifestHydration:true,
 batchReadTransactions:true,
 legacySaveFallback:true,
 initialRosterDeferredOnResume:true,
 loginIndependentFromRoster:true,
 bootIndependentFromRoster:true
};
(()=>{
 const normalize=()=>{try{if(state&&!state?.v640National?.userTeam&&view==='dashboard')view='squad';}catch(e){}};
 document.addEventListener('click',e=>{
  const b=e.target?.closest?.('[data-action="nav"][data-view="dashboard"]');
  if(!b||state?.v640National?.userTeam)return;
  e.preventDefault();e.stopImmediatePropagation();view='squad';closeModal?.();render?.();window.scrollTo({top:0}); 
 },true);
 const baseRender=render;
 render=function(...args){normalize();return baseRender(...args);};
 normalize();
})();
</script>
"""
    html = html.replace("</body>", runtime + "\n</body>", 1)

    if "await v53Call('load',{key:STORE});" in html and "typeof v18194Loader==='function'" not in html:
        fail("loadSelected ainda depende apenas do Worker")
    if "noWorkerWorldCloneOnLoad:true" not in html:
        fail("marcador de load sem clone ausente")
    if html.count("view=loaded?.v640National?.userTeam?'national':'squad';") < 2:
        fail("uma das rotas de continuar carreira ainda nao abre no elenco")
    if "18.194-direct-sharded-load" not in html:
        fail("runtime marker ausente")
    if "dashboardRemovedForClub:true" not in html or "view==='dashboard')view='squad'" not in html:
        fail("dashboard obsoleto ainda pode abrir em carreira de clube")
    if "legacySaveFallback:true" not in html or "if(!loaded)loaded=await v53Call('load',{key:STORE});" not in html:
        fail("fallback para saves antigos ausente")
    if "loginIndependentFromRoster:true" not in html or "async function v548EnterGame(){await v260FastLoadLocal(false);renderWelcome();" not in html:
        fail("login ainda depende da cadeia de loadLocal que toca na base inicial")
    if "bootIndependentFromRoster:true" not in html or "Promise.resolve().then(()=>v260FastLoadLocal(false))" not in html:
        fail("boot ainda depende da cadeia de loadLocal que toca na base inicial")
    if "initialRosterDeferredOnResume:true" not in html or "base local para nova carreira" not in html:
        fail("base inicial ainda e carregada desnecessariamente ao continuar save")

    index.write_text(html, encoding="utf-8")
    print("direct sharded load optimization applied")

if __name__ == "__main__":
    main()
