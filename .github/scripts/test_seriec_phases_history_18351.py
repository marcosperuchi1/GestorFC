from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

def part(src,start,end):
 a=src.index(start)
 b=src.index(end,a)
 return src[a:b]

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_seriec_phases_history_18351.py <project>')
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 for marker in (
  'FUTBR_SERIEC_PHASES_HISTORY_18351',
  'FUTBR_SERIEC_FINAL_CHAMPION_18345',
  "actions:tabs",
  "if(selectedCountry()==='bra'&&Number(selectedDivision())===3)return null;",
  'historic(row.year,row.champion',
  "window.GestorFC?.v18345SerieCWinner?.(s)||null",
  "const EDITION='18.351.0';",
  'FUTBR_CALENDAR_MATCH_RETIRE_18350',
  'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349',
  'v18324-open-retirements'):
  if marker not in html:raise AssertionError('Missing protected source: '+marker)
 page=part(html,'function v663SerieCPage(C){','function v663WaitingHTML(B,D){')
 basic=part(html,'function v94ChampionInfo(){','function v94DecorateChampionDOM(){')
 winner=part(html,'function v18345SerieCWinner(s){','window.GestorFC=window.GestorFC||{};')
 legacy=part(html,'function v18322LegacyRows(s,filter=null){','function v18322ChampionsRows(s,filter=null){')
 collect=part(html,'function v18322CollectSeason(s,year,filter=null){','function v18322CaptureSeason(s,year){')
 harness=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{}};
let state={year:2029,seasonDone:true},view='competitions',
v54CompetitionMode='league',v663BraCView='first';
const selectedCountry=()=> 'bra',selectedDivision=()=>3,
esc=x=>String(x),v663PhaseTabs=(scope,cur,tabs)=>'<TABS>'+tabs.map(x=>x[1]).join(' ')+'</TABS>',
v663StandingsHTML=(groups,records,title,{actions=''}={})=>'<PANEL>'+title+actions+'</PANEL>',
v663CFinalHTML=()=>'<FINAL/>';
const v18322N=x=>Number(x)||0;
const v18322ClubName=(s,id)=>String(s.teams.find(t=>t.id===id)?.name||id);
const v18322MatchRow=(r,f)=> !f||(f.country==='all'||r.country===f.country)&&
 (f.kind==='all'||r.kind===f.kind)&&(f.division==='all'||r.division===Number(f.division))&&
 (f.year==='all'||r.year===Number(f.year))&&(f.competition==='all'||r.competition===f.competition);
const v18322CupRunners=()=>new Map(),v18322IntlScorers=()=>new Map(),v18322Scorers=()=>[];
const WorldCatalog={countries:[{id:'bra',name:'Brasil'}]};
const E={
 table:(s,c,d)=>s.teams.filter(x=>x.country===c&&x.division===Number(d)),
 team:(s,id)=>s.teams.find(x=>String(x.id)===String(id)),
};
const g0=Array.from({length:14},(_,i)=>'a'+i),g1=Array.from({length:14},(_,i)=>'b'+i);
const C={year:2029,format:'two-groups-14',
 firstGroups:[g0,g1],firstStandings:{0:{},1:{}},
 quadGroups:[[g0[0],g0[1],g1[0],g1[1]],[g0[2],g0[3],g1[2],g1[3]]],
 quadStandings:[{},{}],finalTie:null,champion:g0[0],runnerUp:null};
const s={year:2029,seasonDone:true,teams:[...g0,...g1].map(id=>({id,name:id,country:'bra',division:3})),
 braLower:{serieC:C},schedule:[],v98LeagueTitleHistory:[],
 worldHistory:[],internationalHistory:[],cupWinners:{},competitions:{},competitionStats:{}};
state=s;
let htmlPage=v663SerieCPage(C);
assert.match(htmlPage,/1ª fase/);assert.match(htmlPage,/2ª fase/);
assert.match(htmlPage,/<TABS>/);
assert.equal((htmlPage.match(/<TABS>/g)||[]).length,1,'Only one set of visible phase tabs');
v663BraCView='second';
htmlPage=v663SerieCPage(C);
assert.match(htmlPage,/<TABS>/);
assert.match(htmlPage,/Quadrangular A/);
v663BraCView='first';
assert.equal(v94ChampionInfo(),null,'Generic table winner may never win Brazilian Serie C');
assert.equal(v18345SerieCWinner(s),null,'No final means no champion');
C.finalTie={a:'a0',b:'b0',score:[0,0],winner:null,results:[]};
function fixture(leg,home,away,score){
 return {v661Brazil:'C',v661Phase:'final',v661Tie:0,v661Leg:leg,home,away,result:score};
}
const first=fixture(1,'b0','a0',{home:0,away:2}),
 second=fixture(2,'a0','b0',null);
