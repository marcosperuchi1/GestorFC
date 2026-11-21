"""Start vacations from an exact bounded checkpoint instead of cloning the world.

Apply after the 18.373 storage and job-search ownership corrections.  The UI
keeps its complete world for the existing read-only vacation views; only the
large postMessage serialization buffer is removed from the boot path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MARK = 'FUTBR_VACATION_BOUNDED_BOOT_18373'


def once(source, old, new, label):
    if source.count(old) != 1:
        raise RuntimeError(f'18.373 vacation boot {label}: expected one anchor, got {source.count(old)}')
    return source.replace(old, new, 1)


IDENTITY = r'''
function v18373VacationPoint(s){return {
 careerId:String(s?.v1903CareerId||''),coachId:String(s?.userCoachId||''),user:String(s?.user||''),
 futbrSaveId:String(s?.futbrSaveId||''),userEmployed:!!s?.userEmployed,
 year:Number(s?.year),day:Number(s?.day),seasonDone:!!s?.seasonDone,
 nationalCode:String(s?.v640National?.userTeam||'')};}
function v18373SameVacationPoint(a,b){return !!a&&!!b&&!!a.careerId&&!!a.coachId&&
 ['careerId','coachId','user','futbrSaveId','userEmployed','year','day','seasonDone','nationalCode']
  .every(key=>a[key]===b[key]);}
function v18373VerifyVacationBoot(stored,token,message){
 const point=v18373VacationPoint(stored?.root);
 if(message?.mode!=='vacation'||!message.loadSaved||message.state||message.vacationCheckpoint||
    stored?.format!=='GFC_SHARDED_171'||!token?.token||
    !Number.isSafeInteger(Number(token.revision))||Number(token.revision)<1||
    String(stored.token)!==String(token.token)||Number(stored.revision)!==Number(token.revision)||
    !v18373SameVacationPoint(point,token)||Number(stored.year)!==point.year||Number(stored.day)!==point.day||
    point.year!==Number(message.year)||point.day!==Number(message.day)||
    point.careerId!==String(message.v1903CareerId)||point.user!==String(message.v1903User)||
    !!point.nationalCode!==!!message.v1903National||
    !['players','teams','coaches','schedule','competitions','competitionStats','allTimeStats']
      .every(key=>stored.collections?.[key]))
  throw Error('O checkpoint das férias não corresponde à carreira e à jornada atuais. Nenhuma jornada foi simulada.');
 return true;
}
'''

UI = r'''
/* FUTBR_VACATION_BOUNDED_BOOT_18373 */
const v18373VacationBootStats={version:'18.373',checkpoints:0,failures:0,lastMs:0,lastYear:null,lastDay:null};
''' + IDENTITY + r'''
async function v18373PrepareVacationBoot(current){
 const began=performance.now(),origin=v18373VacationPoint(current);
 const check=()=>{
  if(state!==current||!v18373SameVacationPoint(v18373VacationPoint(state),origin)||
     v53Sim.active||v53Sim.syncing||v53Sim.patching||v125VacIncoming||v53Creating||
     window.GestorFC?.jobWaitMemory18373?.status?.().ownsWorld)
   throw Error('A carreira mudou durante a preparação das férias. O checkpoint anterior foi preservado.');
 };
 try{
  check();
  // A migration already between batches still owns its captured old season.
  // The starting guard makes it yield without committing; join that work
  // before the writer observes the legacy or packed historical collections.
  if(typeof v555ArchiveMigration!=='undefined'&&v555ArchiveMigration)await v555ArchiveMigration;
  check();if(v52SavePromise)await v52SavePromise;check();
  // Vacation controls and recent coach/team decisions can have changed without
  // calling persist. Always checkpoint the current world; do not reuse a merely
  // matching date, and never send a fallback full-state message on failure.
  v53Sim.progress='Preparando o salvamento para iniciar as férias';
  try{v53PaintStatus();}catch(e){}
  const pending=persist(false);await v52FlushSave();await pending;
  if(v52SavePromise)await v52SavePromise;check();
  if(!saveOK||v52SaveDirty||v52SavePromise)
   throw Error('Não foi possível confirmar o salvamento antes das férias. A carreira continua aberta.');
  const stored=await v52ReadRaw(STORE);check();
  const token={...origin,token:String(stored?.token||''),revision:Number(stored?.revision)||0};
  v18373VerifyVacationBoot(stored,token,{mode:'vacation',loadSaved:true,vacationCheckpoint:false,
   year:origin.year,day:origin.day,v1903CareerId:origin.careerId,v1903User:origin.user,
   v1903National:!!origin.nationalCode});
  if(!saveOK||v52SaveDirty||v52SavePromise)throw Error('Uma alteração ainda precisa ser salva antes das férias.');
  v18373VacationBootStats.checkpoints++;v18373VacationBootStats.lastMs=Math.round(performance.now()-began);
  v18373VacationBootStats.lastYear=origin.year;v18373VacationBootStats.lastDay=origin.day;
  return token;
 }catch(error){v18373VacationBootStats.failures++;throw error;}
}
window.GestorFC.vacationBoot18373={status:()=>({...v18373VacationBootStats}),fullStateTransfer:false};
'''


def patch(source):
    if MARK in source:
        return source
    for required in ('FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN', 'FUTBR_JOBWAIT_SINGLE_OWNER_18373'):
        if required not in source:
            raise RuntimeError('Missing prerequisite ' + required)

    source = once(source,
        " return !!(state?.v18373JobWaitPartial||flow?.ownsWorld||flow?.phase==='preparing');",
        " return !!(v53Sim?.starting||state?.v18373JobWaitPartial||flow?.ownsWorld||flow?.phase==='preparing');",
        'pause yielding archive migration during simulation preparation')

    start = source.index('async function v53StartSimulation(mode,options={}){')
    end = source.index('\nrunVacation=async function()', start)
    base = source[start:end]
    old = "  const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=!!options?.liveStateNoPreSave&&\n      (mode==='vacation'||((mode==='day'||mode==='dayfast')&&\n       state?.userEmployed===false&&!state?.v640National?.userTeam))||v18369CanStartFromReturnedVacation(mode,state);"
    new = "  const v18373VacationBoot=mode==='vacation'?await v18373PrepareVacationBoot(state):null;\n  const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=mode!=='vacation'&&(!!options?.liveStateNoPreSave&&\n      (mode==='vacation'||((mode==='day'||mode==='dayfast')&&\n       state?.userEmployed===false&&!state?.v640National?.userTeam))||v18369CanStartFromReturnedVacation(mode,state));"
    base = once(base, old, new, 'bounded current-state checkpoint before Worker boot')
    base = once(base, '    w.postMessage(msg);',
        "    if(v18373VacationBoot){msg.vacationBoot18373=v18373VacationBoot;msg.vacationCheckpoint=false;}\n    w.postMessage(msg);",
        'exact checkpoint token and no stale vacation overlay')
    source = source[:start] + UI + '\n' + base + source[end:]

    worker_start = source.index('function v53WorkerMain(){')
    worker_end = source.index('\n\n\nconst v18191uPlayerFields=', worker_start)
    worker = source[worker_start:worker_end]
    worker = once(worker, ' async function simulate(message){',
        IDENTITY + "\n async function simulate(message){\n  if(message.vacationBoot18373&&(message.mode!=='vacation'||!message.loadSaved||message.state||message.vacationCheckpoint))\n   throw Error('As férias exigem o checkpoint limitado confirmado antes do início.');",
        'Worker boot transport guard')
    anchor = '   world=await decode(stored);stored=null;'
    worker = once(worker, anchor,
        '   if(message.vacationBoot18373)v18373VerifyVacationBoot(stored,message.vacationBoot18373,message);\n' + anchor,
        'verify the exact manifest before decoding or playing')
    return source[:worker_start] + worker + source[worker_end:]


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: fix_vacation_memory_boot_18373.py <project>')
    root = Path(sys.argv[1])
    path = root / 'src/index.html'
    source = patch(path.read_text(encoding='utf-8'))
    path.write_text(source, encoding='utf-8')
    report = {'ok': True, 'version': '18.373.0',
              'boundedCheckpointBeforeVacationBoot': True,
              'exactManifestVerifiedBeforeWorkerDecode': True,
              'staleVacationOverlayDisabledForFreshBoot': True,
              'inFlightArchiveMigrationJoinedBeforeSave': True,
              'completeUiPreservedForVacationQueries': True}
    (root / 'vacation-memory-boot-18373-install.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
