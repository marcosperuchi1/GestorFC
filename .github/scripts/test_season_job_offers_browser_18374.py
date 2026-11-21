"""Recover a legacy 2031 unemployed save through the real button and Worker.

The previous career/year are fixture inputs, not seasons claimed to have been
played. The complete catalog, 2031 calendar, dismissal function, next matches,
job-search loop, compact transport, proposal, named saves and takeover are real.
The companion rollover browser gate covers the actual 2028 -> 2029 transition.
"""
from __future__ import annotations
import hashlib
import json
import mimetypes
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright
from memory_probe_18373 import MemoryProbe18373, chromium_memory_args
from test_long_career_memory_browser_18373 import inject_hooks
from test_vacation_resume_browser_18369 import browser_path


HOOK = r'''
/* TEST_ONLY_SEASON_JOB_OFFERS_18374 */
window.__seasonOffers374={done:false,result:null,phase:'startup',progress:[],expected:null,
 identity(){return window.__longCareer373.identity();},
 snapshot(){return {...window.__longCareer373.snapshot(),phase:this.phase,done:this.done,
  elapsed:state?E.unemployedRounds18374(state):null,offers:(state?.v636CoachOffers||[]).map(o=>({
   id:o.id,teamId:o.teamId,year:o.year,day:o.day,expiresDay:o.expiresDay,status:o.status}))};},
 shell(){
  const app=document.getElementById('app');if(!app)return;
  app.innerHTML='<main style="padding:32px"><h1>Carreira de teste · 2031</h1>'+
   '<p>Treinador livre desde o encerramento de 2030. Calendário e mercado originais.</p>'+
   button('v89-job-wait','Até o fim / proposta','primary','id="season-jobwait-374"')+
   button('v636-open-job-offers','Propostas','secondary','id="season-offers-374"')+
   button('futbr125-exit-game','Salvar e sair','secondary','id="season-exit-374"')+'</main>';
  v18363PaintJobButtons(document);
 },
 async prepare(){
  if(state||window.__namedMemory373.snapshot().entries.length)throw Error('Expected isolated empty save profile');
  v548Session={username:'isolated-season-offers-18374',plan:'premium'};render=()=>this.shell();
  const baseToast=toast;toast=(...args)=>{window.__longCareer373.notices.push(args.map(String).join(' '));return baseToast(...args);};
  this.phase='preparing-legacy-2031';window.__longCareer373.phase=this.phase;
  const picked=WorldCatalog.clubs.find(t=>/le havre/i.test(t.name));
  if(!picked)throw Error('The original club catalog has no Le Havre');
  state=E.createCareer({club:picked.id,manager:'Carreira após demissão no fim do ano',seed:183742031,difficulty:'normal'});
  const titleholders=[],used=new Set();
  for(const c of Object.values(state.competitions||{})){
   if(!['UEFA','CONMEBOL','CONCACAF','AFC','CAF','OFC'].includes(c.conf))continue;
   const champion=(c.participants||[]).find(id=>!used.has(id)&&E.team(state,id));
   if(champion){titleholders.push({year:2030,id:c.id,name:c.name,conf:c.conf,champion});used.add(champion);}
  }
  state.internationalHistory=titleholders;state.year=2031;E.setupSeason(state);
  state.v1903CareerId='integration-season-job-offers-18374';state.live=null;
  state.vacation.active=false;state.vacation.paused=true;
  v636CoachState(state);v636EnsureTracker(state);
  v622Settings(state).renewals='board';v18371CommitSettings(state);
  const oldLastDay=Math.max(137,state.schedule.length)-1,club=E.team(state,state.user),me=state.coaches[state.userCoachId];
  // Execute the real departure and replacement logic. Only the save's old
  // timestamp and current date are inputs to reproduce the user's legacy save.
  state.year=2030;state.day=oldLastDay;E.dismissCoach(state,club,'Contrato encerrado no fim da temporada de teste');
  me.unemployedSince={year:2030,day:oldLastDay};
  state.year=2031;state.day=33;state.lastDay=32;state.seasonDone=false;
  state.v636CoachOffers=[];state.v636CoachOfferMeta={lastOfferDay:oldLastDay-2,rejected:{}};
  state.vacation.active=false;state.vacation.paused=true;
  // Prior vacancy pressure is explicit fixture input; candidates and the
  // actual invitation are still chosen by the production eligibility policy.
  let compatibleBoards=0;
  for(const t of state.teams)if(t.id!==state.user&&t.country===club.country&&Number(t.division)===Number(club.division)&&
     Number(t.base)<=Number(me.reputation)+10){t.fanPressure=Math.max(60,Number(t.fanPressure)||0);compatibleBoards++;}
  E.prepareStage(state);
  saved=null;view='career';saveOK=true;v52SavePromise=null;v52SaveDirty=false;v52PendingState=null;
  v53Sim.active=false;v53Sim.starting=false;v53Sim.syncing=false;v53Sim.patching=false;v53Sim.finished=null;
  window.__longCareer373.observeWorkers();
  const identity=this.identity();
  if(identity.players<180000||identity.teams<5000||identity.employed||me.clubId||!compatibleBoards)
   throw Error('Invalid complete legacy fixture: '+JSON.stringify(identity));
  this.initial={...identity,oldDismissal:{...me.unemployedSince},lastOfferDay:state.v636CoachOfferMeta.lastOfferDay,
   compatibleBoards,oldCoachReplaced:club.coachId!==me.id,calendarOriginal:true,priorSeasonsActuallySimulated:false,
   oldSaveInputs:true,authAndOuterShellIsolated:true};
  this.phase='initial-named-save';render();window.GestorFC.namedSaves125.save();return this.initial;
 },
 startSearch(){
  this.done=false;this.result=null;
  (async()=>{let timer=null;
   try{
    const before=this.identity(),initialStamp={...state.coaches[state.userCoachId].unemployedSince};
    this.phase='real-job-search';window.__longCareer373.phase=this.phase;
    render();const button=document.getElementById('season-jobwait-374');v18363PaintJobButtons(document);
    if(!button||button.disabled)throw Error('Actual job-search button disabled: '+v18363LastBlocker);
    const transport=window.__longCareer373.transport,startCount=transport.jobDays.length;
    button.click();
    timer=setInterval(()=>{
     const owner=window.GestorFC.jobWaitMemory18373.status();
     if(owner.ownsWorld&&transport.ownerSamples.length<100)transport.ownerSamples.push({phase:owner.phase,
      players:window.__longCareer373.count(state?.players),day:state?.day,year:state?.year});
    },100);
    const began=Date.now();
    while(v89JobWait.active||v18365Job.pending||v53Sim.active||v53Sim.starting||v53Sim.syncing||
      v52SavePromise||window.GestorFC.jobWaitMemory18373.status().ownsWorld){
     if(Date.now()-began>360000)throw Error('Original job search did not recover the legacy save');
     await new Promise(r=>setTimeout(r,25));
    }
    clearInterval(timer);timer=null;
    const after=this.identity(),offers=v636PendingCoachOffers(state).map(o=>({...o}));
    if(after.year!==2031||after.day<=before.day||after.day-before.day>8||!offers.length||
       transport.jobDays.length<=startCount)throw Error('No eligible offer within eight genuine rounds: '+JSON.stringify(this.snapshot()));
    if(after.career!==before.career||after.coachId!==before.coachId||after.employed||
       after.players!==before.players||after.teams!==before.teams||after.renewals!=='board')
      throw Error('Search changed the career, full world, or manager preferences');
    const me=state.coaches[state.userCoachId];
    if(me.unemployedSince.year!==initialStamp.year||me.unemployedSince.day!==initialStamp.day)
      throw Error('The legacy dismissal history was rewritten to fake elapsed time');
    for(const o of offers){const target=E.team(state,o.teamId);
     if(!target||target.id===state.user||target.base>Number(me.reputation||60)+10||o.expiresDay<state.day)
      throw Error('Offer violated the actual club/reputation policy');}
    const deadline=Date.now()+3000;
    while(!document.querySelector('#modal-root [data-action="v636-accept-job-offer"]')&&Date.now()<deadline)
     await new Promise(r=>setTimeout(r,20));
    if(!document.querySelector('#modal-root [data-action="v636-accept-job-offer"]'))throw Error('Original offer modal did not open');
    this.result={ok:true,before,after,offers,daysAdvanced:after.day-before.day,actualButtonClick:true,
     actualWorkerRounds:true,oldDismissalStampPreserved:true,automaticOfferModal:true,
     owner:window.GestorFC.jobWaitMemory18373.status(),memory:window.GestorFC.memoryStorage18373.status()};
   }catch(error){this.result={ok:false,error:String(error),stack:String(error.stack),snapshot:this.snapshot()};}
   finally{if(timer)clearInterval(timer);this.done=true;}
  })();return true;
 },
 startExit(){
  this.done=false;this.result=null;
  (async()=>{
   try{
    this.phase='save-offer-and-exit';window.__longCareer373.phase=this.phase;
    const close=document.querySelector('#modal-root [data-action="close"]');if(close)close.click();
    await new Promise(r=>setTimeout(r,60));
    const offers=(state.v636CoachOffers||[]).map(o=>({id:o.id,teamId:o.teamId,year:o.year,day:o.day,expiresDay:o.expiresDay,status:o.status}));
    if(!offers.length)throw Error('Deferring removed the offer');
    this.expected={world:window.__longCareer373.worldAudit(),offers,meta:JSON.stringify(state.v636CoachOfferMeta)};
    render();document.getElementById('season-exit-374').click();
    const confirm=document.querySelector('#modal-root [data-action="futbr125-save-and-exit"]');
    if(!confirm)throw Error('Original save-and-exit dialog missing');confirm.click();
    const began=Date.now();
    while(state||window.__namedMemory373.snapshot().busy){
     if(Date.now()-began>180000)throw Error('Named save and exit did not finish');
     await new Promise(r=>setTimeout(r,25));
    }
    this.result={ok:true,actualSaveExitClick:true,manifest:await window.__namedMemory373.manifest(),expected:this.expected};
   }catch(error){this.result={ok:false,error:String(error),stack:String(error.stack),snapshot:this.snapshot()};}
   finally{this.done=true;}
  })();return true;
 },
 verifyReload(){
  const world=window.__longCareer373.worldAudit(),offers=(state?.v636CoachOffers||[]).map(o=>({
   id:o.id,teamId:o.teamId,year:o.year,day:o.day,expiresDay:o.expiresDay,status:o.status}));
  if(JSON.stringify(world)!==JSON.stringify(this.expected.world)||JSON.stringify(offers)!==JSON.stringify(this.expected.offers)||
    JSON.stringify(state.v636CoachOfferMeta)!==this.expected.meta)throw Error('Named reload changed the saved world, offers, or dated clock');
  render();document.getElementById('season-offers-374').click();
  return {ok:true,world,offers,datedClockPreserved:true,twentyCollectionsPreserved:true,actualNamedLoader:true};
 },
 async verifyAcceptance(offer){
  if(!state?.userEmployed||state.user!==offer.teamId||state.coaches[state.userCoachId].clubId!==offer.teamId||
    v622Settings(state).renewals!=='board'||(state.v636CoachOffers||[]).length)throw Error('Original offer acceptance failed');
  await v52FlushSave();if(v52SavePromise)await v52SavePromise;
  return {ok:true,actualOfferAcceptance:true,identity:this.identity(),manifest:await window.__namedMemory373.manifest()};
 }
};
'''


