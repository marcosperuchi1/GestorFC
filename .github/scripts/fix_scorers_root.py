from __future__ import annotations
import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def strip_script(html: str, script_id: str) -> tuple[str, int]:
    pattern = re.compile(
        r"(?:\\n|\s)*<script\b(?=[^>]*\bid=[\"']"
        + re.escape(script_id)
        + r"[\"'])[^>]*>[\s\S]*?</script>(?:\\n|\s)*",
        re.I,
    )
    return pattern.subn("\n", html)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_scorers_root.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    if "futbr-scorers-root-18210" in html:
        print("Canonical scorers root 18.210 already installed")
        return

    removed = {}
    for script_id in (
        "futbr-final-integrity-18198",
        "futbr-terminal-scorers-18199",
        "futbr-terminal-scorers-18202",
        "futbr-terminal-scorers-18203",
    ):
        html, count = strip_script(html, script_id)
        removed[script_id] = count

    if removed["futbr-final-integrity-18198"] != 1:
        fail("camada 18.198 esperada nao foi localizada uma unica vez")
    if removed["futbr-terminal-scorers-18199"] != 1:
        fail("camada 18.199 esperada nao foi localizada uma unica vez")

    root = r'''
<script id="futbr-scorers-root-18210">
(()=>{
 const G=window.GestorFC=window.GestorFC||{};
 const v18210BaseRenderPage=renderPage;

 function v18210Esc(value){
  const text=String(value??'');
  try{return typeof esc==='function'?esc(text):text.replace(/[&<>\"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[ch]));}
  catch(e){return text;}
 }
 function v18210Norm(value){
  try{return typeof E!=='undefined'&&typeof E.normName==='function'?E.normName(String(value||'')):String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}
  catch(e){return String(value||'').toLowerCase();}
 }
 function v18210Number(value){const n=Number(value);return Number.isFinite(n)?n:0;}
 function v18210Countries(){
  try{if(typeof C!=='undefined'&&Array.isArray(C))return C;}catch(e){}
  try{if(Array.isArray(WorldCatalog?.countries))return WorldCatalog.countries;}catch(e){}
  return [];
 }
 function v18210NationLabel(code){
  const key=String(code||'UNK').toUpperCase();
  try{if(typeof NAT!=='undefined'&&NAT?.[key]?.[0])return NAT[key][0];}catch(e){}
  return key;
 }
 function v18210NationHTML(code){
  try{if(typeof nation==='function')return nation(code);}catch(e){}
  return v18210Esc(v18210NationLabel(code));
 }
 function v18210RowsSource(rows){
  if(!rows||typeof rows!=='object')return [];
  const source=rows.players||rows.stats||rows;
  if(Array.isArray(source))return source.map((row,index)=>[String(row?.id??row?.playerId??row?.player_id??index),row]);
  if(source instanceof Map)return [...source.entries()].map(([id,row])=>[String(id),row]);
  return Object.entries(source);
 }
 function v18210Merge(map,raw,key='',national=false){
  if(!raw||typeof raw!=='object')return;
  const nested=raw.player&&typeof raw.player==='object'?raw.player:null;
  const id=String(raw.id??raw.playerId??raw.player_id??nested?.id??key??'');
  if(!id)return;
  const live=state?.players?.[id];
  const name=String(raw.name??raw.playerName??raw.player_name??nested?.name??live?.name??id);
  const natCode=String(raw.natCode??raw.nationality??nested?.natCode??live?.natCode??'UNK').toUpperCase();
  let row=map.get(id);
  if(!row){row={id,name,natCode,goals:0,assists:0,apps:0,minutes:0,clubs:{},nationalTeams:{}};map.set(id,row);}
  row.name=name||row.name;row.natCode=natCode||row.natCode;
  row.goals+=v18210Number(raw.goals??raw.goal??raw.g??raw.stats?.goals);
  row.assists+=v18210Number(raw.assists??raw.assist??raw.a??raw.stats?.assists);
  row.apps+=v18210Number(raw.apps??raw.appearances??raw.matches??raw.games??raw.j??raw.stats?.apps);
  row.minutes+=v18210Number(raw.minutes??raw.mins??raw.stats?.minutes);
  if(raw.clubs&&typeof raw.clubs==='object')Object.assign(row.clubs,raw.clubs);
  const clubName=raw.clubName??raw.teamName??raw.club?.name??raw.team?.name;
  if(clubName)row.clubs[String(raw.clubId??raw.teamId??Object.keys(row.clubs).length)]=String(clubName);
  if(national){
   const code=String(raw.teamCode??raw.nationalCode??raw.countryCode??'').toUpperCase();
   if(code)row.nationalTeams[code]=String(raw.teamName??raw.nationalTeamName??v18210NationLabel(code));
  }
 }
 function v18210CompetitionAllowed(key,f){
  const parts=String(key||'').split(':'),kind=parts[0]||'',country=parts[1]||'',division=parts[2]||'';
  const wanted=String(f.kind||'all');
  if(wanted==='national'||wanted.startsWith('nat|'))return false;
  if(wanted!=='all'&&wanted!==kind&&wanted!==String(key))return false;
  if(f.country&&f.country!=='all'&&['league','cup'].includes(kind)&&country!==String(f.country))return false;
  if(f.division&&f.division!=='all'&&kind==='league'&&Number(division)!==Number(f.division))return false;
  return true;
 }
 function v18210ClubSource(s,f){
  const year=f.year==='all'?'all':Number(f.year||s.year);
  if(year==='all')return s.allTimeStats||{};
  const archive=(s.scorerArchive||[]).find(item=>Number(item?.year)===year);
  const live=s.competitionStats||{};
  const liveHasRows=Object.values(live).some(rows=>v18210RowsSource(rows).length>0);
  return year!==Number(s.year)||(archive&&(!liveHasRows||!!s.seasonDone))?(archive?.competitions||{}):live;
 }
 function v18210Collect(s,f){
  const map=new Map(),source=v18210ClubSource(s,f),year=f.year==='all'?'all':Number(f.year||s.year);
  if(year==='all'){
   for(const [id,raw] of v18210RowsSource(source))v18210Merge(map,raw,id,false);
  }else{
   for(const [key,rows] of Object.entries(source||{})){
    if(!v18210CompetitionAllowed(key,f))continue;
    for(const [id,raw] of v18210RowsSource(rows))v18210Merge(map,raw,id,false);
   }
  }
  const wanted=String(f.kind||'all');
  if(f.year==='all'||wanted==='all'||wanted==='national'||wanted.startsWith('nat|')){
   const stats=s.v640National?.playerStats||{};
   const years=f.year==='all'?Object.keys(stats):[String(Number(f.year||s.year))];
   for(const y of years){
    for(const [competition,rows] of Object.entries(stats?.[y]||{})){
     if(wanted.startsWith('nat|')&&wanted!=='nat|'+competition)continue;
     for(const [id,raw] of v18210RowsSource(rows))v18210Merge(map,raw,id,true);
    }
   }
  }
  return [...map.values()]
   .filter(row=>row.goals>0)
   .sort((a,b)=>b.goals-a.goals||b.assists-a.assists||a.minutes-b.minutes||String(a.name).localeCompare(String(b.name),'pt-BR'));
 }
 function v18210Option(value,label,current){return '<option value="'+v18210Esc(value)+'" '+(String(current)===String(value)?'selected':'')+'>'+v18210Esc(label)+'</option>';}
 function v18210ClubHTML(row,kind){
  const nationalOnly=kind==='national'||String(kind||'').startsWith('nat|');
  const national=Object.entries(row.nationalTeams||{});
  if(nationalOnly)return national.length?national.map(([code,name])=>'<span class="pill">'+(typeof v640Flag==='function'?v640Flag(code):'')+' '+v18210Esc(name)+'</span>').join(' '):'<span class="muted">Selecao</span>';
  const live=state?.players?.[row.id];let club=null;
  try{club=live?.clubId&&typeof E!=='undefined'&&typeof E.team==='function'?E.team(state,live.clubId):(state?.teams||[]).find(t=>t.id===live?.clubId);}catch(e){}
  if(club){try{return '<div class="v538-scorer-club">'+(typeof badge==='function'?badge(club,'small'):'')+(typeof teamButton==='function'?teamButton(club):'<strong>'+v18210Esc(club.name)+'</strong>')+'</div>';}catch(e){return '<strong>'+v18210Esc(club.name)+'</strong>';}}
  const names=Object.values(row.clubs||{}).filter(Boolean);
  let out=names.length?v18210Esc(names.at(-1)):'Livre';
  if(String(kind||'')==='all'&&national.length)out+=' '+national.map(([code,name])=>'<span class="pill">'+(typeof v640Flag==='function'?v640Flag(code):'')+' '+v18210Esc(name)+'</span>').join(' ');
  return out;
 }
 function v18210ScorersContent(){
  const s=state;if(!s)return '<div class="empty">Nenhuma carreira carregada.</div>';
  const f=(typeof scorerFilter!=='undefined'&&scorerFilter)||(window.scorerFilter={});
  f.kind=f.kind||'all';f.country=f.country||'all';f.division=f.division||'all';f.year=f.year??'';f.query=f.query||'';f.nationality=f.nationality||'all';f.page=Math.max(0,Number(f.page)||0);
  let ranked=[];try{ranked=v18210Collect(s,f);}catch(e){console.error('[FutBR] criacao raiz de Artilheiros:',e);ranked=[];}
  const wantedNat=String(f.nationality||'all').toUpperCase(),query=v18210Norm(f.query||'');
  const rows=ranked.filter(row=>(wantedNat==='ALL'||row.natCode===wantedNat)&&(!query||v18210Norm(row.name).includes(query)));
  const rank=new Map(ranked.map((row,index)=>[row.id,index+1]));
  const years=[...new Set([Number(s.year),...(s.scorerArchive||[]).map(item=>Number(item?.year)),...Object.keys(s.v640National?.playerStats||{}).map(Number)])].filter(Number.isFinite).sort((a,b)=>b-a);
  const natCodes=[...new Set(ranked.map(row=>row.natCode))].sort((a,b)=>v18210NationLabel(a).localeCompare(v18210NationLabel(b),'pt-BR'));
  const competitionOptions={all:'Todas / global',league:'Ligas nacionais',cup:'Copas nacionais',national:'Selecoes - todas'};
  for(const competition of Object.values(s.competitions||{}))if(competition?.id)competitionOptions[competition.id]=competition.name||competition.id;
  for(const byYear of Object.values(s.v640National?.playerStats||{}))for(const key of Object.keys(byYear||{})){let label=key;try{if(typeof v641NationalCompetitionName==='function')label=v641NationalCompetitionName(s,key);}catch(e){}competitionOptions['nat|'+key]=label;}
  const pageSize=50,pages=Math.max(1,Math.ceil(rows.length/pageSize));f.page=Math.min(f.page,pages-1);const start=f.page*pageSize,end=Math.min(start+pageSize,rows.length),visible=rows.slice(start,end);
  const nationalOnly=f.kind==='national'||String(f.kind).startsWith('nat|'),disableClub=f.year==='all'||nationalOnly;
  const countryOptions='<option value="all">Todos</option>'+v18210Countries().map(country=>v18210Option(country.id,country.name,f.country)).join('');
  const divisionOptions=[['all','Todas'],['1','1a divisao'],['2','2a divisao'],['3','3a divisao'],['4','4a divisao']].map(([value,label])=>v18210Option(value,label,f.division)).join('');
  const body=visible.map(row=>{
   const clickable=!!s.players?.[row.id];
   const player=clickable?'<button class="table-button player-name" data-action="player" data-player="'+v18210Esc(row.id)+'">'+v18210Esc(row.name)+'</button>':'<span class="player-name">'+v18210Esc(row.name)+'</span>';
   let star='';try{if(typeof starBadge==='function')star=starBadge(row);}catch(e){}
   return '<tr><td>'+(rank.get(row.id)||'—')+'</td><td>'+player+' '+star+'</td><td>'+v18210NationHTML(row.natCode)+'</td><td class="club-history">'+v18210ClubHTML(row,f.year==='all'?'all':f.kind)+'</td><td class="number green strong">'+row.goals+'</td><td class="number">'+row.assists+'</td><td class="number">'+row.apps+'</td><td class="number">'+(row.goals/Math.max(1,row.apps)).toFixed(2)+'</td></tr>';
  }).join('');
  const prev=start?'':'disabled',next=end<rows.length?'':'disabled';
  return '<section class="panel" data-v18210-scorers-root="1"><div class="panel-body"><div class="filters">'+
   '<div class="field grow"><label for="score-query">Buscar atleta</label><input id="score-query" data-v641-score-query value="'+v18210Esc(f.query)+'" placeholder="Nome do jogador"></div>'+
   '<div class="field compact"><label for="score-kind">Competicao</label><select id="score-kind" data-v3="score-kind">'+Object.entries(competitionOptions).map(([value,label])=>v18210Option(value,label,f.kind)).join('')+'</select></div>'+
   '<div class="field compact"><label for="score-country">Pais</label><select id="score-country" data-v3="score-country" '+(disableClub?'disabled':'')+'>'+countryOptions+'</select></div>'+
   '<div class="field compact"><label for="score-div">Divisao</label><select id="score-div" data-v3="score-division" '+(disableClub||f.kind==='cup'?'disabled':'')+'>'+divisionOptions+'</select></div>'+
   '<div class="field compact"><label for="score-nationality">Nacionalidade</label><select id="score-nationality" data-v3="score-nationality"><option value="all">Todas</option>'+natCodes.map(code=>v18210Option(code,v18210NationLabel(code),wantedNat)).join('')+'</select></div>'+
   '<div class="field compact"><label for="score-year">Temporada</label><select id="score-year" data-v3="score-year">'+years.map(year=>v18210Option(year,year,Number(f.year||s.year))).join('')+v18210Option('all','Carreira global',f.year)+'</select></div></div></div>'+
   '<div class="table-scroll v615-ranking-scroll"><table><thead><tr><th>#</th><th>Atleta</th><th>Nacionalidade</th><th>Clube / selecao</th><th class="number">Gols</th><th class="number">Assist.</th><th class="number">J</th><th class="number">Gols/jogo</th></tr></thead><tbody>'+body+'</tbody></table></div>'+
   (!rows.length?'<div class="empty">Nenhum artilheiro encontrado neste recorte.</div>':'<div class="pagination v615-ranking-pagination"><span class="tiny muted">Pagina '+(f.page+1)+' de '+pages+' · '+(start+1)+'-'+end+' de '+rows.length+' artilheiros</span><div class="flex"><button class="btn small" data-action="score-prev" '+prev+'>Anterior</button><button class="btn small" data-action="score-next" '+next+'>Proxima</button></div></div>')+'</section>';
 }
 function v18210RankingsPage(){
  const tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';
  return '<div class="v677-ranking-hub">'+tabs+'<div class="v677-ranking-content"><div class="v615-rankings-shell">'+v18210ScorersContent()+'</div></div></div>';
 }
 function v18198EnforceInitialSquads(s){
  if(!s?.teams||Number(s.year)!==2026)return {moved:0,max:0};let moved=0,max=0;
  for(const team of s.teams){
   team.roster=[...new Set(team.roster||[])];team.academy=[...new Set(team.academy||[])].filter(id=>!team.roster.includes(id));team.proReserve=[...new Set(team.proReserve||[])].filter(id=>!team.roster.includes(id)&&!team.academy.includes(id));
   if(team.roster.length>32){const extra=team.roster.splice(32);for(const id of extra){const player=s.players?.[id];if(!player)continue;if(Number(player.age)<=20||player.squad==='youth'){if(!team.academy.includes(id))team.academy.push(id);player.squad='youth';player.proReserve=false;}else{if(!team.proReserve.includes(id))team.proReserve.push(id);player.squad='senior';player.proReserve=true;}player.clubId=team.id;moved++;}}
   for(const id of team.roster){const player=s.players?.[id];if(player){player.clubId=team.id;player.squad='senior';player.proReserve=false;}}
   for(const id of team.academy){const player=s.players?.[id];if(player){player.clubId=team.id;player.squad='youth';player.proReserve=false;}}
   if(Array.isArray(team.lineup))team.lineup=team.lineup.map(id=>id&&team.roster.includes(id)?id:null);
   try{E.repairLineup?.(s,team);}catch(e){}
   max=Math.max(max,team.roster.length);
  }
  s.v18198InitialSquads={version:'18.210',maxRoster:max,moved};return {moved,max};
 }

 window.v18198EnforceInitialSquads=v18198EnforceInitialSquads;
 window.v18210ScorersContent=v18210ScorersContent;
 window.v18210RankingsPage=v18210RankingsPage;
 try{scorersPage=v18210ScorersContent;}catch(e){window.scorersPage=v18210ScorersContent;}
 renderPage=function(){if(view==='rankings')return v18210RankingsPage();return v18210BaseRenderPage();};
 G.scorersRoot18210={version:'18.210',singleCanonicalRoute:true,noDomOverlay:true,liveAndArchiveStats:true,preservesPerformanceArchitecture:true};
})();
</script>
'''

    html = html.rstrip() + "\n\n" + root + "\n"

    forbidden = [
        "futbr-terminal-scorers-18199",
        "futbr-terminal-scorers-18202",
        "futbr-terminal-scorers-18203",
        "MutationObserver(()=>{if(v18203",
        "v18202Intent",
        "v18203Intent",
    ]
    for marker in forbidden:
        if marker in html:
            fail("camada antiga de Artilheiros permaneceu: " + marker)
    required = [
        "futbr-scorers-root-18210",
        "singleCanonicalRoute:true",
        "noDomOverlay:true",
        "liveAndArchiveStats:true",
        "preservesPerformanceArchitecture:true",
        "window.v18198EnforceInitialSquads",
        "if(view==='rankings')return v18210RankingsPage()",
    ]
    for marker in required:
        if marker not in html:
            fail("marcador raiz de Artilheiros ausente: " + marker)

    index_path.write_text(html, encoding="utf-8")
    print("Canonical root scorers screen 18.210 installed; old DOM overlays removed: " + str(removed))


if __name__ == "__main__":
    main()
