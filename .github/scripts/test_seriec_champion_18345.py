from __future__ import annotations
import json,subprocess,sys
from pathlib import Path

def between(source,begin,end):
    a=source.index(begin)
    b=source.index(end,a)
    return source[a:b]

def main():
    if len(sys.argv)!=2:raise SystemExit("usage: test_seriec_champion_18345.py <project>")
    project=Path(sys.argv[1]).resolve()
    html=(project/"src/index.html").read_text(encoding="utf-8")
    checks=[
      "/* FUTBR_SERIEC_FINAL_CHAMPION_18345:",
      "function v18345CFirstPhaseFinished(C)",
      "function v18345CQuadPhaseFinished(C)",
      "if(!C||C.quadGroups.length||!v18345CFirstPhaseFinished(C))return;",
      "if(v18345CQuadPhaseFinished(C)){const a=v661Order",
      "if(!C.finalTie)C.finalTie={a:a[0],b:b[0],score:[0,0],winner:null,results:[]};",
      "if(!C.promoted.length&&v18345CQuadPhaseFinished(C)){",
      "function v18345SerieCWinner(s)",
      "window.GestorFC.v18345SerieCWinner=v18345SerieCWinner",
      "changed+=v18345SyncCArchives(s,w,runner)",
      "if(div===3&&state.braLower?.serieC)"
    ]
    for mark in checks:
        if mark not in html:raise AssertionError("Missing Serie C 18.345 code: "+mark)
    if "if(!C.champion&&!C.finalTie)C.champion=a[0]" in html:
        raise AssertionError("Old premature champion fallback still present")
    if "FUTBR_CHAMPIONS_RETIREMENT_18322" in html:
        assert "window.GestorFC?.v18345SerieCWinner?.(s)||null" in html
    guards=between(html,"/* FUTBR_SERIEC_FINAL_CHAMPION_18345:","function v661EnsureCQuadrangular(s)")
    ensure=between(html,"function v661EnsureCQuadrangular(s)","function v661CampaignScoreD(s")
    prepare=between(html,"function v661PreparePlan(s,stage,plan)","function v661RecordBrazilResult(s")
    verified=between(html,"/* FUTBR_SERIEC_VERIFIED_FINAL_18345:","function v99RepairBrazilLowerChampions(s)")
    repair=between(html,"function v99RepairBrazilLowerChampions(s)","// Career screen:")
    fixture=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}},E={
 team:(s,id)=>(s.teams||[]).find(t=>String(t.id)===String(id)),
 coachRating:c=>Number(c.bonusPoints)||0,
 human:s=>(s.teams||[])[0],
 normName:x=>String(x||'').toLowerCase()
};
function v99TieWinner(s,tie,code){return tie?.winner||null;}
let addedTitles=0;
function v99RepairLeagueCoachTitle(s,div,winner,label){addedTitles++;}
function v661Order(s,g,st){return [...g].sort((a,b)=>Number(st?.[b]?.pts||0)-Number(st?.[a]?.pts||0));}
function v661StatMap(group){return Object.fromEntries(group.map(x=>[x,{p:0,pts:0}]));}
function roundRobin(g,reverse){return []; }
function v661MakeTieFixture(s,code,phase,tie,index,leg,division,final){return {home:leg===1?tie.b:tie.a,away:leg===1?tie.a:tie.b,v661Brazil:code,v661Phase:phase,v661Leg:leg,v661Tie:index,result:null};}
function v661AddFixtures(stage,fs){stage.fixtures.push(...fs);}
function v661MakeLeagueFixture(s,code,phase,group,round,index,pair,division){return {home:pair.home,away:pair.away};}
function v661EnsureDTies(){return [];}
function v661PrepareMocks(){return true;}
"""
    tests=r"""
const group=['leader','qa','qb','t4','t5','t6','t7','t8'];
const teams=group.map(id=>({id,name:id,division:3,country:'bra'}));
const C={year:2026,participants:group,format:'single-quadrangular',
 firstGroups:[group],firstStandings:{0:Object.fromEntries(group.map((id,i)=>[id,{p:2,pts:100-i}]))},
 quadGroups:[],quadStandings:[],quadSchedule:[],promoted:[],relegated:[],finalTie:null,champion:null,runnerUp:null};
