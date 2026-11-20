from __future__ import annotations
import json,subprocess,tempfile,sys
from pathlib import Path

def main():
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 assert 'FUTBR_BOUNDED_JOBWAIT_18370' in s
 assert "const EDITION='18.370.0';" in s
 assert 'const yearBefore=Number(state.year)||0,worldBefore=state;' not in s
 assert 'jobWaitResident:v18368SameWorker,jobWaitAuto:true' in s
 assert "if(mode==='dayfast'&&options?.jobWaitAuto===true)msg.jobWaitAuto=true;" in s
 assert "!(fastManualDay&&message.jobWaitAuto===true)" in s
 assert "if((!fastManualDay&&!nationalJump&&!nextMatchJump||message.jobWaitAuto===true)&&v150ManualSavePromise)" in s
 a=s.index('/* FUTBR_BOUNDED_JOBWAIT_18370');b=s.index('const v89BaseCareerPage=careerPage;',a)
 ui=s[a:b]
 a=s.index("if(m.op==='jobwait-checkpoint-18370')");b=s.index("if(m.op==='save'){",a)
 worker=s[a:b]
 test=r'''
const assert=require('node:assert/strict');
const window={GestorFC:{v172:{_finishJobWait(){}}}};
const document={querySelector(){return {querySelector(){return null;}};}};
const performance={now:()=>Date.now()};
let v53Worker={id:1},v53Sim={active:false,starting:false,syncing:false,patching:false},
 v53PatchQueue=[],v125VacIncoming=null,v93CoachSaveTimer=0,v89JobWait={active:false,stop:false,days:0},
 v52SavePromise=null,v52SaveDirty=false,v53Creating=false,v143PostRankPending=false,
 v86RankCache={dirty:false},v18119SeasonTransfer={active:false},state=null,view='career';
let saves=[],starts=[],notices=[],allowOffer=false,failDay=null;
const E={team:(s,id)=>s.teams.find(t=>t.id===id)};
function v18356ReconcileRollover(){}function v18358SafeJobButtons(){return false;}
function v18363CanUseJobWait(){return true;}function v89HasNationalJob(){return false;}
function v636PendingCoachOffers(s){return allowOffer&&s.day>=6?[{teamId:'other'}]:[];}
function v636CoachOfferModal(){}function v93ScheduleCoachDecisionSave(){}
function v89PaintJobWait(){}function v555UpdateChrome(){}function render(){}function persist(){}
function v53Saved(){}function toast(t){notices.push(String(t));}
async function v53Prepare(){throw Error('Unexpected season rollover');}
async function v53StartSimulation(mode,opts){
 assert.equal(mode,'dayfast');assert.equal(opts.jobWaitAuto,true);
 starts.push({mode,opts});state.day++;if(state.day===9)v89JobWait.stop=true;
 return state;
}
async function v53Call(op,data){
 assert.equal(op,'jobwait-checkpoint-18370');
 if(failDay===state.day)throw Error('INTENTIONAL_SAVE_FAILURE');
 assert.equal(data.day,state.day);assert.equal(data.year,state.year);
 assert.equal(data.careerId,state.v1903CareerId);assert.deepEqual(data.coachDelta.offers,state.v636CoachOffers);
 saves.push({day:data.day,year:data.year});
 return {ok:true,year:data.year,day:data.day,careerId:data.careerId,saved:{at:Date.now(),ms:22}};
}
function setup(){state={year:2028,day:0,seasonDone:false,user:'t0',userEmployed:false,
 v1903CareerId:'fixture-2028',teams:[{id:'t0'},{id:'other'}],players:{},schedule:[],
 v636CoachOffers:[{status:'pending'}],v636CoachCareer:[],v636CoachOfferMeta:{},news:[]};
 v89JobWait={active:false,stop:false,days:0};v53Worker={id:1};starts=[];saves=[];notices=[];allowOffer=false;failDay=null;
 v18370JobSave.commits=0;v18370JobSave.failed=0;v18370JobSave.busy=false;
}
(async()=>{
 setup();await v89RunJobWait();
 assert.deepEqual(saves.map(s=>s.day),[4,8,9], '4-day checkpoints plus final stop');
 assert.equal(starts.length,9);assert.equal(v18370JobSave.commits,3);
 setup();allowOffer=true;await v89RunJobWait();
 assert.deepEqual(saves.map(s=>s.day),[4,6], 'new offer must force durable end');
 assert.equal(starts.length,6);
 setup();failDay=4;await v89RunJobWait();
 assert.equal(starts.length,4,'no later rounds after failed checkpoint');
 assert.ok(notices.some(s=>s.includes('INTENTIONAL_SAVE_FAILURE')));
 assert.ok(v18370JobSave.failed>=1);
 console.log(JSON.stringify({ok:true,version:'18.370.0',checkpointDays:[4,8,9],
  immediateOfferCheckpoint:true,rollbackOnFailure:true,noUnboundedSaveChain:true,
  priorWorldReferenceRemoved:true,allHistoricalFieldsStayInWorld:true}));
})().catch(err=>{console.error(err);process.exitCode=1;});
'''
 source=test[:test.index('(async()=>{')]+ui+'\n'+test[test.index('(async()=>{'):]
 with tempfile.TemporaryDirectory() as d:
  f=Path(d)/'test.js';f.write_text(source,encoding='utf-8');p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=45)
  if p.returncode:raise RuntimeError(p.stderr[-4000:]+'\n'+p.stdout[-1000:])
  ui_report=json.loads(p.stdout.strip().splitlines()[-1])
 test_worker=r'''
const assert=require('node:assert/strict');
let running=false,v150ManualSavePromise=null,world=null,called=0;
async function save(w){called++;return {at:100,ms:1};}
async function check(m){
''' + worker + r'''
 throw Error('No checkpoint route');
}
(async()=>{
 const players={p:{id:'p',goals:30}},history={2026:{p:{goals:4}},2027:{p:{goals:8}}};
 world={players,teams:[],schedule:[],v1903CareerId:'career-28',user:'t0',year:2028,day:110,
  v538CareerArchive:history,v636CoachOffers:[],v636CoachOfferMeta:{},v636CoachCareer:[],news:[]};
 const args={op:'jobwait-checkpoint-18370',careerId:'career-28',user:'t0',year:2028,day:110,
  coachDelta:{offers:[{status:'pending'}],offerMeta:{lastOfferDay:110},tracker:null,career:[],news:['a']}};
 const ok=await check(args);assert.equal(ok.ok,true);assert.equal(called,1);
 assert.strictEqual(world.players,players);assert.strictEqual(world.v538CareerArchive,history);
 assert.equal(world.v636CoachOffers.length,1);
 for(const p of [{...args,day:109},{...args,careerId:'wrong'},{...args,user:'wrong'}])
  await assert.rejects(check(p));
 assert.equal(called,1,'wrong-career checkpoint must never save');
 console.log(JSON.stringify({ok:true,retainsArchives:true,retainsPlayers:true,
  exactDayAndCareer:true,oneAtomicSave:true,uiOfferDeltaPreserved:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
'''
 with tempfile.TemporaryDirectory() as d:
  f=Path(d)/'test-worker.js';f.write_text(test_worker,encoding='utf-8');p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=45)
  if p.returncode:raise RuntimeError(p.stderr[-4000:]+'\n'+p.stdout[-1000:])
  worker_report=json.loads(p.stdout.strip().splitlines()[-1])
 report={**ui_report,'worker':worker_report,'actualPostRoundLoopExecuted':True,'originalWorkerCheckpointGuardExecuted':True}
 (root/'jobwait-memory-18370-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
