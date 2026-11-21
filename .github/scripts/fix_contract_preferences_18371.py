from __future__ import annotations
import json,sys
from pathlib import Path

MARK='FUTBR_CONTRACT_PREFERENCES_18371'

def once(text,old,new,reason):
    n=text.count(old)
    if n!=1:raise RuntimeError(f'18.371 settings {reason}: expected one original occurrence, got {n}')
    return text.replace(old,new,1)

ENGINE=r'''
  /* FUTBR_CONTRACT_PREFERENCES_18371
     The decision belongs to this manager's career, not to the current club.
     Keep one tiny copy on the manager as well as the legacy root field. Both
     travel through the existing sharded saves; there is no account/global cache. */
  function managerSettings18371(s,incoming=null){
    if(!s)return {renewals:'manual',matchSpeed:'180',offerPopup:true,revision18371:0};
    const me=s.coaches?.[s.userCoachId],stored=me?.v18371CareerSettings,
      valid=x=>!!x&&typeof x==='object'&&!Array.isArray(x),
      revision=x=>Math.max(0,Number.isSafeInteger(x?.revision18371)?x.revision18371:0);
    let cfg=valid(s.v622Settings)?s.v622Settings:null;
    // Equal/legacy revisions prefer the explicit root value, including manual
    // and false. A newer saved user decision wins over an older worker copy.
    if(valid(stored)&&(!cfg||revision(stored)>revision(cfg)))cfg={...stored};
    if(!cfg)cfg={};
    if(valid(incoming)&&revision(incoming)>=revision(cfg)){
      if(incoming.renewals==='manual'||incoming.renewals==='board')cfg.renewals=incoming.renewals;
      if(typeof incoming.matchSpeed==='string'||typeof incoming.matchSpeed==='number')cfg.matchSpeed=String(incoming.matchSpeed);
      if(typeof incoming.offerPopup==='boolean')cfg.offerPopup=incoming.offerPopup;
      cfg.revision18371=revision(incoming);
    }
    if(cfg.renewals!=='manual'&&cfg.renewals!=='board')cfg.renewals='manual';
    if(!cfg.matchSpeed)cfg.matchSpeed='180';
    cfg.matchSpeed=String(cfg.matchSpeed);
    if(typeof cfg.offerPopup!=='boolean')cfg.offerPopup=true;
    cfg.revision18371=revision(cfg);s.v622Settings=cfg;
    if(me)me.v18371CareerSettings={renewals:cfg.renewals,matchSpeed:cfg.matchSpeed,
      offerPopup:cfg.offerPopup,revision18371:cfg.revision18371};
    return cfg;
  }
  function applyManagerSettings18371(s,envelope){
    // A previous career or another manager must never supply preferences.
    if(!s||!envelope||!String(s.v1903CareerId||'')||
       String(envelope.careerId||'')!==String(s.v1903CareerId)||
       String(envelope.coachId||'')!==String(s.userCoachId||''))return false;
    managerSettings18371(s,envelope.settings);return true;
  }
  function boardRenewals18371(s,force=false){
    if(!s||managerSettings18371(s).renewals!=='board'||!s.userEmployed||
       s.live||s.v640National?.userTeam)return 0;
    const t=human(s);if(!t)return 0;
    const due=(t.roster||[]).map(id=>player(s,id)).filter(p=>p&&Number(p.contract)<=1)
      .sort((a,b)=>Number(!!b.star)-Number(!!a.star)||overall(b)-overall(a)||
        (Number(a.age)||99)-(Number(b.age)||99));
    let done=0;
    for(const p of due){
      const years=Number(p.age)<=24?5:Number(p.age)<=29?4:Number(p.age)<=33?3:2;
      const newWage=Math.max(Math.ceil(Number(p.wage||0)*1.05/100)*100,
        Math.ceil(salaryDemand58(p)*.94/100)*100),fee=Math.round(newWage*4),
        reserve=Math.max(payroll(s,t)*2.5,400000);
      if(!force&&t.balance-fee<reserve)continue;
      if(force&&t.balance<fee)continue;
      try{renew(s,p.id,years);p.v622BoardRenewedYear=s.year;done++;
        news(s,'Renovação pela diretoria',p.name+' renovou por '+years+' temporadas.','good');
      }catch(e){}
    }
    return done;
  }
'''

UI=r'''
function v18371SettingsEnvelope(s=state){
 if(!s)return null;const cfg=v622Settings(s);
 return {careerId:String(s.v1903CareerId||''),coachId:String(s.userCoachId||''),
  settings:{renewals:cfg.renewals,matchSpeed:cfg.matchSpeed,
   offerPopup:cfg.offerPopup,revision18371:cfg.revision18371}};
}
function v18371CommitSettings(s=state){
 if(!s)return;const cfg=v622Settings(s);cfg.revision18371++;
 E.managerSettings18371(s,cfg);
 // The UI owns preferences even when a previous round left a resident worker.
 // Send only four scalar fields, never another world or player collection.
 if(s===state&&v53Worker)try{
  v53Worker.postMessage({op:'manager-settings-18371',...v18371SettingsEnvelope(s)});
 }catch(e){console.warn('[18.371] preferences will sync with the next command',e);}
}
function v18371PreserveSettingsRoot(next,current=state){
 const envelope=v18371SettingsEnvelope(current);
 if(envelope)E.applyManagerSettings18371(next,envelope);
 return next;
}
window.GestorFC=window.GestorFC||{};
window.GestorFC.contractPreferences18371={
 version:'18.371.0',scope:'manager-career',
 status:()=>v18371SettingsEnvelope(state),
 preserveRoot:next=>v18371PreserveSettingsRoot(next)
};
'''

