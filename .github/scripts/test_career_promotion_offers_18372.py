"""Execute the shipped promotion rules, async round hooks and original takeover.

The browser release gate separately runs complete real matches and Workers.
These fixtures isolate merit, vacancies, identity, cooldown and persistence.
"""
from __future__ import annotations
import json, subprocess, sys, tempfile
from pathlib import Path


def between(s, start, end):
    a=s.index(start)
    return s[a:s.index(end,a)]


def main():
    root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
    assert 'FUTBR_CAREER_PROMOTION_OFFERS_18372' in s
    helpers=between(s,'  function promotionHash18372(','  function availableJobs(s){')
    jobs=between(s,'  function availableJobs(s){','  /* FUTBR_CONTRACT_PREFERENCES_18371')
    settings=between(s,'  function managerSettings18371(','  function applyManagerSettings18371(')
    take=between(s,'  function takeJob(s,id){','  function startVacation(s,')
    start_job=between(s,'  function startCoachJob(s,c,t,','  function v151CoachIdentity(')
    dismiss=between(s,'  function dismissCoach(s,t,reason){','  function hireCoach(s,')
    ledger=between(s,'  function v18117CoachRoundLedger(','  async function advanceDayAsync(')
    round_code=between(s,'  async function advanceDayAsync(','  advanceDay=function(s){')
    tracker=between(s,'function v636CoachState(s=state){','function v636TitleCounts(')
    take_wrapper=between(s,'const v636BaseTakeJob=E.takeJob;','const v636BaseNextSeason=')
    generator=between(s,'function v636GenerateCoachOffer(s,','function v636CoachOfferModal(')
    defer=between(s,' function deferOpenOffers(){',' const baseModal=modal;')
    ui_available=between(s,'function v56ExceptionalWork(s){','E.availableJobs=v56AvailableJobs;')
    simulate=between(s,' async function simulate(message){',' self.onmessage=event=>')
    assert simulate.index('await v93ApplyVacationCheckpoint(')<simulate.index('E.applyPromotionOfferEnvelope18372(')
    assert simulate.index('world.vacation={')<simulate.index('E.applyPromotionOfferEnvelope18372(')
    assert round_code.count('generatePromotionOffer18372(s,stage,v18117OpeningJob);')==1
    assert 'msg.careerPromotion18372=E.promotionOfferEnvelope18372?.(state)||null;' in s
    assert 'v636CoachOffers:world.v636CoachOffers||[],v636CoachOfferMeta:world.v636CoachOfferMeta||{}' in s
    assert s.count('E.recordPromotionRejection18372(state,o);')==2
    assert s.count("esc(o.reason||'')")==2
    assert "const EDITION='18.372.0';" in s
    engine_source=between(s,'const Engine = (() => {',"if(typeof module!=='undefined'&&module.exports)")
    assert 'function generatePromotionOffer18372(' in engine_source
    assert 'promotionProfile18372,promotionJobs18372,promotionPulse18372,generatePromotionOffer18372' in engine_source
    prefix=r'''
const assert=require('node:assert/strict');
const sum=a=>a.reduce((n,x)=>n+Number(x),0),clamp=(n,a,b)=>Math.max(a,Math.min(b,n));
const team=(s,id)=>s.teams.find(t=>String(t.id)===String(id)),coach=(s,t)=>s.coaches[t.coachId];
const human=s=>team(s,s.user),strength=(s,t)=>t.ovr??t.base;
const country=()=>({confederation:'CONMEBOL'});
const news=(s,title,body,kind)=>{s.news??=[];s.news.push({title,body,kind});};
const autoLineup=()=>{},ledger=()=>{},coachMarket=()=>{};
function v172FillCoachVacancy(s,t){t.coachId='reserve';s.coaches.reserve.clubId=t.id;}
let state=null;
'''
    middle=r'''
const E={team,coach,human,strength,sum,clamp,news,normName:x=>String(x||'').toLowerCase(),
 promotionProfile18372,promotionJobs18372,promotionPulse18372,generatePromotionOffer18372,
 validPromotionOffer18372,adoptLegacyPromotionOffers18372,recordPromotionRejection18372,promotionOfferEnvelope18372,
 applyPromotionOfferEnvelope18372,takeJob,availableJobs};
function fixture(){
 const s={v1903CareerId:'promotion-test-18372',year:2026,day:24,lastDay:23,user:'current',
  userCoachId:'me',userEmployed:true,manager:'Manager',live:null,board:100,seasonDone:false,
  teams:[],players:{},coaches:{},history:[],v636CoachCareer:[],v636CoachOffers:[],
  v636CoachOfferMeta:{lastOfferDay:-99,rejected:{}},cupWinners:{},coachMoves:[],
  vacation:{active:false,paused:false,remaining:30,completed:0,delegateTransfers:false},
  v622Settings:{renewals:'board',matchSpeed:'90',offerPopup:false,revision18371:3},
  schedule:Array.from({length:100},()=>({type:'league',fixtures:[]}))};
 const add=(id,base,division,pressure=60)=>{
  const t={id,name:id,short:id,base,ovr:base,country:'bra',division,fanPressure:pressure,
   coachId:id==='current'?'me':'coach-'+id,roster:[],balance:1000000,stats:{p:18,w:15,d:2,l:1,pts:47},
   tactics:{formation:'4-3-3',style:'possession'}};
  s.teams.push(t);s.coaches[t.coachId]={id:t.coachId,real:true,name:t.coachId,clubId:id,jobGames:20,
   recent:Array(10).fill(3),pressure,reputation:base,salary:1000,titles:[],jobs:[{club:id,year:2026,day:0}]};
  return t;
 };
 add('current',60,3,0);
 for(let i=0;i<12;i++)add('weak-'+i,50,2,99);
 add('better',67,2,70);
 s.coaches.reserve={id:'reserve',clubId:null,jobs:[],recent:[],reputation:60};
 s.coaches.me.reputation=60;s.coaches.me.jobGames=20;
 s.v636CareerTracker={year:2026,clubId:'current',clubName:'current',startDay:0,
  v18117Games:18,v18117Wins:15,v18117Draws:2,v18117Losses:1,v18117LeaguePoints:47};
 s.v636TrackingInitialized=true;
 return s;
}
function preparePulse(s,start=24){
 for(let day=start;day<90;day++){
  s.day=day;s.lastDay=day-1;
  if(promotionPulse18372(s).roll<promotionPulse18372(s).chance){
   s.schedule[day-1]={type:'league',fixtures:[{id:'match-'+day,home:s.user,away:'weak-0',result:{home:2,away:0,winner:s.user},division:3,country:'bra'}]};
   return s;
  }
 }
 throw Error('No deterministic eligible pulse in fixture');
}
const prepareStage=()=>{},upcoming=s=>(s.schedule[s.day]?.fixtures||[]).find(f=>f.home===s.user||f.away===s.user),
 automated=()=>true,trainAndRecover=()=>{},stageFinances=()=>{},academyTrain=()=>{},
 repairLineup=()=>{},syncEligibility=()=>{},invalidateMarket=()=>{},trimOldResultDetails125=()=>{},
 aiMarket=()=>{},roleNeeds=()=>[],inferPositions=()=>{},setTeamEligibility=()=>{};
function completeSeason(s){s.seasonDone=true;}
function v636CleanCoachOffers(s){s.v636CoachOffers=(s.v636CoachOffers||[]).filter(o=>
 ['pending','deferred'].includes(o.status)&&Number(o.year)===Number(s.year)&&Number(o.expiresDay)>=s.day&&
 (!o.promotion18372||validPromotionOffer18372(s,o)));}
function v636PendingCoachOffers(s){return (s.v636CoachOffers||[]).filter(o=>o.status==='pending');}
let modalKind='coach-offers';
const pending=()=>v636PendingCoachOffers(state),v93ScheduleCoachDecisionSave=()=>{};
const v636ClubOVR=(s,t)=>promotionOVR18372(s,t),v636OfferHash=promotionHash18372;
let unemployedLegacyCalls=0;
function v636CreateCoachOffer(s,t,reason){unemployedLegacyCalls++;const o={id:'legacy',teamId:t.id,year:s.year,day:s.day,expiresDay:s.day+4,status:'pending',reason};s.v636CoachOffers.push(o);return o;}
const v56OriginalAvailableJobs=availableJobs;
const v56ClubOverall=promotionOVR18372,v56Hash=promotionHash18372;
'''
    tests=r'''
(async()=>{
 const result={ok:true,version:'18.372.0'};
 // Exact prior shortlist behavior demonstrates the reproduced starvation.
 let s=fixture();const me=s.coaches.me;
 const legacy=s.teams.filter(t=>t.id!==s.user&&t.base<=me.reputation+8&&
  (t.division===2||t.fanPressure>=45||!t.coachId))
  .sort((a,b)=>(b.fanPressure||0)-(a.fanPressure||0)||b.base-a.base).slice(0,12);
 assert(!legacy.some(t=>t.id==='better'));assert(promotionJobs18372(s).some(t=>t.id==='better'));
 assert.equal(v56AvailableJobs(s).length,0,'Interested candidates are not yet received invitations');
 result.superiorClubBeyondLegacyCut=true;
 assert(promotionProfile18372(s).eligible);
 for(const mutate of [x=>x.coaches.me.recent=Array(10).fill(0),x=>x.coaches.me.jobGames=11,
  x=>x.coaches.me.pressure=60,x=>x.userEmployed=false,x=>x.v640National={userTeam:'BRA'},
  x=>x.coaches.me.clubId='other']){
  const bad=fixture();mutate(bad);assert(!promotionProfile18372(bad).eligible);assert.equal(promotionJobs18372(bad).length,0);
  assert.equal(generatePromotionOffer18372(preparePulse(bad)),null);
 }
 result.goodAndPoorFormControls=true;result.employmentAndNationalGuards=true;
 const settled=fixture();settled.coaches['coach-better'].pressure=0;team(settled,'better').fanPressure=0;
 assert.equal(promotionJobs18372(settled).length,0);
 settled.coaches['coach-better'].jobGames=2;settled.coaches['coach-better'].pressure=70;
 assert.equal(promotionJobs18372(settled).length,0);
 const foreign=fixture();Object.assign(team(foreign,'better'),{base:60,ovr:60,country:'usa',division:1});
 assert.equal(promotionJobs18372(foreign).length,0,'Foreign division number is not an upgrade');
 Object.assign(team(foreign,'better'),{base:67,ovr:67});assert.equal(promotionJobs18372(foreign).length,1);
 Object.assign(team(foreign,'better'),{country:'bra',division:4});assert.equal(promotionJobs18372(foreign).length,0);
 result.plausibleBoardInterestRequired=true;result.domesticDivisionAndForeignQuality=true;
 s=preparePulse(fixture());const before=JSON.stringify({teams:s.teams,coaches:s.coaches}),offer=generatePromotionOffer18372(s);
 assert(offer);assert.equal(offer.expiresDay,offer.day+4);assert.equal(offer.ovr,67);
 assert.deepEqual(v56AvailableJobs(s).map(t=>t.id),['better']);
 assert.equal(s.v636CoachOfferMeta.promotion18372.last.seasonLength,100);
 result.uiListsOnlyReceivedOffers=true;
 assert.equal(JSON.stringify({teams:s.teams,coaches:s.coaches}),before,'An approach must not employ/dismiss anyone');
 const id=offer.id,expires=offer.expiresDay;
 assert.equal(generatePromotionOffer18372(s),null);assert.equal(s.v636CoachOffers.length,1);
 const restored=JSON.parse(JSON.stringify(s));assert(validPromotionOffer18372(restored,restored.v636CoachOffers[0]));
 assert.equal(restored.v636CoachOffers[0].id,id);assert.equal(restored.v636CoachOffers[0].expiresDay,expires);
 state=restored;assert.equal(deferOpenOffers(),1);assert.equal(restored.v636CoachOffers[0].status,'deferred');
 assert.equal(restored.v636CoachOffers[0].id,id);restored.day++;assert.equal(generatePromotionOffer18372(restored),null);
 assert.equal(restored.v636CoachOffers[0].expiresDay,expires);
 restored.day=expires+1;assert(!validPromotionOffer18372(restored,restored.v636CoachOffers[0]));
 assert.equal(generatePromotionOffer18372(restored),null,'Twelve-round cooldown survives expiry');
 result.noEmploymentMutationBeforeAcceptance=true;result.oneOfferAndCooldown=true;
 result.sameOfferAndExpiryAfterReload=true;result.deferredOfferPreserved=true;result.originalDeferHandlerPreservesExpiry=true;
 const rejected=JSON.parse(JSON.stringify(s));recordPromotionRejection18372(rejected,rejected.v636CoachOffers[0]);
 assert.equal(rejected.v636CoachOfferMeta.promotion18372.rejected.better.seasonLength,100);
 rejected.v636CoachOffers=[];preparePulse(rejected,rejected.day+12);
 assert(rejected.day-offer.day<24,'Rejection test must use an actual positive pulse during its cooldown');
 assert.equal(generatePromotionOffer18372(rejected),null);result.rejectionCooldownPreserved=true;
 // The old season's saved length, not the new calendar, defines elapsed rounds.
 const cross=fixture(),stamp={year:2026,day:98,seasonLength:100};cross.year=2027;cross.day=3;
 for(const length of [60,160]){
  cross.schedule=Array.from({length},()=>({type:'league',fixtures:[]}));
  assert.equal(promotionGap18372(cross,stamp),5);cross.day=10;assert.equal(promotionGap18372(cross,stamp),12);
  cross.day=22;assert.equal(promotionGap18372(cross,stamp),24);cross.day=3;
 }
 const reloadedStamp=JSON.parse(JSON.stringify(s.v636CoachOfferMeta.promotion18372.last));
 cross.year=s.year;cross.day=s.day+11;assert.equal(promotionGap18372(cross,reloadedStamp),11);
 result.seasonBoundaryCooldownUsesOriginalCalendar=true;
 const envelope=JSON.parse(JSON.stringify(promotionOfferEnvelope18372(rejected)));
 const resident=JSON.parse(JSON.stringify(rejected));resident.v636CoachOffers=[offer];resident.v636CoachOfferMeta={};
 assert(applyPromotionOfferEnvelope18372(resident,envelope));assert.equal(resident.v636CoachOffers.length,0);
 assert.deepEqual(resident.v636CoachOfferMeta,rejected.v636CoachOfferMeta);
 for(const changes of [{careerId:'other'},{coachId:'other'},{user:'other'},{day:resident.day-1}])
  assert(!applyPromotionOfferEnvelope18372(resident,{...envelope,...changes}));
 result.compactWorkerDecisionOverlay=true;result.otherCareerClubAndDateRejected=true;
 result.offerEnvelopeBytes=Buffer.byteLength(JSON.stringify(envelope));assert(result.offerEnvelopeBytes<3000);
 // The actual takeover uses the invitation even if form and the shortlist change.
 state=JSON.parse(JSON.stringify(s));state.coaches.me.recent=Array(10).fill(0);
 team(state,'better').fanPressure=0;state.coaches['coach-better'].pressure=0;
 assert.deepEqual(v56AvailableJobs(state).map(t=>t.id),['better'],'Received offer stays visible until its original expiry');
 assert.equal(promotionJobs18372(state).length,0);assert.equal(availableJobs(state).length,1);
 const originalTitles=JSON.stringify(state.coaches.me.titles);
 E.takeJob(state,'better');assert.equal(state.user,'better');assert.equal(state.coaches.me.clubId,'better');
 assert.equal(state.v636CoachOffers.length,0);assert.equal(state.v622Settings.renewals,'board');
 assert.equal(state.v622Settings.offerPopup,false);assert.equal(JSON.stringify(state.coaches.me.titles),originalTitles);
 assert(state.v636CoachCareer.some(row=>row.clubId==='current'&&row.games===18));
 assert(state.coaches.me.jobs.some(job=>job.club==='current'));assert.equal(state.v636CareerTracker.clubId,'better');
 result.originalTakeJobAcceptsCurrentOffer=true;result.historyAndPreferencesPreserved=true;
 for(const mutate of [x=>x.day=expires+1,x=>x.v1903CareerId='other-career',x=>x.v636CoachOffers[0].promotion18372.fromClubId='wrong']){
  const invalid=JSON.parse(JSON.stringify(s));mutate(invalid);
  assert(promotionJobs18372(invalid).some(t=>t.id==='better'),'Invalid offer test retains sporting eligibility');
  assert.throws(()=>E.takeJob(invalid,'better'),/vaga/);assert.equal(invalid.user,'current');
 }
 const neverInvited=fixture();assert(promotionJobs18372(neverInvited).length);
 assert.throws(()=>E.takeJob(neverInvited,'better'),/vaga/);
 result.expiredAndWrongCareerOffersRejected=true;result.expiredOfferCannotFallBackToCandidates=true;
 // Existing 18.371 invitations remain actionable even when later form falls.
 // Bind their missing scope to the loaded career once without changing dates.
 const legacyOffer=JSON.parse(JSON.stringify(s));
 const old=legacyOffer.v636CoachOffers[0];delete old.promotion18372;old.id=`j636-${old.year}-${old.day}-${old.teamId}`;
 const legacyId=old.id,legacyExpiry=old.expiresDay;legacyOffer.coaches.me.recent=Array(10).fill(0);
 assert.deepEqual(availableJobs(legacyOffer).map(t=>t.id),['better']);
 assert.equal(old.id,legacyId);assert.equal(old.expiresDay,legacyExpiry);assert(old.promotion18372.legacy18371);
 const legacyRestored=JSON.parse(JSON.stringify(legacyOffer));
 assert.equal(adoptLegacyPromotionOffers18372(legacyRestored),0,'A bound legacy record is never rebound');
 for(const mutate of [x=>x.v1903CareerId='other',x=>x.userCoachId='reserve',x=>x.day=legacyExpiry+1]){
  const invalid=JSON.parse(JSON.stringify(legacyRestored));mutate(invalid);
  assert.equal(adoptLegacyPromotionOffers18372(invalid),0);assert.throws(()=>E.takeJob(invalid,'better'),/vaga/);
 }
 E.takeJob(legacyRestored,'better');assert.equal(legacyRestored.user,'better');
 assert.equal(legacyRestored.v622Settings.renewals,'board');
 result.legacyOffersBoundAndAccepted=true;result.legacyScopeAndExpiryPreserved=true;
 // Execute shipped advanceDayAsync and vacationStepAsync. Only the broad match
 // and finance dependencies are fixtures; the round tail, ledger and generator
 // are the actual source. The browser gate additionally simulates full matches.
 const rounds=[];
 for(const vacation of [false,true]){
  const round=preparePulse(fixture());round.day--;round.lastDay=round.day-1;
  round.vacation.active=vacation;const oldDay=round.day,oldRemaining=round.vacation.remaining;
  if(vacation)await vacationStepAsync(round,()=>{});else await advanceDayAsync(round,()=>{});
  assert.equal(round.day,oldDay+1);assert.equal(round.v636CoachOffers.length,1);
  assert.equal(round.v636CareerTracker.v18117Games,19);assert.equal(round.user,'current');
  if(vacation){assert(!round.vacation.active);assert(round.vacation.paused);assert.equal(round.vacation.remaining,oldRemaining-1);assert.match(round.vacation.reason,/proposta/);}
  rounds.push({mode:vacation?'vacation':'day',day:round.day,offer:round.v636CoachOffers[0].id});
  assert.equal(v636GenerateCoachOffer(round,true),0,'UI fallback cannot duplicate the Worker offer');
 }
 result.actualAsyncRoundAndVacationFunctionsExecuted=true;result.normalAndVacationOffers=rounds;
 result.vacationStopsAfterCompletedRound=true;result.uiDoesNotDuplicateWorkerOffer=true;
 const noGame=preparePulse(fixture());noGame.schedule[noGame.lastDay].fixtures[0].result=null;
 assert.equal(generatePromotionOffer18372(noGame),null);result.confirmedUserMatchRequired=true;
 // Keep the old unemployed branch available; the new generator never consumes it.
 const free=fixture();free.userEmployed=false;free.coaches.me.clubId=null;free.coaches.me.unemployedSince={year:2026,day:0};
 assert.equal(generatePromotionOffer18372(preparePulse(free)),null);
 for(let d=2;d<45&&!unemployedLegacyCalls;d++){free.day=d;v636GenerateCoachOffer(free,false);}
 assert(unemployedLegacyCalls>0);result.unemployedMarketPreserved=true;
 // A pulse is deterministic, selective, and is never guaranteed per victory.
 const chances=fixture(),accepted=[];
 for(let d=12;d<80;d++){chances.day=d;const a=promotionPulse18372(chances),b=promotionPulse18372(chances);assert.deepEqual(a,b);accepted.push(a.roll<a.chance);}
 assert(accepted.some(Boolean)&&accepted.some(x=>!x));result.deterministicSelectivePulse=true;
 result.noFullWorldClone=true;console.log(JSON.stringify(result));
})().catch(error=>{console.error(error.stack||error);process.exitCode=1;});
'''
    program=prefix+helpers+jobs+settings+start_job+dismiss+take+ledger+round_code+middle+tracker+take_wrapper+generator+ui_available+defer+tests
    with tempfile.NamedTemporaryFile('w',suffix='.cjs',encoding='utf-8',delete=False) as f:
        f.write(program);temp=f.name
    try:
        run=subprocess.run(['node',temp],text=True,capture_output=True,timeout=60)
        if run.returncode:raise RuntimeError(run.stderr+'\n'+run.stdout)
        result=json.loads(run.stdout.strip().splitlines()[-1])
    finally:
        Path(temp).unlink(missing_ok=True)
    result['engineWorkerScopeVerified']=True
    result['overlayAfterCheckpointRestore']=True
    (root/'career-promotion-offers-18372-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
