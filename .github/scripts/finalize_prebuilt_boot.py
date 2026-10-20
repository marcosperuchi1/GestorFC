from __future__ import annotations
import re, sys
from pathlib import Path


def fail(msg: str) -> None:
    raise RuntimeError(msg)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: finalize_prebuilt_boot.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    # A base consolidada ja existe neste ponto do pipeline. Daqui em diante,
    # nenhum codigo de compatibilidade pode decodificar elencos durante o boot.
    html = replace_once(
        html,
        "function v310RosterRecord(id){\n if(v310RosterDeleted.has(id))return undefined;",
        "function v310RosterRecord(id){\n if(!v310RosterText&&!V310_BOOTSTRAP_ROSTERS[id])return undefined;\n if(v310RosterDeleted.has(id))return undefined;",
        "guarda de leitura sincrona da base",
    )

    # Correcoes antigas ja foram materializadas pelo consolidador no asset final.
    html = replace_once(
        html,
        "v526PrioritizeJoaquinRoster();\n\n// Bandeiras offline",
        "/* Joaquin/Joaquim Freitas ja esta ordenado no asset consolidado do build. */\n\n// Bandeiras offline",
        "priorizacao Joaquin no boot",
    )

    old_anthony = """// Corrige a identidade conhecida do Anthony Valencia nesta base antes de qualquer nova carreira.
(function v530PatchRosterFacts(){
 for(const source of [BundledRosters,rosterCache]){
  const list=source?.t0?.players;if(!Array.isArray(list))continue;
  const p=list.find(x=>E.normName(x?.name||'')==='anthony valencia');if(p){p.age=23;p.ageEstimated=false;}
 }
})();"""
    html = replace_once(
        html,
        old_anthony,
        "// Anthony Valencia ja esta corrigido no asset consolidado gerado no build.\n// Nenhum elenco e consultado durante a avaliacao inicial da pagina.",
        "correcao Anthony no boot",
    )

    old_fluminense = """// 18.3 database correction: Fluminense starts new careers with Marcão (BRA).
try{const v183FluBase=v310RosterRecord('t6');if(v183FluBase){v310RosterOverrides.t6={...v183FluBase,coach:{...(v183FluBase.coach||{}),name:'Marcão',natCode:'BRA',real:true,source:'Editor local FutBR Manager 18.3',fetchedAt:'2026-10-06'}};v310RosterCache.delete('t6');}}catch(e){}"""
    html = replace_once(
        html,
        old_fluminense,
        "// Marcao (BRA) no Fluminense ja esta gravado no asset consolidado do build.\n// Nao consultar t6 durante o boot.",
        "correcao Fluminense no boot",
    )

    # Este sweep existia apenas para preparar os 256 registros mantidos no cache.
    # O consolidador ja aplicou as mesmas correcoes ao arquivo definitivo.
    sweep = re.compile(
        r"// Previously the age and position sweeps ran before v206SupportNames\.\n"
        r"for\(const t of \(WorldCatalog\.clubs\|\|\[\]\)\.slice\(-256\)\)\{\n"
        r" const roster=BundledRosters\[t\.id\];\n"
        r" if\(!roster\)continue;\n"
        r" v515ApplyPositionFixesToItem\(t\.id,roster\);\n"
        r" for\(const p of roster\.players\|\|\[\]\)\{\n"
        r"  if\(Number\.isFinite\(Number\(p\.age\)\)&&Number\(p\.age\)>=14&&Number\(p\.age\)<=60\)p\.ageEstimated=false;\n"
        r" \}\n"
        r" v206RenameSupportRoster\(t,roster\);\n"
        r"\}\n"
    )
    match = sweep.search(html)
    if not match:
        fail("sweep legado dos 256 elencos nao encontrado")
    html = (
        html[: match.start()]
        + "// Posicoes, idades e nomes dos 256 registros finais ja foram consolidados no asset durante o build.\n"
          "// O boot nao percorre elencos.\n"
        + html[match.end() :]
    )

    old_meta = """function v691RefreshMeta(){
 EditionMeta.clubs=WorldCatalog.clubs.length;
 EditionMeta.leagues=new Set(WorldCatalog.clubs.map(t=>t.country+':'+(Number(t.division)||1))).size;
 EditionMeta.realPlayers=Object.values(rosterCache||{}).reduce((n,r)=>n+(r?.players?.length||0),0);
}"""
    new_meta = """function v691RefreshMeta(){
 EditionMeta.clubs=WorldCatalog.clubs.length;
 EditionMeta.leagues=new Set(WorldCatalog.clubs.map(t=>t.country+':'+(Number(t.division)||1))).size;
 const prebuilt=Number(window.GestorFC?.baseRosterStats310?.players);
 if(Number.isFinite(prebuilt)&&prebuilt>0)EditionMeta.realPlayers=prebuilt;
 else if(typeof v310RosterText==='string'&&v310RosterText)EditionMeta.realPlayers=Object.values(rosterCache||{}).reduce((n,r)=>n+(r?.players?.length||0),0);
}"""
    html = replace_once(html, old_meta, new_meta, "metadados sem varredura pre-login")

    # Restaura o teto historico de 32 atletas no elenco principal. A ordem da
    # base consolidada e preservada: os 32 primeiros seniors continuam no
    # profissional e todo senior excedente vai para Categorias de base.
    html = replace_once(
        html,
        "if(t.prebuiltInitial){\n      const seeded=[...t.roster];t.roster=[];t.proReserve=[];t.seniorTarget=seniorTarget(s,t);",
        "if(t.prebuiltInitial){\n      const seeded=[...t.roster];t.roster=[];t.proReserve=[];t.seniorTarget=seniorTarget(s,t);let v18197PrebuiltSeniorCount=0;",
        "contador do teto senior precompilado",
    )
    html = replace_once(
        html,
        "p.clubId=t.id;p.squad='senior';p.proReserve=false;t.roster.push(id);",
        "if(v18197PrebuiltSeniorCount<32){p.clubId=t.id;p.squad='senior';p.proReserve=false;t.roster.push(id);v18197PrebuiltSeniorCount++;}else{p.clubId=t.id;p.squad='youth';p.proReserve=false;p.ageEstimated=false;p.youthOrigin??=t.id;p.academyApps??=0;p.academyGoals??=0;p.development??=0;p.youthStart??=overall(p);p.youthYear??=s.year;p.v576YouthInitialOVR??=p.youthStart;p.v577YouthInitialOVR??=p.youthStart;p.v576YouthModel??=1;p.v577YouthModel??=1;p.v576PotentialFixed??=1;p.v577PotentialFixed??=1;p.academyStarPath=p.potential>=90;t.academy.push(id);}",
        "teto de 32 seniors e excedente na base",
    )

    # Duas camadas historicas ainda tentavam aumentar/reconstruir o profissional
    # depois que o Worker ja havia devolvido a divisao correta 32 + academia.
    html = replace_once(
        html,
        "const V579_VERSION='5.79',V579_INITIAL_MAIN=35;",
        "const V579_VERSION='5.79',V579_INITIAL_MAIN=32;",
        "limite legado 5.79",
    )
    html = replace_once(
        html,
        "const V582_VERSION='5.82',V582_MAX_INITIAL_SENIORS=60;",
        "const V582_VERSION='5.82',V582_MAX_INITIAL_SENIORS=32;",
        "limite legado 5.82",
    )
    html = replace_once(
        html,
        "  try{v582RepairFreshProtectedCareer?.(out);}catch(e){}\n",
        "  // A base consolidada ja e a autoridade. Nao reconstruir o clube protegido.\n  out.v582InitialRosterIntegrity=1;out.v582InitialRosterSource='prebuilt-consolidated';\n",
        "reconstrucao 5.82 depois da nova carreira",
    )

    # Monte o formulario imediatamente. A base de jogadores so pode ser aberta
    # depois que uma sessao valida existir. Isso vale tanto para sessao restaurada
    # quanto para login manual (v548EnterGame ja aguarda a base).
    old_boot = """async function v548Boot(){
 const localPreload=Promise.resolve().then(()=>v260FastLoadLocal(false)).catch(e=>{console.warn('[FutBR] leitura local no boot:',e?.message||e);return null;});
 const rosterPreload=Promise.resolve().then(()=>v310StartRosterLoad()).catch(e=>{console.error('[FutBR] base instalada no boot:',e?.message||e);return null;});
 const authPromise=Promise.resolve().then(()=>v580RestoreRemoteSession()).catch(e=>{console.warn('[FutBR] sessao remota no boot:',e?.message||e);return null;});
 let timeoutId=0;
 const timeout=new Promise(resolve=>{timeoutId=setTimeout(()=>resolve(null),6000);});
 const authenticated=await Promise.race([authPromise,timeout]);
 if(timeoutId)clearTimeout(timeoutId);
 if(authenticated){
  await Promise.all([localPreload,rosterPreload]);
  if(!state)renderWelcome();
  return;
 }
 await localPreload;
 v548RenderAuth('login','Validando sua sessao. Se necessario, entre novamente.');
 authPromise.then(session=>{if(session&&!state){v548EnterGame().catch(e=>console.warn('[FutBR] entrada apos validacao:',e?.message||e));}}).catch(()=>{});
}"""
    new_boot = """async function v548Boot(){
 // O login deve existir visualmente antes de qualquer leitura da base de jogadores.
 v548RenderAuth('login','');
 const localPreload=Promise.resolve().then(()=>v260FastLoadLocal(false)).catch(e=>{console.warn('[FutBR] leitura local no boot:',e?.message||e);return null;});
 const authPromise=Promise.resolve().then(()=>v580RestoreRemoteSession()).catch(e=>{console.warn('[FutBR] sessao remota no boot:',e?.message||e);return null;});
 let timeoutId=0;
 const timeout=new Promise(resolve=>{timeoutId=setTimeout(()=>resolve(null),6000);});
 const authenticated=await Promise.race([authPromise,timeout]);
 if(timeoutId)clearTimeout(timeoutId);
 if(authenticated){
  await localPreload;
  await v310StartRosterLoad();
  if(!state)renderWelcome();
  return;
 }
 // Mantem o formulario ja montado. A base so sera aberta depois de login valido.
 authPromise.then(session=>{if(session&&!state){v548EnterGame().catch(e=>console.warn('[FutBR] entrada apos validacao:',e?.message||e));}}).catch(()=>{});
}"""
    html = replace_once(html, old_boot, new_boot, "boot autenticacao primeiro")

    html = replace_once(
        html,
        "rosterPreloadedDuringAuth:true,\n loginUiIndependentFromRoster:true,",
        "rosterPreloadedDuringAuth:false,\n loginUiIndependentFromRoster:true,\n rosterLoadAfterAuthentication:true,\n noRosterReadBeforeLogin:true,",
        "marcadores do boot",
    )

    # Invariantes da versao final que vai para o Tauri.
    boot_start = html.find("async function v548Boot(){")
    boot_end = html.find("\nv548Boot().catch", boot_start)
    if boot_start < 0 or boot_end < 0:
        fail("nao foi possivel localizar v548Boot final")
    boot = html[boot_start:boot_end]
    first_auth = boot.find("v548RenderAuth('login','');")
    first_roster = boot.find("v310StartRosterLoad()")
    if first_auth < 0 or first_roster < 0 or first_auth > first_roster:
        fail("boot final ainda pode tocar na base antes de montar o login")
    if "rosterPreload=" in boot:
        fail("preload de roster durante autenticacao ainda presente")
    if "await localPreload;\n v548RenderAuth" in boot:
        fail("login ainda espera leitura local")

    # A cadeia historica de scorersPage acumulou wrappers que podem falhar antes
    # de page.innerHTML ser substituido. O sintoma e a aba Artilheiros ativa com
    # o conteudo anterior ainda visivel. A rota final usa um renderer independente
    # que le diretamente competitionStats/scorerArchive/allTimeStats e, quando ja
    # existente, o historico de selecoes.
    ranking_guard = r'''
<script id="futbr-final-integrity-18198">
(()=>{
 const G=window.GestorFC=window.GestorFC||{};

 function v18198Esc(v){try{return typeof esc==='function'?esc(String(v??'')):String(v??'');}catch(e){return String(v??'');}}
 function v18198Norm(v){try{return E.normName(String(v||''));}catch(e){return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();}}
 function v18198Merge(map,r,national=false){
  if(!r?.id)return;
  let x=map.get(r.id);
  if(!x){x={id:r.id,name:r.name||state?.players?.[r.id]?.name||r.id,natCode:r.natCode||state?.players?.[r.id]?.natCode||'UNK',goals:0,assists:0,apps:0,minutes:0,clubs:{},nationalTeams:{}};map.set(r.id,x);}
  x.name=r.name||x.name;x.natCode=r.natCode||x.natCode;
  x.goals+=Number(r.goals)||0;x.assists+=Number(r.assists)||0;x.apps+=Number(r.apps)||0;x.minutes+=Number(r.minutes)||0;
  if(national){if(r.teamCode)x.nationalTeams[r.teamCode]=r.teamName||r.teamCode;}
  else Object.assign(x.clubs,r.clubs||{});
 }
 function v18198ClubRows(s,f){
  const map=new Map(),year=f.year==='all'?'all':Number(f.year||s.year);
  if(year==='all'){
   for(const r of Object.values(s.allTimeStats||{}))v18198Merge(map,r,false);
   return map;
  }
  const db=year!==Number(s.year)?((s.scorerArchive||[]).find(x=>Number(x?.year)===year)?.competitions||{}):(s.competitionStats||{});
  for(const [key,rows] of Object.entries(db||{})){
   const parts=String(key).split(':'),kind=parts[0]||'',country=parts[1]||'',division=parts[2]||'';
   const wanted=String(f.kind||'all');
   if(wanted==='national'||wanted.startsWith('nat|'))continue;
   if(wanted!=='all'&&wanted!==kind&&wanted!==key)continue;
   if(f.country&&f.country!=='all'&&['league','cup'].includes(kind)&&country!==f.country)continue;
   if(f.division&&f.division!=='all'&&kind==='league'&&Number(division)!==Number(f.division))continue;
   for(const r of Object.values(rows||{}))v18198Merge(map,r,false);
  }
  return map;
 }
 function v18198AddNationalRows(s,f,map){
  const root=s?.v640National;if(!root?.playerStats)return;
  const wanted=String(f.kind||'all'),global=f.year==='all';
  if(!global&&wanted!=='all'&&wanted!=='national'&&!wanted.startsWith('nat|'))return;
  const years=global?Object.keys(root.playerStats||{}):[String(Number(f.year||s.year))];
  for(const y of years){
   const ydb=root.playerStats?.[y]||{};
   for(const [comp,rows] of Object.entries(ydb)){
    if(!global&&wanted.startsWith('nat|')&&wanted!=='nat|'+comp)continue;
    for(const r of Object.values(rows||{}))v18198Merge(map,r,true);
   }
  }
 }
 function v18198ScorerRows(s,f){
  const map=v18198ClubRows(s,f);v18198AddNationalRows(s,f,map);
  return [...map.values()].filter(r=>(Number(r.goals)||0)>0).sort((a,b)=>(Number(b.goals)||0)-(Number(a.goals)||0)||(Number(b.assists)||0)-(Number(a.assists)||0)||(Number(a.minutes)||0)-(Number(b.minutes)||0)||String(a.name||'').localeCompare(String(b.name||''),'pt-BR'));
 }
 function v18198Option(value,label,current){return '<option value="'+v18198Esc(value)+'" '+(String(current)===String(value)?'selected':'')+'>'+v18198Esc(label)+'</option>';}
 function v18198Nation(code){try{return typeof nation==='function'?nation(code):v18198Esc(code||'UNK');}catch(e){return v18198Esc(code||'UNK');}}
 function v18198Star(p){try{return typeof starBadge==='function'?starBadge(p):'';}catch(e){return '';}}
 function v18198Source(p,kind){
  const nationalOnly=kind==='national'||String(kind||'').startsWith('nat|'),nat=Object.entries(p.nationalTeams||{});
  if(nationalOnly)return nat.length?nat.map(([code,name])=>'<span class="pill">'+(typeof v640Flag==='function'?v640Flag(code):'')+' '+v18198Esc(name)+'</span>').join(' '):'<span class="muted">Selecao</span>';
  const live=state?.players?.[p.id],tid=live?.clubId;let team=null;try{team=tid?E.team(state,tid):null;}catch(e){}
  if(team){try{return '<div class="v538-scorer-club">'+badge(team,'small')+teamButton(team)+'</div>';}catch(e){return '<strong>'+v18198Esc(team.name)+'</strong>';}}
  const clubs=Object.values(p.clubs||{}).filter(Boolean);
  let club=clubs.length?v18198Esc(clubs.at(-1)):'Livre';
  if(String(kind||'')==='all'&&nat.length)club+=' '+nat.map(([code,name])=>'<span class="pill">'+(typeof v640Flag==='function'?v640Flag(code):'')+' '+v18198Esc(name)+'</span>').join(' ');
  return club;
 }
 function v18198ScorersPage(){
  const s=state;if(!s)return '<div class="empty">Nenhuma carreira carregada.</div>';
  const f=scorerFilter||(scorerFilter={});f.kind=f.kind||'all';f.country=f.country||'all';f.division=f.division||'all';f.year=f.year??'';f.query=f.query||'';f.nationality=f.nationality||'all';f.page=Math.max(0,Number(f.page)||0);
  let ranked=[];try{ranked=v18198ScorerRows(s,f);}catch(e){console.error('[FutBR] artilharia final:',e);ranked=[];}
  const wantNat=String(f.nationality||'all').toUpperCase(),q=v18198Norm(f.query||'');
  const rows=ranked.filter(p=>(wantNat==='ALL'||String(p.natCode||'UNK').toUpperCase()===wantNat)&&(!q||v18198Norm(p.name||'').includes(q)));
  const rank=new Map(ranked.map((p,i)=>[p.id,i+1]));
  const years=[...new Set([Number(s.year),...(s.scorerArchive||[]).map(x=>Number(x?.year)),...Object.keys(s.v640National?.playerStats||{}).map(Number)])].filter(Number.isFinite).sort((a,b)=>b-a);
  const natCodes=[...new Set(ranked.map(x=>String(x.natCode||'UNK').toUpperCase()))].sort((a,b)=>(NAT?.[a]?.[0]||a).localeCompare(NAT?.[b]?.[0]||b,'pt-BR'));
  const compOpts={all:'Todas / global',league:'Ligas nacionais',cup:'Copas nacionais',national:'Selecoes - todas'};
  for(const c of Object.values(s.competitions||{}))if(c?.id)compOpts[c.id]=c.name||c.id;
  for(const y of Object.values(s.v640National?.playerStats||{}))for(const k of Object.keys(y||{})){let label=k;try{if(typeof v641NationalCompetitionName==='function')label=v641NationalCompetitionName(s,k);}catch(e){}compOpts['nat|'+k]=label;}
  const pageSize=50,pages=Math.max(1,Math.ceil(rows.length/pageSize));f.page=Math.min(f.page,pages-1);const start=f.page*pageSize,end=Math.min(start+pageSize,rows.length),visible=rows.slice(start,end);
  const nationalOnly=f.kind==='national'||String(f.kind||'').startsWith('nat|'),disableClub=f.year==='all'||nationalOnly;
  const compHTML=Object.entries(compOpts).map(([v,l])=>v18198Option(v,l,f.kind)).join('');
  const countryHTML='<option value="all">Todos</option>'+((Array.isArray(C)?C:[]).map(c=>v18198Option(c.id,c.name,f.country)).join(''));
  const divHTML=[['all','Todas'],['1','1a divisao'],['2','2a divisao'],['3','3a divisao'],['4','4a divisao']].map(([v,l])=>v18198Option(v,l,f.division)).join('');
  const natHTML='<option value="all">Todas</option>'+natCodes.map(code=>v18198Option(code,NAT?.[code]?.[0]||code,wantNat)).join('');
  const yearHTML=years.map(y=>v18198Option(y,y,Number(f.year||s.year))).join('')+v18198Option('all','Carreira global',f.year);
  const body=visible.map(p=>{
   const clickable=!!s.players?.[p.id],player=clickable?'<button class="table-button player-name" data-action="player" data-player="'+v18198Esc(p.id)+'">'+v18198Esc(p.name)+'</button>':'<span class="player-name">'+v18198Esc(p.name)+'</span>';
   return '<tr><td>'+(rank.get(p.id)||'—')+'</td><td>'+player+' '+v18198Star(p)+'</td><td>'+v18198Nation(p.natCode)+'</td><td class="club-history">'+v18198Source(p,f.year==='all'?'all':f.kind)+'</td><td class="number green strong">'+(Number(p.goals)||0)+'</td><td class="number">'+(Number(p.assists)||0)+'</td><td class="number">'+(Number(p.apps)||0)+'</td><td class="number">'+((Number(p.goals)||0)/Math.max(1,Number(p.apps)||0)).toFixed(2)+'</td></tr>';
  }).join('');
  const prev=start?'':'disabled',next=end<rows.length?'':'disabled';
  return '<section class="panel"><div class="panel-body"><div class="filters">'+
   '<div class="field grow"><label for="score-query">Buscar atleta</label><input id="score-query" data-v641-score-query value="'+v18198Esc(f.query)+'" placeholder="Nome do jogador"></div>'+
   '<div class="field compact"><label for="score-kind">Competicao</label><select id="score-kind" data-v3="score-kind">'+compHTML+'</select></div>'+
   '<div class="field compact"><label for="score-country">Pais</label><select id="score-country" data-v3="score-country" '+(disableClub?'disabled':'')+'>'+countryHTML+'</select></div>'+
   '<div class="field compact"><label for="score-div">Divisao</label><select id="score-div" data-v3="score-division" '+(disableClub||f.kind==='cup'?'disabled':'')+'>'+divHTML+'</select></div>'+
   '<div class="field compact"><label for="score-nationality">Nacionalidade</label><select id="score-nationality" data-v3="score-nationality">'+natHTML+'</select></div>'+
   '<div class="field compact"><label for="score-year">Temporada</label><select id="score-year" data-v3="score-year">'+yearHTML+'</select></div></div></div>'+
   '<div class="table-scroll v615-ranking-scroll"><table><thead><tr><th>#</th><th>Atleta</th><th>Nacionalidade</th><th>Clube / selecao</th><th class="number">Gols</th><th class="number">Assist.</th><th class="number">J</th><th class="number">Gols/jogo</th></tr></thead><tbody>'+body+'</tbody></table></div>'+
   (!rows.length?'<div class="empty">Nenhum artilheiro encontrado neste recorte.</div>':'<div class="pagination v615-ranking-pagination"><span class="tiny muted">Pagina '+(f.page+1)+' de '+pages+' · '+(start+1)+'-'+end+' de '+rows.length+' artilheiros</span><div class="flex"><button class="btn small" data-action="score-prev" '+prev+'>Anterior</button><button class="btn small" data-action="score-next" '+next+'>Proxima</button></div></div>')+
   '</section>';
 }

 // Ultima barreira do elenco inicial. Normalmente e no-op porque o Worker ja
 // devolve 32 + academia; existe para impedir qualquer futura camada de UI de
 // recolocar jovens no profissional.
 function v18198EnforceInitialSquads(s){
  if(!s?.teams||Number(s.year)!==2026)return {moved:0,max:0};let moved=0,max=0;
  for(const t of s.teams){
   t.roster=[...new Set(t.roster||[])];t.academy=[...new Set(t.academy||[])].filter(id=>!t.roster.includes(id));t.proReserve=[...new Set(t.proReserve||[])].filter(id=>!t.roster.includes(id)&&!t.academy.includes(id));
   if(t.roster.length>32){
    const extra=t.roster.splice(32);
    for(const id of extra){const p=s.players?.[id];if(!p)continue;if(Number(p.age)<=20||p.squad==='youth'){if(!t.academy.includes(id))t.academy.push(id);p.squad='youth';p.proReserve=false;}else{if(!t.proReserve.includes(id))t.proReserve.push(id);p.squad='senior';p.proReserve=true;}p.clubId=t.id;moved++;}
   }
   for(const id of t.roster){const p=s.players?.[id];if(p){p.clubId=t.id;p.squad='senior';p.proReserve=false;}}
   for(const id of t.academy){const p=s.players?.[id];if(p){p.clubId=t.id;p.squad='youth';p.proReserve=false;}}
   if(Array.isArray(t.lineup))t.lineup=t.lineup.map(id=>id&&t.roster.includes(id)?id:null);
   try{E.repairLineup?.(s,t);}catch(e){}
   max=Math.max(max,t.roster.length);
  }
  s.v18198InitialSquads={version:'18.198',maxRoster:max,moved};return {moved,max};
 }

 // O helper fica global para o pipeline RPC e para os testes.
 window.v18198EnforceInitialSquads=v18198EnforceInitialSquads;
 const v18198BaseRenderPage=renderPage;
 const v18198RankingHub=inner=>'<div class="v677-ranking-hub">'+(typeof v677RankingTabs==='function'?v677RankingTabs():'')+'<div class="v677-ranking-content">'+inner+'</div></div>';
 renderPage=function(){
  if(view==='rankings'){
   try{return v18198RankingHub('<div class="v615-rankings-shell">'+v18198ScorersPage()+'</div>');}
   catch(e){console.error('[FutBR] falha final em Artilheiros:',e);return v18198RankingHub('<div class="notice error">Nao foi possivel montar a artilharia desta carreira.</div>');}
  }
  if(view==='coaches')return v18198RankingHub(coachesPage());
  return v18198BaseRenderPage();
 };
 G.finalIntegrity18198={version:'18.198',explicitScorersRoute:true,directScorerRenderer:true,legacyProtectedRosterRepairDisabled:true,initialSeniorCap:32};
})();
</script>
'''
    if 'futbr-final-integrity-18198' not in html:
        html = replace_once(html, '</body>', ranking_guard + '\n</body>', 'integridade final de artilheiros e elenco')

    html = replace_once(
        html,
        "window.v18198EnforceInitialSquads=v18198EnforceInitialSquads;\n const v18198BaseRenderPage=renderPage;",
        "window.v18198EnforceInitialSquads=v18198EnforceInitialSquads;\n window.v18198ScorersPage=v18198ScorersPage;\n const v18198BaseRenderPage=renderPage;",
        "expor renderer de artilheiros para camada terminal",
    )

    # Chama a barreira de elenco imediatamente no retorno real do Worker, depois
    # dos complementos nacionais e antes de o estado chegar a interface.
    html = replace_once(
        html,
        " if(out&&op==='create')v18170EnsureAllNationalPools(out);",
        " if(out&&op==='create'){v18170EnsureAllNationalPools(out);try{window.v18198EnforceInitialSquads?.(out);}catch(e){console.error('[FutBR] teto inicial:',e);}}",
        "barreira final de 32 no RPC",
    )

    # Alguns patches historicos do pacote fonte ficam fisicamente depois de
    # </html>. Portanto a correcao de Artilheiros precisa ser a ultima camada do
    # arquivo, nao apenas a ultima antes de </body>.
    terminal_scorers = r'''
<script id="futbr-terminal-scorers-18199">
(()=>{
 const G=window.GestorFC=window.GestorFC||{};
 function v18199Hub(){
  const tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';
  const inner=typeof window.v18198ScorersPage==='function'?window.v18198ScorersPage():'<div class="notice error">Artilharia indisponivel.</div>';
  return '<div class="v677-ranking-hub">'+tabs+'<div class="v677-ranking-content"><div class="v615-rankings-shell">'+inner+'</div></div></div>';
 }
 function v18199Decorate(page){
  try{v551CleanScreen?.(page);}catch(e){}
  try{v554CleanLegacyCopy?.();}catch(e){}
  try{v548ApplyFeatureLocks?.(page);}catch(e){}
  try{v1882EnhanceCountrySelects?.(page);}catch(e){}
  try{v54ApplyPositionOrder?.();v5MarkSelection?.();v510ApplyTrophyPhotos?.();}catch(e){}
  try{v555ScheduleDecor?.(page);}catch(e){}
 }
 function v18199Paint(){
  if(!state)return false;
  view='rankings';
  try{v260BodyClasses?.();}catch(e){}
  const root=document.querySelector('#app'),page=document.querySelector('#v555-page');
  if(!page)return false;
  let html='';
  try{html=v18199Hub();}catch(e){
   console.error('[FutBR] terminal Artilheiros:',e);
   html='<div class="v677-ranking-hub">'+(typeof v677RankingTabs==='function'?v677RankingTabs():'')+'<div class="v677-ranking-content"><div class="notice error">Nao foi possivel montar a artilharia desta carreira.</div></div></div>';
  }
  page.innerHTML=html;
  v18199Decorate(page);
  try{if(root)v555UpdateChrome?.(root);}catch(e){}
  try{if(root)v677SyncRankingNavigation?.(root);}catch(e){}
  try{v260BodyClasses?.();}catch(e){}
  return true;
 }
 window.v18199PaintScorers=v18199Paint;

 // Esta e propositalmente a ultima definicao de renderPage do arquivo.
 const v18199BaseRenderPage=renderPage;
 renderPage=function(){
  if(view==='rankings'){
   try{return v18199Hub();}
   catch(e){console.error('[FutBR] render terminal Artilheiros:',e);return '<div class="notice error">Nao foi possivel montar a artilharia desta carreira.</div>';}
  }
  return v18199BaseRenderPage();
 };

 // Intercepta a aba antes do delegador historico data-action=nav.
 document.addEventListener('click',e=>{
  const btn=e.target?.closest?.('.v677-ranking-tab[data-view="rankings"]');
  if(!btn)return;
  e.preventDefault();e.stopImmediatePropagation();
  try{closeModal?.();}catch(err){}
  view='rankings';
  if(!v18199Paint())try{render();}catch(err){console.error('[FutBR] navegacao Artilheiros:',err);}
  try{window.scrollTo({top:0});}catch(err){}
 },true);

 G.terminalScorers18199={version:'18.199',physicalLastLayer:true,captureNavigation:true,directPagePaint:true};
})();
</script>
'''
    if 'futbr-terminal-scorers-18199' not in html:
        html = html.rstrip() + "\\n\\n" + terminal_scorers + "\\n"

    index_path.write_text(html, encoding="utf-8")
    print("prebuilt boot finalized: login-first, authoritative-32-plus-academy, terminal-scorers-18199")


if __name__ == "__main__":
    main()
