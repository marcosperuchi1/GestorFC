from __future__ import annotations
import json, re, sys
from pathlib import Path

DUP_ASA_ID = 'v691_bra_agremiacao-sportiva-arapiraquense_17aitfs'
KEEP_ASA_ID = 'v58_bra_4_08'
JUVENTUS_ID = 'v691_bra_atletico-juventus_x1llm6'

def fail(msg):
    raise RuntimeError(msg)

def script_block(html, script_id):
    for marker in (f'id="{script_id}"', f"id='{script_id}'"):
        pos=html.find(marker)
        if pos>=0: break
    else:
        fail(f'script {script_id} not found')
    start=html.find('>',pos)+1
    end=html.find('</script>',start)
    if start<=0 or end<0: fail(f'invalid script {script_id}')
    return start,end

def replace_once(text,old,new,label):
    n=text.count(old)
    if n!=1: fail(f'{label}: expected 1 occurrence, got {n}')
    return text.replace(old,new,1)

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: fix_gameplay_parity.py <project-dir>')
    project=Path(sys.argv[1]).resolve()
    p=project/'src'/'index.html'
    html=p.read_text(encoding='utf-8')

    # --- 1) Remove duplicate ASA from the authoritative portable catalog.
    a,b=script_block(html,'gfc-v1865-portable-base')
    base=json.loads(html[a:b])
    clubs=base.get('clubs') or []
    before=len(clubs)
    removed=[c for c in clubs if c.get('id')==DUP_ASA_ID]
    if len(removed)!=1: fail(f'duplicate ASA record count unexpected: {len(removed)}')
    base['clubs']=[c for c in clubs if c.get('id')!=DUP_ASA_ID]
    for key in ('crests','rosters','clubPalette','clubPalettes'):
        if isinstance(base.get(key),dict): base[key].pop(DUP_ASA_ID,None)

    # Juventus BR: remove ambiguous external world-ranking identity. Keep club/base itself.
    juve=next((c for c in base['clubs'] if c.get('id')==JUVENTUS_ID),None)
    if not juve: fail('Brazilian Juventus not found in portable base')
    juve.pop('v515WorldRating',None)
    juve.pop('v515WorldRatingDate',None)
    juve['ratingIdentityReview']='18.163-br-juventus-ambiguous-name'
    juve['supportRosterGrowthGuard']=True

    compact=json.dumps(base,ensure_ascii=False,separators=(',',':'))
    html=html[:a]+compact+html[b:]

    # If the same duplicate was also copied into another static catalog, filter it
    # immediately before team-id maps/Engine are created.
    anchor="const V310_TEAM_BY_ID=new Map((WorldCatalog.clubs||[]).map(t=>[t.id,t]));"
    if anchor not in html:
        fail('V310_TEAM_BY_ID anchor not found')
    catalog_guard=f"""{{
 const v18163DupASA=WorldCatalog.clubs.findIndex(c=>c?.id==='{DUP_ASA_ID}');
 if(v18163DupASA>=0)WorldCatalog.clubs.splice(v18163DupASA,1);
}}
const v18163JuveCatalog=WorldCatalog.clubs.find(c=>c?.id==='{JUVENTUS_ID}');
if(v18163JuveCatalog){{delete v18163JuveCatalog.v515WorldRating;delete v18163JuveCatalog.v515WorldRatingDate;v18163JuveCatalog.supportRosterGrowthGuard=true;}}
"""
    html=html.replace(anchor,catalog_guard+anchor,1)

    # Rankings by bare club name must never promote a regional namesake.
    old_rating="function v515RatingForClub(t){for(const n of [t.name,...(t.aliases||[])]){const p=V515_RATING_MAP.get(v515Norm(n));if(p)return p;}return null;}"
    new_rating="function v515RatingForClub(t){if(t?.regionalOnly)return null;for(const n of [t.name,...(t.aliases||[])]){const p=V515_RATING_MAP.get(v515Norm(n));if(p)return p;}return null;}"
    html=replace_once(html,old_rating,new_rating,'world ranking regional namesake guard')

    # --- 1b) Fresh careers must not inherit runtime-only UI state from another save.
    html=html.replace(
        "stopTimer();state=loaded;saved=loaded;compCountry=null;compDivision=null;v52MarketIndex=null;v5RenderedView=null;",
        "stopTimer();state=loaded;saved=loaded;compCountry=null;compDivision=null;v52MarketIndex=null;v5RenderedView=null;try{v51ModalClub=null;v51EditingClub=null;v4AcademyClub=null;if(typeof v523ClubView!=='undefined')v523ClubView=null;}catch(e){}try{document.documentElement.removeAttribute('data-visual-club');}catch(e){}",
        1
    )
    html=html.replace(
        "initialClub:loaded.user,initialCountry:ht?.country||'',initialDivision:Number(ht?.division||0),startType:nationalCode?'national':'club'",
        "initialClub:nationalCode?'':loaded.user,initialCountry:ht?.country||'',initialDivision:Number(ht?.division||0),startType:nationalCode?'national':'club'",
        1
    )

    # --- 2) Correct support/fallback player identity and potential.
    old_player="""p.name=String(rp.name).slice(0,80);p.real=true;p.clubId=t.id;p.providerId=String(rp.providerId||'');p.ageEstimated=!rp.age;p.positionEstimated=!!rp.positionEstimated;p.sourceOrder=i;p.listed=i>14&&rng(s)<.15;
        if(hasDbOvr)v200ApplyDatabaseOVR(p,dbOvr);t.roster.push(id);"""
    new_player="""p.name=String(rp.name).slice(0,80);p.real=rp.real!==false&&!rp.supportFictional;p.supportFictional=!!rp.supportFictional;p.initialFiller=!!rp.initialFiller;p.clubId=t.id;p.providerId=String(rp.providerId||'');p.ageEstimated=!rp.age;p.positionEstimated=!!rp.positionEstimated;p.sourceOrder=i;p.listed=i>14&&rng(s)<.15;
        if(hasDbOvr)v200ApplyDatabaseOVR(p,dbOvr);
        if(rp.supportFictional){
          const current=overall(p),div=Number(t.division)||1,age=Number(p.age)||25;
          const room=div>=4?(age<=20?5:age<=23?3:1):div===3?(age<=20?6:age<=23?4:2):div===2?(age<=20?8:age<=23?6:3):Math.max(3,Math.min(10,(Number(p.potential)||current)-current));
          p.potential=Math.max(current,Math.min(Number(p.potential)||current,current+room));
          p.star=false;p.starCandidate=false;p.editorStarOverride=false;
        }
        t.roster.push(id);"""
    html=replace_once(html,old_player,new_player,'support roster identity/potential')

    # Additional universal guard: support players in lower divisions cannot bypass
    # the normal annual growth cap due to stale flags or star status.
    old_growth="""function v18123DevelopmentRate(t,p){
    // Sem teto absoluto: contratacoes e jovens excepcionais continuam fortes.
    const div=Number(t?.division)||1,base={1:1,2:.79,3:.56,4:.39}[div]||.67;
    const o=overall(p),relative=o-(Number(t?.base)||65);
    const outlier=relative>10?.58:relative>6?.77:1;
    const prospect=p.star&&p.age<=21?1.10:1;
    return clamp(base*outlier*prospect,.22,1.1);
  }"""
    new_growth="""function v18123DevelopmentRate(t,p){
    const div=Number(t?.division)||1,base={1:1,2:.79,3:.56,4:.39}[div]||.67;
    const o=overall(p),relative=o-(Number(t?.base)||65);
    const outlier=relative>10?.58:relative>6?.77:1;
    const support=p?.supportFictional?(div>=4?.72:div===3?.82:.90):1;
    const prospect=!p?.supportFictional&&p.star&&p.age<=21?1.10:1;
    return clamp(base*outlier*support*prospect,.18,1.1);
  }"""
    html=replace_once(html,old_growth,new_growth,'support development rate')

    # --- 2b) "Avancar ate a selecao" already publishes a compact live delta every day.
    # Allow the same live repaint used in Vacation for Overview/National only.
    old_jump_refresh="if(v53Sim?.mode!=='dayfast'&&v53Sim?.mode!=='nationaljump'&&v53Sim?.mode!=='nextmatch')refresh=true;"
    new_jump_refresh="if(v53Sim?.mode!=='dayfast'&&v53Sim?.mode!=='nextmatch'&&(v53Sim?.mode!=='nationaljump'||['world','national'].includes(view)))refresh=true;"
    html=replace_once(html,old_jump_refresh,new_jump_refresh,'national jump overview refresh')

    # national-jump-day is a progress event; keep the chrome/status current as the
    # corresponding vac-live packet updates state.day and the open Overview.
    old_jump_day="v53Sim.day=Number(m.day)||v53Sim.day;v53Sim.progress='Avancando ate a Selecao · jornada '+v53Sim.day;v53PaintStatus();continue;"
    new_jump_day="v53Sim.day=Number(m.day)||v53Sim.day;v53Sim.progress='Avancando ate a Selecao · jornada '+v53Sim.day;v53PaintStatus();if(['world','national'].includes(view)&&!document.hidden)try{v53RefreshView(false);}catch(e){}continue;"
    html=replace_once(html,old_jump_day,new_jump_day,'national jump progress repaint')

    # --- 3) Live standings repaint: once per completed world day.
    # This keeps the existing lightweight shell but refreshes the visible standings
    # deterministically for club and national-team careers.
    runtime=r'''
<script id="futbr-v18163-parity-live">
(()=>{
 let lastStamp='',scheduled=false,v18165LastObservedDay=null,v18165DayTimer=0;
 function v18165RefreshVisibleDay(){
  if(typeof state==='undefined'||!state||document.hidden)return;
  const day=String(state.year)+'|'+String(state.day);
  if(v18165LastObservedDay===null){v18165LastObservedDay=day;return;}
  if(day===v18165LastObservedDay)return;
  v18165LastObservedDay=day;
  if(!['world','competitions','national'].includes(String(typeof view!=='undefined'?view:'')))return;
  try{
   if(view==='competitions'&&typeof vCleanRefreshCompetitionShell80==='function'){
    if(!vCleanRefreshCompetitionShell80())v53RefreshView(true);
   }else{
    v53RefreshView(true);
   }
  }catch(e){console.warn('[18.165] refresh por jornada:',e?.message||e);}
 }
 function v18165StartDayObserver(){
  if(v18165DayTimer)return;
  v18165LastObservedDay=typeof state!=='undefined'&&state?String(state.year)+'|'+String(state.day):null;
  v18165DayTimer=setInterval(v18165RefreshVisibleDay,180);
 }
 v18165StartDayObserver();
 function nationalOnly(){try{return !!state?.v640National?.userTeam&&state.userEmployed===false;}catch(_){return false;}}
 function cleanNationalClubVisualResidue(){
  if(!nationalOnly())return;
  try{
   const modalOpen=!!document.querySelector('#modal-root .modal');
   if(!modalOpen){v51ModalClub=null;v51EditingClub=null;}
   document.querySelectorAll('table tbody tr.is-user,table tbody tr.v670-own-standing').forEach(tr=>{
    if(tr.querySelector('[data-team],.v634-club-cell,.v247-standing-club-box'))tr.classList.remove('is-user','v670-own-standing');
   });
   if(!modalOpen&&typeof v128NationalTheme==='function')v128NationalTheme(state.v640National.userTeam);
  }catch(e){console.warn('[18.163] national visual isolation:',e?.message||e);}
 }
 function activeViewNeedsRefresh(){try{return ['world','competitions','national','clubrankings'].includes(String(typeof view!=='undefined'?view:''));}catch(_){return false;}}
 function paint(){
  scheduled=false;
  if(typeof state==='undefined'||!state||document.hidden||!activeViewNeedsRefresh())return;
  const stamp=String(state.year)+'|'+String(state.day)+'|'+String(view);
  if(stamp===lastStamp)return;lastStamp=stamp;
  try{
   if(view==='competitions'&&typeof vCleanRefreshCompetitionShell80==='function'){
    if(!vCleanRefreshCompetitionShell80())v53RefreshView(true);
   }else{
    v53RefreshView(true);
   }
  }catch(e){console.warn('[18.163] live standings refresh:',e?.message||e);}
 }
 function schedule(){
  if(scheduled)return;scheduled=true;
  requestAnimationFrame(()=>requestAnimationFrame(paint));
 }
 const basePaint=window.v53PaintStatus;
 if(typeof basePaint==='function'){
  window.v53PaintStatus=function(){const out=basePaint.apply(this,arguments);if(v53Sim?.active)schedule();return out;};
 }
 document.addEventListener('visibilitychange',()=>{if(!document.hidden){schedule();cleanNationalClubVisualResidue();}});
 window.addEventListener('focus',()=>{schedule();cleanNationalClubVisualResidue();v18165RefreshVisibleDay();});
 queueMicrotask(()=>{cleanNationalClubVisualResidue();v18165RefreshVisibleDay();});
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.parity18163={liveStandings:true,overviewPerRound:true,overviewView:'world',dayObserverMs:180,careerTypeIndependent:true,duplicateASA:DUP_ASA_PLACEHOLDER};
})();
</script>
'''.replace('DUP_ASA_PLACEHOLDER',repr(DUP_ASA_ID))
    if 'futbr-v18163-parity-live' not in html:
        html=html+'\n'+runtime

    # Final structural checks.
    if len(base['clubs']) != before-1: fail('ASA was not removed exactly once')
    if html.count('"name":"ASA"')>1: fail('more than one ASA remains in initial source')
    if old_player in html: fail('old support-player creation block remains')
    if "p.real=rp.real!==false&&!rp.supportFictional" not in html:
        fail('new support-player identity rule was not applied')
    if 'supportFictional?(div>=4?.72' not in html: fail('support development guard missing')
    if 'futbr-v18163-parity-live' not in html: fail('live standings parity patch missing')
    if 'v18165RefreshVisibleDay' not in html: fail('overview per-round refresh missing')
    if "v53Sim?.mode!=='nationaljump'||['world','national'].includes(view)" not in html:
        fail('national jump overview live refresh missing')

    p.write_text(html,encoding='utf-8')
    print(json.dumps({
      'ok':True,
      'clubs_before':before,
      'clubs_after':len(base['clubs']),
      'removed_duplicate_asa':DUP_ASA_ID,
      'kept_asa':KEEP_ASA_ID,
      'juventus_growth_guard':JUVENTUS_ID,
      'standings_live_refresh':True
    },ensure_ascii=False))

if __name__=='__main__': main()
