from __future__ import annotations
import json,sys
from pathlib import Path

VERSION='18.370.0'
MARK='FUTBR_BOUNDED_JOBWAIT_18370'

def once(s,old,new,label):
 n=s.count(old)
 if n!=1:raise RuntimeError(f'18.370 {label}: expected one anchor, got {n}')
 return s.replace(old,new,1)

UI_HELPER=r'''/* FUTBR_BOUNDED_JOBWAIT_18370
   An automatic job search is one continuous simulation, not an endless
   pipeline of complete asynchronous world saves. Preserve exact archives,
   checkpoint every four confirmed days and at every stop/offer/season end. */
const v18370JobSave={interval:4,commits:0,failed:0,lastMs:0,lastDay:null,lastYear:null,lastError:'',busy:false};
async function v18370CommitJobWait(){
 if(!state||v53Sim?.active||v53Sim?.starting||v53Sim?.syncing||v53Sim?.patching||v125VacIncoming)
  throw Error('Sincronização incompleta: checkpoint de propostas adiado com segurança.');
 if(v18370JobSave.busy)throw Error('Há outro checkpoint de propostas em andamento.');
 const year=Number(state.year),day=Number(state.day),careerId=String(state.v1903CareerId||'');
 if(!careerId||!Number.isSafeInteger(day)||!Number.isSafeInteger(year)||!v53Worker)
  throw Error('O estado completo do Worker não está disponível para o checkpoint.');
 v18370JobSave.busy=true;
 try{
  const before=performance.now();
  // Retain all game news (the game already caps this list at 70 entries).
  // These UI-only coach fields can change after Worker publishes each day.
  const coachDelta={offers:state.v636CoachOffers||[],offerMeta:state.v636CoachOfferMeta||{},
   tracker:state.v636CareerTracker||null,career:state.v636CoachCareer||[],
   news:Array.isArray(state.news)?state.news:[]};
  const result=await v53Call('jobwait-checkpoint-18370',{
   careerId,year,day,user:String(state.user||''),coachDelta});
  if(!result?.ok||Number(result.day)!==day||Number(result.year)!==year||
     String(result.careerId)!==careerId)
   throw Error('Checkpoint confirmou outra jornada ou carreira.');
  v18370JobSave.commits++;v18370JobSave.lastDay=day;v18370JobSave.lastYear=year;
  v18370JobSave.lastMs=Math.round(performance.now()-before);
  v18370JobSave.lastError='';
  try{v53Saved(result.saved||result);}catch(error){console.warn('[18.370] checkpoint UI',error);}
  if(typeof v93CoachSaveTimer!=='undefined'&&v93CoachSaveTimer){clearTimeout(v93CoachSaveTimer);v93CoachSaveTimer=0;}
  return true;
 }catch(error){v18370JobSave.failed++;v18370JobSave.lastError=String(error?.message||error);throw error;}
 finally{v18370JobSave.busy=false;}
}
window.GestorFC.jobWaitMemory18370={status:()=>({version:'18.370.0',...v18370JobSave,
  day:state?.day??null,year:state?.year??null,workerActive:!!v53Sim?.active,
  queue:v53PatchQueue?.length||0})};
'''

WORKER_HANDLER=r'''  if(m.op==='jobwait-checkpoint-18370'){
   if(running)throw Error('A jornada ainda está sendo simulada.');
   if(v150ManualSavePromise)await v150ManualSavePromise.catch(()=>{});
   if(!world?.players||!world?.teams||!world?.schedule||
      String(world.v1903CareerId||'')!==String(m.careerId||'')||
      String(world.user||'')!==String(m.user||'')||
      Number(world.year)!==Number(m.year)||Number(world.day)!==Number(m.day))
    throw Error('Worker de propostas divergiu da carreira/jornada da interface. Nenhum save foi sobrescrito.');
   const delta=m.coachDelta||{},serialized=JSON.stringify(delta);
   if(serialized.length>160000)throw Error('O delta de ofertas excedeu o limite seguro.');
   if(!Array.isArray(delta.offers)||!Array.isArray(delta.career)||!Array.isArray(delta.news)||
      !delta.offerMeta||typeof delta.offerMeta!=='object')
    throw Error('Delta de carreira inválido.');
   world.v636CoachOffers=delta.offers;
   world.v636CoachOfferMeta=delta.offerMeta;
   world.v636CareerTracker=delta.tracker||null;
   world.v636CoachCareer=delta.career;
   world.news=delta.news;
   // Exactly one atomic, sharded save; the world never leaves this Worker.
   const saved=await save(world);
   return {ok:true,year:world.year,day:world.day,careerId:world.v1903CareerId,saved};
  }
'''

