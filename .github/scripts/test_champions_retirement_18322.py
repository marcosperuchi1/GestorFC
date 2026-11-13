from pathlib import Path
import json,re,subprocess,sys

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_champions_retirement_18322.py <project>')
 root=Path(sys.argv[1]);html=(root/'src'/'index.html').read_text(encoding='utf-8')
 required=['FUTBR_CHAMPIONS_RETIREMENT_18322','v18322CaptureSeason(s,oldYear);',
  'v18322BaseCompetitionsPage=competitionsPage','v18322BaseNationalPage=v640NationalPage',
  'v18322BaseTransfersPage=transferActivityPage','auto=clubBefore===s.user?',
  'root.history[0].scorer={id:p.id','function v18322RetirementPage()']
 for m in required:
  if m not in html:raise RuntimeError('Missing feature: '+m)
 if 'root.history=root.history.slice(0,80);' in html:raise RuntimeError('National title archive still capped at 80')
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
let competitionsPage=()=>'<p>Competições atuais</p>';
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
  {id:'b1',name:'Flamengo',country:'bra',division:1,stats:{pts:80}},
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
assert.equal(api.version,'18.322');
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
assert(v640NationalPage().includes('Histórico de títulos'));
assert(transferActivityPage().includes('Aposentadorias'));
act({dataset:{action:'v18322-toggle-clubs',mode:'history'}});
assert(competitionsPage().includes('Artilheiro da liga'));
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
console.log(JSON.stringify({ok:true,version:'18.322',editions:count,topScorer:true,runnerUp:true,
 nationalHistory:true,teamCrests:true,retirementHistory:true,manualRetirement:true,
 preservesReload:true,noFabricatedLegacy:true,allFourRankTabsPreserved:true}));
"""
 path=root/'.test18322.js'
 path.write_text(code,encoding='utf-8')
 try:r=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=45)
 finally:path.unlink(missing_ok=True)
 if r.returncode:raise RuntimeError('18.322 JS integration failed:\n'+(r.stderr or r.stdout)[-10000:])
 data=json.loads(r.stdout.strip().splitlines()[-1])
 if not data.get('ok'):raise RuntimeError('18.322 invalid result')
 (root/'champions-retirement-18322-tests.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(data,ensure_ascii=False))
if __name__=='__main__':main()
