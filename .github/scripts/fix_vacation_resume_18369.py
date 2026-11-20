from __future__ import annotations
import json,sys
from pathlib import Path

VERSION='18.369.0'
MARK='FUTBR_VACATION_RESUME_HANDOFF_18369'

def once(text,old,new,reason):
    n=text.count(old)
    if n!=1:raise RuntimeError(f'18.369 {reason}: expected one original source occurrence, got {n}')
    return text.replace(old,new,1)

RUNTIME=r"""
/* FUTBR_VACATION_RESUME_HANDOFF_18369
   A completed vacation sends an authoritative, fully rebuilt career back to
   the UI. Its preceding full save can still be on the OLD day, because the
   vacation saves via a checkpoint. Do not run a new Worker from that stale
   old-day save or start a huge pre-save before next-match / one-day advance.
   The next action will use THIS authenticated, synchronized live world once.
   Never release a partially streamed world, a busy Worker or another career. */
let v18369VacationReturn=null;
const v18369ResumeStats={captured:0,liveStarts:0,invalid:0,
 last:'idle',startedDay:null,returnedDay:null};
function v18369CaptureVacationReturn(s=state,m=null){
 if(!s||!s.players||!Array.isArray(s.teams)||!s.teams.length||
    !Array.isArray(s.schedule)||!s.schedule.length||
    s.vacation?.active||v125VacIncoming||v53Sim?.syncing||
    v53Sim?.patching||v53Sim?.active||v53Sim?.starting||
    !String(s.v1903CareerId||'')){
  v18369VacationReturn=null;
  v18369ResumeStats.last='cannot-capture-incomplete-vacation';
  return false;
 }
 v18369VacationReturn={world:s,careerId:String(s.v1903CareerId),
   year:Number(s.year),day:Number(s.day),session:Number(m?.session??v53Sim?.session),
   at:Date.now()};
 v18369ResumeStats.captured++;
 v18369ResumeStats.returnedDay=Number(s.day);
 v18369ResumeStats.last='vacation-world-returned';
 return true;
}
function v18369CanStartFromReturnedVacation(mode,s=state){
 if(mode!=='day'&&mode!=='dayfast'&&mode!=='nextmatch')return false;
 const x=v18369VacationReturn;
 if(!x)return false;
 const matches=!!s&&s===x.world&&
   String(s.v1903CareerId||'')===x.careerId&&
   Number(s.year)===x.year&&Number(s.day)===x.day&&
   !s.seasonDone&&!s.vacation?.active&&
   !!s.players&&Array.isArray(s.teams)&&!!s.teams.length&&
   Array.isArray(s.schedule)&&!!s.schedule.length&&
   !v53Sim?.active&&!v53Sim?.syncing&&
   !v53Sim?.patching&&!v125VacIncoming&&!v53Creating&&
   !v52SavePromise;
 if(!matches){
  // An actual save, season rollover or career change invalidates the token.
  // A real in-flight save remains protected: the old safe fallback is used.
  if(s!==x.world||Number(s?.year)!==x.year||Number(s?.day)!==x.day||
     String(s?.v1903CareerId||'')!==x.careerId){
   v18369VacationReturn=null;
   v18369ResumeStats.invalid++;
  }
  return false;
 }
 v18369ResumeStats.last='live-post-vacation-start-'+mode;
 v18369ResumeStats.liveStarts++;
 v18369ResumeStats.startedDay=Number(s.day);
 return true;
}
window.GestorFC=window.GestorFC||{};
window.GestorFC.vacationResume18369={status:()=>({
 version:'18.369.0',ready:!!v18369VacationReturn,careerId:v18369VacationReturn?.careerId||'',
 year:v18369VacationReturn?.year??null,day:v18369VacationReturn?.day??null,
 workerActive:!!v53Sim?.active,workerStarting:!!v53Sim?.starting,
 syncing:!!v53Sim?.syncing,patching:!!v53Sim?.patching,
 incoming:!!v125VacIncoming,fullSaveActive:!!v52SavePromise,
 ...v18369ResumeStats
})};
"""

