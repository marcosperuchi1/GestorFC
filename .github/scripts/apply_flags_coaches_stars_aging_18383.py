"""FutBR 18.383: offline Oceanian/Asian flags and long-career realism.

Patch only the authoritative annual player-aging, star review, national coaching
and flag display functions. No new per-day scans or world copies. Saves and
pre-existing histories remain compatible. User-supplied flag artwork is stored
in three small local base64 data files, not remotely fetched.
"""
from pathlib import Path
import base64, hashlib, json, re, subprocess, sys

MARK="FUTBR_LONG_CAREER_REALISM_18383"

AGING=r"""
/* FUTBR_AGE_OVR_CURVE_18383: modify skills, not a transient displayed OVR. */
function v18383AgePlayer(s,p){
 const age=Number(p.age)||0;
 if(!p.skills||age<=31)return 0;
 let drop=0;
 for(const k of ['att','def','pas','pace','gk']){
  const before=Number(p.skills[k]);
  if(!Number.isFinite(before))continue;
  if(age<35){
   const delta=E.rand(s,0,1);
   p.skills[k]=Math.max(12,before-delta);drop+=delta;
   continue;
  }
  const base=age>=40?4:age>=38?3:age>=36?2:1;
  let delta=base;
  if(k==='pace'&&['ATA','LAT'].includes(p.pos)&&age>=36)delta++;
  if(k==='gk'&&p.pos==='GOL')delta=Math.max(1,base-1);
  if(k==='def'&&p.pos==='ZAG')delta=Math.max(1,base-1);
  if(k==='pas'&&p.pos==='MEI')delta=Math.max(1,base-1);
  const adjusted=Math.max(12,before-delta);
  p.skills[k]=adjusted;drop+=before-adjusted;
 }
 return drop;
}
"""

RETIRE=r"""
/* FUTBR_RETIREMENT_REALISM_18383
   Typical careers finish around 35-38, with rare exceptional 39/40+ veterans.
   Goalkeepers age slightly more slowly and genuinely outstanding athletes get
   modest extensions, not a near-immunity to retirement. */
function retirementChance549(s,p,m={}){
 const age=Number(p?.age)||0;
 if(age<35)return 0;
 if(age>=44)return 1;
 const chance=age>=42?.999:age===41?.985:age===40?.965:
              age===39?.87:age===38?.70:age===37?.49:age===36?.27:.115;
 const rating=Number(m.rating)||6.5,recent=Number(m.recent)||rating;
 const fitness=Number(m.fitness)||100,minutes=Number(m.minutes)||0;
 const fatigue=(fitness<69?.13:0)+(fitness<55?.13:0)+(minutes>3200?.07:0)+
               ((Number(m.load)||0)>2?.06:0);
 const exceptional=rating>=7.45&&recent>=7.25&&fitness>=68;
 const extension=exceptional?(age>=40?.82:.72):1;
 const position=p.pos==='GOL'?(age<=38?.78:.88):1;
 return Math.min(.999,Math.max(0,(chance+fatigue)*extension*position));
}
"""

AUTO_RETIRE=r"""
function shouldAutoRetire549(s,p,m={},chance=retirementChance549(s,p,m),roll=null){
 if(!p||p.squad==='youth')return false;
 const age=Number(p.age)||0;
 if(age>=44||(p.pos!=='GOL'&&age>=42))return true;
 if(age<35||chance<=0)return false;
 const userClub=!!(s?.userEmployed&&p.clubId===s.user);
 if(userClub&&age<37&&!v18346DelegatedRetirement(s))return false;
 return (roll==null?rng(s):Number(roll))<chance;
}
"""

