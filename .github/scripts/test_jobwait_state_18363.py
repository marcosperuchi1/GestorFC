from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path

def part(text,start,end):
 a=text.index(start);b=text.index(end,a+len(start))
 return text[a+len(start):b]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_jobwait_state_18363.py <project>')
 root=Path(sys.argv[1])
 s=(root/'src/index.html').read_text(encoding='utf-8')
 script='<script id="futbr-jobwait-state-18363">'
 assert s.count(script)==1
 assert s.count('/* FUTBR_JOBWAIT_STATE_CORE_18363')==1
 assert "const EDITION='18.363.0';" in s
 assert "window.GestorFC.version='18.363.0';window.GestorFC.visualVersion='18.363.0';" in s
 helper=part(s,script,'</script>')
 job=part(s,'async function v89RunJobWait(){','const v89BaseCareerPage=careerPage;')
 start=s.index('function v18334ShouldWait(){')
 assert 'if(v18363CanUseJobWait())return false;' in s[start:start+220]
 assert 'if(!v18363CanUseJobWait()){' in job
 assert 'await v53StartSimulation(\'dayfast\');' in job
 assert 'if(v18112Dismissal.pending||v53Sim?.active||v53Sim?.starting||v53Sim?.patching||v53Sim?.syncing)' not in job
 assert 'Object.keys(state.players)' not in helper
 assert 'persist(' not in helper
 assert 'v52FlushSave(' not in helper
 assert 'v18363NoActualWork' in helper
 assert 'v18363RecoveredStale++' in helper
 assert 'v18359TrustedCompleted()' not in helper
 assert 'v18363PaintJobButtons(root||document);' in helper

 pre=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{v172:{_finishJobWait(){}}}},nativeSetTimeout=require('node:timers').setTimeout;
function setTimeout(fn,delay){return delay===900?-1:nativeSetTimeout(fn,delay);}
let state,view='career',v53Sim,v18112Dismissal,v125VacIncoming=null,
 v53Creating=false,v52Processing=false,v52SavePromise=null,v53RPC=new Map(),v53Worker={},
 v18119SeasonTransfer={active:false},v18121NewSeasonPreparation=false,
 v18326AdvanceBusy=false,v168RolloverRunning=false,v91RolloverActive=false,
 v18359VacationPromise=null,v18362VacationOrigin=null,
 v18357LiveFallback=null,v18359FinishedWorld=null,
 v89JobWait={active:false,stop:false,days:0},v86RankCache={dirty:false};
let simDays=0,modalCount=0,notices=[],optionsHistory=[];
const btn1={disabled:true,attrs:{},title:'',removeAttribute(k){delete this.attrs[k];if(k==='disabled')this.disabled=false;},setAttribute(k,v){this.attrs[k]=v;if(k==='disabled')this.disabled=true;}};
const btn2={...btn1,attrs:{},removeAttribute:btn1.removeAttribute,setAttribute:btn1.setAttribute};
const document={
 querySelectorAll(q){return q.includes('v89-job-wait')?[btn1,btn2]:[]},
 querySelector(q){return null}
};
function makeWorld(){return {year:2027,day:41,v1903CareerId:'career-Chapecoense-2027',
 userEmployed:false,seasonDone:false,live:null,v640National:null,
 players:{p1:{id:'p1'}},teams:[{id:'chapecoense'}],schedule:Array(164).fill({}),
 vacation:{active:false,paused:true},offers:[]};}
function reset(){
 state=makeWorld();v53Sim={active:false,starting:false,finished:null,
 syncing:true,patching:true,session:8};
 v18112Dismissal={pending:true,ready:false,careerId:state.v1903CareerId,
 year:2027,day:41,notified:false};
 v53RPC=new Map();v53Worker={};v125VacIncoming=null;v53Creating=false;v52Processing=true;
 v52SavePromise=null;v18119SeasonTransfer.active=false;
 v18121NewSeasonPreparation=false;v18326AdvanceBusy=false;
 v168RolloverRunning=false;v91RolloverActive=false;
 v18359VacationPromise=null;v18362VacationOrigin=null;
 v18357LiveFallback=null;v18359FinishedWorld=null;
 v89JobWait={active:false,stop:false,days:0};btn1.disabled=true;btn2.disabled=true;
}
function v555UpdateChrome(){
 for(const b of [btn1,btn2]){
  b.disabled=!!(v18112Dismissal.pending||v53Sim.syncing||v53Sim.active||v53Sim.starting);
  if(b.disabled)b.setAttribute('aria-busy','true');
 }
}
function render(){v555UpdateChrome(document)}
function v18356ReconcileRollover(){return false}
function toast(s){notices.push(s)}
function v89PaintJobWait(){v555UpdateChrome(document)}
function v89HasNationalJob(){return !!state?.v640National?.userTeam}
function v636PendingCoachOffers(s){return s?.offers||[]}
function v636CoachOfferModal(){modalCount++}
function v93ScheduleCoachDecisionSave(){}
function persist(){}
async function v53Prepare(op){assert.equal(op,'next');state.year++;state.day=0;state.seasonDone=false}
async function v53StartSimulation(mode,opt={}){
 assert.equal(mode,'dayfast');
 optionsHistory.push(opt);simDays++;state.day++;state.offers.push({teamId:'chapecoense'});
 return state;
}
"""
 test=r"""
