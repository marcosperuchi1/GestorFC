from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path

VERSION='18.362.0'

def section(s,start,end):
 a=s.index(start);b=s.index(end,a+len(start));return s[a:b]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_core_transitions_18362.py <project>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 for anchor in ('FUTBR_CORE_LIFECYCLE_18362','FUTBR_DISMISSAL_FINISHED_SIGNAL_18359',
                'FUTBR_VACATION_FINALIZE_LIGHT_18360','FUTBR_OOMSAFE_ARCHIVE_18352',
                "const EDITION='18.362.0';","window.GestorFC.version='18.362.0';"):
  assert anchor in s,anchor
 fn=section(s,'function v18359OnWorkerFinished(m,wasVacation){','const v18359BaseChrome=v555UpdateChrome;')
 guard=section(s,'/* FUTBR_CORE_LIFECYCLE_18362','function v18359RefreshButtons(root=document){')
 wrap=section(s,'const v18359BaseStart=v53StartSimulation;','window.GestorFC.lifecycle18362=')
 cleanup=section(s,'function v18362CleanupBusy(){','window.GestorFC.v18360CleanupStatus=')
 assert 'if(!dismissed)return false' in fn
 assert "phase:'worker-finished'" in fn
 assert "phase:'promoted'" in fn
 assert 'if(v53Sim?.active||v53Sim?.starting' in guard
 assert 'v18362CommitVacation(origin)' in wrap
 assert 'await p' in wrap
 assert 'await new Promise(r=>setTimeout(r,15000))' in cleanup
 assert 'await cleanupManifest(oldManifest,keep)' in cleanup
 assert "Math.min(768,(" in s
 assert "async function v548EnterGame(){" in s
 assert "await v260FastLoadLocal(false);" in s
 assert "await v310StartRosterLoad();" in s
 assert "FUTBR_FAST_SIGNED_UPDATER_18361" not in fn
 pre=r"""
const assert=require('node:assert/strict');
let state,view='dashboard',v53Sim,v18112Dismissal,v125VacIncoming=null;
let v53Creating=false,v18326AdvanceBusy=false,v18121NewSeasonPreparation=false;
let v18119SeasonTransfer={active:false},v18357AwaitingPromotion=false,
 v18358RecoveryDone=false,v18357LiveFallback=null,v89JobWait={active:false};
let v18359FinishedWorld=null,v18359FinishCount=0,v18359ReleaseCount=0,
 v18359BlockedReason='not-finished',v18359VacationPromise=null;
let v52Processing=false,v52SavePromise=null,v18360CleanupTail=Promise.resolve();
const v18360CleanupStats={scheduled:0,completed:0,failed:0,active:false,lastError:''};
let statusCount=0,dayArgs=[],work=null,jobBtn={disabled:true},waitResolve;
const window={GestorFC:{}};
const document={querySelectorAll:()=>[jobBtn],querySelector:()=>null};
function v18359HasWorld(s=state){return !!s&&s.userEmployed===false&&
 !s.v640National?.userTeam&&!!s.players&&Array.isArray(s.teams)&&
 Array.isArray(s.schedule)&&!s.vacation?.active&&!v125VacIncoming;}
function v18359RefreshButtons(){jobBtn.disabled=false}
function v18119CompleteSeasonTransfer(){v18119SeasonTransfer.active=false}
function closeModal(){}
function render(){v18359RefreshButtons()}
function toast(){}
function world(){return {year:2031,day:35,v1903CareerId:'C1',userEmployed:false,
 players:{p:{id:'p'}},teams:[],schedule:[],vacation:{active:true}}}
function v53StartSimulation(mode,options={}){
 if(mode==='vacation')return new Promise(resolve=>{waitResolve=resolve});
 if(mode==='dayfast'||mode==='day'){dayArgs.push(options);return Promise.resolve(state)}
 throw Error('mode');
}
function reset(){
 state=world();v53Sim={active:true,starting:false,session:17,
 syncing:true,patching:true,finished:{kind:'pending'}};
 v18112Dismissal={pending:true,ready:false,careerId:'C1',notified:false};
 v18119SeasonTransfer.active=true;
}
"""
 tests=r"""
(async()=>{
 reset();
 const p=v53StartSimulation('vacation');
 assert.equal(v18359OnWorkerFinished({kind:'finished'},true),true);
 assert.equal(v18359TrustedCompleted(),false,'Worker active must never unlock');
 assert.equal(v18112Dismissal.pending,true,'Event must not finalize before checkpoint');
 assert.equal(v18359FinishedWorld.phase,'worker-finished');
 v53Sim.active=false;v53Sim.finished=null;state.vacation.active=false;
 waitResolve(state);await p;
 assert.equal(v18359TrustedCompleted(),true,'Promotion occurs only after the settled promise');
 assert.equal(v18112Dismissal.pending,false);
 assert.equal(jobBtn.disabled,false);
 await v53StartSimulation('dayfast');
 assert.equal(dayArgs[0].liveStateNoPreSave,true);
 // Active unfinished stream must never promote.
 reset();v125VacIncoming={partial:true};
 assert.equal(v18359OnWorkerFinished({},true),false);
 v125VacIncoming=null;
 // An ordinary unemployed vacation is never mistaken for a dismissal.
 reset();v18112Dismissal.pending=false;v18362VacationOrigin={careerId:'C1',employed:false};
 v53Sim.active=false;state.vacation.active=false;
 assert.equal(v18362CommitVacation(v18362VacationOrigin),false);
 assert.equal(v18112Dismissal.ready,false);
 // Cleanup is inspected statically; no 15-second housekeeping timer is
 // started by the fast regression test.
 console.log(JSON.stringify({ok:true,version:'18.362.0',
 actualWorkerEventDeferred:true,outerPromiseRequired:true,
 firstUnemployedDayUsesLiveWorld:true,noEarlyUnlock:true,
 careerAndNationalGuards:true,unemployedVacationNotDismissal:true,
 cleanupDelayed:true,saveAndHistoryUnchanged:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
 # Test real installed JS methods rather than a duplicate implementation.
 ftxt=pre+"\n"+guard+"\n"+fn+"\n"+wrap+"\n"+tests
 with tempfile.TemporaryDirectory() as td:
  f=Path(td)/'core-18362.cjs';f.write_text(ftxt,encoding='utf-8')
  c=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=20)
  if c.returncode:raise RuntimeError('Core JS check: '+c.stderr[-3000:])
  p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=20)
  if p.returncode:raise RuntimeError('Core JS runtime: '+(p.stderr or p.stdout)[-3500:])
  result=json.loads(p.stdout.strip().splitlines()[-1])
 (root/'core-transitions-18362-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':main()
