"""Behavioral A/B of the real Engine's 2029 qualification and calendar builders.

The catalog is real; historical results are explicit deterministic fixtures.
This is a calendar/component benchmark, not a claim that three full seasons
were played or a measurement of the UI's complete season transition.
"""
from __future__ import annotations
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


FIXTURE_JS = r'''
function rankFixture(E,year=2029){
 const s={year,day:0,seed:183742029,seasonDone:false,teams:[],coaches:{},players:{},schedule:[],
  internationalHistory:[],worldHistory:[],v652ClubPerformanceHistory:[],v18110LeagueTitles:{},
  cupWinners:{},competitions:{},previousPlacements:{},user:'t18',userEmployed:false,userCoachId:'c18',
  vacation:{},news:[],finance:[],options:{}};
 for(const [i,c] of E.WorldCatalog.clubs.entries()){
  const t={...c,roster:[],academy:[],proReserve:[],stats:{p:0,w:0,d:0,l:0,gf:0,ga:0,pts:0,form:[]}};
  s.teams.push(t);s.coaches['c'+i]={id:'c'+i,club:c.id,reputation:c.base,
   titles:i%12===0?[year-3,year-2,year-1].map(y=>({club:c.id,year:y,key:'cup:'+c.country,label:'Copa '+c.country,points:100})):[]};
 }
 for(const c of E.WorldCatalog.countries)s.previousPlacements[c.id]=s.teams.filter(t=>t.country===c.id&&Number(t.division)===1).sort((a,b)=>b.base-a.base).map(t=>t.id);
 for(const y of [year-3,year-2,year-1]){
  const clubs={};s.teams.forEach((t,i)=>clubs[t.id]={leaguePoints:Math.round(((i*17+y)%200))/10,cupPoints:((i+y)%40)/10});
  s.v652ClubPerformanceHistory.push({year:y,clubs});
  for(const conf of E.CONF_KEYS){const ids=s.teams.filter(t=>E.country(t.country)?.confederation===conf&&Number(t.division)===1).sort((a,b)=>b.base-a.base).map(t=>t.id);
   s.internationalHistory.push({year:y,id:E.MAIN_CUP[conf],name:E.MAIN_CUP[conf],
    champion:ids[(y-(year-3))%Math.min(3,ids.length)],points:Object.fromEntries(ids.slice(0,32).map((id,i)=>[id,60-i]))});}
 }
 s.internationalHistory.push({year:year-1,id:'sud',name:'Sul-Americana',champion:'t1',points:{t1:40}});
 return s;
}
'''


