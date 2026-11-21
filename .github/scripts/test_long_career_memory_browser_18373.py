"""Real Workers and named saves with a full 2029 world and three years of history.

The historical records and prior poor form are explicit test inputs, not three
seasons claimed to have been played. The complete original club/player catalog,
2029 calendar, matches, dismissals, job offers, storage, click dispatchers and
reload are real. Authentication and the outer application shell are isolated.
No world is JSON-stringified for observation and no garbage collection is forced.
"""
from __future__ import annotations

import json
import mimetypes
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright
from memory_probe_18373 import MemoryProbe18373, chromium_memory_args
from test_vacation_resume_browser_18369 import browser_path


NAMED_HOOK = r'''
/* TEST_ONLY_NAMED_MEMORY_18373 */
window.__namedMemory373={
 snapshot(){return {busy,modalKind,activeId:slots.activeId,
  entries:sorted().map(x=>({id:x.id,name:x.name,year:x.year,day:x.day,archived:x.archived})),
  hasState:!!state};},
 async manifest(){
  await writingIndex;const m=await get(BASE);
  return m?{format:m.format,token:m.token,revision:m.revision,year:m.year,day:m.day,
   careerId:m.root?.v1903CareerId,coachId:m.root?.userCoachId,user:m.root?.user,
   saveId:m.root?.futbrSaveId,employed:m.root?.userEmployed,
   collections:Object.fromEntries(Object.entries(m.collections||{}).map(([k,v])=>
    [k,{chunks:v.keys?.length||0,nested:v.nested||null,encoding:v.encoding||null,
      hashFormat:v.archiveHash||null,hashes:v.hashes?.length||0,
      unhashableChunks:(v.hashes||[]).filter(h=>h===null).length}]))}:null;
 }
};
'''


