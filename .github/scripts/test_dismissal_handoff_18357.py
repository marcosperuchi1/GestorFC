from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path

def section(src,start,end):
    a=src.index(start);b=src.index(end,a+len(start))
    return src[a:b]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_dismissal_handoff_18357.py <project>')
    root=Path(sys.argv[1])
    src=(root/'src/index.html').read_text(encoding='utf-8')
    assert 'FUTBR_DISMISSAL_HANDOFF_18357' in src
    assert "window.GestorFC.version='18.357.0';window.GestorFC.visualVersion='18.357.0';" in src
    assert src.count('/* FUTBR_DISMISSAL_HANDOFF_18357')==1
    assert 'function v18334SafeToVerify(){\n return !v18357AwaitingPromotion&&' in src
    assert "if(v18357AwaitingPromotion)return false;" in src
    helper=section(src,'/* FUTBR_DISMISSAL_HANDOFF_18357','/* FUTBR_JOBWAIT_SEASON_RECOVERY_18356')
    inner=section(src,'const v18112BaseSimulation=v53StartSimulation;','const v18112BaseChrome=v555UpdateChrome;')
    outer=section(src,'const baseStart171=v53StartSimulation;','G.v171={version:V')
    if 'await persist(false);await v52FlushSave();' in inner:
        p=inner.index('await persist(false);await v52FlushSave();')
        raise RuntimeError('Legacy forced save still present: '+inner[max(0,p-270):p+400])
    assert 'v18357AwaitingPromotion=true' in inner
    assert outer.index('await promoteVacationCheckpoint()')<outer.index('await v18357FinalizeDismissal()')
    assert 'liveStateNoPreSave:true' in outer
    assert 'careerId:String(m?.root?.v1903CareerId' in src
    assert 'userEmployed:m?.root?.userEmployed' in src
    assert 'function v18357NoPendingWorldTransfer()' in helper
    pre=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{v171:{storageAudit:async()=>{audits++;return audit;}}}};
const performance={now:()=>100};const V='17.1';
let state, audit,saveStamp='',saveOK=true,view='dashboard';
let v53Sim={active:false,starting:false,syncing:false,patching:false,finished:null,pause:false};
let v18112Dismissal={pending:false,ready:false,year:0,day:0,careerId:'',notified:false};
let v125VacIncoming=null,v53Creating=false,v52Processing=false,v18326AdvanceBusy=false;
let v18119SeasonTransfer={active:false},v53RPC=new Map(),v89JobWait={active:false};
let v93VacCheckpointValid=true;
let audits=0,promotions=0,rebuilds=0,renders=0,toasts=0,started=0,optionsSeen=[];
let promoteShouldFail=false;
function fresh(year=2030){
 state={year,day:87,v1903CareerId:'career-A',userEmployed:true,v640National:null,
  vacation:{active:true,paused:false,remaining:8,untilSeason:true}};
 audit={year:year-1,day:86,careerId:'career-A',userEmployed:true};
 v18112Dismissal={pending:false,ready:false,year,day:0,careerId:'',notified:false};
 v53Sim={active:false,starting:false,syncing:false,patching:false,finished:null,pause:false};
 v125VacIncoming=null;v53Creating=false;v52Processing=false;v18326AdvanceBusy=false;
 v18119SeasonTransfer.active=false;v53RPC.clear();v93VacCheckpointValid=true;
 promoteShouldFail=false;
}
function toast(msg){toasts++;}function closeModal(){}
function render(){renders++;}function v53PaintStatus(){}function updateSaveStatus(){}
async function persist(){rebuilds++;throw Error('An extra world-wide save must NEVER run')}
async function v52FlushSave(){rebuilds++;throw Error('No legacy full save')}
async function promoteVacationCheckpoint(){
 promotions++;
 assert.equal(v18357AwaitingPromotion,true,'18.112 must defer handoff until 17.1 checkpoint');
 assert.equal(v18112Dismissal.pending,true,'button must remain protected until checkpoint');
 if(promoteShouldFail)throw Error('synthetic checkpoint unavailable');
 audit={year:state.year,day:state.day,careerId:state.v1903CareerId,userEmployed:false};
}
let v53StartSimulation=async(mode,opts)=>{
 started++;optionsSeen.push({mode,opts:opts||{}});
 if(mode==='vacation'){
  state.userEmployed=false;
  state.vacation.active=false;
  v18112Dismissal.pending=true;
  v18112Dismissal.year=state.year;v18112Dismissal.day=state.day;
  v18112Dismissal.careerId=state.v1903CareerId;
  v53Sim.active=false;v53Sim.syncing=false;v53Sim.finished=null;
 }
 return state;
};
"""
    tests=r"""