HARNESS = r'''
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const {performance}=require('node:perf_hooks');
const a=require(process.argv[2]),b=require(process.argv[3]);
const digest=x=>crypto.createHash('sha256').update(JSON.stringify(x)).digest('hex');
const normalized=x=>JSON.parse(JSON.stringify(x));
function reset(){globalThis.__rankCount=0;globalThis.__rankCapture=null;}
function timed(E,op){const s=rankFixture(E);let scans=0;const coaches=s.coaches;
 Object.defineProperty(s,'coaches',{get(){scans++;return coaches;},configurable:true});reset();
 const history=()=>digest({international:s.internationalHistory,world:s.worldHistory,domestic:s.v652ClubPerformanceHistory,official:s.v18110LeagueTitles});
 const beforeHistory=history();
 const start=performance.now(),result=op(E,s),ms=performance.now()-start;
 assert.equal(history(),beforeHistory,'ranking/calendar setup altered archived history');
 return {state:s,result,metrics:{ms,profileCalls:globalThis.__rankCount,coachEnumerations:scans,rssBytes:process.memoryUsage().rss}};
}
const oldSelect=timed(a,(E,s)=>E.selectWorld(s)),newSelect=timed(b,(E,s)=>E.selectWorld(s));
assert.deepEqual(normalized(newSelect.result),normalized(oldSelect.result),'qualified clubs, reasons and profiles changed');
assert(newSelect.metrics.profileCalls<oldSelect.metrics.profileCalls/5,'rank profiles still rebuilt by every comparator');
assert(newSelect.metrics.coachEnumerations<oldSelect.metrics.coachEnumerations/20,'coach scan still scales with comparator calls');
assert.equal(newSelect.result.ids.length,32);assert.equal(new Set(newSelect.result.ids).size,32);
assert.equal(newSelect.state.teams.length,5627);
assert.equal(b.seasonRankAudit18374().active,false);

// Current-year and legacy name-only titles must retain source priority, labels,
// all tie-break fields, and duplicate-name behavior, not merely the sorted IDs.
const x=rankFixture(a),y=rankFixture(b),ids=[...x.teams.slice(0,18),...x.teams.filter(t=>t.country==='eng').slice(0,12)].map(t=>t.id);
for(const s of [x,y]){
 s.seasonDone=true;s.day=120;
 for(const id of ids){const t=s.teams.find(t=>t.id===id);t.stats={p:38,w:16,d:8,l:14,gf:45,ga:40,pts:56,form:[]};}
 s.teams[0].name='Nome Duplicado';s.teams[1].name='Nome Duplicado';
 s.coaches.c0.titles.unshift({year:2029,key:'cup:bra',clubName:'NOME DUPLICADO',label:'Primeiro titulo legado',points:90});
 s.coaches.c1.titles.unshift({year:2029,key:'cup:bra',club:'t0',label:'Duplicata deve perder',points:90});
 s.worldHistory=[{year:2028,countries:[{country:'bra',champion:'t0',secondChampion:'t24',cup:'t2'}]}];
 s.cupWinners={bra:'t0',eng:'t40'};
 s.schedule=[{type:'league',fixtures:[{home:'t0',away:'t1',country:'bra',division:1,result:{home:1,away:0}},{home:'t40',away:'t41',country:'eng',division:1,result:{home:0,away:0}}]}];
 s.competitions={ucl:{id:'ucl',conf:'UEFA',name:'Liga dos Campeoes',champion:'t41',standings:{t41:{pts:20}},rounds:{}}};
 s.v18110LeagueTitles={'official':{clubId:'t0',year:2029,key:'league:bra:1',label:'Campeao oficial'},'older':{clubId:'t5',year:2027,key:'cup:bra',label:'Registro anterior'}};
}
let currentChecks=0;
for(const conf of [null,'UEFA','CONMEBOL']){
 globalThis.__rankCapture=[];const expected=a.__originalSort(x,ids,conf),oldProfiles=globalThis.__rankCapture;globalThis.__rankCapture=[];
 const actual=b.__batchSort(y,ids,conf),fastProfiles=globalThis.__rankCapture;globalThis.__rankCapture=null;
 assert.deepEqual(actual,expected,'current title order');
 const originals=new Map(oldProfiles.map(p=>[p.id,normalized(p)]));
 for(const p of fastProfiles)assert.deepEqual(normalized(p),originals.get(p.id),'profile mismatch for '+p.id);
 currentChecks++;
}
// Mutating a title in the same year/day must be visible on the very next call.
for(const s of [x,y])s.coaches.c2.titles.push({club:'t3',year:2029,key:'cwc',label:'Novo Mundial',points:1000});
assert.deepEqual(b.__batchSort(y,ids),a.__originalSort(x,ids));
const winBefore=b.rankProfile633(y,'CONMEBOL','t3').totalPoints;
for(const s of [x,y]){s.year=2030;s.day=0;s.seasonDone=false;s.schedule=[];s.competitions={};s.cupWinners={};}
assert.deepEqual(b.__batchSort(y,ids),a.__originalSort(x,ids));
assert.equal(b.seasonRankAudit18374().active,false);

globalThis.__throwRankComparison=true;assert.throws(()=>b.__batchSort(y,ids),/injected comparator failure/);
globalThis.__throwRankComparison=false;assert.equal(b.seasonRankAudit18374().active,false,'operation cache survived failure');
assert.deepEqual(b.__batchSort(y,ids),a.__originalSort(x,ids),'operation after failure is stale');

// Original full 2029 calendar builders, including all continental draws and the
// CWC country/confederation constraints, run in both engines with the same seed.
const oldCalendar=timed(a,(E,s)=>{E.setupSeason(s);return {seed:s.seed,schedule:s.schedule,competitions:s.competitions,cupProgress:s.cupProgress,cupDraws:s.cupDraws,braLower:s.braLower};});
const newCalendar=timed(b,(E,s)=>{E.setupSeason(s);return {seed:s.seed,schedule:s.schedule,competitions:s.competitions,cupProgress:s.cupProgress,cupDraws:s.cupDraws,braLower:s.braLower};});
assert.equal(digest(newCalendar.result),digest(oldCalendar.result),'calendar, RNG state, participants or pots differ');
const audit=b.worldAudit631(newCalendar.state);
assert.deepEqual(audit.groups,Array(8).fill(4));assert.deepEqual(audit.potSizes,[8,8,8,8]);
assert.equal(audit.associationClashes.length,0);assert.equal(audit.confederationClashes.length,0);
assert(newCalendar.metrics.profileCalls<oldCalendar.metrics.profileCalls/4);
assert(newCalendar.metrics.coachEnumerations<oldCalendar.metrics.coachEnumerations/20);
assert.equal(b.seasonRankAudit18374().active,false);
console.log(JSON.stringify({ok:true,version:'18.374.0',fixture:'Real Engine and 5627-club catalog; deterministic synthetic historical standings/titles; this measures calendar components, not full UI rollover',
 clubs:x.teams.length,qualification:{baseline:oldSelect.metrics,patched:newSelect.metrics,ids:newSelect.result.ids},
 calendar:{baseline:oldCalendar.metrics,patched:newCalendar.metrics,sha256:digest(newCalendar.result),days:newCalendar.state.schedule.length,audit},
 originalEngineExecuted:true,originalFullCatalog:true,sameWorldCupQualifiersAndReasons:true,sameCalendarAndRandomState:true,
 currentAndHistoricalTitleProfilesIdentical:currentChecks===3,legacyNameOnlyAndDuplicateTitlesPreserved:true,
 sameDayChangesVisible:true,yearChangeVisible:true,cacheReleasedAfterSuccessAndFailure:true,
 profileWorkBoundedByClubs:true,coachScansBoundedBySorts:true,worldCupDrawRulesPreserved:true,
 noHistoryDeleted:true,testHooksNotShipped:true}));
'''