HOOK = r'''
/* TEST_ONLY_LONG_CAREER_MEMORY_18373 */
window.__longCareer373={done:false,result:null,phase:'startup',progress:[],notices:[],
 transport:{workersCreated:0,workersTerminated:0,fullWorldSaves:0,fullWorldJobDays:0,
  rpcWorldLoads:0,jobDays:[],vacationBoots:[],ownerSamples:[],finished:[],dismissals:[]},
 count(obj){let n=0;for(const key in obj||{})if(Object.prototype.hasOwnProperty.call(obj,key))n++;return n;},
 hash(text){let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619);}return h>>>0;},
 digest(value){
  // Commutative object-key accumulation, with array indices included in keys.
  // This visits leaves without allocating a second copy or a giant JSON string.
  let nodes=0,strings=0,chars=0;
  const visit=v=>{nodes++;
   if(v===null)return 0x6a09e667;
   if(typeof v!=='object'){const text=typeof v+':'+String(v);strings++;chars+=text.length;return this.hash(text);}
   let sum=Array.isArray(v)?(0x3c6ef372+v.length)>>>0:0xbb67ae85,xor=0,keys=0;
   for(const key in v)if(Object.prototype.hasOwnProperty.call(v,key)){
    const child=visit(v[key]),mixed=(Math.imul(this.hash(key),31)^child)>>>0;
    sum=(sum+mixed)>>>0;xor=(xor^((mixed<<13)|(mixed>>>19)))>>>0;keys++;
   }
   return (sum^xor^Math.imul(keys,2654435761))>>>0;
  };
  const hash=visit(value);return {hash,nodes,strings,chars};
 },
 historyDigest(){return Object.fromEntries(['v555CareerArchive','v538CareerArchive','scorerArchive']
  .map(k=>[k,this.digest(state?.[k]??null)]));},
 worldAudit(){return {identity:this.identity(),
  collections:Object.fromEntries(['players','teams','coaches','schedule','competitions',
   'competitionStats','allTimeStats','v555CareerArchive','v538CareerArchive','scorerArchive',
   'retiredPlayers','retirementHistory','retirements','history','internationalHistory',
   'v735NationalArchive','transfers','crestOverrides','v622Settings','v636CoachCareer']
   .map(k=>[k,this.digest(state?.[k]??null)]))};},
 identity(){return {career:String(state?.v1903CareerId||''),coachId:String(state?.userCoachId||''),
  club:String(state?.user||''),year:Number(state?.year)||0,day:Number(state?.day)||0,
  employed:state?.userEmployed,saveId:state?.futbrSaveId||null,
  players:this.count(state?.players),teams:state?.teams?.length||0,
  calendar:state?.schedule?.length||0,renewals:state?v622Settings(state).renewals:null};},
 snapshot(){return {phase:this.phase,done:this.done,identity:this.identity(),
  sim:{active:!!v53Sim.active,starting:!!v53Sim.starting,syncing:!!v53Sim.syncing,
   finished:!!v53Sim.finished,mode:v53Sim.mode,day:v53Sim.day,progress:v53Sim.progress},
  search:{active:!!v89JobWait.active,pending:!!v18365Job.pending,stage:v89JobWait.stage},
  worker:!!v53Worker,rpc:v53RPC.size,saving:!!v52SavePromise,dirty:!!v52SaveDirty,
  memory:window.GestorFC.memoryStorage18373?.status?.(),
  owner:window.GestorFC.jobWaitMemory18373?.status?.(),
  named:window.__namedMemory373.snapshot(),notices:this.notices.slice(-5)};},
 observeWorkers(){
  const seen=new WeakSet(),original=v53GetWorker,test=this;
  v53GetWorker=function(...args){return original.apply(this,args).then(worker=>{
   if(seen.has(worker))return worker;seen.add(worker);const id=++test.transport.workersCreated,
    send=worker.postMessage,terminate=worker.terminate,receive=worker.onmessage;
   worker.postMessage=function(message,...rest){
    if(message?.op==='save'&&message.state)test.transport.fullWorldSaves++;
    if(message?.op==='load')test.transport.rpcWorldLoads++;
    if(message?.op==='simulate'&&message.mode==='vacation')
     test.transport.vacationBoots.push({worker:id,phase:test.phase,hasState:!!message.state,
      loadSaved:!!message.loadSaved,exactCheckpoint:!!message.vacationBoot18373,
      staleOverlay:!!message.vacationCheckpoint,uiPlayers:test.count(state?.players)});
    if(message?.op==='simulate'&&['day','dayfast'].includes(message.mode)){
     if(message.state)test.transport.fullWorldJobDays++;
     test.transport.jobDays.push({worker:id,phase:test.phase,mode:message.mode,
      hasState:!!message.state,loadSaved:!!message.loadSaved,useResident:!!message.useResident,
      day:message.day,uiPlayers:test.count(state?.players),
      owner:!!window.GestorFC.jobWaitMemory18373?.status?.().ownsWorld});
    }
    return send.call(this,message,...rest);
   };
   worker.terminate=function(...args){test.transport.workersTerminated++;return terminate.apply(this,args);};
   worker.onmessage=function(event){
    const m=event?.data;
    if(m?.kind==='vac-dismissed')test.transport.dismissals.push({worker:id,day:m.day,year:m.year,session:m.session});
    if(m?.kind==='finished')test.transport.finished.push({worker:id,phase:test.phase,day:m.day,year:m.year,session:m.session});
    return receive.call(this,event);
   };return worker;
  });};
 },
 renderShell(){
  const app=document.getElementById('app');if(!app)return;
  // Keep the original game controls and modals, while isolating account setup
  // and the unrelated full shell. No Engine/Worker/storage operation is mocked.
  app.innerHTML='<main id="v555-page" style="padding:32px"><h1>Carreira de teste · 2029</h1>'+
   '<p>Validação com catálogo completo e histórico de três temporadas.</p>'+
   button('v89-job-wait','Até o fim / proposta','primary','id="memory-jobwait-373"')+
   button('futbr125-exit-game','Salvar e sair','secondary','id="memory-exit-373"')+'</main>';
  try{v18363PaintJobButtons(document);}catch(e){}
  return app;
 },
 async prepare(){
  if(state||window.__namedMemory373.snapshot().entries.length)throw Error('Expected an empty isolated profile');
  v548Session={username:'isolated-memory-fixture-18373',plan:'premium'};
  render=()=>this.renderShell();
  const baseToast=toast;toast=(...args)=>{this.notices.push(args.map(String).join(' '));return baseToast(...args);};
  this.phase='creating-2029-fixture';
  state=E.createCareer({club:'t0',manager:'Carreira longa sob teste',seed:183732029,difficulty:'normal'});
  // Later calendars require the preceding continental titleholders. Supply
  // valid historical inputs from each real competition's own participants;
  // never bypass or weaken the original allocation/qualification assertions.
  const titleholders=[],usedChampions=new Set();
  for(const c of Object.values(state.competitions||{})){
   if(!['UEFA','CONMEBOL','CONCACAF','AFC','CAF','OFC'].includes(c.conf))continue;
   const champion=(c.participants||[]).find(id=>!usedChampions.has(id)&&E.team(state,id));
   if(champion){titleholders.push({year:2028,id:c.id,name:c.name,conf:c.conf,champion});usedChampions.add(champion);}
  }
  const lib=titleholders.find(x=>x.id==='lib'),sud=titleholders.find(x=>x.id==='sud');
  if(!lib||!sud||lib.champion===sud.champion)throw Error('The real catalog could not supply distinct prior CONMEBOL champions');
  state.internationalHistory=titleholders;
  state.year=2029;E.setupSeason(state); // The actual calendar builder, including the 2029 Club World Cup.
  state.v1903CareerId='memory-integration-18373-2029';state.live=null;
  state.vacation.active=false;state.vacation.paused=true;
  v636CoachState(state);v636EnsureTracker(state);
  const clubs=new Map(state.teams.map(t=>[t.id,t]));
  state.v555CareerArchive={};state.v538CareerArchive={};state.scorerArchive=[];state.allTimeStats={};
  const counts={packedYears:3,packedRecords:0,scorerRecords:0,allTimeRecords:0};
  for(const year of [2026,2027,2028]){
   const packed={n:{},p:{}},competitions={};let i=0;
   for(const pid in state.players){
    const p=state.players[pid],t=clubs.get(p.clubId);i++;if(!t)continue;
    const apps=18+i%23,goals=p.pos==='GOL'?0:i%17,assists=p.pos==='GOL'?0:i%11;
    packed.n[t.id]=t.name;packed.p[pid]=[t.id,apps,goals,assists,i%8,i%19===0?1:0].join('|');
    counts.packedRecords++;
    // Compact scorer archives retain scorers and assist providers. One in
    // three club players has a historical scoring record in this fixture.
    if(i%3===0&&(goals||assists)){
     const key='league:'+t.country+':'+t.division,bucket=competitions[key]??={};
     bucket[pid]={id:pid,name:p.name,natCode:p.natCode||'UNK',real:!!p.real,star:!!p.star,
      goals,assists,apps,minutes:apps*77,clubs:{[t.id]:t.name},byClub:{}};counts.scorerRecords++;
    }
    if(year===2028){state.allTimeStats[pid]={id:pid,name:p.name,natCode:p.natCode||'UNK',
     real:!!p.real,star:!!p.star,goals:goals*3,assists:assists*3,apps:apps*3,
     minutes:apps*77*3,clubs:{[t.id]:t.name}};counts.allTimeRecords++;}
    if(i%12000===0)await new Promise(r=>setTimeout(r,0));
   }
   state.v555CareerArchive[year]=packed;state.scorerArchive.unshift({year,competitions});
  }
  // The companion codec suite exercises legacy year-id-v1 saves and mixed
  // schemas. This browser fixture uses the game's current packed archive so
  // a legitimate background migration cannot change its structural digest.
  v622Settings(state).renewals='board';v18371CommitSettings(state);
  saved=null;view='career';saveOK=true;v52SavePromise=null;v52SaveDirty=false;v52PendingState=null;
  v53Sim.active=false;v53Sim.starting=false;v53Sim.syncing=false;v53Sim.patching=false;v53Sim.finished=null;
  this.observeWorkers();this.initial={...this.identity(),counts,history:this.historyDigest(),
   fixtureInputs:'Original full world and 2029 calendar; synthetic 2026–2028 statistics and valid 2028 continental titleholders in real schemas',
   previousContinentalChampions:titleholders,
   priorSeasonsActuallySimulated:false,authAndOuterShellIsolated:true};
  if(this.initial.players<180000||this.initial.teams<5000||counts.packedRecords<400000||counts.scorerRecords<90000)
   throw Error('Long-career fixture is unexpectedly small: '+JSON.stringify(this.initial));
  if(!state.competitions.cwc)throw Error('The original calendar omitted the 2029 Club World Cup');
  this.phase='initial-named-save';render();window.GestorFC.namedSaves125.save();return this.initial;
 },
 assertHistory(label){
  const actual=this.historyDigest();
  if(JSON.stringify(actual)!==JSON.stringify(this.initial.history))
   throw Error(label+' changed historical records: '+JSON.stringify({expected:this.initial.history,actual}));
  return actual;
 },
 startDismissalSearch(cycle){
  if(this.working)throw Error('Another test flow is running');this.working=true;this.done=false;this.result=null;
  (async()=>{
   let timer=null;
   try{
    const before=this.identity(),club=E.team(state,state.user),coach=state.coaches[state.userCoachId];
    if(!before.employed||coach.clubId!==club.id||before.renewals!=='board')throw Error('Invalid current employment');
    this.phase='dismissal-'+cycle;
    const division=state.teams.filter(t=>t.country===club.country&&Number(t.division)===Number(club.division));
    club.stats.pts=Math.min(...division.filter(t=>t.id!==club.id).map(t=>Number(t.stats.pts)))-10;
    state.allowUserDismissal=true;coach.jobGames=20;coach.pressure=100;coach.recent=Array(10).fill(0);coach.lastTitleDay=-100;
    const dismissalsBefore=this.transport.dismissals.length;
    E.startVacation(state,24,false);await v53StartSimulation('vacation',{liveStateNoPreSave:true});
    const returnedAt=performance.now(),dismissed=this.identity();
    if(state.userEmployed!==false||this.transport.dismissals.length<=dismissalsBefore)
     throw Error('Original board did not dismiss the coach after a real vacation match');
    this.phase='job-search-'+cycle;render();
    const btn=document.getElementById('memory-jobwait-373');v18363PaintJobButtons(document);
    if(!btn||btn.disabled)throw Error('Actual job-search control is disabled: '+v18363LastBlocker);
    const dayBefore=Number(state.day),daysBefore=this.transport.jobDays.length;
    btn.click(); // No delay, forced GC, invented message or checkpoint reload.
    const immediateClickMs=performance.now()-returnedAt;
    timer=setInterval(()=>{
     const status=window.GestorFC.jobWaitMemory18373.status();
     if(status.ownsWorld&&this.transport.ownerSamples.filter(s=>s.cycle===cycle).length<100)
      this.transport.ownerSamples.push({cycle,phase:status.phase,players:this.count(state?.players),
       packedYears:this.count(state?.v555CareerArchive),day:state?.day});
    },200);
    const started=Date.now();
    while(v89JobWait.active||v18365Job.pending||v53Sim.active||v53Sim.starting||
      v53Sim.syncing||v52SavePromise||window.GestorFC.jobWaitMemory18373.status().ownsWorld){
     if(Date.now()-started>480000)throw Error('Genuine job search exceeded eight minutes');
     await new Promise(r=>setTimeout(r,25));
    }
    clearInterval(timer);timer=null;
    const after=this.identity(),offers=v636PendingCoachOffers(state).map(o=>({...o}));
    if(!offers.length||after.day<=dayBefore||this.transport.jobDays.length<=daysBefore)
     throw Error('Original job search did not advance and stop on a real offer: '+JSON.stringify(this.snapshot()));
    if(after.career!==before.career||after.coachId!==before.coachId||after.employed||after.players!==before.players||
     after.teams!==before.teams||after.renewals!=='board')throw Error('Job search lost the full career or manager preferences');
    for(const o of offers)if(!E.team(state,o.teamId)||o.expiresDay<state.day)throw Error('Invalid job invitation');
    const history=this.assertHistory('Search cycle '+cycle);
    const modalDeadline=Date.now()+2000;
    while(!document.querySelector('#modal-root [data-action="v636-accept-job-offer"]')&&Date.now()<modalDeadline)
     await new Promise(r=>setTimeout(r,15)); // Wait for the original modal's 30 ms scheduling, without opening it in the test.
    if(!document.querySelector('#modal-root [data-action="v636-accept-job-offer"]'))
     throw Error('Actual offer modal was not opened after restoring the full world');
    this.result={ok:true,cycle,before,dismissed,after,offers,history,immediateClickMs,
     realDismissal:true,realJobOffer:true,actualJobButton:true,daysAdvanced:after.day-dayBefore,
     memory:window.GestorFC.memoryStorage18373.status(),owner:window.GestorFC.jobWaitMemory18373.status()};
   }catch(error){this.result={ok:false,error:String(error),stack:String(error.stack),snapshot:this.snapshot()};}
   finally{if(timer)clearInterval(timer);this.done=true;this.working=false;}
  })();return true;
 },
 startVacationExit(cycle,offer){
  if(this.working)throw Error('Another test flow is running');this.working=true;this.done=false;this.result=null;
  (async()=>{
   let timer=null;
   try{
    if(state.user!==offer.teamId||!state.userEmployed||state.coaches[state.userCoachId].clubId!==offer.teamId||
     v622Settings(state).renewals!=='board'||v636PendingCoachOffers(state).length)throw Error('Actual invitation was not accepted');
    await v52FlushSave();if(v52SavePromise)await v52SavePromise;
    const before=this.identity();this.phase='manual-vacation-'+cycle;
    // Prior stable board confidence is fixture input; the following matches
    // and manual end command continue to use the original simulation.
    const me=state.coaches[state.userCoachId],club=E.team(state,state.user);
    me.pressure=0;me.jobGames=0;me.recent=[];club.fanPressure=0;club.balance=Math.max(club.balance,1000000);
    E.startVacation(state,24,false);let stopped=false;
    const vacation=v53StartSimulation('vacation',{liveStateNoPreSave:true});
    timer=setInterval(()=>{
     if(!stopped&&v53Sim.active&&v53Sim.mode==='vacation'&&Number(v53Sim.day)>=before.day+2)
      stopped=v723RequestVacationControl('end')===true;
    },100);
    await vacation;clearInterval(timer);timer=null;
    if(!stopped||state.vacation.active||!state.userEmployed||v53Sim.active||v53Sim.syncing)
     throw Error('Original manual vacation end did not return a complete employed career');
    this.assertHistory('Vacation cycle '+cycle);
    const playerWritesBeforeExit=window.GestorFC.memoryStorage18373.status().playerChunksWritten;
    if(cycle===2){
     // Exercise the dirty save-and-exit path too, while keeping renewals delegated.
     v622Settings(state).offerPopup=!v622Settings(state).offerPopup;
     v18371CommitSettings(state);persist();
    }
    this.beforeExit=this.worldAudit();this.phase='save-and-exit-'+cycle;
    const began=performance.now();render();document.getElementById('memory-exit-373').click();
    const confirm=document.querySelector('#modal-root [data-action="futbr125-save-and-exit"]');
    if(!confirm)throw Error('Original in-game save-and-exit dialog did not open');
    confirm.click(); // The original named-save router, ensureSaved and returnToCareerMenu.
    const requested=Date.now();
    while(state||window.__namedMemory373.snapshot().busy){
     if(Date.now()-requested>180000)throw Error('Actual save and exit exceeded three minutes');
     await new Promise(r=>setTimeout(r,25));
     if(!window.__namedMemory373.snapshot().busy&&state&&Date.now()-requested>1000)
      throw Error('Save and exit returned without leaving the career: '+this.notices.slice(-3).join(' | '));
    }
    const manifest=await window.__namedMemory373.manifest();
    if(v53Worker||v52SavePromise||v52SaveDirty||v52PendingState||v53RPC.size)
     throw Error('Returning to the menu retained active world/Worker/save references: '+JSON.stringify(this.snapshot()));
    this.result={ok:true,cycle,before,beforeExit:this.beforeExit,manualStop:true,
     actualSaveAndExitControls:true,dirtySavePath:cycle===2,elapsedMs:performance.now()-began,
     playerChunksWrittenDuringExit:window.GestorFC.memoryStorage18373.status().playerChunksWritten-playerWritesBeforeExit,
     manifest,named:window.__namedMemory373.snapshot(),memory:window.GestorFC.memoryStorage18373.status()};
   }catch(error){this.result={ok:false,error:String(error),stack:String(error.stack),snapshot:this.snapshot()};}
   finally{if(timer)clearInterval(timer);this.done=true;this.working=false;}
  })();return true;
 },
 verifyReload(){
  if(!state||window.__namedMemory373.snapshot().busy)throw Error('The original named-save loader has not completed');
  const audit=this.worldAudit();
  if(JSON.stringify(audit)!==JSON.stringify(this.beforeExit))
   throw Error('Reload changed saved identity or full collection digests: '+JSON.stringify({before:this.beforeExit,after:audit}));
  this.assertHistory('Named save reload');
  if(window.GestorFC.jobWaitMemory18373.status().ownsWorld||v53RPC.size||v53Worker)
   throw Error('Direct loading left a duplicate resident Worker or pending ownership');
  return {ok:true,audit,actualNamedSaveLoader:true,allAuditedCollectionsPreserved:true,
   memory:window.GestorFC.memoryStorage18373.status()};
 }
};
'''


