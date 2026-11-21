"""One calendar-aware unemployed market, shared by every UI generation path.

The 18.355 fix lived in the first generator but v93/v181 replaced it with
same-year subtraction. A manager dismissed at day 150 then waited until day
152 of the NEXT season. Keep timing and offer decisions in the Engine shared
by the full world and the small 18.373 job-search mirror.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

MARK = 'FUTBR_UNEMPLOYED_CALENDAR_18374'

ENGINE = r'''
  /* FUTBR_UNEMPLOYED_CALENDAR_18374
     A round number is local to one season. Store its year and calendar size;
     old careers deliberately use a conservative elapsed-year lower bound. */
  function jobMarketStamp18374(s){
    return {year:Number(s.year),day:Math.max(0,Number(s.day)||0),
      seasonLength:Math.max(1,Number(s.schedule?.length)||38)};
  }
  function jobMarketGap18374(s,stamp){
    if(!stamp||!Number.isFinite(Number(stamp.year))||!Number.isFinite(Number(stamp.day)))return Infinity;
    const year=Number(s?.year),day=Math.max(0,Number(s?.day)||0),oldYear=Number(stamp.year),
      oldDay=Math.max(0,Number(stamp.day)||0),years=year-oldYear;
    if(!Number.isFinite(year)||years<0)return -1;
    if(years===0)return day-oldDay;
    const knownLength=Number(stamp.seasonLength),remaining=Number.isFinite(knownLength)&&knownLength>=oldDay
      ?Math.max(0,knownLength-oldDay):1;
    // A legacy save did not record the old calendar. Never apply today's
    // shorter calendar to a last-day dismissal from a longer previous year.
    return remaining+(years-1)*Math.max(1,Number(s.schedule?.length)||38)+day;
  }
  function unemployedRounds18374(s){
    const me=s?.coaches?.[s?.userCoachId];if(!me)return 0;
    let since=me.unemployedSince;
    if(!since||!Number.isFinite(Number(since.year))||!Number.isFinite(Number(since.day))){
      const ended=(me.jobs||[]).find(j=>j?.end&&Number.isFinite(Number(j.endYear))&&Number.isFinite(Number(j.endDay)));
      since=ended?{year:Number(ended.endYear),day:Number(ended.endDay)}:null;
    }
    // Earliest builds could omit unemployedSince entirely. That must not
    // produce (day - day) forever; valid free managers can re-enter the market.
    return since?Math.max(0,jobMarketGap18374(s,since)):Math.max(2,Number(s?.day)||0);
  }
  function jobMarketMeta18374(s){
    const meta=s.v636CoachOfferMeta=s.v636CoachOfferMeta&&typeof s.v636CoachOfferMeta==='object'
      ?s.v636CoachOfferMeta:{lastOfferDay:-99,rejected:{}};
    meta.rejected=meta.rejected&&typeof meta.rejected==='object'?meta.rejected:{};
    const me=s.coaches?.[s.userCoachId],since=me?.unemployedSince,
      key=[s.v1903CareerId||'',s.userCoachId||'',s.user||'',since?.year??'',since?.day??''].join('|');
    let clock=meta.unemployed18374;
    if(!clock||clock.key!==key){
      clock=meta.unemployed18374={key,last:null,rejected:{}};
      const latest=(s.v636CoachOffers||[]).filter(o=>o&&Number.isFinite(Number(o.year))&&Number.isFinite(Number(o.day)))
        .sort((a,b)=>Number(b.year)-Number(a.year)||Number(b.day)-Number(a.day))[0];
      const oldDay=Number(meta.lastOfferDay),explicitYear=Number(meta.lastOfferYear);
      if(latest)clock.last={year:Number(latest.year),day:Number(latest.day)};
      else if(Number.isFinite(oldDay)&&oldDay>=0)clock.last={
        year:Number.isFinite(explicitYear)?explicitYear:Number(s.year)-(oldDay>Number(s.day)?1:0),day:oldDay};
    }
    clock.rejected=clock.rejected&&typeof clock.rejected==='object'?clock.rejected:{};
    return clock;
  }
  function recordJobOffer18374(s){
    const stamp=jobMarketStamp18374(s),clock=jobMarketMeta18374(s);
    clock.last=stamp;s.v636CoachOfferMeta.lastOfferDay=stamp.day;s.v636CoachOfferMeta.lastOfferYear=stamp.year;
    return stamp;
  }
  function recordJobRejection18374(s,o){
    if(!s||s.userEmployed!==false||s.v640National?.userTeam||!o?.teamId)return false;
    jobMarketMeta18374(s).rejected[String(o.teamId)]=jobMarketStamp18374(s);return true;
  }
  function jobRejectionGap18374(s,id){
    const clock=jobMarketMeta18374(s),key=String(id);
    if(!clock.rejected[key]){
      const legacy=Number(s.v636CoachOfferMeta.rejected?.[key]);
      if(Number.isFinite(legacy)&&legacy>=0)clock.rejected[key]={
        year:Number(s.year)-(legacy>Number(s.day)?1:0),day:legacy};
    }
    return jobMarketGap18374(s,clock.rejected[key]);
  }
  function generateUnemployedOffer18374(s,candidates=null,clubOverall=null){
    if(!s||s.userEmployed!==false||s.v640National?.userTeam)return 0;
    const me=s.coaches?.[s.userCoachId];if(!me||me.clubId||me.nationalTeamCode)return 0;
    const clock=jobMarketMeta18374(s),day=Math.max(0,Number(s.day)||0),year=Number(s.year),
      free=unemployedRounds18374(s),lastGap=jobMarketGap18374(s,clock.last);
    if(free<2||lastGap<1)return 0;
    s.v636CoachOffers=Array.isArray(s.v636CoachOffers)?s.v636CoachOffers:[];
    const active=s.v636CoachOffers.filter(o=>o&&['pending','deferred'].includes(o.status)&&
      Number(o.year)===year&&Number(o.expiresDay)>=day&&String(o.teamId)!==String(s.user)&&
      (!o.promotion18372||validPromotionOffer18372(s,o))&&team(s,o.teamId));
    // One new invitation pauses fast-forward. Deferred invitations can coexist
    // (up to five), but never manufacture duplicates while a fresh one waits.
    if(active.some(o=>o.status==='pending')||active.length>=5)return 0;
    const occupied=new Set(active.map(o=>String(o.teamId))),seen=new Set(),
      source=Array.isArray(candidates)?candidates:availableJobs(s),
      jobs=source.filter(t=>{
        if(!t||String(t.id)===String(s.user)||seen.has(String(t.id))||occupied.has(String(t.id))||
           Number(t.base)>Number(me.reputation||60)+10||jobRejectionGap18374(s,t.id)<5)return false;
        seen.add(String(t.id));return true;
      });
    if(!jobs.length)return 0;
    // Normal approaches remain varied. After eight simulated rounds without
    // an offer, an eligible compatible board is guaranteed to make contact.
    const overdue=free>=8&&lastGap>=8,chance=clamp(62+(free-2)*8,62,94),
      pulse=promotionHash18372(`${year}|${day}|${me.id}|free-offer18374`)%100;
    if(!overdue&&pulse>=chance)return 0;
    const prev=team(s,s.user),prevDiv=Number(prev?.division)||0,
      ovr=t=>typeof clubOverall==='function'?Number(clubOverall(t))||Number(t?.base)||0:promotionOVR18372(s,t),
      previousOVR=ovr(prev),scored=jobs.map(t=>{const rating=ovr(t);return {t,rating,score:
        (prevDiv&&Number(t.division)===prevDiv?30:0)+(prevDiv&&Number(t.division)===prevDiv+1?14:0)+
        (prev&&t.country===prev.country?5:0)-Math.abs(rating-previousOVR)*.7+rating*.08};})
        .sort((a,b)=>b.score-a.score||String(a.t.id).localeCompare(String(b.t.id))),
      band=scored.slice(0,8),selected=band[promotionHash18372(`${year}|${day}|${me.id}|free-pick18374`)%band.length],t=selected.t,
      offer={id:`j636-${year}-${day}-${t.id}`,teamId:t.id,year,day,expiresDay:day+14,status:'pending',seen:false,
        ovr:Math.round(selected.rating),reason:Number(t.division)===prevDiv?
          'Projeto compatível com o nível da sua última divisão.':'Clube competitivo interessado no seu trabalho.',
        unemployed18374:{careerId:String(s.v1903CareerId||''),coachId:String(s.userCoachId),fromClubId:String(s.user||'')}};
    s.v636CoachOffers.push(offer);recordJobOffer18374(s);
    news(s,'Proposta de trabalho',t.name+' demonstrou interesse no seu trabalho e enviou uma proposta para assumir a equipe.','good');
    return 1;
  }

'''


def once(source: str, old: str, new: str, reason: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f'18.374 job market {reason}: expected one occurrence, got {count}')
    return source.replace(old, new, 1)


def replace_region(source: str, start: str, end: str, replacement: str) -> str:
    a = source.index(start)
    b = source.index(end, a)
    return source[:a] + replacement + source[b:]


def patch(source: str) -> str:
    if MARK in source:
        return source
    source = once(source, '  function availableJobs(s){', ENGINE + '  function availableJobs(s){', 'shared engine clock')
    source = once(source, '  return {promotionProfile18372,',
                  '  return {jobMarketStamp18374,jobMarketGap18374,unemployedRounds18374,recordJobOffer18374,recordJobRejection18374,generateUnemployedOffer18374,promotionProfile18372,',
                  'engine exports')
    old = "const since=me.unemployedSince,yearGap=Math.max(0,Number(s.year)-Number(since?.year??s.year));\n     const roundsFree=yearGap>0?Math.max(8,yearGap*38+Number(s.day||0)-Number(since?.day||0)):Math.max(0,Number(s.day||0)-Number(since?.day||0));"
    # The baseline indentation is kept strict while allowing the extra single
    # indentation introduced by the earlier 18.355 patch.
    import re
    pattern = r'const since=me\.unemployedSince,yearGap=Math\.max\(0,Number\(s\.year\)-Number\(since\?\.year\?\?s\.year\)\);\s*const roundsFree=yearGap>0\?Math\.max\(8,yearGap\*38\+Number\(s\.day\|\|0\)-Number\(since\?\.day\|\|0\)\):Math\.max\(0,Number\(s\.day\|\|0\)-Number\(since\?\.day\|\|0\)\);'
    source, count = re.subn(pattern, 'const roundsFree=unemployedRounds18374(s);', source)
    if count != 1:
        raise RuntimeError(f'18.374 job market vacancy fallback: expected one original expression, got {count}')
    source = once(source, 'c.clubId=null;c.unemployedSince={year:s.year,day:s.day};c.reputation=',
                  'c.clubId=null;c.unemployedSince=jobMarketStamp18374(s);c.reputation=', 'dismissal calendar')
    for old in ['me.unemployedSince={year:state.year,day:state.day};']:
        if source.count(old) != 2:
            raise RuntimeError('18.374 expected both club and national voluntary resignations')
        source = source.replace(old, 'me.unemployedSince=E.jobMarketStamp18374(state);')
    source = replace_region(source, 'function v636GenerateCoachOffer(s,afterUserMatch=false){',
                            'function v636CoachOfferModal(force=false){', r'''function v636GenerateCoachOffer(s,afterUserMatch=false){
 if(!s)return 0;v636CoachState(s);v636CleanCoachOffers(s);
 if(s.userEmployed)return afterUserMatch?Number(!!E.generatePromotionOffer18372(s)):0;
 /* FUTBR_UNEMPLOYED_GENERATOR_PRIMARY_18374 */
 return E.generateUnemployedOffer18374(s,E.availableJobs(s),t=>v636ClubOVR(s,t));
}
''')
    source = replace_region(source, 'v636GenerateCoachOffer=function(s,afterUserMatch=false){\n if(!s||s.userEmployed)return v93BaseGenerateCoachOffer',
                            '// Display the last completed vacation cash change', r'''v636GenerateCoachOffer=function(s,afterUserMatch=false){
 if(!s||s.userEmployed)return v93BaseGenerateCoachOffer(s,afterUserMatch);
 v636CoachState(s);v636CleanCoachOffers(s);
 /* FUTBR_UNEMPLOYED_GENERATOR_V93_18374 */
 return E.generateUnemployedOffer18374(s,E.availableJobs(s),t=>v636ClubOVR(s,t));
};

''')
    source = replace_region(source, ' v636GenerateCoachOffer=function(s,afterUserMatch=false){\n  if(!s||s.userEmployed)return v181BaseGenerate',
                            ' // Deciding later keeps every proposal visible', r''' v636GenerateCoachOffer=function(s,afterUserMatch=false){
  if(!s||s.userEmployed)return v181BaseGenerate(s,afterUserMatch);
  v636CoachState(s);v636CleanCoachOffers(s);
  /* FUTBR_UNEMPLOYED_GENERATOR_V181_18374 */
  return E.generateUnemployedOffer18374(s,E.availableJobs(s),t=>v636ClubOVR(s,t));
 };
 
''')
    source = once(source, 's.v636CoachOffers.push(offer);meta.lastOfferDay=Number(s.day);E.news(',
                  's.v636CoachOffers.push(offer);E.recordJobOffer18374(s);E.news(', 'legacy create date')
    old = 'E.recordPromotionRejection18372(state,o);'
    if source.count(old) != 2:
        raise RuntimeError('18.374 expected both actual offer rejection handlers')
    source = source.replace(old, old + 'E.recordJobRejection18374(state,o);')
    source = once(source, 's.v636CoachOffers.push(offer);s.v636CoachOfferMeta.lastOfferDay=day;',
                  's.v636CoachOffers.push(offer);s.v636CoachOfferMeta.lastOfferDay=day;s.v636CoachOfferMeta.lastOfferYear=year;',
                  'promotion issuing year')
    return source


def main() -> None:
    root = Path(sys.argv[1])
    path = root / 'src/index.html'
    source = patch(path.read_text(encoding='utf-8'))
    path.write_text(source, encoding='utf-8')
    report = {'ok': True, 'version': '18.374.0', 'sharedCalendarAwareMarket': True,
              'activeAndLegacyGeneratorsDelegated': source.count('return E.generateUnemployedOffer18374(s,E.availableJobs(s),t=>v636ClubOVR(s,t));') == 3,
              'existingStuckSavesSupported': True, 'boundedEligibleOfferWait': 8,
              'datedRejectionCooldowns': True, 'dismissalCalendarRecorded': True,
              'compactJobWaitTransportUnchanged': 'FUTBR_JOBWAIT_SINGLE_OWNER_18373' in source}
    if not all(v for v in report.values()):
        raise RuntimeError('18.374 job market installation is incomplete')
    (root / 'season-job-offers-18374-install.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