def engine_source(html: str, patched: bool) -> str:
    catalog=json.loads(html.split('const WorldCatalog = ',1)[1].split(';\n',1)[0])
    # The exact authoritative catalog normalization preceding Engine in the game.
    assert 'v18163DupASA' in html
    catalog['clubs']=[c for c in catalog['clubs'] if c['id']!='v691_bra_agremiacao-sportiva-arapiraquense_17aitfs']
    start=html.index('const Engine = (() => {');end=html.index("if(typeof module!=='undefined'&&module.exports)",start)
    engine=html[start:end]
    at=engine.rfind('  return {')
    hook=r'''
    /* TEST_ONLY_ROLLOVER_18374 */
    const testProfile=v633RankProfile;
    v633RankProfile=function(...args){globalThis.__rankCount=(globalThis.__rankCount||0)+1;const p=testProfile(...args);if(globalThis.__rankCapture)globalThis.__rankCapture.push(p);return p;};
    const testCompare=v633CompareProfiles;
    v633CompareProfiles=function(...args){if(globalThis.__throwRankComparison)throw Error('injected comparator failure');return testCompare(...args);};
'''
    engine=engine[:at]+hook+engine[at:]
    at=engine.rfind('  return {')+len('  return {')
    exports="__originalSort:(s,ids,conf=null)=>[...ids].sort((a,b)=>conf?v633RankCompare(s,conf,a,b):v633GlobalRankCompare(s,a,b)),"
    if patched:exports+='__batchSort:v18374RankClubIds,'
    engine=engine[:at]+exports+engine[at:]
    return 'const WorldCatalog='+json.dumps(catalog,ensure_ascii=False)+';const BundledRosters={};\n'+engine+'\nmodule.exports=Engine;'


def main() -> None:
    if len(sys.argv) not in (2,3):raise SystemExit('usage: test_season_rollover_18374.py <project> [baseline-html]')
    root=Path(sys.argv[1]).resolve();source=(root/'src/index.html').read_text(encoding='utf-8')
    baseline=Path(sys.argv[2]).read_text(encoding='utf-8') if len(sys.argv)==3 else (root/'baseline-18373.html').read_text(encoding='utf-8')
    assert 'FUTBR_SEASON_RANK_BATCH_18374' in source and 'FUTBR_SEASON_RANK_BATCH_18374' not in baseline
    assert 'TEST_ONLY_ROLLOVER_18374' not in source
    result={'ok':False,'version':'18.374.0','sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
            'baselineSourceSha256':hashlib.sha256(baseline.encode('utf-8')).hexdigest()}
    report=root/'season-rollover-18374-tests.json'
    try:
        with tempfile.TemporaryDirectory(prefix='futbr-rollover-18374-') as temp:
            d=Path(temp);old=d/'old.js';new=d/'new.js';run=d/'run.cjs'
            old.write_text(engine_source(baseline,False),encoding='utf-8');new.write_text(engine_source(source,True),encoding='utf-8')
            run.write_text(FIXTURE_JS+'\n'+HARNESS,encoding='utf-8')
            executed=subprocess.run(['node',str(run),str(old),str(new)],text=True,capture_output=True,timeout=300)
            if executed.returncode:raise RuntimeError(executed.stderr[-4500:])
            result.update(json.loads(executed.stdout.strip().splitlines()[-1]))
    except Exception as error:result['error']=str(error)
    report.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['ok']:raise SystemExit('18.374 real calendar/ranking regression failed')


if __name__=='__main__':main()
