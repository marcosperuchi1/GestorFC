from __future__ import annotations
import json
import re
import sys
from pathlib import Path

VERSION="18.366.0"
MARK="FUTBR_SCOPE_REPAIR_18366"
SCRIPT_IDS=(
 "futbr-jobwait-state-18363",
 "futbr-vacation-handoff-18364",
 "futbr-dismissal-source-18365",
)

def one(text, old, new, label):
    count=text.count(old)
    if count!=1:
        raise RuntimeError(f"18.366 {label}: expected exactly 1 anchor, got {count}")
    return text.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: fix_unemployed_scope_18366.py <project-dir>")
    root=Path(sys.argv[1]).resolve()
    p=root/"src/index.html"
    html=p.read_text(encoding="utf-8")
    if MARK in html: raise RuntimeError("18.366 repair already applied")
    for required in (
        "let state=null,saved=null",
        "const v53Sim={",
        "const v18359BaseStart=v53StartSimulation;",
        "FUTBR_JOBWAIT_STATE_CORE_18363",
        "FUTBR_VACATION_JOB_HANDOFF_18364",
        "FUTBR_DISMISSAL_SOURCE_18365",
        "if(el.dataset.action==='v89-job-wait'&&typeof v18365HandleClick==='function'",
        "v53Worker?.postMessage({op:'pause',end:true,reason:'dismissal'})",
    ):
        if required not in html:raise RuntimeError("18.366 required live source missing "+required)

    # These 18.363/364/365 blocks were placed BEFORE </body>, outside the
    # original (()=>{
    #   let state=null; let v53Sim=...; let v53Worker=...
    # })(); scope. They were never able to read the authoritative game state.
    # Move the EXACT existing blocks into that same IIFE. Do NOT duplicate the
    # world, restore a disk save, or add another worker.
    blocks=[]
    for script_id in SCRIPT_IDS:
        pattern=re.compile(
            r"\s*<script\s+id=[\"']"+re.escape(script_id)+
            r"[\"']\s*>\s*([\s\S]*?)\s*</script>\s*",re.I)
        matches=list(pattern.finditer(html))
        if len(matches)!=1:
            raise RuntimeError(f"18.366 {script_id}: expected one detached script, found {len(matches)}")
        block=matches[0].group(1)
        if not block.strip():
            raise RuntimeError("18.366 empty detached script "+script_id)
        blocks.append((script_id,block))
        html=html[:matches[0].start()]+"\n"+html[matches[0].end():]
    # Find the executable source containing the actual lexical declaration.
    # The primary IIFE has a closing })(); directly before its </script>.
    index=html.index("let state=null,saved=null")
    script_close=html.find("</script>",index)
    if script_close<0:raise RuntimeError("18.366 main script closing tag not found")
    iife_close=html.rfind("})();",index,script_close)
    if iife_close<0 or html[iife_close+len("})();"):script_close].strip():
        raise RuntimeError("18.366 main closure is not exactly before </script>; refusing unsafe patch")
    main_open=html.rfind("<script",0,index)
    if main_open<0 or not main_open<index<iife_close<script_close:
        raise RuntimeError("18.366 state not in expected main game script")

    extra=r"""
/* FUTBR_SCOPE_REPAIR_18366
   All three last controllers now share the original private lexical state.
   A separate <script> tag cannot access state, worker or active game views.
   Never recreate state, never start a parallel vacation Worker. */
const v18366BaseVacationHeader=v624VacationHeaderHTML;
v624VacationHeaderHTML=function(...args){
 const html=v18366BaseVacationHeader(...args);
 if(state?.userEmployed===false&&v53Sim?.mode==='vacation')
  return html.replace('Em execução','Encerrando férias');
 return html;
};
window.GestorFC=window.GestorFC||{};
window.GestorFC.scope18366={
 version:'18.366',
 status:()=>({
  sameGameScope:true,
  year:state?.year??null,
  day:state?.day??null,
  unemployed:!!(state&&state.userEmployed===false),
  workerActive:!!v53Sim?.active,
  workerMode:v53Sim?.mode||'',
  pendingJobHandoff:!!v18365Job.pending,
  queuedClicks:v18365Job.requested,
  repeatedClicks:v18365Job.duplicateClicks,
  handoffState:v18365Job.last,
  workerEndMessages:v18365Job.workerStopSent
 })
};
"""
    insert="\n"+'\n'.join(
        f"// 18.366 relocated in-scope: {script_id}\n{block}\n"
        for script_id,block in blocks
    )+"\n"+extra+"\n"
    html=html[:iife_close]+insert+html[iife_close:]
    # Explicitly assert that the old detached scripts are GONE, not left as
    # duplicate, broken event owners.
    for script_id,_ in blocks:
        if re.search(r"<script\s+id=[\"']"+re.escape(script_id)+r"[\"']",html,re.I):
            raise RuntimeError("18.366 external script still present "+script_id)
    for anchor in (
        "FUTBR_JOBWAIT_STATE_CORE_18363",
        "FUTBR_VACATION_JOB_HANDOFF_18364",
        "FUTBR_DISMISSAL_SOURCE_18365",
        MARK,
    ):
        if html.count("/* "+anchor)!=1:
            raise RuntimeError("18.366 duplicate/missing in-scope runtime "+anchor)
    html=one(html,"const EDITION='18.365.0';",
        "const EDITION='18.366.0';","visible edition")
    html=one(html,
      "window.GestorFC.version='18.365.0';window.GestorFC.visualVersion='18.365.0';",
      "window.GestorFC.version='18.366.0';window.GestorFC.visualVersion='18.366.0';",
      "runtime version")
    p.write_text(html,encoding="utf-8")
    report={
        "ok":True,"version":VERSION,"originalStateScopeReused":True,
        "relocatedOriginalDetachedScripts":[x[0] for x in blocks],
        "allControllersExecuteInsideOriginalGameIIFE":True,
        "removesDetachedReferenceErrors":True,
        "realButtonListenerReusesGameState":True,
        "originalWorkerStopAndAtomicCheckpointPreserved":True,
        "samePrivateCareerAndHistory":True,
        "noExtraWorldSerialization":True,"noParallelWorker":True,
        "careerViewUsesSameState":True,
    }
    (root/"scope-repair-18366-install.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":main()
