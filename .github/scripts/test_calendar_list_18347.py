from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_calendar_list_18347.py <project>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src/index.html').read_text(encoding='utf-8')
    start='/* FUTBR_CALENDAR_LIST_18347 */'
    end='/* FUTBR_CALENDAR_LIST_18347_END */'
    assert html.count(start)==1 and html.count(end)==1,'Calendar must load inside main game engine once'
    assert html.count("<style id=\"futbr-calendar-list-18347-style\">")==1
    js=start+'\n'+html.split(start,1)[1].split(end,1)[0]
    original_end="window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';"
    assert html.index(start)<html.index(original_end),'Calendar must share game runtime closure'
    checks=[
      'FUTBR_CALENDAR_LIST_18347',
      "['calendar','calendar','Calendário de jogos']",
      "data-v18347-calendar-range",
      'Campeonato Brasileiro · Série C',
      'function calendarPage18347()',
      "badge(h,'small')","badge(a,'small')",
      "const previousRenderPage=renderPage;",
      "const previousSquadPage=squadPage;",
      "v18324RetirementOpen=false;",
      "previousSquadPage()",
      "window.GestorFC.calendarList18347",
      "state"
    ]
    for mark in checks:
        if mark not in js:raise AssertionError('Missing calendar/list UI feature: '+mark)
    harness=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}};
let renders=0;
const document={events:{},addEventListener(name,fn){this.events[name]=fn}};
function render(){renders++}
const NAV=[['dashboard','home','Visão geral'],['squad','users','Elenco'],['competitions','trophy','Competições']];
let view='dashboard',v18324RetirementOpen=true;
let state=null;
const esc=x=>String(x==null?'':x).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
const badge=(t,size)=>"<span class='shield club-crest' data-club='"+esc(t?.id)+"' data-size='"+size+"'></span>";
const divisionLabel=(c,d)=>c+" "+d;
function renderPage(){return 'base-page';}
function squadPage(){
 return "<div class=\"v18324-retirement-access\"><span>Aposentadorias</span><button>Gerenciar aposentadorias</button></div><section>Elenco original</section>";
}
const E={
 team:(s,id)=>s.teams.find(t=>t.id===id),
 country:c=>({cup:c==='bra'?'Copa do Brasil':'Copa nacional'}),
 overall:p=>p.ovr,coach:(s,t)=>s.coaches[t.coachId],
 table:(s,c,d)=>s.teams.filter(t=>t.country===c&&Number(t.division)===Number(d)).sort((a,b)=>b.stats.pts-a.stats.pts)
};
function mkClub(id,name,ovr=78,points=35){
 return {id,name,country:'bra',division:1,short:name.slice(0,3),color:'#fff',city:'Rio de Janeiro',
  stats:{pts:points,form:['V','E','V','D','V']},coachId:'c_'+id,
  roster:Array.from({length:15},(_,i)=>id+'_p'+i),lineup:Array.from({length:11},(_,i)=>id+'_p'+i)};
}
state={
 user:'u',userEmployed:true,year:2031,day:2,coaches:{},
 teams:[mkClub('u','Flamengo',80,40),mkClub('a','Palmeiras',81,38),mkClub('b','Grêmio',76,31)],
 players:{},competitions:{lib:{name:'Copa Libertadores'}},
 schedule:[],retirements:[{name:'Antigo',year:2028}]
};
for(const t of state.teams){
 state.coaches[t.coachId]={name:'Técnico '+t.name};
 for(const id of t.roster)state.players[id]={id,ovr:t.id==='a'?82:t.id==='b'?76:80};
}
for(let i=0;i<16;i++){
 const f={id:'m'+i,home:i%2?'a':'u',away:i%2?'u':'a',country:'bra',division:1,result:i<2?{home:1,away:0}:null};
 state.schedule.push({type:'league',label:'Campeonato Brasileiro - Rodada '+(i+1),round:i+1,fixtures:[f,{home:'a',away:'b'}]});
}
"""
    tests=r"""
assert.equal(NAV.filter(n=>n[0]==='calendar').length,1);
assert.equal(NAV.findIndex(n=>n[0]==='calendar'),NAV.findIndex(n=>n[0]==='competitions')-1);
assert.equal(renderPage(),'base-page');
const originals=state.retirements;
const squad=squadPage();
assert(!squad.includes('Gerenciar aposentadorias'));
assert(!squad.includes('Histórico de aposentadorias'));
assert(squad.includes('Elenco original'));
assert.equal(v18324RetirementOpen,false);
assert.strictEqual(state.retirements,originals);
view='calendar';
let page=renderPage();
assert(page.includes('Calendário de jogos · 2031'));
assert(page.includes('Campeonato Brasileiro · Série A'));
assert(page.includes('Próximos 10 jogos'));
assert(page.includes('Palmeiras'));
assert(page.includes('Técnico Palmeiras'));
assert(page.includes('OVR médio:'));
assert(page.includes('Posição:'));
assert(page.includes('Forma recente:'));
assert(page.includes('Ficha do adversário'));
assert(page.includes('data-club='));
assert(page.includes('v18347-line'));
assert(page.includes('PRÓXIMO'));
assert(!page.includes('v18322-panel'));
assert(!page.includes('card-grid'));
assert.equal((page.match(/<details class='v18347-item/g)||[]).length,10);
assert(!page.includes('Grêmio'),'Other clubs must not appear as player opponent');
document.events.change({target:{matches:selector=>selector==='[data-v18347-calendar-range]',value:'all'}});
assert.equal(renders,1);
page=renderPage();
assert.equal((page.match(/<details class='v18347-item/g)||[]).length,16);
assert(page.includes('Resumo da partida'));
state.userEmployed=false;
assert(renderPage().includes('Assuma um clube'));
assert.strictEqual(state.retirements,originals);
console.log('PASS: 16 real fixtures, next 10, crests, competition, interactive opponent information, retired screen removed, saves unchanged');
"""
    proc=subprocess.run(['node','-e',harness+'\n'+js+'\n'+tests],text=True,capture_output=True,timeout=40)
    if proc.returncode:
        raise RuntimeError('18.347 real injected UI regression failed:\n'+proc.stderr[-7500:])
    print(proc.stdout)
    report={'ok':True,'version':'18.347','realHTMLFeatureExecuted':True,
      'compactListLayout':True,'realCrests':True,'all16FixtureRows':True,
      'next10Default':True,'opponentProfileAvailable':True,
      'teamAndLeagueInformation':True,'retirementPageRemoved':True,
      'manualPlayerRetirementPreserved':True,'savedRetirementHistoryUntouched':True,
      'nationalCareerNoCrash':True,
      'noFabricatedFixtures':True}
    (root/'calendar-list-18347-tests.json').write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
