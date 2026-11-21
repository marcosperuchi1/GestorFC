from __future__ import annotations
import json, sys
from pathlib import Path

MARK = 'FUTBR_CAREER_PROMOTION_OFFERS_18372'


def once(s, old, new, label):
    if s.count(old) != 1:
        raise RuntimeError(f'18.372 promotion {label}: expected one anchor, found {s.count(old)}')
    return s.replace(old, new, 1)


ENGINE = r'''
  /* FUTBR_CAREER_PROMOTION_OFFERS_18372
     One shared market for real match results in the UI and the Worker. An
     approach changes no employment until the manager accepts its live offer. */
  function promotionHash18372(text){let h=2166136261;for(const ch of String(text)){h^=ch.charCodeAt(0);h=Math.imul(h,16777619);}return h>>>0;}
  function promotionProfile18372(s){
    const me=s?.coaches?.[s?.userCoachId],recent=(me?.recent||[]).slice(-10),
      games=Number(me?.jobGames)||0,ppg=recent.length?sum(recent)/recent.length:0,
      recentPoints=sum(recent.slice(-6)),pressure=Number(me?.pressure)||0;
    const eligible=!!(s?.userEmployed===true&&!s?.v640National?.userTeam&&me&&
      String(me.clubId||'')===String(s.user||'')&&team(s,s.user)&&games>=12&&
      recent.length>=8&&ppg>=2.1&&recentPoints>=12&&pressure<=30);
    return {eligible,games,ppg,recentPoints,pressure};
  }
  function promotionOVR18372(s,t){
    let squad=Number(t?.base)||50;try{squad=Number(strength(s,t))||squad;}catch(e){}
    return Math.round(squad*.68+(Number(t?.base)||50)*.32);
  }
  function validPromotionOffer18372(s,o){
    const p=o?.promotion18372,me=s?.coaches?.[s?.userCoachId];
    return !!(p&&s?.userEmployed===true&&!s?.v640National?.userTeam&&me&&
      String(me.clubId||'')===String(s.user||'')&&String(s.v1903CareerId||'')&&
      p.careerId===String(s.v1903CareerId)&&p.coachId===String(s.userCoachId)&&
      p.fromClubId===String(s.user)&&['pending','deferred'].includes(o.status)&&
      Number(o.year)===Number(s.year)&&Number(o.day)<=Number(s.day)&&
      Number(o.expiresDay)>=Number(s.day)&&String(o.teamId)!==String(s.user)&&team(s,o.teamId));
  }
  function adoptLegacyPromotionOffers18372(s){
    const me=s?.coaches?.[s?.userCoachId];
    if(s?.userEmployed!==true||s.v640National?.userTeam||!String(s.v1903CareerId||'')||
       !me||String(me.clubId||'')!==String(s.user||''))return 0;
    let count=0;
    // The old save did not identify the issuing employment. Bind only an
    // existing, still-live original j636 record to its loaded career once.
    // Never recreate an offer, renew its deadline or rebind a scoped record.
    for(const o of s.v636CoachOffers||[]){
      if(!o||o.promotion18372||o.id!==`j636-${o.year}-${o.day}-${o.teamId}`||
         !['pending','deferred'].includes(o.status)||Number(o.year)!==Number(s.year)||
         !Number.isFinite(Number(o.day))||Number(o.day)<0||Number(o.day)>Number(s.day)||
         !Number.isFinite(Number(o.expiresDay))||Number(o.expiresDay)<Number(s.day)||
         String(o.teamId)===String(s.user)||!team(s,o.teamId))continue;
      o.promotion18372={careerId:String(s.v1903CareerId),coachId:String(s.userCoachId),
        fromClubId:String(s.user),legacy18371:true};count++;
    }
    return count;
  }
  function promotionJobs18372(s){
    const profile=promotionProfile18372(s);if(!profile.eligible)return [];
    const current=team(s,s.user),me=s.coaches[s.userCoachId],currentOVR=promotionOVR18372(s,current),
      base=Number(current.base)||0,cap=Math.max(Number(me.reputation)||base,base)+8;
    const candidates=[];
    for(const t of s.teams||[]){
      if(!t||String(t.id)===String(current.id)||Number(t.base)>cap)continue;
      const sameCountry=t.country===current.country,division=Number(t.division)||0,
        currentDivision=Number(current.division)||0,
        higherDivision=sameCountry&&division>0&&currentDivision>0&&division<currentDivision;
      if(sameCountry&&division>currentDivision)continue;
      if(higherDivision?Number(t.base)<base-1:Number(t.base)<base+3)continue;
      const incumbent=coach(s,t),pressure=Math.max(Number(t.fanPressure)||0,Number(incumbent?.pressure)||0);
      // A settled incumbent is not displaced merely to create an offer.
      if(incumbent&&(incumbent.id===me.id||Number(incumbent.jobGames)<8||pressure<45))continue;
      const ovr=promotionOVR18372(s,t);
      if(ovr<currentOVR+(higherDivision?1:3)||ovr>currentOVR+12)continue;
      candidates.push({t,score:ovr+(sameCountry?6:0)+(higherDivision?7:0)+pressure*.025});
    }
    // Rank only after checking the entire eligible market. The old twelve-job
    // pressure shortlist could contain no better clubs despite genuine interest.
    return candidates.sort((a,b)=>b.score-a.score||String(a.t.id).localeCompare(String(b.t.id)))
      .slice(0,8).map(x=>x.t);
  }
  function promotionMeta18372(s){
    s.v636CoachOfferMeta??={lastOfferDay:-99,rejected:{}};
    s.v636CoachOfferMeta.rejected??={};
    return s.v636CoachOfferMeta.promotion18372??={rejected:{}};
  }
  function promotionGap18372(s,stamp){
    if(!stamp||!Number.isFinite(Number(stamp.year))||!Number.isFinite(Number(stamp.day)))return Infinity;
    const years=Number(s.year)-Number(stamp.year);
    if(years<0)return -1;if(years===0)return Number(s.day)-Number(stamp.day);
    // Retain the calendar that actually contained the decision. A league
    // restructure next season must neither shorten nor restart the cooldown.
    const previousLength=Number(stamp.seasonLength)||Math.max(38,Number(stamp.day)||0);
    return Math.max(0,previousLength-Number(stamp.day))+
      (years-1)*Math.max(38,Number(s.schedule?.length)||0)+Number(s.day);
  }
  function promotionPulse18372(s){
    const profile=promotionProfile18372(s),me=s?.coaches?.[s?.userCoachId],
      title=(me?.titles||[]).some(t=>Number(t.year)===Number(s?.year)&&String(t.club)===String(s?.user));
    const chance=clamp(Math.round(18+Math.max(0,profile.ppg-2.1)*12+(title?3:0)),18,30),
      roll=promotionHash18372(`${s?.v1903CareerId}|${s?.year}|${s?.day}|${s?.user}|${s?.userCoachId}|promotion18372`)%100;
    return {chance,roll};
  }
  function recordPromotionRejection18372(s,o){
    if(!validPromotionOffer18372(s,o))return false;
    const meta=promotionMeta18372(s);meta.rejected??={};
    meta.rejected[String(o.teamId)]={year:Number(s.year),day:Number(s.day),seasonLength:Number(s.schedule?.length)||38};
    return true;
  }
  function generatePromotionOffer18372(s,stage=null,openingJob=null){
    if(!s||!String(s.v1903CareerId||'')||!promotionProfile18372(s).eligible)return null;
    const source=openingJob?.clubId??s.user;
    if(String(source)!==String(s.user)||openingJob&&(Number(openingJob.year)!==Number(s.year)||
       Number(openingJob.day)!==Number(s.lastDay)))return null;
    stage=stage||s.schedule?.[Number(s.lastDay)];
    // Only confirmed matches under this manager can trigger a recruitment pulse.
    if(!stage?.fixtures?.some(f=>f?.result&&f.result.home!=null&&f.result.away!=null&&[String(f.home),String(f.away)].includes(String(source))&&
       Number.isFinite(Number(f.result.home))&&Number.isFinite(Number(f.result.away))))return null;
    const meta=promotionMeta18372(s),day=Number(s.day)||0,year=Number(s.year),clubId=String(s.user);
    if(meta.checked?.year===year&&meta.checked.day===day&&meta.checked.clubId===clubId)return null;
    meta.checked={year,day,clubId};
    s.v636CoachOffers=Array.isArray(s.v636CoachOffers)?s.v636CoachOffers:[];
    s.v636CoachOffers=s.v636CoachOffers.filter(o=>!o?.promotion18372||validPromotionOffer18372(s,o));
    const active=s.v636CoachOffers.some(o=>o&&['pending','deferred'].includes(o.status)&&
      Number(o.year)===year&&Number(o.expiresDay)>=day&&team(s,o.teamId));
    if(active||meta.last?.clubId===clubId&&promotionGap18372(s,meta.last)<12)return null;
    const pulse=promotionPulse18372(s);if(pulse.roll>=pulse.chance)return null;
    const candidates=promotionJobs18372(s).filter(t=>promotionGap18372(s,meta.rejected?.[String(t.id)])>=24);
    if(!candidates.length)return null;
    const index=promotionHash18372(`${s.v1903CareerId}|${year}|${day}|${clubId}|promotion-pick18372`)%candidates.length,
      t=candidates[index],current=team(s,s.user),ovr=promotionOVR18372(s,t),fromOVR=promotionOVR18372(s,current),
      higher=t.country===current.country&&Number(t.division)<Number(current.division),
      reason='Sua campanha consistente chamou a atenção da diretoria. '+
        (higher?`Convite para subir da ${current.division}ª para a ${t.division}ª divisão no mesmo país. `:'Um projeto de maior nível esportivo. ')+
        `OVR do clube: ${fromOVR} → ${ovr}.`,
      offer={id:`j18372-${year}-${day}-${t.id}`,teamId:t.id,year,day,expiresDay:day+4,
        status:'pending',seen:false,ovr,reason,promotion18372:{careerId:String(s.v1903CareerId||''),
          coachId:String(s.userCoachId),fromClubId:clubId,fromOVR,toOVR:ovr,
          fromDivision:Number(current.division),toDivision:Number(t.division),sameCountry:t.country===current.country}};
    s.v636CoachOffers.push(offer);s.v636CoachOfferMeta.lastOfferDay=day;
    meta.last={year,day,clubId,seasonLength:Number(s.schedule?.length)||38};
    news(s,'Proposta de crescimento na carreira',t.name+' enviou um convite. '+reason,'good');
    if(s.vacation?.active){s.vacation.active=false;s.vacation.paused=true;
      s.vacation.reason='Chegou uma proposta para assumir o '+t.name+'.';}
    return offer;
  }
  function promotionOfferEnvelope18372(s){
    if(!s?.userEmployed||s.v640National?.userTeam)return null;
    return {careerId:String(s.v1903CareerId||''),coachId:String(s.userCoachId||''),
      user:String(s.user||''),year:Number(s.year),day:Number(s.day),
      offers:s.v636CoachOffers||[],meta:s.v636CoachOfferMeta||{lastOfferDay:-99,rejected:{}}};
  }
  function applyPromotionOfferEnvelope18372(s,p){
    if(!s||s.userEmployed!==true||s.v640National?.userTeam||!p||!String(s.v1903CareerId||'')||p.careerId!==String(s.v1903CareerId)||
       p.coachId!==String(s.userCoachId)||p.user!==String(s.user)||Number(p.year)!==Number(s.year)||
       Number(p.day)!==Number(s.day)||!Array.isArray(p.offers)||!p.meta||typeof p.meta!=='object')return false;
    s.v636CoachOffers=p.offers;s.v636CoachOfferMeta=p.meta;return true;
  }
'''