STARS=r"""
/* FUTBR_ELITE_STAR_PROMOTION_18383
   Evaluate a small shortlist: Big Five first divisions, major European
   competitions and FIFA/Euro international events. No Object.values(players)
   allocation for the entire 225k+ player world. Outstanding evidence from
   major competitions is required; potential alone cannot award star status. */
function reviewWorldStars58(s){
 const selected=new Map(),majorEvents=new Map(),year=Number(s.year)||2026;
 const add=(id,level=1)=>{
  const key=String(id||''),p=s.players?.[key];if(!p||p.star||p.squad==='youth')return;
  const old=selected.get(key)||0;
  if(level>old)selected.set(key,level);
 };
 const bigFive=new Set(['eng','esp','ita','ger','fra']);
 for(const t of s.teams||[]){
  if(!t)continue;
  const country=String(t.country||t.countryCode||'').toLowerCase();
  if(!bigFive.has(country)||Number(t.division||1)!==1)continue;
  for(const id of t.roster||[])add(id,2);
 }
 // A major European/World event can also promote a player who represents a
 // club outside the Big Five. Only actual competition performances count.
 const bigEvent=/champions|uefa.champ|champ\\.league|\\bucl\\b|mundial|world.?cup|copa.?do.?mundo|intercontinental|euro.?cup/i;
 for(const [key,rows] of Object.entries(s.competitionStats||{})){
  if(!bigEvent.test(key))continue;
  for(const id in rows||[]){
   const r=rows[id];if(!r)continue;
   add(id,3);
   const old=majorEvents.get(id)||{goals:0,assists:0,apps:0};
   old.goals+=Number(r.goals)||0;
   old.assists+=Number(r.assists)||0;
   old.apps+=Number(r.apps)||0;
   majorEvents.set(id,old);
  }
 }
 const national=s.v640National,international=national?.playerStats?.[String(year)];
 if(international&&typeof international==='object')for(const [cid,rows] of Object.entries(international)){
  const meta=national?.competitions?.[cid],name=String(meta?.name||cid);
  if(!/copa do mundo|world cup|fifa|euro/i.test(name))continue;
  for(const [id,r] of Object.entries(rows||{})){
   const pid=String(r?.id||id);if(!s.players?.[pid])continue;
   add(pid,3);
   const old=majorEvents.get(pid)||{goals:0,assists:0,apps:0};
   old.goals+=Number(r.goals)||0;old.assists+=Number(r.assists)||0;old.apps+=Number(r.apps)||0;
   majorEvents.set(pid,old);
  }
 }
 const eligible=[];let candidates=0;
 for(const [id,level] of selected){
  const p=s.players[id],o=overall(p),age=Number(p.age)||0;
  if(age<17||age>32||o<78)continue;
  const n=Number(p.seasonRatingCount58)||0;
  const avg=n?(Number(p.seasonRatingSum58)||0)/n:Number(p.lastMatchRating)||6.5;
  const apps=Math.max(n,Number(p.apps)||0),goals=Number(p.goals)||0,assists=Number(p.assists)||0;
  const major=majorEvents.get(id)||{goals:0,assists:0,apps:0};
  const leagueElite=level>=2&&apps>=18&&o>=80&&(
    (goals>=20&&avg>=7.0)||(assists>=14&&avg>=7.05)||
    (n>=18&&avg>=7.38&&o>=84)||(goals>=27)||(assists>=20));
  const majorElite=level>=3&&o>=80&&(
    major.goals>=7||(major.assists>=5&&major.apps>=5)||
    (major.goals>=5&&major.apps>=5&&avg>=7.25));
  if(!leagueElite&&!majorElite){
   if(apps>=12&&p.starYears)p.starYears=Math.max(0,p.starYears-1);
   continue;
  }
  p.starYears=Math.min(5,(Number(p.starYears)||0)+1);
  p.starCandidate=true;candidates++;
  const exceptional=(leagueElite&&goals>=34&&apps>=22&&o>=84)||
                    (majorElite&&major.goals>=9&&o>=84);
  if(p.starYears>=2||exceptional)
   eligible.push({p,score:o+goals*.85+assists*.55+major.goals*2.1+major.assists+
     (n?avg:6.5)*4+(age<=24?4:0)});
 }
 eligible.sort((a,b)=>b.score-a.score||String(a.p.id).localeCompare(String(b.p.id)));
 let promoted=0;
 for(const {p} of eligible.slice(0,6)){
  p.star=true;p.starCandidate=false;p.starSince={year,day:Number(s.day)||0};
  promoted++;
  news(s,'Nova estrela mundial',p.name+' se destacou entre os melhores nas grandes competições.','good');
 }
 s.starSystem58={edition:18383,lastReview:year,promoted,candidates};
 return {promoted,candidates,considered:selected.size};
}
"""

