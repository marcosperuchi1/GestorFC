"""Regression: recover 2026 scorers from 2033 career data, preserve newer seasons."""
from pathlib import Path
import sys,subprocess,json
def main(root):
 root=Path(root).resolve();s=(root/'src/index.html').read_text(encoding='utf-8')
 start=s.index('/* FUTBR_SCORERS_IN_SCOPE_18220_START */')
 end=s.index('/* FUTBR_SCORERS_IN_SCOPE_18220_END */',start)+len('/* FUTBR_SCORERS_IN_SCOPE_18220_END */')
 original=s[start:end]
 start=s.index('/* FUTBR_SCORER_HISTORY_RECOVERY_18377')
 end=s.index('window.GestorFC.render=render;',start)
 patch=s[start:end]
 mock=r'''
const assert=require('node:assert/strict');
global.window=global;window.GestorFC={};
let state=null;
let scorerFilter={kind:'all',country:'all',division:'all',year:'2026',query:'',nationality:'all',page:0};
const C=[{id:'bra',name:'Brasil'}],WorldCatalog={countries:C},NAT={BRA:['Brasil'],ENG:['Inglaterra'],QAT:['Catar']};
const E={team:(s,id)=>s.teams.find(t=>t.id===id)||null,normName:x=>String(x||'').toLowerCase()};
function esc(x){return String(x??'').replace(/&/g,'&amp;')}
function nation(c){return c}function badge(t){return t.name}
function teamButton(t){return t.name}function v640Flag(x){return x}
function v677RankingTabs(){return '<nav>Rankings</nav>'}
function v320Players(s){return Object.values(s.players||{})}
'''
 test=r'''
const ss={
 year:2033,day:1,seasonDone:false,
 teams:[{id:'old',name:'Clube de 2026',country:'bra',division:1},
        {id:'new',name:'Clube atual de 2033',country:'eng',division:1},
        {id:'old2',name:'Outro clube de 2026',country:'eng',division:1}],
 players:{p1:{id:'p1',name:'Artilheiro de 2026',natCode:'BRA',clubId:'new'},
          p2:{id:'p2',name:'Vice de 2026',natCode:'ENG',clubId:'new'},
          p3:{id:'p3',name:'Jogador da selecao',natCode:'QAT',clubId:'new'}},
 scorerArchive:[2028,2029,2030,2031,2032].map(year=>({year,competitions:year===2032?
 {'league:bra:1':{p2:{id:'p2',name:'Vice de 2026',natCode:'ENG',goals:12,apps:15}}}:{}})),
 v555CareerArchive:{'2026':{n:{old:'Clube de 2026',old2:'Outro clube de 2026'},p:{
  p1:'old|32|35|7|1|0',p2:'old2|29|17|4|1|0',
  zero:'old|30|0|0|1|0',card:'old|0|0|0|1|0'}}},
 v538CareerArchive:{'2027':{p1:[{teamId:'old',teamName:'Clube de 2026',goals:28,apps:35,assists:4}]}},
 allTimeStats:{},competitionStats:{'league:eng:1':{p1:{id:'p1',goals:10,apps:12}}},
 v640National:{playerStats:{'2026':{'world-cup':{
  p3:{id:'p3',name:'Jogador da selecao',natCode:'QAT',goals:7,apps:13,teamCode:'QAT',teamName:'Catar'}
 }}}}
};
state=ss;
const f={...scorerFilter};
let r=v18220Collect(ss,f);
assert.equal(r.length,3);
assert.deepEqual(r.map(p=>[p.id,p.goals]),[['p1',35],['p2',17],['p3',7]]);
assert(!ss.scorerArchive.some(a=>a.year===2026),'Do not duplicate large world archives');
const html=v18220ScorersContent(ss,f);
assert(html.indexOf('Artilheiro de 2026')<html.indexOf('Jogador da selecao'));
let team=v18220ClubHTML(ss,r[0],'all');
assert(team.includes('Clube de 2026')&&!team.includes('Clube atual'),team);
const nat=v18220ClubHTML(ss,r[2],'all');
assert(nat.includes('Catar')&&!nat.includes('Clube atual'),nat);
assert.equal(window.GestorFC.historyScorers18377.fromYear(ss,2026).scorers,2);
assert.equal(v18220Collect(ss,{...f,year:'2027'})[0].goals,28,'Legacy 5.38 fallback');
assert.equal(v18220Collect(ss,{...f,year:'2032'})[0].goals,12,'Preserve normal archive');
assert.equal(ss.scorerArchive.length,5,'Keep compact retention');
const other={...ss,v555CareerArchive:{'2026':{n:{old:'Clube de 2026'},p:{p1:'old|20|2|0|0|0'}}}};
assert.equal(v18220Collect(other,f).find(x=>x.id==='p1').goals,2,'No cross-save mixing');
let many={};for(let i=0;i<80000;i++)many['g'+i]='old|20|0|0|0|0';many['star']='old|25|42|7|0|0';
const big={...ss,v555CareerArchive:{'2026':{n:{old:'Clube de 2026'},p:many}}};
assert.equal(window.GestorFC.historyScorers18377.fromYear(big,2026).scorers,1,'Memory-bounded scorer cache');
assert(v18220Collect(big,f).some(p=>p.id==='star'&&p.goals===42));
console.log(JSON.stringify({ok:true,version:'18.377.0',recoveredYear:2026,
 firstTopScorerGoals:35,leaderboard:['p1','p2','p3'],recentArchivePreserved:true,
 legacyArchiveSupported:true,historicalClubsCorrect:true,
 noStateMutation:true,80kUnscoredPlayersExcluded:true}));
'''
 js=mock+'\n'+original+'\n'+patch+'\n'+test
 check=subprocess.run(['node','--input-type=commonjs','-'],input=js,text=True,capture_output=True,timeout=75)
 if check.returncode:raise RuntimeError(check.stderr[-3500:])
 report=json.loads(check.stdout.strip())
 (root/'historical-scorers-18377-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main(sys.argv[1])
