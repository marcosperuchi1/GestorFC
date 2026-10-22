from __future__ import annotations
import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def function_bounds(src: str, name: str) -> tuple[int, int]:
    match = re.search(r"function\s+" + re.escape(name) + r"\s*\(", src)
    if not match:
        fail(f"funcao ausente: {name}")
    brace = src.find("{", match.end())
    if brace < 0:
        fail(f"abertura ausente: {name}")
    depth = 0
    quote = None
    escaped = False
    template_depth = 0
    for index in range(brace, len(src)):
        ch = src[index]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif quote == "`" and ch == "$" and index + 1 < len(src) and src[index + 1] == "{":
                template_depth += 1
            elif quote == "`" and ch == "}" and template_depth:
                template_depth -= 1
            elif ch == quote and template_depth == 0:
                quote = None
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return match.start(), index + 1
    fail(f"funcao nao fechada: {name}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_scorers_render_root.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    path = project / "src" / "index.html"
    html = path.read_text(encoding="utf-8")

    if "futbr-scorers-render-root-18211" in html:
        print("Scorers render root 18.211 already installed")
        return
    if "futbr-scorers-root-18210" not in html:
        fail("renderer canonico 18.210 ausente")

    start, end = function_bounds(html, "v555RenderPage")
    original = html[start:end]
    if "page.innerHTML=renderPage()" not in original:
        fail("v555RenderPage original inesperado")

    replacement = r'''function v555RenderPage(root){
 const page=root.querySelector('#v555-page'),notices=root.querySelector('#v555-notices');if(!page||!notices)return;
 const t0=performance.now();notices.innerHTML=v555NoticesHTML();let pageHTML='';
 if(view==='rankings'){
  // A expressao da direita e avaliada antes de innerHTML. Limpar primeiro evita
  // conservar Clubes/Selecoes/Tecnicos se qualquer dado real vier inconsistente.
  page.innerHTML='';page.dataset.v18211Scorers='loading';
  try{
   const factory=window.v18211RankingsHTML;
   pageHTML=typeof factory==='function'?factory():renderPage();
  }catch(error){
   console.error('[FutBR] criacao raiz de Artilheiros 18.211:',error);
   try{pageHTML=typeof window.v18211FallbackHTML==='function'?window.v18211FallbackHTML(error):'<div class="notice error">Nao foi possivel montar a artilharia.</div>';}
   catch(fallbackError){console.error('[FutBR] fallback de Artilheiros:',fallbackError);pageHTML='<div class="notice error">Nao foi possivel montar a artilharia.</div>';}
  }
 }else pageHTML=renderPage();
 page.innerHTML=String(pageHTML||'');delete page.dataset.v18211Scorers;
 v555Perf.pageRenders++;v555Perf.lastPageMs=performance.now()-t0;v551CleanScreen(page);v554CleanLegacyCopy();v548ApplyFeatureLocks(page);v1882EnhanceCountrySelects(page);try{v54ApplyPositionOrder?.();v5MarkSelection?.();v510ApplyTrophyPhotos?.();}catch(e){}v555ScheduleDecor(page);v555LastView=view;
}'''
    html = html[:start] + replacement + html[end:]

    terminal = r'''
<script id="futbr-scorers-render-root-18211">
(()=>{
 const G=window.GestorFC=window.GestorFC||{};
 let cacheState=null,cacheStamp='',cacheRows=[];
 function escSafe(value){const text=String(value??'');try{return typeof esc==='function'?esc(text):text.replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));}catch(e){return text;}}
 function numberSafe(value){const n=Number(value);return Number.isFinite(n)?n:0;}
 function rowEntries(rows){
  if(!rows||typeof rows!=='object')return [];
  const source=rows.players||rows.stats||rows;
  try{if(Array.isArray(source))return source.map((row,index)=>[String(row?.id??row?.playerId??index),row]);}catch(e){}
  try{if(source instanceof Map)return [...source.entries()].map(([id,row])=>[String(id),row]);}catch(e){}
  try{return Object.entries(source);}catch(e){return [];}
 }
 function merge(map,key,raw){
  if(!raw||typeof raw!=='object')return;
  const nested=raw.player&&typeof raw.player==='object'?raw.player:null;
  const id=String(raw.id??raw.playerId??raw.player_id??nested?.id??key??'');if(!id)return;
  let live=null;try{live=state?.players?.[id]||null;}catch(e){}
  const name=String(raw.name??raw.playerName??raw.player_name??nested?.name??live?.name??id);
  const natCode=String(raw.natCode??raw.nationality??nested?.natCode??live?.natCode??'UNK').toUpperCase();
  let row=map.get(id);if(!row){row={id,name,natCode,goals:0,assists:0,apps:0,minutes:0,clubs:{}};map.set(id,row);}
  row.name=name||row.name;row.natCode=natCode||row.natCode;
  row.goals+=numberSafe(raw.goals??raw.goal??raw.g??raw.stats?.goals);
  row.assists+=numberSafe(raw.assists??raw.assist??raw.a??raw.stats?.assists);
  row.apps+=numberSafe(raw.apps??raw.appearances??raw.matches??raw.games??raw.j??raw.stats?.apps);
  row.minutes+=numberSafe(raw.minutes??raw.mins??raw.stats?.minutes);
  try{if(raw.clubs&&typeof raw.clubs==='object')Object.assign(row.clubs,raw.clubs);}catch(e){}
  const clubName=raw.clubName??raw.teamName??raw.club?.name??raw.team?.name;
  if(clubName)row.clubs[String(raw.clubId??raw.teamId??Object.keys(row.clubs).length)]=String(clubName);
 }
 function liveRows(){
  const s=state;if(!s)return [];
  const stamp=[s.year,s.day,s.seasonDone?1:0,s.nextId||0,Object.keys(s.competitionStats||{}).length,(s.scorerArchive||[]).length].join('|');
  if(cacheState===s&&cacheStamp===stamp)return cacheRows;
  const map=new Map();let source=s.competitionStats||{};
  try{
   if(s.seasonDone||!Object.values(source).some(rows=>rowEntries(rows).length)){
    const archived=Array.isArray(s.scorerArchive)?s.scorerArchive.find(item=>Number(item?.year)===Number(s.year)):null;
    if(archived?.competitions)source=archived.competitions;
   }
  }catch(e){}
  try{for(const rows of Object.values(source||{}))for(const [key,raw] of rowEntries(rows))merge(map,key,raw);}catch(e){console.warn('[FutBR] leitura segura de artilheiros:',e);}
  cacheRows=[...map.values()].filter(row=>numberSafe(row.goals)>0).sort((a,b)=>b.goals-a.goals||b.assists-a.assists||a.minutes-b.minutes||String(a.name).localeCompare(String(b.name),'pt-BR'));
  cacheState=s;cacheStamp=stamp;return cacheRows;
 }
 function fallbackContent(error=null){
  const rows=liveRows().slice(0,100);
  const body=rows.map((row,index)=>{
   let club='Livre';try{const names=Object.values(row.clubs||{}).filter(Boolean);if(names.length)club=names[names.length-1];const p=state?.players?.[row.id],t=p?.clubId&&typeof E!=='undefined'&&typeof E.team==='function'?E.team(state,p.clubId):null;if(t?.name)club=t.name;}catch(e){}
   const player=state?.players?.[row.id]?'<button class="table-button player-name" data-action="player" data-player="'+escSafe(row.id)+'">'+escSafe(row.name)+'</button>':'<span class="player-name">'+escSafe(row.name)+'</span>';
   return '<tr><td>'+(index+1)+'</td><td>'+player+'</td><td>'+escSafe(row.natCode)+'</td><td>'+escSafe(club)+'</td><td class="number green strong">'+row.goals+'</td><td class="number">'+row.assists+'</td><td class="number">'+row.apps+'</td><td class="number">'+(row.goals/Math.max(1,row.apps)).toFixed(2)+'</td></tr>';
  }).join('');
  const detail=error&&G?.debugScorersErrors?'<div class="tiny muted mt8">'+escSafe(error?.message||error)+'</div>':'';
  return '<div class="v615-rankings-shell" data-v18211-safe-root="1"><section class="panel"><div class="panel-body"><div class="filters"><div class="field grow"><label>Buscar atleta</label><input id="score-query" placeholder="Nome do jogador" disabled></div><div class="field compact"><label>Temporada</label><strong>'+escSafe(state?.year||'—')+'</strong></div></div>'+detail+'</div><div class="table-scroll v615-ranking-scroll"><table><thead><tr><th>#</th><th>Atleta</th><th>Nacionalidade</th><th>Clube / selecao</th><th class="number">Gols</th><th class="number">Assist.</th><th class="number">J</th><th class="number">Gols/jogo</th></tr></thead><tbody>'+body+'</tbody></table></div>'+(!rows.length?'<div class="empty">Nenhum artilheiro registrado nesta temporada.</div>':'')+'</section></div>';
 }
 function hub(inner){let tabs='';try{tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';}catch(e){}return '<div class="v677-ranking-hub">'+tabs+'<div class="v677-ranking-content">'+inner+'</div></div>';}
 function rankingsHTML(){
  try{
   const rich=typeof window.v18210RankingsPage==='function'?window.v18210RankingsPage():'';
   if(typeof rich==='string'&&rich.includes('data-v18210-scorers-root="1"'))return hub(rich);
  }catch(error){G.scorersRender18211.lastRichError=String(error?.stack||error);console.error('[FutBR] renderer completo de Artilheiros:',error);return hub(fallbackContent(error));}
  return hub(fallbackContent());
 }
 window.v18211FallbackHTML=error=>hub(fallbackContent(error));
 window.v18211RankingsHTML=rankingsHTML;
 G.scorersRender18211={version:'18.211',rootRenderBranch:true,clearsStalePageBeforeEvaluation:true,safeFallback:true,noObserver:true,noClickInterceptor:true,preservesPerformanceArchitecture:true,lastRichError:''};
})();
</script>
'''
    html = html.rstrip() + "\n\n" + terminal + "\n"

    for marker in [
        "futbr-scorers-render-root-18211",
        "clearsStalePageBeforeEvaluation:true",
        "page.dataset.v18211Scorers='loading'",
        "window.v18211RankingsHTML",
    ]:
        if marker not in html:
            fail("marcador 18.211 ausente: " + marker)

    path.write_text(html, encoding="utf-8")
    print("Scorers rendering patched at v555RenderPage root with safe fallback 18.211")


if __name__ == "__main__":
    main()
