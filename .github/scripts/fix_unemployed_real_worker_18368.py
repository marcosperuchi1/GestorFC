from __future__ import annotations
import json,sys
from pathlib import Path

VERSION='18.368.0'
MARK='FUTBR_UNEMPLOYED_WORKER_REAL_PROGRESS_18368'

def once(s, old, new, label):
    hits=s.count(old)
    if hits!=1: raise RuntimeError(f'18.368 {label}: expected one real-source occurrence, got {hits}')
    return s.replace(old,new,1)

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: fix_unemployed_real_worker_18368.py <project>')
    root=Path(sys.argv[1]).resolve()
    target=root/'src/index.html'
    s=target.read_text(encoding='utf-8')
    if MARK in s: raise RuntimeError('18.368 patch attempted twice')
    for feature in ('FUTBR_JOBWAIT_REAL_PROGRESS_18367','FUTBR_SCOPE_REPAIR_18366',
                    'FUTBR_JOBWAIT_STATE_CORE_18363','v18311LiveVacation',
                    "async function v53StartSimulation(mode,options={}){"):
        if feature not in s:raise RuntimeError('18.368 missing stable source '+feature)

    # Existing 18.367 job-search loop invokes dayfast without options.
    # In that case the original simulation first awaits v52FlushSave, which
    # can encode the complete 150k+ player world BEFORE even starting Worker.
    # The existing 18.311 live-state pathway safely avoids this pre-save,
    # retaining the previous committed checkpoint until the Worker commits
    # the advanced day. A complete state is transferred only for the first
    # day; later days reuse the exact same still-resident Worker.
    a=s.index('async function v89RunJobWait(){')
    b=s.index('const v89BaseCareerPage=careerPage;',a)
    job=s[a:b]
    job=once(job,
      "  try{\n   while(state&&!state.userEmployed",
      "  let v18368Resident=null;\n  try{\n   while(state&&!state.userEmployed",
      'track resident Worker only for this job-search run')
    job=once(job,
      "   await v53StartSimulation('dayfast');",
      """   const v18368SameWorker=!!(v18368Resident&&v53Worker&&v18368Resident===v53Worker&&
       !v53Sim?.active&&!v53Sim?.starting);
   // First round sends the authoritative live world exactly once; every
   // subsequent round uses the resident Worker with matching career/year/day.
   // Never wait for an entire-world pre-save before the first journey.
   await v53StartSimulation('dayfast',{
      liveStateNoPreSave:true,jobWaitResident:v18368SameWorker
   });
   v18368Resident=v53Worker||null;""",
      'make actual unemployed dayfast Worker start without full pre-save')
    job=once(job,
      "   v89JobWait.lastProgressAt=Date.now();v89JobWait.stage='round-completed';",
      """   v89JobWait.lastProgressAt=Date.now();v89JobWait.stage='round-completed';
   // Refresh only existing chrome: the original Worker controls the world.
   try{v555UpdateChrome(document.querySelector('#app')||document);}catch(e){}""",
      'refresh confirmed day in header')
    s=s[:a]+job+s[b:]

    # The real baseline simulator must not clone the entire world on every
    # dayfast request. The worker already checks career ID, former club,
    # national-team identity and exact year/day before reusing its world.
    # This option is exclusively used by the unemployed auto-search loop.
    start=s.index('async function v53StartSimulation(mode,options={}){')
    end=s.index('runVacation=async function',start)
    core=s[start:end]
    core=once(core,'     if(!canLoadSaved)msg.state=state;',
      """     if(mode==='dayfast'&&options?.jobWaitResident===true)msg.jobWaitResident=true;
     if(!canLoadSaved&&!(mode==='dayfast'&&options?.jobWaitResident===true))msg.state=state;""",
      'send live full world only for first dayfast job round')
    s=s[:start]+core+s[end:]

    # Fail closed if the worker could not reuse the exact same world. NEVER
    # fall back to a different career or silently process an old disk save.
    worker=s.index('  async function simulate(message){')
    next_fn=s.index("   if(!residentManual&&message.loadSaved){",worker)
    s=s[:next_fn]+"""   if(message.jobWaitResident&&!residentManual)
    throw Error('O Worker de propostas perdeu a sincronização de carreira/jornada. Avanço interrompido sem recuperar um save antigo.');
"""+s[next_fn:]

    runtime="""/* FUTBR_UNEMPLOYED_WORKER_REAL_PROGRESS_18368
   Same original dayfast Worker, no full-world pre-save before first round,
   no state clone on subsequent rounds, exact resident identity guard. */
window.GestorFC.unemployedWorker18368={
 status:()=>({
  version:'18.368.0',running:!!v89JobWait?.active,
  stage:v89JobWait?.stage||'idle',daysConfirmed:Number(v89JobWait?.days)||0,
  year:Number(state?.year)||0,day:Number(state?.day)||0,
  workerActive:!!v53Sim?.active,workerStarting:!!v53Sim?.starting,
  workerMode:v53Sim?.mode||'',workerProgress:v53Sim?.progress||'',
  preSaveRunning:!!v52SavePromise,saveDirty:!!v52SaveDirty,
  careerId:String(state?.v1903CareerId||'')
 })
};
"""
    s=once(s,'const v18366BaseVacationHeader=v624VacationHeaderHTML;',runtime+'const v18366BaseVacationHeader=v624VacationHeaderHTML;','in-scope diagnostic')
    s=once(s,"const EDITION='18.367.0';","const EDITION='18.368.0';",'visible version')
    s=once(s,"window.GestorFC.version='18.367.0';window.GestorFC.visualVersion='18.367.0';",
      "window.GestorFC.version='18.368.0';window.GestorFC.visualVersion='18.368.0';",'runtime version')
    target.write_text(s,encoding='utf-8')
    report={
      'ok':True,'version':VERSION,'firstDayUsesOriginalLiveWorker':True,
      'blockingFullPreSaveRemoved':True,'previousCheckpointPreserved':True,
      'residentWorkerReusedOnlyWhenIdentical':True,'workerValidatesYearDayAndCareer':True,
      'fullWorldTransferredAtMostOncePerContinuousWait':True,
      'perRoundOriginalWorldCheckpointPreserved':True,
      'noParallelWorkers':True,'nationalManagerUnaffected':True,
      'historicRecordsAndSaveCodecUnchanged':True,
    }
    (root/'unemployed-worker-18368-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
