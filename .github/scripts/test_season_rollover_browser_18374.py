"""A/B actual UI season rollover, then a post-final-round dismissal job search.

The full bundled catalog, original Engine, UI dispatcher, Worker and checkpoint
paths run unchanged. Season results/history are explicit fixtures, not a claim
that the complete 2026--2028 seasons were played. Component and full transition
timings are reported separately.
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
from test_vacation_resume_browser_18369 import browser_path


HOOK=r'''
/* TEST_ONLY_ROLLOVER_18374 */
window.__rollover374={phase:'startup',notices:[],finished:false,result:null,prepareMs:null,engineMs:null,
 digest(value){let h=2166136261,nodes=0;const put=x=>{const z=String(x);for(let i=0;i<z.length;i++){h^=z.charCodeAt(i);h=Math.imul(h,16777619);}};
  const visit=x=>{nodes++;if(x===null||typeof x!=='object'){put(typeof x+':'+String(x));return;}put(Array.isArray(x)?'array:'+x.length:'object');for(const k of Object.keys(x).sort()){put(k);visit(x[k]);}};
  visit(value);return {hash:h>>>0,nodes};},
 identity(){return {year:state?.year,day:state?.day,seasonDone:!!state?.seasonDone,club:state?.user,
  employed:state?.userEmployed,career:state?.v1903CareerId,players:Object.keys(state?.players||{}).length,
  teams:state?.teams?.length||0,renewals:state?v622Settings(state).renewals:null};},
 snapshot(){return {phase:this.phase,finished:this.finished,identity:this.identity(),prepareMs:this.prepareMs,engineMs:this.engineMs,
  sim:{active:v53Sim.active,starting:v53Sim.starting,syncing:v53Sim.syncing},creating:v53Creating,
  search:v89JobWait.active,offers:(state?.v636CoachOffers||[]).filter(o=>o.status==='pending'),notices:this.notices.slice(-4)};},
 shell(){const app=document.getElementById('app');if(!app)return;
  app.innerHTML='<main style="padding:32px"><h1>Virada de temporada · teste completo</h1>'+button('next-season','Próxima temporada','primary','id="rollover-next-374"')+
   button('v89-job-wait','Até o fim / proposta','primary','id="rollover-job-374"')+'</main>';
  try{v18363PaintJobButtons(document);}catch(e){}},
 async prepare(){
  v548Session={username:'isolated-rollover-18374',plan:'premium'};render=()=>this.shell();
  const bt=toast;toast=(...args)=>{this.notices.push(args.map(String).join(' '));return bt(...args);};
  state=E.createCareer({club:'t18',manager:'Virada completa 2028',seed:183742028,difficulty:'normal'});
  state.v1903CareerId='rollover-full-2028-2029';state.live=null;
  const template=Object.values(state.competitions||{}).filter(c=>['UEFA','CONMEBOL','CONCACAF','AFC','CAF','OFC'].includes(c.conf));
  state.internationalHistory=[];
  for(const year of [2026,2027]){const used=new Set();for(const c of template){
   const champion=(c.participants||[]).find(id=>!used.has(id)&&E.team(state,id));
   if(champion){used.add(champion);state.internationalHistory.push({year,id:c.id,name:c.name,conf:c.conf,champion,
    points:Object.fromEntries((c.participants||[]).map((id,i)=>[id,Math.max(0,40-i)]))});}
  }}
  state.year=2028;E.setupSeason(state);
  state.v555CareerArchive={};state.v538CareerArchive={};state.scorerArchive=[];state.allTimeStats={};state.competitionStats={};
  const clubs=new Map(state.teams.map(t=>[t.id,t]));let i=0,records=0;
  for(const year of [2026,2027]){const packed={n:{},p:{}},scores={};
   for(const pid in state.players){const p=state.players[pid],t=clubs.get(p.clubId);if(!t)continue;i++;
    const apps=20+i%18,goals=p.pos==='GOL'?0:i%12,assists=p.pos==='GOL'?0:i%8;
    packed.n[t.id]=t.name;packed.p[pid]=[t.id,apps,goals,assists,i%6,0].join('|');records++;
    if(i%3===0&&(goals||assists)){const key='league:'+t.country+':'+t.division;
     (scores[key]??={})[pid]={id:pid,name:p.name,natCode:p.natCode||'UNK',goals,assists,apps,minutes:apps*75,clubs:{[t.id]:t.name},byClub:{}};}
    if(i%12000===0)await new Promise(r=>setTimeout(r,0));
   }state.v555CareerArchive[year]=packed;state.scorerArchive.unshift({year,competitions:scores});
  }
  i=0;for(const pid in state.players){const p=state.players[pid],t=clubs.get(p.clubId);if(!t)continue;i++;
   const apps=20+i%18,goals=p.pos==='GOL'?0:i%12,assists=p.pos==='GOL'?0:i%8,key='league:'+t.country+':'+t.division;
   (state.competitionStats[key]??={})[pid]={id:pid,name:p.name,natCode:p.natCode||'UNK',goals,assists,apps,minutes:apps*75,clubs:{[t.id]:t.name},byClub:{[t.id]:{apps,goals,assists}}};
   state.allTimeStats[pid]={id:pid,name:p.name,natCode:p.natCode||'UNK',goals:goals*3,assists:assists*3,apps:apps*3,minutes:apps*225,clubs:{[t.id]:t.name}};
   p.apps=apps;p.goals=goals;p.assists=assists;
   if(i%12000===0)await new Promise(r=>setTimeout(r,0));
  }
  // Completed-season fixture: use real calendar/participants, deterministic
  // results and legitimate champions. The transition itself is unmodified.
  state.cupWinners={};for(const c of E.WorldCatalog.countries){const candidates=state.teams.filter(t=>t.country===c.id).sort((a,b)=>b.base-a.base);if(candidates.length)state.cupWinners[c.id]=candidates[0].id;}
  for(const t of state.teams)t.stats={p:38,w:15,d:8,l:15,gf:42,ga:41,pts:53,form:[]};
  for(const d of state.schedule){d.prepared=true;for(const f of d.fixtures||[])f.result={home:1,away:0,events:[],cardIds125:[]};}
  const used=new Set();for(const c of Object.values(state.competitions||{})){
   const champion=(c.participants||[]).find(id=>!used.has(id))||c.participants?.[0];
   if(!champion)continue;used.add(champion);c.champion=champion;c.played=20;
   const runner=c.participants.find(id=>id!==champion);if(runner)c.rounds.final=[{a:champion,b:runner,score:[1,0],winner:champion,results:[{home:1,away:0}]}];
  }
  for(const [key,div] of [['serieC',3],['serieD',4]]){const c=state.braLower?.[key];if(c){const ts=state.teams.filter(t=>t.country==='bra'&&Number(t.division)===div);c.champion=ts[0]?.id;c.runnerUp=ts[1]?.id;}}
  state.day=state.schedule.length;state.seasonDone=true;state.live=null;
  if(state.vacation){state.vacation.active=false;state.vacation.paused=true;}
  v622Settings(state).renewals='board';v18371CommitSettings(state);
  v636CoachState(state);v636EnsureTracker(state);
  const me=E.team(state,state.user);E.dismissCoach(state,me,'Demissão ao término da última jornada');
  if(state.userEmployed!==false)throw Error('Original dismissal did not free the manager');
  saved=state;saveOK=true;v52SavePromise=null;v52SaveDirty=false;v52PendingState=null;view='career';
  v53Sim.active=false;v53Sim.starting=false;v53Sim.syncing=false;v53Sim.patching=false;v53Sim.finished=null;
  this.before={...this.identity(),history:this.digest(state.v555CareerArchive),scorers:this.digest(state.scorerArchive),historyRecords:records,
   unemployedSince:{...state.coaches[state.userCoachId].unemployedSince},fixture:'Original catalog/calendar; synthetic completed-season results and 2026–2027 statistics'};
  const next=E.nextSeason,test=this;E.nextSeason=function(...args){const a=performance.now();try{return next.apply(this,args);}finally{test.engineMs=performance.now()-a;}};
  const prepare=v53Prepare;v53Prepare=async function(op,...args){if(op!=='next')return prepare.call(this,op,...args);const a=performance.now();test.phase='real-next-season';try{return await prepare.call(this,op,...args);}finally{test.prepareMs=performance.now()-a;test.finished=true;test.phase='rollover-returned';}};
  this.phase='ready';this.shell();return this.before;
 },
 rolloverAudit(){
  const prior={2026:state.v555CareerArchive?.[2026],2027:state.v555CareerArchive?.[2027]};
  const priorScores=(state.scorerArchive||[]).filter(x=>Number(x.year)<2028);
  return {ok:state.year===2029&&!state.seasonDone&&!v53Creating,identity:this.identity(),prepareMs:this.prepareMs,engineMs:this.engineMs,
   stages:{...v91Stats},rank:E.seasonRankAudit18374?.()||null,historyPreserved:this.digest(prior).hash===this.before.history.hash,
   scorersPreserved:this.digest(priorScores).hash===this.before.scorers.hash,
   archivedCurrentPlayers:Object.keys(state.v555CareerArchive?.[2028]?.p||{}).length,
   historyDigest:this.digest(state.v555CareerArchive),scorerDigest:this.digest(state.scorerArchive),
   calendarDigest:this.digest({schedule:state.schedule,competitions:state.competitions}),
   worldCup:E.worldAudit631(state),worldCupParticipants:state.competitions?.cwc?.participants,
   nationalCalendar:state.v735CalendarDates?.length||0,employed:state.userEmployed,
   fullWorldSave:false,saveState:window.GestorFC.memoryStorage18373?.status?.()};
 },
 startSearch(){this.phase='after-rollover-job-search';this.finished=false;this.searchStartDay=Number(state.day)||0;
  const b=document.getElementById('rollover-job-374');if(!b||b.disabled)throw Error('Job search control blocked after season rollover');b.click();},
 searchAudit(){const offers=(state.v636CoachOffers||[]).filter(o=>o.status==='pending');return {
  ok:offers.length>0&&!v89JobWait.active&&!v53Sim.active&&!v53Sim.starting&&!v53Sim.syncing,
  identity:this.identity(),offers,days:Number(state.day)-this.searchStartDay,rounds:E.unemployedRounds18374?.(state),
  owner:window.GestorFC.jobWaitMemory18373?.status?.(),renewals:v622Settings(state).renewals,
  historiesPresent:!!state.v555CareerArchive?.[2026]&&!!state.v555CareerArchive?.[2027]&&!!state.v555CareerArchive?.[2028]};}
};
'''


def inject(html: str) -> str:
    assert 'TEST_ONLY_ROLLOVER_18374' not in html
    start=html.index('let state=null,saved=null');end=html.index('</script>',start)
    at=html.rfind('})();',start,end);assert start<at<end
    return html[:at]+'\n'+HOOK+'\n'+html[at:]


def run(pw,root:Path,html:str,mode:str) -> dict:
    errors=[];dialogs=[];crashes=[];phase='startup';result={'ok':False,'mode':mode}
    browser=pw.chromium.launch(executable_path=browser_path(),headless=True,
        args=['--disable-gpu','--disable-dev-shm-usage','--no-sandbox',*chromium_memory_args()])
    probe=MemoryProbe18373(browser).start();context=browser.new_context(viewport={'width':1440,'height':1000});page=context.new_page()
    page.set_default_timeout(600000)
    page.on('pageerror',lambda e:errors.append({'phase':phase,'message':str(e)}));page.on('crash',lambda:crashes.append(phase))
    def dialog(d):dialogs.append(d.message);d.dismiss()
    page.on('dialog',dialog)
    body=inject(html)
    def route(r):
        u=urlsplit(r.request.url)
        if u.netloc!='rollover-18374.test':r.abort();return
        rel=unquote(u.path).lstrip('/')
        if rel in ('','index.html'):r.fulfill(status=200,content_type='text/html; charset=utf-8',body=body);return
        p=(root/'src'/rel).resolve()
        if p.is_file() and (root/'src').resolve() in p.parents:r.fulfill(path=str(p),content_type=mimetypes.guess_type(p.name)[0] or 'application/octet-stream')
        else:r.fulfill(status=404,body='not found')
    page.route('**/*',route)
    try:
        page.goto('https://rollover-18374.test/',wait_until='domcontentloaded',timeout=120000)
        page.wait_for_function('() => !!window.__rollover374',timeout=120000);page.wait_for_timeout(1000)
        phase='fixture';probe.mark(page,phase);result['before']=page.evaluate('() => window.__rollover374.prepare()')
        print('18.374 ROLLOVER '+mode+' fixture '+json.dumps(result['before'],ensure_ascii=False),flush=True)
        phase='actual-next-season-click';probe.mark(page,phase);page.locator('#rollover-next-374').click(timeout=600000)
        page.wait_for_function('() => window.__rollover374.finished',timeout=600000)
        phase='rollover-audit';probe.mark(page,phase);result['rollover']=page.evaluate('() => window.__rollover374.rolloverAudit()')
        print('18.374 ROLLOVER '+mode+' result '+json.dumps(result['rollover'],ensure_ascii=False),flush=True)
        assert result['rollover']['ok'],'Actual next-season dispatcher did not complete'
        assert result['rollover']['historyPreserved'] and result['rollover']['scorersPreserved'],'Historical statistics changed'
        assert result['rollover']['archivedCurrentPlayers']>150000,'Current player history was not archived'
        assert result['rollover']['worldCup']['groups']==[4]*8
        assert not result['rollover']['worldCup']['associationClashes'] and not result['rollover']['worldCup']['confederationClashes']
        if mode=='patched':
            phase='post-rollover-job-search';probe.mark(page,phase);page.evaluate('() => window.__rollover374.startSearch()')
            deadline=time.monotonic()+600
            while time.monotonic()<deadline:
                page.wait_for_timeout(1500);probe.mark(page,phase);a=page.evaluate('() => window.__rollover374.searchAudit()')
                if a['ok']:break
            else:raise TimeoutError('No job offer after rollover: '+json.dumps(page.evaluate('() => window.__rollover374.snapshot()')))
            result['jobSearch']=a
            assert 0<=a['days']<=8 and a['historiesPresent'] and a['renewals']=='board'
            assert a['owner']['recoveries']==0 and a['identity']['players']>150000
            page.screenshot(path=str(root/'artifacts/season-rollover-offer-18374.png'))
        assert not dialogs and not crashes
        assert not [e for e in errors if e['phase']!='startup'],'Flow errors: '+json.dumps(errors)
        result['ok']=True
    except Exception as e:
        result['error']=str(e)
        try:result['failureState']=page.evaluate('() => window.__rollover374?.snapshot?.()');page.screenshot(path=str(root/f'artifacts/season-rollover-18374-{mode}-failure.png'))
        except Exception as extra:result['diagnosticError']=str(extra)
    finally:
        result['memory']=probe.finish();probe.write_trace(root/f'artifacts/season-rollover-18374-{mode}-memory.jsonl')
        result['errors']=errors;result['nativeDialogs']=dialogs;result['crashes']=crashes;browser.close()
    return result


def main() -> None:
    if len(sys.argv)!=2:raise SystemExit('usage: test_season_rollover_browser_18374.py <project>')
    root=Path(sys.argv[1]).resolve();(root/'artifacts').mkdir(exist_ok=True)
    source=(root/'src/index.html').read_text(encoding='utf-8');baseline=(root/'baseline-18373.html').read_text(encoding='utf-8')
    result={'ok':False,'version':'18.374.0','sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
            'baselineSourceSha256':hashlib.sha256(baseline.encode('utf-8')).hexdigest()}
    with sync_playwright() as pw:
        result['baseline']=run(pw,root,baseline,'baseline')
        result['patched']=run(pw,root,source,'patched')
    a=result['baseline'];b=result['patched']
    flags={'actualNextSeasonUiAndEngine':a['ok'] and b['ok'],
        'fullOriginalCatalog':a.get('before',{}).get('players',0)>180000 and b.get('before',{}).get('players',0)>180000,
        'priorAndClosedSeasonHistoryPreserved':b.get('rollover',{}).get('historyPreserved',False) and b.get('rollover',{}).get('scorersPreserved',False),
        'sameCalendarParticipantsAndPots':a.get('rollover',{}).get('calendarDigest')==b.get('rollover',{}).get('calendarDigest') and a.get('rollover',{}).get('worldCupParticipants')==b.get('rollover',{}).get('worldCupParticipants'),
        'sameHistoricalArchives':a.get('rollover',{}).get('historyDigest')==b.get('rollover',{}).get('historyDigest') and a.get('rollover',{}).get('scorerDigest')==b.get('rollover',{}).get('scorerDigest'),
        'finalRoundDismissalReceivesNextYearOffer':b.get('jobSearch',{}).get('ok',False),
        'boundedOfferWaitAfterRollover':b.get('jobSearch',{}).get('days',999)<=8,
        'memoryBudgetPreserved':b.get('memory',{}).get('ok',False),
        'testHooksNotShipped':'TEST_ONLY_ROLLOVER_18374' not in source}
    if a['ok'] and b['ok']:
        result['fullTransitionSpeedup']=a['rollover']['prepareMs']/max(1,b['rollover']['prepareMs'])
        flags['fullTransitionFaster']=b['rollover']['prepareMs']<a['rollover']['prepareMs']*.85
    result.update(flags);result['ok']=all(flags.values())
    (root/'season-rollover-browser-18374-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['ok']:raise SystemExit('18.374 full season rollover browser regression failed')


if __name__=='__main__':main()
