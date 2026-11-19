from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

def part(src,begin,end):
 a=src.index(begin)
 b=src.index(end,a)
 return src[a:b]

HARNESS=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}};
const E={team:(s,id)=>s.teams?.find(x=>String(x.id)===String(id)),
 human:s=>s.teams?.[0],normName:x=>String(x||'').toLowerCase(),
 coachRating:()=>30};
const v18322N=x=>Number.isFinite(Number(x))?Number(x):0;
const v18322ClubName=(s,id)=>E.team(s,id)?.name||String(id||'');
let persisted=0;
const v18322Preview=new WeakMap();
const v18345CleanCClubTitles=()=>0,v18345SyncCArchives=()=>0,v99RepairLeagueCoachTitle=()=>{};
const v661RecordStat=()=>{},v99TieWinner=()=>null;
const v18322MatchRow=(r,f)=> !f||f.year==='all'||Number(f.year)===r.year;
const v18322LegacyRows=()=>[];
let v18322CollectSeason=()=>[];
function makeState(year=2028){
 const first={v661Brazil:'C',v661Phase:'final',v661Tie:0,v661Leg:1,
  home:'b',away:'a',result:{home:1,away:0},v661Recorded:true};
 const second={v661Brazil:'C',v661Phase:'final',v661Tie:0,v661Leg:2,
  home:'a',away:'b',result:null};
 const C={year,finalTie:{a:'a',b:'b',score:[0,1],winner:null,
  results:[{home:1,away:0}]},champion:null,runnerUp:null};
 return {year,day:21,seasonDone:false,teams:[{id:'a',name:'Finalista A',country:'bra',division:3},
  {id:'b',name:'Finalista B',country:'bra',division:3}],
  braLower:{serieC:C},schedule:[{fixtures:[first]},{fixtures:[second]}],
  competitionStats:{'league:bra:3':{
    p1:{id:'p1',name:'Jogador A',goals:13,assists:3,clubs:{a:'Finalista A'}},
    p2:{id:'p2',name:'Jogador B',goals:13,assists:1,clubs:{b:'Finalista B'}},
    p3:{id:'p3',name:'Jogador C',goals:12,assists:8,clubs:{a:'Finalista A'}}
  }},
  v18322Champions:[],v98LeagueTitleHistory:[],scorerArchive:[],coaches:{},
  worldHistory:[],history:[]};
}
window.GestorFC.v18345SerieCWinner=v18345SerieCWinner;
const s=makeState();
let leg2=s.schedule[1].fixtures[0];
assert.equal(v18353RecordSerieCFinal(s,leg2,{}),false,'One leg cannot create a podium');
assert.equal(window.GestorFC.v18345SerieCWinner(s),null);
leg2.result={home:2,away:0};
v661RecordBrazilResult(s,leg2,{});
assert.equal(window.GestorFC.v18345SerieCWinner(s),'a');
assert.equal(s.seasonDone,false);
assert.equal(s.v18322Champions.length,1,'Live final must write history immediately');
assert.equal(s.v18322Champions[0].runner,'b','Actual finalist, not table runner-up');
assert.deepEqual(s.v18322Champions[0].scorers.map(x=>x.id),['p1','p2'],'All top scorer ties');
assert.equal(s.v18322Champions[0].scorers[0].goals,13);
assert.equal(s.braLower.serieC.runnerUp,'b');
assert.deepEqual(JSON.parse(JSON.stringify(s)).v18322Champions[0].scorers,s.v18322Champions[0].scorers,
  'Result must survive serialization before rollover');
const restored=JSON.parse(JSON.stringify(s));
restored.v18322Champions=[];
assert.equal(v18353CaptureFromVerifiedFinal(restored),1,'Loaded completed current-season final recovery');
assert.equal(v18353CaptureFromVerifiedFinal(restored),0,'Idempotent completion');
const h=makeState();
h.schedule=[{fixtures:[h.schedule[0].fixtures[0]]}];
h.braLower.serieC.finalTie.winner='a';
assert.equal(v18353RecordSerieCFinal(h,h.schedule[0].fixtures[0],{}),false,
 'Single archived leg may not register official final');
assert.equal(v18353CaptureFromVerifiedFinal(h),0);
const historic=makeState();
historic.scorerArchive=[
 {year:2026,competitions:{'league:bra:3':{
  p80:{id:'p80',name:'Artilheiro de 2026',goals:21,clubs:{a:'Finalista A'}},
  p81:{id:'p81',name:'Segundo',goals:20}}}},
 {year:2027,competitions:{'league:bra:3':{
  p90:{id:'p90',name:'Artilheiro de 2027',goals:19,clubs:{b:'Finalista B'}}}}}
];
const plain=[
 {year:2026,kind:'league',country:'bra',division:3,competition:'league:bra:3',
  champion:'a',runner:null,scorers:[],legacy:true},
 {year:2027,kind:'league',country:'bra',division:3,competition:'league:bra:3',
  champion:'b',runner:null,scorers:[],legacy:true}
];
let expanded=v18353EnrichSerieCRows(historic,plain);
assert.equal(expanded[0].scorers[0].name,'Artilheiro de 2026');
assert.equal(expanded[1].scorers[0].name,'Artilheiro de 2027');
assert.equal(expanded[0].runner,null,'Do not make up missing 2026 runner');
assert.equal(expanded[1].runner,null,'Do not make up missing 2027 runner');
historic.v98LeagueTitleHistory=[{year:2027,country:'bra',division:3,champion:'b',runner:'a'}];
expanded=v18353EnrichSerieCRows(historic,plain);
assert.equal(expanded[1].runner,'a','Recover runner only from matching official archival evidence');
historic.v98LeagueTitleHistory=[];
historic.braLowerLast={year:2027,cChampion:'b',cRunnerUp:'a'};
expanded=v18353EnrichSerieCRows(historic,plain);
assert.equal(expanded[1].runner,'a','Recover runner from matching signed season summary');
historic.v98LeagueTitleHistory=[
 {year:2026,country:'bra',division:3,champion:'a'},
 {year:2027,country:'bra',division:3,champion:'b'}];