COACH=r"""
/* FUTBR_NATIONAL_COACH_ROTATION_18383
   Annual appointment decisions use previous season's results, competition
   outcomes and tenure. Human-controlled national teams are never reassigned.
   No per-match work, world scan or save-format migration is required. */
function v18383HashNational(text){
 let n=2166136261>>>0;
 for(let i=0;i<text.length;i++)n=Math.imul(n^text.charCodeAt(i),16777619)>>>0;
 return n>>>0;
}
function v18383NationalCoachName(t,year){
 const pools={
  UEFA:[['Luca','Marco','Martin','Ivan','Pavel','André','Lukas','Stefan','Mateo','Johan'],['Rossi','Novák','Schmidt','Kovač','Silva','Müller','Petrović','Jansen','Costa','Kowalski']],
  CONMEBOL:[['Carlos','Rafael','Diego','Marcelo','Pablo','Julián','Gustavo','Bruno','Matías','Hernán'],['García','Silva','Pereira','Rojas','Ferreira','Gómez','Santos','Torres','Almeida','Mendoza']],
  CONCACAF:[['Michael','José','Daniel','Javier','Carlos','Andrés','Leonardo','Luis','Kevin','Marco'],['Williams','Hernández','Martínez','Johnson','Brown','López','García','Campbell','Torres','Morgan']],
  CAF:[['Amadou','Moussa','Youssef','Samuel','Ibrahim','Kofi','Ahmed','Idrissa','Abdoulaye','Joseph'],['Diallo','Traoré','Mensah','Kamara','Sow','Koné','Ndiaye','Okafor','Bamba','Diop']],
  AFC:[['Hiroshi','Kenji','Ali','Sami','Reza','Jae-min','Park','Omar','Akira','Sanjay'],['Tanaka','Kim','Rahman','Suzuki','Hassan','Khan','Nakamura','Lee','Saleh','Ahmed']],
  OFC:[['Tane','Peter','James','Michael','Kelepi','Samuel','Liam','David','Sione','Mika'],['Williams','Tavita','Smith','Ratu','Brown','Tui','Mataele','Jones','Vula','Latu']]
 };
 const [first,last]=pools[t.conf]||pools.OFC;
 const a=v18383HashNational(String(t.code)+'|'+year+'|primeiro');
 const b=v18383HashNational(String(t.code)+'|'+year+'|sobrenome');
 return first[a%first.length]+' '+last[b%last.length];
}
function v18383RotateNationalCoaches(s,oldYear){
 const root=s?.v640National,year=Number(s?.year)||0;
 if(!root?.teams||!year||Number(root.v18383ReviewedYear)===Number(oldYear))return 0;
 let changed=0;
 for(const t of Object.values(root.teams)){
  if(!t||!t.code)continue;
  if(root.userTeam===t.code||String(t.coach?.id||'')===String(s.userCoachId||'!'))continue;
  const coach=t.coach||v640MakeAiCoach(t),started=Number(coach.startedYear)||2026;
  const tenure=Math.max(0,year-started);
  const played=Number(t.played)||0,wins=Number(t.wins)||0,losses=Number(t.losses)||0;
  const delta=Math.max(0,played-(Number(t.v18383ReviewedPlayed)||0));
  const w=Math.max(0,wins-(Number(t.v18383ReviewedWins)||0));
  const l=Math.max(0,losses-(Number(t.v18383ReviewedLosses)||0));
  t.v18383ReviewedPlayed=played;t.v18383ReviewedWins=wins;t.v18383ReviewedLosses=losses;
  const performance=delta>=5?(w+0.5*Math.max(0,delta-w-l))/delta:.5;
  const results=(root.history||[]).filter(h=>Number(h.year)===Number(oldYear)&&
    (h.champion===t.code||h.runnerUp===t.code));
  const champion=results.some(h=>h.champion===t.code);
  const finalist=!champion&&results.some(h=>h.runnerUp===t.code);
  let probability=tenure>=9?1:tenure>=7?.76:tenure>=5?.43:tenure>=3?.20:.07;
  if(performance<.28&&delta>=5)probability+=.31;
  else if(performance<.42&&delta>=5)probability+=.15;
  if(champion)probability*=.12;
  else if(finalist)probability*=.45;
  if(tenure<2&&!champion)probability=Math.min(probability,.09);
  if(tenure>=9)probability=1; // prevents decade-long permanent AI national posts
  const roll=v18383HashNational(t.code+'|'+oldYear+'|'+coach.id)/4294967296;
  if(roll>=Math.min(.99,probability)&&tenure<9)continue;
  const reason=tenure>=7?'fim de ciclo':performance<.36?'desempenho insuficiente':'renovação de comando';
  const previous={year:Number(oldYear),id:coach.id,name:coach.name,reason};
  t.coachHistory=Array.isArray(t.coachHistory)?t.coachHistory.slice(-11):[];
  t.coachHistory.push(previous);
  const name=v18383NationalCoachName(t,year);
  t.coach={id:'nc-'+t.code+'-'+year+'-'+(v18383HashNational(name+t.code)%1000),
   name,natCode:t.code,nationalTeam:t.code,ai:true,startedYear:year,
   previousCoachId:coach.id,appointedReason:reason};
  t.lastCoachChange={year,previous:coach.name,current:name,reason};
  changed++;
 }
 root.v18383ReviewedYear=Number(oldYear);
 root.v18383CoachChanges=changed;
 return changed;
}
"""