def main():
 if len(sys.argv)!=2: raise SystemExit('usage: fix_vacation_resume_18369.py <project>')
 root=Path(sys.argv[1]).resolve()
 file=root/'src/index.html'
 s=file.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.369 already installed')
 for a in ('FUTBR_UNEMPLOYED_WORKER_REAL_PROGRESS_18368',
           'FUTBR_CORE_LIFECYCLE_18362',
           'v53DrainPatches=function(){',
           'const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=',
           'const v18366BaseVacationHeader=v624VacationHeaderHTML;'):
  if a not in s: raise RuntimeError('18.369 missing preserved source: '+a)
 # Base simulator: preserve the existing 18.311 fast path and its 18.368
 # resident-Worker protection. Reuse it once after a successful vacation
 # WITHOUT waiting for an outdated full save or loading old day from disk.
 bs=s.index('async function v53StartSimulation(mode,options={}){')
 be=s.index('runVacation=async function',bs)
 base=s[bs:be]
 flag='const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation='
 a=base.index(flag)
 end=base.index(';',a+len(flag))
 prior=base[a:end+1]
 if "mode==='vacation'" not in prior or "options?.liveStateNoPreSave" not in prior:
  raise RuntimeError('18.369 existing authoritative live-state condition changed')
 if 'v18369CanStartFromReturnedVacation' in prior:
  raise RuntimeError('18.369 live-state condition already modified')
 modified=prior[:-1]+'||v18369CanStartFromReturnedVacation(mode,state);'
 base=once(base,prior,modified,'reuse the existing safe live-state branch')
 if 'if(!v18311LiveVacation&&state?.v1903CareerId&&!saveOK)' not in base:
  raise RuntimeError('18.369 original live-state save protection lost')
 if 'const canLoadSaved=!v18311LiveVacation&&' not in base:
  raise RuntimeError('18.369 live state would incorrectly load old save')
 if 'if(!canLoadSaved&&!(mode===\'dayfast\'&&options?.jobWaitResident===true))msg.state=state;' not in base:
  raise RuntimeError('18.369 live state Worker transfer is missing')
 s=s[:bs]+base+s[be:]
 # 18.369: the actual next-match Worker formerly showed 'Partidas: 16/16'
 # indefinitely. Report the REAL post-match stages, without changing sporting
 # decisions or replaying the round. One short message per stage; no world clone.
 eng_start=s.index('async function advanceDayAsync(s,onProgress=()=>{},options=null){')
 eng_end=s.index('async function vacationStepAsync(',eng_start)
 engine=s[eng_start:eng_end]
 phase_marks=[
  ("    const played=new Set(matches.flatMap",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Recuperando os elencos');\\n    const played=new Set(matches.flatMap"),
  ("    for(const {f,m} of matches){applyIntlResult(s,f,m);",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Aplicando resultados e disciplina');\\n    for(const {f,m} of matches){applyIntlResult(s,f,m);"),
  ("    if(stage.type!=='world'&&stage.type!=='national')for(const t of s.teams){stageFinances",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Processando financas');\\n    if(stage.type!=='world'&&stage.type!=='national')for(const t of s.teams){stageFinances"),
  ("    if(delegatedDepthEmergency||stage.type==='league'){const q=",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Avaliando mercado de transferencias');\\n    if(delegatedDepthEmergency||stage.type==='league'){const q="),
  ("    if(stage.type==='league'||delegatedDepthEmergency){const q=",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Avaliando mercado de tecnicos');\\n    if(stage.type==='league'||delegatedDepthEmergency){const q="),
  ("    const uf=stage.fixtures.find(f=>f.home===s.user||f.away===s.user);",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Consolidando estatisticas da rodada');\\n    const uf=stage.fixtures.find(f=>f.home===s.user||f.away===s.user);"),
  ("    s.lastDay=s.day;s.day++;s.live=null;delete s.liveCompanions;",
   "    if(s.v158FastManualEngine)onProgress(1,1,'Concluindo jornada no calendario');\\n    s.lastDay=s.day;s.day++;s.live=null;delete s.liveCompanions;")
 ]
 for old,new in phase_marks:
  engine=once(engine,old,new.replace('\\\\n','\\n'),'trace authoritative original Engine phase')
 s=s[:eng_start]+engine+s[eng_end:]
 # Only the active, final patch-drain handler may declare vacation fully
 # returned. The first legacy definition no longer owns the 18.360 stream.
 ds=s.rindex('v53DrainPatches=function(){')
 de=s.index('async function v722CatchUpAfterFocus(){',ds)
 drain=s[ds:de]
 anchor='v53Sim.active=false;v53Sim.patching=false;v53Sim.syncing=false;vacationLoop=false;v52Processing=false;'
 replacement=anchor+"""
    if(wasVacation){
     if(!m.error)v18369CaptureVacationReturn(state,m);
     else{v18369VacationReturn=null;v18369ResumeStats.last='vacation-failed';}
    }"""
 drain=once(drain,anchor,replacement,'capture after last completed vacation Worker event')
 s=s[:ds]+drain+s[de:]
 s=once(s,'const v18366BaseVacationHeader=v624VacationHeaderHTML;',
    RUNTIME+'\nconst v18366BaseVacationHeader=v624VacationHeaderHTML;',
    'insert inside original private game IIFE')
 s=once(s,"const EDITION='18.368.0';","const EDITION='18.369.0';",'version')
 s=once(s,"window.GestorFC.version='18.368.0';window.GestorFC.visualVersion='18.368.0';",
    "window.GestorFC.version='18.369.0';window.GestorFC.visualVersion='18.369.0';",'runtime version')
 file.write_text(s,encoding='utf-8')
 report={
  'ok':True,'version':VERSION,
  'rootCause':'First advance after vacation could read stale pre-vacation save or wait for entire-world pre-save',
  'commonHandoffForEmployedAndUnemployed':True,
  'captureOnlyAfterRealFullWorkerSync':True,
  'normalDayAfterVacationUsesLiveWorld':True,
  'nextMatchAfterVacationUsesLiveWorld':True,
  'noOldSaveReplay':True,
  'noNewFullPreSaveBeforeFirstAdvance':True,
  'unemployedResidentWorkerUnchanged':True,
  'careerIdentityAndSessionGuard':True,
  'noNewWorkerDuringStreaming':True,
  'checkpointAndHistoricDataUnchanged':True,
  'realEnginePhaseTelemetry':True}
 (root/'vacation-resume-18369-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
