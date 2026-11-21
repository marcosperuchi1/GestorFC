"""Real game dialogs and earned promotion offers in normal play and vacations.

Fixtures provide a prior good campaign and interested boards. The actual Engine
plays the next match, the original Worker consolidates it, and the real modal
and click dispatcher process the offer. No proposal/result/Worker is mocked.
"""
from __future__ import annotations

import json
import mimetypes
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright
from test_native_confirmations_18372 import TEST_HOOK, run_browser_ui
from test_vacation_resume_browser_18369 import browser_path


PROMOTION_HOOK = r'''
/* TEST_ONLY_PROMOTION_FLOW_18372 */
window.__promotion372={done:false,result:null,progress:[],notices:[],
 prepareIsolatedUI(){
  if(state)throw Error('UI test requires a new empty browser context');
  // Isolate account/network setup only. All game dialogs, guards, Engine,
  // Workers and storage continue to run their original implementations.
  v548Session={username:'isolated-ui-fixture-18372',plan:'premium'};
  render=()=>document.getElementById('app');
  return true;
 },
 snapshot(){
  const me=state?.coaches?.[state?.userCoachId],t=state&&E.team(state,state.user);
  return {career:String(state?.v1903CareerId||''),coachId:String(state?.userCoachId||''),
   clubId:state?.user,clubName:t?.name,year:state?.year,day:state?.day,
   employed:state?.userEmployed,coachClub:me?.clubId,renewals:state?v622Settings(state).renewals:null,
   profile:state?E.promotionProfile18372(state):null,
   offers:(state?.v636CoachOffers||[]).map(o=>({...o})),
   vacation:state?.vacation?{active:state.vacation.active,paused:state.vacation.paused,
    remaining:state.vacation.remaining,completed:state.vacation.completed,reason:state.vacation.reason}:null,
   sim:{active:!!v53Sim?.active,starting:!!v53Sim?.starting,syncing:!!v53Sim?.syncing,
    finished:!!v53Sim?.finished,mode:v53Sim?.mode},modalKind,
   players:Object.keys(state?.players||{}).length,teams:state?.teams?.length||0,
   jobs:(me?.jobs||[]).slice(0,4).map(j=>({...j})),rpc:v53RPC.size,
   checkpoint:{valid:!!v93VacCheckpointValid,year:v93VacCheckpointYear,day:v93VacCheckpointDay,
    directLoaderAvailable:typeof window.GestorFC?.v171?.loadDirect==='function'},
   guards:{processing:!!v52Processing,saving:!!v52SavePromise,
    awaitingPromotion:!!v18357AwaitingPromotion,vacationPromise:!!v18359VacationPromise}};
 },
 setup(mode){
  const club=E.WorldCatalog.clubs.find(c=>c.country==='bra'&&/chapecoense/i.test(c.name))||
   E.WorldCatalog.clubs.filter(c=>c.country==='bra'&&Number(c.division)===2)
    .sort((a,b)=>Number(a.base)-Number(b.base))[0];
  if(!club)throw Error('No actual Brazilian development club in the game catalog');
  render=()=>document.getElementById('app');
  const baseToast=toast;toast=(...args)=>{this.notices.push(args.map(String).join(' '));
   return baseToast(...args);};
  state=E.createCareer({club:club.id,manager:'Teste de crescimento na carreira',
   seed:183722026,difficulty:'normal'});
  saved=null;view='squad';saveOK=true;v52SavePromise=null;v52SaveDirty=false;v52PendingState=null;
  v53Sim.active=false;v53Sim.starting=false;v53Sim.syncing=false;v53Sim.patching=false;v53Sim.finished=null;
  state.live=null;state.vacation.active=false;state.vacation.paused=true;
  v636CoachState(state);v636EnsureTracker(state);
  const me=state.coaches[state.userCoachId],current=E.team(state,state.user);
  // Inputs describe the campaign before the next real match. No result or
  // offer is assigned by this test, and club/player strength remains original.
  me.jobGames=18;me.recent=Array(10).fill(3);me.pressure=0;
  me.reputation=Math.max(Number(me.reputation)||0,Number(current.base)||0);
  current.fanPressure=0;
  let interestedBoards=0;
  for(const t of state.teams){
   if(t.id===current.id||Number(t.base)>Math.max(me.reputation,current.base)+8)continue;
   if(t.country===current.country&&Number(t.division)>Number(current.division))continue;
   const coach=E.coach(state,t);if(!coach)continue;
   coach.jobGames=20;coach.pressure=70;t.fanPressure=70;interestedBoards++;
  }
  const start=state.schedule.findIndex(stage=>stage.type==='league'&&
   stage.fixtures?.some(f=>f.home===state.user||f.away===state.user));
  if(start<0)throw Error('No real league match for the selected club');
  state.day=start;state.lastDay=start?start-1:null;E.prepareStage(state);
  if(!E.upcoming(state))throw Error('Original match preparation did not find the fixture');
  // Select a deterministic initial career identifier before its first save.
  // The production recruitment probability and hash are never overridden.
  let pulse=null;
  for(let n=0;n<1000;n++){
   state.v1903CareerId='integration-promotion-18372-'+mode+'-'+n;
   pulse=E.promotionPulse18372({...state,day:Number(state.day)+1});
   if(pulse.roll<18)break;
  }
  if(!pulse||pulse.roll>=18)throw Error('No deterministic recruitment pulse for the fixture');
  const candidates=E.promotionJobs18372(state);
  if(!candidates.length)throw Error('The real world has no eligible superior interested club');
  v622Settings(state).renewals='board';v18371CommitSettings(state);
  const snapshot=this.snapshot();
  this.initial={...snapshot,mode,interestedBoards,pulse,
   candidates:candidates.map(t=>({id:t.id,name:t.name,base:t.base,division:t.division,country:t.country})),
   fixtureInputsOnly:true};
  this.progress=[{stage:'fixture-ready',snapshot}];
  return this.initial;
 },
 observeManualStorage373(){
  if(!window.GestorFC?.memoryStorage18373)return false;
  const original=v53GetWorker,ids=new WeakMap(),events=[];let seq=0;
  this.manualStorageProbe={events,idOf:worker=>worker?ids.get(worker)||null:null};
  v53GetWorker=function(...args){return original.apply(this,args).then(worker=>{
   if(ids.has(worker))return worker;const id=++seq;ids.set(worker,id);
   const send=worker.postMessage,terminate=worker.terminate;
   worker.postMessage=function(message,...rest){
    if(message?.op==='settle-storage-18373'||message?.op==='prime-manual')
     events.push({kind:'send',op:message.op,worker:id,pending:!!worker.v18373CheckpointBusy});
    return send.call(this,message,...rest);
   };
   worker.terminate=function(...args){events.push({kind:'terminate',worker:id,
    pending:!!worker.v18373CheckpointBusy});return terminate.apply(this,args);};
   return worker;
  });};return true;
 },
 async checkManualCleanFlush373(){
  const runtime=window.GestorFC?.memoryStorage18373;
  if(!runtime)return null;
  const probe=this.manualStorageProbe,worker=v53Worker,workerId=probe?.idOf(worker),
   before={pending:!!worker?.v18373CheckpointBusy,dirty:!!v52SaveDirty,
    uiSavePending:!!v52SavePromise,settlements:Number(runtime.status().cleanWorkerSettlements)||0,
    year:Number(state.year),day:Number(state.day),careerId:String(state.v1903CareerId||''),
    coachId:String(state.userCoachId||''),user:String(state.user||''),saveId:String(state.futbrSaveId||'')},
   eventStart=probe?.events.length||0;
  if(before.dirty)throw Error('Post-match fixture must reach a clean flush without inventing a UI edit.');
  // Exactly the original clean flush used before a named load. Do not add a
  // persist, edit flags or wait for a timer to hide a deferred-save race.
  await v52FlushSave();
  const manifest=await v52ReadRaw(STORE),root=manifest?.root,
   events=(probe?.events||[]).slice(eventStart),afterSettlements=Number(runtime.status().cleanWorkerSettlements)||0;
  if(manifest?.format!=='GFC_SHARDED_171'||Number(manifest.year)!==before.year||Number(manifest.day)!==before.day||
     Number(root?.year)!==before.year||Number(root?.day)!==before.day||
     String(root?.v1903CareerId||'')!==before.careerId||String(root?.userCoachId||'')!==before.coachId||
     String(root?.user||'')!==before.user||String(root?.futbrSaveId||'')!==before.saveId)
   throw Error('Clean flush returned before the manual checkpoint reached the current career/day.');
  const sent=events.findIndex(e=>e.kind==='send'&&e.op==='settle-storage-18373'&&e.worker===workerId),
   released=events.findIndex(e=>e.kind==='terminate'&&e.worker===workerId);
  if(before.pending&&(sent<0||released<=sent||afterSettlements<=before.settlements||v53Worker===worker))
   throw Error('A deferred manual save was not settled before releasing its Worker: '+JSON.stringify({before,events,afterSettlements}));
  this.manualSettlement={ok:true,originalCleanFlush:true,noExtraPersist:true,before,
   afterSettlements,events,settledBeforeRelease:before.pending?sent>=0&&released>sent:null,
   currentManifest:{format:manifest.format,year:manifest.year,day:manifest.day,
    careerId:root.v1903CareerId,coachId:root.userCoachId,user:root.user}};
  this.progress.push({stage:'manual-clean-flush-verified',report:this.manualSettlement});
  return this.manualSettlement;
 },
 start(mode){
  const initial=this.setup(mode);this.done=false;this.result=null;
  (async()=>{
   try{
    const before=Number(state.day);
    // A manually played match consolidates against the durable pre-match
    // world. Create it through the original save queue, as normal career
    // creation does; flushing an empty queue alone would be a no-op.
    this.progress.push({stage:'saving-initial-fixture'});
    const initialSave=persist();await v52FlushSave();await initialSave;
    if(v52SavePromise)await v52SavePromise;
    if(!saveOK||v52SaveDirty)throw Error('Original initial career save did not complete');
    this.progress.push({stage:'initial-fixture-saved'});
    if(mode==='normal'){
     this.observeManualStorage373();
     E.kickoff(state);E.finishMatch(state,state.live);
     if(state.live?.status!=='finished')throw Error('The original league match did not finish');
     this.progress.push({stage:'real-human-match-finished',fixtureId:state.live.fixtureId,
      status:state.live.status});
     const sync=v552StartPostMatchSync();
     if(!sync)throw Error('The original post-match command refused the finished match');
     await sync;
     if(!v552RoundSync.done||v552RoundSync.error)throw Error('The original post-match Worker did not settle');
     await this.checkManualCleanFlush373();
    }else{
     E.startVacation(state,24,false);
     await v53StartSimulation('vacation',{liveStateNoPreSave:true});
    }
    const after=this.snapshot(),offer=(state.v636CoachOffers||[]).find(o=>E.validPromotionOffer18372(state,o));
    this.progress.push({stage:'real-worker-settled',snapshot:after});
    if(!offer||Number(state.day)<=before||!state.userEmployed||state.user!==initial.clubId)
     throw Error('No earned offer after the real completed match: '+JSON.stringify(after));
    if(v53Sim.active||v53Sim.syncing||v53Sim.finished)throw Error('Worker still owns the active world');
    const target=E.team(state,offer.teamId),promotion=offer.promotion18372;
    if(!target||!(promotion.toOVR>promotion.fromOVR)||target.id===state.user)
     throw Error('The proposed club is not an objective sporting improvement');
    if(mode==='vacation'&&(state.vacation.active||!state.vacation.paused||
      Number(state.vacation.remaining)<=0||Number(state.vacation.completed)<1))
     throw Error('Vacation failed to pause for the new offer with remaining days preserved');
    this.result={ok:true,mode,initial,after,offer:{...offer},target:{id:target.id,name:target.name,
     base:target.base,country:target.country,division:target.division,coachId:target.coachId},
     actualDaysAdvanced:Number(state.day)-before,originalEngineAndWorker:true,
     generatedAfterRealCompletedMatch:true,offerDidNotChangeEmployment:true,
     superiorClub:true,promotionPausedVacation:mode==='vacation',
     manualSettlement:this.manualSettlement||null};
   }catch(error){this.result={ok:false,mode,error:String(error),stack:String(error.stack),
     initial,progress:this.progress,snapshot:this.snapshot(),notices:this.notices};}
   finally{this.done=true;}
  })();return initial;
 },
 renderCareer(){view='career';document.getElementById('app').innerHTML=careerPage();return this.snapshot();},
 async reload(){
  const before=this.snapshot();
  // Keep only compact identities/offer data while the original loader reads
  // the durable world. No whole-world test copy is retained across this read.
  state=null;saved=null;
  const loaded=await Promise.race([v53Call('load',{key:STORE}),
   new Promise((_,reject)=>setTimeout(()=>reject(Error('Reload exceeded 120 seconds')),120000))]);
  if(!loaded?.players||!loaded.teams||!loaded.schedule||!loaded.competitions)
   throw Error('Original storage reader returned an incomplete career');
  state=loaded;saved=loaded;view='career';
  const after=this.snapshot();
  for(const key of ['career','coachId','clubId','year','day','employed','renewals','players','teams'])
   if(before[key]!==after[key])throw Error('Reload changed '+key+': '+JSON.stringify({before,after}));
  const beforeOffers=before.offers.map(o=>o.id),afterOffers=after.offers.map(o=>o.id);
  if(JSON.stringify(beforeOffers)!==JSON.stringify(afterOffers))throw Error('Reload lost the earned offer');
  v636CoachOfferModal(true);
  return {ok:true,before,after};
 },
 async verifyAccepted(oldOffer){
  const current=this.snapshot();
  if(current.clubId!==oldOffer.teamId||current.coachId!==this.initial.coachId||
    current.career!==this.initial.career||!current.employed||current.coachClub!==oldOffer.teamId||
    current.renewals!=='board'||current.offers.length||current.vacation?.active)
   throw Error('Acceptance did not preserve the manager career/preferences: '+JSON.stringify(current));
  if(E.validPromotionOffer18372(state,oldOffer))throw Error('The prior employment invitation remained actionable');
  const target=E.team(state,state.user);
  if(target.coachId!==state.userCoachId)throw Error('Original Engine did not hire the manager at the target');
  await Promise.race([(async()=>{await v52FlushSave();if(v52SavePromise)await v52SavePromise;})(),
   new Promise((_,reject)=>setTimeout(()=>reject(Error('Acceptance save exceeded 120 seconds')),120000))]);
  return {ok:true,snapshot:this.snapshot(),currentInvitationConsumed:true,
   careerPreserved:true,settingsPreserved:true,originalJobTransition:true};
 },
 rejectedSnapshot(){const s=this.snapshot();return {...s,meta:state.v636CoachOfferMeta};}
};
'''


