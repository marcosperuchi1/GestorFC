from __future__ import annotations
import sys,json
from pathlib import Path
MARK='FUTBR_JOBWAIT_REAL_PROGRESS_18367'
def once(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'18.367 {label}: expected one anchor, got {n}')
 return s.replace(a,b,1)
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_jobwait_real_progress_18367.py <project>')
 root=Path(sys.argv[1]);p=root/'src/index.html';s=p.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.367 already applied')
 for a in ('FUTBR_SCOPE_REPAIR_18366','FUTBR_JOBWAIT_STATE_CORE_18363',"await v53StartSimulation('dayfast');"):
  if a not in s:raise RuntimeError('missing '+a)
 start=s.index('async function v89RunJobWait(){')
 end=s.index('const v89BaseCareerPage=careerPage;',start)
 block=s[start:end]
 block=once(block,"v89JobWait.active=true;v89JobWait.stop=false;v89JobWait.startDay=Number(state.day)||0;v89JobWait.days=0;window.__gfcV172JobWait=true;render();v89PaintJobWait();",
  """v89JobWait.active=true;v89JobWait.stop=false;v89JobWait.startDay=Number(state.day)||0;v89JobWait.days=0;
  v89JobWait.stage='starting-first-round';v89JobWait.startedAt=Date.now();v89JobWait.lastProgressAt=Date.now();
  window.__gfcV172JobWait=true;render();v89PaintJobWait();""",'initial search activity')
 block=once(block,
  "await v53StartSimulation('dayfast');\n   v89JobWait.days+=Math.max(1,(Number(state?.day)||before+1)-before);",
  """// 18.367: do not report a phantom day. The original Worker is the ONLY
   // authority for world mutations; reuse its memory-safe turbo dayfast route.
   v89JobWait.stage='simulating-dayfast';
   const yearBefore=Number(state.year)||0,worldBefore=state;
   v89PaintJobWait();
   await v53StartSimulation('dayfast');
   if(!state||state.userEmployed||v89HasNationalJob())break;
   const after=Number(state.day);
   const yearAfter=Number(state.year);
   if(!Number.isFinite(after)||!Number.isFinite(before)||
      (yearAfter===yearBefore&&after<=before)){
    throw Error('O motor concluiu sem avançar a jornada. Busca pausada para evitar progresso falso; o último save permanece preservado.');
   }
   if(yearAfter!==yearBefore&&yearAfter<yearBefore)
    throw Error('A temporada retrocedeu durante o avanço. Busca interrompida com segurança.');
   v89JobWait.days+=yearAfter===yearBefore?after-before:1;
   v89JobWait.lastProgressAt=Date.now();v89JobWait.stage='round-completed';
   // No full-world redraw or new Worker during the loop.
   """,'verify genuine day progress')
 # The 18.366 source has multiple layers of wrappers and formatting.
 # Modify the unique final reset itself, not an indent-sensitive finally header.
 final_reset="v89JobWait.active=false;"
 if block.count(final_reset)!=1:
  raise RuntimeError(f'18.367 final cleanup: expected one reset, got {block.count(final_reset)}')
 cleanup=block.index(final_reset)
 if "finally" not in block[max(0,cleanup-220):cleanup]:
  raise RuntimeError('18.367 final reset is no longer inside finally; refusing unsafe patch')
 block=block.replace(final_reset,"v89JobWait.stage='idle';"+final_reset,1)
 s=s[:start]+block+s[end:]
 s=once(s,"const EDITION='18.366.0';","const EDITION='18.367.0';",'edition')
 s=once(s,"window.GestorFC.version='18.366.0';window.GestorFC.visualVersion='18.366.0';",
   "window.GestorFC.version='18.367.0';window.GestorFC.visualVersion='18.367.0';",'runtime version')
 insert="""/* FUTBR_JOBWAIT_REAL_PROGRESS_18367: genuine Worker day validation.
   Never infer progress or perform an extra world save in this view. */
window.GestorFC.jobProgress18367={
 status:()=>({running:!!v89JobWait.active,stage:v89JobWait.stage||'idle',
  daysConfirmed:v89JobWait.days||0,lastProgressAt:v89JobWait.lastProgressAt||0,
  year:state?.year??null,day:state?.day??null,workerMode:v53Sim?.mode||'',
  workerActive:!!v53Sim?.active,workerStarting:!!v53Sim?.starting,
  workerProgress:v53Sim?.progress||'',savePending:!!v52SavePromise,
  syncPending:!!v53Sim?.syncing,careerId:String(state?.v1903CareerId||'')})
};
"""
 anchor="const v18366BaseVacationHeader=v624VacationHeaderHTML;"
 s=once(s,anchor,insert+anchor,'in-scope runtime telemetry')
 p.write_text(s,encoding='utf-8')
 (root/'job-progress-18367-install.json').write_text(json.dumps(dict(ok=True,version='18.367.0',progressOnlyOnWorkerDay=True,usesExistingDayfastWorker=True,noExtraCheckpoint=True,noParallelWorker=True),indent=2),encoding='utf-8')
if __name__=='__main__':main()
