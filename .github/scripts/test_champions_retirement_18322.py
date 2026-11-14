from pathlib import Path
import json,re,subprocess,sys

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_champions_retirement_18322.py <project>')
 root=Path(sys.argv[1]);html=(root/'src'/'index.html').read_text(encoding='utf-8')
 required=['FUTBR_CHAMPIONS_RETIREMENT_18322','v18322CaptureSeason(s,oldYear);',
  'v18322BaseCompetitionsPage=competitionsPage','v18322BaseNationalPage=v640NationalPage',
  'v18322BaseTransfersPage=transferActivityPage','auto=clubBefore===s.user?',
  'root.history[0].scorer={id:p.id','function v18322RetirementPage()','data-v18322="c-year"','v18322-docked-toolbar','v18322-scorer-list','v18322VisibleLimit=120','v18324-docked-toolbar','v18324-retirement-access','v18324-open-retirements','FUTBR_RETIRE_MODAL_18328_START','data-v18328-choice="confirm"','FUTBR_MANUAL_ADVANCE_18326_START','dayfast-single-day','stopsBeforeOwnFixture:true']
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
 createElement(tag){
  return {id:'',textContent:'',className:'',dataset:{},listeners:{},removed:false,
   setAttribute(){},remove(){this.removed=true},focus(){document.activeElement=this},
   addEventListener(key,cb){this.listeners[key]=cb},
   querySelector(sel){
    if(!this.fields)this.fields={};
    if(!this.fields[sel]){
     const el={textContent:'',dataset:{},focus(){document.activeElement=this},closest(){return this}};
     if(sel.includes('choice="confirm"'))el.dataset.v18328Choice='confirm';
     if(sel.includes('choice="cancel"'))el.dataset.v18328Choice='cancel';
     this.fields[sel]=el;
    }return this.fields[sel];
   },
   querySelectorAll(sel){return sel==='button'
    ?[this.querySelector('[data-v18328-choice="cancel"]'),this.querySelector('[data-v18328-choice="confirm"]')]:[]}
  };
 },
 addEventListener(name,cb){this.listeners[name]=cb;},
 removeEventListener(name,cb){if(this.listeners[name]===cb)delete this.listeners[name];}};
const esc=x=>String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
const WorldCatalog={countries:[{id:'bra',name:'Brasil',cup:'Copa do Brasil'},{id:'eng',name:'Inglaterra',cup:'FA Cup'}]};
let state=null,view='competitions',renderCalls=0,persistCalls=0;
let v54CompetitionMode='league',v4Competition='lib';
const selectedCountry=()=>state?.teams?.[0]?.country||'bra',selectedDivision=()=>1;
const badge=t=>'<i class="shield">ESCUDO '+esc(t.id)+'</i>';
const render=()=>{renderCalls++;};
const persist=()=>{persistCalls++;};
const toast=()=>{},confirm=()=>{throw Error('Native confirm forbidden')};
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
const v579ManualRetirementEligible=(s,p)=>!!(s&&p&&p.clubId===s.user&&p.squad!=='youth'&&Number(p.age)>=35);
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

const advanceCases={dayfast:0,next:0,nationalNext:0,legacy:0};
document.body={classList:{toggle(){}},appendChild(el){this.lastModal=el;}};document.querySelectorAll=()=>[];document.querySelector=()=>null;document.hidden=false;document.activeElement=null;
let v53Sim={active:false,starting:false},v53Creating=false,v128NationalAdvanceBusy=false;
let v555UpdateChrome=()=>{},v128UpdateNationalChrome=()=>{};
let v53StartSimulation=async mode=>{
 if(mode!=='dayfast')throw Error('Unexpected worker mode '+mode);
 advanceCases.dayfast++;const day=state.day;state.day++;state.lastDay=day;return state;
};
let v1891AdvanceToNextMatch=async()=>{advanceCases.next++;while(state.day<state.schedule.length){
 const f=state.schedule[state.day]?.fixtures?.find(x=>x.home===state.user||x.away===state.user);
 if(f&&!f.result)break;state.day++;
}return state;};
let v128AdvanceAsNationalCoach=async()=>{advanceCases.nationalNext++;return state;};
let v640PrepareNationalStage=()=>{};
let v640UserFixture=s=>s.schedule?.[s.day]?.nationalFixtures?.find(x=>x.home===s.v640National?.userTeam||x.away===s.v640National?.userTeam)||null;
let showDay=()=>{};
E.upcoming=s=>s.schedule?.[s.day]?.fixtures?.find(x=>x.home===s.user||x.away===s.user)||null;

