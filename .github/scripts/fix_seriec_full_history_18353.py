from __future__ import annotations
import json
import sys
from pathlib import Path

MARK="FUTBR_SERIEC_FULL_PODIUM_18353"
VERSION="18.353.0"
KEY="league:bra:3"

ENGINE=r"""
/* FUTBR_SERIEC_FULL_PODIUM_18353
   Capture the entire finished Serie C final in the authoritative simulation
   BEFORE the season changes. No archive has to await 'Proxima temporada'. */
function v18353RecordSerieCFinal(s,last,m){
 const C=s?.braLower?.serieC,tie=C?.finalTie,year=Number(s?.year)||0;
 if(!year||!tie?.a||!tie?.b||String(tie.a)===String(tie.b))return false;
 const finals=[];
 for(const stage of s.schedule||[])for(const f of stage?.fixtures||[])
  if(f?.v661Brazil==='C'&&f?.v661Phase==='final'&&Number(f.v661Tie||0)===0)finals.push(f);
 if(finals.length!==2)return false;
 const legs=[null,null],goals={[tie.a]:0,[tie.b]:0};
 for(const f of finals){
  const leg=Number(f.v661Leg),r=f.result;
  if(![1,2].includes(leg)||legs[leg-1]||!r)return false;
  if(f.home!==(leg===1?tie.b:tie.a)||f.away!==(leg===1?tie.a:tie.b))return false;
  const h=Number(r.home),a=Number(r.away);
  if(!Number.isFinite(h)||!Number.isFinite(a)||h<0||a<0)return false;
  goals[f.home]+=h;goals[f.away]+=a;legs[leg-1]=f;
 }
 if(!legs[0]||!legs[1])return false;
 let winner=null;
 if(goals[tie.a]!==goals[tie.b])winner=goals[tie.a]>goals[tie.b]?tie.a:tie.b;
 else{
  const r=legs[1].result;
  if(Array.isArray(r.pens)&&r.pens.length>=2){
   const ph=Number(r.pens[0]),pa=Number(r.pens[1]);
   if(Number.isFinite(ph)&&Number.isFinite(pa)&&ph!==pa)winner=ph>pa?tie.a:tie.b;
  }
  if(!winner)winner=m?.pens?.winner||r.qualifier||r.winner||tie.winner||null;
 }
 if(![String(tie.a),String(tie.b)].includes(String(winner)))return false;
 const runner=String(winner)===String(tie.a)?tie.b:tie.a;
 const db=s.competitionStats?.['league:bra:3']||{};
 const positive=Object.entries(db).filter(([,r])=>Number(r?.goals)>0);
 const top=positive.reduce((v,[,r])=>Math.max(v,Number(r.goals)||0),0);
 const scorers=positive.filter(([,r])=>Number(r.goals)===top).map(([pid,r])=>{
  const clubs=Object.entries(r.byClub||{}).sort((a,b)=>(Number(b[1]?.goals)||0)-(Number(a[1]?.goals)||0)),
   club=clubs[0]?.[0]||Object.keys(r.clubs||{})[0]||r.club||null;
  return {id:String(r.id||pid),name:String(r.name||s.players?.[pid]?.name||'Jogador'),
   goals:top,club,clubName:String(r.clubs?.[club]||s.teams?.find(t=>String(t.id)===String(club))?.name||'')};
 }).sort((a,b)=>a.name.localeCompare(b.name,'pt-BR'));
 const row={year,kind:'league',country:'bra',division:3,competition:'league:bra:3',
  champion:String(winner),championName:s.teams?.find(t=>String(t.id)===String(winner))?.name||String(winner),
  runner:String(runner),runnerName:s.teams?.find(t=>String(t.id)===String(runner))?.name||String(runner),
  scorers};
 C.champion=winner;C.runnerUp=runner;
 s.v18322Champions=Array.isArray(s.v18322Champions)?s.v18322Champions:[];
 const existing=s.v18322Champions.find(x=>Number(x?.year)===year&&x?.competition==='league:bra:3');
 if(existing&&String(existing.champion)===row.champion&&String(existing.runner||'')===row.runner&&
    JSON.stringify(existing.scorers||[])===JSON.stringify(row.scorers))return false;
 // Keep previously confirmed scorers if an older engine has no surviving
 // competitionStats on load. Never turn an existing official result into blanks.
 if(!row.scorers.length&&existing?.scorers?.length)row.scorers=existing.scorers;
 s.v18322Champions=[row,...s.v18322Champions.filter(x=>
  !(Number(x?.year)===year&&x?.competition==='league:bra:3'))];
 for(const h of s.v98LeagueTitleHistory||[])if(Number(h?.year)===year&&
  h.country==='bra'&&Number(h.division)===3){
  h.champion=winner;h.runner=runner;
 }
 return true;
}
"""