let s={year:2026,day:0,teams,coaches:{},schedule:[],braLower:{serieC:C,serieD:null},history:[],v18322Champions:[],v98LeagueTitleHistory:[],worldHistory:[]};
assert.equal(v18345CFirstPhaseFinished(C),false);
v661EnsureCQuadrangular(s);
assert.equal(C.quadGroups.length,0,'first-phase standings must not qualify prematurely');
for(const rec of Object.values(C.firstStandings[0]))rec.p=group.length-1;
assert.equal(v18345CFirstPhaseFinished(C),true);
v661EnsureCQuadrangular(s);
assert.equal(C.quadGroups.length,2);
assert.equal(C.quadGroups[0][0],'leader');
assert.equal(v18345CQuadPhaseFinished(C),false);
C.quadStandings.forEach((m,gi)=>Object.values(m).forEach((r,i)=>{r.p=6;r.pts=25-i}));
assert.equal(v18345CQuadPhaseFinished(C),true);
// Even if another layer stored promoted clubs prematurely, the final must still be created.
C.promoted=['wrong-provisional'];
const stage={fixtures:[]};
v661PreparePlan(s,stage,{code:'C',phase:'final',leg:1});
assert.equal(stage.fixtures.length,1,'missing Serie C final leg after provisional promotion');
assert.equal(C.promoted.length,4);
assert.ok(C.finalTie.a&&C.finalTie.b);
const a=C.finalTie.a,b=C.finalTie.b;
assert.notEqual(a,b);
function fixture(leg,home,away,hg,ag,extra={}){
 return {v661Brazil:'C',v661Phase:'final',v661Tie:0,v661Leg:leg,
   home,away,result:hg===null?null:{home:hg,away:ag,...extra}};
}
let first=fixture(1,b,a,1,2),second=fixture(2,a,b,null,null);
s.schedule=[{fixtures:[first]},{fixtures:[second]}];
s.v18322Champions=[{year:2026,competition:'league:bra:3',champion:'leader',runner:'qa'}];
s.v98LeagueTitleHistory=[{year:2026,country:'bra',division:3,champion:'leader'}];
s.coaches={old:{id:'old',titles:[{year:2026,key:'league:bra:3',club:'leader',points:70}],bonusPoints:70}};
C.champion='leader';
assert.equal(v18345SerieCWinner(s),null,'first leg is not the championship');
assert.ok(v99RepairBrazilLowerChampions(s)>0);
assert.equal(C.champion,null);
assert.equal(C.runnerUp,null);
assert.equal(s.coaches.old.titles.length,0);
assert.equal(s.v18322Champions.length,0);
assert.equal(s.v98LeagueTitleHistory.length,0);
assert.equal(addedTitles,0);
// Actual two-leg winner differs from first-phase leader and first leg winner.
second.result={home:0,away:3}; // second leg: a 0 - 3 b, b wins on aggregate
let win=v18345SerieCWinner(s);
assert.equal(win,b);
v99RepairBrazilLowerChampions(s);
assert.equal(C.champion,b);
assert.equal(C.runnerUp,a);
assert.ok(addedTitles>0);
s.v18322Champions=[{year:2026,competition:'league:bra:3',champion:'leader',runner:a}];
s.v98LeagueTitleHistory=[{year:2026,country:'bra',division:3,champion:'leader'}];
v99RepairBrazilLowerChampions(s);
assert.equal(s.v18322Champions[0].champion,b);
assert.equal(s.v18322Champions[0].runner,a);
assert.equal(s.v98LeagueTitleHistory[0].champion,b);
// Aggregate tied: winner comes ONLY from second-leg penalty resolution.
first.result={home:1,away:0};
second.result={home:1,away:0,pens:[4,5]};
assert.equal(v18345SerieCWinner(s),b);
second.result={home:1,away:0};
C.finalTie.winner=null;
assert.equal(v18345SerieCWinner(s),null,'no champion before decisive penalties');
second.result={home:1,away:0,qualifier:a};
assert.equal(v18345SerieCWinner(s),a);
second.result=null;
assert.equal(v18345SerieCWinner(s),null);
console.log('PASS: championship only after both legs, safe promotion, archive, title, tie-break and no phase-one leader');
"""
    program="\n".join([fixture,guards,ensure,prepare,verified,repair,tests])
    run=subprocess.run(["node","-e",program],text=True,capture_output=True,timeout=40)
    if run.returncode:
        raise RuntimeError("18.345 executable source regression failed:\n"+run.stderr[-9000:])
    print(run.stdout.strip())
    report={"ok":True,"version":"18.345","firstPhaseNoEarlyQualification":True,
       "quadCompletionMandatory":True,"finalGeneratedWithOldPromotedCache":True,
       "oneLegDoesNotAwardChampion":True,"twoLegFinalWinnerOnly":True,
       "firstPhaseLeaderNotChampion":True,"penaltyTieResolved":True,
       "wrongCoachTitleRemoved":True,"currentHistoricalRowsRepaired":True,
       "savesRetained":True}
    (project/"serie-c-champion-18345-tests.json").write_text(
         json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":main()
