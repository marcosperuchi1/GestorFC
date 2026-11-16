from __future__ import annotations
import json
import sys
from pathlib import Path

VERSION = "18.334"
MARK = "FUTBR_UNEMPLOYED_RESUME_18334_BEGIN"
ANCHOR = "const v18112BaseChrome=v555UpdateChrome;"
OLD_WAIT = "const waiting=v18112Dismissal.pending||(!v89JobWait.active&&(v53Sim?.active||v53Sim?.starting||v53Sim?.syncing||v53Sim?.patching));"
NEW_WAIT = "const waiting=v18334ShouldWait();if(waiting)v18334ScheduleRecovery();"

HELPER = r"""
/* FUTBR_UNEMPLOYED_RESUME_18334_BEGIN
   Repair only the post-vacation unemployed handoff. Do not bypass active Workers.
   Re-enable job search only after the authoritative saved day/year is verified. */
let v18334RecoverPromise=null,v18334LastTry=0;
function v18334EligibleForJobWait(s=state){
 return !!s&&s.userEmployed===false&&!s.v640National?.userTeam&&!s.seasonDone&&!s.live&&!s.vacation?.active;
}
function v18334SafeToVerify(){
 return v18334EligibleForJobWait()&&!v53Sim?.active&&!v53Sim?.starting&&!v53Creating&&!v18326AdvanceBusy;
}
function v18334ShouldWait(){
 if(v89JobWait.active)return !!v89JobWait.stop; // Keep Stop accessible during each Worker day.
 return !v18334EligibleForJobWait()||!!(v18112Dismissal.pending||
  v53Sim?.active||v53Sim?.starting||v53Sim?.syncing||v53Sim?.patching||
  v53Creating||v18326AdvanceBusy);
}
async function v18334RecoverDismissal(){
 if(v18334RecoverPromise)return v18334RecoverPromise;
 if(!v18334SafeToVerify())return false;
 if(!v18112Dismissal.pending&&!v53Sim?.syncing&&!v53Sim?.patching)return true;
 const s=state,year=Number(s.year),day=Number(s.day),careerId=String(s.v1903CareerId||'');
 const task=(async()=>{
  try{
   // The 18.112 safeguard is mandatory: never run another round on an old checkpoint.
   await persist(false);
   await v52FlushSave();
   const audit=await window.GestorFC?.v171?.storageAudit?.();
   if(!audit||Number(audit.year)!==year||Number(audit.day)!==day)return false;
   if(audit.careerId&&careerId&&String(audit.careerId)!==careerId)return false;
   if(state!==s||Number(state.year)!==year||Number(state.day)!==day||
      String(state.v1903CareerId||'')!==careerId||!v18334SafeToVerify())return false;
   if(state.vacation){
    state.vacation.active=false;state.vacation.paused=true;
    state.vacation.remaining=0;state.vacation.untilSeason=false;
   }
   v18112Dismissal.pending=false;v18112Dismissal.ready=true;
   // These are stale UI-sync guards only; the Worker is inactive and the save was audited.
   v53Sim.syncing=false;v53Sim.patching=false;
   const root=document.querySelector('#app');
   if(root)try{v555UpdateChrome(root);}catch(e){console.warn('[18.334] chrome',e);}
   return true;
  }catch(err){
   console.warn('[18.334] Salvamento da demissão ainda não confirmado:',err);
   return false;
  }
 })();
 v18334RecoverPromise=task;
 try{return await task;}finally{v18334RecoverPromise=null;}
}
function v18334ScheduleRecovery(){
 if(!v18334SafeToVerify()||v18334RecoverPromise)return;
 if(!v18112Dismissal.pending&&!v53Sim?.syncing&&!v53Sim?.patching)return;
 const now=Date.now();
 if(now-v18334LastTry<2000)return;
 v18334LastTry=now;
 queueMicrotask(()=>{void v18334RecoverDismissal();});
}
window.GestorFC.unemployedResume18334={
 version:'18.334',checkpointAuditRequired:true,workerMutualExclusion:true,
 status:()=>({year:Number(state?.year)||0,day:Number(state?.day)||0,
  unemployed:!!(state?.userEmployed===false),pending:!!v18112Dismissal.pending,
  syncing:!!v53Sim?.syncing,patching:!!v53Sim?.patching,
  active:!!v53Sim?.active,waiting:!!v18334ShouldWait()}),
 recover:()=>v18334RecoverDismissal()
};
/* FUTBR_UNEMPLOYED_RESUME_18334_END */
"""

def once(src: str, old: str, new: str, label: str) -> str:
    hits = src.count(old)
    if hits != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {hits}")
    return src.replace(old, new, 1)

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_unemployed_resume_18334.py <project-dir>")
    root = Path(sys.argv[1]).resolve()
    target = root / "src" / "index.html"
    html = target.read_text(encoding="utf-8")
    if MARK in html:
        print(json.dumps({"ok": True, "version": VERSION, "alreadyInstalled": True}))
        return
    if "FUTBR_UNEMPLOYED_TURBO_18327" not in html:
        raise RuntimeError("Missing validated 18.327 job-search pipeline")
    if "FUTBR_MANUAL_ADVANCE_18326_START" not in html:
        raise RuntimeError("Missing 18.326 advance serialization")
    html = once(html, ANCHOR, HELPER + "\n" + ANCHOR, "vacation-dismissal chrome anchor")
    html = once(html, OLD_WAIT, NEW_WAIT, "stale sync/discharge waiting guard")
    if "const waiting=v18112Dismissal.pending||" in html:
        raise RuntimeError("Original unrecoverable job-search button guard is still active")
    target.write_text(html, encoding="utf-8")
    report = {
        "ok": True, "version": VERSION, "scope": "dismissal-during-vacation and unemployed proposal button",
        "autoRecovery": "only when no worker or manual day is active",
        "checkpointAudit": "persist + flush + exact year/day and optional career ID",
        "preservesExistingSave": True, "retainsWorkerLock": True,
        "preservesTurboOfferLoop": True, "nationalCareerUnchanged": True,
    }
    (root / "unemployed-resume-18334-install.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))

if __name__ == "__main__":
    main()
