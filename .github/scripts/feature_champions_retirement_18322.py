from pathlib import Path
import json
import sys

VERSION = '18.322'
MARK = 'FUTBR_CHAMPIONS_RETIREMENT_18322'
UI = r"""
/* FUTBR_CHAMPIONS_RETIREMENT_18322 */
let v18322ClubOpen=false,v18322NationalOpen=false,v18322TransferTab='transfers';
const v18322ClubFilters={country:'all',kind:'all',division:'all',competition:'all'};
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
 return scored.filter(x=>v18322N(x.goals)===max).slice(0,4).map(r=>{
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
 const comps=new Map();
 for(const stage of s.schedule||[])for(const f of stage?.fixtures||[]){
  if(!f?.competition||!f.result)continue;
  const id=String(f.competition),a=comps.get(id)||{goals:new Map(),expected:0,counted:0};
  const hg=v18322N(f.result.home),ag=v18322N(f.result.away);
  a.expected+=Math.max(0,hg)+Math.max(0,ag);
  for(const ev of f.result.events||[]){
   if(ev?.type!=='goal'||!ev.pid)continue;
   const club=Number(ev.side)===0?f.home:f.away,player=s.players?.[ev.pid];
   const key=String(ev.pid),row=a.goals.get(key)||{id:key,name:player?.name||ev.name||'Jogador',club,clubName:v18322ClubName(s,club),goals:0};
   row.goals++;a.counted++;a.goals.set(key,row);
  }
  comps.set(id,a);
 }
 const result=new Map();
 for(const [id,a] of comps){
  if(a.counted<a.expected||!a.counted){result.set(id,[]);continue;}
  result.set(id,v18322Scorers(Object.fromEntries(a.goals)));
 }
 return result;
}
function v18322CollectSeason(s,year){
 if(!s?.teams?.length)return [];
 const rows=[],cupRunners=v18322CupRunners(s),intlGoals=v18322IntlScorers(s);
 const add=(kind,country,division,competition,champion,runner,scorers)=>{
  if(!champion)return;
  rows.push({year,kind,country:country||'',division:Number(division)||0,competition:String(competition),
   champion:String(champion),championName:v18322ClubName(s,champion),
   runner:runner?String(runner):null,runnerName:runner?v18322ClubName(s,runner):'',
   scorers:Array.isArray(scorers)?scorers:[]});
 };
 const divisions=new Map();
 for(const t of s.teams||[]){
  if(!t?.country)continue;
  if(!divisions.has(t.country))divisions.set(t.country,new Set());
  divisions.get(t.country).add(v18322N(t.division)||1);
 }
 for(const c of WorldCatalog.countries){
  for(const div of [...(divisions.get(c.id)||[])].sort((a,b)=>a-b)){
   const list=E.table(s,c.id,div)||[];
   const isMls=c.id==='usa'&&div===1,mls=s.competitions?.mls;
   const brazilLower=c.id==='bra'&&(div===3||div===4)?(div===3?s.braLower?.serieC:s.braLower?.serieD):null;
   // Nas Séries C e D, o vencedor da final prevalece sobre o líder da classificação.
   const champ=brazilLower?(brazilLower.champion||null):isMls?(mls?.champion||null):list[0]?.id;
   const runner=brazilLower?(brazilLower.runnerUp||null):isMls?(mls?.runnerUp||mls?.cupRunner||null):list[1]?.id;
   add('league',c.id,div,'league:'+c.id+':'+div,champ,runner,v18322Scorers(s.competitionStats?.['league:'+c.id+':'+div]));
  }
  const champ=s.cupWinners?.[c.id];
  if(champ)add('cup',c.id,0,'cup:'+c.id,champ,cupRunners.get(c.id),v18322Scorers(s.competitionStats?.['cup:'+c.id]));
 }
 for(const c of Object.values(s.competitions||{})){
  if(!c?.champion||c.id==='mls')continue;
  let runner=null;
  const finals=Object.entries(c.rounds||{}).filter(([key])=>/final|^f$/i.test(key)).flatMap(([,ties])=>Array.isArray(ties)?ties:[]);
  for(const t of finals)if(t?.winner===c.champion&&t?.a&&t?.b){runner=t.a===c.champion?t.b:t.a;break;}
  if(!runner)for(const stage of s.schedule||[])for(const f of stage?.fixtures||[])
   if(f?.final&&f.competition===c.id&&(f.home===c.champion||f.away===c.champion)){runner=f.home===c.champion?f.away:f.home;}
  add('international','international',0,c.id,c.champion,runner,intlGoals.get(String(c.id))||[]);
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
function v18322LegacyRows(s){
 const result=[],teamId=(id)=>id?String(id):null;
 for(const h of s.worldHistory||[])for(const row of h?.countries||[]){
  const country=String(row.country||''),year=v18322N(h.year);
  if(!year||!country)continue;
  for(const [key,id,div,kind] of [
   ['league:'+country+':1',row.champion,1,'league'],
   ['league:'+country+':2',row.secondChampion,2,'league'],
   ['cup:'+country,row.cup,0,'cup']]){
   if(!id)continue;
   result.push({year,kind,country,division:div,competition:key,
    champion:teamId(id),championName:v18322ClubName(s,id),
    runner:null,runnerName:'',scorers:[],legacy:true});
  }
 }
 for(const h of s.internationalHistory||[])if(h?.champion){
  result.push({year:v18322N(h.year),kind:'international',country:'international',division:0,
   competition:String(h.id||''),champion:teamId(h.champion),
   championName:v18322ClubName(s,h.champion),runner:null,runnerName:'',scorers:[],legacy:true});
 }
 return result;
}
function v18322ChampionsRows(s){
 if(!s)return [];
 const old=Array.isArray(s.v18322Champions)?s.v18322Champions:[];
 const all=new Map();
 for(const x of v18322LegacyRows(s))all.set(x.year+'|'+x.competition,x);
 for(const x of old)all.set(x.year+'|'+x.competition,x);
 if(s.seasonDone){
  let preview=v18322Preview.get(s);
  if(!preview||preview.year!==s.year||preview.day!==s.day){
   preview={year:s.year,day:s.day,rows:v18322CollectSeason(s,Number(s.year))};
   v18322Preview.set(s,preview);
  }
  for(const x of preview.rows)if(!all.has(x.year+'|'+x.competition))all.set(x.year+'|'+x.competition,x);
 }
 return [...all.values()].filter(x=>x.year>0).sort((a,b)=>b.year-a.year||String(a.competition).localeCompare(String(b.competition),'pt-BR'));
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
 if(!sc?.length)return '<span class="muted">Sem registro</span>';
 return sc.map(x=>'<span class="v18322-scorer">'+
 (national?(typeof v640Flag==='function'?v640Flag(x.teamCode||''):''):
  (x.club&&E.team(state,x.club)?badge(E.team(state,x.club),'small'):''))+
 '<span>'+v18322Esc(x.name)+' <small>('+v18322N(x.goals)+' gols)</small></span></span>').join(' ');
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
 const f=v18322ClubFilters,all=v18322ChampionsRows(state);
 const countries=[...new Set(all.map(x=>x.country).filter(x=>x!=='international'))].sort((a,b)=>v18322CountryLabel(a).localeCompare(v18322CountryLabel(b),'pt-BR'));
 const filtered=all.filter(x=>(f.country==='all'||x.country===f.country)&&
 (f.kind==='all'||x.kind===f.kind)&&
 (f.division==='all'||x.kind!=='league'||x.division===Number(f.division))&&
 (f.competition==='all'||x.competition===f.competition));
 const competitions=[...new Set(all.filter(x=>f.country==='all'||x.country===f.country).map(x=>x.competition))].sort();
 const divisions=[...new Set(all.filter(x=>x.kind==='league'&&(f.country==='all'||x.country===f.country)).map(x=>x.division))].sort((a,b)=>a-b);
 return '<section class="v18322-panel"><h2>Histórico de campeões</h2>'+
 '<p class="tiny muted">Do título mais recente ao mais antigo. Os dados anteriores à atualização aparecem quando disponíveis no save.</p>'+
 '<div class="v18322-filters"><label>País<select data-v18322="c-country">'+v18322Option('all','Todos os países',f.country)+countries.map(c=>v18322Option(c,v18322CountryLabel(c),f.country)).join('')+v18322Option('international','Internacionais / Mundial',f.country)+'</select></label>'+
 '<label>Campeonato<select data-v18322="c-kind">'+
 [['all','Todos'],['league','Ligas'],['cup','Copas'],['international','Internacionais']].map(x=>v18322Option(x[0],x[1],f.kind)).join('')+
 '</select></label><label>Divisão<select data-v18322="c-division">'+v18322Option('all','Todas',f.division)+divisions.map(d=>v18322Option(d,d+'ª divisão',f.division)).join('')+'</select></label>'+
 '<label>Competição<select data-v18322="c-competition">'+v18322Option('all','Todas',f.competition)+competitions.map(id=>v18322Option(id,v18322CompLabel(id),f.competition)).join('')+
 '</select></label></div>'+v18322Table(filtered.map(x=>({year:x.year,competition:v18322CompLabel(x.competition),
  champ:v18322ClubCrest(x.champion,x.championName),runner:v18322ClubCrest(x.runner,x.runnerName),
  scorer:v18322ScorerCell(x.scorers)})))+'</section>';
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
function v18322Table(rows){
 return '<div class="v18322-scroller"><table><thead><tr><th>Ano</th><th>Campeonato</th><th>Campeão</th><th>Vice-campeão</th><th>Artilheiro(s)</th></tr></thead><tbody>'+
 (rows.length?rows.map(x=>'<tr><td><b>'+v18322N(x.year)+'</b></td><td>'+v18322Esc(x.competition)+'</td><td>'+x.champ+'</td><td>'+x.runner+'</td><td>'+x.scorer+'</td></tr>').join(''):
 '<tr><td colspan="5" class="muted">Ainda não existem edições concluídas para estes filtros.</td></tr>')+
 '</tbody></table></div><div class="tiny muted v18322-foot">'+rows.length+' edição(ões) encontradas · “Sem registro” indica dado não preservado no histórico antigo.</div>';
}
function v18322RetirementPage(){
 const s=state,rows=Array.isArray(s?.retirements)?s.retirements:[],
 years=[...new Set(rows.map(x=>v18322N(x.year)))].sort((a,b)=>b-a),
 shown=rows.filter(x=>v18322RetireYear==='all'||v18322N(x.year)===v18322N(v18322RetireYear));
 const team=s?.userEmployed?E.team(s,s.user):null,
 senior=[...(team?.roster||[]),...(team?.proReserve||[])].map(id=>s?.players?.[id]).filter(p=>p&&p.squad!=='youth'&&v18322N(p.age)>=35);
 return '<section class="v18322-panel"><h2>Aposentadorias</h2><p class="tiny muted">Aposentadorias efetivadas na virada da temporada. Jogadores do seu clube podem anunciar a aposentadoria a partir de 35 anos; aos 40 anos ou mais também poderão se aposentar automaticamente.</p>'+
 '<div class="stats-grid"><div class="stat-card"><strong>'+rows.length+'</strong><span>Jogadores aposentados na carreira</span></div><div class="stat-card"><strong>'+rows.filter(x=>v18322N(x.year)===v18322N(s?.year)-1).length+'</strong><span>Na última virada</span></div></div>'+
 (senior.length?'<h3>Veteranos do seu clube</h3><div class="v18322-scroller"><table><thead><tr><th>Jogador</th><th>Idade</th><th>OVR</th><th>Decisão</th></tr></thead><tbody>'+
 senior.sort((a,b)=>v18322N(b.age)-v18322N(a.age)).map(p=>'<tr><td>'+v18322Esc(p.name)+'</td><td>'+p.age+'</td><td>'+E.overall(p)+'</td><td><button class="btn small" data-action="v18322-retire" data-player="'+v18322Esc(p.id)+'">'+
 (p.v579ManualRetire?'Cancelar aposentadoria':'Aposentar ao fim da temporada')+'</button></td></tr>').join('')+'</tbody></table></div>':
 '<p class="tiny muted">Não há jogadores do seu clube com 35 anos ou mais disponíveis para aposentadoria manual.</p>')+
 '<h3>Histórico de aposentadorias</h3><label class="v18322-year">Temporada<select data-v18322="retire-year">'+v18322Option('all','Todas',v18322RetireYear)+years.map(y=>v18322Option(y,y,v18322RetireYear)).join('')+'</select></label>'+
 '<div class="v18322-scroller"><table><thead><tr><th>Temporada</th><th>Jogador</th><th>Clube</th><th>Idade</th><th>OVR</th><th>Tipo</th></tr></thead><tbody>'+
 (shown.length?shown.slice(0,700).map(x=>'<tr><td>'+v18322N(x.year)+'</td><td>'+v18322Esc(x.name||x.id)+'</td><td>'+v18322ClubCrest(x.club,x.clubName)+'</td><td>'+v18322N(x.age)+'</td><td>'+v18322N(x.ovr)+'</td><td>'+(x.manual?'Anunciada':'Automática')+'</td></tr>').join(''):
 '<tr><td colspan="6" class="muted">Nenhuma aposentadoria registrada neste período.</td></tr>')+
 '</tbody></table></div></section>';
}
const v18322BaseCompetitionsPage=competitionsPage;
competitionsPage=function(){
 return '<div class="v18322-switch"><button class="btn small '+(v18322ClubOpen?'':'primary')+'" data-action="v18322-toggle-clubs" data-mode="current">Temporada atual</button>'+
 '<button class="btn small '+(v18322ClubOpen?'primary':'')+'" data-action="v18322-toggle-clubs" data-mode="history">Histórico de campeões</button></div>'+
 (v18322ClubOpen?v18322HistoryPage('club'):v18322BaseCompetitionsPage());
};
const v18322BaseNationalPage=v640NationalPage;
v640NationalPage=function(){
 return '<div class="v18322-switch"><button class="btn small '+(v18322NationalOpen?'':'primary')+'" data-action="v18322-toggle-national" data-mode="current">Seleções</button>'+
 '<button class="btn small '+(v18322NationalOpen?'primary':'')+'" data-action="v18322-toggle-national" data-mode="history">Histórico de títulos</button></div>'+
 (v18322NationalOpen?v18322HistoryPage('national'):v18322BaseNationalPage());
};
const v18322BaseTransfersPage=transferActivityPage;
transferActivityPage=function(){
 return '<div class="v18322-switch"><button class="btn small '+(v18322TransferTab==='transfers'?'primary':'')+'" data-action="v18322-transfer-tab" data-tab="transfers">Transferências</button>'+
 '<button class="btn small '+(v18322TransferTab==='retirements'?'primary':'')+'" data-action="v18322-transfer-tab" data-tab="retirements">Aposentadorias</button></div>'+
 (v18322TransferTab==='retirements'?v18322RetirementPage():v18322BaseTransfersPage());
};
const v18322BaseAction=act;
act=function(el){
 const action=el?.dataset?.action;
 if(action==='v18322-toggle-clubs'){v18322ClubOpen=el.dataset.mode==='history';render();return;}
 if(action==='v18322-toggle-national'){v18322NationalOpen=el.dataset.mode==='history';render();return;}
 if(action==='v18322-transfer-tab'){v18322TransferTab=el.dataset.tab==='retirements'?'retirements':'transfers';render();return;}
 if(action==='v18322-retire'){
  try{
   const p=E.player(state,el.dataset.player);if(!p)throw Error('Jogador indisponível.');
   if(!p.v579ManualRetire&&!confirm('Confirmar aposentadoria de '+p.name+' ao fim da temporada?'))return;
   const marked=v579ToggleRetirement(state,p.id);persist();render();
   toast(marked?'Aposentadoria anunciada.':'Aposentadoria cancelada.','success');
  }catch(e){toast(e?.message||String(e),'warn');}return;
 }
 return v18322BaseAction(el);
};
document.addEventListener('change',e=>{
 const key=e.target?.dataset?.v18322;if(!key||!state)return;
 const value=e.target.value;
 if(key==='c-country'){v18322ClubFilters.country=value;v18322ClubFilters.competition='all';v18322ClubFilters.division='all';}
 else if(key==='c-kind'){v18322ClubFilters.kind=value;v18322ClubFilters.competition='all';}
 else if(key==='c-division')v18322ClubFilters.division=value;
 else if(key==='c-competition')v18322ClubFilters.competition=value;
 else if(key==='n-conf')v18322NationalFilters.conf=value;
 else if(key==='n-nation')v18322NationalFilters.nation=value;
 else if(key==='n-competition')v18322NationalFilters.competition=value;
 else if(key==='retire-year')v18322RetireYear=value;
 else return;
 render();
},true);
const v18322Style=document.createElement('style');v18322Style.id='v18322-history-style';
v18322Style.textContent='.v18322-switch{display:flex;gap:8px;flex-wrap:wrap;padding:6px 0 12px}.v18322-panel{padding:16px;border:1px solid var(--line,#875251);background:var(--panel,#331716);border-radius:16px}.v18322-panel h2{font-size:20px;margin:0 0 8px}.v18322-panel h3{margin:18px 0 10px;font-size:16px}.v18322-filters{display:grid;grid-template-columns:repeat(4,minmax(130px,1fr));gap:10px;margin:14px 0}.v18322-filters label,.v18322-year{display:flex;flex-direction:column;gap:5px;font-size:11px;letter-spacing:.025em}.v18322-filters select,.v18322-year select{width:100%;background:var(--panel2,#482221);border:1px solid var(--line,#82423c);color:inherit;border-radius:8px;padding:9px}.v18322-scroller{overflow:auto;max-height:65vh;border:1px solid var(--line,#82423c);border-radius:10px}.v18322-scroller table{width:100%;min-width:790px;border-collapse:collapse;font-size:12px}.v18322-scroller th{position:sticky;top:0;background:var(--panel2,#482221);z-index:2}.v18322-scroller th,.v18322-scroller td{padding:9px 10px;border-bottom:1px solid var(--line,#82423c);text-align:left;vertical-align:middle}.v18322-club,.v18322-scorer{display:inline-flex;align-items:center;gap:7px;white-space:nowrap}.v18322-scorer{margin:2px 6px 2px 0}.v18322-scorer small{opacity:.7}.v18322-foot{margin-top:8px}.v18322-year{margin:8px 0 14px;max-width:180px}@media(max-width:950px){.v18322-filters{grid-template-columns:repeat(2,minmax(130px,1fr))}}';
document.head.appendChild(v18322Style);
window.GestorFC.championsRetire18322={
 version:'18.322',clubRows:()=>v18322ChampionsRows(state),
 nationalRows:()=>state?.v640National?.history||[],
 retirements:()=>state?.retirements||[],
 stats:()=>({saved:state?.v18322Champions?.length||0,national:state?.v640National?.history?.length||0,
  retirements:state?.retirements?.length||0})
};
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
      "v91Stats.retired=retired.size;\n if(retired.size)try{E.news(s,'Aposentadorias',retired.size+' jogadores encerraram a carreira na virada para '+s.year+'. Consulte Movimentações > Aposentadorias.','info');}catch(e){}\n t=v91Now();",
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
    anchor="\n})();\n</script>\n<script id=\"v202-meta\">"
    html=replace_once(html,anchor,"\n"+UI+"\n})();\n</script>\n<script id=\"v202-meta\">",
      'Funcoes no escopo original para competir e selecoes')
    file.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,'seasonWinnersPersistent':True,'noHistoryTruncation':True,
      'domesticDivisions':True,'continentalAndNational':True,'scorersWithActualStatistics':True,
      'retirementAutomaticAge40':True,'manualAge35':True,
      'retirementHistoryVisible':True,'noRetroactiveFabricatedStats':True}
    (project/'champions-retirement-18322-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
