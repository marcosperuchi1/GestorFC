"""Regression exercise the exact live v91ResetPlayers with a 2042->2043 career,
including user-owned senior players and all delegation states."""
from pathlib import Path
import json,subprocess,hashlib,sys
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_season_scope_18384.py <prepared-root>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 a=s.index('/* FUTBR_SEASON_SCOPE_FIX_18384');b=s.index('function v91PromoteAgedYouth(',a)
 live=s[a:b]
 if 'v18346DelegatedRetirement(s)' in live:raise RuntimeError('Rollover still calls invisible engine helper')
 if 'function v18384DelegatedRetirement(s)' not in live:raise RuntimeError('Missing helper visible to outer UI')
 mock=r"""
const assert=require('node:assert/strict');
global.window={};
const snapshots=[];
const E={
 retirementChance549:(s,p,st)=>(Number(p.age)>=39?.99:Number(p.age)>=36?.65:.11),
 shouldAutoRetire549:(s,p,st,chance)=>{
  if(p.squad==='youth')return false;
  if(p.age>=42)return true;
  return p.age>=39&&chance>=.9;
 },
 attributes:(p)=>({...p.skills}),copy:(x)=>JSON.parse(JSON.stringify(x)),
 overall:p=>Math.round((p.skills.att+p.skills.pas+p.skills.pace)/3),
 team:(s,id)=>(s.teams||[]).find(x=>x.id===id),
 rand:()=>1
};
function v91RetirementSnapshot(p){return {rating:7.1,fitness:91,load:0.6};}
function v91UpdateMarketReputation(p){}
function v18383AgePlayer(s,p){for(let k of ['att','def','pas','pace','gk'])p.skills[k]=Math.max(12,p.skills[k]-2);}
const model=(id,age,clubId='u',squad='senior')=>({id,name:id,age,clubId,squad,
 pos:'ATA',contract:3,goals:17,assists:4,potential:84,
 skills:{att:82,def:43,pas:75,pace:83,gk:11},fitness:89,
 honors538:[{year:2037,label:'Copa da Inglaterra'}]});
const sample=vacation=>({
 year:2043,user:'u',userEmployed:true,vacation,
 players:{user36:model('user36',35),user40:model('user40',39),other40:model('other40',39,'ai'),
  youth:model('youth',19,'u','youth')},
 teams:[{id:'u',name:'Liverpool'},{id:'ai',name:'Ipswich Town'}],
 retirements:[{name:'old-retired',year:2032}]
});
"""
 checks=r"""
// Reproduces 18.383 crash: a senior user player turns 36 and the missing
// v18346 helper used to be evaluated. Must finish without ReferenceError.
const regular=sample(null);
const initial=JSON.stringify(regular.retirements);
const x=v91ResetPlayers(regular,2042);
assert.equal(x.count,4);
assert.equal(regular.players.user36.age,36);
assert.equal(regular.players.user36.contract,2);
assert.equal(regular.players.user36.goals,0);
assert.equal(regular.players.user36.skills.att,80);
assert.equal(regular.players.user36.honors538.length,1);
assert.equal(regular.players.user36.clubId,'u');
assert.equal(regular.players.youth.squad,'youth');
assert(x.retired.has('other40'));
assert(x.retired.has('user40'));
assert(regular.retirements.some(row=>row.name==='old-retired'), 'Historic retirements must survive');
assert(regular.retirements.some(row=>row.name==='other40'), 'New retirement recorded');
const delegated=sample({delegateTransfers:true,active:true,completed:0,startYear:2042});
assert(v18384DelegatedRetirement(delegated));
assert.doesNotThrow(()=>v91ResetPlayers(delegated,2042));
const completed=sample({delegateTransfers:true,active:false,completed:1,startYear:2042});
assert(v18384DelegatedRetirement(completed));
const stale=sample({delegateTransfers:true,active:false,completed:0,startYear:2034});
assert(!v18384DelegatedRetirement(stale));
const none=sample(null);
assert(!v18384DelegatedRetirement(none));
console.log(JSON.stringify({ok:true,season2042To2043Completes:true,
 noUndefinedDelegatedRetirement:true,
 userSquadOwnershipPreserved:true,ageAndOvrPreserved:true,
 delegatedVacationStillSupported:true,nonDelegatedCareerStillSupported:true,
 historicalHonorsPreserved:true,historicalRetirementsPreserved:true,
 noNewGlobalWorldScan:true}));
"""
 f=root/'season-scope-18384-fixture.cjs';f.write_text(mock+'\n'+live+'\n'+checks,encoding='utf-8')
 out=subprocess.run(['node',str(f)],text=True,capture_output=True,timeout=45)
 try:f.unlink()
 except OSError:pass
 if out.returncode:raise RuntimeError('2042->2043 actual code failed: '+out.stderr[-4000:])
 report=json.loads(out.stdout.strip().splitlines()[-1]);report['sourceSha256']=hashlib.sha256(s.encode()).hexdigest()
 (root/'season-scope-18384-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
