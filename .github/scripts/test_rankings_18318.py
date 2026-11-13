from pathlib import Path
import sys,subprocess,json,re
def main():
 root=Path(sys.argv[1]);html=(root/'src'/'index.html').read_text(encoding='utf-8')
 match=re.search(r'<script id="futbr-ranking-18318">([\s\S]*?)</script>',html)
 if not match:raise RuntimeError('ranking 18.318 missing')
 js=r"""
const assert=require('assert');
let state=null,view='clubrankings';
let v18221ClubRankPage=function(){return 'old';};
let v86ClubRankingPage=function(){return 'old';};
let v632ClubRankingPage=function(){return 'old';};
let v18221ScheduleClubRankPrewarm=function(){};
let invalidations=0;
function v18221InvalidateClubRanking(){invalidations++}
function v677RankingTabs(){return '<nav>Ranking tabs</nav>'}
const E={clubRankingRows633(){throw Error('legacy rebuild should not run')}};
const events={};
const document={addEventListener(name,fn){events[name]=fn},querySelector(){return null}};
const window={GestorFC:{}};
""" + match.group(1) + r"""
const teams=Array.from({length:120},(_,i)=>({id:'t'+i,name:'Clube '+i,country:'Brasil',conf:'CONMEBOL',base:60+i%20}));
const rows={};const order=[];
for(let i=0;i<120;i++){const id='t'+i;order.push(id);rows[id]={id,conf:'CONMEBOL',points:i,performancePoints:i,totalPoints:i,titlePoints:0};}
state={year:2026,teams,worldHistory:[{year:2026,countries:[{country:'Brasil',champion:'t1',cup:'t2'}]}],internationalHistory:[{year:2026,id:'libertadores',champion:'t3'}],cupWinners:{},competitions:{},v18300ClubRankingStore:{revision:1,recordRevision:1,rows,order,records:{t0:{games:5,wins:3,draws:1,losses:1}}}};
let html=v18221ClubRankPage();
assert(html.includes('Ranking de Clubes'));
assert(!html.includes('primeira montagem 0%'));
assert(!html.includes('---'));
assert.equal(window.GestorFC.rankRebuild18318.rows().length,120);
assert.equal(window.GestorFC.rankRebuild18318.stats.builds,1);
const a=window.GestorFC.rankRebuild18318.rows().find(x=>x.id==='t1');
const b=window.GestorFC.rankRebuild18318.rows().find(x=>x.id==='t2');
const c=window.GestorFC.rankRebuild18318.rows().find(x=>x.id==='t3');
assert.equal(a.ledger.L,1);assert.equal(b.ledger.C,1);assert.equal(c.ledger.I,1);
assert(a.bonus>0&&b.bonus>0&&c.bonus>0);
assert.equal(window.GestorFC.rankRebuild18318.rows().find(x=>x.id==='t0').games,5);
for(let i=0;i<10;i++)v18221ClubRankPage();
assert.equal(window.GestorFC.rankRebuild18318.stats.builds,1,'reopening rebuilds entire ranking');
state.v18300ClubRankingStore.revision++;
const newer=window.GestorFC.rankRebuild18318.rows();
assert.equal(window.GestorFC.rankRebuild18318.stats.builds,2,'revision failed to invalidate');
assert(newer.every((r,i)=>i===0||newer[i-1].score>=r.score),'ranking unsorted');
console.log(JSON.stringify({ok:true,version:'18.318',teams:newer.length,titleColumns:true,bonus:true,records:true,cacheHits:window.GestorFC.rankRebuild18318.stats.hits,sort:true,buildingStuck:false}));
"""
 p=root/'.rank18318.test.js';p.write_text(js,encoding='utf-8')
 try:r=subprocess.run(['node',str(p)],capture_output=True,text=True,timeout=40)
 finally:p.unlink(missing_ok=True)
 if r.returncode:raise RuntimeError((r.stderr or r.stdout)[-6000:])
 result=json.loads(r.stdout.strip().splitlines()[-1])
 (root/'ranking-rebuild-18318-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result))
if __name__=='__main__':main()
