from __future__ import annotations
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_scorers_navigation.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "futbr-terminal-scorers-18202" in html:
        print("Scorers navigation 18.202 already patched")
        return
    if "window.v18198ScorersPage=v18198ScorersPage;" not in html:
        fail("renderer final de Artilheiros 18.198 ausente")

    # Depois do encerramento do ano, as estatisticas da temporada podem ja ter
    # sido movidas para scorerArchive enquanto state.year ainda e o mesmo. O
    # renderer antigo consultava somente competitionStats e retornava vazio.
    old_db = "const db=year!==Number(s.year)?((s.scorerArchive||[]).find(x=>Number(x?.year)===year)?.competitions||{}):(s.competitionStats||{});"
    new_db = "const live=s.competitionStats||{},archived=(s.scorerArchive||[]).find(x=>Number(x?.year)===year),liveHasRows=Object.values(live).some(rows=>Object.keys(rows||{}).length);const db=(year!==Number(s.year)||(archived&&(!liveHasRows||!!s.seasonDone)))?(archived?.competitions||{}):live;"
    html = replace_once(html, old_db, new_db, "fonte pos-temporada dos artilheiros")

    terminal = r'''
<script id="futbr-terminal-scorers-18202">
(()=>{
 const G=window.GestorFC=window.GestorFC||{};
 const V18202_SCORER_VIEWS=new Set(['rankings','scorers','topscorers','artilheiros']);
 let v18202Painting=false,v18202Scheduled=false,v18202ForceScheduled=false;

 function v18202Norm(value){
  return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
 }
 function v18202ViewIsScorers(){return V18202_SCORER_VIEWS.has(v18202Norm(typeof view==='undefined'?'':view));}
 function v18202Trigger(node){
  const el=node?.closest?.('button,a,[role="tab"],[data-view],[data-route],[data-action],[data-page],[data-ranking-view]');
  if(!el)return false;
  const attrs=['data-view','data-route','data-action','data-page','data-ranking-view','href'];
  for(const name of attrs){
   const raw=el.getAttribute?.(name);if(!raw)continue;
   const value=v18202Norm(raw).replace(/^#/, '');
   if(V18202_SCORER_VIEWS.has(value)||value.includes('artilheiro')||value.includes('scorer'))return true;
  }
  const text=v18202Norm(el.textContent);
  return text==='artilheiro'||text==='artilheiros'||text.startsWith('artilheiros ');
 }
 function v18202ActiveTabIsScorers(){
  const selectors=[
   '.v677-ranking-tab.active','.v677-ranking-tab[aria-selected="true"]',
   '[role="tab"].active','[role="tab"][aria-selected="true"]',
   '[data-view="rankings"].active','[data-view="rankings"][aria-current="page"]'
  ];
  try{return [...document.querySelectorAll(selectors.join(','))].some(v18202Trigger);}catch(e){return false;}
 }
 function v18202Page(){return document.querySelector('#v555-page');}
 function v18202Mounted(page){
  try{return !!page?.querySelector?.('[data-v18202-scorers-root="1"]');}catch(e){return false;}
 }
 function v18202Hub(){
  const tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';
  const inner=typeof window.v18198ScorersPage==='function'?window.v18198ScorersPage():'<div class="notice error">Artilharia indisponivel.</div>';
  return '<div class="v677-ranking-hub">'+tabs+'<div class="v677-ranking-content"><div class="v615-rankings-shell" data-v18202-scorers-root="1">'+inner+'</div></div></div>';
 }
 function v18202Decorate(page){
  try{v551CleanScreen?.(page);}catch(e){}
  try{v554CleanLegacyCopy?.();}catch(e){}
  try{v548ApplyFeatureLocks?.(page);}catch(e){}
  try{v1882EnhanceCountrySelects?.(page);}catch(e){}
  try{v54ApplyPositionOrder?.();v5MarkSelection?.();v510ApplyTrophyPhotos?.();}catch(e){}
  try{v555ScheduleDecor?.(page);}catch(e){}
 }
 function v18202Paint(force=false){
  if(!state||v18202Painting)return false;
  if(!force&&!v18202ViewIsScorers()&&!v18202ActiveTabIsScorers())return false;
  const page=v18202Page();if(!page)return false;
  v18202Painting=true;
  try{
   view='rankings';
   let content='';
   try{content=v18202Hub();}
   catch(e){console.error('[FutBR] Artilheiros 18.202:',e);content='<div class="v677-ranking-hub">'+(typeof v677RankingTabs==='function'?v677RankingTabs():'')+'<div class="v677-ranking-content"><div class="notice error">Nao foi possivel montar a artilharia desta carreira.</div></div></div>';}
   page.innerHTML=content;page.dataset.v18202Scorers='1';
   v18202Decorate(page);
   const root=document.querySelector('#app');
   try{if(root)v555UpdateChrome?.(root);}catch(e){}
   try{if(root)v677SyncRankingNavigation?.(root);}catch(e){}
   try{v260BodyClasses?.();}catch(e){}
   return true;
  }finally{v18202Painting=false;}
 }
 function v18202Ensure(){
  const wanted=v18202ViewIsScorers()||v18202ActiveTabIsScorers();
  if(!wanted)return false;
  const page=v18202Page();if(!page)return false;
  if(v18202Mounted(page))return true;
  return v18202Paint(true);
 }
 function v18202Schedule(force=false){
  v18202ForceScheduled=v18202ForceScheduled||!!force;
  if(v18202Scheduled)return;
  v18202Scheduled=true;
  const run=()=>{
   const must=v18202ForceScheduled;v18202ForceScheduled=false;v18202Scheduled=false;
   if(must||v18202ViewIsScorers()||v18202ActiveTabIsScorers())v18202Paint(true);
  };
  const next=()=>{if(typeof requestAnimationFrame==='function')requestAnimationFrame(run);else run();};
  if(typeof queueMicrotask==='function')queueMicrotask(next);else setTimeout(next,0);
 }
 window.v18202PaintScorers=v18202Paint;
 window.v18202EnsureScorers=v18202Ensure;

 // O retorno de renderPage fica correto mesmo quando a navegacao nao passa pelo
 // listener das abas do ranking.
 const v18202BaseRenderPage=renderPage;
 renderPage=function(){
  if(v18202ViewIsScorers()){
   view='rankings';
   try{return v18202Hub();}
   catch(e){console.error('[FutBR] render Artilheiros 18.202:',e);return '<div class="notice error">Nao foi possivel montar a artilharia desta carreira.</div>';}
  }
  return v18202BaseRenderPage();
 };

 // Algumas rotas historicas escrevem diretamente em #v555-page e ignoram
 // renderPage. Depois de qualquer renderizacao, confirma fisicamente o quadro.
 if(typeof render==='function'){
  const v18202BaseRender=render;
  render=function(...args){
   const result=v18202BaseRender.apply(this,args);
   v18202Schedule(false);
   return result;
  };
 }

 // Captura tanto a aba atual quanto botoes antigos cujo unico identificador e o
 // texto Artilheiros. Isso cobre menu principal, ranking de clubes, selecoes e
 // tecnicos, inclusive depois da virada de temporada.
 document.addEventListener('click',event=>{
  if(!v18202Trigger(event.target))return;
  event.preventDefault();event.stopImmediatePropagation();
  try{closeModal?.();}catch(e){}
  view='rankings';
  const painted=v18202Paint(true);
  if(!painted){try{render();}catch(e){console.error('[FutBR] navegacao Artilheiros 18.202:',e);}}
  v18202Schedule(true);
  try{window.scrollTo({top:0});}catch(e){}
 },true);

 // Se uma camada tardia recolocar clubes, selecoes ou tecnicos dentro da aba
 // ativa, o observer restaura Artilheiros imediatamente, sem exigir novo clique.
 const v18202Observer=new MutationObserver(()=>{
  if(v18202Painting)return;
  const page=v18202Page();
  if(!page)return;
  if((v18202ViewIsScorers()||v18202ActiveTabIsScorers())&&!v18202Mounted(page))v18202Schedule(true);
 });
 try{v18202Observer.observe(document.documentElement,{subtree:true,childList:true});}catch(e){}
 try{window.addEventListener('popstate',()=>v18202Schedule(false));window.addEventListener('hashchange',()=>v18202Schedule(false));window.addEventListener('pageshow',()=>v18202Schedule(false));}catch(e){}
 setTimeout(()=>v18202Ensure(),0);

 G.scorersNavigation18202={version:'18.202',allNavigationPaths:true,staleContentObserver:true,postSeasonArchiveFallback:true,physicalLastLayer:true};
})();
</script>
'''

    html = html.rstrip() + "\n\n" + terminal + "\n"
    index_path.write_text(html, encoding="utf-8")
    print("Scorers navigation and post-season archive fallback 18.202 applied")


if __name__ == "__main__":
    main()
