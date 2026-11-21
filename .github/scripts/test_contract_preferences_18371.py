from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path

def between(s,start,end,last=False):
    a=s.rindex(start) if last else s.index(start)
    return s[a:s.index(end,a)]

def main():
    root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
    assert 'FUTBR_CONTRACT_PREFERENCES_18371' in s
    engine=between(s,'  function managerSettings18371(s,','  function takeJob(s,id){')
    jobs=between(s,'  function takeJob(s,id){','  function startVacation(s,')
    dismiss=between(s,'  function dismissCoach(s,t,reason){','  function hireCoach(s,')
    settings=between(s,'function v622Settings(s=state){','function v622AllowedSpeedOptions(){')
    renew=between(s,'function v622BoardRenewals(s,force=false){','function v622AfterCompletedRound(s){')
    start=between(s,'async function v53StartSimulation(mode,options={}){','runVacation=async function()')
    drain=between(s,"   if(m.kind==='vac-sync-start'){","   if(m.kind==='vac-sync-collection-start'){",True)
    handler="if(m.op==='manager-settings-18371'){E.applyManagerSettings18371(world,m);return;}"
    assert s.count(handler)==1
    assert s.count('msg.managerSettings18371=v18371SettingsEnvelope(state);')==1
    assert s.count('E.applyManagerSettings18371(world,message.managerSettings18371);')==1
    assert s.count('window.GestorFC.contractPreferences18371.preserveRoot(manifest.root);')==1
    worker_start=between(s,'  // FUTBR_MANAGER_PREFERENCES_WORKER_18371:',
        "  const lowMemoryVacation=message.mode==='vacation'")
    simulate=between(s,' async function simulate(message){',' self.onmessage=event=>')
    assert simulate.index('await v93ApplyVacationCheckpoint(')<simulate.index('E.applyManagerSettings18371(world,message.managerSettings18371);')
    assert simulate.index('world.vacation={')<simulate.index('E.applyManagerSettings18371(world,message.managerSettings18371);')
    # The old root-transfer statement is retained as the exact red fixture. The
    # current source pump is executed below, rather than a second implementation.
    old="state=null;saved=null;v125VacIncoming={...(m.root||{}),v538CareerArchive:archive538||{},v555CareerArchive:archive555||{},scorerArchive:scorers||[],crestOverrides:overrides||{}};"
    if len(sys.argv)>2:
        baseline=Path(sys.argv[2]).read_text(encoding='utf-8')
        assert old in baseline
        assert 'msg.managerSettings18371=' not in baseline
    test=r'''
const assert=require('node:assert/strict');
const window={GestorFC:{}};
const document={hidden:false};
const V526_SPEEDS={'180':'normal','90':'fast'};
let state=null,saved=null,v53Worker=null,v53WorkerReady=null,v53WorkerFailed=false,
 v143PostRankPending=false,v143NationalRepairToken=0,v143NationalRepairRunning=false,
 v53Creating=false,v52SaveDirty=false,v52PendingState=null,v52NotifySave=false,
 v52SaveTimer=null,v52SavePromise=null,v52SaveWaiters=[],saveOK=true,
 v158ManualPrimePromise=null,v158ManualPrimeDay=-1,v158ManualPrimeYear=-1,
 vacationLoop=false,vacationDelay=10,v53Sim={active:false,starting:false,session:0},
 v81RankCacheHold=null,v92SeasonReviewSync=false,v125VacIncoming=null,
 v547SeasonIndexCache=new WeakMap(),v555CoachCache={},v555ShellState=null,
 v260ShellLockedState=null,v555MarketWarmJob=null,v555MarketWarmListJob=null,
 v555MarketWarmScheduled=false,v555DecorFrame=0,v52MarketIndex=null,v5RenderedView=null;
const messages=[];let originalVacationCalls=0,renewed=[],world=null;
const E={team:(s,id)=>s.teams?.find(t=>t.id===id),human:s=>s.teams?.find(t=>t.id===s.user),
 player:(s,id)=>s.players[id],overall:p=>p.ovr||60,payroll:()=>1000,
 salaryDemand58:()=>1000,news:()=>{},renew:(s,id,years)=>{
  const p=s.players[id];p.contract=years;E.human(s).balance-=100;
  renewed.push({club:s.user,id,years});},
 startVacation:(s,days,delegate)=>{originalVacationCalls++;s.vacation={active:true,remaining:days,delegateTransfers:delegate};}}
function v148EnsureNationalReady(){return false;}function v18369CanStartFromReturnedVacation(){return false;}
async function v52FlushSave(){}function v5CrestsOut(){}function v53PaintStatus(){}
function stopTimer(){}function render(){}function v18369ConsumeVacationReturn(){}
function v18369PaintOnly(f){return f();}function v18360SyncStart(){}
function v18310ReleaseOldVacationState(){state.players={};state.competitionStats={};state.allTimeStats={};}
function v18119BeginSeasonTransfer(){}
async function v53GetWorker(){v53Worker={postMessage(m){messages.push(structuredClone(m));
 if(m.op==='simulate'){v53Sim.active=false;v53Sim.finished.resolve(true);}}};return v53Worker;}
function team(s,id){return E.team(s,id);}function coach(s,t){return s.coaches[t.coachId];}
function human(s){return E.human(s);}function player(s,id){return E.player(s,id);}
function overall(p){return E.overall(p);}function payroll(s,t){return E.payroll(s,t);}
function salaryDemand58(p){return E.salaryDemand58(p);}function renew(s,id,years){return E.renew(s,id,years);}
function availableJobs(s){return s.teams.filter(t=>t.id!==s.user);}
function ledger(){}function clamp(x,a,b){return Math.max(a,Math.min(b,x));}
function v172FillCoachVacancy(s,t){t.coachId='replacement-'+t.id;s.coaches[t.coachId]={id:t.coachId,clubId:t.id,jobs:[],reputation:60};}
function coachMarket(){}function autoLineup(){}function news(){}
function startCoachJob(s,c,t){c.clubId=t.id;t.coachId=c.id;c.jobs.unshift({club:t.id});}
function fixture(id='career-A'){
 return {v1903CareerId:id,userCoachId:'me',user:'A',userEmployed:true,year:2029,day:7,
  players:{a:{id:'a',contract:1,age:24,wage:1000},b:{id:'b',contract:1,age:30,wage:1000},
   c:{id:'c',contract:1,age:31,wage:1000}},
  teams:[{id:'A',name:'Alpha',balance:100000,roster:['a'],coachId:'me'},
   {id:'B',name:'Beta',balance:100000,roster:['b'],coachId:null},
   {id:'C',name:'Gamma',balance:100000,roster:['c'],coachId:null}],
  coaches:{me:{id:'me',clubId:'A',jobs:[{club:'A'}],salary:100,reputation:70}},
  schedule:[],cupWinners:{},vacation:{active:false},manager:'Tester',news:[]};
}
'''
    test+=engine+'\nObject.assign(E,{managerSettings18371,applyManagerSettings18371,boardRenewals18371});\n'+settings+'\n'+renew+'\n'+jobs+'\n'+dismiss+'\n'+start
    test+='\nfunction applyActualIncoming(m){do{\n'+drain+'\n}while(false);return v125VacIncoming;}\n'
    test+='\nfunction applyWorkerStart(message){'+worker_start+'}\n'
    test+='\nfunction receiveSettings(m){'+handler+'}\n'
    test+='\nfunction originalIncoming(m){const archive538={},archive555={},scorers=[],overrides={};'+old+'return v125VacIncoming;}\n'
    test+='\nconst settingsScopeSource='+json.dumps(settings)+';\n'
    test+=r'''
(async()=>{
 state=fixture();state.v622Settings={renewals:'board',matchSpeed:'90',offerPopup:false};
 const oldRoot={v1903CareerId:'career-A',userCoachId:'me',user:'A',v622Settings:{renewals:'manual',matchSpeed:'180',offerPopup:true}};
 assert.equal(originalIncoming({root:structuredClone(oldRoot)}).v622Settings.renewals,'manual',
  'baseline replaces the manager choice with the stale worker root');

 state=fixture();state.v622Settings={renewals:'board',matchSpeed:'90',offerPopup:false};
 v18371CommitSettings();
 const actual=applyActualIncoming({kind:'vac-sync-start',root:structuredClone(oldRoot),syncSeq:1});
 assert.equal(state,null,'the old world must still be released');
 assert.deepEqual(actual.v622Settings,{renewals:'board',matchSpeed:'90',offerPopup:false,revision18371:1});

 state=fixture();state.v622Settings={renewals:'board',matchSpeed:'90',offerPopup:false};
 v18371CommitSettings();
 v53Sim={active:false,starting:false,session:0};messages.length=0;
 await v53StartSimulation('dayfast');
 const command=messages.find(m=>m.op==='simulate');
 assert.ok(command);assert.equal(command.loadSaved,true);assert.equal('state' in command,false);
 assert.deepEqual(command.managerSettings18371.settings,{renewals:'board',matchSpeed:'90',offerPopup:false,revision18371:1});
 assert.ok(JSON.stringify(command.managerSettings18371).length<250,'only a tiny settings envelope');
 let worker=fixture();worker.v622Settings={renewals:'manual',matchSpeed:'180',offerPopup:true};
 E.applyManagerSettings18371(worker,command.managerSettings18371);
 assert.equal(worker.v622Settings.renewals,'board');
 assert.equal(worker.v622Settings.offerPopup,false);
 // Same manager, three clubs, unemployed intervals and JSON save/reload.
 state=fixture();state.v622Settings={renewals:'board',matchSpeed:'90',offerPopup:false};
 v18371CommitSettings();const clubPrefs=[];
 for(const id of ['A','B','C']){
  if(state.user!==id)takeJob(state,id);
  assert.equal(v622Settings(state).renewals,'board');
  assert.equal(v622Settings(state).offerPopup,false);
  E.startVacation(state,1,false);
  assert.equal(state.players[id.toLowerCase()].contract,1,'UI start must not charge before loading worker state');
  const beforeBalance=E.human(state).balance;
  world=state;applyWorkerStart({mode:'vacation',managerSettings18371:v18371SettingsEnvelope(state)});
  assert.ok(state.players[id.toLowerCase()].contract>1,'new club renews before vacation');
  assert.equal(E.human(state).balance,beforeBalance-100,'one authoritative fee');
  applyWorkerStart({mode:'vacation',managerSettings18371:v18371SettingsEnvelope(state)});
  assert.equal(E.human(state).balance,beforeBalance-100,'no duplicate fee on resume');
  clubPrefs.push({club:id,renewals:v622Settings(state).renewals});
  state.vacation.active=false;
  dismissCoach(state,E.team(state,id),'crisis');
  assert.equal(state.userEmployed,false);assert.equal(v622Settings(state).renewals,'board');
  state=JSON.parse(JSON.stringify(state));
  assert.equal(v622Settings(state).renewals,'board');
 }
 assert.equal(originalVacationCalls,3);assert.equal(renewed.length,3);
 // An explicit manual decision wins, including after a save and a later club.
 v622Settings(state).renewals='manual';v18371CommitSettings(state);
 const latest=v18371SettingsEnvelope(state);state=JSON.parse(JSON.stringify(state));
 takeJob(state,'A');state.players.a.contract=1;
 E.startVacation(state,1,false);world=state;
 applyWorkerStart({mode:'vacation',managerSettings18371:v18371SettingsEnvelope(state)});
 assert.equal(state.players.a.contract,1);
 assert.equal(v622Settings(state).renewals,'manual');
 assert.equal(state.coaches.me.v18371CareerSettings.renewals,'manual');
 // An obsolete board message cannot overwrite a newer explicit manual choice.
 E.applyManagerSettings18371(state,command.managerSettings18371);
 assert.equal(v622Settings(state).renewals,'manual');
 // A tiny root is sufficient for checkpoint promotion without touching shards.
 const promoted={v1903CareerId:state.v1903CareerId,userCoachId:state.userCoachId,
  v622Settings:{renewals:'board',revision18371:0}};
 window.GestorFC.contractPreferences18371.preserveRoot(promoted);
 assert.equal(promoted.v622Settings.renewals,'manual');
 // Missing legacy root recovers from this manager's saved choice.
 delete state.v622Settings;assert.equal(v622Settings(state).renewals,'manual');
 // New careers are independent even if their coach ID has the same shape.
 const another=fixture('career-B');assert.equal(v622Settings(another).renewals,'manual');
 assert.equal(E.applyManagerSettings18371(another,command.managerSettings18371),false);
 assert.equal(E.applyManagerSettings18371(state,{...latest,coachId:'someone-else'}),false);
 assert.equal(v622Settings(another).renewals,'manual');
 // Original message dispatcher consumes updates while the worker is resident.
 world=worker;receiveSettings({op:'manager-settings-18371',...latest});
 assert.equal(worker.v622Settings.renewals,'manual');
 // Old vacation checkpoint restores root AND manager shard before the new
 // settings envelope is applied. The explicit manual decision still wins.
 world=fixture();Object.assign(world,structuredClone({v622Settings:{renewals:'board',
  offerPopup:true,matchSpeed:'180',revision18371:1},coaches:{me:{id:'me',clubId:'A',
   v18371CareerSettings:{renewals:'board',offerPopup:true,matchSpeed:'180',revision18371:1}}}}));
 const renewalsBefore=renewed.length;
 applyWorkerStart({mode:'vacation',managerSettings18371:latest});
 assert.equal(world.v622Settings.renewals,'manual');
 assert.equal(world.v622Settings.offerPopup,false);assert.equal(renewed.length,renewalsBefore);
 // A separate script cannot see the private UI helper/state. Only the public
 // tiny-root bridge is available, matching the actual sharded-save script.
 const vm=require('node:vm'),isolated={window:{GestorFC:{}},Engine:E,fixture};
 vm.createContext(isolated);
 vm.runInContext("(()=>{let state=fixture('private-career');const E=Engine;"+
  "const V526_SPEEDS={'180':'normal','90':'fast'};"+
  "state.v622Settings={renewals:'board',matchSpeed:'90',offerPopup:false,revision18371:7};"+
  settingsScopeSource+"})();",isolated);
 assert.equal(typeof isolated.state,'undefined');
 assert.equal(typeof isolated.v18371PreserveSettingsRoot,'undefined');
 const scoped=vm.runInContext("(()=>{const manifest={root:{v1903CareerId:'private-career',"+
  "userCoachId:'me',v622Settings:{renewals:'manual'}}};"+
  "window.GestorFC.contractPreferences18371.preserveRoot(manifest.root);return JSON.stringify(manifest.root.v622Settings);})();",isolated);
 assert.equal(JSON.parse(scoped).renewals,'board');
 // National management does not renew contracts at the previous club.
 state=fixture();state.v640National={userTeam:'BRA'};
 state.v622Settings={renewals:'board',matchSpeed:'180',offerPopup:true};
 const before=renewed.length;E.startVacation(state,1,false);world=state;
 applyWorkerStart({mode:'vacation',managerSettings18371:v18371SettingsEnvelope(state)});
 assert.equal(renewed.length,before);
 console.log(JSON.stringify({ok:true,version:'18.371.0',baselineStaleRootLosesBoard:true,
  sourceSimulationMessageExecuted:true,sourceFinalDrainExecuted:true,
  sourceTakeJobAndDismissalExecuted:true,clubs:clubPrefs,
  serializedReloadPreservesSettings:true,manualChoiceWins:true,
  offerPopupFalsePreserved:true,oldMessageCannotRevertManual:true,
  otherCareerAndManagerRejected:true,preVacationRenewalsAllClubs:true,
  authoritativeWorkerRenewsOnce:true,uiDoesNotMutateBeforeSavedWorldLoad:true,
  staleCheckpointCannotOverrideManual:true,separateScriptBridgeExecuted:true,
  nationalJobDoesNotRenewOldClub:true,checkpointRootPreserved:true,
  smallEnvelopeBytes:JSON.stringify(command.managerSettings18371).length,
  noFullWorldCloneAdded:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
'''
    with tempfile.TemporaryDirectory() as d:
        f=Path(d)/'contracts.js';f.write_text(test,encoding='utf-8')
        p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=45)
        if p.returncode:raise RuntimeError(p.stderr[-6000:]+'\n'+p.stdout[-2000:])
        report=json.loads(p.stdout.strip().splitlines()[-1])
    (root/'contract-preferences-18371-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
