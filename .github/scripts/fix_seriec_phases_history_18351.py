from __future__ import annotations
import json
import sys
from pathlib import Path

MARK = "FUTBR_SERIEC_PHASES_HISTORY_18351"
VERSION = "18.351.0"

WINNER = r"""
/* FUTBR_SERIEC_PHASES_HISTORY_18351 - only a completed, provable two-leg final can award Serie C */
function v18345SerieCWinner(s){
 const C=s?.braLower?.serieC,tie=C?.finalTie;
 if(!tie?.a||!tie?.b||String(tie.a)===String(tie.b))return null;
 const valid=id=>String(id)===String(tie.a)||String(id)===String(tie.b);
 const pick=(h,a,home,away)=>{
  const hg=Number(h),ag=Number(a);
  if(!Number.isFinite(hg)||!Number.isFinite(ag)||hg<0||ag<0)return null;
  return {home,away,hg,ag};
 };
 const all=(s.schedule||[]).flatMap(st=>(st?.fixtures||[]).filter(f=>
  f?.v661Brazil==='C'&&f?.v661Phase==='final'&&Number(f.v661Tie||0)===0));
 const legs=[null,null];
 if(all.length){
  if(all.length!==2)return null;
  for(const f of all){
   const leg=Number(f.v661Leg);
   if(![1,2].includes(leg)||legs[leg-1]||!f.result||!valid(f.home)||!valid(f.away)||String(f.home)===String(f.away))return null;
   const entry=pick(f.result.home,f.result.away,f.home,f.away);
   if(!entry)return null;
   legs[leg-1]={...entry,result:f.result};
  }
  if(!legs[0]||!legs[1])return null;
 }else if(Array.isArray(tie.results)&&tie.results.length===2){
  // Older saves can retain tie.results while dropping matchday fixtures.
  // The two legs are played at B's home, then at A's home.
  const first=pick(tie.results[0].home,tie.results[0].away,tie.b,tie.a);
  const second=pick(tie.results[1].home,tie.results[1].away,tie.a,tie.b);
  if(!first||!second)return null;
  legs[0]={...first,result:tie.results[0]};
  legs[1]={...second,result:tie.results[1]};
 }else return null;
 if(legs[0].home!==tie.b||legs[0].away!==tie.a||
    legs[1].home!==tie.a||legs[1].away!==tie.b)return null;
 const goals={[tie.a]:0,[tie.b]:0};
 for(const leg of legs){goals[leg.home]+=leg.hg;goals[leg.away]+=leg.ag;}
 if(goals[tie.a]!==goals[tie.b])return goals[tie.a]>goals[tie.b]?tie.a:tie.b;
 const last=legs[1].result;
 if(Array.isArray(last.pens)&&last.pens.length>=2){
  const ph=Number(last.pens[0]),pa=Number(last.pens[1]);
  if(Number.isFinite(ph)&&Number.isFinite(pa)&&ph!==pa)return ph>pa?tie.a:tie.b;
 }
 for(const id of [last.qualifier,last.winner,tie.winner])if(valid(id))return id;
 return null;
}
"""

LEGACY = r"""
 // Restore historical Série C rows already stored in older career archives.
 // A first-stage leader for the current season must never be used as champion.
 const finishedCurrent=window.GestorFC?.v18345SerieCWinner?.(s)||null;
 const historic=(year,id,source)=>{
  year=v18322N(year);
  if(!year||!id)return;
  if(year===v18322N(s.year)&&String(id)!==String(finishedCurrent||''))return;
  const record={year,kind:'league',country:'bra',division:3,competition:'league:bra:3',
   champion:String(id),championName:v18322ClubName(s,id),runner:null,
   runnerName:'',scorers:[],legacy:true,source};
  if(v18322MatchRow(record,filter))result.push(record);
 };
 for(const row of s.v98LeagueTitleHistory||[])
  if(row?.country==='bra'&&v18322N(row.division)===3)
   historic(row.year,row.champion,'v98LeagueTitleHistory');
 for(const yearRow of s.worldHistory||[])for(const row of yearRow?.countries||[])
  if(row?.country==='bra'&&row.divisionChampions?.['3'])
   historic(yearRow.year,row.divisionChampions['3'],'worldHistory');
"""

