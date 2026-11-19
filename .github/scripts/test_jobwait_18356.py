from __future__ import annotations

import json,subprocess,sys,tempfile
from pathlib import Path

VERSION='18.356.0'

def extract(src,first,last):
    i=src.index(first);j=src.index(last,i+len(first))
    return src[i:j]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_jobwait_18356.py <project>')
    root=Path(sys.argv[1]).resolve()
    s=(root/'src/index.html').read_text(encoding='utf-8')
    assert s.count('/* FUTBR_JOBWAIT_SEASON_RECOVERY_18356')==1
    assert "window.GestorFC.version='18.356.0';window.GestorFC.visualVersion='18.356.0';" in s
    assert 'const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=!!options?.liveStateNoPreSave&&' in s
    assert "useResident:!v18311LiveVacation&&(mode==='day'||mode==='dayfast'" in s
    assert "const canLoadSaved=!v18311LiveVacation&&!!saveOK" in s
    assert "if(!canLoadSaved)msg.state=state;" in s
    assert "mode==='dayfast')&&state.userEmployed===false&&" in s
    assert "if(mode==='day'||mode==='dayfast')v636AfterRound(state,before)" in s
    assert "async function v89RunJobWait(){\n v18356ReconcileRollover();" in s
    assert "function v18334ShouldWait(){\n v18356ReconcileRollover();" in s
    assert "await v53StartSimulation('dayfast');" in extract(s,'async function v89RunJobWait(){','const v89BaseCareerPage=careerPage;')
    assert 'FUTBR_LONG_CAREER_SAVE_18338_BEGIN' in s
    assert 'FUTBR_JOB_SAVE_EXIT_18355' in s

    helper=extract(s,'/* FUTBR_JOBWAIT_SEASON_RECOVERY_18356','const v18112BaseChrome=v555UpdateChrome;')
    # A narrow test mounts only the new helper and mocked game lifecycle. It
    # asserts the exact 2027 screenshot state, an unfinished worker, an active
    # national manager, same-season dismissal, and click-time recovery.
    js=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}};
const v53RPC=new Map();
let state={year:2026,day:163,userEmployed:false,seasonDone:true,live:null,
 v1903CareerId:'santos-save',v640National:null,vacation:{active:false,paused:true}};
const v18112Dismissal={pending:true,ready:false,year:2026,day:163,careerId:'santos-save'};
const v89JobWait={active:false,stop:false};
const v53Sim={active:true,starting:false,syncing:true,patching:true,finished:null};
let v53Creating=false,v52Processing=false,v18326AdvanceBusy=false;
let v18121NewSeasonPreparation=false;
let v18119SeasonTransfer={active:false},v168RolloverRunning=false,v91RolloverActive=false;
let v168DeferredRolloverSave=false;
const controls={advance:{disabled:true,attrs:{}},jobs:{disabled:true,attrs:{}}};
for(const el of Object.values(controls)){
 el.removeAttribute=function(k){delete this.attrs[k];};
 el.setAttribute=function(k,v){this.attrs[k]=v;};
}
controls.advance.dataset={action:'advance'};controls.jobs.dataset={action:'v89-job-wait'};
const root={querySelectorAll(q){return q.includes('v89-job-wait')?
 [controls.jobs,controls.advance]:[];}};
const document={querySelector(q){return q==='#app'?root:null;}};
function v555UpdateChrome(){
 for(const el of Object.values(controls))
  el.disabled=!!(v53Creating||v53Sim.active||v18112Dismissal.pending||v53Sim.syncing);
}
async function v53Prepare(op){
 if(op!=='next')throw Error('wrong mocked operation');
 v53Creating=true;
 try{
  state.year=2027;state.day=0;state.seasonDone=false;
  v168DeferredRolloverSave=true;
  v555UpdateChrome(root);
 }finally{v53Creating=false;}
 return true;
}
""" + helper + r"""
(async()=>{
 await v53Prepare('next',{state});
 await Promise.resolve();
 assert.equal(state.year,2027);assert.equal(state.day,0);
 assert.equal(v168DeferredRolloverSave,true,'New year checkpoint deferred as designed');
 assert.equal(controls.jobs.disabled,false,'Job-wait must be clickable in 2027 day 1');
 assert.equal(controls.advance.disabled,false,'Manual day must be clickable in 2027 day 1');
 assert.equal(v18112Dismissal.pending,false,'Old-year dismissal guard must be released');
 assert.equal(v53Sim.syncing,false);assert.equal(v53Sim.patching,false);
 assert.equal(v53Sim.active,false,'Stale last-year busy flag must clear only when no live Worker');
 assert.equal(v18356CanUseJobButtons(),true);
 // An active Worker has an unresolved promise, and must NEVER be interrupted.
 v168DeferredRolloverSave=true;v18112Dismissal.pending=true;
 v18112Dismissal.year=2026;v53Sim.active=true;v53Sim.finished={resolve(){}};
 v53Sim.syncing=true;
 assert.equal(v18356ReconcileRollover(),false);
 assert.equal(v18112Dismissal.pending,true);assert.equal(v53Sim.active,true);
 v53Sim.finished=null;v53Sim.active=false;
 // The same season, even if dismissed midyear, still needs the exact storage audit.
 v18112Dismissal.year=2027;state.day=20;
 assert.equal(v18356ReconcileRollover(),false);
 assert.equal(v18112Dismissal.pending,true);
 // Another career's handoff must not be inherited.
 v18112Dismissal.year=2026;v18112Dismissal.careerId='other-save';
 assert.equal(v18356ReconcileRollover(),false);
 v18112Dismissal.careerId='santos-save';
 v53Sim.syncing=false;
 assert.equal(v18356ReconcileRollover(),true);
 // Once no rollover is pending, manual and automatic buttons work in mid-season.
 v168DeferredRolloverSave=false;v555UpdateChrome(root);
 assert.equal(controls.jobs.disabled,false);
 // No recovery during an active national-team job.
 state.v640National={userTeam:'BRA'};v168DeferredRolloverSave=true;
 v18112Dismissal.pending=true;v18112Dismissal.year=2026;
 assert.equal(v18356ReconcileRollover(),false);
 state.v640National=null;state.userEmployed=true;
 assert.equal(v18356ReconcileRollover(),false);
 // Stop button remains owned by the running job-wait loop.
 state.userEmployed=false;v89JobWait.active=true;
 assert.equal(v18356ReconcileRollover(),false);
 // Never unlock a real season transition.
 v89JobWait.active=false;v53Creating=true;
 assert.equal(v18356ReconcileRollover(),false);
 console.log(JSON.stringify({ok:true,version:'18.356.0',
  screenshot2027DayOneRecovered:true,bothButtonsReenabled:true,
  genuineWorkerProtected:true,sameSeasonCheckpointAuditPreserved:true,
  careerIdProtected:true,nationalJobProtected:true,alreadyWorkingSeasonPreserved:true,
  firstDayUsesLiveState:true,priorCheckpointPreserved:true}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
    with tempfile.TemporaryDirectory() as td:
        f=Path(td)/'jobwait-18356.cjs'
        f.write_text(js,encoding='utf-8')
        check=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=20)
        if check.returncode:raise RuntimeError('JS syntax: '+check.stderr[-4000:])
        p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=30)
        if p.returncode:raise RuntimeError('18.356 behavior regression: '+(p.stderr or p.stdout)[-4500:])
        report=json.loads(p.stdout.strip().splitlines()[-1])
    (root/'jobwait-season-18356-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