UI = r'''
/* FUTBR_PROMOTION_RETURN_UI_18372: wait for the existing stream/checkpoint. */
let v18372OfferTimer=0;
function v18372ShowPromotionAfterReturn(){
 clearTimeout(v18372OfferTimer);
 const careerId=String(state?.v1903CareerId||''),clubId=String(state?.user||'');
 let tries=0;
 const show=()=>{
  if(!state||String(state.v1903CareerId||'')!==careerId||String(state.user||'')!==clubId)return;
  if(v53Sim?.active||v53Sim?.starting||v53Sim?.syncing||v53Sim?.patching||v53Sim?.finished||
     v125VacIncoming||v52Processing||v52SavePromise||
     (typeof v18357AwaitingPromotion!=='undefined'&&v18357AwaitingPromotion)||
     (typeof v18359VacationPromise!=='undefined'&&v18359VacationPromise)){
   if(++tries<1800)v18372OfferTimer=setTimeout(show,100);return;
  }
  const offers=v636PendingCoachOffers(state).filter(o=>E.validPromotionOffer18372(state,o)&&!o.seen);
  if(!offers.length||modalKind)return;
  view='career';render();v636CoachOfferModal(false);
 };
 v18372OfferTimer=setTimeout(show,0);
}
'''


def patch(s):
    if MARK in s:
        return s
    s = once(s, '  function availableJobs(s){', ENGINE + '\n  function availableJobs(s){', 'shared Engine market')
    s = once(s, '    if(s.userEmployed)return normal.sort((a,b)=>(b.fanPressure||0)-(a.fanPressure||0)||b.base-a.base).slice(0,12);',
             '    if(s.userEmployed){adoptLegacyPromotionOffers18372(s);return (s.v636CoachOffers||[]).filter(o=>validPromotionOffer18372(s,o)).map(o=>team(s,o.teamId));}', 'only a received current invitation authorizes an employed takeover')
    s = once(s, "    const t=availableJobs(s).find(t=>t.id===id);if(!t)throw Error('Esta vaga não está disponível.');",
             "    const invitation=(s.v636CoachOffers||[]).find(o=>String(o?.teamId)===String(id)&&validPromotionOffer18372(s,o));\n    const t=invitation?team(s,id):availableJobs(s).find(t=>t.id===id);if(!t)throw Error('Esta vaga não está disponível.');", 'accept the current invitation through the real Engine')
    s = once(s, "    invalidateMarket(s);trimOldResultDetails125(s,2);const v172RoundEnded=",
             "    generatePromotionOffer18372(s,stage,v18117OpeningJob);\n    invalidateMarket(s);trimOldResultDetails125(s,2);const v172RoundEnded=", 'real completed async rounds and vacations')
    s = once(s, '  return {managerSettings18371,',
             '  return {promotionProfile18372,promotionJobs18372,promotionPulse18372,generatePromotionOffer18372,validPromotionOffer18372,adoptLegacyPromotionOffers18372,recordPromotionRejection18372,promotionOfferEnvelope18372,applyPromotionOfferEnvelope18372,managerSettings18371,', 'export shared Engine API')
    a=s.index('function v56ExceptionalWork(s){'); b=s.index('function v56AvailableJobs(s){',a)
    s=s[:a]+"function v56ExceptionalWork(s){return E.promotionProfile18372(s).eligible;}\n"+s[b:]
    s=once(s,'function v56AvailableJobs(s){\n const raw=',
           'function v56AvailableJobs(s){\n if(s?.userEmployed)return v56OriginalAvailableJobs(s)||[];\n const raw=', 'employed UI lists received invitations only')
    old=" s.v636CoachOfferMeta.rejected=s.v636CoachOfferMeta.rejected&&typeof s.v636CoachOfferMeta.rejected==='object'?s.v636CoachOfferMeta.rejected:{};"
    s=once(s,old,old+'\n E.adoptLegacyPromotionOffers18372(s);', 'bind existing legacy invitations before rendering or saving')
    # Keep the existing unemployed market and its later multiple-offer wrappers.
    start=s.index(' if(s.userEmployed){',s.index('function v636GenerateCoachOffer(s,'))
    end=s.index('\n const candidates=',start)
    s=s[:start]+" if(s.userEmployed)return afterUserMatch?Number(!!E.generatePromotionOffer18372(s)):0;\n"+s[end:]
    s=once(s,'const v636BaseStartSimulation=v53StartSimulation;',UI+'\nconst v636BaseStartSimulation=v53StartSimulation;', 'private UI return gate')
    s=once(s,"if(v636PendingCoachOffers(state).length){if(typeof v93ScheduleCoachDecisionSave==='function')v93ScheduleCoachDecisionSave(60000);else persist();}}return out;};",
           "if(v636PendingCoachOffers(state).length){if(typeof v93ScheduleCoachDecisionSave==='function')v93ScheduleCoachDecisionSave(60000);else persist();if(mode==='vacation')v18372ShowPromotionAfterReturn();}}return out;};", 'show after vacation checkpoint settles')
    s=once(s,'msg.managerSettings18371=v18371SettingsEnvelope(state);',
           'msg.managerSettings18371=v18371SettingsEnvelope(state);\n  msg.careerPromotion18372=E.promotionOfferEnvelope18372?.(state)||null;', 'compact current offer decisions')
    s=once(s,'  // FUTBR_MANAGER_PREFERENCES_WORKER_18371:',
           '  E.applyPromotionOfferEnvelope18372(world,message.careerPromotion18372);\n  // FUTBR_MANAGER_PREFERENCES_WORKER_18371:', 'decisions applied after saved/checkpoint restoration')
    s=once(s,'v636CareerTracker:world.v636CareerTracker||null,v636CoachCareer:world.v636CoachCareer||[]};',
           'v636CareerTracker:world.v636CareerTracker||null,v636CoachCareer:world.v636CoachCareer||[],v636CoachOffers:world.v636CoachOffers||[],v636CoachOfferMeta:world.v636CoachOfferMeta||{}};', 'live offer metadata follows actual Worker state')
    old='state.v636CoachOfferMeta.rejected[o.teamId]=Number(state.day);'
    if s.count(old)!=2:raise RuntimeError('18.372 expected both original rejection handlers')
    s=s.replace(old,'E.recordPromotionRejection18372(state,o);'+old)
    s=once(s,"  if(!state||state.userEmployed||modalKind!=='coach-offers')return 0;",
           "  if(!state||modalKind!=='coach-offers'||state.userEmployed&&!pending().some(o=>E.validPromotionOffer18372(state,o)))return 0;", 'defer a promotion without extending its expiry')
    # The original and the deferred-offer modal both explain only genuine promotions.
    old='${o.ovr||v636ClubOVR(state,t)}</span>'
    if s.count(old)!=2:raise RuntimeError('18.372 expected both offer card renderers')
    s=s.replace(old,old+'${o.promotion18372?\'<p class="tiny mt8">\'+esc(o.reason||\'\')+\'</p>\':\'\'}')
    old='Number(o.expiresDay)>=Number(s.day)&&E.team(s,o.teamId)'
    if s.count(old)!=3:raise RuntimeError(f'18.372 expected three UI offer validity predicates, got {s.count(old)}')
    s=s.replace(old,'Number(o.expiresDay)>=Number(s.day)&&(!o.promotion18372||E.validPromotionOffer18372(s,o))&&E.team(s,o.teamId)')
    for old,new in [
        ('pelo menos 18 jogos no cargo, média mínima de 2,45 pontos nos últimos jogos, 15+ pontos nos últimos seis e pressão da torcida de no máximo 12%. O clube interessado também precisa ter OVR e nível-base superiores.',
         'pelo menos 12 jogos no cargo, média mínima de 2,1 pontos nos últimos jogos, 12+ pontos nos últimos seis e pressão de no máximo 30%. O clube interessado precisa oferecer crescimento esportivo e ter uma vaga ou uma diretoria insatisfeita. Cada convite depende de interesse e tem intervalo entre abordagens.'),
        ('Seu momento é excepcional. Somente clubes de nível claramente superior ao atual podem apresentar proposta.',
         'Sua boa fase pode despertar o interesse de clubes de nível claramente superior ao atual.'),
        ('Enquanto estiver empregado, propostas só aparecem após uma sequência realmente excepcional e apenas de clubes de nível superior.',
         'Enquanto estiver empregado, propostas podem aparecer após uma boa sequência consistente e apenas de clubes de nível superior.'),
        ('Seu trabalho ainda não atingiu o patamar excepcional exigido para receber propostas de clubes maiores.',
         'Consolide uma boa campanha para despertar o interesse de clubes maiores.'),
        ('Seu momento é excepcional. Clubes de nível superior podem apresentar propostas.',
         'Sua boa fase pode despertar o interesse de clubes de nível superior.'),
        ('Convites deste tipo só são gerados em fase excepcional e por clubes esportivamente superiores ao seu atual.',
         'Convites deste tipo dependem de uma boa campanha consistente e vêm de clubes esportivamente superiores ao seu atual.'),
        ('somente uma fase realmente excepcional habilita abordagens, e apenas clubes de nível superior podem procurar o treinador.',
         'uma boa campanha consistente pode atrair abordagens de clubes de nível superior com interesse em trocar de treinador.')]:
        s=once(s,old,new,'promotion explanation')
    s=once(s,"const EDITION='18.371.0';","const EDITION='18.372.0';",'edition')
    s=once(s,"window.GestorFC.version='18.371.0';window.GestorFC.visualVersion='18.371.0';",
           "window.GestorFC.version='18.372.0';window.GestorFC.visualVersion='18.372.0';",'visual edition')
    return s


def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_career_promotion_offers_18372.py <project>')
    root=Path(sys.argv[1]);path=root/'src/index.html';source=path.read_text(encoding='utf-8');out=patch(source)
    path.write_text(out,encoding='utf-8')
    report={'ok':True,'version':'18.372.0','sharedEnginePromotionMarket':True,
            'realCompletedRoundHook':True,'vacationPausesForProposal':True,
            'currentOfferAcceptance':True,'compactDecisionOverlay':True,
            'unemployedMarketPreserved':True,'noFullWorldClone':True}
    (root/'career-promotion-offers-18372-install.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