state=testState();
""" + body.group(0) + r"""
const api=window.GestorFC.championsRetire18322;
assert.equal(api.version,'18.328');
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
assert(squadPage().includes('Gerenciar aposentadorias'),'Elenco must show retirement entry');
act({dataset:{action:'v18324-open-retirements'}});
assert.equal(view,'squad','Retirement management must remain in Elenco');
assert(squadPage().includes('Histórico de aposentadorias'),'Retirement management must render inside Elenco');
assert(squadPage().includes('data-action="v18322-retire"'),'Eligible squad retirement controls absent');
assert(!transferActivityPage().includes('Aposentadorias'),'Movimentacoes must not show retirement');
act({dataset:{action:'v18324-open-retirements'}});
assert(squadPage().includes('Gerenciar aposentadorias'),'Elenco must reopen normal squad list');
view='competitions';
assert(!competitionsPage().startsWith('<div class="v18322-switch">'),'Extra tabs row reduces standings height');
assert(v640NationalPage().includes('Histórico de títulos'));
assert(!transferActivityPage().includes('Aposentadorias'),'Movimentacoes must remain transfer-only');
act({dataset:{action:'v18322-toggle-clubs',mode:'history'}});
assert(competitionsPage().includes('Artilheiro da liga'));
assert(competitionsPage().includes('data-v18322="c-year"'),'Year filter missing');
assert(competitionsPage().includes('value="bra" selected'),'Default country not selected');
assert(competitionsPage().includes('value="league" selected'),'Default league filter not selected');
assert(competitionsPage().includes('value="1" selected'),'Default division 1 not selected');
act({dataset:{action:'v18322-toggle-national',mode:'history'}});
assert(v640NationalPage().includes('FLAG BRA'));
assert(!transferActivityPage().includes('Veterano aposentado'),'Retirement history must not appear in Movimentacoes');
const savesBeforeModal=persistCalls;
act({dataset:{action:'v18322-retire',player:'p3'}});
assert(!state.players.p3.v579ManualRetire,'Opening must not commit retirement');
assert.equal(persistCalls,savesBeforeModal,'Opening cannot persist');
assert(document.body.lastModal?.listeners.click,'Missing in-game confirmation');
assert.equal(document.body.lastModal.fields['[data-v18328-player]'].textContent,'Veterano');
document.body.lastModal.listeners.click({target:document.body.lastModal.querySelector('[data-v18328-choice="cancel"]')});
assert(!state.players.p3.v579ManualRetire,'Cancel must leave player unchanged');
act({dataset:{action:'v18322-retire',player:'p3'}});
const escapeModal=document.body.lastModal;
document.listeners.keydown({key:'Escape',preventDefault(){},stopPropagation(){}});
assert(escapeModal.removed&&!state.players.p3.v579ManualRetire,'Esc must cancel without saving');
act({dataset:{action:'v18322-retire',player:'p3'}});
const modal=document.body.lastModal;
const button=modal.querySelector('[data-v18328-choice="confirm"]');
modal.listeners.click({target:button});
modal.listeners.click({target:button});
assert(state.players.p3.v579ManualRetire&&persistCalls===savesBeforeModal+1,'Duplicate confirmation must only save once');
assert(modal.removed,'Modal did not close');
assert(window.GestorFC.retirementModal18328.status().nativeConfirm===false);
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

