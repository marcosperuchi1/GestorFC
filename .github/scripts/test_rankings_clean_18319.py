from pathlib import Path
import sys, re, json, subprocess

def main():
    root=Path(sys.argv[1]).resolve()
    html=(root/'src'/'index.html').read_text(encoding='utf-8')
    required=[
      'FUTBR_RANK_CORE_18319_START',
      "else if(view==='clubrankings')v18220PageHTML=v86ClubRankingPage();",
      'Motor limpo 18.319',
      "/* 18.319: previous rank warm-up disabled */"
    ]
    for key in required:
      if key not in html: raise RuntimeError('Invalid ranking entrypoint: '+key)
    for ident in ['futbr-ranking-18318','gfc-v18317-title-engine',
                  'gfc-v18316-rank-rollover-carry','gfc-v18315-sparse-title-ranking',
                  'gfc-v18314-ranking-cache-fix']:
      if '<script id="'+ident+'">' in html: raise RuntimeError('Legacy module still installed '+ident)
    engine=re.search(r'/\* FUTBR_RANK_CORE_18319_START \*/([\s\S]*?)/\* FUTBR_RANK_CORE_18319_END \*/',html)
    renderer=re.search(r'function v86ClubRankingPage\(\)\{([\s\S]*?)\n\}\n// Desliga inteiramente',html)
    if not engine or not renderer:raise RuntimeError('Native engine was not correctly installed')
    body='/* FUTBR_RANK_CORE_18319_START */'+engine.group(1)+'/* FUTBR_RANK_CORE_18319_END */'
    page='function v86ClubRankingPage(){'+renderer.group(1)+'\n}'
    if 'v86EnsureBuild(false)' in page:raise RuntimeError('Legacy async worker still in native page')
    if 'v18319EnsureRanking(state)' not in page:raise RuntimeError('Native renderer does not use clean engine')
    test=r"""
const assert=require('assert');
const window={GestorFC:{}},performance=require('perf_hooks').performance;
const nf=new Intl.NumberFormat('pt-BR'),V86_RANK_LIMIT=1000,V86_RANK_PAGE=50;
const WorldCatalog={countries:[
 {id:'bra',name:'Brasil',confederation:'CONMEBOL'},
 {id:'esp',name:'Espanha',confederation:'UEFA'}]};
const E={country:id=>WorldCatalog.countries.find(x=>x.id===id)||null,
 team:(s,id)=>s.teams.find(x=>x.id===id)||null,
 normName:x=>String(x||'').toLowerCase(),
 CONF_KEYS:['CONMEBOL','UEFA']};
const v632ClubFilter={query:'',conf:'all',country:'all',page:0};
const v86RankCache=null;
const v633RankWindow=s=>({start:s.year-3,end:s.year});
const esc=x=>String(x||'');
const teamButton=t=>t.name;
const badge=()=>'<i>Escudo</i>';
const v532FlagHTML=()=>'',v530CountryNat=x=>x;
const button=(id,text)=>'<button>'+text+'</button>';
const v183TitleCells=r=>{
 let counts={L:0,C:0,I:0,M:0,R:0,O:0};
 for(const title of r.titles||[]){
  const key=String(title.key||'');
  const cat=key.startsWith('league:')?'L':key.startsWith('cup:')?'C':
  key==='cwc'||key==='icup'?'M':key==='recopa'?'R':
  ['lib','ucl'].includes(key)?'I':'O';
  counts[cat]++;
 }
 return Object.values(counts).map(n=>'<td>'+n+'</td>').join('');
};
const teams=Array.from({length:1400},(_,i)=>({id:'cl'+i,name:'Clube '+i,country:i%2?'bra':'esp',division:1,base:50+i%75,
 stats:{p:38,w:20+i%15,d:5,l:3,pts:65+i%20}}));
let state={
 year:2026,day:38,seasonDone:true,teams,coaches:{a:{titles:[{year:2025,club:'cl4',key:'recopa',name:'Recopa'}]}},
 worldHistory:[{year:2025,countries:[{country:'bra',champion:'cl1',cup:'cl2',secondChampion:'cl3'}]}],
 internationalHistory:[{year:2025,id:'lib',name:'Libertadores',champion:'cl4',points:{cl4:13}}],
 cupWinners:{bra:'cl2'},competitions:{cwc:{id:'cwc',name:'Mundial de Clubes',champion:'cl5'},
  mls:{id:'mls',champion:'cl6'}},
 v652ClubPerformanceHistory:[{year:2025,clubs:{cl4:{leaguePoints:13,cupPoints:4}}}]
};
""" + body + '\n' + page + r"""
const first=v86ClubRankingPage();
assert(first.includes('Motor limpo 18.319'),'actual page did not change');
assert(first.includes('Ranking de Clubes'));
assert(!first.includes('primeira montagem'));
assert(!first.includes('…'),'the renderer still contains provisional data');
const api=window.GestorFC.rankClean18319;
assert(api&&api.version==='18.319');
const rows=api.rows();
assert.equal(rows.length,1000);
assert(rows.every(x=>Number.isFinite(x.totalPoints)));
assert(rows.every((x,i)=>i===0||rows[i-1].totalPoints>=x.totalPoints));
assert.equal(rows.find(x=>x.id==='cl1').titles.filter(t=>t.key.startsWith('league:')).length,1);
assert.equal(rows.find(x=>x.id==='cl2').titles.filter(t=>t.key.startsWith('cup:')).length,2);
assert.equal(rows.find(x=>x.id==='cl4').titles.length,2);
assert.equal(rows.find(x=>x.id==='cl5').titles.length,1);
assert(first.includes('Bônus títulos')&&first.includes('Coef.'));
assert.equal(api.status().builds,1);
for(let i=0;i<25;i++)v86ClubRankingPage();
assert.equal(api.status().builds,1,'ranking recalculated on each open');
assert(api.status().hits>=25);
v632ClubFilter.conf='UEFA';
assert(v86ClubRankingPage().includes('Espanha'),'filter not applied');
assert.equal(api.status().builds,1);
state.day=39;
v86ClubRankingPage();
assert.equal(api.status().builds,2,'new day was ignored');
console.log(JSON.stringify({ok:true,version:'18.319',realRenderer:true,
 teams:rows.length,cacheHits:api.status().hits,noAsyncBuild:true,
 titleLedger:true,recordFields:true,filter:true,builds:api.status().builds,
 firstBuildMs:api.status().elapsedMs}));
"""
    path=root/'.rank18319-smoke.js';path.write_text(test,encoding='utf-8')
    try:
      run=subprocess.run(['node',str(path)],capture_output=True,text=True,timeout=45)
    finally:path.unlink(missing_ok=True)
    if run.returncode:
      raise RuntimeError('Native ranking smoke failed:\n'+(run.stderr or run.stdout)[-9000:])
    result=json.loads(run.stdout.strip().splitlines()[-1])
    if not result.get('ok'):raise RuntimeError('Test result not OK')
    (root/'ranking-clean-18319-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