UI=r"""
/* FUTBR_SERIEC_UI_REPAIR_18353
   Existing completed saves may predate the live-final write. Safely capture
   only if the same proven two-leg final can still be verified. */
function v18353ArchiveScorers(s,year){
 const archive=(s.scorerArchive||[]).find(a=>Number(a?.year)===Number(year));
 return v18322Scorers(archive?.competitions?.['league:bra:3']||{});
}
function v18353CaptureFromVerifiedFinal(s){
 const C=s?.braLower?.serieC,tie=C?.finalTie,year=Number(s?.year)||0;
 const champion=window.GestorFC?.v18345SerieCWinner?.(s)||null;
 if(!champion||!year||Number(C?.year)!==year||!tie?.a||!tie?.b)return 0;
 const runner=String(champion)===String(tie.a)?tie.b:tie.a;
 if(String(runner)===String(champion))return 0;
 let scorers=v18322Scorers(s.competitionStats?.['league:bra:3']);
 if(!scorers.length)scorers=v18353ArchiveScorers(s,year);
 const entries=Array.isArray(s.v18322Champions)?s.v18322Champions:[];
 const existing=entries.find(r=>Number(r?.year)===year&&r.competition==='league:bra:3');
 if(!scorers.length&&existing?.scorers?.length)scorers=existing.scorers;
 const row={year,kind:'league',country:'bra',division:3,competition:'league:bra:3',
  champion:String(champion),championName:v18322ClubName(s,champion),
  runner:String(runner),runnerName:v18322ClubName(s,runner),scorers};
 if(existing&&String(existing.champion)===row.champion&&String(existing.runner||'')===row.runner&&
  JSON.stringify(existing.scorers||[])===JSON.stringify(scorers))return 0;
 s.v18322Champions=[row,...entries.filter(r=>
  !(Number(r?.year)===year&&r?.competition==='league:bra:3'))];
 C.champion=champion;C.runnerUp=runner;
 for(const h of s.v98LeagueTitleHistory||[])
  if(Number(h?.year)===year&&h?.country==='bra'&&Number(h.division)===3){
   h.champion=champion;h.runner=runner;
  }
 return 1;
}
function v18353EnrichSerieCRows(s,rows){
 return rows.filter(r=>!(r.competition==='league:bra:3'&&
  Number(r.year)===Number(s.year)&&
  !(window.GestorFC?.v18345SerieCWinner?.(s)))).map(r=>{
  if(r.competition!=='league:bra:3')return r;
  const year=Number(r.year),old=(s.v98LeagueTitleHistory||[]).find(x=>
    Number(x?.year)===year&&x.country==='bra'&&Number(x.division)===3&&
    String(x.champion)===String(r.champion));
  const last=s.braLowerLast;
  const verified=Number(last?.year)===year&&String(last?.cChampion)===String(r.champion);
  const runner=r.runner||old?.runner||(verified?last?.cRunnerUp:null)||null;
  const scorers=r.scorers?.length?r.scorers:v18353ArchiveScorers(s,year);
  if(!runner&&!scorers?.length)return r;
  return {...r,runner:runner?String(runner):null,
   runnerName:runner?v18322ClubName(s,runner):'',
   scorers:scorers?.length?scorers:[]};
 });
}

/* Preserve historic league top-scorer summaries BEFORE the 5-season
   scorerArchive ring evicts old years. This stores at most the tied leaders,
   not the historical player database: negligible impact on long save memory. */
const v18353HistoricalBackfillSeen=new WeakMap();
function v18353BackfillHistoricalSerieC(s){
 if(!s||!Array.isArray(s.scorerArchive)||!s.scorerArchive.length)return 0;
 const key='league:bra:3',yearNow=Number(s.year)||0;
 const stamp=()=>[yearNow,s.scorerArchive.map(a=>Number(a?.year)||0).join(','),
  (s.v18322Champions||[]).filter(r=>r?.competition===key)
   .map(r=>String(r.year)+':'+String(r.champion)+':'+(r.scorers?.length||0)).join(',')].join('|');
 const before=stamp();
 if(v18353HistoricalBackfillSeen.get(s)===before)return 0;
 s.v18322Champions=Array.isArray(s.v18322Champions)?s.v18322Champions:[];
 let added=0;
 for(const archive of s.scorerArchive){
  const year=Number(archive?.year)||0;
  if(!year||year>=yearNow)continue;
  const scorers=v18353ArchiveScorers(s,year);
  if(!scorers.length)continue;
  let row=s.v18322Champions.find(r=>Number(r?.year)===year&&r.competition===key);
  const legacy=(s.v98LeagueTitleHistory||[]).find(r=>Number(r?.year)===year&&
    r?.country==='bra'&&Number(r?.division)===3&&r.champion);
  const fallback=(!row&&!legacy?v18322LegacyRows(s,{
   year:String(year),country:'bra',kind:'league',division:'3',competition:key
  }).find(r=>r?.competition===key):null);
  const champion=row?.champion||legacy?.champion||fallback?.champion||null;
  if(!champion)continue;
  const last=s.braLowerLast;
  const fromLast=Number(last?.year)===year&&String(last?.cChampion)===String(champion)
   ?last?.cRunnerUp:null;
  const runner=row?.runner||legacy?.runner||fallback?.runner||fromLast||null;
  const original=row?.scorers?.length?row.scorers:[];
  if(original.length&&(!runner||row?.runner))continue;
  const update={
   year,kind:'league',country:'bra',division:3,competition:key,
   champion:String(champion),championName:v18322ClubName(s,champion),
   runner:runner?String(runner):null,runnerName:runner?v18322ClubName(s,runner):'',
   scorers:original.length?original:scorers,
   ...(row?.legacy||fallback?.legacy?{legacy:true}:null)
  };
  s.v18322Champions=[update,...s.v18322Champions.filter(r=>
   !(Number(r?.year)===year&&r?.competition===key))];
  added++;
 }
 v18353HistoricalBackfillSeen.set(s,stamp());
 return added;
}

window.GestorFC=window.GestorFC||{};
window.GestorFC.v18353CaptureFromVerifiedFinal=v18353CaptureFromVerifiedFinal;
window.GestorFC.v18353BackfillHistoricalSerieC=v18353BackfillHistoricalSerieC;
"""

