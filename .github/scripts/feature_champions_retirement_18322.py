from pathlib import Path
import json
import sys

VERSION = '18.328'
MARK = 'FUTBR_CHAMPIONS_RETIREMENT_18322'
UI = r"""
/* FUTBR_CHAMPIONS_RETIREMENT_18322 */
let v18322ClubOpen=false,v18322NationalOpen=false,v18322TransferTab='transfers';
const v18322ClubFilters={country:'all',kind:'all',division:'all',competition:'all',year:'all'};
let v18322ClubFilterState=null,v18322VisibleLimit=120;
const v18322NationalFilters={conf:'all',nation:'all',competition:'all'};
let v18322RetireYear='all';
const v18322Preview=new WeakMap();
const v18322N=(x)=>Number.isFinite(Number(x))?Number(x):0;
const v18322Esc=(x)=>esc(String(x??''));
function v18322CountryLabel(id){return WorldCatalog.countries.find(c=>c.id===id)?.name||String(id||'');}
function v18322ClubName(s,id,fallback=''){
 return E.team(s,id)?.name||fallback||(id?String(id):'Sem registro');
}
function v18322Scorers(db){
 const scored=Object.values(db||{}).filter(x=>x&&v18322N(x.goals)>0);
 if(!scored.length)return [];
 scored.sort((a,b)=>v18322N(b.goals)-v18322N(a.goals)||v18322N(b.assists)-v18322N(a.assists)||String(a.name).localeCompare(String(b.name),'pt-BR'));
 const max=v18322N(scored[0].goals);
 return scored.filter(x=>v18322N(x.goals)===max).map(r=>{
  const grouped=Object.entries(r.byClub||{}).sort((a,b)=>v18322N(b[1]?.goals)-v18322N(a[1]?.goals));
  const club=grouped[0]?.[0]||Object.keys(r.clubs||{})[0]||r.club||null;
  return {id:String(r.id||''),name:String(r.name||'Jogador'),goals:max,club,clubName:String(r.clubs?.[club]||'')};
 });
}
function v18322CupRunners(s){
 const map=new Map();
 for(const stage of s.schedule||[])for(const f of stage?.fixtures||[]){
  if(!f?.final||!f?.result||!f?.country||f.country==='international')continue;
  const winner=s.cupWinners?.[f.country]||f.result.qualifier||f.result.winner;
  if(winner!==f.home&&winner!==f.away)continue;
  map.set(f.country,winner===f.home?f.away:f.home);
 }
 return map;
}

function v18322IntlScorers(s){
 const result=new Map(),raw=new Map();
 // Use actual competitionStats recorded for the entire season. Fixture events
 // can be pruned in simulation and cannot be the only official scorer source.
 for(const [id,db] of Object.entries(s.competitionStats||{})){
  if(id.startsWith('league:')||id.startsWith('cup:'))continue;
  const leaders=v18322Scorers(db);
  if(leaders.length)result.set(String(id),leaders);
 }
 for(const stage of s.schedule||[])for(const f of stage?.fixtures||[]){
  if(!f?.competition||!f?.result)continue;
  const id=String(f.competition);
  if(result.has(id))continue;
  const row=raw.get(id)||{goals:new Map(),expected:0,counted:0};
  row.expected+=Math.max(0,v18322N(f.result.home))+Math.max(0,v18322N(f.result.away));
  const events=(f.result.events||[]).some(e=>e?.type==='goal')
   ?f.result.events:Array.isArray(f.result.scorers)?f.result.scorers:[];
  for(const ev of events){
   if(!ev?.pid||(ev.type&&ev.type!=='goal'))continue;
   const club=Number(ev.side)===0?f.home:f.away,p=s.players?.[ev.pid],key=String(ev.pid);
   const scorer=row.goals.get(key)||{id:key,name:p?.name||ev.name||'Jogador',club,
    clubName:v18322ClubName(s,club),goals:0};
   scorer.goals++;row.counted++;row.goals.set(key,scorer);
  }
  raw.set(id,row);
 }
 for(const [id,row] of raw)if(!result.has(id)){
  // A partial event log cannot determine the official competition winner.
  result.set(id,row.counted>0&&row.counted===row.expected
   ?v18322Scorers(Object.fromEntries(row.goals)):[]);
 }
 return result;
}
function v18322MatchRow(row,f){
 if(!f)return true;
 if(f.year!=='all'&&f.year!=null&&Number(row.year)!==Number(f.year))return false;
 if(f.country!=='all'&&f.country!=null&&row.country!==f.country)return false;
 if(f.kind!=='all'&&f.kind!=null&&row.kind!==f.kind)return false;
 if(f.division!=='all'&&f.division!=null&&row.kind==='league'&&Number(row.division)!==Number(f.division))return false;
 if(f.competition!=='all'&&f.competition!=null&&row.competition!==f.competition)return false;
 return true;
}

function v18322CollectSeason(s,year,filter=null){
 if(!s?.teams?.length)return [];
 const rows=[],requiresCup=!filter||filter.kind==='all'||filter.kind==='cup',
  requiresIntl=!filter||filter.kind==='all'||filter.kind==='international';
 const cupRunners=requiresCup?v18322CupRunners(s):new Map();
 const intlGoals=requiresIntl?v18322IntlScorers(s):new Map();
 const add=(kind,country,division,competition,champion,runner,scorers)=>{
  if(!champion)return;
  const row={year,kind,country:country||'',division:Number(division)||0,competition:String(competition),
   champion:String(champion),championName:v18322ClubName(s,champion),
   runner:runner?String(runner):null,runnerName:runner?v18322ClubName(s,runner):'',
   scorers:Array.isArray(scorers)?scorers:[]};
  if(v18322MatchRow(row,filter))rows.push(row);
 };
 const divisions=new Map();
 if(!filter||filter.kind==='league'||filter.kind==='all')
  for(const t of s.teams||[]){
   if(!t?.country||(filter?.country!=='all'&&filter?.country&&filter.country!==t.country))continue;
   if(!divisions.has(t.country))divisions.set(t.country,new Set());
   divisions.get(t.country).add(v18322N(t.division)||1);
  }
 for(const c of WorldCatalog.countries){
  if(filter?.country&&filter.country!=='all'&&filter.country!==c.id)continue;
  if(!filter||filter.kind==='all'||filter.kind==='league'){
   for(const div of [...(divisions.get(c.id)||[])].sort((a,b)=>a-b)){
    const key='league:'+c.id+':'+div;
    if(filter?.division!=='all'&&filter?.division!=null&&div!==Number(filter.division))continue;
    if(filter?.competition!=='all'&&filter?.competition!=null&&filter.competition!==key)continue;
    const list=E.table(s,c.id,div)||[],isMls=c.id==='usa'&&div===1,mls=s.competitions?.mls;
    const brazilLower=c.id==='bra'&&(div===3||div===4)?(div===3?s.braLower?.serieC:s.braLower?.serieD):null;
    const champ=brazilLower?(brazilLower.champion||null):isMls?(mls?.champion||null):list[0]?.id;
    const runner=brazilLower?(brazilLower.runnerUp||null):isMls?(mls?.runnerUp||mls?.cupRunner||null):list[1]?.id;
    add('league',c.id,div,key,champ,runner,v18322Scorers(s.competitionStats?.[key]));
   }
  }
  if(requiresCup){
   const key='cup:'+c.id,champ=s.cupWinners?.[c.id];
   if(champ&&(!filter||filter.competition==='all'||filter.competition===key))
    add('cup',c.id,0,key,champ,cupRunners.get(c.id),v18322Scorers(s.competitionStats?.[key]));
  }
 }
 if(requiresIntl&&(!filter||filter.country==='all'||filter.country==='international')){
  for(const [key,c] of Object.entries(s.competitions||{})){
   const id=String(c?.id||key);
   if(!c?.champion||id==='mls'||(filter?.competition!=='all'&&filter?.competition&&filter.competition!==id))continue;
   let runner=null;
   const finals=Object.entries(c.rounds||{}).filter(([phase])=>/final|^f$/i.test(phase)).flatMap(([,ties])=>Array.isArray(ties)?ties:[]);
   for(const tie of finals)if(tie?.winner===c.champion&&tie?.a&&tie?.b){runner=tie.a===c.champion?tie.b:tie.a;break;}
   if(!runner)for(const stage of s.schedule||[])for(const f of stage?.fixtures||[])
    if(f?.final&&f.competition===id&&(f.home===c.champion||f.away===c.champion))
     runner=f.home===c.champion?f.away:f.home;
   add('international','international',0,id,c.champion,runner,intlGoals.get(id)||[]);
  }
 }
 return rows;
}
function v18322CaptureSeason(s,year){
 if(!s?.seasonDone)return 0;
 const old=s.v18322Champions=Array.isArray(s.v18322Champions)?s.v18322Champions:[];
 const rows=v18322CollectSeason(s,year);
 const keys=new Set(rows.map(x=>x.year+'|'+x.competition));
 const merged=old.filter(x=>!keys.has(x.year+'|'+x.competition));
 s.v18322Champions=[...rows,...merged].sort((a,b)=>b.year-a.year||String(a.competition).localeCompare(String(b.competition)));
 v18322Preview.delete(s);return rows.length;
}

function v18322LegacyRows(s,filter=null){
 const result=[],teamId=id=>id?String(id):null;
 if(!filter||filter.kind==='all'||filter.kind==='league'||filter.kind==='cup'){
  for(const h of s.worldHistory||[]){
   const year=v18322N(h?.year);
   if(filter?.year!=='all'&&filter?.year!=null&&year!==Number(filter.year))continue;
   for(const row of h?.countries||[]){
    const country=String(row.country||'');
    if(!year||!country||(filter?.country!=='all'&&filter?.country&&filter.country!==country))continue;
    for(const [key,id,div,kind] of [
     ['league:'+country+':1',row.champion,1,'league'],
     ['league:'+country+':2',row.secondChampion,2,'league'],
     ['cup:'+country,row.cup,0,'cup']]){
     if(!id)continue;
     const item={year,kind,country,division:div,competition:key,
      champion:teamId(id),championName:v18322ClubName(s,id),
      runner:null,runnerName:'',scorers:[],legacy:true};
     if(v18322MatchRow(item,filter))result.push(item);
    }
   }
  }
 }
 if(!filter||filter.kind==='all'||filter.kind==='international'){
  if(!filter||filter.country==='all'||filter.country==='international')
   for(const h of s.internationalHistory||[])if(h?.champion){
    const item={year:v18322N(h.year),kind:'international',country:'international',division:0,
     competition:String(h.id||''),champion:teamId(h.champion),
     championName:v18322ClubName(s,h.champion),runner:null,runnerName:'',scorers:[],legacy:true};
    if(v18322MatchRow(item,filter))result.push(item);
   }
 }
 return result;
}
function v18322ChampionsRows(s,filter=null){
 if(!s)return [];
 const records=new Map();
 for(const row of v18322LegacyRows(s,filter))records.set(row.year+'|'+row.competition,row);
 for(const row of Array.isArray(s.v18322Champions)?s.v18322Champions:[])
  if(v18322MatchRow(row,filter))records.set(row.year+'|'+row.competition,row);
 if(s.seasonDone&&(!filter||filter.year==='all'||Number(filter.year)===Number(s.year))){
  const signature=[s.year,s.day,filter?.country||'all',filter?.kind||'all',
   filter?.division||'all',filter?.competition||'all'].join('|');
  let preview=v18322Preview.get(s);
  if(!preview||preview.signature!==signature){
   preview={signature,rows:v18322CollectSeason(s,Number(s.year),filter)};
   v18322Preview.set(s,preview);
  }
  for(const row of preview.rows)if(!records.has(row.year+'|'+row.competition))
   records.set(row.year+'|'+row.competition,row);
 }
 return [...records.values()].filter(x=>Number(x.year)>0)
  .sort((a,b)=>Number(b.year)-Number(a.year)||String(a.competition).localeCompare(String(b.competition),'pt-BR'));
}
function v18322InitClubFilters(){
 if(v18322ClubFilterState===state)return;
 const mode=String(v54CompetitionMode||'league');
 const country=mode==='international'?'international':
  (typeof selectedCountry==='function'?selectedCountry():E.human(state)?.country)||'all';
 v18322ClubFilters.country=country;
 v18322ClubFilters.kind=mode==='cup'?'cup':mode==='international'?'international':'league';
 v18322ClubFilters.division=mode==='league'?
  String(typeof selectedDivision==='function'?selectedDivision():E.human(state)?.division||1):'all';
 v18322ClubFilters.competition=mode==='international'?String(v4Competition||'all'):'all';
 v18322ClubFilters.year='all';
 v18322VisibleLimit=120;
 v18322ClubFilterState=state;
}
function v18322AvailableYears(s){
 const years=new Set();
 for(const row of s?.v18322Champions||[])if(v18322N(row?.year))years.add(v18322N(row.year));
 for(const rows of [s?.worldHistory,s?.internationalHistory,s?.v640National?.history])
  for(const row of rows||[])if(v18322N(row?.year))years.add(v18322N(row.year));
 if(s?.seasonDone)years.add(v18322N(s.year));
 return [...years].filter(y=>y>0).sort((a,b)=>b-a);
}
function v18322Option(value,label,current){
 return '<option value="'+v18322Esc(value)+'"'+(String(value)===String(current)?' selected':'')+'>'+v18322Esc(label)+'</option>';
}
function v18322ClubCrest(id,name=''){
 const t=id&&E.team(state,id);
 return t?'<span class="v18322-club">'+badge(t,'small')+'<button type="button" data-action="team" data-team="'+v18322Esc(id)+'" class="table-button">'+v18322Esc(t.name)+'</button></span>':
  '<span class="v18322-club">'+v18322Esc(name||'Sem registro')+'</span>';
}

function v18322ScorerCell(sc,national=false){
 if(!sc?.length)return '<span class="muted">Dados de artilharia indisponíveis neste save</span>';
 return '<div class="v18322-scorer-list">'+sc.map(x=>'<div class="v18322-scorer">'+
  (national?(typeof v640Flag==='function'?v640Flag(x.teamCode||''):''):
   (x.club&&E.team(state,x.club)?badge(E.team(state,x.club),'small'):''))+
  '<span>'+v18322Esc(x.name)+' <small>('+v18322N(x.goals)+' gols)</small></span></div>').join('')+'</div>';
}
function v18322HistoryPage(kind){
 if(kind==='national'){
  const root=state?.v640National||{},h=Array.isArray(root.history)?root.history:[];
  const f=v18322NationalFilters,teams=root.teams||{};
  const options=[...new Set(h.map(x=>String(x.id||'')))].filter(Boolean).sort();
  const nations=[...new Set(h.flatMap(x=>[String(x.champion||''),String(x.runnerUp||'')]))].filter(Boolean).sort();
  const rows=h.filter(x=>(f.conf==='all'||String(root.competitions?.[x.id]?.conf||teams[x.champion]?.conf||'')===f.conf)&&
   (f.competition==='all'||x.id===f.competition)&&
   (f.nation==='all'||x.champion===f.nation||x.runnerUp===f.nation)).sort((a,b)=>v18322N(b.year)-v18322N(a.year));
  const renderNation=(code)=>code?
   '<span class="v18322-club">'+(typeof v640Flag==='function'?v640Flag(code):'')+
   v18322Esc(teams[code]?.name||code)+'</span>':'<span class="muted">Sem registro</span>';
  return '<section class="v18322-panel"><h2>Histórico de títulos das Seleções</h2>'+
  '<p class="tiny muted">Edições concluídas · seleção campeã e vice · artilharia registrada. Competições de seleções não possuem divisões de clubes.</p>'+
  '<div class="v18322-filters"><label>Confederação<select data-v18322="n-conf">'+
  v18322Option('all','Todas',f.conf)+[...new Set(Object.values(teams).map(t=>t?.conf))].filter(Boolean).sort().map(c=>v18322Option(c,c,f.conf)).join('')+
  '</select></label><label>Seleção<select data-v18322="n-nation">'+v18322Option('all','Todas',f.nation)+nations.map(c=>v18322Option(c,teams[c]?.name||c,f.nation)).join('')+
  '</select></label><label>Campeonato<select data-v18322="n-competition">'+v18322Option('all','Todos',f.competition)+options.map(id=>v18322Option(id,root.competitions?.[id]?.name||h.find(x=>x.id===id)?.name||id,f.competition)).join('')+
  '</select></label></div>'+v18322Table(rows.map(x=>({year:x.year,competition:x.name||root.competitions?.[x.id]?.name||x.id,champ:renderNation(x.champion),
    runner:renderNation(x.runnerUp),scorer:v18322ScorerCell(x.scorer?[x.scorer]:v18322NationalScorers(root,x.year,x.id),true)})))+'</section>';
 }

 v18322InitClubFilters();
 const f=v18322ClubFilters,base=v18322ChampionsRows(state,{...f,competition:'all'});
 const filtered=f.competition==='all'?base:base.filter(x=>x.competition===f.competition);
 const competitions=[...new Set(base.map(x=>x.competition))].sort((a,b)=>v18322CompLabel(a).localeCompare(v18322CompLabel(b),'pt-BR'));
 if(f.competition!=='all'&&!competitions.includes(f.competition))competitions.push(f.competition);
 const years=v18322AvailableYears(state);
 const countries=[...(WorldCatalog.countries||[])].sort((a,b)=>String(a.name).localeCompare(String(b.name),'pt-BR'));
 const divisions=[...new Set([
  ...(state?.teams||[]).filter(t=>f.country==='all'||t.country===f.country).map(t=>Number(t.division)||1),
  ...(state?.v18322Champions||[]).filter(x=>x.kind==='league'&&(f.country==='all'||x.country===f.country)).map(x=>Number(x.division)||1)
 ])].filter(x=>x>0).sort((a,b)=>a-b);
 const visible=filtered.slice(0,v18322VisibleLimit);
 return '<section class="v18322-panel"><h2>Histórico de campeões</h2>'+
 '<p class="tiny muted">Títulos do mais recente ao mais antigo · apenas os resultados filtrados são exibidos. Dados antigos aparecem quando disponíveis.</p>'+
 '<div class="v18322-filters"><label>Ano<select data-v18322="c-year">'+v18322Option('all','Todos os anos',f.year)+
 years.map(y=>v18322Option(y,y,f.year)).join('')+'</select></label>'+
 '<label>País<select data-v18322="c-country">'+v18322Option('all','Todos os países',f.country)+
 countries.map(c=>v18322Option(c.id,c.name,f.country)).join('')+
 v18322Option('international','Internacionais / Mundial',f.country)+'</select></label>'+
 '<label>Campeonato<select data-v18322="c-kind">'+
 [['all','Todos'],['league','Ligas'],['cup','Copas'],['international','Internacionais']]
 .map(x=>v18322Option(x[0],x[1],f.kind)).join('')+'</select></label>'+
 '<label>Divisão<select data-v18322="c-division">'+v18322Option('all','Todas',f.division)+
 divisions.map(d=>v18322Option(d,d+'ª divisão',f.division)).join('')+'</select></label>'+
 '<label>Competição<select data-v18322="c-competition">'+v18322Option('all','Todas',f.competition)+
 competitions.map(id=>v18322Option(id,v18322CompLabel(id),f.competition)).join('')+
 '</select></label></div>'+v18322Table(visible.map(x=>({year:x.year,competition:v18322CompLabel(x.competition),
 champ:v18322ClubCrest(x.champion,x.championName),runner:v18322ClubCrest(x.runner,x.runnerName),
 scorer:v18322ScorerCell(x.scorers)})),filtered.length)+
 (filtered.length>v18322VisibleLimit?'<button class="btn small v18322-more" data-action="v18322-more">Exibir mais resultados</button>':'')+
 '</section>';
}

function v18322NationalScorers(root,year,key){
 const scores=v18322Scorers(root.playerStats?.[String(year)]?.[key]||{});
 return scores.map(x=>({...x,teamCode:root.playerStats?.[String(year)]?.[key]?.[x.id]?.teamCode||''}));
}
function v18322CompLabel(key){
 const pieces=String(key||'').split(':');
 if(pieces[0]==='league')return v18322CountryLabel(pieces[1])+' · '+pieces[2]+'ª divisão';
 if(pieces[0]==='cup')return WorldCatalog.countries.find(x=>x.id===pieces[1])?.cup||'Copa · '+v18322CountryLabel(pieces[1]);
 return state?.competitions?.[key]?.name||String(key||'Competição').toUpperCase();
}

function v18322Table(rows,total=rows.length){
 return '<div class="v18322-scroller"><table><thead><tr><th>Ano</th><th>Campeonato</th><th>Campeão</th><th>Vice-campeão</th><th>Artilheiro(s)</th></tr></thead><tbody>'+
 (rows.length?rows.map(x=>'<tr><td><b>'+v18322N(x.year)+'</b></td><td>'+v18322Esc(x.competition)+'</td><td>'+x.champ+'</td><td>'+x.runner+'</td><td>'+x.scorer+'</td></tr>').join(''):
 '<tr><td colspan="5" class="muted">Nenhuma edição concluída corresponde aos filtros escolhidos.</td></tr>')+
 '</tbody></table></div><div class="tiny muted v18322-foot">Exibindo '+rows.length+' de '+total+' edição(ões). Informações não preservadas nos saves antigos não são inventadas.</div>';
}
function v18322RetirementPage(){
 const s=state,rows=Array.isArray(s?.retirements)?s.retirements:[],
 years=[...new Set(rows.map(x=>v18322N(x.year)))].sort((a,b)=>b-a),
 shown=rows.filter(x=>v18322RetireYear==='all'||v18322N(x.year)===v18322N(v18322RetireYear));
 const senior=v18324EligibleVeterans();
 return '<section class="v18322-panel"><h2>Aposentadorias</h2><p class="tiny muted">Aposentadorias efetivadas na virada da temporada. Jogadores do seu clube podem anunciar a aposentadoria a partir de 35 anos; aos 40 anos ou mais também poderão se aposentar automaticamente.</p>'+
 '<div class="stats-grid"><div class="stat-card"><strong>'+rows.length+'</strong><span>Jogadores aposentados na carreira</span></div><div class="stat-card"><strong>'+rows.filter(x=>v18322N(x.year)===v18322N(s?.year)-1).length+'</strong><span>Na última virada</span></div></div>'+
 (senior.length?'<h3>Veteranos do seu clube</h3><div class="v18322-scroller"><table><thead><tr><th>Jogador</th><th>Idade</th><th>OVR</th><th>Decisão</th></tr></thead><tbody>'+
 senior.sort((a,b)=>v18322N(b.age)-v18322N(a.age)).map(p=>'<tr><td>'+v18322Esc(p.name)+'</td><td>'+p.age+'</td><td>'+E.overall(p)+'</td><td><button class="btn small" data-action="v18322-retire" data-player="'+v18322Esc(p.id)+'">'+
 (p.v579ManualRetire?'Cancelar aposentadoria':'Aposentar ao fim da temporada')+'</button></td></tr>').join('')+'</tbody></table></div>':
 '<p class="tiny muted">Não há jogadores elegíveis no seu clube. A aposentadoria manual fica disponível a partir dos 35 anos.</p>')+
 '<h3>Histórico de aposentadorias</h3><label class="v18322-year">Temporada<select data-v18322="retire-year">'+v18322Option('all','Todas',v18322RetireYear)+years.map(y=>v18322Option(y,y,v18322RetireYear)).join('')+'</select></label>'+
 '<div class="v18322-scroller"><table><thead><tr><th>Temporada</th><th>Jogador</th><th>Clube</th><th>Idade</th><th>OVR</th><th>Tipo</th></tr></thead><tbody>'+
 (shown.length?shown.slice(0,700).map(x=>'<tr><td>'+v18322N(x.year)+'</td><td>'+v18322Esc(x.name||x.id)+'</td><td>'+v18322ClubCrest(x.club,x.clubName)+'</td><td>'+v18322N(x.age)+'</td><td>'+v18322N(x.ovr)+'</td><td>'+(x.manual?'Anunciada':'Automática')+'</td></tr>').join(''):
 '<tr><td colspan="6" class="muted">Nenhuma aposentadoria registrada neste período.</td></tr>')+
 '</tbody></table></div></section>';
}


const v18322BaseCompetitionsPage=competitionsPage;
function v18322ClubSwitch(){
 return '<div class="v18322-switch" role="group" aria-label="Visualização das competições">'+
 '<button class="btn small '+(v18322ClubOpen?'':'primary')+
 '" data-action="v18322-toggle-clubs" data-mode="current">Temporada atual</button>'+
 '<button class="btn small '+(v18322ClubOpen?'primary':'')+
 '" data-action="v18322-toggle-clubs" data-mode="history">Histórico de campeões</button></div>';
}
competitionsPage=function(){
 const tabs=v18322ClubSwitch();
 if(v18322ClubOpen)return '<div class="v18322-history-screen">'+tabs+v18322HistoryPage('club')+'</div>';
 const current=v18322BaseCompetitionsPage();
 // Class "v605-label-free-toolbar" makes a literal class=...toolbar exact match fail.
 // Insert controls WITHIN the real toolbar; no separate row above the table.
 const toolbar=/<div class="v54-competition-toolbar(?:\s+[^"]*)?">/;
 if(toolbar.test(current))return current.replace(toolbar,open=>
  open.replace('v54-competition-toolbar',
  'v54-competition-toolbar v18322-docked-toolbar v18324-docked-toolbar')+tabs);
 // Fallback overlaid inside competition screen: never increase page height.
 return current.replace(/<div class="v54-competitions-screen([^"]*)">/,match=>
  match+'<div class="v18324-toolbar-fallback">'+tabs+'</div>');
};
const v18324BaseSquadPage=squadPage;
let v18324RetirementOpen=false,v18324RetirementState=null;
function v18324EligibleVeterans(){
 const club=state?.userEmployed?E.team(state,state.user):null;
 const ids=new Set([...(club?.roster||[]),...(club?.proReserve||[])]);
 return [...ids].map(id=>E.player(state,id)).filter(p=>v579ManualRetirementEligible(state,p));
}
squadPage=function(){
 if(!state?.userEmployed)return v18324BaseSquadPage();
 if(v18324RetirementState!==state){v18324RetirementState=state;v18324RetirementOpen=false;}
 const eligible=v18324EligibleVeterans();
 const info=eligible.length
  ?eligible.length+' jogador(es) com 35 anos ou mais podem anunciar aposentadoria'
  :'Disponível para jogadores do clube a partir de 35 anos';
 return '<div class="v18324-retirement-access">'+
  '<span><strong>Aposentadorias</strong><small>'+v18322Esc(info)+'</small></span>'+
  '<button class="btn small" type="button" data-action="v18324-open-retirements">'+
  (v18324RetirementOpen?'Voltar ao elenco':'Gerenciar aposentadorias')+
  (eligible.length&&!v18324RetirementOpen?' ('+eligible.length+')':'')+'</button>'+
  '</div>'+(v18324RetirementOpen?v18322RetirementPage():v18324BaseSquadPage());
};
const v18322BaseNationalPage=v640NationalPage;
v640NationalPage=function(){
 return '<div class="v18322-switch"><button class="btn small '+(v18322NationalOpen?'':'primary')+'" data-action="v18322-toggle-national" data-mode="current">Seleções</button>'+
 '<button class="btn small '+(v18322NationalOpen?'primary':'')+'" data-action="v18322-toggle-national" data-mode="history">Histórico de títulos</button></div>'+
 (v18322NationalOpen?v18322HistoryPage('national'):v18322BaseNationalPage());
};
const v18322BaseTransfersPage=transferActivityPage;
// Aposentadorias ficam somente em Elenco; Movimentacoes volta a ser
// exclusivamente o historico do mercado de transferencias.
transferActivityPage=function(){return v18322BaseTransfersPage();};
const v18322BaseAction=act;
act=function(el){
 const action=el?.dataset?.action;
 if(action==='v18322-toggle-clubs'){if(el.dataset.mode==='history')v18322InitClubFilters();v18322ClubOpen=el.dataset.mode==='history';render();return;}
 if(action==='v18322-more'){v18322VisibleLimit+=120;render();return;}
 if(action==='v18324-open-retirements'){v18324RetirementOpen=!v18324RetirementOpen;view='squad';render();return;}
 if(action==='v18322-toggle-national'){v18322NationalOpen=el.dataset.mode==='history';render();return;}

 if(action==='v18322-retire'){
  try{v18328OpenRetireModal(el.dataset.player);}
  catch(e){toast(e?.message||String(e),'warn');}
  return;
 }
 return v18322BaseAction(el);
};
document.addEventListener('change',e=>{
 const key=e.target?.dataset?.v18322;if(!key||!state)return;
 const value=e.target.value;

 if(key==='c-country'){v18322ClubFilters.country=value;v18322ClubFilters.competition='all';}
 else if(key==='c-kind'){v18322ClubFilters.kind=value;v18322ClubFilters.competition='all';}
 else if(key==='c-division')v18322ClubFilters.division=value;
 else if(key==='c-year')v18322ClubFilters.year=value;
 else if(key==='c-competition')v18322ClubFilters.competition=value;
 else if(key==='n-conf')v18322NationalFilters.conf=value;
 else if(key==='n-nation')v18322NationalFilters.nation=value;
 else if(key==='n-competition')v18322NationalFilters.competition=value;
 else if(key==='retire-year')v18322RetireYear=value;
 else return;
 if(key.startsWith('c-'))v18322VisibleLimit=120;

 render();
},true);
const v18322Style=document.createElement('style');v18322Style.id='v18322-history-style';
v18322Style.textContent="\n.v18322-switch{display:flex;align-items:center;gap:6px;flex-wrap:nowrap;padding:6px 0 10px}\n.v18322-switch .btn{white-space:nowrap}\n.v18322-docked-toolbar{grid-template-columns:minmax(245px,auto) minmax(150px,180px) minmax(170px,1fr) minmax(115px,.55fr)!important;gap:7px!important;align-items:end!important}\n.v18322-docked-toolbar>.v18322-switch{padding:0!important;min-width:0;align-self:end}\n.v18322-docked-toolbar>.v18322-switch .btn{font-size:10px!important;padding:7px 9px!important;min-height:31px;line-height:1.4}\n.v18322-panel{padding:14px;border:1px solid var(--line,#875251);background:var(--panel,#331716);border-radius:14px;min-width:0}\n.v18322-panel h2{font-size:19px;margin:0 0 5px}\n.v18322-panel h3{margin:18px 0 10px;font-size:16px}\n.v18322-filters{display:grid;grid-template-columns:repeat(5,minmax(110px,1fr));gap:8px;margin:12px 0}\n.v18322-filters label,.v18322-year{display:flex;flex-direction:column;gap:5px;font-size:11px;min-width:0}\n.v18322-filters select,.v18322-year select{width:100%;min-width:0;background:var(--panel2,#482221);border:1px solid var(--line,#82423c);color:inherit;border-radius:8px;padding:9px}\n.v18322-scroller{overflow:auto;max-height:calc(100dvh - 345px);min-height:190px;border:1px solid var(--line,#82423c);border-radius:10px}\n.v18322-scroller table{width:100%;min-width:820px;border-collapse:collapse;font-size:12px}\n.v18322-scroller th{position:sticky;top:0;background:var(--panel2,#482221);z-index:2}\n.v18322-scroller th,.v18322-scroller td{padding:8px 9px;border-bottom:1px solid var(--line,#82423c);text-align:left;vertical-align:middle;overflow-wrap:anywhere}\n.v18322-scroller th:first-child,.v18322-scroller td:first-child{width:6%}\n.v18322-scroller th:last-child,.v18322-scroller td:last-child{width:30%}\n.v18322-club{display:inline-flex;align-items:center;gap:6px;white-space:normal;max-width:100%}\n.v18322-scorer-list{display:flex;flex-direction:column;gap:5px;width:100%}\n.v18322-scorer{display:flex;align-items:center;gap:7px;min-width:0;white-space:normal}\n.v18322-scorer>span:last-child{min-width:0;overflow-wrap:anywhere}\n.v18322-scorer small{opacity:.75;white-space:nowrap}\n.v18322-foot{margin-top:8px}\n.v18322-more{margin-top:10px}\n.v18322-year{margin:8px 0 14px;max-width:180px}\n@media(max-width:1150px){.v18322-docked-toolbar{grid-template-columns:minmax(215px,auto) minmax(135px,160px) minmax(120px,1fr) minmax(100px,.6fr)!important}.v18322-docked-toolbar>.v18322-switch .btn{padding:6px!important;font-size:9px!important}}\n@media(max-width:850px){.v18322-filters{grid-template-columns:repeat(2,minmax(130px,1fr))}.v18322-docked-toolbar{grid-template-columns:repeat(2,minmax(0,1fr))!important}.v18322-docked-toolbar>.v18322-switch{grid-column:1/-1}}\n";
v18322Style.textContent += "\n/* 18.324: tabs are children of the existing toolbar, not a new block row. */\n@media(min-width:761px){\n body.v54-competitions-view .v54-competition-toolbar.v18324-docked-toolbar{\n  display:grid!important;\n  grid-template-columns:minmax(215px,auto) minmax(140px,175px) minmax(150px,1fr) minmax(105px,130px)!important;\n  align-items:center!important;gap:7px!important;\n  box-sizing:border-box!important;padding:3px 7px!important;\n  margin:0 0 4px!important;min-height:37px!important;max-height:44px!important;\n }\n .v18324-docked-toolbar>.v18322-switch{\n  display:flex!important;align-items:center!important;justify-content:flex-start!important;\n  gap:4px!important;margin:0!important;padding:0!important;\n  min-height:0!important;height:30px!important;flex-wrap:nowrap!important;\n }\n .v18324-docked-toolbar>.v18322-switch .btn{\n  min-height:28px!important;height:28px!important;max-height:28px!important;\n  padding:4px 7px!important;font-size:9.4px!important;line-height:1.1!important;\n  white-space:nowrap!important;\n }\n .v18324-docked-toolbar>.field{min-width:0!important;margin:0!important}\n .v18324-docked-toolbar>.field select{min-height:29px!important;height:29px!important}\n /* 20 positions fit at standard desktop heights, with one row per club. */\n body.v54-competitions-view .v604-comp-league-fit .v54-standings-table td{\n  height:clamp(23px,3.35dvh,31px)!important;min-height:0!important;\n  padding-top:1px!important;padding-bottom:1px!important;\n  line-height:1!important;font-size:10px!important;\n }\n body.v54-competitions-view .v604-comp-league-fit .v54-standings-table .v247-standing-club-box{\n  min-height:0!important;height:clamp(21px,2.9dvh,27px)!important;\n  max-height:27px!important;padding:1px 5px!important;box-sizing:border-box!important;\n }\n body.v54-competitions-view .v604-comp-league-fit .v54-standings-table .shield.small{\n  width:19px!important;height:21px!important;min-height:0!important;\n }\n body.v54-competitions-view .v604-comp-league-fit .v54-standings-table .table-button{\n  font-size:10px!important;line-height:1!important;\n }\n}\n.v54-competitions-screen{position:relative}\n.v18324-toolbar-fallback{position:absolute;top:1px;right:8px;z-index:3}\n.v18324-toolbar-fallback .v18322-switch{margin:0;padding:0}\n.v18324-retirement-access{display:flex;align-items:center;justify-content:space-between;gap:12px;\n margin:0 0 9px;padding:9px 12px;border:1px solid var(--line);border-radius:10px;\n background:var(--panel);min-width:0}\n.v18324-retirement-access span{display:flex;flex-direction:column;gap:3px;min-width:0}\n.v18324-retirement-access strong{font-size:12px}\n.v18324-retirement-access small{font-size:10px;opacity:.78}\n.v18324-retirement-access button{flex:0 0 auto}\n@media(min-width:761px) and (max-width:1150px){\n body.v54-competitions-view .v54-competition-toolbar.v18324-docked-toolbar{\n  grid-template-columns:minmax(175px,auto) minmax(120px,145px) minmax(125px,1fr) minmax(95px,115px)!important}\n .v18324-docked-toolbar>.v18322-switch .btn{font-size:8.3px!important;padding:4px 5px!important}\n}\n@media(max-width:760px){\n .v18324-docked-toolbar{display:grid!important;grid-template-columns:1fr 1fr!important}\n .v18324-docked-toolbar>.v18322-switch{grid-column:1/-1;padding:0!important}\n .v18324-retirement-access{flex-wrap:wrap}\n}\n";
document.head.appendChild(v18322Style);
window.GestorFC.championsRetire18322={
 version:'18.328',clubRows:()=>v18322ChampionsRows(state),
 nationalRows:()=>state?.v640National?.history||[],
 retirements:()=>state?.retirements||[],
 stats:()=>({saved:state?.v18322Champions?.length||0,national:state?.v640National?.history?.length||0,
  retirements:state?.retirements?.length||0})
};

/* FUTBR_MANUAL_ADVANCE_18326_START */
let v18326AdvanceBusy=false,v18326LastAction=null;
function v18326AdvanceVisual(busy){
 v18326AdvanceBusy=!!busy;
 try{document.body.classList.toggle('v18326-advance-busy',v18326AdvanceBusy);}catch(e){}
 try{document.querySelectorAll('.v555-advance-wrap [data-action="advance"],.v555-advance-wrap [data-action="v1891-nextmatch"]').forEach(b=>{b.disabled=!!busy;});}catch(e){}
}
function v18326HasOwnMatch(s){
 if(!s||s.seasonDone)return false;
 if(s.v640National?.userTeam){
  if(s.schedule?.[s.day]?.type==='national')v640PrepareNationalStage(s);
  const f=v640UserFixture(s);return !!(f&&!f.result);
 }
 const f=E.upcoming(s);return !!(f&&!f.result);
}
async function v18326ManualAdvance(el){
 const mode=el?.dataset?.action;
 if(!state)return v18326BaseAct(el);
 if(v18326AdvanceBusy||v53Sim?.active||v53Sim?.starting||v53Creating){toast('Um avanço já está em andamento. Aguarde a conclusão.','warn');return;}
 const before=state,oldDay=Number(state.day)||0,oldYear=Number(state.year)||0,from=view;
 v18326AdvanceVisual(true);
 v18326LastAction={mode,year:oldYear,day:oldDay,phase:'starting'};
 try{
  if(mode==='advance'&&(state.seasonDone||state.live))return await v18326BaseAct(el);
  if(mode==='v1891-nextmatch'&&(state.seasonDone||state.live))return await v1891AdvanceToNextMatch();
  if(state.vacation?.active){toast('Pause ou encerre as férias antes de avançar manualmente.','warn');return;}
  if(mode==='v1891-nextmatch'){
   if(state.v640National?.userTeam)return await v128AdvanceAsNationalCoach();
   return await v1891AdvanceToNextMatch();
  }
  if(mode!=='advance')return await v18326BaseAct(el);
  if(state.userEmployed===false&&!state.v640National?.userTeam){toast('Assuma um clube ou uma seleção antes de avançar.','warn');return;}
  // Preserve every human fixture: never simulate a match that the coach must play.
  if(v18326HasOwnMatch(state)){
   v18326LastAction.phase='match-ready';return await v18326BaseAct(el);
  }
  // One click means one world jornada. dayfast is the tested single-step Worker
  // path, avoiding the heavy generic 'day' and its separate old world baseline.
  v18326LastAction.phase='simulating-one-day';
  const result=await v53StartSimulation('dayfast');
  if(!state||state!==before){v18326LastAction.phase='reloaded';return result;}
  if(Number(state.day)<=oldDay&&Number(state.year)===oldYear&&!state.seasonDone)
   throw Error('A jornada não avançou. Nenhuma nova simulação foi iniciada para evitar duplicidade.');
  v18326LastAction={mode,year:Number(state.year)||oldYear,day:Number(state.day)||oldDay,steps:1,phase:'finished'};
  if(!document.hidden){render();if(view===from&&state.lastDay!=null&&typeof showDay==='function')showDay(state.lastDay);}
  return result;
 }catch(e){
  v18326LastAction={mode,year:oldYear,day:oldDay,phase:'error',error:String(e?.message||e)};
  toast('Falha no avanço: '+(e?.message||e),'error');
  try{if(state&&!document.hidden)render();}catch(_){}
 }finally{
  v18326AdvanceVisual(false);
  try{const root=document.querySelector('#app');if(root?.dataset?.v555Shell==='1')v555UpdateChrome(root);}catch(e){}
 }
}
// National careers also show the two commands, one-day vs. next national match.
const v18326BaseNationalChrome=v128UpdateNationalChrome;
v128UpdateNationalChrome=function(root){
 const result=v18326BaseNationalChrome(root);
 if(!root||!state?.v640National?.userTeam)return result;
 const adv=root.querySelector('.v555-advance-wrap');if(!adv)return result;
 const btn=adv.querySelector('[data-action="advance"]');
 if(btn){btn.innerHTML=icon('play')+' Avançar jornada';btn.disabled=!!(v18326AdvanceBusy||v53Sim?.active||v53Sim?.starting||v128NationalAdvanceBusy);}
 const canJump=!state.seasonDone&&!state.live&&!v18326HasOwnMatch(state);
 const old=adv.querySelector('[data-action="v1891-nextmatch"]');
 if(canJump&&!old){adv.insertAdjacentHTML('beforeend',button('v1891-nextmatch',icon('arrow')+' Avançar até a Próxima Partida','secondary v1891-nextmatch-button',v18326AdvanceBusy?'disabled':'title="Parar antes da próxima partida da seleção"'));}
 else if(!canJump&&old)old.remove();
 adv.querySelectorAll('button').forEach(b=>{if(v18326AdvanceBusy)b.disabled=true;});
 return result;
};
const v18326BaseAct=act;
act=function(el){
 const action=el?.dataset?.action;
 if(action==='advance'||action==='v1891-nextmatch')return v18326ManualAdvance(el);
 return v18326BaseAct(el);
};
const v18326CSS=document.createElement('style');v18326CSS.id='v18326-advance-style';
v18326CSS.textContent='body.v18326-advance-busy .v555-advance-wrap button{pointer-events:none!important;opacity:.56!important;cursor:wait!important}';
document.head.appendChild(v18326CSS);
window.GestorFC.manualAdvance18326={version:'18.326',status:()=>({busy:v18326AdvanceBusy,last:v18326LastAction}),
 dayMode:'dayfast-single-day',nextMode:'nextmatch-worker',nationalOneDay:true,serializesClicks:true,stopsBeforeOwnFixture:true};
/* FUTBR_MANUAL_ADVANCE_18326_END */


/* FUTBR_RETIRE_MODAL_18328_START */
let v18328RetireOverlay=null,v18328RetirePreviousFocus=null;
function v18328CloseRetireModal(){
 const old=v18328RetireOverlay;v18328RetireOverlay=null;
 document.removeEventListener('keydown',v18328RetireKeydown,true);
 if(old)old.remove();
 const prior=v18328RetirePreviousFocus;v18328RetirePreviousFocus=null;
 if(prior&&typeof prior.focus==='function'){
  try{prior.focus({preventScroll:true})}catch(e){try{prior.focus()}catch(_){}}
 }
}
function v18328RetireKeydown(e){
 if(!v18328RetireOverlay)return;
 if(e.key==='Escape'){e.preventDefault();e.stopPropagation();v18328CloseRetireModal();return;}
 if(e.key!=='Tab')return;
 const buttons=v18328RetireOverlay.querySelectorAll('button');
 if(!buttons.length)return;
 const first=buttons[0],last=buttons[buttons.length-1];
 if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}
 else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
}
function v18328OpenRetireModal(id){
 const s=state,p=E.player(s,id);
 if(!p||!v579ManualRetirementEligible(s,p))throw Error('Jogador n\u00e3o est\u00e1 eleg\u00edvel para aposentadoria.');
 const wasScheduled=!!p.v579ManualRetire;
 if(v18328RetireOverlay)v18328CloseRetireModal();
 v18328RetirePreviousFocus=document.activeElement;
 const overlay=document.createElement('div');
 overlay.className='v18328-retire-backdrop';
 overlay.setAttribute('data-v18328-modal','retirement');
 overlay.innerHTML=`
 <section class="v18328-retire-card" role="dialog" aria-modal="true"
   aria-labelledby="v18328-retire-heading" aria-describedby="v18328-retire-details">
   <div class="v18328-retire-top"><span class="v18328-retire-symbol" aria-hidden="true">&#9203;</span>
    <div><div class="v18328-retire-kicker">ELENCO / APOSENTADORIAS</div>
    <h2 id="v18328-retire-heading"></h2></div></div>
   <div class="v18328-retire-body"><div class="v18328-retire-player" data-v18328-player></div>
    <p id="v18328-retire-details" data-v18328-details></p></div>
   <div class="v18328-retire-footer">
    <button type="button" class="v18328-retire-btn v18328-retire-secondary" data-v18328-choice="cancel">Voltar</button>
    <button type="button" class="v18328-retire-btn v18328-retire-primary" data-v18328-choice="confirm"></button>
   </div>
 </section>`;
 overlay.querySelector('#v18328-retire-heading').textContent=wasScheduled?'Cancelar aposentadoria':'Confirmar aposentadoria';
 overlay.querySelector('[data-v18328-player]').textContent=p.name||'Jogador';
 overlay.querySelector('[data-v18328-details]').textContent=wasScheduled
  ?'Deseja cancelar a aposentadoria j\u00e1 anunciada? O jogador continuar\u00e1 no elenco.'
  :'Deseja confirmar a aposentadoria deste jogador ao fim da temporada? A confirma\u00e7\u00e3o ser\u00e1 registrada na carreira.';
 overlay.querySelector('[data-v18328-choice="confirm"]').textContent=wasScheduled?'Confirmar cancelamento':'Confirmar aposentadoria';
 let processing=false;
 overlay.addEventListener('click',e=>{
  if(v18328RetireOverlay!==overlay)return;
  if(e.target===overlay){v18328CloseRetireModal();return;}
  const choice=e.target?.closest?.('[data-v18328-choice]')?.dataset?.v18328Choice;
  if(choice==='cancel'){v18328CloseRetireModal();return;}
  if(choice!=='confirm'||processing)return;
  processing=true;
  try{
   const latest=E.player(state,id);
   if(state!==s||!latest||!v579ManualRetirementEligible(state,latest))
    throw Error('O elenco mudou. Abra novamente a confirma\u00e7\u00e3o.');
   if(!!latest.v579ManualRetire!==wasScheduled)
    throw Error('A decis\u00e3o do jogador foi alterada. Abra novamente a confirma\u00e7\u00e3o.');
   const marked=v579ToggleRetirement(state,id);
   v18328CloseRetireModal();
   try{
    const saved=persist();
    if(saved&&typeof saved.catch==='function')
     saved.catch(err=>toast('N\u00e3o foi poss\u00edvel salvar a aposentadoria: '+(err?.message||err),'warn'));
   }catch(err){toast('N\u00e3o foi poss\u00edvel salvar a aposentadoria: '+(err?.message||err),'warn');}
   render();
   toast(marked?'Aposentadoria anunciada.':'Aposentadoria cancelada.','success');
  }catch(err){v18328CloseRetireModal();toast(err?.message||String(err),'warn');}
 });
 v18328RetireOverlay=overlay;
 document.body.appendChild(overlay);
 document.addEventListener('keydown',v18328RetireKeydown,true);
 overlay.querySelector('[data-v18328-choice="confirm"]').focus();
}
const v18328RetireStyle=document.createElement('style');
v18328RetireStyle.id='v18328-retire-modal-style';
v18328RetireStyle.textContent=`
.v18328-retire-backdrop{position:fixed;inset:0;z-index:2147483000;display:flex;
 align-items:center;justify-content:center;box-sizing:border-box;padding:20px;
 background:rgba(16,5,8,.79);backdrop-filter:blur(3px)}
.v18328-retire-card{box-sizing:border-box;width:min(470px,100%);max-height:min(90dvh,700px);
 overflow:auto;border:1px solid #ad5b56;border-radius:16px;
 background:linear-gradient(145deg,#5d2324 0%,#3a181c 100%);color:#fff;
 box-shadow:0 22px 70px rgba(0,0,0,.55);font-family:inherit}
.v18328-retire-top{display:flex;align-items:center;gap:14px;padding:22px 24px 14px;
 border-bottom:1px solid rgba(255,255,255,.12)}
.v18328-retire-symbol{display:flex;justify-content:center;align-items:center;flex:none;
 width:42px;height:42px;border:1px solid rgba(255,255,255,.2);border-radius:12px;
 background:#702c31;font-size:23px}
.v18328-retire-kicker{font-size:10px;font-weight:700;letter-spacing:.12em;color:#f6aaa5}
.v18328-retire-top h2{margin:4px 0 0;font-size:20px;font-weight:800;line-height:1.25;color:#fff}
.v18328-retire-body{padding:19px 24px 22px}
.v18328-retire-player{font-size:17px;font-weight:800;margin-bottom:11px}
.v18328-retire-body p{margin:0;font-size:13px;line-height:1.65;color:#edcecd}
.v18328-retire-footer{display:flex;justify-content:flex-end;flex-wrap:wrap;gap:10px;
 padding:15px 24px 22px;border-top:1px solid rgba(255,255,255,.10)}
.v18328-retire-btn{appearance:none;border-radius:9px;padding:11px 15px;min-height:39px;
 cursor:pointer;font:700 12px inherit;font-family:inherit;transition:filter .15s ease,transform .15s ease}
.v18328-retire-btn:hover{filter:brightness(1.1)}
.v18328-retire-btn:focus-visible{outline:2px solid #ffcbc4;outline-offset:3px}
.v18328-retire-secondary{color:#fff;border:1px solid #ad5b56;background:#4d2326}
.v18328-retire-primary{color:#211010;border:1px solid #ed585d;background:#ed5057}
@media(max-width:540px){.v18328-retire-top{padding:18px 17px 14px}
 .v18328-retire-body{padding:17px}.v18328-retire-footer{padding:14px 17px 18px}
 .v18328-retire-btn{flex:1 1 auto}.v18328-retire-top h2{font-size:18px}}
`;
document.head.appendChild(v18328RetireStyle);
window.GestorFC.retirementModal18328={version:'18.328',open:v18328OpenRetireModal,
 close:v18328CloseRetireModal,status:()=>({open:!!v18328RetireOverlay,source:'in-game-modal',nativeConfirm:false})};
/* FUTBR_RETIRE_MODAL_18328_END */

/* FUTBR_CHAMPIONS_RETIREMENT_18322_END */
"""

