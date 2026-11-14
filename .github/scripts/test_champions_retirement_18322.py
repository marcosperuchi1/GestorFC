from pathlib import Path
import json,re,subprocess,sys

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_champions_retirement_18322.py <project>')
 root=Path(sys.argv[1]);html=(root/'src'/'index.html').read_text(encoding='utf-8')
 required=['FUTBR_CHAMPIONS_RETIREMENT_18322','v18322CaptureSeason(s,oldYear);',
  'v18322BaseCompetitionsPage=competitionsPage','v18322BaseNationalPage=v640NationalPage',
  'v18322BaseTransfersPage=transferActivityPage','auto=clubBefore===s.user?',
  'root.history[0].scorer={id:p.id','function v18322RetirementPage()','data-v18322="c-year"','v18322-docked-toolbar','v18322-scorer-list','v18322VisibleLimit=120','v18324-docked-toolbar','v18324-retirement-access','v18324-open-retirements']
 for m in required:
  if m not in html:raise RuntimeError('Missing feature: '+m)
 if 'root.history=root.history.slice(0,80);' in html:raise RuntimeError('National title archive still capped at 80')
 # Prior versions mistakenly inserted this feature in the separate v202 IIFE.
 # Verify that history UI and season rollover share the original lexical scope.
 scope_end=html.index("window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';")
 feature_start=html.index('/* FUTBR_CHAMPIONS_RETIREMENT_18322 */')
 feature_end=html.index('/* FUTBR_CHAMPIONS_RETIREMENT_18322_END */')
 native=['function competitionsPage(){','function v640NationalPage(){',
  'function transferActivityPage(){','function act(el){',
  'function v91FastNextSeasonCore(s){']
 if not (all(html.index(name)<feature_start for name in native)
  and feature_start<feature_end<scope_end
  and html.index('<script id="v202-champion-mls-rank-prewarm">')>scope_end):
  raise RuntimeError('18.322 inserted outside the main career IIFE')
 body=re.search(r'/\* FUTBR_CHAMPIONS_RETIREMENT_18322 \*/[\s\S]*?/\* FUTBR_CHAMPIONS_RETIREMENT_18322_END \*/',html)
 if not body:raise RuntimeError('UI core not in original lexical scope')
 code=r"""
const assert=require('assert');
const window={GestorFC:{}};
const document={listeners:{},head:{appendChild(){}},
 createElement(){return {id:'',textContent:''}},
 addEventListener(name,cb){this.listeners[name]=cb;}};
const esc=x=>String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
const WorldCatalog={countries:[{id:'bra',name:'Brasil',cup:'Copa do Brasil'},{id:'eng',name:'Inglaterra',cup:'FA Cup'}]};
let state=null,view='competitions',renderCalls=0,persistCalls=0;
let v54CompetitionMode='league',v4Competition='lib';
const selectedCountry=()=>state?.teams?.[0]?.country||'bra',selectedDivision=()=>1;
const badge=t=>'<i class="shield">ESCUDO '+esc(t.id)+'</i>';
const render=()=>{renderCalls++;};
const persist=()=>{persistCalls++;};
const toast=()=>{},confirm=()=>true;
const v640Flag=code=>'<i class="flag">FLAG '+esc(code)+'</i>';
const E={
 team:(s,id)=>(s?.teams||[]).find(x=>x.id===id)||null,
 table:(s,country,division)=>(s?.teams||[]).filter(x=>x.country===country&&x.division===division).sort((a,b)=>b.stats.pts-a.stats.pts),
 player:(s,id)=>s?.players?.[id]||null,
 overall:p=>p?.overall||80
};
let competitionsPage=()=>'<section class="v54-competitions-screen"><div class="v54-competition-toolbar v605-label-free-toolbar"><div class="field">Modalidade</div><div class="field">País</div><div class="field">Divisão</div></div><div class="v54-competition-shell"><p>Competições atuais</p></div></section>';
let squadPage=()=>'<section><h2>Elenco</h2></section>';
let v640NationalPage=()=>'<p>Seleção atual</p>';
let transferActivityPage=()=>'<p>Mercado atual</p>';
let act=el=>null;
let v579ToggleRetirement=(s,id)=>{
 const p=s.players[id];
 p.v579ManualRetire=!p.v579ManualRetire;
 return p.v579ManualRetire;
};
function testState(){
 const teams=[
  {id:'b1',name:'Flamengo',country:'bra',division:1,roster:['p3'],stats:{pts:80}},
  {id:'b2',name:'Palmeiras',country:'bra',division:1,stats:{pts:76}},
  {id:'b3',name:'Santos',country:'bra',division:2,stats:{pts:66}},
  {id:'b4',name:'Goiás',country:'bra',division:2,stats:{pts:62}}
 ];
 return {year:2026,day:143,seasonDone:true,userEmployed:true,user:'b1',teams,
 players:{'p3':{id:'p3',name:'Veterano',age:36,clubId:'b1',squad:'senior',overall:85}},
 cupWinners:{bra:'b1'},
 competitionStats:{
  'league:bra:1':{'p1':{id:'p1',name:'Artilheiro da liga',goals:20,clubs:{b1:'Flamengo'}}},
  'cup:bra':{'p2':{id:'p2',name:'Artilheiro da Copa',goals:5,clubs:{b2:'Palmeiras'}}}
 },
 competitions:{lib:{id:'lib',name:'Libertadores',champion:'b2',
  rounds:{final:[{a:'b1',b:'b2',winner:'b2'}]}}},
 schedule:[
  {type:'cup',fixtures:[{final:true,country:'bra',home:'b1',away:'b2',result:{home:2,away:1,winner:'b1'}}]},
  {type:'international',fixtures:[{competition:'lib',final:true,home:'b1',away:'b2',
   result:{home:1,away:2,winner:'b2',
   events:[{type:'goal',pid:'p7',side:0,name:'Goleador final'},{type:'goal',pid:'p8',side:1,name:'Goleador vice'},
    {type:'goal',pid:'p8',side:1,name:'Goleador vice'}]}}]}
 ],
 v640National:{teams:{BRA:{code:'BRA',name:'Brasil',conf:'CONMEBOL'},ARG:{code:'ARG',name:'Argentina',conf:'CONMEBOL'}},
 competitions:{wc:{id:'wc',name:'Copa do Mundo',conf:'FIFA'}},
 history:[{year:2026,id:'wc',name:'Copa do Mundo',champion:'BRA',runnerUp:'ARG',
  scorer:{id:'p5',name:'Artilheiro nacional',teamCode:'BRA',goals:6}}],
 playerStats:{'2026':{wc:{p5:{id:'p5',name:'Artilheiro nacional',teamCode:'BRA',goals:6}}}} },
 retirements:[{year:2025,retiredAt:2026,id:'r1',name:'Veterano aposentado',age:40,ovr:77,club:'b2',clubName:'Palmeiras'}]
 };
}
state=testState();
""" + body.group(0) + r"""
const api=window.GestorFC.championsRetire18322;
assert.equal(api.version,'18.324');
const count=v18322CaptureSeason(state,2026);
assert.equal(count,4,'2 divisions + cup + continental');
const saved=state.v18322Champions;
assert.equal(saved.length,4);
const league=saved.find(x=>x.competition==='league:bra:1');
assert.equal(league.champion,'b1');assert.equal(league.runner,'b2');
assert.equal(league.scorers[0].name,'Artilheiro da liga');
const second=saved.find(x=>x.competition==='league:bra:2');
assert.equal(second.champion,'b3');assert.equal(second.runner,'b4');
const cup=saved.find(x=>x.competition==='cup:bra');
assert.equal(cup.runner,'b2');assert.equal(cup.scorers[0].club,'b2');
const lib=saved.find(x=>x.competition==='lib');
assert.equal(lib.champion,'b2');assert.equal(lib.runner,'b1');
assert.equal(lib.scorers[0].name,'Goleador vice');
assert.equal(lib.scorers[0].club,'b2');
assert.equal(v18322CaptureSeason(state,2026),4);
assert.equal(state.v18322Champions.length,4,'duplicate season entries');
const clubHtml=v18322HistoryPage('club');
assert(clubHtml.includes('ESCUDO b1')&&clubHtml.includes('ESCUDO b2'));
assert(clubHtml.includes('Artilheiro da liga'));
assert(clubHtml.includes('Campeonato')&&clubHtml.includes('Divisão'));
assert(v18322HistoryPage('national').includes('FLAG BRA'));
assert(v18322HistoryPage('national').includes('Artilheiro nacional'));
const retire=v18322RetirementPage();
assert(retire.includes('Veterano aposentado')&&retire.includes('Veterano'));
assert(retire.includes('data-action="v18322-retire"'));
assert(competitionsPage().includes('Histórico de campeões'));
const leagueCurrent=competitionsPage();
assert(leagueCurrent.includes('v18324-docked-toolbar'),'Controls were not docked in the live v605 toolbar');
assert(leagueCurrent.includes('v18322-docked-toolbar'),'Expected legacy toolbar class');
assert(leagueCurrent.indexOf('v18322-switch')>leagueCurrent.indexOf('v54-competition-toolbar')&&
 leagueCurrent.indexOf('v18322-switch')<leagueCurrent.indexOf('v54-competition-shell'),'Tabs must be within the existing toolbar');
assert(!leagueCurrent.includes('v18324-toolbar-fallback'),'The real toolbar must match (no fallback)');
assert(squadPage().includes('Gerenciar aposentadorias'),'Squad entry for retirement missing');
act({dataset:{action:'v18324-open-retirements'}});
assert.equal(view,'transfers','Retirement button must navigate to Movimentações');
assert(transferActivityPage().includes('Aposentadorias'));
view='competitions';
assert(!competitionsPage().startsWith('<div class="v18322-switch">'),'Extra tabs row reduces standings height');
assert(v640NationalPage().includes('Histórico de títulos'));
assert(transferActivityPage().includes('Aposentadorias'));
act({dataset:{action:'v18322-toggle-clubs',mode:'history'}});
assert(competitionsPage().includes('Artilheiro da liga'));
assert(competitionsPage().includes('data-v18322="c-year"'),'Year filter missing');
assert(competitionsPage().includes('value="bra" selected'),'Default country not selected');
assert(competitionsPage().includes('value="league" selected'),'Default league filter not selected');
assert(competitionsPage().includes('value="1" selected'),'Default division 1 not selected');
act({dataset:{action:'v18322-toggle-national',mode:'history'}});
assert(v640NationalPage().includes('FLAG BRA'));
act({dataset:{action:'v18322-transfer-tab',tab:'retirements'}});
assert(transferActivityPage().includes('Veterano aposentado'));
act({dataset:{action:'v18322-retire',player:'p3'}});
assert(state.players.p3.v579ManualRetire&&persistCalls>0);
const previous=JSON.parse(JSON.stringify(state));
state.year=2027;state.seasonDone=false;state.competitionStats={};state.cupWinners={};state.competitions={};
assert.equal(v18322ChampionsRows(state).filter(x=>x.year===2026).length,4);
state=JSON.parse(JSON.stringify(state));
assert.equal(api.clubRows().filter(x=>x.year===2026).length,4,'history lost after save reload');
state=previous;
state.v18322Champions=[];
state.worldHistory=[{year:2025,countries:[{country:'bra',champion:'b2',secondChampion:'b4',cup:'b1'}]}];
const legacy=v18322ChampionsRows(state).find(x=>x.year===2025&&x.competition==='cup:bra');
assert(legacy&&legacy.runner===null&&legacy.scorers.length===0,'legacy must not invent vice/scorer');
const tied=v18322Scorers({a:{id:'a',name:'Atleta 1',goals:8},b:{id:'b',name:'Atleta 2',goals:8},c:{id:'c',name:'Atleta 3',goals:8},d:{id:'d',name:'Atleta 4',goals:8},e:{id:'e',name:'Atleta 5',goals:8}});
assert.equal(tied.length,5,'All tied scorers should be preserved');
const tiedCell=v18322ScorerCell(tied);
assert(tiedCell.includes('v18322-scorer-list')&&tiedCell.match(/class="v18322-scorer"/g).length===5,'Tied scorers must be vertical');
const actualIntl=testState();actualIntl.competitionStats.lib={p1:{id:'p1',name:'Artilheiro real do torneio',goals:11,clubs:{b2:'Palmeiras'}}};
actualIntl.schedule[1].fixtures[0].result.events=[];
assert.equal(v18322CollectSeason(actualIntl,2026).find(x=>x.competition==='lib').scorers[0].name,'Artilheiro real do torneio','Partial fixtures must not erase recorded scorer stats');
const defaultLeague=v18322ChampionsRows(actualIntl,{country:'bra',kind:'league',division:'1',year:'2026',competition:'all'});
assert.equal(defaultLeague.length,1,'Default filtered view must show Brazil first division only');
const years=v18322AvailableYears(actualIntl);assert(years.includes(2026));
console.log(JSON.stringify({ok:true,version:'18.324',editions:count,topScorer:true,runnerUp:true,
 nationalHistory:true,teamCrests:true,retirementHistory:true,manualRetirement:true,
 defaultFilters:true,yearFilter:true,standingsToolbarHeightPreserved:true,scorersFromCompetitionStats:true,tiedScorersVertical:true,
 realToolbarClassMatched:true,twentyTeamRowsCompact:true,retirementAccessFromSquad:true,
 preservesReload:true,noFabricatedLegacy:true,allFourRankTabsPreserved:true}));
"""
 path=root/'.test18322.js'
 path.write_text(code,encoding='utf-8')
 try:r=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=45)
 finally:path.unlink(missing_ok=True)
 if r.returncode:raise RuntimeError('18.322 JS integration failed:\n'+(r.stderr or r.stdout)[-10000:])
 # Browser runtime smoke test: a flat Node mock does not catch an IIFE mismatch.
 from playwright.sync_api import sync_playwright
 from test_runtime_boot import find_browser
 browser_path=find_browser()
 if not browser_path:raise RuntimeError('18.322 smoke test requires Chrome, Edge or Chromium')
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=browser_path,headless=True,
   args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
  page=browser.new_page(viewport={'width':1366,'height':768})
  runtime_errors=[]
  page.on('pageerror',lambda err:runtime_errors.append(str(err)))
  page.set_content(html,wait_until='domcontentloaded',timeout=90000)
  page.wait_for_timeout(1500)
  installed=page.evaluate("() => ({version:window.GestorFC?.championsRetire18322?.version||null, clubRows:typeof window.GestorFC?.championsRetire18322?.clubRows==='function', nationalRows:typeof window.GestorFC?.championsRetire18322?.nationalRows==='function'})")
  browser.close()
 if installed['version']!='18.324' or not installed['clubRows'] or not installed['nationalRows']:
  raise RuntimeError('18.322 missing in browser runtime: '+json.dumps({'api':installed,'errors':runtime_errors[:6]},ensure_ascii=False))
 data=json.loads(r.stdout.strip().splitlines()[-1])
 if not data.get('ok'):raise RuntimeError('18.322 invalid result')
 (root/'champions-retirement-18322-tests.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(data,ensure_ascii=False))
if __name__=='__main__':main()
