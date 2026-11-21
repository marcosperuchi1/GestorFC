"""Execute all shipped offer generators against rollover and legacy-save inputs.

The separate browser gate uses the full catalog, real Worker, original button,
offer modal, takeover and persisted reload. These tests deliberately isolate
calendar/cooldown policy and compare the exact 18.373 implementations.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def between(source: str, start: str, end: str) -> str:
    a = source.index(start)
    return source[a:source.index(end, a)]


def pieces(source: str) -> dict[str, str]:
    return {
        'helpers': between(source, '  function promotionHash18372(', '  function availableJobs(s){'),
        'jobs': between(source, '  function availableJobs(s){', '  /* FUTBR_CONTRACT_PREFERENCES_18371'),
        'state': between(source, 'function v636CoachState(s=state){', 'function v636ClubFromName('),
        'create': between(source, 'function v636CreateCoachOffer(s,t,reason){', 'function v636GenerateCoachOffer('),
        'primary': between(source, 'function v636GenerateCoachOffer(s,afterUserMatch=false){', 'function v636CoachOfferModal('),
        'v93': between(source, 'const v93BaseGenerateCoachOffer=v636GenerateCoachOffer;', '// Display the last completed vacation cash change'),
        'v181': between(source, ' const v181BaseGenerate=v636GenerateCoachOffer;', ' // Deciding later keeps every proposal visible'),
        'uiJobs': between(source, 'function v56ExceptionalWork(s){', 'E.availableJobs=v56AvailableJobs;'),
        'workerProgress': between(source, 'function v18373PublishJobProgress(){', 'function v18373ReleaseWorkerGraph(){'),
        'workerDelta': between(source, 'function v18373ApplyJobCoachDelta(delta){', 'function v18373JobTeam(t){'),
    }


HARNESS = r'''
const assert=require('node:assert/strict'),vm=require('node:vm');
const input=JSON.parse(require('node:fs').readFileSync(process.argv[2],'utf8'));
const prefix=`
 const clamp=(n,a,b)=>Math.max(a,Math.min(b,n)),sum=a=>a.reduce((n,x)=>n+Number(x),0);
 const team=(s,id)=>(s.teams||[]).find(t=>String(t.id)===String(id));
 const coach=(s,t)=>s.coaches[t.coachId],strength=(s,t)=>t?.ovr??t?.base??0;
 const country=()=>({confederation:'UEFA'}),news=(s,title,body,kind)=>{s.news??=[];s.news.push({title,body,kind});};
 let state=null;
`;
const middle=`
 const E={team,coach,strength,sum,clamp,news,availableJobs,
  adoptLegacyPromotionOffers18372,validPromotionOffer18372,promotionProfile18372,generatePromotionOffer18372,
  ...(typeof generateUnemployedOffer18374==='function'?{generateUnemployedOffer18374,recordJobOffer18374}:{}),
 };
 const v636OfferHash=promotionHash18372,v56Hash=promotionHash18372,v56ClubOverall=promotionOVR18372,
   v636ClubOVR=promotionOVR18372,v56OriginalAvailableJobs=availableJobs;
 function v636PendingCoachOffers(s){return (s.v636CoachOffers||[]).filter(o=>o?.status==='pending'&&Number(o.year)===Number(s.year)&&Number(o.expiresDay)>=s.day);}
 function v636CleanCoachOffers(s){s.v636CoachOffers=(s.v636CoachOffers||[]).filter(o=>o&&['pending','deferred'].includes(o.status)&&Number(o.year)===Number(s.year)&&Number(o.expiresDay)>=s.day);}
 function v181ValidOffers(s){return s.v636CoachOffers.filter(o=>o&&['pending','deferred'].includes(o.status)&&Number(o.year)===Number(s.year)&&Number(o.expiresDay)>=s.day);}
 const MAX_VALID_OFFERS=5,UNEMPLOYED_OFFER_LIFE=14;
 function fixture(year=2031,day=33,since={year:2030,day:150},last=149){
  const s={v1903CareerId:'unemployed-fixture',year,day,lastDay:day-1,user:'old',userCoachId:'me',userEmployed:false,
   teams:[],players:{},coaches:{me:{id:'me',name:'Manager',reputation:74,clubId:null,nationalTeamCode:null,unemployedSince:since,
    jobs:[{club:'old',year:2028,day:1,end:'Contrato encerrado',endYear:since?.year,endDay:since?.day}]}},
   schedule:Array.from({length:164},()=>({type:'league',fixtures:[]})),v636CoachOffers:[],
   v636CoachOfferMeta:{lastOfferDay:last,rejected:{}},v640National:{userTeam:null},news:[]};
  s.teams.push({id:'old',name:'Le Havre',country:'fra',division:1,base:73,ovr:73,coachId:'replacement',fanPressure:0});
  for(let i=0;i<12;i++)s.teams.push({id:'club'+i,name:'Compatible '+i,country:i<6?'fra':'bel',division:i<9?1:2,
    base:68+i%5,ovr:68+i%5,coachId:'ai'+i,fanPressure:60});
  s.teams.push({id:'elite',name:'Unreachable Elite',country:'eng',division:1,base:99,ovr:99,coachId:'elite-coach',fanPressure:100});
  return s;
 }
 globalThis.fixture=fixture;
`;
function context(parts,kind='v93'){
 const ctx=vm.createContext({console,structuredClone});
 let code=prefix+parts.helpers+parts.jobs+middle+parts.state+parts.create+parts.primary+parts.uiJobs+
   '\nE.availableJobs=v56AvailableJobs;\n';
 if(kind==='v93'||kind==='v181')code+=parts.v93;
 if(kind==='v181')code+=parts.v181;
 code+='\nglobalThis.call=s=>v636GenerateCoachOffer(s,false);globalThis.E=E;';
 vm.runInContext(code,ctx);return ctx;
}
const report={ok:true,version:'18.374.0',oldSourceReproduced:[],newGenerators:[]};
// Execute the exact late overrides, not an approximation of their arithmetic.
for(const kind of ['v93','v181']){
 const c=context(input.old,kind),s=c.fixture();let generated=0;
 for(let day=0;day<=33;day++){s.day=day;generated+=c.call(s);}
 assert.equal(generated,0,'18.373 must reproduce 34 rounds without an offer for '+kind);
 assert(c.E.availableJobs(s).length>0,'Failure must occur despite eligible actual candidates');
 report.oldSourceReproduced.push({generator:kind,year:2031,lastDismissalYear:2030,lastDismissalDay:150,throughDay:33,offers:generated});
}
for(const kind of ['primary','v93','v181']){
 const c=context(input.next,kind),evaluate=x=>vm.runInContext(x,c);
 // Recover the screenshot's already-stuck save at the next actual evaluation.
 const stuck=c.fixture();assert.equal(c.call(stuck),1,kind+' legacy stuck save');
 assert.equal(stuck.v636CoachOffers.length,1);assert.notEqual(stuck.v636CoachOffers[0].teamId,'elite');
 const offer=stuck.v636CoachOffers[0];assert.equal(offer.year,2031);assert.equal(c.call(stuck),0,'No duplicate on same day');
 stuck.day++;assert.equal(c.call(stuck),0,'A fresh offer must pause further approaches');
 // Every fresh new-year run receives a level-compatible offer within eight
 // confirmed rounds, regardless of deterministic variety and old cooldowns.
 const flows=[];
 for(const [oldYear,length,newLength] of [[2028,137,164],[2030,164,137],[2032,171,149]]){
  const s=c.fixture(oldYear+1,0,{year:oldYear,day:length,seasonLength:length},length-2);
  s.schedule.length=newLength;s.v636CoachOfferMeta.rejected={club0:length-3,club1:length-1};
  let found=-1;
  for(let day=0;day<=8;day++){s.day=day;if(c.call(s)){found=day;break;}}
  assert(found>=2&&found<=8,kind+' cross-season wait was not bounded');
  assert.equal(s.v636CoachOffers.length,1);assert.equal(s.v636CoachOffers[0].year,oldYear+1);
  assert(s.teams.find(t=>t.id===s.v636CoachOffers[0].teamId).base<=84);
  flows.push({year:oldYear+1,oldCalendar:length,newCalendar:newLength,offerDay:found});
 }
 // Persist the clock and offer with an ordinary JSON-compatible save; a
 // roundtrip must not reset the cadence or recreate the same invitation.
 const saved=JSON.parse(JSON.stringify(stuck));assert.equal(c.call(saved),0);
 assert.deepEqual(JSON.parse(JSON.stringify(saved.v636CoachOffers)),JSON.parse(JSON.stringify(stuck.v636CoachOffers)));
 // A declined offer just before rollover stays blocked for exactly five
 // rounds using the OLD calendar, even if the new calendar is shorter.
 c.sample=c.fixture(2030,163,{year:2030,day:150,seasonLength:164},-99);
 evaluate(`recordJobRejection18374(sample,{teamId:'club0'});sample.v636CoachOfferMeta.rejected.club0=sample.day;`);
 c.sample=JSON.parse(JSON.stringify(c.sample));c.sample.year=2031;c.sample.day=0;c.sample.schedule.length=137;
 assert.equal(evaluate("jobRejectionGap18374(sample,'club0')"),1);
 c.sample.day=3;assert.equal(evaluate("jobRejectionGap18374(sample,'club0')"),4);
 c.sample.day=4;assert.equal(evaluate("jobRejectionGap18374(sample,'club0')"),5);
 // Same-season calendars are exact, and unknown old lengths do not strand a
 // coach when the following calendar contains fewer dates.
 c.sample=c.fixture(2029,1,{year:2028,day:199},199);
 assert.equal(evaluate('unemployedRounds18374(sample)'),2);
 c.sample=c.fixture(2031,151,{year:2031,day:150,seasonLength:164},-99);assert.equal(c.call(c.sample),0);
 c.sample=c.fixture(2031,33,null,-99);c.sample.coaches.me.jobs=[];
 assert.equal(c.call(c.sample),1,'Legacy missing dismissal stamp cannot wait forever');
 // Never infer a job for a manager who is employed, manages a national team,
 // has a future corrupted dismissal timestamp or lacks an eligible employer.
 for(const modify of [s=>{s.userEmployed=true;s.coaches.me.clubId='old';},
    s=>{s.v640National.userTeam='FRA';},s=>{s.coaches.me.nationalTeamCode='FRA';},
    s=>{s.coaches.me.unemployedSince={year:2032,day:0};},s=>{s.teams=s.teams.filter(t=>t.id==='old'||t.id==='elite');}]){
  const no=c.fixture();modify(no);assert.equal(c.call(no),0);
 }
 // A closed market still supplies a realistic compatible project after the
 // bounded unemployment period; it never circumvents reputation ceilings.
 const closed=c.fixture();closed.teams.forEach(t=>t.fanPressure=0);
 assert(c.E.availableJobs(closed).length);assert.equal(c.call(closed),1);
 // Deferral permits another project, but one per club and a five-offer cap.
 const deferred=c.fixture();let distinct=new Set();
 for(let day=33;day<90&&deferred.v636CoachOffers.length<5;day++){
  deferred.day=day;
  for(const o of deferred.v636CoachOffers){o.status='deferred';o.expiresDay=120;}
  c.call(deferred);distinct=new Set(deferred.v636CoachOffers.map(o=>o.teamId));
  assert.equal(distinct.size,deferred.v636CoachOffers.length);
 }
 assert.equal(deferred.v636CoachOffers.length,5);deferred.day++;assert.equal(c.call(deferred),0);
 report.newGenerators.push({generator:kind,stuckSaveRecovered:true,rollovers:flows,saveReloadPreserved:true,
  noDuplicateFreshOffer:true,rejectionCooldownAcrossCalendarChange:true,closedMarketFallback:true,maxDeferredOffers:5});
}
// Exercise the actual small Worker packet and coach-delta functions. Engine
// candidates originate in the complete Worker world; the UI uses only those
// candidates, without players, histories, or an invented replacement vacancy.
{
 const c=context(input.next,'v93');
 vm.runInContext(`
  let world=fixture(),v18373JobWaitWorker=true,session=7,packet=null;
  const self={postMessage:m=>{packet=structuredClone(m);}},
    v18373WorkerIdentity=s=>({careerId:s.v1903CareerId,coachId:s.userCoachId,user:s.user,
      userEmployed:s.userEmployed,year:s.year,day:s.day}),
    v18373JobTeam=t=>({...t}),v18373JobOverall=t=>promotionOVR18372(world,t);
 `+input.next.workerProgress+input.next.workerDelta+`
  E.availableJobs=availableJobs;v18373PublishJobProgress();
  const mirror={...packet.root,v1903CareerId:world.v1903CareerId,user:world.user,userCoachId:world.userCoachId,
    teams:structuredClone([packet.previous,...packet.candidates]),coaches:{[world.userCoachId]:packet.coach},
    schedule:Array(packet.scheduleLength),players:{},v640National:{userTeam:null},
    v18373JobWaitPartial:true,v18373JobCandidates:packet.candidates.map(t=>t.id),v18373JobOVR:packet.ovr};
  E.availableJobs=v56AvailableJobs;
  const generated=v636GenerateCoachOffer(mirror,false);
  v18373ApplyJobCoachDelta({offers:mirror.v636CoachOffers,offerMeta:mirror.v636CoachOfferMeta,
    tracker:mirror.v636CareerTracker,career:mirror.v636CoachCareer||[],news:mirror.news||[]});
  globalThis.compact={generated,uiPlayers:Object.keys(mirror.players).length,workerOffers:world.v636CoachOffers,
    mirrorOffers:mirror.v636CoachOffers,workerMeta:world.v636CoachOfferMeta,mirrorMeta:mirror.v636CoachOfferMeta,
    candidates:packet.candidates.map(t=>t.id)};
 `,c);
 assert.equal(c.compact.generated,1);assert.equal(c.compact.uiPlayers,0);
 assert.equal(c.compact.workerOffers.length,1);
 assert.equal(JSON.stringify(c.compact.workerOffers),JSON.stringify(c.compact.mirrorOffers));
 assert.equal(JSON.stringify(c.compact.workerMeta),JSON.stringify(c.compact.mirrorMeta));
 assert(c.compact.candidates.includes(c.compact.workerOffers[0].teamId));
 report.actualCompactPacketAndDelta=true;
}
Object.assign(report,{allActiveOverridesShareCalendar:true,existing2031SaveRecovers:true,
  latestSeasonStampStored:true,calendarLengthChangesHandled:true,eligibleWaitBoundedAtEightRounds:true,
  realisticReputationCeilingPreserved:true,freshOfferStopsGeneration:true,
  repeatedDismissalYearsCovered:true,actualFunctionsExecuted:true});
process.stdout.write(JSON.stringify(report));
'''


def main() -> None:
    root = Path(sys.argv[1])
    source = (root / 'src/index.html').read_text(encoding='utf-8')
    baseline = root / 'baseline-18373.html'
    if not baseline.exists():
        raise RuntimeError('The exact prepared 18.373 baseline must be retained before applying 18.374 patches')
    old = baseline.read_text(encoding='utf-8')
    assert 'FUTBR_UNEMPLOYED_CALENDAR_18374' not in old
    assert 'FUTBR_UNEMPLOYED_CALENDAR_18374' in source
    assert source.count('return E.generateUnemployedOffer18374(s,E.availableJobs(s),t=>v636ClubOVR(s,t));') == 3
    assert 'c.clubId=null;c.unemployedSince=jobMarketStamp18374(s);c.reputation=' in source
    assert source.count('E.recordJobRejection18374(state,o);') == 2
    assert 'TEST_ONLY_SEASON_JOB_OFFERS_18374' not in source
    with tempfile.TemporaryDirectory(prefix='futbr-job-market-18374-') as d:
        tmp = Path(d)
        (tmp / 'input.json').write_text(json.dumps({'old': pieces(old), 'next': pieces(source)}, ensure_ascii=False), encoding='utf-8')
        (tmp / 'test.cjs').write_text(HARNESS, encoding='utf-8')
        run = subprocess.run(['node', str(tmp / 'test.cjs'), str(tmp / 'input.json')], text=True, encoding='utf-8', capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stderr or run.stdout)
        report = json.loads(run.stdout)
        # Parse every shipped inline script, including UI paths not exercised
        # by the policy fixtures; no browser fixtures are shipped in the game.
        scripts = [body for attrs, body in re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>', source, flags=re.I)
                   if body.strip() and not re.search(r'type\s*=\s*[\'\"](?:application/(?:json|ld\+json|octet-stream)|importmap)', attrs, re.I)]
        (tmp / 'scripts.json').write_text(json.dumps(scripts), encoding='utf-8')
        parse = subprocess.run(['node', '-e', "const fs=require('fs'),vm=require('vm');const s=JSON.parse(fs.readFileSync(process.argv[1],'utf8'));s.forEach((code,i)=>new vm.Script(code,{filename:'inline-'+i+'.js'}));process.stdout.write(String(s.length));", str(tmp / 'scripts.json')], text=True, encoding='utf-8', capture_output=True)
        if parse.returncode:
            raise RuntimeError(parse.stderr)
        report['parsedScripts'] = int(parse.stdout)
    report.update(sourceSha256=hashlib.sha256(source.encode('utf-8')).hexdigest(),
                  baselineSourceSha256=hashlib.sha256(old.encode('utf-8')).hexdigest(),
                  testHooksNotShipped=True)
    (root / 'season-job-offers-18374-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