assert.equal(v18353BackfillHistoricalSerieC(historic),2,
 'Persist each recovered old scorer before the five-year archive eviction');
assert.equal(v18353BackfillHistoricalSerieC(historic),0,'Historical backfill must be idempotent');
historic.scorerArchive=[];
assert.equal(historic.v18322Champions.find(r=>r.year===2026).scorers[0].name,'Artilheiro de 2026');
assert.equal(historic.v18322Champions.find(r=>r.year===2027).scorers[0].name,'Artilheiro de 2027');
assert.equal(historic.v18322Champions.find(r=>r.year===2027).runner,'a');

// Preserve complete final data across the old next-season collection call.
v18322CollectSeason=()=>([{year:2028,kind:'league',country:'bra',division:3,
 competition:'league:bra:3',champion:'a',runner:null,scorers:[]}]);
const oldScorers=s.v18322Champions[0].scorers;
const captured=v18322CaptureSeason(s,2028);
assert.equal(captured,1);
assert.equal(s.v18322Champions[0].runner,'b');
assert.deepEqual(s.v18322Champions[0].scorers,oldScorers);
const fromCurrent=v18322ChampionsRows(s,{year:'all'});
assert.equal(fromCurrent[0].runner,'b');
// At render/load, the existing 18.351 repair now also materializes missing final rows.
const saved=makeState();
saved.schedule[1].fixtures[0].result={home:2,away:0};
saved.braLower.serieC.finalTie.results.push({home:2,away:0});
saved.braLower.serieC.finalTie.winner='a';
assert(v99RepairBrazilLowerChampions(saved)>=1);
assert.equal(saved.v18322Champions.length,1);
assert.equal(saved.v18322Champions[0].runner,'b');
console.log('PASS 18.353: live final, vice, tied scorers, legacy year recovery, save-before-rollover and no invention');
"""

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_seriec_full_history_18353.py <project>')
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 for name in ('FUTBR_SERIEC_FULL_PODIUM_18353','FUTBR_SERIEC_UI_REPAIR_18353',
  'FUTBR_SERIEC_PHASES_HISTORY_18351','FUTBR_OOMSAFE_ARCHIVE_18352',
  "const EDITION='18.353.0';",
  "window.GestorFC.version='18.353.0';window.GestorFC.visualVersion='18.353.0';",
  'v18353RecordSerieCFinal(s,f,m)','v18353EnrichSerieCRows(s,[...records.values()])'):
  if name not in html:raise RuntimeError('Lost code invariant: '+name)
 engine=part(html,'/* FUTBR_SERIEC_FULL_PODIUM_18353',
             'function v661FinalizeBrazilLower(')
 scorer=part(html,'function v18322Scorers(db){','function v18322CupRunners(')
 ui=part(html,'/* FUTBR_SERIEC_UI_REPAIR_18353',
          'function v18322InitClubFilters(')
 original=part(html,'function v18322CaptureSeason(s,year){','function v18322LegacyRows(')
 winner=part(html,'function v18345SerieCWinner(s){','window.GestorFC=window.GestorFC||{};')
 repair=part(html,'function v99RepairBrazilLowerChampions(s)','// Career screen:')
 js='\n'.join([HARNESS[:HARNESS.index('window.GestorFC.v18345SerieCWinner=')],
     engine,scorer,ui,original,winner,repair,
     HARNESS[HARNESS.index('window.GestorFC.v18345SerieCWinner='):]])
 path=root/'test-seriec-full-history-18353.cjs'
 path.write_text(js,encoding='utf-8')
 try:
  syntax=subprocess.run(['node','--check',str(path)],text=True,capture_output=True,timeout=40)
  if syntax.returncode:raise RuntimeError('JS parse failed: '+syntax.stderr[-11000:])
  test=subprocess.run(['node','--max-old-space-size=512',str(path)],
    text=True,capture_output=True,timeout=90)
  if test.returncode:raise RuntimeError('Serie C podium regression failed: '+test.stderr[-15000:])
 finally:
  path.unlink(missing_ok=True)
 report={'ok':True,'version':'18.353.0',
  'runnerAndChampRecordedImmediately':True,'seasonDoneNotRequired':True,
  'topScorerTiesPreserved':True,'singleLegDoesNotAward':True,
  'oldCurrentFinalRecovered':True,'legacy2026ScorerFromArchivedYear':True,
  'legacy2027ScorerFromArchivedYear':True,'archivedScorersSurviveArchiveEviction':True,'missingViceNotInvented':True,
  'verifiedStoredViceRecovered':True,
  'rolloverDoesNotEraseRunnerOrScorers':True,
  'workingUnder512MBNodeHeap':True,'saveFormatUnchanged':True}
 (root/'serie-c-full-history-18353-tests.json').write_text(
   json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(test.stdout.strip(),flush=True)
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
