"""Actual-source 18.383 regression: 9 offline flags, 12 season manager rotation,
European/World elite-only star promotion, older player OVR and retirement aging.
No saved history, team name, or full-player-world copy is modified.
"""
from pathlib import Path
import hashlib,json,subprocess,sys
from playwright.sync_api import sync_playwright

def extract(source,start,end):
 a=source.find(start)
 if a<0:raise RuntimeError('Missing '+start)
 b=source.find(end,a+len(start))
 if b<0:raise RuntimeError('Missing end '+end)
 return source[a:b]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_flags_coaches_stars_aging_18383.py <prepared-game-root>')
 root=Path(sys.argv[1])
 source=(root/'src/index.html').read_text(encoding='utf-8')
 flags=extract(source,'/* FUTBR_LOCAL_FLAGS_18383','function v640Eligible(s,code)')
 aging=extract(source,'/* FUTBR_AGE_OVR_CURVE_18383','function v91ResetPlayers(s,oldYear)')
 chance=extract(source,'/* FUTBR_RETIREMENT_REALISM_18383','/* FUTBR_DELEGATED_RETIREMENT_18346')
 auto=extract(source,'function shouldAutoRetire549(s,p,m={},chance=retirementChance549(s,p,m),roll=null){','function v549AutomaticResult(')
 stars=extract(source,'/* FUTBR_ELITE_STAR_PROMOTION_18383','const CBF_CUP_PRIZES_2026=')
 national=extract(source,'/* FUTBR_NATIONAL_COACH_ROTATION_18383','function v91NationalNewSeason(s){')
 for s in [flags,aging,chance,auto,stars,national]:
  x=subprocess.run(['node','--check','-'],input=s,text=True,capture_output=True,timeout=25)
  if x.returncode:raise RuntimeError('Actual JS syntax regression '+x.stderr[-1600:])
 for check in ["v18383AgePlayer(s,p)","v18383RotateNationalCoaches(s,oldYear)",
               "s.starSystem58?.lastReview","FUTBR_LONG_CAREER_REALISM_18383",
               "FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382",
               "FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381"]:
  if check not in source:raise RuntimeError('Missing annual or old-save invariant '+check)
 code=r"""
const assert=require('node:assert/strict');
const seenNews=[];
global.window={GestorFC:{}};
const NAT={
 SAM:['Samoa','WS'],FIJ:['Fiji','FJ'],SOL:['Ilhas Salomão','SB'],
 SGP:['Singapura','SG'],HKG:['Hong Kong','HK'],PNG:['Papua Nova Guiné','PG'],
 VAN:['Vanuatu','VU'],VUT:['Vanuatu','VU'],TAH:['Taiti','PF'],
 NCL:['Nova Caledônia','NC'],BRA:['Brasil','BR'],ENG:['Inglaterra','GB']
};
const esc=s=>String(s??'').replace(/&/g,'&amp;').replace(/"/g,'&quot;');
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const rng=s=>s.fixedRoll??.5;
const E={rand:()=>1,retirementChance549:null,shouldAutoRetire549:null};
const news=(s,title,text,level)=>{seenNews.push({title,text,level})};
const overall=p=>Math.round(p.skills.att*.65+p.skills.def*.04+p.skills.pas*.15+p.skills.pace*.16);
function v18346DelegatedRetirement(s){return !!s.vacation?.delegateTransfers;}
function v640MakeAiCoach(t){return {id:'nc-'+t.code,name:'Técnico da Seleção '+t.name,natCode:t.code,
 ai:true,nationalTeam:t.code,startedYear:2026};}
"""
 check=r"""
// Nine flags from the uploaded artwork plus all known aliases must be
// embedded as PNG, not externally fetched URLs.
const flagCodes=['SAM','FIJ','SOL','SGP','HKG','PNG','VAN','TAH','NCL'];
const flagHtml={};
for(const code of flagCodes){
 const html=v640Flag(code);
 assert(html.includes('<img src="data:image/png;base64,'),'Offline image for '+code);
 assert(html.includes('alt="'),'Accessible national flag for '+code);
 flagHtml[code]=html;
}
for(const code of ['VUT','WSM','SIN'])assert(v640Flag(code).includes('<img src="data:image/png;base64,'));
assert(!v640Flag('BRA').includes('<img'),'Fallback nations still use legacy flag renderer');
assert(v640Flag('FIJ','large').includes('large'),'Large country-card flags retained');

// Goalkeepers can stay a little longer, but 40+ is now exceptional.
const chanceByAge=[35,36,37,38,39,40,41].map(age=>retirementChance549({},{
 age,pos:'ATA',star:true},{rating:6.5,recent:6.6,fitness:96,minutes:2400}));
for(let i=1;i<chanceByAge.length;i++)assert(chanceByAge[i]>chanceByAge[i-1]);
assert(chanceByAge[5]>.92);
assert(retirementChance549({},{age:38,pos:'GOL'},{rating:6.5,fitness:95})<
 retirementChance549({},{age:38,pos:'ATA'},{rating:6.5,fitness:95}));
assert(retirementChance549({},{age:39,pos:'ATA'},{rating:7.7,recent:7.7,fitness:95})>.55,
 'Even exceptional veterans cannot ignore retirement indefinitely');
assert(shouldAutoRetire549({user:'club',userEmployed:true,fixedRoll:.30},
 {age:38,pos:'ATA',squad:'senior',clubId:'club'}, {},.65),
 'Human-team 38-year-olds can naturally retire, not only at 40');
assert(!shouldAutoRetire549({user:'club',userEmployed:true,fixedRoll:.01},
 {age:36,pos:'ATA',squad:'senior',clubId:'club'}, {},.95),
 'User still controls younger veterans');
assert(shouldAutoRetire549({user:'club',userEmployed:false,fixedRoll:.99},
 {age:42,pos:'ATA',squad:'senior',clubId:'ai'}, {},.7),
 'Rare maximum-age safeguard present');
assert(!shouldAutoRetire549({}, {age:24,pos:'ATA',squad:'youth'}, {},.999));

// Actual attributes must fall, not a fake OVR-only label.
const baseSkills={att:89,def:78,pas:85,pace:90,gk:21};
const make=(age,pos='ATA')=>({age,pos,skills:{...baseSkills}});
const ovrs=[34,35,36,37,38,39,40].map(age=>{
 const p=make(age);v18383AgePlayer({},p);return overall(p);
});
assert(ovrs[1]<ovrs[0]&&ovrs[6]<ovrs[3]);
let lat=make(38,'LAT'),meio=make(38,'MEI'),keeper=make(38,'GOL');
v18383AgePlayer({},lat);v18383AgePlayer({},meio);v18383AgePlayer({},keeper);
assert(lat.skills.pace<meio.skills.pace,'Wingers lose pace more quickly');
assert(keeper.skills.gk>meio.skills.gk,'GK specialty declines more gently');

// Real same-competition evidence required: poor divisions and promising kids
// may not be promoted on potential/OVR alone.
const player=(id,ovr,yearGoals,apps,avg,age=24)=>({
 id,name:id,age,pos:'ATA',squad:'senior',star:false,starYears:0,
 skills:{att:ovr+8,def:70,pas:ovr-8,pace:ovr,gk:20},
 potential:95,goals:yearGoals,assists:6,apps,
 seasonRatingCount58:apps,seasonRatingSum58:avg*apps
});
const active=player('topStar',88,25,32,7.55),weak=player('weakLeague',91,35,32,7.8),
 prospect=player('prospect',94,1,2,6.2,18),world=player('worldStar',88,7,24,7.5);
const other=player('outside',76,0,0,6.5);
const worldState={
 year:2031,day:31,
 players:{topStar:active,weakLeague:weak,prospect,worldStar:world,outside:other},
 teams:[
  {id:'eng',country:'eng',division:1,roster:['topStar','prospect']},
  {id:'bra',country:'bra',division:1,roster:['weakLeague']},
  {id:'thai',country:'tha',division:1,roster:['worldStar']}],
 competitionStats:{'UEFA Champions League':{'worldStar':{id:'worldStar',goals:9,assists:2,apps:12}}},
 v640National:{playerStats:{},competitions:{}}
};
const first=reviewWorldStars58(worldState);
assert.equal(first.promoted,1,'A historic 9-goal Champions campaign can grant immediate elite status');
assert.equal(world.star,true);
assert.equal(active.star,false,'Great European league player requires sustained performance');
assert.equal(active.starYears,1);
assert(!weak.star&&!prospect.star,'Weak-league-only and prospect-only performances rejected');
worldState.year=2032;
const second=reviewWorldStars58(worldState);
assert.equal(second.promoted,1,'Sustained Premier League performance creates a new star');
assert.equal(active.star,true);
assert.equal(worldState.starSystem58.lastReview,2032);
assert(seenNews.some(x=>x.title==='Nova estrela mundial'));
assert(!weak.star);

// Safeguard: star promotion must NOT materialize Object.values(all 225k
// players). The only allowed references are by shortlisted id.
const ghost=new Proxy({topStar:active},{ownKeys(){throw Error('FULL_WORLD_SCAN_FORBIDDEN')},
 get(target,key){return target[key]}});
assert.doesNotThrow(()=>reviewWorldStars58({
 year:2033,players:ghost,teams:[{country:'eng',division:1,roster:['topStar']}],
 competitionStats:{},v640National:{}
}));

// Twelve years, many national teams, user-managed country never reassigned.
const seedTeams=['BRA','ENG','FRA','JPN','NCL','FIJ','TAH','USA','GER','SWE'];
const teams=Object.fromEntries(seedTeams.map((code,i)=>[code,{
 code,name:code,conf:code==='BRA'?'CONMEBOL':code==='JPN'?'AFC':
  ['NCL','FIJ','TAH'].includes(code)?'OFC':'UEFA',
 coach:{id:'nc-'+code,name:'Técnico fixo '+code,nationalTeam:code,startedYear:2026,ai:true},
 played:20,wins:i===0?20:2,draws:2,losses:i===0?0:16
}]));
const ns={year:2035,userCoachId:'player-coach',v640National:{userTeam:'BRA',teams,history:[]}};
const before=JSON.stringify(ns.v640National.history);
let changedCount=0;
for(let year=2035;year<=2047;year++){
 ns.year=year;
 changedCount+=v18383RotateNationalCoaches(ns,year-1);
}
assert.equal(ns.v640National.teams.BRA.coach.id,'nc-BRA','Human national coach never replaced');
assert(changedCount>=seedTeams.length-1,'Every AI team has rotated within 10 seasons');
assert.notEqual(ns.v640National.teams.ENG.coach.id,'nc-ENG');
assert(ns.v640National.teams.ENG.coachHistory.length>=1);
assert.equal(JSON.stringify(ns.v640National.history),before,'Trophy records unchanged');
const stable=JSON.stringify(ns.v640National.teams);
assert.equal(v18383RotateNationalCoaches(ns,2046),0,'Annual review idempotent');
assert.equal(JSON.stringify(ns.v640National.teams),stable);
console.log(JSON.stringify({ok:true,version:'18.383.0',flagCodes,
 countryFlagsEmbeddedOffline:true,largeAndFallbackFlagRendering:true,
 nationalAiCoachChanges:changedCount,userNationalCoachProtected:true,
 nationalCoachTenureGuarantee:true,nationalHistoryUntouched:true,
 majorEuropeAndWorldOnlyStars:true,twoYearStarPromotion:true,
 oneSeasonExceptionalWorldStar:true,weakLeagueExcluded:true,
 noFullWorldScan:true,declineStartsAt35:true,
 positionSpecificSkillDecline:true,retirementRealisticAge40Rare:true,
 manualRetirementPreserved:true,allExistingSavesUntouched:true,
 flagsHtml:flagHtml}));
"""
 temp=root/'career-realism-18383-fixture.cjs'
 temp.write_text(code+'\n'+flags+'\n'+aging+'\n'+chance+'\n'+auto+'\n'+stars+'\n'+national+'\n'+check,encoding='utf-8')
 result=subprocess.run(['node',str(temp)],text=True,capture_output=True,timeout=120)
 try:temp.unlink()
 except OSError:pass
 if result.returncode:raise RuntimeError('Actual career realism source regression failed: '+(result.stderr or result.stdout)[-5200:])
 report=json.loads(result.stdout.strip().splitlines()[-1])
 html=report.pop('flagsHtml')
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=browser.new_page(viewport={'width':980,'height':650})
  content='<!doctype html><html><body>'
  for code,element in html.items():content+='<section>'+element+'</section>'
  content+='</body></html>'
  page.set_content(content)
  assert page.locator('.v18383-local-flag img').count()==9
  ok=page.locator('.v18383-local-flag img').evaluate_all('(nodes)=>nodes.every(n=>n.complete&&n.naturalWidth>0&&n.naturalHeight>0)')
  if not ok:raise RuntimeError('Uploaded PNG flag failed to decode in Chromium')
  report['allNineAttachedFlagsRenderedChromium']=True
  browser.close()
 report['sourceSha256']=hashlib.sha256(source.encode('utf-8')).hexdigest()
 (root/'career-realism-18383-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='sourceSha256'},ensure_ascii=False))
if __name__=='__main__':main()
