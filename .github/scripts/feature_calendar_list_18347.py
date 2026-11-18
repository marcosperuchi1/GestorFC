from __future__ import annotations
import json
import sys
from pathlib import Path

MARK='FUTBR_CALENDAR_LIST_18347'
JS=r"""
/* FUTBR_CALENDAR_LIST_18347 */
(function(){
 'use strict';
 let listScope='next';
 if(!NAV.some(item=>item[0]==='calendar')){
  const index=NAV.findIndex(item=>item[0]==='competitions');
  NAV.splice(index>=0?index:3,0,['calendar','calendar','Calendário de jogos']);
 }
 function safe(value){return esc(String(value==null?'':value));}
 function n(value){const v=Number(value);return Number.isFinite(v)?v:0;}
 function label(s,stage,f,home){
  const key=String(f.competition||'');
  if(String(f.v661Brazil||'')==='C')return 'Campeonato Brasileiro · Série C';
  if(String(f.v661Brazil||'')==='D')return 'Campeonato Brasileiro · Série D';
  if(s.competitions?.[key]?.name)return String(s.competitions[key].name);
  if(key==='mls')return 'Major League Soccer';
  if(stage.type==='cup'||f.cupTieKey){
   try{const country=E.country(f.country||home.country);if(country?.cup)return country.cup;}catch(e){}
   return 'Copa nacional';
  }
  if(stage.type==='league'||f.division){
   const country=String(f.country||home.country||'');
   const division=n(f.division)||n(home.division)||1;
   if(country==='bra')return 'Campeonato Brasileiro · '+(['','Série A','Série B','Série C','Série D'][division]||division+'ª divisão');
   try{return divisionLabel(country,division);}catch(e){return division+'ª divisão';}
  }
  return key||String(stage.label||'Competição');
 }
 function phase(stage,f,i){
  const map={first:'Primeira fase',quad:'Quadrangular',qf:'Quartas de final',sf:'Semifinal',final:'Final',access:'Acesso',r16:'Oitavas'};
  const p=String(f.v661Phase||f.phase||'');
  let text=map[p]||p.replace(/[_-]/g,' ')||(stage.type==='league'&&n(stage.round)?'Rodada '+n(stage.round):String(stage.label||'Jornada '+(i+1)));
  const leg=n(f.v661Leg||f.leg);
  if(leg===1||leg===2)text+=' · '+leg+'º jogo';
  return text;
 }
 function fixtures(s){
  const out=[];
  if(!s?.userEmployed||!s.user)return out;
  const club=String(s.user);
  for(let day=0;day<(s.schedule||[]).length;day++){
   const stage=s.schedule[day];
   for(const f of stage?.fixtures||[]){
    if(!f||(String(f.home)!==club&&String(f.away)!==club))continue;
    const home=E.team(s,f.home),away=E.team(s,f.away);
    if(!home||!away)continue;
    out.push({day,stage,f,home,away,opponent:String(f.home)===club?away:home,atHome:String(f.home)===club,played:!!f.result});
   }
  }
  return out;
 }
 function info(s,opponent,cache){
  const ids=(opponent?.lineup||[]).filter(Boolean);
  const roster=ids.length>=9?ids:(opponent?.roster||[]);
  const ovr=[];
  for(const id of roster){
   const p=s.players?.[id];if(!p)continue;
   try{const x=Number(E.overall(p));if(Number.isFinite(x))ovr.push(x);}catch(e){}
  }
  if(ids.length<9)ovr.sort((a,b)=>b-a);
  const eleven=ovr.slice(0,11);
  const power=eleven.length?String(Math.round(eleven.reduce((a,b)=>a+b,0)/eleven.length)):'—';
  const scope=String(opponent.country||'')+':'+String(opponent.division||'');
  if(!cache.has(scope)){
   let list=[];
   try{list=(E.table(s,opponent.country,opponent.division)||[]).map(t=>t.id);}catch(e){}
   cache.set(scope,list);
  }
  const pos=cache.get(scope).indexOf(opponent.id);
  const coach=E.coach(s,opponent)?.name||'A definir';
  const form=Array.isArray(opponent.stats?.form)&&opponent.stats.form.length?
   opponent.stats.form.slice(-5).join(' · '):'Sem jogos';
  return {power,rank:pos>=0?(pos+1)+'º':'—',coach,form};
 }
 function row(s,x,next,cache){
  const f=x.f,r=f.result,h=x.home,a=x.away,opp=x.opponent,day=x.day;
  const cmp=label(s,x.stage,f,h),rnd=phase(x.stage,f,day),stats=info(s,opp,cache);
  const score=r?n(r.home)+' × '+n(r.away)+(r.pens?' (pên.)':''):'×';
  const mando=f.neutral?'Neutro':x.atHome?'Casa':'Fora';
  const status=x.played?'Finalizado':x===next?'PRÓXIMO':'A disputar';
  const history=x.played&&f.id!=null?
    "<button class='btn small ghost' data-action='result' data-day='"+day+"' data-fixture='"+safe(f.id)+"'>Resumo da partida</button>":'';
  return [
   "<details class='v18347-item"+(x===next?' next':'')+"' data-day='"+day+"'>",
   "<summary class='v18347-line' aria-label='Jornada "+(day+1)+": "+safe(h.name)+" contra "+safe(a.name)+"'>",
   "<span class='v18347-day'><b>J"+(day+1)+"</b><small>"+safe(rnd)+"</small></span>",
   "<span class='v18347-competition'>"+safe(cmp)+"</span>",
   "<span class='v18347-match'>",
   "<span class='v18347-team'>"+badge(h,'small')+"<strong>"+safe(h.name)+"</strong></span>",
   "<b class='v18347-score'>"+score+"</b>",
   "<span class='v18347-team'>"+badge(a,'small')+"<strong>"+safe(a.name)+"</strong></span>",
   "</span>",
   "<span class='v18347-place'>"+mando+"</span>",
   "<span class='v18347-state'>"+status+"</span>",
   "<span class='v18347-arrow' aria-hidden='true'>▾</span>",
   "</summary>",
   "<div class='v18347-details'>",
   "<span><b>Adversário:</b> "+safe(opp.name)+"</span>",
   "<span><b>Técnico:</b> "+safe(stats.coach)+"</span>",
   "<span><b>Posição:</b> "+safe(stats.rank)+"</span>",
   "<span><b>OVR médio:</b> "+safe(stats.power)+"</span>",
   "<span><b>Forma recente:</b> "+safe(stats.form)+"</span>",
   "<span><b>Local:</b> "+safe(f.neutral?'Campo neutro':h.city||'A definir')+"</span>",
   "<span><b>Competição:</b> "+safe(cmp)+" · "+safe(rnd)+"</span>",
   "<span class='v18347-buttons'>"+history+
    "<button class='btn small secondary' data-action='team' data-team='"+safe(opp.id)+"'>Ficha do adversário</button></span>",
   "</div></details>"
  ].join('');
 }
 function calendarPage18347(){
  const s=state;
  const club=s?.userEmployed?E.team(s,s.user):null;
  if(!club)return "<section class='panel v18347-calendar'><h2>Calendário de jogos</h2><p class='subtext'>Assuma um clube para visualizar os confrontos de sua equipe.</p></section>";
  const all=fixtures(s),next=all.find(x=>x.day>=n(s.day)&&!x.played)||null;
  const upcoming=all.filter(x=>x.day>=n(s.day)&&!x.played);
  const chosen=listScope==='all'?all:(upcoming.length?upcoming.slice(0,10):all.slice(-10));
  const cache=new Map();
  const head="<header class='v18347-toolbar'><div><h2>Calendário de jogos · "+safe(s.year)+"</h2>"+
    "<p class='subtext'>"+safe(club.name)+" · Lista cronológica de partidas e adversários</p></div>"+
    "<label>Exibir <select data-v18347-calendar-range aria-label='Jogos exibidos'>"+
    "<option value='next'"+(listScope==='next'?' selected':'')+">Próximos 10 jogos</option>"+
    "<option value='all'"+(listScope==='all'?' selected':'')+">Temporada inteira</option></select></label></header>";
  const column="<div class='v18347-columns'><span>Jornada</span><span>Competição</span><span>Confronto</span><span>Mando</span><span>Situação</span><span></span></div>";
  const body=chosen.length?chosen.map(x=>row(s,x,next,cache)).join(''):"<div class='empty'>Ainda não há confrontos definidos para esta temporada.</div>";
  const foot="<div class='v18347-footer'>"+chosen.length+" de "+all.length+
   " partida(s) disponíveis. Confrontos futuros eliminatórios aparecerão após os sorteios. Clique na linha para ver informações do adversário.</div>";
  return "<section class='panel v18347-calendar'>"+head+column+
    "<div class='v18347-list'>"+body+"</div>"+foot+"</section>";
 }
 const previousRenderPage=renderPage;
 renderPage=function(){if(view==='calendar')return calendarPage18347();return previousRenderPage();};
 const previousSquadPage=squadPage;
 squadPage=function(){
  try{v18324RetirementOpen=false;}catch(e){}
  const result=previousSquadPage();
  return typeof result==='string'?result.replace(/<div class="v18324-retirement-access">[\s\S]*?<\/div>/,''):result;
 };
 document.addEventListener('change',function(event){
  if(!event.target?.matches?.('[data-v18347-calendar-range]'))return;
  listScope=event.target.value==='all'?'all':'next';
  render();
 },true);
 if(typeof window!=='undefined'){
  window.GestorFC=window.GestorFC||{};
  window.GestorFC.calendarList18347={version:'18.347',fixtures:()=>fixtures(state),page:calendarPage18347};
 }
})();
/* FUTBR_CALENDAR_LIST_18347_END */
"""
CSS=r"""
<style id="futbr-calendar-list-18347-style">
.v18347-calendar{min-width:0;margin:0}
.v18347-toolbar{display:flex;align-items:end;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:14px}
.v18347-toolbar h2{font-size:21px;margin:0 0 5px}
.v18347-toolbar p{margin:0}
.v18347-toolbar label{display:flex;align-items:center;gap:8px;font-size:12px;white-space:nowrap}
.v18347-toolbar select{background:var(--panel2,#482221);color:inherit;border:1px solid var(--line,#875252);border-radius:8px;padding:8px;max-width:100%}
.v18347-columns,.v18347-line{display:grid;grid-template-columns:90px minmax(140px,1.1fr) minmax(260px,2.5fr) 65px 89px 22px;gap:9px;align-items:center}
.v18347-columns{padding:8px 13px;background:var(--panel2,#482221);font-size:10px;text-transform:uppercase;letter-spacing:.05em;opacity:.8}
.v18347-item{border:0;border-bottom:1px solid var(--line,#875252);margin:0}
.v18347-item summary::-webkit-details-marker{display:none}
.v18347-item summary::marker{content:''}
.v18347-line{list-style:none;cursor:pointer;min-height:55px;padding:9px 13px}
.v18347-line:hover{background:rgba(255,255,255,.04)}
.v18347-line:focus-visible{outline:2px solid #d9bc69;outline-offset:-2px}
.v18347-item.next .v18347-line{box-shadow:inset 3px 0 #d9bc69;background:rgba(223,189,85,.06)}
.v18347-day{display:flex;flex-direction:column;gap:2px}
.v18347-day b{font-size:12px}
.v18347-day small{font-size:10px;opacity:.8;line-height:1.3}
.v18347-competition{font-size:12px;font-weight:650;overflow-wrap:anywhere;min-width:0}
.v18347-match{display:flex;align-items:center;gap:6px;min-width:0}
.v18347-team{display:flex;align-items:center;gap:5px;flex:1 1 0;min-width:0}
.v18347-team strong{font-size:12px;overflow-wrap:anywhere;min-width:0}
.v18347-team .club-crest,.v18347-team .shield{width:25px;height:28px;flex:0 0 25px;min-width:25px}
.v18347-score{font-size:13px;flex:0 0 auto;white-space:nowrap}
.v18347-place,.v18347-state{font-size:11px;white-space:nowrap}
.v18347-item.next .v18347-state{font-weight:700;color:#e3c87b}
.v18347-arrow{text-align:center;font-size:16px;opacity:.8}
.v18347-item[open] .v18347-arrow{transform:rotate(180deg)}
.v18347-details{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px 13px;padding:12px 16px 15px 104px;background:rgba(0,0,0,.08);font-size:12px}
.v18347-details span{min-width:0;overflow-wrap:anywhere}
.v18347-details b{opacity:.75}
.v18347-buttons{grid-column:1/-1;display:flex;gap:6px;align-items:center;flex-wrap:wrap}
.v18347-footer{padding:11px 14px;font-size:11px;opacity:.78}
@media(max-width:950px){
 .v18347-columns{display:none}
 .v18347-line{grid-template-columns:60px minmax(0,1fr) 72px;gap:4px 8px;min-height:70px}
 .v18347-day{grid-column:1;grid-row:1/3}
 .v18347-competition{grid-column:2;grid-row:1}
 .v18347-place{grid-column:3;grid-row:1;text-align:right}
 .v18347-match{grid-column:2/4;grid-row:2}
 .v18347-state{grid-column:2;grid-row:3}
 .v18347-arrow{grid-column:3;grid-row:3;text-align:right}
 .v18347-details{padding:10px 12px 12px 75px;grid-template-columns:repeat(2,minmax(0,1fr))}
}
@media(max-width:540px){
 .v18347-toolbar{padding:12px}
 .v18347-toolbar label{width:100%;justify-content:space-between}
 .v18347-toolbar select{max-width:65%}
 .v18347-line{grid-template-columns:48px minmax(0,1fr) 66px;gap:4px 5px;padding:9px 10px}
 .v18347-competition{font-size:11px}
 .v18347-team{gap:3px}
 .v18347-team strong{font-size:10px}
 .v18347-team .club-crest,.v18347-team .shield{width:20px;height:23px;flex:0 0 20px;min-width:20px}
 .v18347-score{font-size:11px}
 .v18347-details{grid-template-columns:minmax(0,1fr);padding:10px}
}
</style>
"""

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: feature_calendar_list_18347.py <project>')
    project=Path(sys.argv[1]).resolve()
    source=project/'src/index.html'
    html=source.read_text(encoding='utf-8')
    if MARK in html:raise RuntimeError('18.347 already installed')
    # Remove obsolete navigation instructions, but keep the underlying archival event.
    html=html.replace('Consulte Elenco > Gerenciar aposentadorias.', 'Registros preservados na carreira.')
    anchor="window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';\n})();\n</script>"
    if html.count(anchor)!=1:raise RuntimeError('Main game IIFE anchor missing: cannot install calendar safely')
    html=html.replace(anchor,JS+'\n'+anchor,1)
    i=html.rfind('</body>')
    if i<0:raise RuntimeError('Closing body not found')
    html=html[:i]+CSS+html[i:]
    source.write_text(html,encoding='utf-8')
    report={'ok':True,'version':'18.347',
      'compactListInsteadOfCards':True,'calendarMainNavigation':True,
      'chronologicalFixtures':True,'realClubCrests':True,'competitionAndRound':True,
      'next10AndWholeSeason':True,'opponentCoachRankOverallFormAndVenue':True,
      'expandableDetails':True,'retirementHistoryScreenHidden':True,
      'manualRetirementFromPlayerProfilePreserved':True,
      'retirementSaveArchiveIntact':True,'noSaveMigrationRequired':True}
    (project/'calendar-list-18347-install.json').write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
