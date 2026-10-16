from __future__ import annotations
import sys
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def replace_once(text, old, new, label):
    n=text.count(old)
    if n!=1:
        fail(f"{label}: esperado 1, encontrado {n}")
    return text.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: optimize_save_load.py <project-dir>")

    project=Path(sys.argv[1]).resolve()
    index=project/"src"/"index.html"
    html=index.read_text(encoding="utf-8")

    # 1. Sharded saves: bounded parallel reads instead of one IndexedDB request at a time.
    old_decode=""" async function v171DecodeManifest(x){const s={...(x.root||{})};for(const [key,spec] of Object.entries(x.collections||{})){const dst=spec?.isArray?new Array(Number(spec.length)||0):{};for(const chunkKey of spec?.keys||[]){const rows=await read(chunkKey);for(const [id,row] of rows||[]){if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;}}s[key]=dst;}return s;}"""
    new_decode=""" async function v171DecodeManifest(x){
  const s={...(x.root||{})};
  for(const [key,spec] of Object.entries(x.collections||{})){
   const dst=spec?.isArray?new Array(Number(spec.length)||0):{},keys=spec?.keys||[];
   for(let i=0;i<keys.length;i+=8){
    const chunks=await Promise.all(keys.slice(i,i+8).map(k=>read(k)));
    for(const rows of chunks||[])for(const [id,row] of rows||[]){
     if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;
    }
    if(i+8<keys.length)await new Promise(r=>setTimeout(r,0));
   }
   s[key]=dst;
  }
  return s;
 }"""
    html=replace_once(html,old_decode,new_decode,"parallel sharded decode")

    # 2. The player base must not delay the initial menu. Start it only when useful.
    old_enter="""async function v548EnterGame(){await v310StartRosterLoad();renderWelcome();await loadLocal();}"""
    new_enter="""async function v548EnterGame(){v310StartRosterLoad().catch(e=>console.warn('[FutBR] base local em segundo plano:',e?.message||e));renderWelcome();await loadLocal();}"""
    if old_enter in html:
        html=html.replace(old_enter,new_enter,1)

    # Remove eager boot of the large compact roster source. New career/load paths request it.
    eager="""v310StartRosterLoad().catch(e=>console.error('[FutBR] base local de jogadores:',e?.message||e));"""
    html=html.replace(eager,"/* Base compacta carregada sob demanda no desktop. */",1)

    # 3. Named save load: save state + compact player base load in parallel, one click only,
    # force a clean shell, and recover automatically from a blank page.
    start=html.find("async function loadSelected(id){")
    end=html.find("\nasync function doSave(",start)
    if start<0 or end<0:
        fail("loadSelected block not found")

    new_load=r'''async function loadSelected(id){
 if(busy)return;const target=findSlot(id);if(!target)return;
 if(!belongsToAccount(target)){toast('Este save pertence a outra conta.','error');return;}
 busy=true;block('Carregando '+target.name+'...');
 try{
  await ready;
  const rosterPromise=typeof v310StartRosterLoad==='function'
   ?v310StartRosterLoad()
   :Promise.resolve(null);
  const check=target.archived?await get(ARCHIVE+id).catch(()=>null):await get(BASE).catch(()=>null);
  const owner=check?.root?.v548Access?.owner;
  if(owner&&owner!==signedAccount()&&v548Session?.plan!=='author')throw Error('Este save pertence a outra conta.');
  if(v53Sim?.active||v53Sim?.starting||v53Creating)throw Error('Encerre as férias antes de trocar de carreira.');
  await v52FlushSave();if(v52SavePromise)await v52SavePromise;

  if(slots.activeId!==id){
   const active=currentSlot();
   if(active&&!active.archived){
    block('Preservando '+active.name+'...');
    await archiveCurrent((n,t)=>block('Preservando '+active.name+' · '+n+'/'+t));
   }
   block('Restaurando '+target.name+'...');
   await restoreArchive(id,(n,t)=>block('Restaurando '+target.name+' · '+n+'/'+t));
   target.archived=false;
  }

  slots.activeId=id;await writeIndex();
  try{if(v53Worker&&!v53Sim.active){v53Worker.terminate();v53Worker=null;v53WorkerReady=null;}}catch(e){}

  block('Abrindo '+target.name+'...');
  const [loaded]=await Promise.all([
   v53Call('load',{key:STORE}),
   rosterPromise
  ]);
  if(!loaded)throw Error('Nenhuma carreira salva foi encontrada.');
  if(!loaded.players||!loaded.teams||!loaded.schedule||!loaded.competitions)
   throw Error('O save está incompleto. A versão anterior foi preservada; não avance a carreira.');

  if(loaded.vacation){loaded.vacation.active=false;loaded.vacation.paused=true;}
  state=loaded;saved=loaded;
  view=loaded?.v640National?.userTeam?'national':(loaded.seasonDone?'squad':'dashboard');
  if(loaded?.v640National?.userTeam)v640NationalViewCode=loaded.v640National.userTeam;
  compCountry=null;compDivision=null;v52MarketIndex=null;v5RenderedView=null;
  try{v250MarkFreshState?.(state);}catch(e){}

  // Force a fresh persistent shell. This avoids a stale empty page after a long reload.
  try{if(typeof v555ShellState!=='undefined')v555ShellState=null;}catch(e){}
  const app=document.getElementById('app');if(app){delete app.dataset.v555Shell;}
  let firstError=null;
  try{render();}catch(e){firstError=e;console.error('[FutBR] primeiro render do save:',e);}

  await new Promise(resolve=>requestAnimationFrame(()=>resolve()));
  let page=document.querySelector('#v555-page');
  if(!page||!page.innerHTML.trim()){
   // The squad screen is intentionally used as the safest season-end landing page.
   if(!loaded?.v640National?.userTeam)view='squad';
   try{
    if(typeof v555ShellState!=='undefined')v555ShellState=null;
    const root=document.getElementById('app');if(root)delete root.dataset.v555Shell;
    render();
   }catch(e){console.error('[FutBR] render de recuperação:',e);if(firstError)throw firstError;throw e;}
   await new Promise(resolve=>requestAnimationFrame(()=>resolve()));
   page=document.querySelector('#v555-page');
  }
  if(!page||!page.innerHTML.trim())throw Error('A carreira foi carregada, mas a tela não pôde ser montada. Reinicie o jogo e tente novamente.');

  state.futbrSaveId=id;saved=state;copyMeta(state,target);await writeIndex();
  unblock();closeModal();toast('Carreira carregada: '+target.name,'success');
 }catch(e){
  toast(e?.message||String(e),'error');console.error('FutBR save:',e);
 }finally{
  busy=false;unblock();if(!state)listDialog();
 }
}'''
    html=html[:start]+new_load+html[end:]

    runtime=r'''
<script id="futbr-desktop-load-optimization">
window.GestorFC=window.GestorFC||{};
window.GestorFC.desktopLoadOptimization={
 version:'18.162',
 shardReadConcurrency:8,
 playerBase:'lazy-concurrent',
 blankScreenRecovery:true,
 seasonEndLanding:'squad'
};
</script>
'''
    if 'futbr-desktop-load-optimization' not in html:
        html=html.replace("</body>",runtime+"</body>",1)

    # Safety checks.
    if "for(const chunkKey of spec?.keys||[]){const rows=await read(chunkKey)" in html:
        fail("sequential shard decoder still present")
    if eager in html:
        fail("eager player base load still present")
    if "blankScreenRecovery:true" not in html:
        fail("load optimization marker missing")

    index.write_text(html,encoding="utf-8")
    print("save load optimization applied")

if __name__=="__main__":
    main()
