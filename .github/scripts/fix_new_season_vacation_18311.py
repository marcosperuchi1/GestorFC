from __future__ import annotations
import json, sys
from pathlib import Path

VERSION='18.311'

def fail(msg):
    raise RuntimeError(msg)

def once(src, old, new, label):
    n=src.count(old)
    if n!=1:
        fail(f'{label}: esperado 1, encontrado {n}')
    return src.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: fix_new_season_vacation_18311.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src'/'index.html'
    html=path.read_text(encoding='utf-8')
    if 'v18311VacationCheckpointFix' in html:
        print('18.311 already applied')
        return

    # Base simulator: when the new-season wrapper explicitly chooses the live-state
    # path, do not force a complete 200k-player save before the Worker can start.
    start=html.find('async function v53StartSimulation(mode,options={}){')
    end=html.find('\nrunVacation=async function',start)
    if start<0 or end<0:
        fail('v53StartSimulation base nao localizado')
    base=html[start:end]
    base=once(
        base,
        'const compactHumanMatch=!!manualOverlaySnapshot;',
        "const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=mode==='vacation'&&!!options?.liveStateNoPreSave&&!v52SavePromise;",
        'flag live-state vacation'
    )
    base=once(
        base,
        '}else{await v52FlushSave();if(v52SavePromise)await v52SavePromise;}',
        "}else if(v18311LiveVacation){clearTimeout(v52SaveTimer);v52SaveTimer=null;v52SaveDirty=false;v52PendingState=null;v52NotifySave=false;const waiters=v52SaveWaiters.splice(0);for(const resolve of waiters)try{resolve();}catch(e){}try{window.GestorFC.v18311LastFastStart={year:Number(state?.year)||0,day:Number(state?.day)||0,phase:'live-state-worker'};}catch(e){}}else{await v52FlushSave();if(v52SavePromise)await v52SavePromise;}",
        'skip blocking pre-save'
    )
    base=once(
        base,
        'if(state?.v1903CareerId&&!saveOK){',
        'if(!v18311LiveVacation&&state?.v1903CareerId&&!saveOK){',
        'do not demand initial save in live vacation'
    )
    base=once(
        base,
        "const canLoadSaved=!!saveOK&&(mode==='day'||mode==='dayfast'||mode==='nationaljump'||mode==='nextmatch'||mode==='vacation');",
        "const canLoadSaved=!v18311LiveVacation&&!!saveOK&&(mode==='day'||mode==='dayfast'||mode==='nationaljump'||mode==='nextmatch'||mode==='vacation');",
        'force live state instead of previous-season save'
    )
    html=html[:start]+base+html[end:]

    # New-season wrapper: vacation is special. Keep the last committed save intact,
    # cancel only the pending unsaved rollover request, and send the authoritative
    # 2027+ state directly to the simulation Worker. The Worker resumes its normal
    # per-journey checkpointing immediately after it starts.
    ws=html.find('const v168BaseStartSimulation=v53StartSimulation;')
    we=html.find('// Autoridade final da virada:',ws)
    if ws<0 or we<0:
        fail('wrapper de nova temporada nao localizado')
    wrapper=html[ws:we]
    anchor=" if(v168DeferredRolloverSave&&state){"
    if wrapper.count(anchor)!=1:
        fail(f'ancora deferred save: esperado 1, encontrado {wrapper.count(anchor)}')
    fast=r""" if(v168DeferredRolloverSave&&state&&mode==='vacation'&&!v52SavePromise){
  if(v53Sim.active||v53Sim.starting||v53Creating)throw Error('Outra operação da carreira está em andamento.');
  v18121NewSeasonPreparation=true;
  v53Sim.starting=true;v53Sim.mode=mode;v53Sim.progress='Inicializando férias da nova temporada';
  const target=state,year=Number(state.year)||0,day=Number(state.day)||0;
  try{
   v148EnsureNationalReady(target);
   if(state!==target||Number(state.year)!==year||Number(state.day)!==day)throw Error('A carreira mudou durante a preparação das férias.');
   clearTimeout(v52SaveTimer);v52SaveTimer=null;
   v52PendingState=null;v52SaveDirty=false;v52NotifySave=false;
   const waiters=v52SaveWaiters.splice(0);for(const resolve of waiters)try{resolve();}catch(e){}
   v168DeferredRolloverSave=false;
   const G=window.GestorFC=window.GestorFC||{};
   G.v18311VacationCheckpointFix={version:'18.311',liveStateStart:true,blockingFullPreSave:false,workerCheckpoint:true,previousSavePreserved:true};
   G.v18311LastFastStart={year,day,at:Date.now(),mode};
  }catch(e){
   v168DeferredRolloverSave=true;
   if(state===target){v52PendingState=target;v52SaveDirty=true;v52NotifySave=false;}
   try{window.GestorFC.v18311LastFastStart={year,day,ok:false,error:String(e?.message||e)};}catch(_){}
   throw e;
  }finally{
   v53Sim.starting=false;v18121NewSeasonPreparation=false;
   try{v53PaintStatus();}catch(e){}
  }
  const options={...(rest[0]||{}),liveStateNoPreSave:true,vacationCheckpoint:true};
  try{return await v168BaseStartSimulation(mode,options);}
  catch(e){
   v168DeferredRolloverSave=true;
   if(state){v52PendingState=state;v52SaveDirty=true;v52NotifySave=false;}
   throw e;
  }
 }
"""
    wrapper=wrapper.replace(anchor,fast+anchor,1)
    html=html[:ws]+wrapper+html[we:]

    if "v53Sim.progress='Salvando o calendário da nova temporada (uma única vez)'" not in html:
        fail('fluxo legado de fallback nao encontrado')
    if "liveStateNoPreSave:true,vacationCheckpoint:true" not in html:
        fail('opcoes 18.311 nao instaladas')
    if "blockingFullPreSave:false" not in html:
        fail('marcador 18.311 ausente')

    path.write_text(html,encoding='utf-8')
    report={
        'ok':True,
        'version':VERSION,
        'problem':'blocking full save before first vacation of new season',
        'fix':'live authoritative state starts Worker without blocking pre-save',
        'blockingFullPreSave':False,
        'workerCheckpoint':True,
        'previousSavePreserved':True,
        'fallbackForNonVacation':True,
    }
    (root/'new-season-vacation-18311-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
    main()
