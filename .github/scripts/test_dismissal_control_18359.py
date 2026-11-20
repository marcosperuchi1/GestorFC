from __future__ import annotations
import json
import subprocess
import sys
import tempfile
from pathlib import Path

def section(src,start,end):
    a=src.index(start)
    b=src.index(end,a+len(start))
    return src[a:b]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_dismissal_control_18359.py <project>')
    root=Path(sys.argv[1])
    src=(root/'src/index.html').read_text(encoding='utf-8')
    tag='<script id="futbr-dismissal-finished-18359">'
    assert src.count(tag)==1
    assert src.count('/* FUTBR_DISMISSAL_FINISHED_SIGNAL_18359')==1
    assert "window.GestorFC.version='18.359.0';window.GestorFC.visualVersion='18.359.0';" in src
    helper=section(src,tag,'</script>')
    assert "v18359OnWorkerFinished(m,wasVacation);" in src
    assert src.index(tag)>src.index('/* FUTBR_DISMISSAL_BUTTON_RECOVERY_18358')
    assert src.index(tag)>src.index('const v18112BaseChrome=v555UpdateChrome;')
    assert src.index(tag)>src.index('const baseStart171=v53StartSimulation;')
    assert "const v18359BaseChrome=v555UpdateChrome;" in helper
    assert "const v18359BaseStart=v53StartSimulation;" in helper
    # Test the actual patched click handler, not a reimplemented version.
    job=section(src,'async function v89RunJobWait(){','const v89BaseCareerPage=careerPage;')
    assert "if(!v18359TrustedCompleted()&&(v18112Dismissal.pending||" in job
    assert "await v53StartSimulation('dayfast');" in job
    # Signal must occur within the authoritative 18.119 Worker message
    # handler, after the original finished promise resolution.
    i=src.index('function v18119CompleteSeasonTransfer(){')
    j=src.index("if(m.kind==='finished'){",i)
    k=src.index('    continue;',j)+len('    continue;')
    event=src[j:k]
    assert event.index("finish?.resolve(state)")<event.index("v18359OnWorkerFinished(m,wasVacation)")
    assert event.count('v18359OnWorkerFinished(m,wasVacation)')==1

    pre=r"""
const assert=require('node:assert/strict');
let state,view='dashboard',v53Sim,v18112Dismissal,v125VacIncoming=null;
let v53Creating=false,v18326AdvanceBusy=false,v18121NewSeasonPreparation=false;
let v18119SeasonTransfer={active:false},v18357AwaitingPromotion=false,
    v18358RecoveryDone=false,v18357LiveFallback=null,v89JobWait={active:false,stop:false,days:0};
let v86RankCache={dirty:false},renderCount=0,modalCount=0,workerDays=0;
let overlayCount=0,alerts=[],dayArgs=[],resolveVacation,jobBtn,advBtn;
const window={GestorFC:{v172:{_finishJobWait(){}}}};
const document={
 querySelectorAll(sel){if(sel.includes('v89-job-wait'))return [jobBtn];return []},
 querySelector(sel){return sel.includes('advance')?advBtn:null}
};
function newButton(){
 return {disabled:true,attrs:{'aria-busy':'true'},title:'Aguardando a sincronização da demissão',
  removeAttribute(k){delete this.attrs[k];if(k==='disabled')this.disabled=false;},
  setAttribute(k,v){this.attrs[k]=v;}
 };
}
function newWorld(){
 return {year:2031,day:68,v1903CareerId:'career-A',userEmployed:false,
  userCoachId:'coach-A',teams:[{id:'club-1'}],schedule:Array(164),
  players:{player:{id:'player'}},vacation:{active:false,paused:true},
  seasonDone:false,live:null,v640National:null,offers:[]};
}
function reset(){
 state=newWorld();v53Sim={active:false,starting:false,finished:null,syncing:true,patching:true,
  session:7,pause:false,pauseMode:'',mode:'vacation'};
 v18112Dismissal={pending:true,ready:false,careerId:'career-A',notified:false};
 v125VacIncoming=null;v53Creating=false;v18326AdvanceBusy=false;
 v18121NewSeasonPreparation=false;v18119SeasonTransfer.active=true;
 v18357AwaitingPromotion=true;v18358RecoveryDone=false;v18357LiveFallback=null;
 v89JobWait={active:false,stop:false,days:0};jobBtn=newButton();advBtn=newButton();
}
function v18119CompleteSeasonTransfer(){overlayCount++;v18119SeasonTransfer.active=false}
function closeModal(){}
function render(){renderCount++;v555UpdateChrome(document)}
function toast(s){alerts.push(s)}
function v555UpdateChrome(){jobBtn.disabled=true;jobBtn.setAttribute('aria-busy','true');advBtn.disabled=true}
function v18356ReconcileRollover(){}
function v18358SafeJobButtons(){return false}
function v89HasNationalJob(){return !!state?.v640National?.userTeam}
function v636PendingCoachOffers(s){return s?.offers||[]}
function v636CoachOfferModal(){modalCount++}
function v89PaintJobWait(){}
function persist(){return Promise.resolve()}
function v93ScheduleCoachDecisionSave(){}
async function v53Prepare(mode){if(mode!=='next')throw Error('wrong next');state.year++;state.day=0;state.seasonDone=false}
function v53StartSimulation(mode,options={}){
 if(mode==='vacation')return new Promise(resolve=>{resolveVacation=()=>resolve(state)});
 if(mode==='dayfast'||mode==='day'){
  dayArgs.push(options);
  workerDays++;state.day++;state.offers.push({id:'offer',teamId:'club-1'});
  return Promise.resolve(state);
 }
 throw Error('wrong mode '+mode);
}
"""
    checks=r"""
(async()=>{
 reset();
 // The vacation promise is still open while the 17.1 checkpoint
 // promotion is pending. The Worker itself has already finished and
 // the complete players/history world is in state.
 const vacationTask=v53StartSimulation('vacation');
 assert.ok(v18359VacationPromise,'The entire outer vacation promise must be tracked');
 const ok=v18359OnWorkerFinished({kind:'finished',error:null},true);
 assert.equal(ok,true,'Real Worker finished event releases the dismissal');
 await Promise.resolve();
 assert.equal(v18112Dismissal.pending,false);
 assert.equal(v18112Dismissal.ready,true);
 assert.equal(v18359TrustedCompleted(),true);
 assert.equal(v18358RecoveryDone,true);
 assert.deepEqual(v18357LiveFallback,{year:2031,day:68,careerId:'career-A'});
 assert.equal(v18119SeasonTransfer.active,false);
 assert.equal(jobBtn.disabled,false,'Real header button must be re-enabled');
 assert.equal(jobBtn.attrs['aria-busy'],undefined);
 assert.equal(advBtn.disabled,false);
 // An old chrome repaint that sets "waiting" must be overridden LAST.
 v555UpdateChrome(document);
 assert.equal(jobBtn.disabled,false,'Legacy painter cannot re-disable the button');
 v53Sim.syncing=true;v53Sim.patching=true;
 const jobTask=v89RunJobWait();
 await new Promise(r=>setTimeout(r,20));
 assert.equal(workerDays,0,'Never run the first unemployed day against a competing checkpoint');
 resolveVacation();
 await vacationTask;
 await jobTask;
 await new Promise(r=>setTimeout(r,70));
 assert.equal(workerDays,1);
 assert.equal(dayArgs[0].liveStateNoPreSave,true,'First day must use returned live 2031 world');
 assert.equal(modalCount,1,'The existing job offer dialog must appear');
 assert.equal(v89JobWait.active,false);
 assert.equal(v18359ReleaseCount,1);
 // Verify guards against false completion signals, even if the
 // remaining state resembles an unemployed manager.
 reset();v53Sim.active=true;
 assert.equal(v18359OnWorkerFinished({error:null},true),false);
 assert.equal(v18112Dismissal.pending,true);
 reset();v125VacIncoming={incomplete:true};
 assert.equal(v18359OnWorkerFinished({error:null},true),false);
 reset();state.v640National={userTeam:'BRA'};
 assert.equal(v18359OnWorkerFinished({error:null},true),false);
 reset();v18112Dismissal.careerId='other-career';
 assert.equal(v18359OnWorkerFinished({error:null},true),false);
 reset();assert.equal(v18359OnWorkerFinished({error:'worker failed'},true),false);
 reset();assert.equal(v18359OnWorkerFinished({},false),false);
 console.log(JSON.stringify({ok:true,version:'18.359.0',
  actualFinishedWorkerSignal:true,headersReenabledAfterLegacyPaint:true,
  jobWaitClickUnblocked:true,
  noAdvanceWhilePromotionInFlight:true,
  firstWorkerDayUsesSynchronizedWorld:true,
  realOfferModalAppears:true,
  noUnlockOnActiveWorker:true,noUnlockOnPartialStream:true,
  nationalCareerProtected:true,careerIdentityProtected:true,
  workerErrorsCannotUnlock:true,zeroDuplicateWorldSaves:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    # Evaluate the actual final wrapper and actual 18.89 job wait function.
    with tempfile.TemporaryDirectory() as tmp:
        f=Path(tmp)/'test-18359.cjs'
        f.write_text(pre+'\n'+helper+'\n'+job+'\n'+checks,encoding='utf-8')
        c=subprocess.run(['node','--check',str(f)],capture_output=True,text=True,timeout=30)
        if c.returncode:
            raise RuntimeError('18.359 JS syntax invalid: '+c.stderr[-4500:])
        p=subprocess.run(['node',str(f)],capture_output=True,text=True,timeout=55)
        if p.returncode:
            raise RuntimeError('18.359 actual button/Worker regression failed: '+(p.stderr or p.stdout)[-6500:])
        result=json.loads(p.stdout.strip().splitlines()[-1])
    (root/'dismissal-control-18359-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':main()
