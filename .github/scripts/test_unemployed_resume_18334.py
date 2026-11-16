from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: test_unemployed_resume_18334.py <project-dir>")
    root = Path(sys.argv[1]).resolve()
    src = (root / "src" / "index.html").read_text(encoding="utf-8")
    a = "/* FUTBR_UNEMPLOYED_RESUME_18334_BEGIN"
    b = "/* FUTBR_UNEMPLOYED_RESUME_18334_END */"
    if src.count(a) != 1 or src.count(b) != 1:
        raise RuntimeError("18.334 patch missing or duplicated")
    start = src.index(a)
    end = src.index(b, start) + len(b)
    helper = src[start:end]
    wrapper_match = re.search(
        r"const v18112BaseChrome=v555UpdateChrome;[\s\S]*?\n};",
        src[end:],
    )
    if not wrapper_match:
        raise RuntimeError("18.112 dismissal chrome wrapper not found")
    wrapper = wrapper_match.group(0)
    if "v18334ShouldWait()" not in wrapper or "v18334ScheduleRecovery()" not in wrapper:
        raise RuntimeError("18.112 chrome did not receive 18.334 recovery guard")
    if "const waiting=v18112Dismissal.pending||" in wrapper:
        raise RuntimeError("Legacy permanently-disabled job button guard survives")
    if "FUTBR_UNEMPLOYED_TURBO_18327" not in src:
        raise RuntimeError("18.327 Turbo offer loop missing")
    job_start = src.find("async function v89RunJobWait(){")
    job_end = src.find("const v89BaseCareerPage=careerPage;", job_start)
    if job_start < 0 or job_end <= job_start or "await v53StartSimulation('dayfast');" not in src[job_start:job_end]:
        raise RuntimeError("18.327 fast unemployed offer loop missing")
    if "mode==='dayfast')v636AfterRound(state,before)" not in src:
        raise RuntimeError("18.327 dayfast coach-offer hook missing")
    boot = r"""
const assert=require('node:assert/strict');
let state={year:2031,day:18,v1903CareerId:'career-2031',
 userEmployed:false,v640National:null,seasonDone:false,live:null,
 vacation:{active:false,paused:true,remaining:0,untilSeason:false}};
const v53Sim={active:false,starting:false,syncing:true,patching:false,mode:'vacation'};
const v18112Dismissal={pending:true,ready:false,year:2031,day:18,careerId:'career-2031'};
const v89JobWait={active:false,stop:false};
let v53Creating=false,v18326AdvanceBusy=false;
let persistCalls=0,flushCalls=0,auditCalls=0;
let audit={year:2031,day:18,careerId:'career-2031'};
let chromeCalls=0;
const button={disabled:false,title:'',attrs:{},
 setAttribute(k,v){this.attrs[k]=v;},removeAttribute(k){delete this.attrs[k];}};
const root={querySelectorAll(sel){return sel==='[data-action="v89-job-wait"]'?[button]:[];}};
const document={querySelector(sel){return sel==='#app'?root:null;}};
const window={GestorFC:{v171:{storageAudit:async()=>{auditCalls++;return audit;}}}};
function v555UpdateChrome(){chromeCalls++;return true;}
async function persist(){persistCalls++;}
async function v52FlushSave(){flushCalls++;}
"""
    tests = r"""
(async()=>{
 // Reproduce the screenshot: 2031, dismissed during vacation, no worker alive,
 // stale "pending/syncing" from previous vacation means button was disabled.
 v555UpdateChrome(root);
 assert.equal(button.disabled,true,'Stale post-vacation state initially locks button');
 await new Promise(r=>setTimeout(r,15));
 assert.equal(v18112Dismissal.pending,false,'Dismissal flag must be cleared after save');
 assert.equal(v18112Dismissal.ready,true);
 assert.equal(v53Sim.syncing,false,'Stale sync flag must be released after audit');
 assert.equal(button.disabled,false,'2031 proposal button must be enabled');
 assert.equal(persistCalls,0,'Already-saved checkpoint should not be rewritten');
 assert.equal(flushCalls,0,'Already-confirmed checkpoint requires no extra flush');
 assert.ok(auditCalls>=1);
 assert.equal(state.vacation.active,false);
 assert.equal(state.vacation.paused,true);
 assert.equal(state.year,2031);
 assert.equal(state.day,18);
 // Genuine running Worker must NEVER be bypassed.
 v18112Dismissal.pending=true;v53Sim.active=true;v53Sim.syncing=true;
 const savesBefore=persistCalls;
 v555UpdateChrome(root);
 assert.equal(button.disabled,true,'Do not unlock while Worker is active');
 assert.equal(await v18334RecoverDismissal(),false);
 assert.equal(persistCalls,savesBefore,'Do not save concurrently with Worker');
 v53Sim.active=false;
 // An invalid checkpoint must leave the action safely disabled.
 audit={year:2030,day:18,careerId:'career-2031'};
 assert.equal(await v18334RecoverDismissal(),false);
 v555UpdateChrome(root);
 assert.equal(button.disabled,true,'Unverified save must not unlock proposal search');
 assert.equal(v18112Dismissal.pending,true);
 // Checkpoint with the wrong career is equally unsafe.
 audit={year:2031,day:18,careerId:'other-save'};
 assert.equal(await v18334RecoverDismissal(),false);
 assert.equal(v18112Dismissal.pending,true);
 // Correct checkpoint recovers the same save, preserving world and history.
 audit={year:2031,day:18,careerId:'career-2031'};
 assert.equal(await v18334RecoverDismissal(),true);
 assert.equal(button.disabled,false);
 // During Turbo waiting, keep Stop available even if a worker day is running.
 v89JobWait.active=true;v89JobWait.stop=false;v53Sim.active=true;
 v555UpdateChrome(root);
 assert.equal(button.disabled,false,'Stop must remain available during job wait');
 v89JobWait.stop=true;v555UpdateChrome(root);
 assert.equal(button.disabled,true,'Prevent double stop after Stop requested');
 v89JobWait.active=false;v89JobWait.stop=false;v53Sim.active=false;
 // Current-club and national careers do not activate unemployed recovery.
 state.userEmployed=true;v18112Dismissal.pending=true;v53Sim.syncing=true;
 const after=persistCalls;
 assert.equal(await v18334RecoverDismissal(),false);
 assert.equal(persistCalls,after);
 state.userEmployed=false;state.v640National={userTeam:'BRA'};
 assert.equal(await v18334RecoverDismissal(),false);
 assert.equal(persistCalls,after);
 console.log(JSON.stringify({ok:true,version:'18.334',
  recovered2031:true,exactCheckpointRequired:true,careerIdProtected:true,
  noConcurrentWorker:true,turboStopStillWorks:true,otherCareersUnaffected:true,
  saveCalls:persistCalls,flushCalls,auditCalls}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
    file = root / "test-unemployed-resume-18334.cjs"
    file.write_text(boot + "\n" + helper + "\n" + wrapper + "\n" + tests, encoding="utf-8")
    try:
        chk = subprocess.run(["node", "--check", str(file)], capture_output=True, text=True, timeout=30)
        if chk.returncode:
            raise RuntimeError("18.334 JavaScript syntax: " + chk.stderr[-4000:])
        run = subprocess.run(["node", str(file)], capture_output=True, text=True, timeout=40)
        if run.returncode:
            raise RuntimeError("18.334 regression failed: " + (run.stderr or run.stdout)[-5000:])
    finally:
        file.unlink(missing_ok=True)
    result = json.loads(run.stdout.strip().splitlines()[-1])
    if not result.get("ok"):
        raise RuntimeError("18.334 runtime regression did not succeed")
    (root / "unemployed-resume-18334-tests.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()