def replace_once(s,old,new,description):
    n=s.count(old)
    if n!=1:raise RuntimeError(f'{description}: esperava 1 ancora; encontrou {n}')
    return s.replace(old,new,1)

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: feature_champions_retirement_18322.py <project-dir>')
    project=Path(sys.argv[1]);file=project/'src'/'index.html'
    html=file.read_text(encoding='utf-8')
    if MARK in html:return
    for required in ['FUTBR_RANK_CORE_18320_START','FUTBR_RANK_UI_18321','function v91FastNextSeasonCore(s)','function finishTournament(s,c,winner,runner)','const v579BaseShowPlayer=showPlayer']:
        if required not in html:raise RuntimeError('Expected base missing: '+required)
    html=replace_once(html,
      "const rankFresh=false; // final titles/movements",
      "v18322CaptureSeason(s,oldYear);\n const rankFresh=false; // final titles/movements",
      'Arquivar todas as divisoes antes da virada')
    # Players of the human club may choose retirement from 35, and can retire
    # automatically at 40+. The former condition prevented all user-club retirements.
    html=replace_once(html,
      "protectedByUser=!!(s.userEmployed&&clubBefore===s.user);",
      "protectedByUser=!!(s.userEmployed&&clubBefore===s.user&&Number(p.age)<39);",
      'Protecao de veteranos do time do usuario')
    html=replace_once(html,
      "auto=!!(E.shouldAutoRetire549&&E.shouldAutoRetire549(s,p,snap,chance));",
      "auto=clubBefore===s.user?(Number(p.age)>=40&&E.rng(s)<chance):!!(E.shouldAutoRetire549&&E.shouldAutoRetire549(s,p,snap,chance));",
      'Aposentadoria automatica de veteranos de 40 anos')
    html=replace_once(html,
      "v91Stats.retired=retired.size;\n t=v91Now();",
      "v91Stats.retired=retired.size;\n if(retired.size)try{E.news(s,'Aposentadorias',retired.size+' jogadores encerraram a carreira na virada para '+s.year+'. Consulte Elenco > Gerenciar aposentadorias.','info');}catch(e){}\n t=v91Now();",
      'Aviso de aposentadorias na nova temporada')
    # Preserve all national tournament editions and the scorer at the final.
    national_legacy="root.history=root.history.slice(0,80);"
    if html.count(national_legacy)!=2:
        raise RuntimeError('Esperadas duas rotinas de finais das selecoes, encontrado '+str(html.count(national_legacy)))
    national_archive=(
      "const nationalStats=Object.values(root.playerStats?.[String(s.year)]?.[c.id]||{})"
      ".filter(x=>Number(x?.goals)>0)"
      ".sort((a,b)=>Number(b.goals)-Number(a.goals)||Number(b.assists||0)-Number(a.assists||0));"
      "if(nationalStats.length){const p=nationalStats[0];root.history[0].scorer="
      "{id:p.id,name:p.name,teamCode:p.teamCode,goals:Number(p.goals)||0};}"
    )
    html=html.replace(national_legacy,national_archive)
    # Install into the same lexical scope as career functions: the v202-prewarm
    # script is a separate IIFE and cannot see or override these functions.
    anchor="window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';\n})();\n</script>"
    html=replace_once(html,anchor,"\n"+UI+"\n"+anchor,
      'Inserir historico e captura no escopo original da carreira')
    file.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,'seasonWinnersPersistent':True,'noHistoryTruncation':True,
      'domesticDivisions':True,'continentalAndNational':True,'scorersWithActualStatistics':True,
      'retirementAutomaticAge40':True,'manualAge35':True,
      'retirementHistoryVisible':True,'noRetroactiveFabricatedStats':True,'yearFilter':True,'lightweightDefaultView':True,'scorerFallback':True,'compactTableToolbar':True,'realToolbarDocking':True,'twentyVisibleClubs':True,'retirementAccessInSquad':True,'retirementOnlyInSquad':True,'manualAdvanceSingleDay':True,'manualAdvanceStopBeforeMatch':True,'nationalAdvanceButtons':True,'inGameRetirementModal':True,'noNativeRetirementConfirm':True}
    (project/'champions-retirement-18322-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