def inject(source: str) -> str:
    assert 'FUTBR_UNEMPLOYED_CALENDAR_18374' in source
    assert 'TEST_ONLY_SEASON_JOB_OFFERS_18374' not in source
    html = inject_hooks(source)
    start = html.index('let state=null,saved=null')
    end = html.index('</script>', start)
    anchor = html.rfind('})();', start, end)
    assert start < anchor < end
    return html[:anchor] + '\n' + HOOK + '\n' + html[anchor:]


def wait_flow(page, probe, limit=400):
    deadline = time.monotonic() + limit
    last = None
    while time.monotonic() < deadline:
        page.wait_for_timeout(1500)
        snap = page.evaluate('() => window.__seasonOffers374.snapshot()')
        probe.mark(page, snap['phase'])
        if snap['phase'] != last or snap['done']:
            print('18.374 JOB MARKET ' + json.dumps(snap, ensure_ascii=False), flush=True)
            last = snap['phase']
        if snap['done']:
            result = page.evaluate('() => window.__seasonOffers374.result')
            if not result or not result.get('ok'):
                raise RuntimeError('Actual legacy job search failed: ' + json.dumps(result, ensure_ascii=False))
            return result
    raise TimeoutError('Legacy job-search browser flow exceeded its limit')


def main() -> None:
    root = Path(sys.argv[1]).resolve()
    source = (root / 'src/index.html').read_text(encoding='utf-8')
    html = inject(source)
    artifacts = root / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    result = {'ok': False, 'version': '18.374.0', 'sourceSha256': hashlib.sha256(source.encode('utf-8')).hexdigest()}
    errors, dialogs, crashes = [], [], []
    phase = 'startup'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=browser_path(), headless=True,
            args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox', *chromium_memory_args()])
        probe = MemoryProbe18373(browser).start()
        context = browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append({'phase': phase, 'message': str(e)}))
        page.on('crash', lambda: crashes.append({'phase': phase}))

        def native_dialog(dialog):
            dialogs.append({'phase': phase, 'message': dialog.message})
            dialog.dismiss()

        page.on('dialog', native_dialog)

        def route(route):
            req = urlsplit(route.request.url)
            if req.netloc != 'season-offers-18374.test':
                route.abort()
                return
            relative = unquote(req.path).lstrip('/')
            if relative in ('', 'index.html'):
                route.fulfill(status=200, content_type='text/html; charset=utf-8', body=html)
                return
            path = (root / 'src' / relative).resolve()
            if path.is_file() and (root / 'src').resolve() in path.parents:
                route.fulfill(path=str(path), content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
            else:
                route.fulfill(status=404, body='not found')

        page.route('**/*', route)
        try:
            page.goto('https://season-offers-18374.test/', wait_until='domcontentloaded', timeout=120000)
            page.wait_for_function('() => !!window.__seasonOffers374&&!!window.GestorFC?.namedSaves125', timeout=120000)
            page.wait_for_timeout(1000)
            phase = 'legacy-save-fixture'
            result['initial'] = page.evaluate('() => window.__seasonOffers374.prepare()')
            page.locator('#futbr125-save-name').fill('Retomada de carreira 2031')
            page.locator('[data-action="futbr125-save-current"]').click()
            page.wait_for_function('''() => {const s=window.__namedMemory373.snapshot();
              return !s.busy&&s.entries.length===1&&s.modalKind!=='futbr125-save';}''', timeout=240000)
            phase = 'job-search'
            page.evaluate('() => window.__seasonOffers374.startSearch()')
            result['search'] = wait_flow(page, probe)
            page.screenshot(path=str(artifacts / 'season-job-offer-18374.png'))
            phase = 'save-and-exit'
            page.evaluate('() => window.__seasonOffers374.startExit()')
            result['exit'] = wait_flow(page, probe)
            phase = 'named-reload'
            page.evaluate('() => window.GestorFC.namedSaves125.open()')
            page.locator('[data-action="futbr125-load"]').click()
            page.wait_for_function('''() => {const s=window.__namedMemory373.snapshot();
              return s.hasState&&!s.busy&&s.modalKind!=='futbr125-list';}''', timeout=240000)
            result['reload'] = page.evaluate('() => window.__seasonOffers374.verifyReload()')
            phase = 'offer-acceptance'
            page.locator('[data-action="v636-accept-job-offer"]').first.click()
            result['accepted'] = page.evaluate('(offer) => window.__seasonOffers374.verifyAcceptance(offer)', result['reload']['offers'][0])
            result['transport'] = page.evaluate('() => window.__longCareer373.transport')
            t = result['transport']
            flags = {
                'legacy2031SaveRecovered': result['search']['daysAdvanced'] <= 8,
                'fullOriginalWorld': result['initial']['players'] >= 180000 and result['initial']['teams'] >= 5000,
                'actualJobSearchButtonAndWorker': result['search']['actualButtonClick'] and bool(t['jobDays']),
                'compactWorkerTransportPreserved': t['fullWorldJobDays'] == 0 and all(d['uiPlayers'] == 0 for d in t['jobDays']),
                'zeroWholeWorldSaveTransfers': t['fullWorldSaves'] == 0,
                'completeWorldReturnedWithoutRecovery': result['search']['owner']['recoveries'] == 0,
                'oldDismissalHistoryPreserved': result['search']['oldDismissalStampPreserved'],
                'automaticOfferModal': result['search']['automaticOfferModal'],
                'offerAndDatedClockSurviveNamedReload': result['reload']['datedClockPreserved'],
                'twentySavedCollectionsPreserved': result['reload']['twentyCollectionsPreserved'],
                'realOfferAcceptedAndSaved': result['accepted']['actualOfferAcceptance'] and result['accepted']['manifest']['user'] == result['accepted']['identity']['club'],
                'boardRenewalsFollowNewClub': result['accepted']['identity']['renewals'] == 'board',
                'testHooksNotShipped': True,
            }
            result.update(flags)
            assert all(flags.values()), 'Season job-offer browser invariant failed: ' + json.dumps(flags)
            assert not dialogs and not crashes
            assert not [e for e in errors if e['phase'] != 'startup'], 'Runtime errors: ' + json.dumps(errors)
            result['ok'] = True
        except Exception as error:
            result['error'] = str(error)
            try:
                result['failureState'] = page.evaluate('() => window.__seasonOffers374?.snapshot?.()')
                result['failureTransport'] = page.evaluate('() => window.__longCareer373?.transport')
                page.screenshot(path=str(artifacts / 'season-job-offers-18374-failure.png'))
            except Exception as diagnostic:
                result['diagnosticError'] = str(diagnostic)
        finally:
            result['memory'] = probe.finish()
            probe.write_trace(artifacts / 'season-job-offers-18374-memory.jsonl')
            result['withinMeasuredMemoryBudget'] = result['memory']['ok']
            result['ok'] = bool(result['ok'] and result['withinMeasuredMemoryBudget'])
            result['errors'], result['nativeDialogs'], result['crashes'] = errors, dialogs, crashes
            (root / 'season-job-offers-browser-18374-tests.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            browser.close()
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if not result['ok']:
        raise SystemExit('18.374 legacy unemployed-save integration failed')


if __name__ == '__main__':
    main()
