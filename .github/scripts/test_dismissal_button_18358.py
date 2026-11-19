from __future__ import annotations
import json,subprocess,sys,tempfile
from pathlib import Path

def segment(src,a,b):
    i=src.index(a);j=src.index(b,i+len(a))
    return src[i:j]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_dismissal_button_18358.py <project>')
    root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
    assert s.count('/* FUTBR_DISMISSAL_BUTTON_RECOVERY_18358')==1
    assert "window.GestorFC.version='18.358.0';window.GestorFC.visualVersion='18.358.0';" in s
    assert 'v18358PromotionSettled=true;' in segment(s,'const baseStart171=v53StartSimulation;','G.v171={version:V')
    assert 'function v18357NoPendingWorldTransfer(){\n if(v18358HandoffReady())return true;' in s
    assert 'if(v18358HandoffReady())v18358CompleteOldOverlay();' in s
    assert 'if(v18358SafeJobButtons())return true;' in s
    assert 'if((v18358SafeJobButtons()||v18358SeasonEndReady())&&!v89JobWait.active)return false;' in s
    assert "if(state&&!state.userEmployed&&!v89HasNationalJob()){" in s
    assert 'if(state.seasonDone){\n  try{await v53Prepare(\'next\');}' in s
    assert "const disabled='';" in s
    helper=segment(s,'/* FUTBR_DISMISSAL_BUTTON_RECOVERY_18358','/* FUTBR_JOBWAIT_SEASON_RECOVERY_18356')
    job=segment(s,'async function v89RunJobWait(){','const v89BaseCareerPage=careerPage;')
    assert "await v53StartSimulation('dayfast');" in job
    assert "v18356ReconcileRollover();" in job

    pre=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{v171:{storageAudit:async()=>audit},
 v172:{_finishJobWait:()=>{}}}};
let state,audit,view='dashboard',toasts=[],renders=0,overlays=0,modals=0,saved=0,simDays=0;
let v53Sim={active:false,starting:false,syncing:false,patching:false,finished:null,mode:'vacation'};
let v18112Dismissal={pending:false,ready:false,year:0,day:0,careerId:'',notified:false};
let v125VacIncoming=null,v53Creating=false,v52Processing=false,v18326AdvanceBusy=false;
let v18119SeasonTransfer={active:false},v53RPC=new Map();
let v89JobWait={active:false,stop:false,days:0};
let v168DeferredRolloverSave=false,v18121NewSeasonPreparation=false;
let v18119SeasonTransferStatus=null,v18119SeasonTransferError=null;
const document={querySelector(){return null},querySelectorAll(){return []}};
function v18119CompleteSeasonTransfer(){overlays++;v18119SeasonTransfer.active=false}
function v18356ReconcileRollover(){return false}
function v53PaintStatus(){}
function toast(msg){toasts.push(msg)}
function closeModal(){}
function render(){renders++}
function persist(){saved++;return Promise.resolve()}
function v636PendingCoachOffers(s){return s.offers||[]}
function v636CoachOfferModal(){modals++}
function v89HasNationalJob(){return !!state.v640National?.userTeam}
function v89PaintJobWait(){}
let v86RankCache={dirty:false};
function v93ScheduleCoachDecisionSave(){saved++;}
function fresh(opts={}){
 state={year:2030,day:67,v1903CareerId:'career-A',userEmployed:false,
  players:{p:{id:'p'}},teams:[{id:'t'}],schedule:[{type:'league'}],
  seasonDone:false,live:null,v640National:null,
  vacation:{active:false,paused:true},offers:[],...opts};
 audit={year:2030,day:67,careerId:'career-A',userEmployed:false};
 v53Sim={active:false,starting:false,syncing:true,patching:true,finished:null,mode:'vacation'};
 v18112Dismissal={pending:true,ready:false,year:2030,day:67,careerId:'career-A',notified:false};
 v125VacIncoming=null;v53Creating=false;v52Processing=true;
 v18326AdvanceBusy=false;v18119SeasonTransfer={active:true};
 v53RPC=new Map([['stale',{}]]);
 v89JobWait={active:false,stop:false,days:0};
 v18357AwaitingPromotion=true;v18358PromotionSettled=false;
 v18358RecoveryDone=false;v18357LiveFallback=null;
}
async function v53Prepare(op){
 assert.equal(op,'next');
 state.year++;state.day=0;state.seasonDone=false;
}
async function v53StartSimulation(mode){
 assert.equal(mode,'dayfast');
 simDays++;state.day++;state.offers.push({teamId:'t'});
 return state;
}
"""
    tests=r"""
