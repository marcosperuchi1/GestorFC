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
        raise SystemExit("usage: fix_scorers_live_runtime.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "futbr-terminal-scorers-18203" in html:
        print("Live scorers 18.203 already patched")
        return
    if "futbr-terminal-scorers-18202" not in html:
        fail("camada 18.202 de Artilheiros ausente")

    # A tela vazia nao executava estes acessos. Assim que a primeira rodada
    # criava jogadores no ranking, NAT/C e o formato das linhas passavam a ser
    # avaliados e uma excecao podia conservar a tela anterior.
    html = replace_once(
        html,
        "(NAT?.[a]?.[0]||a).localeCompare(NAT?.[b]?.[0]||b,'pt-BR')",
        "((typeof NAT!=='undefined'&&NAT?.[a]?.[0])||a).localeCompare((typeof NAT!=='undefined'&&NAT?.[b]?.[0])||b,'pt-BR')",
        "ordenacao segura de nacionalidades",
    )
    html = replace_once(
        html,
        "v18198Option(code,NAT?.[code]?.[0]||code,wantNat)",
        "v18198Option(code,(typeof NAT!=='undefined'&&NAT?.[code]?.[0])||code,wantNat)",
        "rotulo seguro de nacionalidade",
    )
    html = replace_once(
        html,
        "((Array.isArray(C)?C:[]).map(c=>v18198Option(c.id,c.name,f.country)).join(''))",
        "(((typeof C!=='undefined'&&Array.isArray(C))?C:[]).map(c=>v18198Option(c.id,c.name,f.country)).join(''))",
        "lista segura de paises",
    )
    html = replace_once(
        html,
        "for(const r of Object.values(rows||{}))v18198Merge(map,r,false);",
        "{const source=rows?.players||rows?.stats||rows||{};for(const [rid,raw] of Object.entries(source)){const r=raw&&typeof raw==='object'?(raw.id?raw:{...raw,id:raw.playerId||raw.player_id||rid}):null;if(r)v18198Merge(map,r,false);}}",
        "linhas ao vivo de clubes",
    )
    html = replace_once(
        html,
        "for(const r of Object.values(rows||{}))v18198Merge(map,r,true);",
        "{const source=rows?.players||rows?.stats||rows||{};for(const [rid,raw] of Object.entries(source)){const r=raw&&typeof raw==='object'?(raw.id?raw:{...raw,id:raw.playerId||raw.player_id||rid}):null;if(r)v18198Merge(map,r,true);}}",
        "linhas ao vivo de selecoes",
    )

    terminal = r'''
<script id="futbr-terminal-scorers-18203">
(()=>{
 const G=window.GestorFC=window.GestorFC||{};
 const V18203_SCORERS=new Set(['rankings','ranking','scorers','topscorers','artilheiros','artilheiro']);
 const V18203_OTHER=new Set(['clubrankings','clubs','clubes','nationalrankings','nations','selecoes','coaches','tecnicos','coachrankings']);
 let v18203Intent=false,v18203Painting=false,v18203Scheduled=false;
 const v18203BaseScorers=typeof window.v18198ScorersPage==='function'?window.v18198ScorersPage:null;

 function v18203Norm(value){
  return String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
 }
 function v18203Esc(value){
  try{return typeof esc==='function'?esc(String(value??'')):String(value??'').replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));}
  catch(e){return String(value??'');}
 }
 function v18203Elements(eventOrNode){
  const out=[];const add=node=>{if(node&&node.nodeType!==3&&!out.includes(node))out.push(node);};
  try{for(const node of eventOrNode?.composedPath?.()||[])add(node);}catch(e){}
  let node=eventOrNode?.target||eventOrNode;
  for(let i=0;node&&i<12;i++,node=node.parentElement||node.parentNode)add(node);
  return out;
 }
 function v18203Classify(eventOrNode){
  let sawRankingMenu=false;
  for(const el of v18203Elements(eventOrNode)){
   if(!el?.getAttribute)continue;
   const attrs=['data-view','data-route','data-page','data-ranking-view','data-ranking-tab','href','id'];
   for(const name of attrs){
    const raw=el.getAttribute(name);if(!raw)continue;
    const value=v18203Norm(raw).replace(/^#/, '');
    if(V18203_SCORERS.has(value)||value.includes('artilheiro')||value.includes('scorer'))return 'scorers';
    if(V18203_OTHER.has(value))return 'other';
   }
   const action=v18203Norm(el.getAttribute('data-action'));
   const text=v18203Norm(el.textContent);
   if(text==='artilheiros'||text==='artilheiro'||text.startsWith('artilheiros '))return 'scorers';
   if(text==='ranking'||text==='rankings'||text==='ranking geral')sawRankingMenu=true;
   if((action==='nav'||action==='navigate'||action==='ranking')&&(text==='ranking'||text==='rankings'))sawRankingMenu=true;
   if(['clubes','selecoes','tecnicos'].includes(text))return 'other';
  }
  return sawRankingMenu?'scorers':null;
 }
 function v18203CurrentIsScorers(){
  const value=v18203Norm(typeof view==='undefined'?'':view);
  return v18203Intent||V18203_SCORERS.has(value);
 }
 function v18203Page(){return document.querySelector('#v555-page');}
 function v18203Mounted(page){
  try{return !!page?.querySelector?.('[data-v18203-scorers-root="1"]');}catch(e){return false;}
 }
 function v18203Number(value){const n=Number(value);return Number.isFinite(n)?n:0;}
 function v18203CollectRows(){
  const s=state;if(!s)return [];
  const f=(typeof scorerFilter!=='undefined'&&scorerFilter)||{};
  const selected=f.year==='all'?'all':Number(f.year||s.year);
  const map=new Map(),seen=new WeakSet();
  const merge=(raw,key='')=>{
   if(!raw||typeof raw!=='object')return;
   const goals=v18203Number(raw.goals??raw.goal??raw.g??raw.stats?.goals);
   const assists=v18203Number(raw.assists??raw.assist??raw.a??raw.stats?.assists);
   const apps=v18203Number(raw.apps??raw.appearances??raw.matches??raw.games??raw.j??raw.stats?.apps);
   const minutes=v18203Number(raw.minutes??raw.mins??raw.stats?.minutes);
   if(!goals&&!assists&&!apps&&!minutes)return;
   const player=raw.player&&typeof raw.player==='object'?raw.player:null;
   const rawId=raw.id??raw.playerId??raw.player_id??player?.id??key;
   const id=String(rawId||'');
   const live=id?s.players?.[id]:null;
   const rawName=raw.name??raw.playerName??raw.player_name??player?.name??live?.name??id;
   const name=rawName||'Atleta';
   const natCode=raw.natCode??raw.nationality??player?.natCode??live?.natCode??'UNK';
   const mapKey=id||(v18203Norm(name)+'|'+natCode);
   let row=map.get(mapKey);
   if(!row){row={id,name,natCode,goals:0,assists:0,apps:0,minutes:0,clubs:{}};map.set(mapKey,row);}
   row.goals+=goals;row.assists+=assists;row.apps+=apps;row.minutes+=minutes;
   if(raw.clubs&&typeof raw.clubs==='object')Object.assign(row.clubs,raw.clubs);
   const clubName=raw.teamName??raw.clubName??raw.team?.name??raw.club?.name;
   if(clubName)row.clubs[String(raw.teamId??raw.clubId??Object.keys(row.clubs).length)]=clubName;
  };
  const walk=(node,key='',depth=0)=>{
   if(node==null||depth>6||typeof node!=='object')return;
   if(seen.has(node))return;seen.add(node);
   if(Array.isArray(node)){for(const item of node)walk(item,'',depth+1);return;}
   if(node instanceof Map){for(const [k,v] of node.entries())walk(v,String(k),depth+1);return;}
   const looks=('goals' in node)||('goal' in node)||('assists' in node)||('apps' in node)||('appearances' in node)||('matches' in node)||('minutes' in node)||('stats' in node);
   if(looks){merge(node,key);return;}
   for(const [k,v] of Object.entries(node))walk(v,k,depth+1);
  };
  const archives=Array.isArray(s.scorerArchive)?s.scorerArchive:[];
  if(selected==='all'){
   walk(s.allTimeStats||{});
   if(!map.size){for(const archive of archives)walk(archive?.competitions||archive);walk(s.competitionStats||{});}
  }else{
   const archived=archives.find(item=>Number(item?.year)===selected);
   const live=s.competitionStats||{};
   const liveRows=Object.values(live).some(value=>value&&typeof value==='object'&&Object.keys(value).length);
   if(selected!==Number(s.year)||(archived&&(!liveRows||s.seasonDone)))walk(archived?.competitions||archived||{});
   else walk(live);
  }
  try{
   const national=s.v640National?.playerStats;
   if(national){if(selected==='all')walk(national);else walk(national?.[String(selected)]||national?.[selected]||{});}
  }catch(e){}
  return [...map.values()].filter(row=>row.goals>0).sort((a,b)=>b.goals-a.goals||b.assists-a.assists||a.minutes-b.minutes||String(a.name).localeCompare(String(b.name),'pt-BR'));
 }
 function v18203Fallback(){
  const rows=v18203CollectRows(),body=rows.slice(0,100).map((row,index)=>{
   let club='Livre';const clubs=Object.values(row.clubs||{}).filter(Boolean);if(clubs.length)club=clubs.at(-1);
   const avg=(row.goals/Math.max(1,row.apps)).toFixed(2);
   const player=row.id&&state?.players?.[row.id]?'<button class="table-button player-name" data-action="player" data-player="'+v18203Esc(row.id)+'">'+v18203Esc(row.name)+'</button>':v18203Esc(row.name);
   return '<tr><td>'+(index+1)+'</td><td>'+player+'</td><td>'+v18203Esc(row.natCode)+'</td><td>'+v18203Esc(club)+'</td><td class="number green strong">'+row.goals+'</td><td class="number">'+row.assists+'</td><td class="number">'+row.apps+'</td><td class="number">'+avg+'</td></tr>';
  }).join('');
  return '<section class="panel"><div class="panel-body"><div class="filters"><div class="field grow"><label>Buscar atleta</label><input data-v18203-live-search placeholder="Nome do jogador"></div><div class="field compact"><label>Temporada</label><strong>'+(state?.year||'—')+'</strong></div></div></div><div class="table-scroll v615-ranking-scroll"><table><thead><tr><th>#</th><th>Atleta</th><th>Nacionalidade</th><th>Clube / selecao</th><th class="number">Gols</th><th class="number">Assist.</th><th class="number">J</th><th class="number">Gols/jogo</th></tr></thead><tbody>'+body+'</tbody></table></div>'+(!rows.length?'<div class="empty">Nenhum artilheiro registrado neste recorte.</div>':'')+'</section>';
 }
 function v18203Scorers(){
  let html='';
  try{html=v18203BaseScorers?v18203BaseScorers():'';}catch(e){G.scorersNavigation18203.lastRendererError=String(e?.stack||e);console.error('[FutBR] renderer de Artilheiros ao vivo:',e);}
  const rows=v18203CollectRows();
  const valid=typeof html==='string'&&(html.includes('score-query')||html.includes('Buscar atleta'));
  const hasKnownRow=!rows.length||rows.slice(0,5).some(row=>html.includes(v18203Esc(row.name)));
  return valid&&hasKnownRow?html:v18203Fallback();
 }
 window.v18198ScorersPage=v18203Scorers;
 function v18203Hub(){
  const tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';
  return '<div class="v677-ranking-hub">'+tabs+'<div class="v677-ranking-content"><div class="v615-rankings-shell" data-v18202-scorers-root="1" data-v18203-scorers-root="1">'+v18203Scorers()+'</div></div></div>';
 }
 function v18203Loading(){
  const page=v18203Page();if(page){page.innerHTML='<div class="v677-ranking-content"><div class="panel"><div class="panel-body">Carregando artilheiros...</div></div></div>';page.dataset.v18203Scorers='loading';}
 }
 function v18203Decorate(page){
  try{v551CleanScreen?.(page);}catch(e){}try{v554CleanLegacyCopy?.();}catch(e){}try{v548ApplyFeatureLocks?.(page);}catch(e){}
  try{v1882EnhanceCountrySelects?.(page);}catch(e){}try{v54ApplyPositionOrder?.();v5MarkSelection?.();v510ApplyTrophyPhotos?.();}catch(e){}try{v555ScheduleDecor?.(page);}catch(e){}
 }
 function v18203Paint(force=false){
  if(!state||v18203Painting)return false;if(!force&&!v18203CurrentIsScorers())return false;
  const page=v18203Page();if(!page)return false;v18203Painting=true;v18203Intent=true;
  try{view='rankings';page.innerHTML=v18203Hub();page.dataset.v18203Scorers='1';v18203Decorate(page);const root=document.querySelector('#app');try{if(root)v555UpdateChrome?.(root);}catch(e){}try{if(root)v677SyncRankingNavigation?.(root);}catch(e){}try{v260BodyClasses?.();}catch(e){}return true;}
  catch(e){G.scorersNavigation18203.lastPaintError=String(e?.stack||e);console.error('[FutBR] pintura Artilheiros 18.203:',e);page.innerHTML='<div class="notice error">Nao foi possivel montar a artilharia. '+v18203Esc(e?.message||e)+'</div>';return false;}
  finally{v18203Painting=false;}
 }
 function v18203Schedule(force=false){
  if(v18203Scheduled)return;v18203Scheduled=true;
  const run=()=>{v18203Scheduled=false;if(force||v18203CurrentIsScorers())v18203Paint(true);};
  if(typeof queueMicrotask==='function')queueMicrotask(()=>typeof requestAnimationFrame==='function'?requestAnimationFrame(run):run());else setTimeout(run,0);
 }
 window.v18203PaintScorers=v18203Paint;
 const v18203BaseRenderPage=renderPage;
 renderPage=function(){if(v18203CurrentIsScorers()){view='rankings';v18203Intent=true;return v18203Hub();}return v18203BaseRenderPage();};
 if(typeof render==='function'){
  const v18203BaseRender=render;
  render=function(...args){const result=v18203BaseRender.apply(this,args);if(v18203CurrentIsScorers())v18203Schedule(true);return result;};
 }
 function v18203Capture(event){
  const route=v18203Classify(event);
  if(route==='other'){v18203Intent=false;return;}
  if(route!=='scorers')return;
  event.preventDefault?.();event.stopImmediatePropagation?.();v18203Intent=true;view='rankings';v18203Loading();
  v18203Paint(true);v18203Schedule(true);
  try{window.scrollTo({top:0});}catch(e){}
 }
 try{window.addEventListener('pointerdown',event=>{if(v18203Classify(event)==='scorers'){v18203Intent=true;view='rankings';}},true);window.addEventListener('click',v18203Capture,true);}catch(e){document.addEventListener('click',v18203Capture,true);}
 const observer=new MutationObserver(()=>{if(v18203Painting||!v18203CurrentIsScorers())return;const page=v18203Page();if(page&&!v18203Mounted(page))v18203Schedule(true);});
 try{observer.observe(document.documentElement,{subtree:true,childList:true});}catch(e){}
 setTimeout(()=>{if(v18203CurrentIsScorers())v18203Paint(true);},0);
 G.scorersNavigation18203={version:'18.203',liveSeason:true,windowCapture:true,ancestorPathRouting:true,safeNationalityLookup:true,defensiveLiveRows:true,staleContentGuard:true};
})();
</script>
'''

    html = html.rstrip() + "\n\n" + terminal + "\n"
    index_path.write_text(html, encoding="utf-8")
    print("Live-season scorers navigation 18.203 applied")


if __name__ == "__main__":
    main()