(async()=>{
 reset();
 assert.equal(v18359FinishedWorld,null,'No 18.362 volatile completion token after load');
 v555UpdateChrome(document);
 assert.equal(btn1.disabled,false,'Screenshot 2027/42 header must unlock');
 assert.equal(btn2.disabled,false,'Career page must unlock');
 assert.equal(v18112Dismissal.pending,false,'Stale dismissal flag must clear at source');
 assert.equal(v53Sim.syncing,false,'Stale syncing flag must not block');
 assert.equal(v53Sim.patching,false);
 assert.equal(v52Processing,false,'Stale save indicator must not freeze job-wait');
 assert.deepEqual(v18357LiveFallback,{year:2027,day:41,careerId:'career-Chapecoense-2027'});
 assert.equal(window.GestorFC.jobWait18363.status().usable,true);
 // An unrelated expired RPC from a terminated vacation worker is not active work.
 reset();v53Worker=null;v53RPC.set('old-worker',{});
 v555UpdateChrome(document);
 assert.equal(btn1.disabled,false,'Orphan RPC after Worker disposal must not block');
 reset();v555UpdateChrome(document);
 await v89RunJobWait();
 assert.equal(simDays,1,'Real dayfast Worker path must execute');
 assert.equal(state.day,42);
 await new Promise(r=>nativeSetTimeout(r,60));
 assert.equal(modalCount,1,'Real job offer dialog must open');
 state.offers=[];v555UpdateChrome(document);
 assert.equal(btn1.disabled,false,'Button must remain enabled AFTER day changed');
 assert.equal(btn2.disabled,false);
 // Reload from a committed save with an old temporary signal lost.
 reset();state.day=42;v18112Dismissal.pending=false;
 v53Sim.syncing=false;v53Sim.patching=false;v18357LiveFallback=null;
 v555UpdateChrome(document);
 assert.equal(btn1.disabled,false,'Loaded unemployed career must not require dismissal event');
 // Genuine operations must still disable and the click must not start dayfast.
 for(const kind of ['active','starting','finished','ipc','transfer','save','vacationPromise']){
  reset();v18112Dismissal.pending=false;v53Sim.syncing=false;v53Sim.patching=false;
  if(kind==='active')v53Sim.active=true;
  if(kind==='starting')v53Sim.starting=true;
  if(kind==='finished')v53Sim.finished={resolve(){}};
  if(kind==='ipc')v53RPC.set('load',{});
  if(kind==='transfer')v18119SeasonTransfer.active=true;
  if(kind==='save')v52SavePromise=Promise.resolve();
  if(kind==='vacationPromise')v18359VacationPromise=Promise.resolve();
  const days=simDays;v555UpdateChrome(document);
  assert.equal(btn1.disabled,true,'Must block '+kind);
  await v89RunJobWait();
  assert.equal(simDays,days,'Click must not run during '+kind);
 }
 // The active button means STOP even while a dayfast Worker is running.
 reset();v89JobWait.active=true;v53Sim.active=true;v18112Dismissal.pending=false;
 v555UpdateChrome(document);assert.equal(btn1.disabled,false,'Stop must remain clickable');
 const before=simDays;await v89RunJobWait();
 assert.equal(v89JobWait.stop,true);assert.equal(simDays,before);
 // A manager still employed or managing a national team is never eligible.
 reset();state.userEmployed=true;
 assert.equal(v18363CanUseJobWait(),false);
 state.userEmployed=false;state.v640National={userTeam:'BRA'};
 assert.equal(v18363CanUseJobWait(),false);
 console.log(JSON.stringify({ok:true,version:'18.363.0',
  screenshot2027Day42Recovered:true,headerAndCareerButtonsRecovered:true,
  staleDismissalAndSyncCleared:true,staleSaveFlagCleared:true,orphanRPCIgnored:true,loadedUnemployedCareerRecovered:true,
  worksAfterSubsequentJourneys:true,realDayfastUsed:true,
  nextOfferAppeared:true,blocksActualWorkerAndSave:true,
  stopButtonAccessible:true,nationalAndEmployedProtected:true,
  previousCheckpointProtected:true,noWholeWorldSave:true}));
})().catch(e=>{console.error(e.stack||e);process.exitCode=1});
"""
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'runtime-18363.cjs'
  f.write_text(pre+'\n'+helper+'\n'+job+'\n'+test,encoding='utf-8')
  c=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=30)
  if c.returncode:raise RuntimeError('18.363 source syntax error: '+c.stderr[-4000:])
  p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=40)
  if p.returncode:raise RuntimeError('18.363 real job-wait regression: '+(p.stderr or p.stdout)[-6500:])
  report=json.loads(p.stdout.strip().splitlines()[-1])
 (root/'jobwait-state-18363-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
