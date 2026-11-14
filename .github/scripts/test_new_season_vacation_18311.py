from __future__ import annotations
import json, sys, subprocess
from pathlib import Path

def fail(msg):
    raise RuntimeError(msg)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: test_new_season_vacation_18311.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    html=(root/'src'/'index.html').read_text(encoding='utf-8')

    required=[
        'v18311VacationCheckpointFix',
        "version:'18.325'",
        'blockingFullPreSave:false',
        'workerCheckpoint:true',
        'previousSavePreserved:true',
        'liveStateNoPreSave:true',
        'vacationCheckpoint:true',
        "const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=mode==='vacation'&&!!options?.liveStateNoPreSave;",
        "if(!v18311LiveVacation&&state?.v1903CareerId&&!saveOK){",
        "const canLoadSaved=!v18311LiveVacation&&!!saveOK&&(mode==='day'||mode==='dayfast'||mode==='nationaljump'||mode==='nextmatch'||mode==='vacation');",
    ]
    for marker in required:
        if marker not in html:
            fail('marcador ausente: '+marker[:120])

    bs=html.find('async function v53StartSimulation(mode,options={}){')
    be=html.find('\nrunVacation=async function',bs)
    if bs<0 or be<0:
        fail('funcao base nao localizada')
    base=html[bs:be]
    live=base.find('}else if(v18311LiveVacation){')
    blocking=base.find('}else{await v52FlushSave();if(v52SavePromise)await v52SavePromise;}')
    if live<0 or blocking<0 or live>blocking:
        fail('live-state nao precede o save bloqueante')
    live_block=base[live:blocking]
    if 'await v52FlushSave()' in live_block:
        fail('live-state ainda aguarda save completo')
    if "if(!canLoadSaved)msg.state=state;" not in base:
        fail('Worker nao recebe o estado vivo quando loadSaved=false')

    ws=html.find('const v168BaseStartSimulation=v53StartSimulation;')
    we=html.find('// Autoridade final da virada:',ws)
    if ws<0 or we<0:
        fail('wrapper 18.181 nao localizado')
    wrapper=html[ws:we]
    fs=wrapper.find("if(v168DeferredRolloverSave&&state&&mode==='vacation'){")
    legacy=wrapper.find('if(v168DeferredRolloverSave&&state){',fs+1)
    if fs<0 or legacy<0 or fs>legacy:
        fail('fast path de ferias nao precede fallback legado')
    fast=wrapper[fs:legacy]
    if 'await v52FlushSave()' in fast:
        fail('fast path ainda bloqueia no save completo')
    if 'return await v168BaseStartSimulation(mode,options)' not in fast:
        fail('fast path nao inicia o Worker')
    if "v52PendingState=null;v52SaveDirty=false" not in fast:
        fail('pedido de save diferido nao e cancelado antes do Worker')
    if "v168DeferredRolloverSave=false" not in fast:
        fail('flag de rollover nao e liberada')
    if "v168DeferredRolloverSave=true" not in fast:
        fail('fallback de recuperacao nao restaura flag em caso de erro')


    # Regression: initial 2027 vacation must start despite a pending full save.
    # The preceding legacy path called v52FlushSave and blocked indefinitely.
    harness=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}};
let state={year:2027,day:1,user:'flamengo'},v168DeferredRolloverSave=true;
let v53Sim={active:false,starting:false,mode:'',progress:''},v53Creating=false;
let v52SavePromise=new Promise(()=>{}),v52SaveDirty=true,v52PendingState=state;
let v52SaveTimer=1,v52NotifySave=false,v52SaveWaiters=[],saveOK=true;
let flushed=0,started=0,opts=null;
function v148EnsureNationalReady(){return false}
function v53PaintStatus(){}
async function v52FlushSave(){flushed++;throw Error('blocking full save must not execute')}
let v53StartSimulation=async(mode,options)=>{
  started++;opts=options;
  assert.equal(mode,'vacation');
  return 'worker-started';
};
""" + wrapper + r"""
(async()=>{
  const result=await Promise.race([
    v53StartSimulation('vacation'),
    new Promise((_,reject)=>setTimeout(()=>reject(new Error('blocked on full save')),3000))
  ]);
  assert.equal(result,'worker-started');
  assert.equal(flushed,0);
  assert.equal(started,1);
  assert.equal(opts.liveStateNoPreSave,true);
  assert.equal(opts.vacationCheckpoint,true);
  assert.equal(v168DeferredRolloverSave,false);
  assert.equal(window.GestorFC.v18311LastFastStart.hadPendingSave,true);
  assert.equal(v53Sim.starting,false);
  console.log(JSON.stringify({ok:true,year:2027,hadPendingFullSave:true,blockingPreSave:false,workerStarted:true}));
})().catch(e=>{console.error(e);process.exit(1)});
"""
    test=root/'test-first-vacation-18325.cjs'
    test.write_text(harness,encoding='utf-8')
    try:
        p=subprocess.run(['node',str(test)],capture_output=True,text=True,timeout=12)
    finally:
        test.unlink(missing_ok=True)
    if p.returncode:
        fail('Regressao da primeira ferias 2027: '+(p.stderr or p.stdout)[-3500:])
    race=json.loads(p.stdout.strip())
    if not race.get('workerStarted'):fail('A simulacao nao iniciou')

    result={
        'ok':True,
        'version':'18.325',
        'newSeasonVacationStartsWithoutFullPreSave':True,
        'liveStatePostedToWorker':True,
        'vacationCheckpointRequested':True,
        'previousCommittedSavePreserved':True,
        'raceWithActiveFullSave':race,
        'nonVacationFallbackPreserved':True,
    }
    (root/'new-season-vacation-18311-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':
    main()
