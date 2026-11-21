"""Real club UI clicks, Engine match, vacation Worker and durable save/reload."""
from __future__ import annotations

import hashlib
import json
import mimetypes
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright
from test_vacation_resume_browser_18369 import browser_path


HOOK = r'''
/* TEST_ONLY_CLUB_MANAGEMENT_18374 */
window.__clubManagement374={notices:[],progress:[],
 snapshot(){const t=state&&E.team(state,state.user);return {year:state?.year,day:state?.day,club:state?.user,
  career:state?.v1903CareerId,balance:t?.balance,players:Object.keys(state?.players||{}).length,teams:state?.teams?.length,
  levels:t?Object.fromEntries(Object.keys(E.managementAreas18374).map(k=>[k,E.facilityLevel18374(t,k)])):null,
  management:t?.management18374?JSON.parse(JSON.stringify(t.management18374)):null,
  ledger:(t?.ledger||[]).slice(0,25).map(x=>({...x})),live:!!state?.live,modalKind,
  sim:{active:!!v53Sim?.active,starting:!!v53Sim?.starting,syncing:!!v53Sim?.syncing}};},
 setup(){
  v548Session={username:'management-integration-18374',plan:'premium'};
  // Account and outer-shell network setup are isolated; clubPage, modals,
  // original click/change handlers, Engine, Worker and storage are untouched.
  render=()=>document.getElementById('app');
  const s=E.createCareer({club:'t0',manager:'Teste de gestão',seed:183742026,difficulty:'normal'});
  state=s;saved=null;view='club';saveOK=true;v52SavePromise=null;v52SaveDirty=false;v52PendingState=null;
  state.live=null;state.vacation.active=false;state.vacation.paused=true;
  state.v1903CareerId='club-management-integration-18374';v636CoachState(state);
  v53Sim.active=false;v53Sim.starting=false;v53Sim.syncing=false;v53Sim.patching=false;v53Sim.finished=null;
  const t=E.human(state);t.balance=500000000;t.trainingLevel=5;t.youthLevel=5;t.medicalLevel=5;
  // A legacy fully developed club is the input. Investments and progress are
  // created by real button clicks and original completed rounds below.
  const day=state.schedule.findIndex(d=>d.type==='league'&&d.fixtures?.some(f=>f.home===state.user||f.away===state.user));
  if(day<0)throw Error('Original calendar has no league match');state.day=day;state.lastDay=day?day-1:null;E.prepareStage(state);
  const baseToast=toast;toast=(...args)=>{this.notices.push(args.map(String).join(' '));return baseToast(...args);};
  render=()=>{const app=document.getElementById('app');if(!state)return app;app.innerHTML=v555ShellHTML();document.body.classList.add('v570-club-finance-view');
   const page=document.getElementById('v555-page');page.innerHTML=clubPage();
   const title=app.querySelector('.v555-club-top');if(title)title.innerHTML=`<strong>${esc(E.human(state)?.name||'Sem clube')}</strong><span class="tiny muted">${state?.year} · Jornada ${Number(state?.day)+1}</span>`;
   return app;};
  render();this.progress.push('fixture');return this.snapshot();
 },
 quote(type){return E.managementQuote18374(state,E.human(state),type);},
 async flush(){await v52FlushSave();if(v52SavePromise)await v52SavePromise;if(!saveOK)throw Error('Storage flush failed');return this.snapshot();},
 async manualRound(){
  await this.flush();const before=this.snapshot(),day=state.day,year=state.year;
  E.kickoff(state);E.finishMatch(state,state.live);
  if(state.live?.status!=='finished')throw Error('Original match did not finish');
  const sync=v552StartPostMatchSync();if(!sync)throw Error('Original post-match sync refused the game');
  await sync;if(!v552RoundSync.done||v552RoundSync.error)throw Error('Original post-match Worker failed');
  await this.flush();render();const after=this.snapshot(),t=E.human(state);
  const charges=t.ledger.filter(l=>l.year===year&&l.day===day&&l.category==='Manutenção');
  if(after.day!==before.day+1||charges.length!==1)throw Error('Manual round did not charge one finance pass: '+JSON.stringify({before,after,charges}));
  this.progress.push('manual-round');return {ok:true,before,after,maintenanceCharges:charges.length};
 },
 async vacationRound(){
  await this.flush();const before=this.snapshot(),day=state.day,year=state.year,stage=state.schedule[day]?.type;
  E.startVacation(state,1,false);await v53StartSimulation('vacation',{liveStateNoPreSave:true});
  await this.flush();render();const after=this.snapshot(),t=E.human(state),charges=t.ledger.filter(l=>l.year===year&&l.day===day&&l.category==='Manutenção');
  if(after.day!==before.day+1||after.sim.active||after.sim.syncing)throw Error('Vacation did not return exactly one completed round');
  if(!['world','national'].includes(stage)&&charges.length!==1)throw Error('Vacation round did not charge one finance pass');
  this.progress.push('vacation-round');return {ok:true,before,after,stage,maintenanceCharges:charges.length};
 },
 async reload(){
  await this.flush();const before=this.snapshot();state=null;saved=null;
  const loaded=await v53Call('load',{key:STORE});if(!loaded?.players||!loaded?.teams)throw Error('Original loader returned incomplete state');
  state=loaded;saved=loaded;view='club';render();const after=this.snapshot();
  for(const key of ['year','day','club','career','balance','players','teams','levels','management']){
   if(JSON.stringify(before[key])!==JSON.stringify(after[key]))throw Error('Durable load changed '+key);
  }this.progress.push('reload');return {ok:true,before,after};
 },
 hiddenForNational(){const before=state.v640National?.userTeam;state.v640National??={};state.v640National.userTeam='BRA';const html=clubPage();state.v640National.userTeam=before||null;return !html.includes('data-facility=')&&html.includes('Assuma um clube');},
 layout(){const rows=[...document.querySelectorAll('.v18374-facility')];return {cards:rows.length,
  pageWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,
  cardMinWidth:Math.min(...rows.map(x=>x.getBoundingClientRect().width)),
  overflowRows:rows.filter(x=>x.scrollWidth>x.clientWidth+2).length,
  scrollArea:!!document.querySelector('.v18374-club-scroll'),progress:this.progress.slice()};}
};
'''