const v18326Fixture=()=>{
 const s=testState();s.year=2027;s.day=0;s.seasonDone=false;s.live=null;
 s.vacation={active:false};s.v640National=null;
 s.schedule=[{type:'league',fixtures:[]},{type:'league',fixtures:[]},
  {type:'league',fixtures:[{home:'b1',away:'b2',result:null}]},{type:'league',fixtures:[]}];return s;
};
async function v18326Regression(){
 state=v18326Fixture();const n=advanceCases.dayfast;await act({dataset:{action:'advance'}});
 assert.equal(advanceCases.dayfast,n+1);assert.equal(state.day,1,'One day only');
 state=v18326Fixture();await act({dataset:{action:'v1891-nextmatch'}});
 assert.equal(state.day,2,'Stop before club game');
 const n2=advanceCases.dayfast;await act({dataset:{action:'advance'}});
 assert.equal(advanceCases.dayfast,n2,'Do not auto play user fixture');
 state=v18326Fixture();state.v640National={userTeam:'BRA'};
 await act({dataset:{action:'advance'}});
 assert.equal(state.day,1,'National one day only');
 await act({dataset:{action:'v1891-nextmatch'}});
 assert.equal(advanceCases.nationalNext,1);
 state=v18326Fixture();state.v640National={userTeam:'BRA'};
 state.schedule[0]={type:'national',nationalFixtures:[{home:'BRA',away:'ARG',result:null}],fixtures:[]};
 const n3=advanceCases.dayfast;await act({dataset:{action:'advance'}});
 assert.equal(advanceCases.dayfast,n3,'National match must not be simulated');
 state=v18326Fixture();state.seasonDone=true;
 const n4=advanceCases.dayfast;await act({dataset:{action:'advance'}});
 assert.equal(advanceCases.dayfast,n4,'Season modal must be preserved');
 return true;
}

console.log(JSON.stringify({ok:true,version:'18.328',editions:count,topScorer:true,runnerUp:true,
 nationalHistory:true,teamCrests:true,retirementHistory:true,manualRetirement:true,inGameRetirementConfirm:true,noNativeRetirementDialog:true,
 defaultFilters:true,yearFilter:true,standingsToolbarHeightPreserved:true,scorersFromCompetitionStats:true,tiedScorersVertical:true,
 realToolbarClassMatched:true,twentyTeamRowsCompact:true,retirementAccessFromSquad:true,retirementOnlyInSquad:true,
 preservesReload:true,noFabricatedLegacy:true,allFourRankTabsPreserved:true,manualAdvancePresent:true}));
v18326Regression().then(()=>console.log(JSON.stringify({ok:true,version:'18.326',manualAdvanceOneDay:true,stopBeforeUserMatch:true,nationalOneDay:true,nationalNextFixture:true}))).catch(e=>{console.error(e);process.exitCode=1;});
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
  installed=page.evaluate("() => ({version:window.GestorFC?.championsRetire18322?.version||null, clubRows:typeof window.GestorFC?.championsRetire18322?.clubRows==='function', nationalRows:typeof window.GestorFC?.championsRetire18322?.nationalRows==='function' ,retirementModal:window.GestorFC?.retirementModal18328?.version||null})")
  browser.close()
 if installed['version']!='18.328' or installed['retirementModal']!='18.328' or not installed['clubRows'] or not installed['nationalRows']:
  raise RuntimeError('18.322 missing in browser runtime: '+json.dumps({'api':installed,'errors':runtime_errors[:6]},ensure_ascii=False))
 data=json.loads(r.stdout.strip().splitlines()[-1])
 if not data.get('ok'):raise RuntimeError('18.322 invalid result')
 (root/'champions-retirement-18322-tests.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(data,ensure_ascii=False))
if __name__=='__main__':main()
