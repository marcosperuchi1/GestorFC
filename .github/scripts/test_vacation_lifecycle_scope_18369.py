from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path

PREFIX=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}},document={querySelectorAll:()=>[],querySelector:()=>null};
const callbacks=[],paints=[];
function makeGame(){
 let state={v1903CareerId:'scope-private-career',year:2026,day:5,user:'t0',
  userEmployed:true,players:{p:{}},teams:[{id:'t0'}],schedule:[{}],
  vacation:{active:false,paused:true}};
 let v53Sim={session:3,active:false,starting:false,syncing:false,patching:false,
  finished:null,pause:false,pauseMode:''};
 let v125VacIncoming=null,v53Creating=false,v52Processing=false,v52SavePromise=null;
 let v89JobWait={active:false},v18326AdvanceBusy=false,v18121NewSeasonPreparation=false;
 let v18112Dismissal={pending:false,careerId:'',ready:false,notified:false};
 let v18119SeasonTransfer={active:false},v18357AwaitingPromotion=false,
  v18358RecoveryDone=false,v18357LiveFallback=null,view='vacation';
 const render=()=>paints.push('render'),closeModal=()=>paints.push('close'),toast=()=>paints.push('toast');
 const v18119CompleteSeasonTransfer=()=>{v18119SeasonTransfer.active=false;};
 let v555UpdateChrome=()=>paints.push('base-chrome');
 let v53StartSimulation=async function(mode){
  assert.equal(mode,'vacation');v53Sim.active=true;
  state.vacation.active=true;v53Sim.session++;
  return new Promise((resolve,reject)=>{v53Sim.finished={resolve,reject};});
 };
 function v18364OnVacationSettled(origin,success){
  callbacks.push({name:'18364',success,career:origin.careerId,
   noPending:!v18359VacationPromise&&!v18362VacationOrigin});
 }
 function v18365OnVacationSettled(origin,success){
  callbacks.push({name:'18365',success,career:origin.careerId,
   noPending:!v18359VacationPromise&&!v18362VacationOrigin});
 }
"""

SUFFIX=r"""
 return {
  begin:()=>v53StartSimulation('vacation'),
  finish(dismissed=false){
   state.day++;state.vacation.active=false;state.vacation.remaining=0;
   if(dismissed){state.userEmployed=false;v18112Dismissal.pending=true;
    v18112Dismissal.careerId=state.v1903CareerId;}
   v53Sim.active=false;v53Sim.starting=false;
   const pending=v53Sim.finished;v53Sim.finished=null;
   // Exact active-queue lifecycle callback, with state private in this IIFE.
   const recorded=v18359OnWorkerFinished({session:v53Sim.session},true);
   pending.resolve(state);
   return recorded;
  },
  phase:()=>({day:state.day,employed:state.userEmployed,view,
   outerPending:!!v18359VacationPromise,originPending:!!v18362VacationOrigin,
   promoted:v18359TrustedCompleted(),dismissalPending:v18112Dismissal.pending,
   recovered:v18358RecoveryDone}),
  chrome:()=>v555UpdateChrome(document),
 };
}
const game=makeGame();
assert.equal(typeof globalThis.state,'undefined');
assert.equal(window.state,undefined);
"""

TEST=r"""
(async()=>{
 assert.equal(storageBusy(),false);
 const employed=game.begin();
 assert.equal(storageBusy(),true,'storage sees the real private in-flight flags');
 assert.equal(game.phase().outerPending,true);
 assert.equal(game.phase().originPending,true);
 assert.equal(game.finish(false),false,'employed callback must return safely without a dismissal');
 await employed;await Promise.resolve();
 assert.equal(game.phase().employed,true);assert.equal(game.phase().day,6);
 assert.equal(game.phase().outerPending,false);assert.equal(game.phase().originPending,false);
 assert.equal(storageBusy(),false);
 assert.equal(window.GestorFC.lifecycle18362.status().settled,1);
 assert.equal(callbacks.length,2);assert.ok(callbacks.every(x=>x.success&&x.noPending));
 game.chrome();

 const fired=game.begin();
 assert.equal(game.finish(true),true,'the same private world is recorded on dismissal');
 await fired;await Promise.resolve();
 assert.equal(game.phase().employed,false);assert.equal(game.phase().day,7);
 assert.equal(game.phase().promoted,true);assert.equal(game.phase().recovered,true);
 assert.equal(game.phase().dismissalPending,false);assert.equal(game.phase().view,'career');
 assert.equal(callbacks.length,4);assert.ok(callbacks.every(x=>x.success&&x.noPending));
 assert.equal(window.GestorFC.lifecycle18362.status().settled,2);
 assert.equal(window.GestorFC.lifecycle18362.status().released,1);
 assert.equal(window.GestorFC.dismissalFinished18359.status().finishes,1);
 const before=window.GestorFC.lifecycle18362.status().cleanupDeferred;
 storageDefer();
 assert.equal(window.GestorFC.lifecycle18362.status().cleanupDeferred,before+1);
 assert.equal(typeof globalThis.state,'undefined');assert.equal(window.state,undefined);
 assert.equal(Object.values(window.GestorFC).some(x=>x?.players||x?.world),false);
 console.log(JSON.stringify({ok:true,version:'18.369.0',
  originalLifecycleFunctionsExecuted:true,lifecycleInsideOriginalPrivateUI:true,
  employedFinishedCallbackHasPrivateState:true,dismissalUsesSamePrivateWorld:true,
  outerVacationPromiseSettlesBeforeHandoff:true,controllerWrapperOrderPreserved:true,
  storageCleanupUsesExplicitScalarBridge:true,careerStateNotExported:true,
  dismissalFinishedIdentityIsWeak:true,
  scopeFixtureNotGameEngine:true}));
})().catch(error=>{console.error(error);process.exitCode=1;});
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_vacation_lifecycle_scope_18369.py <project>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 left='/* FUTBR_LIFECYCLE_SCOPE_18369_BEGIN */'
 right='/* FUTBR_LIFECYCLE_SCOPE_18369_END */'
 assert s.count(left)==s.count(right)==1
 assert '<script id="futbr-dismissal-finished-18359">' not in s
 ui=s.index('let state=null,saved=null');ui_end=s.index('</script>',ui)
 a=s.index(left);b=s.index(right,a)
 assert ui<a<b<ui_end
 lifecycle=s[a+len(left):b]
 assert '<script' not in lifecycle and '</script>' not in lifecycle
 assert 'const v18369FinishedWorlds=new WeakMap();' in lifecycle
 assert 'v18359FinishedWorld={world:' not in lifecycle
 assert lifecycle.count('v18369FinishedWorlds.get(s)!==x')==2
 assert lifecycle.count('v18369FinishedWorlds.set(')==2
 assert s.count('function v18359OnWorkerFinished(m,wasVacation){')==1
 assert s.index('const v18359BaseChrome=')<s.index('const v18363BaseChrome=')<s.index('const v18364BaseChrome=')<s.index('const v18365BaseChrome=')<ui_end
 assert s.index('const v18359BaseStart=')<s.index('const v18363BaseChrome=')
 c=s.index('/* FUTBR_VACATION_FINALIZE_LIGHT_18360')
 d=s.index('async function promoteVacationCheckpoint(){',c)
 cleanup=s[c:d]
 assert 'v18362Transitions' not in cleanup
 assert 'v53Sim' not in cleanup
 ca=cleanup.index('function v18362CleanupBusy(){')
 cb=cleanup.index('function v18360ScheduleObsoleteCleanup(',ca)
 busy=cleanup[ca:cb]
 defer='window.GestorFC?.lifecycle18362?.noteCleanupDeferred?.();'
 assert cleanup.count(defer)==2
 code=(PREFIX+lifecycle+SUFFIX+'\nconst storageBusy=(()=>{'+busy+';return v18362CleanupBusy;})();\n'+
       'const storageDefer=()=>{'+defer+'};\n'+TEST)
 with tempfile.TemporaryDirectory() as td:
  file=Path(td)/'actual-lifecycle-private-scope.js';file.write_text(code,encoding='utf-8')
  result=subprocess.run(['node',str(file)],capture_output=True,text=True,timeout=20)
  if result.returncode:
   raise RuntimeError('18.369 lifecycle scope regression failed:\n'+result.stderr[-10000:]+'\n'+result.stdout[-3000:])
  report=json.loads(result.stdout.strip().splitlines()[-1])
 (root/'vacation-lifecycle-scope-18369-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
