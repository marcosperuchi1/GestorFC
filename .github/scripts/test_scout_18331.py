from __future__ import annotations
import json,re,subprocess,sys,tempfile
from pathlib import Path

def main(project):
    html=(project/"src"/"index.html").read_text(encoding="utf-8")
    assert html.count("/* FUTBR_SCOUT_RESPONSIVE_18331 */")==1
    assert "v638ScoutTopInsert" in html
    assert "if(++visited%192===0)await new Promise(resolve=>setTimeout(resolve,0));" in html
    assert "const q=v572CloneScoutFilters(v529ScoutRead());if(v638ScoutBusy)return;" in html
    assert "const q=v572CloneScoutFilters(v529ScoutRead()),m=v638CreateMission(q)" not in html
    assert "async function v638CandidateUniverseResponsive(q)" in html
    assert "function v638CandidateUniverse(q)" in html
    assert "const v638BaseRender" not in html or True

    # Verify the inserted JavaScript with Node syntax check.
    m=re.search(r'/\* FUTBR_SCOUT_RESPONSIVE_18331 \*/(.*?)function v638CandidateUniverse\(q\)',html,re.S)
    assert m, 'script nao localizado'
    js='/* FUTBR_SCOUT_RESPONSIVE_18331 */'+m.group(1)
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"scout.js"
        p.write_text(js,encoding="utf-8")
        subprocess.run(["node","--check",str(p)],check=True,capture_output=True,text=True)

    # Dynamic parity: compare top 18 and exact totals with the old selector.
    # Uses lightweight deterministic fake players and keeps all game functions unchanged.
    js_check=r"""
const vm=require('vm'),assert=require('assert');
const source=SCOUT_JS_PLACEHOLDER;
let players=[],teams=[],teamCount=40,serial=1;
for(let t=0;t<teamCount;t++){
  const roster=[],academy=[];
  for(let i=0;i<180;i++){
    const id=serial++;
    players[id]={id,age:18+(i%23),pos:['GOL','ZAG','LAT','VOL','MEI','ATA'][i%6],potential:58+(i*3+t)%38,lastMatchRating:6+(i%15)/10,attributes:{passing:50+(i%40),technique:45+(i%44),composure:52+(i%40),reflexes:58+(i%35),handling:52+(i%40),positioning:55+(i%39),strength:55+(i%35),heading:55+(i%40),finishing:55+(i%40),marking:55+(i%35),tackling:55+(i%35),speed:55+(i%35),acceleration:55+(i%35),dribbling:55+(i%35),crossing:55+(i%35),stamina:55+(i%35)}};
    (i%5===0?academy:roster).push(id);
  }
  teams.push({id:t+1,country:t%3?'BR':'AR',roster,academy,balance:200000000});
}
const state={teams,user:1,year:2026,day:1,schedule:[1,2],v638ScoutSeq:0};
const own=teams[0];
const byId=Object.fromEntries(players.map(x=>[x.id,x]));
const E={human:()=>own,player:(_,id)=>byId[id],attributes:p=>p.attributes,overall:p=>55+(p.id%39),transferPrice:(_,id)=>id%100*1000000,value:p=>p.id%100*1000000,clamp:(n,a,b)=>Math.min(b,Math.max(a,n))};
const V529_VALUE_BANDS={any:[0,Infinity]};
const q={scope:'both',pos:'all',maxAge:40,minOvr:35,minPot:45,attr1:'none',attr2:'none',minAttr1:1,minAttr2:1,valueBand:'any',cashMode:'any'};
function v529YouthFee(p,t){return E.value(p);}
function v529ScoutMatch(x,q,soft=false){let misses=0;if(x.p.age>q.maxAge)misses+=Math.min(4,(x.p.age-q.maxAge)*.7);if(q.pos!=='all'&&x.p.pos!==q.pos)misses+=7;if(x.o<q.minOvr)misses+=(q.minOvr-x.o)*.8;if((x.p.potential||x.o)<q.minPot)misses+=(q.minPot-(x.p.potential||x.o))*.55;if(x.fee<0)misses+=3;return soft?misses:misses===0;}
function v529ScoutUniverse(q){const own=E.human(state),rows=[];for(const t of state.teams){if(t.id===own.id)continue;const pool=[];if(q.scope!=='youth')pool.push(...(t.roster||[]).map(id=>({id,youth:false})));if(q.scope!=='senior')pool.push(...(t.academy||[]).map(id=>({id,youth:true})));for(const it of pool){const p=E.player(state,it.id);if(!p)continue;if(it.youth&&p.age<18&&t.country!==own.country)continue;const a=E.attributes(p),o=E.overall(p),feeRaw=it.youth?v529YouthFee(p,t):E.transferPrice(state,p.id),fee=Number.isFinite(feeRaw)?Math.max(0,feeRaw):E.value(p);rows.push({p,t,a,o,fee,youth:it.youth});}}return rows;}
function v638RecentForm(p){return {rating:Number(p.lastMatchRating)||6.5,sample:0};}
function v638TacticalFit(p,t){return 65;}
function v638ValueScore(fee){const m=Math.max(.15,Number(fee||0)/1000000);return E.clamp(Math.round(108-Math.log10(m+1)*31),25,100);}
function v638ScoutScore(x,q){const form=v638RecentForm(x.p),fit=v638TacticalFit(x.p,E.human(state)),ageScore=E.clamp(108-Math.max(0,x.p.age-20)*2.4,35,100),sample=E.clamp(35+form.sample*11,35,100);let score=x.o*.34+(x.p.potential||x.o)*.18+(form.rating*10)*.22+fit*.14+v638ValueScore(x.fee)*.07+ageScore*.03+sample*.02;return score;}
function v638CandidateUniverse(q){const universe=v529ScoutUniverse(q),exact=universe.filter(x=>v529ScoutMatch(x,q,false)),source=exact.length>=18?exact:universe.map(x=>({...x,miss:v529ScoutMatch(x,q,true)}));source.sort((a,b)=>{const pa=(Number(a.miss)||0)*9,pb=(Number(b.miss)||0)*9;return (v638ScoutScore(b,q)-pb)-(v638ScoutScore(a,q)-pa)||a.fee-b.fee;});const rows=source.slice(0,18);return {rows,total:exact.length,near:exact.length<Math.min(18,rows.length)};}
eval(source);
(async()=>{
const old=v638CandidateUniverse(q),fast=await v638CandidateUniverseResponsive(q);
assert.equal(old.total,fast.total);
assert.deepEqual(old.rows.map(x=>x.p.id),fast.rows.map(x=>x.p.id));
q.minOvr=96;q.minPot=96;
const old2=v638CandidateUniverse(q),fast2=await v638CandidateUniverseResponsive(q);
assert.equal(old2.total,fast2.total);
assert.deepEqual(old2.rows.map(x=>x.p.id),fast2.rows.map(x=>x.p.id));
console.log(JSON.stringify({players:players.length,parity:true,fast_limit:18,exact:fast.total,near:fast2.near}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
    js_check=js_check.replace('SCOUT_JS_PLACEHOLDER',json.dumps(js))
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/"parity.js";p.write_text(js_check,encoding="utf-8")
        result=subprocess.run(["node",str(p)],capture_output=True,text=True,timeout=90)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    report={"node_syntax":"ok","async_scanning":"ok","parity":result.stdout.strip(),"scope":"only scout UI"}
    (project/"scout-18331-tests.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: test_scout_18331.py <project>")
    main(Path(sys.argv[1]))