def inject_test_hooks(html: str) -> str:
    assert 'FUTBR_NATIVE_CONFIRMATIONS_18372_BEGIN' in html
    assert 'FUTBR_CAREER_PROMOTION_OFFERS_18372' in html
    assert 'TEST_ONLY_PROMOTION_FLOW_18372' not in html
    save_anchor = 'G.namedSaves125={list:'
    assert html.count(save_anchor) == 1
    html = html.replace(save_anchor, TEST_HOOK + '\n' + save_anchor, 1)
    start = html.index('let state=null,saved=null')
    end = html.index('</script>', start)
    anchor = html.rfind('})();', start, end)
    assert start < anchor < end
    return html[:anchor] + '\n' + PROMOTION_HOOK + '\n' + html[anchor:]


def wait_round(page, mode):
    initial = page.evaluate('(mode)=>window.__promotion372.start(mode)', mode)
    print('18.372 INITIAL ' + json.dumps(initial, ensure_ascii=False), flush=True)
    for _ in range(100):
        page.wait_for_timeout(4000)
        progress = page.evaluate('''()=>({done:window.__promotion372.done,
          stages:window.__promotion372.progress.map(x=>x.stage),snapshot:window.__promotion372.snapshot()})''')
        print('18.372 PROGRESS ' + json.dumps(progress, ensure_ascii=False), flush=True)
        if progress['done']:
            break
    result = page.evaluate('()=>window.__promotion372.result')
    if not result:
        raise RuntimeError('Real promotion flow exceeded 400 seconds: ' + json.dumps(progress))
    if not result.get('ok'):
        raise RuntimeError('Real promotion flow failed: ' + json.dumps(result, ensure_ascii=False))
    page.locator('[data-action="v636-accept-job-offer"]').wait_for(state='visible', timeout=30000)
    result['automaticOfferModalVisible'] = True
    assert 'OVR do clube:' in page.locator('#modal-root').inner_text()
    return result


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_promotion_confirmations_browser_18372.py <project>')
    root = Path(sys.argv[1]).resolve()
    artifacts = root / 'artifacts'
    artifacts.mkdir(exist_ok=True)
    test_html = inject_test_hooks((root / 'src/index.html').read_text(encoding='utf-8'))
    errors, dialogs, console_errors = [], [], []
    result = {'ok': False, 'version': '18.372.0', 'phases': {}}
    phase = 'startup'

    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=browser_path(), headless=True,
            args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox'])

        def open_page(label):
            nonlocal phase
            phase = label + '-startup'
            context = browser.new_context(viewport={'width': 1380, 'height': 900})
            page = context.new_page()
            page.on('pageerror', lambda e: errors.append({'phase': phase, 'message': str(e)[:2400]}))
            page.on('console', lambda m: console_errors.append({'phase': phase, 'message': m.text[:1600]})
                if m.type == 'error' else None)

            def native_dialog(dialog):
                dialogs.append({'phase': phase, 'type': dialog.type, 'message': dialog.message})
                dialog.dismiss()

            page.on('dialog', native_dialog)

            def route(request):
                url = urlsplit(request.request.url)
                if url.hostname == 'localhost' and request.request.resource_type == 'document':
                    request.fulfill(status=200, content_type='text/html; charset=utf-8', body=test_html)
                    return
                if url.hostname == 'localhost' and unquote(url.path).startswith('/assets/'):
                    path = root / 'src' / unquote(url.path).lstrip('/')
                    asset_root = (root / 'src/assets').resolve()
                    if path.is_file() and path.resolve().is_relative_to(asset_root):
                        request.fulfill(path=str(path), content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream')
                        return
                request.abort()

            page.route('**/*', route)
            page.goto('http://localhost:8745/', wait_until='domcontentloaded', timeout=180000)
            page.wait_for_function('()=>!!window.__promotion372&&!!window.__nativeConfirm18372Test', timeout=90000)
            page.wait_for_timeout(1800)
            page.evaluate('()=>window.__promotion372.prepareIsolatedUI()')
            phase = label
            return context, page

        try:
            context, page = open_page('native-confirmation')
            result['phases']['native'] = run_browser_ui(page, artifacts)
            context.close()

            context, page = open_page('normal-promotion')
            normal = wait_round(page, 'normal')
            offer_id = normal['offer']['id']
            page.locator('#modal-root .modal-footer [data-action="close"]').click()
            page.wait_for_function('''id=>(window.__promotion372.snapshot().offers.find(o=>o.id===id)||{}).status==='deferred' ''', arg=offer_id)
            page.evaluate('()=>window.__promotion372.renderCareer()')
            page.locator('[data-action="v636-open-job-offers"]').click()
            page.locator('[data-action="v636-reject-job-offer"]').click()
            page.wait_for_function('()=>window.__promotion372.snapshot().offers.length===0')
            rejected = page.evaluate('()=>window.__promotion372.rejectedSnapshot()')
            assert rejected['clubId'] == normal['initial']['clubId'] and rejected['employed']
            assert normal['offer']['teamId'] in rejected['meta']['promotion18372']['rejected']
            normal['deferredAndReopenedViaCareerButton'] = True
            normal['rejectedThroughRealClick'] = True
            normal['rejectionKeepsCurrentClub'] = True
            result['phases']['normal'] = normal
            context.close()

            context, page = open_page('vacation-promotion')
            vacation = wait_round(page, 'vacation')
            page.screenshot(path=str(artifacts / 'promotion-offer-18372.png'), full_page=True)
            vacation['reload'] = page.evaluate('()=>window.__promotion372.reload()')
            page.locator('[data-action="v636-accept-job-offer"]').click()
            page.wait_for_function('id=>window.__promotion372.snapshot().clubId===id', arg=vacation['offer']['teamId'], timeout=30000)
            vacation['acceptance'] = page.evaluate('offer=>window.__promotion372.verifyAccepted(offer)', vacation['offer'])
            vacation['acceptedThroughRealClick'] = True
            result['phases']['vacation'] = vacation
            context.close()

            flags = {
                'realEngineAndWorkers': normal['originalEngineAndWorker'] and vacation['originalEngineAndWorker'],
                'normalMatchGeneratesPromotion': normal['generatedAfterRealCompletedMatch'],
                'manualCleanFlushHonorsDeferredSave': normal.get('manualSettlement') is None or normal['manualSettlement']['ok'],
                'vacationGeneratesPromotion': vacation['generatedAfterRealCompletedMatch'],
                'vacationPausesAtOffer': vacation['promotionPausedVacation'],
                'superiorClubRequired': normal['superiorClub'] and vacation['superiorClub'],
                'offersShownAutomatically': normal['automaticOfferModalVisible'] and vacation['automaticOfferModalVisible'],
                'deferAndRejectRealClicks': normal['deferredAndReopenedViaCareerButton'] and normal['rejectedThroughRealClick'],
                'offerSurvivesRealSaveReload': vacation['reload']['ok'],
                'promotionAcceptedThroughRealClick': vacation['acceptedThroughRealClick'],
                'careerAndPreferencesPreserved': vacation['acceptance']['careerPreserved'] and vacation['acceptance']['settingsPreserved'],
                'inGameDeleteModalRealClicks': result['phases']['native'].get('ok') is True,
                'noNativeDialogs': not dialogs,
                'testHookNotShipped': True,
            }
            result.update(flags)
            result['ok'] = all(flags.values())
        except Exception as error:
            result['error'] = str(error)
            result['failedPhase'] = phase
            try:
                result['lastPromotionState'] = page.evaluate('()=>window.__promotion372.snapshot()')
                page.screenshot(path=str(artifacts / 'promotion-confirmation-failure-18372.png'), full_page=True)
            except Exception:
                pass
        finally:
            browser.close()

    result['nativeDialogs'] = dialogs
    result['runtimeErrors'] = [e for e in errors if not e['phase'].endswith('-startup')]
    result['startupErrors'] = [e for e in errors if e['phase'].endswith('-startup')][-15:]
    result['consoleErrors'] = console_errors[-15:]
    if result['runtimeErrors'] or dialogs:
        result['ok'] = False
    (root / 'promotion-confirmations-browser-18372-tests.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print('18.372 RESULT ' + json.dumps(result, ensure_ascii=False), flush=True)
    if not result['ok']:
        raise RuntimeError('Real in-game confirmation/promotion regression failed')


if __name__ == '__main__':
    main()