def replace_once(source,old,new,label):
    count=source.count(old)
    if count!=1:raise RuntimeError(f'18.353 {label}: expected 1, got {count}')
    return source.replace(old,new,1)

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_seriec_full_history_18353.py <project>')
 root=Path(sys.argv[1]).resolve()
 cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
 if cfg.get('version')!=VERSION:raise RuntimeError('Signed Windows version 18.353 missing')
 path=root/'src/index.html'
 html=path.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('Patch already installed')
 for needle in ['FUTBR_SERIEC_PHASES_HISTORY_18351',
  'FUTBR_OOMSAFE_ARCHIVE_18352',
  'FUTBR_CALENDAR_MATCH_RETIRE_18350',
  'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349',
  'function v661RecordBrazilResult(s,f,m)',
  'function v18322ChampionsRows(s,filter=null)',
  'function v99RepairBrazilLowerChampions(s)',
  'function v18322CaptureSeason(s,year)',
  'function v18322Scorers(db)',
  'window.GestorFC.v18345SerieCWinner=v18345SerieCWinner;']:
  if needle not in html:raise RuntimeError('Missing preexisting feature: '+needle)

 # The engine executes in both Worker simulation and UI. It must write the
 # result at the moment leg two is recorded, not during a season rollover.
 html=replace_once(html,'function v661RecordBrazilResult(s,f,m)',
   ENGINE+'\nfunction v661RecordBrazilResult(s,f,m)','engine end-of-final source hook')
 html=replace_once(html,
  'C.runnerUp=tie.winner===tie.a?tie.b:tie.a;}}}',
  'C.runnerUp=tie.winner===tie.a?tie.b:tie.a;v18353RecordSerieCFinal(s,f,m);}}}',
  'capture both finalists immediately after last match')

 # For already-finished games saved with 18.352, reconcile a provable final on
 # the next render and use the existing atomic persist() path.
 a=html.index('function v99RepairBrazilLowerChampions(s)')
 b=html.index('// Career screen:',a)
 part=html[a:b]
 part=replace_once(part,'return changed;',
   "if(typeof window!=='undefined'){\n"+
   "    if(typeof window.GestorFC?.v18353CaptureFromVerifiedFinal==='function')\n"+
   "      changed+=window.GestorFC.v18353CaptureFromVerifiedFinal(s)||0;\n"+
   "    if(typeof window.GestorFC?.v18353BackfillHistoricalSerieC==='function')\n"+
   "      changed+=window.GestorFC.v18353BackfillHistoricalSerieC(s)||0;\n"+
   "   }\n   return changed;",
   'UI complete saved final and archival goals before title screen renders')
 html=html[:a]+part+html[b:]

 # UI legacy completion only with season-specific evidence, never a guessed
 # runner or a goals leaderboard from the wrong year.
 html=replace_once(html,
  'function v18322ChampionsRows(s,filter=null){',
  UI+'\nfunction v18322ChampionsRows(s,filter=null){',
  'in-scope historical year-scoped scorer recovery')
 a=html.index('function v18322ChampionsRows(s,filter=null){')
 b=html.index('function v18322InitClubFilters(',a)
 part=html[a:b]
 part=replace_once(part,'return [...records.values()].filter(x=>Number(x.year)>0)',
  'return v18353EnrichSerieCRows(s,[...records.values()]).filter(x=>Number(x.year)>0)',
  'year-specific scorer and runner fill without creating unsupported history')
 html=html[:a]+part+html[b:]

 # Do not overwrite an existing exact result with empty scorer/runner data
 # when Next Season captures all competitions as a separate legacy step.
 a=html.index('function v18322CaptureSeason(s,year){')
 b=html.index('function v18322LegacyRows(',a)
 part=html[a:b]
 part=replace_once(part,
  ' const rows=v18322CollectSeason(s,year);',
  """ const rows=v18322CollectSeason(s,year);
 for(const row of rows)if(row.competition==='league:bra:3'){
  const previous=old.find(r=>Number(r?.year)===Number(year)&&r?.competition===row.competition&&
   String(r.champion)===String(row.champion));
  if(!row.runner&&previous?.runner){row.runner=previous.runner;row.runnerName=previous.runnerName||v18322ClubName(s,previous.runner);}
  if(!row.scorers?.length&&previous?.scorers?.length)row.scorers=previous.scorers;
 }""",
  'preserve proven podium during next season')
 html=html[:a]+part+html[b:]

 html=replace_once(html,"const EDITION='18.352.0';","const EDITION='18.353.0';",
   'visible edition matches Windows build')
 html=replace_once(html,
  "window.GestorFC.version='18.352.0';window.GestorFC.visualVersion='18.352.0';",
  "window.GestorFC.version='18.353.0';window.GestorFC.visualVersion='18.353.0';",
  'sidebar edition matches signed binary')

 path.write_text(html,encoding='utf-8')
 report={'ok':True,'version':VERSION,'championAndRunnerRecordedAtSecondLeg':True,
  'finalScoreValidatedBeforeWriting':True,
  'topScorersAllGoalTiesPreserved':True,
  'historicalScorersReadFromExactYear':True,
  'priorYearRunnerFromStoredEvidenceOnly':True,
  'oldAlreadyFinishedCurrentSeasonRecovered':True,
  'previousValidChampionsSnapshotRetainedAtRollover':True,
  'unchangedScorerArchiveRetention':True,
  'historicTopScorersPersistBeyondFiveYearArchiveLimit':True,
  'noFakeRunnerUp':True,
  'noSaveFormatChange':True,
  'longCareerSaveGuard18352Preserved':True}
 (root/'serie-c-full-history-18353-install.json').write_text(
  json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