def patch(s):
    if MARK in s:return s
    s=once(s,'  function takeJob(s,id){',ENGINE+'\n  function takeJob(s,id){','engine preference owner')
    s=once(s,"  function takeJob(s,id){\n    if(s.live", "  function takeJob(s,id){\n    managerSettings18371(s);\n    if(s.live",'new club preserves manager decision')
    s=once(s,"    if(c.id===s.userCoachId){\n      s.userEmployed=false;", "    if(c.id===s.userCoachId){\n      managerSettings18371(s);\n      s.userEmployed=false;",'dismissal preserves manager decision')
    s=once(s,'  return {varReviewFactor588:', '  return {managerSettings18371,applyManagerSettings18371,boardRenewals18371,varReviewFactor588:','engine export shared with worker')
    old=" const cfg=s.v622Settings||(s.v622Settings={renewals:'manual',matchSpeed:'180',offerPopup:true});"
    s=once(s,old,' const cfg=E.managerSettings18371(s);','legacy settings reader')
    s=once(s,'function v622AllowedSpeedOptions(){',UI+'\nfunction v622AllowedSpeedOptions(){','private UI helpers')
    s=once(s,'Object.assign(cfg,draft);speed=Number(cfg.matchSpeed)||180;',
        'Object.assign(cfg,draft);v18371CommitSettings(state);speed=Number(cfg.matchSpeed)||180;','explicit settings save')
    s=once(s,"else if(el.dataset.v622Setting==='offerPopup')cfg.offerPopup=el.value!=='no';persist();",
        "else if(el.dataset.v622Setting==='offerPopup')cfg.offerPopup=el.value!=='no';v18371CommitSettings(state);persist();",'legacy settings save')
    a=s.index('function v622BoardRenewals(s,force=false){');b=s.index('function v622AfterCompletedRound(s){',a)
    s=once(s,s[a:b],'function v622BoardRenewals(s,force=false){return E.boardRenewals18371(s,force);}\n',
        'same financial renewal rule shared with worker')
    s=once(s,'    if(compactHumanMatch)msg.manualOverlay=manualOverlaySnapshot;',
        '    msg.managerSettings18371=v18371SettingsEnvelope(state);\n    if(compactHumanMatch)msg.manualOverlay=manualOverlaySnapshot;','outgoing simulation preferences')
    anchor="  const lowMemoryVacation=message.mode==='vacation',lowMemoryDay=message.mode==='day';"
    s=once(s,anchor,"""  // FUTBR_MANAGER_PREFERENCES_WORKER_18371: apply after the saved/checkpoint
  // overlay. Renew in the authoritative worker before any vacation match, so
  // loadSaved cannot discard renewals or charge the UI cash a second time.
  E.applyManagerSettings18371(world,message.managerSettings18371);
  if(message.mode==='vacation')E.boardRenewals18371(world,true);
"""+anchor,'worker consumes preferences and renews authoritatively')
    s=once(s," self.onmessage=event=>{const m=event.data;\n  if(m.op==='vac-final-save-ack')",
        " self.onmessage=event=>{const m=event.data;\n  if(m.op==='manager-settings-18371'){E.applyManagerSettings18371(world,m);return;}\n  if(m.op==='vac-final-save-ack')",'resident worker preference update')
    s=once(s,'v125VacIncoming={...(m.root||{})};',
        'v125VacIncoming=v18371PreserveSettingsRoot({...(m.root||{})});','first state drain')
    s=once(s,'    state=null;saved=null;v125VacIncoming={...(m.root||{}),',
        '    const settings18371=v18371SettingsEnvelope(state);\n    state=null;saved=null;v125VacIncoming={...(m.root||{}),','final drain preserves only tiny settings')
    s=once(s,'scorerArchive:scorers||[],crestOverrides:overrides||{}};',
        'scorerArchive:scorers||[],crestOverrides:overrides||{}};\n    E.applyManagerSettings18371(v125VacIncoming,settings18371);','final state drain restores settings')
    # Promotion reuses existing heavy shards. Update just the tiny preferences
    # root before its atomic manifest commit, including edits made during a round.
    old='  await commitManifest(manifest,old,meta);const keep=keysOf(manifest);'
    s=once(s,old,'  window.GestorFC.contractPreferences18371.preserveRoot(manifest.root);\n'+old,
        'atomic checkpoint uses explicit bridge to private settings')
    return s

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_contract_preferences_18371.py <project>')
    root=Path(sys.argv[1]);file=root/'src/index.html';s=file.read_text(encoding='utf-8');out=patch(s)
    file.write_text(out,encoding='utf-8')
    report={'ok':True,'version':'18.371.0','changed':s!=out,'managerCareerSettings':True,
      'compactWorkerOverlay':True,'sameCareerOnly':True,'explicitManualPreserved':True,
      'renewalBeforeVacationRunsInAuthoritativeWorker':True,'newGlobalPreferences':False}
    (root/'contract-preferences-18371-install.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))

if __name__=='__main__':main()