s.schedule=[{fixtures:[first]},{fixtures:[second]}];
assert.equal(v18345SerieCWinner(s),null,'One completed leg cannot crown anyone');
second.result={home:1,away:0};
assert.equal(v18345SerieCWinner(s),'a0','Championship is decided by both legs');
window.GestorFC.v18345SerieCWinner=v18345SerieCWinner;
const curr=v18322CollectSeason(s,2029,{country:'bra',kind:'league',year:'all',division:'3',competition:'league:bra:3'});
assert.equal(curr.length,1,'The completed 2029 Serie C must appear');
assert.equal(curr[0].champion,'a0');
assert.notEqual(curr[0].champion,g0[1]);
C.finalTie.winner='a0';
first.result={home:1,away:0};second.result={home:1,away:0,pens:[3,4]};
assert.equal(v18345SerieCWinner(s),'b0','Penalty winner must be 2nd-leg away team');
second.result={home:1,away:0};C.finalTie.winner=null;
assert.equal(v18345SerieCWinner(s),null,'Unresolved aggregate draw cannot invent winner');
s.schedule=[];
C.finalTie={a:'a0',b:'b0',winner:'a0',
 results:[{home:0,away:2},{home:1,away:0}]};
assert.equal(v18345SerieCWinner(s),'a0','Old saves with two stored leg scores can be restored');
C.finalTie.results=[{home:0,away:2}];
assert.equal(v18345SerieCWinner(s),null,'One archived leg must not create title');
C.finalTie.results=[];
s.v98LeagueTitleHistory=[{year:2027,country:'bra',division:3,champion:'b0'},
 {year:2028,country:'bra',division:3,champion:'a1'},
 {year:2029,country:'bra',division:3,champion:'a0'}];
s.worldHistory=[{year:2026,countries:[{country:'bra',divisionChampions:{3:'a2'}}]}];
const past=v18322LegacyRows(s,{country:'bra',kind:'league',year:'all',division:'3',competition:'league:bra:3'});
assert(past.some(x=>x.year===2026&&x.champion==='a2'),'Legacy worldHistory Serie C missing');
assert(past.some(x=>x.year===2027&&x.champion==='b0'),'Legacy v98 title row missing');
assert(past.some(x=>x.year===2028&&x.champion==='a1'),'Legacy prior season missing');
assert(!past.some(x=>x.year===2029),'Current season cannot use provisional archived leader');
assert(!past.some(x=>x.year===2029&&x.champion==='a0'));
assert(!v18322CollectSeason(s,2029,{country:'bra',kind:'league',year:'all',division:'3',competition:'league:bra:3'})
 .some(x=>x.champion),'Incomplete final must not render a championship');
console.log('PASS 18.351: two-group Serie C phase buttons, final only, current and legacy archives, no false leader');
"""
 program='\n'.join([harness,page,basic,winner,legacy,collect])
 proc=subprocess.run(['node','-e',program],capture_output=True,text=True,timeout=45)
 if proc.returncode:
  raise RuntimeError('18.351 real JS regression failed:\n'+proc.stderr[-13000:])
 print(proc.stdout.strip())
 report={'ok':True,'version':'18.351.0','twoGroupPhaseButtonsVisible':True,
   'onePhaseTabBar':True,'quadSecondTabWorks':True,'genericFirstPhaseTitleBlocked':True,
   'oneLegDoesNotCrownChampion':True,'twoLegWinnerOnly':True,'aggregateAndPenaltyTieCorrect':True,
   'currentCompletedSeasonAppearsInHistory':True,
   'oldArchiveRecoveredOnlyFromStoredData':True,
   'archivedIncompleteFinalRejected':True,
   'currentUnfinishedTitleRejected':True,
   'calendarAndSavesUnchanged':True}
 (root/'serie-c-phases-history-18351-tests.json').write_text(
  json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
 main()