def once(src,old,new,label):
    amount=src.count(old)
    if amount!=1:
        raise RuntimeError(f'18.351 {label}: expected 1 source anchor, got {amount}')
    return src.replace(old,new,1)

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_seriec_phases_history_18351.py <project>')
    root=Path(sys.argv[1]).resolve()
    config=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    if config.get('version')!=VERSION:raise RuntimeError('18.351 signed version not installed')
    path=root/'src/index.html'
    html=path.read_text(encoding='utf-8')
    if MARK in html:raise RuntimeError('18.351 already installed')
    for mark in ('FUTBR_SERIEC_FINAL_CHAMPION_18345',
                 'FUTBR_CALENDAR_MATCH_RETIRE_18350',
                 'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349',
                 'function v663SerieCPage(C)',
                 'function v18322LegacyRows(s,filter=null)',
                 'function v18345SerieCWinner(s)',
                 'function v94ChampionInfo()'):
        if mark not in html:raise RuntimeError('Required validated code missing: '+mark)

    # The 2028+ two-group Serie C view constructed the phase tabs but did not
    # pass them into any visible card, unlike the original one-group view.
    first_panel="'Grupo A',{qualify:4,relegate:3,subtitle:'4 avançam · 3 rebaixados'}"
    html=once(html,first_panel,
       "'Grupo A',{qualify:4,relegate:3,subtitle:'4 avançam · 3 rebaixados',actions:tabs}",
       'two-group Serie C phase buttons')

    # The older generic champion UI silently fell back to the leader of E.table
    # whenever a custom Serie C final was unresolved.
    generic="if(v54CompetitionMode==='league'&&state.seasonDone){if(selectedCountry()==='usa'"
    html=once(html,generic,
      "if(v54CompetitionMode==='league'&&state.seasonDone){if(selectedCountry()==='bra'&&Number(selectedDivision())===3)return null;if(selectedCountry()==='usa'",
      'remove generic first-stage champion fallback')

    # Authoritative winner resolver supports both current schedule fixtures
    # and completed older finalTie.results (without inventing an outcome).
    start="function v18345SerieCWinner(s){"
    end="\nwindow.GestorFC=window.GestorFC||{};"
    if html.count(start)!=1:raise RuntimeError('Final resolver not unique')
    a=html.index(start)
    b=html.find(end,a)
    if b<0 or 'legs.some' not in html[a:b]:
        raise RuntimeError('Unexpected original final resolver; refusing partial patch')
    html=html[:a]+WINNER+html[b:]

    # Only completed, previously stored historical data may be reconstructed.
    old="\n return result;\n}\nfunction v18322ChampionsRows(s,filter=null){"
    html=once(html,old,"\n"+LEGACY+"\n return result;\n}\nfunction v18322ChampionsRows(s,filter=null){",
             'historical third division from stored archives')

    # Prevent subsequent running editions from showing the old version label.
    html=once(html,"const EDITION='18.350.0';","const EDITION='18.351.0';",
              'current Windows edition')
    html=once(html,
      "window.GestorFC.version='18.350.0';window.GestorFC.visualVersion='18.350.0';",
      "window.GestorFC.version='18.351.0';window.GestorFC.visualVersion='18.351.0';",
      'boot Windows edition')

    for mark in ('v18345CFirstPhaseFinished(C)','v18345CQuadPhaseFinished(C)',
       'v18345SerieCWinner(s)','v18345SyncCArchives(s,w,runner)',
       'v18322CollectSeason(s,Number(s.year),filter)',
       'v18322CaptureSeason(s,year)',
       'v18324-open-retirements',
       'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349'):
        if mark not in html:raise RuntimeError('Missing protected invariant: '+mark)
    path.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,'serieCPhaseTabsForTwoGroups':True,
       'serieCNoLeaderTitleFallback':True,'championRequiresTwoCompletedLegs':True,
       'historicTieResultsAcceptedOnlyAfterTwoLegs':True,
       'historicRecordsRecoveredFromExistingSavedData':True,
       'currentYearProvisionalRecordsRejected':True,
       'coachAndTitleRepairMaintained':True,'retirementManagerPreserved':True,
       'calendarAndIncrementalSavesPreserved':True,'noSaveMigration':True}
    (root/'serie-c-phases-history-18351-install.json').write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