(async()=>{
 fresh();
 const pre=persist;
 await v53StartSimulation('vacation');
 assert.equal(promotions,1,'One and only one Worker checkpoint promotion');
 assert.equal(rebuilds,0,'No second full UI save');
 assert.equal(audits,1,'One lightweight manifest audit after promotion');
 assert.equal(v18112Dismissal.pending,false);
 assert.equal(v18112Dismissal.ready,true);
 assert.equal(v18357AwaitingPromotion,false);
 assert.equal(v18357LastStatus,'checkpoint-verified');
 assert.equal(v18357LiveFallback,null,'Verified checkpoint uses normal subsequent Worker');
 assert.equal(view,'career');
 assert.equal(toasts,1,'No repeated dismissal notifications');
 const ok=await v53StartSimulation('dayfast');
 assert.equal(optionsSeen.at(-1).opts.liveStateNoPreSave,undefined,'Normal dayfast unchanged when checkpoint exists');
 // Missing checkpoint: allow first unemployed Worker day to use the
 // returned live world. Never reload the former club/season snapshot.
 fresh(2032);promoteShouldFail=true;
 await v53StartSimulation('vacation');
 assert.equal(v18357LastStatus,'live-state-fallback');
 assert.equal(v18357LiveFallback.year,2032);
 assert.equal(v18357LiveFallback.day,87);
 assert.equal(v18112Dismissal.pending,false);
 assert.equal(rebuilds,0,'No full-world fallback even after failed checkpoint');
 await v53StartSimulation('dayfast');
 assert.equal(optionsSeen.at(-1).opts.liveStateNoPreSave,true);
 assert.equal(v18357LiveFallback,null,'First successful Worker commit clears fallback');
 // In-flight Worker cannot be bypassed by UI recovery.
 fresh(2033);state.userEmployed=false;state.vacation.active=false;
 v18112Dismissal.pending=true;v18112Dismissal.year=2033;
 v18112Dismissal.careerId='career-A';v18357AwaitingPromotion=true;
 v53Sim.active=true;v53Sim.finished={resolve(){}};
 assert.equal(await v18357FinalizeDismissal(),false);
 assert.equal(v18112Dismissal.pending,true);
 if(v18357Retry!==null){clearTimeout(v18357Retry);v18357Retry=null;}
 v53Sim.active=false;v53Sim.finished=null;
 // Mismatch identity must NOT unlock a different user's career.
 v18112Dismissal.careerId='another-career';
 assert.equal(await v18357FinalizeDismissal(),false);
 assert.equal(v18112Dismissal.pending,true);
 // National manager can never fall through into unemployment.
 v18112Dismissal.careerId='career-A';
 state.v640National={userTeam:'BRA'};
 assert.equal(await v18357FinalizeDismissal(),false);
 assert.equal(v18112Dismissal.pending,true);
 v18357AwaitingPromotion=false;
 console.log(JSON.stringify({ok:true,version:'18.357.0',
  endOfVacationCheckpointBeforeJobUnlock:true,
  neverSavesFullWorldTwice:true,careerYearDayEmploymentAudited:true,
  fallbackUsesLiveStateSafely:true,previousSaveNotReplayed:true,
  inFlightWorkerProtected:true,otherCareerProtected:true,nationalManagerProtected:true,
  oneAuditOnePromotion:true}));
})().catch(e=>{console.error(e);process.exit(1);});
"""
    with tempfile.TemporaryDirectory() as td:
        file=Path(td)/'dismissal-18357.cjs'
        file.write_text(pre+'\n'+helper+'\n'+inner+'\n'+outer+'\n'+tests,encoding='utf-8')
        c=subprocess.run(['node','--check',str(file)],capture_output=True,text=True,timeout=20)
        if c.returncode:raise RuntimeError('18.357 generated JS syntax: '+c.stderr[-5000:])
        p=subprocess.run(['node',str(file)],capture_output=True,text=True,timeout=30)
        if p.returncode:raise RuntimeError('18.357 Worker/dismissal runtime regression: '+(p.stderr or p.stdout)[-5000:])
        result=json.loads(p.stdout.strip().splitlines()[-1])
    (root/'dismissal-handoff-18357-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