def patch(s):
 for m in ('FUTBR_VACATION_RESUME_HANDOFF_18369','FUTBR_UNEMPLOYED_WORKER_REAL_PROGRESS_18368',
  'async function v89RunJobWait(){','async function simulate(message){',
  "const yearBefore=Number(state.year)||0,worldBefore=state;"):
  if m not in s:raise RuntimeError('18.370 missing dependency '+m)
 if MARK in s:raise RuntimeError('18.370 patch applied twice')
 a=s.index('async function v89RunJobWait(){');b=s.index('const v89BaseCareerPage=careerPage;',a)
 job=s[a:b]
 job=once(job,'let v18368Resident=null;','let v18368Resident=null,v18370Confirmed=0,v18370CommittedYear=null,v18370CommittedDay=null;', 'bounded loop tracker')
 job=once(job,'const yearBefore=Number(state.year)||0,worldBefore=state;',
  'const yearBefore=Number(state.year)||0;', 'remove retained old full world')
 job=once(job,'liveStateNoPreSave:true,jobWaitResident:v18368SameWorker',
  'liveStateNoPreSave:true,jobWaitResident:v18368SameWorker,jobWaitAuto:true',
  'tag dedicated search mode')
 job=once(job,'v89JobWait.days+=yearAfter===yearBefore?after-before:1;',
  '''v89JobWait.days+=yearAfter===yearBefore?after-before:1;
   v18370Confirmed++;
   // Coalesce full-world writes; the Worker remains resident between rounds.
   if(v18370Confirmed%v18370JobSave.interval===0||state.seasonDone||v89JobWait.stop||
      v636PendingCoachOffers(state).length){
    v89JobWait.stage='saving-checkpoint';
    await v18370CommitJobWait();
    v18370CommittedYear=Number(state.year);v18370CommittedDay=Number(state.day);
   }''','periodic and event checkpoint')
 job=once(job,"finally{\n  v89JobWait.stage='idle';", """finally{
  // Stop, dismissal, proposal and season end always leave a durable checkpoint.
  if(v18370Confirmed>0&&state&&
     (v18370CommittedYear!==Number(state.year)||v18370CommittedDay!==Number(state.day))){
   try{v89JobWait.stage='saving-final-checkpoint';await v18370CommitJobWait();}
   catch(error){toast('A carreira segue aberta, mas a última jornada não foi salva: '+
     (error?.message||error)+'. Salve manualmente antes de sair.','error');}
  }
  v89JobWait.stage='idle';""", 'final checkpoint on any exit')
 job=once(job,"v89JobWait.stage='idle';v89JobWait.active=false;",
  "v89JobWait.stage='idle';v89JobWait.active=false;try{window.GestorFC?.v170?.release?.();}catch(e){}",
  'release duplicate Worker world before final career rendering')
 s=s[:a]+job+s[b:]
 s=once(s,'async function v89RunJobWait(){',UI_HELPER+'\nasync function v89RunJobWait(){', 'in-scope small UI/RPC helper')
 ws=s.index('async function simulate(message){')
 we=s.index('const v124SkipFalse=new Set(',ws)
 engine=s[ws:we]
 engine=once(engine,
  "if(!fastManualDay&&!nationalJump&&!nextMatchJump&&v150ManualSavePromise)await v150ManualSavePromise.catch(()=>{});",
  "if((!fastManualDay&&!nationalJump&&!nextMatchJump||message.jobWaitAuto===true)&&v150ManualSavePromise)await v150ManualSavePromise.catch(()=>{});",
  'backpressure from prior manual save')
 engine=once(engine,
  "if((fastManualDay||nationalJump||nextMatchJump||lowMemoryDay)&&!failure&&world){",
  "if((fastManualDay||nationalJump||nextMatchJump||lowMemoryDay)&&!failure&&world&&!(fastManualDay&&message.jobWaitAuto===true)){",
  'suppress asynchronous save chain for job search only')
 s=s[:ws]+engine+s[we:]
 handle=s.index("if(m.op==='save'){",s.index('async function handle(m){'))
 s=s[:handle]+WORKER_HANDLER+s[handle:]
 s=once(s,"const EDITION='18.369.0';","const EDITION='18.370.0';",'edition')
 s=once(s,"window.GestorFC.version='18.369.0';window.GestorFC.visualVersion='18.369.0';",
  "window.GestorFC.version='18.370.0';window.GestorFC.visualVersion='18.370.0';",'visual version')
 return s

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_bounded_jobwait_18370.py <project>')
 root=Path(sys.argv[1]);file=root/'src/index.html';s=file.read_text(encoding='utf-8')
 s=patch(s);file.write_text(s,encoding='utf-8')
 report={'ok':True,'version':VERSION,'noPerDaySaveChain':True,'workerSaveBackpressure':True,
  'checkpointEveryConfirmedFourDays':True,'finalSaveOnStopOfferSeasonEnd':True,
  'permanentOldStateReferenceRemoved':True,'fullWorldStaysInWorker':True,
  'careerAndDayIdentityChecked':True,'noOldSaveOverwrite':True,'offerAndCareerDeltaPreserved':True,
  'historyAndPlayerCodecPreserved':True,'workerReleasedAtSearchExit':True}
 (root/'jobwait-memory-18370-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
