from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SCORER_SCRIPT_IDS = (
    "futbr-final-integrity-18198",
    "futbr-terminal-scorers-18199",
    "futbr-terminal-scorers-18202",
    "futbr-terminal-scorers-18203",
    "futbr-scorers-root-18210",
    "futbr-scorers-render-root-18211",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def strip_script(html: str, script_id: str) -> tuple[str, int]:
    pattern = re.compile(
        r"\s*<script\b(?=[^>]*\bid=[\"']"
        + re.escape(script_id)
        + r"[\"'])[^>]*>[\s\S]*?</script>\s*",
        re.I,
    )
    return pattern.subn("\n", html)


def function_bounds_all(src: str, name: str) -> list[tuple[int, int]]:
    pattern = re.compile(r"function\s+" + re.escape(name) + r"\s*\(")
    out: list[tuple[int, int]] = []
    for match in pattern.finditer(src):
        brace = src.find("{", match.end())
        if brace < 0:
            continue
        depth = 0
        quote: str | None = None
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
                    out.append((match.start(), index + 1))
                    break
    return out


def last_function(src: str, name: str) -> tuple[int, int]:
    matches = function_bounds_all(src, name)
    if not matches:
        fail(f"funcao ausente no script principal: {name}")
    return matches[-1]


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_scorers_in_scope.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "FUTBR_SCORERS_IN_SCOPE_18220_START" in html:
        print("Artilheiros 18.220 ja esta no escopo original")
        return

    removed: dict[str, int] = {}
    for script_id in SCORER_SCRIPT_IDS:
        html, count = strip_script(html, script_id)
        removed[script_id] = count

    html = re.sub(
        r"\s*/\*\s*scorers-root-compatibility-test-markers:[\s\S]*?\*/\s*",
        "\n",
        html,
        count=1,
    )

    render_positions = function_bounds_all(html, "renderPage")
    if not render_positions:
        fail("renderPage original nao encontrado")
    render_start = render_positions[0][0]
    script_open = html.rfind("<script", 0, render_start)
    script_tag_end = html.find(">", script_open)
    script_close = html.find("</script>", render_start)
    if min(script_open, script_tag_end, script_close) < 0:
        fail("nao foi possivel localizar o bloco principal do jogo")

    script = html[script_tag_end + 1 : script_close]
    rankings_start, rankings_end = last_function(script, "rankingsPage")
    page_start, page_end = last_function(script, "v555RenderPage")

    original_page = script[page_start:page_end]
    assignment = "page.innerHTML=renderPage();"
    if assignment not in original_page:
        fail("v555RenderPage nao possui a atribuicao raiz esperada")

    helper = r'''
/* FUTBR_SCORERS_IN_SCOPE_18220_START */
let v18220ScorerCacheState=null,v18220ScorerCacheKey='',v18220ScorerCacheRows=[];
function v18220Esc(value){
 const text=String(value??'');
 try{return typeof esc==='function'?esc(text):text.replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));}catch(e){return text;}
}
function v18220Norm(value){
 try{return typeof E!=='undefined'&&typeof E.normName==='function'?E.normName(String(value||'')):String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}catch(e){return String(value||'').toLowerCase();}
}
function v18220Number(value){const n=Number(value);return Number.isFinite(n)?n:0;}
function v18220RowsSource(rows){
 if(!rows||typeof rows!=='object')return [];
 const source=rows.players||rows.stats||rows;
 try{if(Array.isArray(source))return source.map((row,index)=>[String(row?.id??row?.playerId??row?.player_id??index),row]);}catch(e){}
 try{if(source instanceof Map)return [...source.entries()].map(([id,row])=>[String(id),row]);}catch(e){}
 try{return Object.entries(source);}catch(e){return [];}
}
function v18220TeamName(s,id){
 if(!id)return '';
 try{const t=typeof E!=='undefined'&&typeof E.team==='function'?E.team(s,id):(s.teams||[]).find(team=>team.id===id);return t?.name||'';}catch(e){return '';}
}
function v18220Merge(map,s,raw,key='',national=false){
 if(!raw||typeof raw!=='object')return;
 const nested=raw.player&&typeof raw.player==='object'?raw.player:null;
 const id=String(raw.id??raw.playerId??raw.player_id??nested?.id??key??'');if(!id)return;
 const live=s.players?.[id];
 const name=String(raw.name??raw.playerName??raw.player_name??nested?.name??live?.name??id);
 const natCode=String(raw.natCode??raw.nationality??nested?.natCode??live?.natCode??'UNK').toUpperCase();
 let row=map.get(id);
 if(!row){row={id,name,natCode,goals:0,assists:0,apps:0,minutes:0,clubs:{},nationalTeams:{}};map.set(id,row);}
 row.name=name||row.name;row.natCode=natCode||row.natCode;
 row.goals+=v18220Number(raw.goals??raw.goal??raw.g??raw.stats?.goals);
 row.assists+=v18220Number(raw.assists??raw.assist??raw.a??raw.stats?.assists);
 row.apps+=v18220Number(raw.apps??raw.appearances??raw.matches??raw.games??raw.j??raw.stats?.apps);
 row.minutes+=v18220Number(raw.minutes??raw.mins??raw.stats?.minutes);
 try{if(raw.clubs&&typeof raw.clubs==='object')Object.assign(row.clubs,raw.clubs);}catch(e){}
 try{if(raw.byClub&&typeof raw.byClub==='object')for(const clubId of Object.keys(raw.byClub)){const label=v18220TeamName(s,clubId);if(label)row.clubs[clubId]=label;}}catch(e){}
 const clubId=raw.clubId??raw.teamId??live?.clubId;
 const clubName=raw.clubName??raw.teamName??raw.club?.name??raw.team?.name??v18220TeamName(s,clubId);
 if(clubName)row.clubs[String(clubId||Object.keys(row.clubs).length)]=String(clubName);
 if(national){const code=String(raw.teamCode??raw.nationalCode??raw.countryCode??'').toUpperCase();if(code)row.nationalTeams[code]=String(raw.teamName??raw.nationalTeamName??code);}
}
function v18220CompetitionAllowed(key,f){
 const parts=String(key||'').split(':'),kind=parts[0]||'',country=parts[1]||'',division=parts[2]||'',wanted=String(f.kind||'all');
 if(wanted==='national'||wanted.startsWith('nat|'))return false;
 if(wanted!=='all'&&wanted!==kind&&wanted!==String(key))return false;
 if(f.country&&f.country!=='all'&&['league','cup'].includes(kind)&&country!==String(f.country))return false;
 if(f.division&&f.division!=='all'&&kind==='league'&&Number(division)!==Number(f.division))return false;
 return true;
}
function v18220Filter(){
 let f;
 try{f=typeof scorerFilter!=='undefined'?scorerFilter:null;}catch(e){f=null;}
 if(!f)f=window.scorerFilter||(window.scorerFilter={});
 f.kind=f.kind||'all';f.country=f.country||'all';f.division=f.division||'all';f.year=f.year??'';f.query=f.query||'';f.nationality=f.nationality||'all';f.page=Math.max(0,Number(f.page)||0);
 return f;
}
function v18220Collect(s,f){
 const cacheKey=[s.year,s.day,s.seasonDone?1:0,f.kind,f.country,f.division,f.year,Object.keys(s.competitionStats||{}).length,(s.scorerArchive||[]).length].join('|');
 if(v18220ScorerCacheState===s&&v18220ScorerCacheKey===cacheKey)return v18220ScorerCacheRows;
 const map=new Map(),year=f.year==='all'?'all':Number(f.year||s.year);
 if(year==='all'){
  for(const [id,raw] of v18220RowsSource(s.allTimeStats||{}))v18220Merge(map,s,raw,id,false);
 }else{
  const archive=(s.scorerArchive||[]).find(item=>Number(item?.year)===year),live=s.competitionStats||{};
  const liveHasRows=Object.values(live).some(rows=>v18220RowsSource(rows).length>0);
  const source=year!==Number(s.year)||(archive&&(!liveHasRows||!!s.seasonDone))?(archive?.competitions||{}):live;
  for(const [competition,rows] of Object.entries(source||{})){
   if(!v18220CompetitionAllowed(competition,f))continue;
   for(const [id,raw] of v18220RowsSource(rows))v18220Merge(map,s,raw,id,false);
  }
 }
 const wanted=String(f.kind||'all');
 if(f.year==='all'||wanted==='all'||wanted==='national'||wanted.startsWith('nat|')){
  const stats=s.v640National?.playerStats||{},years=f.year==='all'?Object.keys(stats):[String(Number(f.year||s.year))];
  for(const y of years)for(const [competition,rows] of Object.entries(stats?.[y]||{})){
   if(wanted.startsWith('nat|')&&wanted!=='nat|'+competition)continue;
   for(const [id,raw] of v18220RowsSource(rows))v18220Merge(map,s,raw,id,true);
  }
 }
 if(![...map.values()].some(row=>row.goals>0)&&year===Number(s.year)&&wanted==='all'){
  let players=[];try{players=typeof v320Players==='function'?v320Players(s):Object.values(s.players||{});}catch(e){players=Object.values(s.players||{});}
  for(const player of players||[])if(v18220Number(player?.goals)>0)v18220Merge(map,s,player,player.id,false);
 }
 v18220ScorerCacheRows=[...map.values()].filter(row=>row.goals>0).sort((a,b)=>b.goals-a.goals||b.assists-a.assists||a.minutes-b.minutes||String(a.name).localeCompare(String(b.name),'pt-BR'));
 v18220ScorerCacheState=s;v18220ScorerCacheKey=cacheKey;return v18220ScorerCacheRows;
}
function v18220NationLabel(code){
 const key=String(code||'UNK').toUpperCase();try{if(typeof NAT!=='undefined'&&NAT?.[key]?.[0])return NAT[key][0];}catch(e){}return key;
}
function v18220NationHTML(code){try{return typeof nation==='function'?nation(code):v18220Esc(v18220NationLabel(code));}catch(e){return v18220Esc(v18220NationLabel(code));}}
function v18220Countries(){try{if(typeof C!=='undefined'&&Array.isArray(C))return C;}catch(e){}try{if(Array.isArray(WorldCatalog?.countries))return WorldCatalog.countries;}catch(e){}return [];}
function v18220Option(value,label,current){return '<option value="'+v18220Esc(value)+'" '+(String(current)===String(value)?'selected':'')+'>'+v18220Esc(label)+'</option>';}
function v18220ClubHTML(s,row,kind){
 const nationalOnly=kind==='national'||String(kind||'').startsWith('nat|'),national=Object.entries(row.nationalTeams||{});
 if(nationalOnly)return national.length?national.map(([code,name])=>'<span class="pill">'+(typeof v640Flag==='function'?v640Flag(code):'')+' '+v18220Esc(name)+'</span>').join(' '):'<span class="muted">Selecao</span>';
 const live=s.players?.[row.id],clubName=v18220TeamName(s,live?.clubId);
 if(clubName){const team=(s.teams||[]).find(item=>item.id===live?.clubId);try{return '<div class="v538-scorer-club">'+(team&&typeof badge==='function'?badge(team,'small'):'')+(team&&typeof teamButton==='function'?teamButton(team):'<strong>'+v18220Esc(clubName)+'</strong>')+'</div>';}catch(e){return '<strong>'+v18220Esc(clubName)+'</strong>';}}
 const names=Object.values(row.clubs||{}).filter(Boolean);return names.length?v18220Esc(names[names.length-1]):'Livre';
}
function v18220ScorersContent(s=state,f=v18220Filter()){
 if(!s)return '<section class="panel"><div class="empty">Nenhuma carreira carregada.</div></section>';
 const ranked=v18220Collect(s,f),wantedNat=String(f.nationality||'all').toUpperCase(),query=v18220Norm(f.query||'');
 const rows=ranked.filter(row=>(wantedNat==='ALL'||row.natCode===wantedNat)&&(!query||v18220Norm(row.name).includes(query))),rank=new Map(ranked.map((row,index)=>[row.id,index+1]));
 const years=[...new Set([Number(s.year),...(s.scorerArchive||[]).map(item=>Number(item?.year)),...Object.keys(s.v640National?.playerStats||{}).map(Number)])].filter(Number.isFinite).sort((a,b)=>b-a);
 const natCodes=[...new Set(ranked.map(row=>row.natCode))].sort((a,b)=>v18220NationLabel(a).localeCompare(v18220NationLabel(b),'pt-BR'));
 const competitionOptions={all:'Todas / global',league:'Ligas nacionais',cup:'Copas nacionais',national:'Selecoes - todas'};
 for(const competition of Object.values(s.competitions||{}))if(competition?.id)competitionOptions[competition.id]=competition.name||competition.id;
 const pageSize=50,pages=Math.max(1,Math.ceil(rows.length/pageSize));f.page=Math.min(f.page,pages-1);const start=f.page*pageSize,end=Math.min(start+pageSize,rows.length),visible=rows.slice(start,end);
 const nationalOnly=f.kind==='national'||String(f.kind).startsWith('nat|'),disableClub=f.year==='all'||nationalOnly;
 const body=visible.map(row=>{const clickable=!!s.players?.[row.id],player=clickable?'<button class="table-button player-name" data-action="player" data-player="'+v18220Esc(row.id)+'">'+v18220Esc(row.name)+'</button>':'<span class="player-name">'+v18220Esc(row.name)+'</span>';return '<tr><td>'+(rank.get(row.id)||'—')+'</td><td>'+player+'</td><td>'+v18220NationHTML(row.natCode)+'</td><td class="club-history">'+v18220ClubHTML(s,row,f.year==='all'?'all':f.kind)+'</td><td class="number green strong">'+row.goals+'</td><td class="number">'+row.assists+'</td><td class="number">'+row.apps+'</td><td class="number">'+(row.goals/Math.max(1,row.apps)).toFixed(2)+'</td></tr>';}).join('');
 return '<section class="panel" data-v18220-scorers-root="1"><div class="panel-head"><div><h3>Ranking de Artilheiros</h3><span class="tiny muted">Estatisticas da temporada, copas e selecoes</span></div></div><div class="panel-body"><div class="filters">'+
  '<div class="field grow"><label for="score-query">Buscar atleta</label><input id="score-query" data-v641-score-query value="'+v18220Esc(f.query)+'" placeholder="Nome do jogador"></div>'+
  '<div class="field compact"><label for="score-kind">Competicao</label><select id="score-kind" data-v3="score-kind">'+Object.entries(competitionOptions).map(([value,label])=>v18220Option(value,label,f.kind)).join('')+'</select></div>'+
  '<div class="field compact"><label for="score-country">Pais</label><select id="score-country" data-v3="score-country" '+(disableClub?'disabled':'')+'><option value="all">Todos</option>'+v18220Countries().map(country=>v18220Option(country.id,country.name,f.country)).join('')+'</select></div>'+
  '<div class="field compact"><label for="score-div">Divisao</label><select id="score-div" data-v3="score-division" '+(disableClub||f.kind==='cup'?'disabled':'')+'>'+[['all','Todas'],['1','1a divisao'],['2','2a divisao'],['3','3a divisao'],['4','4a divisao']].map(([value,label])=>v18220Option(value,label,f.division)).join('')+'</select></div>'+
  '<div class="field compact"><label for="score-nationality">Nacionalidade</label><select id="score-nationality" data-v3="score-nationality"><option value="all">Todas</option>'+natCodes.map(code=>v18220Option(code,v18220NationLabel(code),wantedNat)).join('')+'</select></div>'+
  '<div class="field compact"><label for="score-year">Temporada</label><select id="score-year" data-v3="score-year">'+years.map(year=>v18220Option(year,year,Number(f.year||s.year))).join('')+v18220Option('all','Carreira global',f.year)+'</select></div></div></div>'+
  '<div class="table-scroll v615-ranking-scroll"><table><thead><tr><th>#</th><th>Atleta</th><th>Nacionalidade</th><th>Clube / selecao</th><th class="number">Gols</th><th class="number">Assist.</th><th class="number">J</th><th class="number">Gols/jogo</th></tr></thead><tbody>'+body+'</tbody></table></div>'+
  (!rows.length?'<div class="empty">Nenhum artilheiro registrado neste recorte.</div>':'<div class="pagination v615-ranking-pagination"><span class="tiny muted">Pagina '+(f.page+1)+' de '+pages+' · '+(start+1)+'-'+end+' de '+rows.length+' artilheiros</span><div class="flex"><button class="btn small" data-action="score-prev" '+(start?'':'disabled')+'>Anterior</button><button class="btn small" data-action="score-next" '+(end<rows.length?'':'disabled')+'>Proxima</button></div></div>')+'</section>';
}
function v18220RankingsPage(s=state,f=v18220Filter()){
 let tabs='';try{tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';}catch(e){}
 return '<div class="v677-ranking-hub" data-v18220-rankings-page="1">'+tabs+'<div class="v677-ranking-content"><div class="v615-rankings-shell">'+v18220ScorersContent(s,f)+'</div></div></div>';
}
try{window.GestorFC=window.GestorFC||{};window.GestorFC.scorersInScope18220={version:'18.220',sameEngineScope:true,renderWith:(s,f)=>v18220RankingsPage(s,f),collectWith:(s,f)=>v18220Collect(s,f)};}catch(e){}
/* FUTBR_SCORERS_IN_SCOPE_18220_END */
'''

    rankings_replacement = "function rankingsPage(){return v18220RankingsPage();}"
    page_replacement = original_page.replace(
        assignment,
        "let v18220PageHTML='';if(view==='rankings'){try{v18220PageHTML=v18220RankingsPage();}catch(error){console.error('[FutBR] Artilheiros no escopo original:',error);v18220PageHTML='<div class=\"v677-ranking-content\"><section class=\"panel\"><div class=\"empty\">Nao foi possivel montar a artilharia.</div></section></div>';}}else v18220PageHTML=renderPage();page.innerHTML=v18220PageHTML;",
        1,
    )

    replacements = [
        (page_start, page_end, page_replacement),
        (rankings_start, rankings_end, rankings_replacement),
    ]
    for start, end, replacement in sorted(replacements, reverse=True):
        script = script[:start] + replacement + script[end:]

    insert_at = script.find("function rankingsPage")
    if insert_at < 0:
        fail("rankingsPage substituida nao foi localizada")
    script = script[:insert_at] + helper + "\n" + script[insert_at:]
    html = html[: script_tag_end + 1] + script + html[script_close:]

    if html.count("FUTBR_SCORERS_IN_SCOPE_18220_START") != 1:
        fail("bloco 18.220 nao foi inserido uma unica vez")
    if "page.innerHTML=v18220PageHTML" not in html:
        fail("v555RenderPage nao foi conectado ao renderer 18.220")
    for script_id in SCORER_SCRIPT_IDS:
        if f'id="{script_id}"' in html or f"id='{script_id}'" in html:
            fail(f"camada externa antiga ainda presente: {script_id}")

    report = {
        "ok": True,
        "sameScriptScope": True,
        "removedExternalScripts": removed,
        "scriptOpen": script_open,
        "scriptClose": script_close,
        "helperPosition": html.find("FUTBR_SCORERS_IN_SCOPE_18220_START"),
        "rankingsFunction": True,
        "rootWriter": True,
    }
    (project / "scorers-in-scope-install.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    index_path.write_text(html, encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