(async()=>{
 // Main real-world defect: stream/Worker ended but ancillary indicators still
 // say syncing, processing, active overlay or an unrelated RPC.
 fresh();
 assert.equal(v18357NoPendingWorldTransfer(),false,'No bypass before promotion');
 v18358PromotionSettled=true;
 assert.equal(v18358HandoffReady(),true);
 assert.equal(await v18357FinalizeDismissal(),true);
 assert.equal(v18112Dismissal.pending,false);
 assert.equal(v53Sim.syncing,false);
 assert.equal(v53Sim.patching,false);
 assert.equal(v18119SeasonTransfer.active,false);
 assert.equal(overlays,1);
 assert.equal(v18358RecoveryDone,true);
 assert.equal(v18358SafeJobButtons(),true);
 assert.equal(v18358LastBlocker,'none');
 assert.equal(toasts.length,1,'Dismissal notification only once');

 // A genuine running Worker, missing history/players, wrong career, and a
 // promotion still in flight must all remain unavailable.
 fresh();v18358PromotionSettled=true;
 v53Sim.active=true;v53Sim.finished={resolve(){}};
 assert.equal(v18358HandoffReady(),false);
 assert.equal(await v18357FinalizeDismissal(),false);
 assert.equal(v18112Dismissal.pending,true);
 if(v18357Retry!==null){clearTimeout(v18357Retry);v18357Retry=null}
 v53Sim.active=false;v53Sim.finished=null;
 state.players=null;
 assert.equal(v18358HandoffReady(),false);
 state.players={p:{}};
 v18112Dismissal.careerId='other-career';
 assert.equal(v18358HandoffReady(),false);
 v18112Dismissal.careerId='career-A';
 v18358PromotionSettled=false;
 assert.equal(v18358HandoffReady(),false);

 // Failed checkpoint does not force a full historic rewrite. The next
 // day must be sourced from the current UI world by the 18.357 fallback.
 fresh();audit={year:2029,day:67,careerId:'career-A',userEmployed:true};
 v18358PromotionSettled=true;
 assert.equal(await v18357FinalizeDismissal(),true);
 assert.deepEqual(v18357LiveFallback,{year:2030,day:67,careerId:'career-A'});
 assert.equal(v18358SafeJobButtons(),true);

 // At the end of a season, the same button starts next season and then
 // advances with Turbo until a proposal arrives. It cannot remain disabled.
 fresh({seasonDone:true,day:163});audit={year:2030,day:163,careerId:'career-A',userEmployed:false};
 v18358PromotionSettled=true;
 assert.equal(await v18357FinalizeDismissal(),true);
 const year=state.year;
 await v89RunJobWait();
 assert.equal(state.year,year+1);
 assert.equal(simDays,1);
 assert.ok(modals>=1,'Received proposal opens the dialog');
 assert.equal(v89JobWait.active,false);
 // Also work when a user has been unemployed at season end without a
 // just-completed vacation: the old 18.334 guard blocked this forever.
 fresh({seasonDone:true,day:163});
 v18112Dismissal.pending=false;v53Sim.syncing=false;v53Sim.patching=false;
 v18358RecoveryDone=false;
 assert.equal(v18358SeasonEndReady(),true);
 await v89RunJobWait();
 assert.equal(state.year,2031);
 assert.equal(simDays,2);
 console.log(JSON.stringify({ok:true,version:'18.358.0',
  alreadyFinishedVacationUnlocksJobButton:true,
  staleOverlayAndSaverDoNotBlock:true,
  inFlightWorkerProtected:true,
  incompletePlayerWorldProtected:true,
  careerIdentityProtected:true,
  noReleaseBeforeCheckpointSettles:true,
  failedCheckpointUsesLiveMemory:true,
  seasonEndAdvancesToOffers:true,seasonEndWithoutDismissalRecoveryWorks:true,
  preservesTurboSimulation:true}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
    with tempfile.TemporaryDirectory() as td:
        f=Path(td)/'test-18358.cjs'
        f.write_text(pre+'\n'+helper+'\n'+job+'\n'+tests,encoding='utf-8')
        c=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=25)
        if c.returncode:raise RuntimeError('18.358 javascript invalid: '+c.stderr[-5000:])
        p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=35)
        if p.returncode:raise RuntimeError('18.358 runtime test failed: '+(p.stderr or p.stdout)[-7000:])
        report=json.loads(p.stdout.strip().splitlines()[-1])
    (root/'dismissal-button-18358-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
