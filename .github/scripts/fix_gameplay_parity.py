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
    anchor="const V310_TEAM_BY_ID=new Map(WorldCatalog.clubs.map(t=>[t.id,t]));"
    if anchor not in html:
        fail('V310_TEAM_BY_ID anchor not found')
    catalog_guard=f"""WorldCatalog.clubs=WorldCatalog.clubs.filter(c=>c?.id!=='{DUP_ASA_ID}');
const v18163JuveCatalog=WorldCatalog.clubs.find(c=>c?.id==='{JUVENTUS_ID}');
if(v18163JuveCatalog){{delete v18163JuveCatalog.v515WorldRating;delete v18163JuveCatalog.v515WorldRatingDate;v18163JuveCatalog.supportRosterGrowthGuard=true;}}
"""
    html=html.replace(anchor,catalog_guard+anchor,1)

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

    # --- 3) Live standings repaint: once per completed world day.
    # This keeps the existing lightweight shell but refreshes the visible standings
    # deterministically for club and national-team careers.
    runtime=r'''
<script id="futbr-v18163-parity-live">
(()=>{
 let lastStamp='',scheduled=false;
 function activeViewNeedsRefresh(){return ['dashboard','competitions','national'].includes(String(window.view||''));}
 function paint(){
  scheduled=false;
  if(!window.state||document.hidden||!activeViewNeedsRefresh())return;
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
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule();});
 window.addEventListener('focus',schedule);
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.parity18163={liveStandings:true,careerTypeIndependent:true,duplicateASA:DUP_ASA_PLACEHOLDER};
})();
</script>
'''.replace('DUP_ASA_PLACEHOLDER',repr(DUP_ASA_ID))
    if 'futbr-v18163-parity-live' not in html:
        html=html.replace('</body>',runtime+'</body>',1)

    # Final structural checks.
    if len(base['clubs']) != before-1: fail('ASA was not removed exactly once')
    if html.count('"name":"ASA"')>1: fail('more than one ASA remains in initial source')
    if 'p.real=true;p.clubId=t.id' in html: fail('old support-player real flag remains')
    if 'supportFictional?(div>=4?.72' not in html: fail('support development guard missing')
    if 'futbr-v18163-parity-live' not in html: fail('live standings parity patch missing')

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