def inject(source):
    assert 'FUTBR_CLUB_MANAGEMENT_UI_18374' in source
    assert 'TEST_ONLY_CLUB_MANAGEMENT_18374' not in source
    start=source.index('let state=null,saved=null');end=source.index('</script>',start)
    anchor=source.rfind('})();',start,end)
    assert start<anchor<end
    return source[:anchor]+'\n'+HOOK+'\n'+source[anchor:]


def main():
    root=Path(sys.argv[1]).resolve();source=(root/'src/index.html').read_text(encoding='utf-8')
    artifacts=root/'artifacts';artifacts.mkdir(exist_ok=True)
    html=inject(source);errors=[];dialogs=[];phase='startup'
    result={'ok':False,'version':'18.374.0','sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest()}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path=browser_path(),headless=True,
            args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox'])
        context=browser.new_context(viewport={'width':1440,'height':980})
        page=context.new_page();page.set_default_timeout(30000)
        page.on('pageerror',lambda e:errors.append({'phase':phase,'message':str(e)[:1800]}))
        def native_dialog(d):
            dialogs.append({'type':d.type,'message':d.message});d.dismiss()
        page.on('dialog',native_dialog)
        def route(request):
            u=urlsplit(request.request.url)
            if u.hostname=='localhost' and request.request.resource_type=='document':
                request.fulfill(status=200,content_type='text/html; charset=utf-8',body=html);return
            if u.hostname=='localhost' and unquote(u.path).startswith('/assets/'):
                path=root/'src'/unquote(u.path).lstrip('/');asset_root=(root/'src/assets').resolve()
                if path.is_file() and path.resolve().is_relative_to(asset_root):
                    request.fulfill(path=str(path),content_type=mimetypes.guess_type(path)[0] or 'application/octet-stream');return
            request.abort()
        page.route('**/*',route)
        try:
            page.goto('http://localhost:8746/',wait_until='domcontentloaded',timeout=180000)
            page.wait_for_function('()=>!!window.__clubManagement374',timeout=90000)
            page.wait_for_timeout(1800);phase='management'
            initial=page.evaluate('()=>window.__clubManagement374.setup()');result['initial']=initial
            assert initial['levels']['training']==5 and initial['teams']>5000 and initial['players']>180000
            assert page.locator('.v18374-facility').count()==8
            quote=page.evaluate('()=>window.__clubManagement374.quote("training")')
            page.locator('[data-action="upgrade"][data-upgrade="training"]').click()
            page.locator('[data-action="v18374-start-project"]').wait_for(state='visible')
            assert 'jornadas' in page.locator('#modal-root').inner_text()
            page.screenshot(path=str(artifacts/'club-investment-confirmation-18374.png'),full_page=True)
            page.locator('[data-action="v18374-start-project"]').click()
            started=page.evaluate('()=>window.__clubManagement374.snapshot()')
            assert started['balance']==initial['balance']-quote['cost']
            assert started['levels']['training']==5 and started['management']['projects'][0]['remaining']==quote['duration']
            commercial=page.evaluate('()=>window.__clubManagement374.quote("commercial")')
            page.locator('[data-action="upgrade"][data-upgrade="commercial"]').click()
            page.locator('[data-action="v18374-start-project"]').click()
            two=page.evaluate('()=>window.__clubManagement374.snapshot()')
            assert len(two['management']['projects'])==2
            assert page.locator('[data-action="upgrade"][data-upgrade="youth"]').is_disabled()
            result['manualRound']=page.evaluate('()=>window.__clubManagement374.manualRound()')
            manual=result['manualRound']['after']
            by_type={p['type']:p for p in manual['management']['projects']}
            assert by_type['training']['remaining']==quote['duration']-1
            assert by_type['commercial']['remaining']==commercial['duration']-1
            result['firstReload']=page.evaluate('()=>window.__clubManagement374.reload()')
            result['vacationRound']=page.evaluate('()=>window.__clubManagement374.vacationRound()')
            vacation=result['vacationRound']['after'];projects={p['type']:p for p in vacation['management']['projects']}
            assert projects['training']['remaining']==quote['duration']-2
            assert projects['commercial']['remaining']==commercial['duration']-2
            project=projects['commercial'];refund=int(project['cost']*project['remaining']/project['total']*.85)
            page.locator(f'[data-action="v18374-cancel-project"][data-project="{project["id"]}"]').click()
            page.locator('[data-action="v18374-confirm-cancel"]').wait_for(state='visible')
            # Dismissing this game modal preserves the project and cash.
            page.locator('#modal-root .modal-footer [data-action="close"]').click()
            kept=page.evaluate('()=>window.__clubManagement374.snapshot()')
            assert kept['balance']==vacation['balance'] and len(kept['management']['projects'])==2
            page.locator(f'[data-action="v18374-cancel-project"][data-project="{project["id"]}"]').click()
            page.locator('[data-action="v18374-confirm-cancel"]').click()
            cancelled=page.evaluate('()=>window.__clubManagement374.snapshot()')
            assert cancelled['balance']==vacation['balance']+refund
            assert len(cancelled['management']['projects'])==1 and cancelled['levels']['commercial']==1
            page.locator('#v18374-plan').select_option('development')
            result['finalReload']=page.evaluate('()=>window.__clubManagement374.reload()')
            assert result['finalReload']['after']['management']['plan']=='development'
            result['desktopLayout']=page.evaluate('()=>window.__clubManagement374.layout()')
            assert result['desktopLayout']['overflowRows']==0
            page.screenshot(path=str(artifacts/'club-management-18374.png'),full_page=True)
            page.set_viewport_size({'width':390,'height':844})
            result['mobileLayout']=page.evaluate('()=>window.__clubManagement374.layout()')
            assert result['mobileLayout']['overflowRows']==0
            assert result['mobileLayout']['scrollWidth']<=result['mobileLayout']['pageWidth']+2
            page.screenshot(path=str(artifacts/'club-management-mobile-18374.png'),full_page=True)
            assert page.evaluate('()=>window.__clubManagement374.hiddenForNational()')
            result.update(ok=True,originalClubRendererAndClickHandlers=True,realFullWorld=True,
                paymentAndNoInstantBenefitVerified=True,twoConcurrentProjectsEnforced=True,
                realManualMatchAndWorkerAdvanceProjectsOnce=True,realVacationWorkerAdvancesProjectsOnce=True,
                actualStorageReloadPreservesCostAndProgress=True,cancelModalKeepsProjectUntilConfirmed=True,
                proportionalRefundVerified=True,planChoiceSurvivesReload=True,nationalCoachCannotManageOldClub=True,
                desktopAndMobileLayoutsVerified=True,noNativeDialogs=not dialogs,testHooksNotShipped=True,
                authAndOuterShellIsolated=True)
        except Exception as error:
            result['error']=str(error)
            try:
                result['lastState']=page.evaluate('()=>window.__clubManagement374?.snapshot()')
                page.screenshot(path=str(artifacts/'club-management-failure-18374.png'),full_page=True)
            except Exception:pass
        finally:browser.close()
    result['nativeDialogs']=dialogs;result['flowErrors']=[e for e in errors if e['phase']!='startup'];result['startupErrors']=[e for e in errors if e['phase']=='startup'][-12:]
    if result['flowErrors'] or dialogs:result['ok']=False
    (root/'club-management-browser-18374-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('18.374 MANAGEMENT RESULT '+json.dumps(result,ensure_ascii=False),flush=True)
    if not result['ok']:raise RuntimeError('Club management browser regression failed')


if __name__=='__main__':main()
