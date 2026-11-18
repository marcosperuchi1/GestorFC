from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

MARK='FUTBR_DELEGATED_RETIREMENT_18346'

def section(text,a,b):
    i=text.find(a)
    if i<0:raise RuntimeError('missing required source start '+a)
    j=text.find(b,i)
    if j<0:raise RuntimeError('missing required source end '+b)
    return text[i:j]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_retirement_vacation_18346.py <project>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src/index.html').read_text(encoding='utf-8')
    for marker in (MARK,
      "function v18346DelegatedRetirement(s)",
      "s.vacation.completed)>0",
      "p.pos==='GOL'?47:45",
      "if(age>=ceiling)return true;",
      "E.shouldAutoRetire549(s,p,snap,chance)",
      "function v91ResetPlayers(s,oldYear)",
      "s.retirements=[...newRetirements",
      "v579ManualRetire"):
        if marker not in html:raise RuntimeError('missing 18.346 integration '+marker)
    if "p.clubId===s.user||chance<=0" in html:raise RuntimeError('old user-club retirement veto remains')
    if "protectedByUser=!!(s.userEmployed&&clubBefore===s.user);" in html:
        raise RuntimeError('old v91 retirement gate remains')
    rollover_body=section(html,'function v91ResetPlayers(s,oldYear)','function v91PromoteAgedYouth(s,t,freeSet){')
    if 'v18346DelegatedRetirement(s)' in rollover_body:
        raise RuntimeError('v91 rollover must not call a retirement helper defined inside a separate engine closure')
    if 's.vacation.startYear' not in rollover_body:
        raise RuntimeError('v91 delegation check must be evaluated in the rollover lexical scope')
    code = "\n".join([
       section(html,'function retirementChance549(s,p,m={})','function v549AutomaticResult('),
       section(html,'function v91RetirementSnapshot(p){','function v91PromoteAgedYouth(s,t,freeSet){')
    ])
    harness=r"""
const assert=require('node:assert/strict');
const clamp=(x,a,b)=>Math.min(b,Math.max(a,x));
const rng=s=>s.roll??.99;
const E={
 clamp,rand:()=>0,rng:s=>s.roll??.99,overall:p=>Number(p.ovr)||70,
 attributes:p=>({att:70,def:65}),copy:x=>JSON.parse(JSON.stringify(x||{})),
 team:(s,id)=>(s.teams||[]).find(t=>t.id===id)||null
};
const v586CurrentPerformance=undefined;
"""
    tests=r"""
E.retirementChance549=retirementChance549;
E.shouldAutoRetire549=shouldAutoRetire549;
const metrics={rating:7.80,recent:7.70,fitness:95,load:0,streak:0,minutes:2600};
function player(id,age,club,pos='ATA',rating=6.2,extra={}){
 return {id,name:id,age,clubId:club,pos,squad:'senior',ovr:75,
  seasonRatingCount58:20,seasonRatingSum58:rating*20,
  lastMatchRating:rating,fitness:88,seasonMinutes58:2400,
  marketReputation586:0,matchLoad545:0,skills:{att:65,def:60,pas:62,pace:65,gk:60},
  contract:3,...extra};
}
function save({delegate=true,active=false,completed=30,startYear=2026,year=2027,roll=.99}={}){
 return {user:'user',userEmployed:true,year,roll,day:0,
  vacation:{delegateTransfers:delegate,active,completed,startYear,untilSeason:false},
  players:{},teams:[{id:'user',name:'Your Club'},{id:'ai',name:'Other Club'}],
  retirements:[{year:2025,id:'historic',name:'Historic Veteran'}]};
}
let s=save({delegate:false,completed:0,startYear:2025});
const survivor=player('survivor',42,'user','ATA',8.0);
assert.equal(shouldAutoRetire549(s,survivor,metrics,.995,0),false,'No delegation preserves human control');
assert.equal(v18346DelegatedRetirement(s),false);
s.players.survivor=survivor;
s.players.forced=player('forced',44,'user');
s.players.goalkeeper=player('goalkeeper',45,'user','GOL',7.9);
s.players.youth=player('youth',48,'ai','ATA',5.8,{squad:'youth'});
s.players.ai=player('ai',44,'ai');
const nonDelegated=v91ResetPlayers(s,2026);
assert(!nonDelegated.retired.has('survivor'),'Outstanding non-delegated veteran must be able to continue at 43');
assert(nonDelegated.retired.has('forced'),'At 45 field player must eventually retire without delegation');
assert(nonDelegated.retired.has('ai'),'Other AI clubs remain eligible');
assert(!nonDelegated.retired.has('goalkeeper'),'Top form goalkeeper can continue until 47');
assert(!nonDelegated.retired.has('youth'),'Youth exempt');
assert.equal(s.retirements.filter(x=>x.id==='historic').length,1,'Old retirement history preserved');
assert.equal(s.retirements.find(x=>x.id==='forced').club,'user');

s=save();
assert.equal(v18346DelegatedRetirement(s),true,'Delegation must remain available at end of vacation');
s.players.professional=player('professional',42,'user','ATA',5.9);
s.players.exception=player('exception',42,'user','ATA',7.9);
s.players.manual=player('manual',36,'user','ATA',7.9,{v579ManualRetire:true,v579RetireClub:'user'});
s.players.youth=player('youth',41,'user','GOL',5.8,{squad:'youth'});
assert.equal(shouldAutoRetire549(s,s.players.professional,metrics,.995,0),true,'Eligible user club treated as AI during delegation');
const delegated=v91ResetPlayers(s,2026);
assert(!delegated.retired.has('exception'),'Excellent form at 43 defers retirement on high roll');
assert(delegated.retired.has('manual'),'Manual announcement still respected');
assert(!delegated.retired.has('youth'),'Youth remains excluded');
assert.equal(s.retirements.find(x=>x.id==='manual').manual,true);
assert.equal(s.retirements.filter(x=>x.id==='historic').length,1);
const star=s.players.exception;
assert.equal(retirementChance549(s,{...star,age:43,pos:'ATA'},metrics)<retirementChance549(s,{...star,age:43,pos:'ATA'},{...metrics,rating:6.2,recent:6.2}),true,'Strong performances should reduce retirement probability');
assert.equal(retirementChance549(s,{...star,age:40,pos:'GOL'},metrics)<retirementChance549(s,{...star,age:40,pos:'ATA'},metrics),true,'Goalkeepers retire later');
assert.equal(shouldAutoRetire549(s,{...star,age:46,pos:'GOL'},metrics,.001,.99),false,'46yo goalkeepers may remain');
assert.equal(shouldAutoRetire549(s,{...star,age:47,pos:'GOL'},metrics,.001,.99),true,'47yo goalkeeper ceiling');
assert.equal(shouldAutoRetire549(s,{...star,age:45,pos:'ATA'},metrics,.001,.99),true,'45yo outfield ceiling');
assert.equal(shouldAutoRetire549(s,{...star,age:43,pos:'ATA',squad:'youth'},metrics,.995,0),false,'No youth retirement');

// Multi-season deterministic stress: even with excellent form and a high random roll,
// a delegated club cannot accumulate immortal veteran players.
s=save();
let id='longcareer',years=0;
s.players[id]=player(id,35,'user','ATA',8.4,{star:true});
for(years=0;years<12;years++){
 s.year=2027+years;
 s.vacation.startYear=s.year-1;
 s.vacation.completed=38;
 const round=v91ResetPlayers(s,s.year-1);
 if(round.retired.has(id))break;
}
assert(years<12,'12 seasons must not leave a player active indefinitely');
assert.equal(s.retirements.filter(x=>x.id===id).length,1,'One historical retirement per player');
assert(s.retirements.find(x=>x.id===id).age<=45,'Career limit enforced');
console.log('PASS 18.346: delegated vacation, user control, performance, age ceilings, manual overrides, other clubs, history, 12-year career');
"""
    proc=subprocess.run(['node','-e',harness+'\n'+code+'\n'+tests],text=True,capture_output=True,timeout=60)
    if proc.returncode:
        raise RuntimeError('18.346 real engine regression failed:\n'+proc.stderr[-10000:])
    print(proc.stdout.strip())
    report={
      'ok':True,'version':'18.346',
      'delegatedVacationEnablesRetirement':True,
      'humanManualControlPreservedOutsideDelegation':True,
      'exceptionalFormCanDelay':True,
      'outfieldCeilingAge45':True,'goalkeeperCeilingAge47':True,
      'nonUserAiRetirementPreserved':True,
      'manuallyMarkedRetirementPreserved':True,
      'youthExempt':True,
      'retirementHistoryRetained':True,
      'multiSeasonOldPlayersEventuallyRetire':True,
      'realGameCodeExecuted':True
    }
    (root/'retirement-vacation-18346-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
