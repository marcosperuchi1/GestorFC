from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

def between(source,start,end,label):
    i=source.find(start)
    j=source.find(end,i+len(start)) if i>=0 else -1
    if i<0 or j<0:raise RuntimeError('Source section missing: '+label)
    return source[i:j]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_unemployed_turbo_18327.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src'/'index.html').read_text(encoding='utf-8')
    full=between(html,'  function v33UseFullVacationEngine(s,f,stage){',
        '  function v33TurboPick(s,ids,kind){','match engine')
    hybrid=between(html,'  function v33VacationMatch(s,f,stage){',
        '  function fastMatch(s,f,comp){','hybrid selector')
    offer_hook=between(html,'const v636BaseStartSimulation=v53StartSimulation;',
        'const v636BaseAdvanceDay=E.advanceDay;','offer hook')
    wait=between(html,'async function v89RunJobWait(){',
        'const v89BaseCareerPage=careerPage;','unemployed fast forward')
    expected="if(s?.userEmployed===false&&!s?.v640National?.userTeam)return false;"
    if full.count(expected)!=1:raise RuntimeError('Unemployed Turbo must override full engine and former-user-club guard')
    if "if(f.home===s.user||f.away===s.user)return true;" not in full:raise RuntimeError('Human club games lost their protection')
    if "await v53StartSimulation('dayfast');" not in wait or "await v53StartSimulation('day');" in wait:
        raise RuntimeError('Unemployed job wait still uses slow day mode')
    if "mode==='dayfast')v636AfterRound(state,before)" not in offer_hook:
        raise RuntimeError('Coach offer generation not enabled for dayfast')
    if 'FUTBR_UNEMPLOYED_TURBO_18327' not in html:
        raise RuntimeError('Unemployed Turbo runtime marker missing')
    js=r"""
const assert=require('node:assert/strict');
const V33_FULL_ENGINE_COUNTRIES=new Set(['bra','arg','eng','esp']);
const V33_FULL_STAGE_TYPES=new Set(['international','world','national','intercontinental']);
function team(s,id){return s.teams.find(x=>x.id===id)||null}
function fastMatch(){return {engine:'full',goals:1,assists:1}}
function v33TurboFastMatch(){return {engine:'turbo',goals:1,assists:1}}
const s={user:'former',userEmployed:false,v640National:null,vacation:{active:false},
 teams:[{id:'former',country:'bra',division:1},{id:'other',country:'bra',division:1},
 {id:'other2',country:'eng',division:1}]};
""" + full + hybrid + r"""
const oldClub={home:'former',away:'other',country:'bra',competition:'league:bra:1'};
const major={home:'other',away:'other2',country:'eng',competition:'international:ucl'};
const results=[];
for(const [fixture,stage] of [
  [oldClub,{type:'league'}],[major,{type:'international'}],
  [{home:'other',away:'other2',country:'bra'},{type:'cup'}],
  [{home:'other',away:'other2',country:'bra'},{type:'world'}]
]){
 const r=v33VacationMatch(s,fixture,stage);
 assert.equal(r.engine,'turbo','Unemployed fixture must use Turbo: '+stage.type);
 results.push(stage.type);
}
assert.equal(s.v33HybridStats.turbo,4);
s.userEmployed=true;
assert.equal(v33VacationMatch(s,oldClub,{type:'league'}).engine,'full','Current human club must keep detailed engine');
assert.equal(v33VacationMatch(s,major,{type:'international'}).engine,'full','Employed major tournament must keep detailed engine');
s.userEmployed=false;s.v640National={userTeam:'BRA'};
assert.equal(v33VacationMatch(s,major,{type:'international'}).engine,'full','National career uses existing engine');
s.userEmployed=true;s.v640National=null;
assert.equal(v33VacationMatch(s,{home:'other',away:'other2',country:'bra'},
 {type:'international'}).engine,'full','Engine restored after employment');

let state={year:2027,day:0,user:'former',userEmployed:false,seasonDone:false,
 v636CoachOffers:[],coaches:{},schedule:[{},{},{},{},{},{}]};
const window={__gfcV172JobWait:false,GestorFC:{v172:{_finishJobWait(){window.__gfcV172JobWait=false}}}};
let view='career',calls=0,offerChecks=0,modalOpens=0,saveScheduled=0,renders=0;
const v53Sim={active:false,starting:false,syncing:false,patching:false},v18112Dismissal={pending:false};
let v86RankCache=null;
const v89JobWait={active:false,stop:false,startDay:0,days:0};
let v93CoachSaveTimer=0;
function v89HasNationalJob(){return !!state.v640National?.userTeam}
function v89PaintJobWait(){}
function v555UpdateChrome(){}
function render(){renders++}
const recordedErrors=[];
function toast(msg,level){if(level==='error')recordedErrors.push(String(msg))}
function v636CoachOfferModal(){modalOpens++}
function v93ScheduleCoachDecisionSave(){saveScheduled++}
function persist(){return Promise.resolve()}
function v636PendingCoachOffers(s){return s.v636CoachOffers.filter(o=>o?.status==='pending')}
function v636AfterRound(s,before){
 offerChecks++;
 assert.equal(before.employed,false);
 if(s.day===4)s.v636CoachOffers.push({status:'pending',teamId:'other',year:2027,day:4});
}
let v53StartSimulation=async(mode)=>{
 assert.equal(mode,'dayfast','Job search must use fast one-day Worker');
 calls++;state.day++;return true;
};
""" + offer_hook + wait + r"""
(async()=>{
 await v89RunJobWait();
 assert.deepEqual(recordedErrors,[],'Job search must not swallow Worker errors');
 assert.equal(calls,4,'Job search must stop at first proposal');
 assert.equal(offerChecks,4,'Job offer evaluation must run after every Turbo jornada');
 assert.equal(v89JobWait.days,4);
 assert.equal(state.day,4);
 assert.equal(state.v636CoachOffers.length,1);
 assert.equal(v89JobWait.active,false);
 assert.equal(window.__gfcV172JobWait,false);
 assert.ok(saveScheduled>=1);
 state.v636CoachOffers=[{status:'pending',teamId:'other'}];
 await v89RunJobWait();
 assert.equal(calls,4,'Already pending offer must not simulate more games');
 state.v636CoachOffers=[];
 state.userEmployed=true;
 await v89RunJobWait();
 assert.equal(calls,4,'Employed manager must not start unemployed job wait');
 console.log(JSON.stringify({ok:true,version:'18.327',turboStages:results,
   formerlyManagedClubTurbo:true,employedDetailedEngine:true,nationalDetailedEngine:true,
   workerMode:'dayfast',offerEvaluations:offerChecks,stepsToFirstOffer:4,
   noSkippedOffer:true,noDuplicateFastForward:true}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
    dest=root/'test-unemployed-turbo-18327.cjs'
    dest.write_text(js,encoding='utf-8')
    try:
        check=subprocess.run(['node','--check',str(dest)],capture_output=True,text=True,timeout=20)
        if check.returncode:raise RuntimeError('Turbo test JS syntax: '+check.stderr[-2000:])
        run=subprocess.run(['node',str(dest)],capture_output=True,text=True,timeout=30)
    finally:
        dest.unlink(missing_ok=True)
    if run.returncode:raise RuntimeError('Unemployed Turbo regression: '+(run.stderr or run.stdout)[-4500:])
    result=json.loads(run.stdout.strip().splitlines()[-1])
    if not result.get('ok'):raise RuntimeError('Turbo regression returned no success')
    (root/'unemployed-turbo-18327-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