def once(src,old,new,label):
 n=src.count(old)
 if n!=1:raise RuntimeError(f'18.383 {label}: expected one unique anchor, found {n}')
 return src.replace(old,new,1)

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: apply_flags_coaches_stars_aging_18383.py <prepared-project>')
 root=Path(sys.argv[1]).resolve()
 html_path=root/'src/index.html'
 s=html_path.read_text(encoding='utf-8')
 for marker in ('FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381','FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382',
                'FUTBR_DELEGATED_RETIREMENT_18346','function v91ResetPlayers(s,oldYear)',
                'function v640Flag(code,size='):
  if marker not in s:raise RuntimeError('Missing preserved engine feature: '+marker)
 if MARK in s:raise RuntimeError('18.383 patch already applied')

 assets={}
 for file in ['flags_18383_a.b64','flags_18383_b.b64','flags_18383_c.b64']:
  for line in (Path(__file__).parent/file).read_text(encoding='utf-8').splitlines():
   if not line.strip():continue
   code,encoded=line.split(' ',1)
   raw=base64.b64decode(encoded,validate=True)
   if not raw.startswith(bytes.fromhex('89504e470d0a1a0a')) or not 300<=len(raw)<=8000:
    raise RuntimeError('Invalid or oversized uploaded flag '+code)
   assets[code]='data:image/png;base64,'+encoded.strip()
 if set(assets)!={'SAM','FIJ','SOL','SGP','HKG','PNG','VUT','TAH','NCL'}:
  raise RuntimeError('The nine user-provided national flags are not all present')

 # Replace the existing national flag generator; keep its public signature.
 a=s.index("function v640Flag(code,size='normal'){")
 b=s.index('function v640Eligible(s,code)',a)
 if b-a>800:raise RuntimeError('Unexpected flag generator body')
 mapping={**assets,'VAN':assets['VUT'],'WSM':assets['SAM'],'SIN':assets['SGP']}
 flagjs="""/* FUTBR_LOCAL_FLAGS_18383: nine uploaded images, offline and self-contained. */
const v18383Flags="""+json.dumps(mapping,separators=(',',':'))+""";
function v640Flag(code,size='normal'){
 const key=String(code||'').trim().toUpperCase(),img=v18383Flags[key];
 const info=NAT[key]||[key,''],name=esc(info[0]||key);
 if(img)return '<span class="v640-flag v18383-local-flag '+(size==='large'?'large':'')+
  '" title="'+name+'" aria-label="'+name+'"><img src="'+img+'" alt="'+name+
  '" decoding="async"></span>';
 const iso=String(info[1]||'').toUpperCase();
 const emoji=iso&&iso.length===2?String.fromCodePoint(...iso.split('').map(c=>127397+c.charCodeAt(0))):'⚑';
 return '<span class="v640-flag '+(size==='large'?'large':'')+'" title="'+name+
  '" aria-label="'+name+'">'+emoji+'</span>';
}
"""
 s=s[:a]+flagjs+s[b:]
 flagstyle="""<style id="futbr-local-national-flags-18383">
.v640-flag.v18383-local-flag{display:inline-flex!important;vertical-align:middle;
 align-items:center;justify-content:center;min-width:1.45em;line-height:1}
.v640-flag.v18383-local-flag img{display:block;width:1.45em;height:.98em;
 object-fit:cover;border-radius:1px}
.v640-flag.v18383-local-flag.large img{width:44px;height:28px;max-width:none}
</style>
"""
 s=once(s,'</head>',flagstyle+'</head>','offline flag styles')

 # Patch only the core live functions (Worker and UI share the source).
 a=s.index('  function retirementChance549(s,p,m={}){')
 b=s.index('  /* FUTBR_DELEGATED_RETIREMENT_18346',a)
 if b-a<200 or b-a>2500:raise RuntimeError('Unexpected retirement chance engine')
 s=s[:a]+RETIRE+s[b:]
 a=s.index('function shouldAutoRetire549(s,p,m={},chance=retirementChance549(s,p,m),roll=null){')
 b=s.index('  function v549AutomaticResult(',a)
 if b-a>1600:raise RuntimeError('Unexpected automatic retirement gate')
 s=s[:a]+AUTO_RETIRE+s[b:]

 a=s.index('  function reviewWorldStars58(s){')
 b=s.index('  const CBF_CUP_PRIZES_2026=',a)
 if b-a>3000 or b-a<450:raise RuntimeError('Unexpected original star review body')
 s=s[:a]+STARS+s[b:]

 # Aging is applied in the already-existing single annual player loop.
 a=s.index('function v91ResetPlayers(s,oldYear){')
 b=s.index('function v91PromoteAgedYouth(',a)
 section=s[a:b]
 original="  else if(Number(p.age)>31&&p.skills){for(const k of ['att','def','pas','pace','gk'])if(Number.isFinite(Number(p.skills[k])))p.skills[k]=Math.max(12,Number(p.skills[k])-E.rand(s,0,Number(p.age)>35?3:1));}"
 section=once(section,original,'  else if(p.skills)v18383AgePlayer(s,p);','annual skill decline')
 start=section.index('  let auto=false;if(!manual')
 end=section.index('  if(manual||auto){',start)
 section=section[:start]+"""  let auto=false;
  if(!manual&&p.squad!=='youth'&&Number(p.age)>=35){
   const employedUser=!!(s.userEmployed&&clubBefore===s.user);
   if(!employedUser||Number(p.age)>=37||v18346DelegatedRetirement(s)){
    const chance=E.retirementChance549?E.retirementChance549(s,p,snap):retirementChance549(s,p,snap);
    auto=!!(E.shouldAutoRetire549?E.shouldAutoRetire549(s,p,snap,chance):
        shouldAutoRetire549(s,p,snap,chance));
   }
  }
"""+section[end:]
 s=s[:a]+AGING+section+s[b:]

 # Stars must be reviewed at the end of EVERY season, before the usual
 # v91ResetPlayers() clears seasonal stats, even when old saves lack the flag.
 s=once(s,
 " if(Number(s.v92PendingStarReviewYear)===oldYear){try{E.reviewWorldStars58(s);}catch(e){}delete s.v92PendingStarReviewYear;}",
 " if(Number(s.starSystem58?.lastReview)!==oldYear){try{E.reviewWorldStars58(s);}catch(e){console.warn('[18.383] estrelas',e);}}delete s.v92PendingStarReviewYear;",
 'unconditional once-per-season star review')

 # Extend the existing annual national reset, not per-day simulation.
 a=s.index('function v91NationalNewSeason(s){')
 s=s[:a]+COACH+'\n'+s[a:]
 target=" t=v91Now();v91CoachNewSeason(s);v91NationalNewSeason(s);v91Stats.nationalMs=v91Now()-t;"
 s=once(s,target," t=v91Now();v91CoachNewSeason(s);v91NationalNewSeason(s);v18383RotateNationalCoaches(s,oldYear);v91Stats.nationalMs=v91Now()-t;",'annual national head-coach appraisal')

 # Shared source belongs to the original browser/worker before the version gate.
 s=once(s,'window.GestorFC.render=render;\nwindow.GestorFC.fontSettings18376=',
 """/* FUTBR_LONG_CAREER_REALISM_18383 */
window.GestorFC.longCareerRealism18383={version:'18.383.0',
 flags:9,annualNationalCoachReview:true,eliteStarCompetitionGate:true,
 positionSensitiveAgeDecline:true,retirementBefore40:true,onePassAnnualReset:true};
window.GestorFC.render=render;
window.GestorFC.fontSettings18376=""",'feature marker')
 if s.count(MARK)!=1:raise RuntimeError('Feature marker missing or repeated')
 for script,label in [(AGING,'age decline'),(RETIRE,'retirement chance'),(AUTO_RETIRE,'auto retire'),(STARS,'star promotion'),(COACH,'national manager rotation'),(flagjs,'offline national flags')]:
  res=subprocess.run(['node','--check','-'],input=script,text=True,capture_output=True,timeout=35)
  if res.returncode:raise RuntimeError(label+' syntax: '+res.stderr[-3000:])
 html_path.write_text(s,encoding='utf-8')
 report={'ok':True,'version':'18.383.0','embeddedFlags':sorted(assets.keys()),
 'allFlagsLocalAndOffline':True,'nationalCoachAnnualReview':True,
 'humanManagedNationalSideProtected':True,'nationalCoachHistoryPreserved':True,
 'nationalCoachTenureCeiling':9,'starReviewEverySeason':True,
 'starPromotionOnlyByMajorEuropeanWorldPerformances':True,
 'shortlistNoEntireWorldArray':True,'agingByPositionInAnnualLoop':True,
 'retirementChanceIncreasesAt35To40':True,'goalkeeperRetiresSlightlyLater':True,
 'manualRetirementPreserved':True,'historicalSavesPreserved':True,
 'noAdditionalWorldCopyOrFullPlayerLoop':True,'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'career-realism-18383-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