def inject_hooks(html: str) -> str:
    for marker in ('FUTBR_VACATION_DURABLE_CHECKPOINT_18373',
                   'memoryStorage18373', 'jobWaitMemory18373',
                   'FUTBR_VACATION_BOUNDED_BOOT_18373', 'FUTBR_PLAYER_CHECKPOINT_REUSE_18373'):
        assert marker in html, 'Missing production correction: ' + marker
    assert 'TEST_ONLY_LONG_CAREER_MEMORY_18373' not in html
    anchor = 'G.namedSaves125={list:'
    assert html.count(anchor) == 1
    html = html.replace(anchor, NAMED_HOOK + '\n' + anchor, 1)
    start = html.index('let state=null,saved=null')
    end = html.index('</script>', start)
    anchor = html.rfind('})();', start, end)
    assert start < anchor < end
    return html[:anchor] + '\n' + HOOK + '\n' + html[anchor:]


def wait_flow(page, probe, limit=720):
    deadline = time.monotonic() + limit
    last_phase = None
    while time.monotonic() < deadline:
        page.wait_for_timeout(2000)
        current = page.evaluate('() => window.__longCareer373.snapshot()')
        phase = current['phase']
        probe.mark(page, phase)
        if phase != last_phase or current['done']:
            print('18.373 PROGRESS ' + json.dumps(current, ensure_ascii=False), flush=True)
            last_phase = phase
        if current['done']:
            result = page.evaluate('() => window.__longCareer373.result')
            if not result or not result.get('ok'):
                raise RuntimeError('Real long-career flow failed: ' + json.dumps(result, ensure_ascii=False))
            return result
    raise TimeoutError('Real long-career flow did not finish: ' + json.dumps(current, ensure_ascii=False))


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_long_career_memory_browser_18373.py <project>')
    root = Path(sys.argv[1]).resolve()
    artifacts = root / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    test_html = inject_hooks((root / 'src/index.html').read_text(encoding='utf-8'))
    errors, dialogs, crashes = [], [], []
    result = {'ok': False, 'version': '18.373.0', 'cycles': []}
    phase = 'startup'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=browser_path(), headless=True,
            args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox', *chromium_memory_args()])
        probe = MemoryProbe18373(browser).start()
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append({'phase': phase, 'message': str(error)}))
        page.on('crash', lambda: crashes.append({'phase': phase}))

        def native_dialog(dialog):
            dialogs.append({'phase': phase, 'type': dialog.type, 'message': dialog.message})
            dialog.dismiss()

        page.on('dialog', native_dialog)

        def route_request(route):
            request = urlsplit(route.request.url)
            if request.netloc != 'memory-18373.test':
                route.abort()
                return
            relative = unquote(request.path).lstrip('/')
            if relative in ('', 'index.html'):
                route.fulfill(status=200, content_type='text/html; charset=utf-8', body=test_html)
                return
            path = (root / 'src' / relative).resolve()
            if path.is_file() and (root / 'src').resolve() in path.parents:
                route.fulfill(path=str(path), content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            else:
                route.fulfill(status=404, body='not found')

        page.route('**/*', route_request)
        try:
            page.goto('https://memory-18373.test/', wait_until='domcontentloaded', timeout=120000)
            page.wait_for_function('() => !!window.__longCareer373 && !!window.GestorFC?.namedSaves125', timeout=120000)
            # All startup-script errors are recorded separately. Any exception
            # during the actual game/Worker/save flows is a test failure.
            page.wait_for_timeout(1000)
            phase = 'fixture-and-initial-save'
            probe.mark(page, phase)
            result['initial'] = page.evaluate('() => window.__longCareer373.prepare()')
            print('18.373 INITIAL ' + json.dumps(result['initial'], ensure_ascii=False), flush=True)
            page.locator('#futbr125-save-name').fill('Carreira longa 2029')
            page.locator('[data-action="futbr125-save-current"]').click()
            page.wait_for_function('''() => {
              const s=window.__namedMemory373.snapshot();
              return !s.busy && s.entries.length===1 && s.modalKind!=='futbr125-save';
            }''', timeout=240000)
            result['initialManifest'] = page.evaluate('() => window.__namedMemory373.manifest()')
            assert result['initialManifest']['format'] == 'GFC_SHARDED_171'
            assert result['initialManifest']['year'] == 2029
            probe.mark(page, 'initial-named-save-complete')
            for cycle in (1, 2):
                phase = 'dismissal-and-search-' + str(cycle)
                page.evaluate('(n) => window.__longCareer373.startDismissalSearch(n)', cycle)
                search = wait_flow(page, probe)
                page.screenshot(path=str(artifacts / f'long-career-offer-18373-{cycle}.png'))
                phase = 'acceptance-' + str(cycle)
                offer = search['offers'][0]
                page.locator('[data-action="v636-accept-job-offer"]').first.click()
                page.evaluate('({cycle,offer}) => window.__longCareer373.startVacationExit(cycle,offer)',
                              {'cycle': cycle, 'offer': offer})
                exited = wait_flow(page, probe)
                phase = 'named-reload-' + str(cycle)
                probe.mark(page, phase)
                page.evaluate('() => window.GestorFC.namedSaves125.open()')
                page.locator('[data-action="futbr125-load"]').click()
                page.wait_for_function('''() => {
                  const s=window.__namedMemory373.snapshot();
                  return s.hasState&&!s.busy&&s.modalKind!=='futbr125-list';
                }''', timeout=240000)
                reloaded = page.evaluate('() => window.__longCareer373.verifyReload()')
                result['cycles'].append({'search': search, 'saveAndExit': exited, 'reload': reloaded})
                probe.mark(page, 'reloaded-' + str(cycle))
            result['transport'] = page.evaluate('() => window.__longCareer373.transport')
            result['finalRuntime'] = page.evaluate('() => window.GestorFC.memoryStorage18373.status()')
            result['vacationBoot'] = page.evaluate('() => window.GestorFC.vacationBoot18373.status()')
            result['storageAudit'] = page.evaluate('() => window.GestorFC.v171.storageAudit()')
            t = result['transport']
            flags = {
                'fullOriginalWorldIn2029': result['initial']['players'] >= 180000,
                'threeHistoricalSeasonsPreserved': all(c['reload']['allAuditedCollectionsPreserved'] for c in result['cycles']),
                'twoRealDismissalsAndOffers': len(t['dismissals']) >= 2 and all(c['search']['realJobOffer'] for c in result['cycles']),
                'immediateJobSearchAfterDismissal': all(c['search']['immediateClickMs'] < 2000 for c in result['cycles']),
                'zeroFullWorldJobWaitTransfers': t['fullWorldJobDays'] == 0 and len(t['jobDays']) >= 2,
                'zeroFullWorldSaveTransfers': t['fullWorldSaves'] == 0,
                'zeroFullWorldVacationTransfers': len(t['vacationBoots']) == 4 and all(not boot['hasState'] for boot in t['vacationBoots']),
                'exactCheckpointVacationBoots': all(boot['loadSaved'] and boot['exactCheckpoint'] and not boot['staleOverlay'] for boot in t['vacationBoots']) and result['vacationBoot']['checkpoints'] == 4,
                'completeUiPreservedAtVacationBoot': all(boot['uiPlayers'] == result['initial']['players'] for boot in t['vacationBoots']),
                'unchangedPlayerChunksReusedOnSaveExit': all(c['saveAndExit']['playerChunksWrittenDuringExit'] == 0 for c in result['cycles']),
                'canonicalPlayerCheckpoints': all(m['collections']['players']['hashFormat'] == 'sha256-player-packed-json-v1' and m['collections']['players']['hashes'] == m['collections']['players']['chunks'] > 0 for m in [result['initialManifest'], *[c['saveAndExit']['manifest'] for c in result['cycles']]]),
                'zeroRpcWholeWorldReloads': t['rpcWorldLoads'] == 0,
                'workerSoleWorldOwnerDuringSearch': all(any(s['cycle'] == cycle and s['phase'] == 'worker' for s in t['ownerSamples']) for cycle in (1, 2)) and all(s['players'] == 0 and s['packedYears'] == 0 for s in t['ownerSamples'] if s['phase'] == 'worker') and all(day['uiPlayers'] == 0 for day in t['jobDays']),
                'completeWorldReturnedWithoutRecovery': all(c['search']['owner']['recoveries'] == 0 for c in result['cycles']),
                'manualVacationStopThenRealSaveExit': all(c['saveAndExit']['manualStop'] and c['saveAndExit']['actualSaveAndExitControls'] for c in result['cycles']),
                'cleanAndDirtySaveExitPaths': result['cycles'][0]['saveAndExit']['dirtySavePath'] is False and result['cycles'][1]['saveAndExit']['dirtySavePath'] is True,
                'actualNamedReloadPreservesCollections': all(c['reload']['actualNamedSaveLoader'] for c in result['cycles']),
                'boardRenewalsPreservedAcrossClubs': all(c['reload']['audit']['identity']['renewals'] == 'board' for c in result['cycles']),
                'testHooksNotShipped': True,
            }
            result.update(flags)
            assert all(flags.values()), 'Long-career invariant failed: ' + json.dumps(flags)
            assert not dialogs, 'Unexpected native dialog: ' + json.dumps(dialogs)
            assert not crashes, 'Browser/renderer crashed: ' + json.dumps(crashes)
            flow_errors = [e for e in errors if e['phase'] != 'startup']
            assert not flow_errors, 'Exceptions during actual flows: ' + json.dumps(flow_errors)
            result['ok'] = True
        except Exception as error:
            result['error'] = str(error)
            try:
                result['failureState'] = page.evaluate('() => window.__longCareer373?.snapshot?.()')
                result['failureTransport'] = page.evaluate('() => window.__longCareer373?.transport')
                page.screenshot(path=str(artifacts / 'long-career-memory-18373-failure.png'))
            except Exception as diagnostic_error:
                result['diagnosticError'] = str(diagnostic_error)
        finally:
            result['memory'] = probe.finish()
            probe.write_trace(artifacts / 'long-career-memory-18373-samples.jsonl')
            result['withinMeasuredMemoryBudget'] = result['memory']['ok']
            result['ok'] = bool(result['ok'] and result['withinMeasuredMemoryBudget'])
            result['errors'] = errors
            result['nativeDialogs'] = dialogs
            result['crashes'] = crashes
            (root / 'long-career-memory-browser-18373-tests.json').write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            browser.close()
    print(json.dumps(result, ensure_ascii=False, indent=2), flush=True)
    if not result['ok']:
        raise SystemExit('18.373 real long-career memory integration failed')


if __name__ == '__main__':
    main()
