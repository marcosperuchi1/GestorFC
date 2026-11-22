"""Restore old global scorer standings using the save's existing compact career history."""
from pathlib import Path
import sys,json,hashlib,subprocess
MARK='FUTBR_SCORER_HISTORY_RECOVERY_18377'
UI=r'''
/* FUTBR_SCORER_HISTORY_RECOVERY_18377
   The five-season scorerArchive ring cannot show 2026 in a 2033 career.
   Read the existing, year-specific v555/v538 player career data on demand.
   Never retain the whole archive across years or modify the saved state. */
const v18377ScorerCache=new WeakMap();
function v18377YearStats(s,year){
 if(!s||!Number.isInteger(year)||year>=Number(s.year)||year<2026)return null;
 const packed=s.v555CareerArchive?.[year],legacy=s.v538CareerArchive?.[year];
 if(!packed?.p&&!legacy)return null;
 let years=v18377ScorerCache.get(s);
 if(!years){years=new Map();v18377ScorerCache.set(s,years);}
 if(years.has(year))return years.get(year);
 const players={},clubNames=packed?.n||{},valid=Object.prototype.hasOwnProperty;
 function add(pid,team,stats,nameOverride=''){
  const g=Number(stats?.goals)||0,a=Number(stats?.assists)||0,j=Number(stats?.apps)||0;
  if(g<=0&&a<=0&&j<=0)return;
  const id=String(pid||''),tid=String(team||'');if(!id||!tid)return;
  let row=players[id];
  if(!row){
   const known=s.players?.[id]||s.allTimeStats?.[id]||{};
   row={id,name:String(known.name||nameOverride||id),
     natCode:String(known.natCode||known.nationality||'UNK'),
     goals:0,assists:0,apps:0,minutes:0,clubs:{}};
   players[id]=row;
  }
  row.goals+=g;row.assists+=a;row.apps+=j;
  row.clubs[tid]=String(clubNames[tid]||stats?.teamName||E.team(s,tid)?.name||tid);
 }
 if(packed?.p){
  const src=packed.p;
  for(const id in src){if(!valid.call(src,id))continue;
   const raw=src[id];if(typeof raw!=='string'||!raw)continue;
   for(const segment of raw.split(';')){
    if(!segment)continue;const fields=segment.split('|');if(fields.length<4)continue;
    add(id,fields[0],{apps:fields[1],goals:fields[2],assists:fields[3]});
   }
  }
 }else{
  for(const id in legacy){if(!valid.call(legacy,id))continue;
   for(const row of legacy[id]||[])add(id,row?.teamId,row,row?.name||'');
  }
 }
 for(const id in players)if(players[id].goals<=0)delete players[id];
 const result={year,players,competitions:{'historic-global-clubs':players}};
 years.set(year,result);while(years.size>2)years.delete(years.keys().next().value);
 return result;
}
const v18377PreviousCollect=v18220Collect;
v18220Collect=function(s,f){
 const year=Number(f?.year||s?.year),kind=String(f?.kind||'all'),current=Number(s?.year);
 const missingArchive=!Array.isArray(s?.scorerArchive)||!s.scorerArchive.some(x=>Number(x?.year)===year);
 if(s&&year<current&&missingArchive&&kind==='all'){
  const restored=v18377YearStats(s,year);
  if(restored){
   if(!restored.viewState){restored.viewState=Object.create(s);restored.viewState.scorerArchive=[{year,competitions:restored.competitions}];}
   return v18377PreviousCollect(restored.viewState,f);
  }
 }
 return v18377PreviousCollect(s,f);
};
const v18377PreviousClubHTML=v18220ClubHTML;
v18220ClubHTML=function(s,row,kind){
 const year=Number(v18220Filter().year);
 if(s&&year>=2026&&year<Number(s.year)){
  const entry=v18377YearStats(s,year)?.players?.[row.id];
  if(entry&&Object.keys(entry.clubs).length){
   const names=[...new Set(Object.values(entry.clubs).filter(Boolean))];
   return '<span class="v18377-historical-clubs">'+names.map(v18220Esc).join(' / ')+'</span>';
  }
  const countries=Object.values(row.nationalTeams||{}).filter(Boolean);
  if(countries.length)return '<span class="v18377-historical-nations">'+countries.map(v18220Esc).join(' / ')+'</span>';
 }
 return v18377PreviousClubHTML(s,row,kind);
};
if(window.GestorFC?.scorersInScope18220)
 window.GestorFC.scorersInScope18220.collectWith=(s,f)=>v18220Collect(s,f);
window.GestorFC.historyScorers18377={version:'18.377.0',fromYear:(s,year)=>{
 const a=v18377YearStats(s,year);return {available:!!a,scorers:a?Object.keys(a.players).length:0,year};
}};
'''
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_legacy_scorers_18377.py <prepared-root>')
 root=Path(sys.argv[1]).resolve();p=root/'src/index.html';html=p.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('Historical scorer recovery already applied')
 for marker in ('FUTBR_SCORERS_IN_SCOPE_18220_START','FUTBR_FONT_SETTINGS_18376','function v555PackedRows('):
  if marker not in html:raise RuntimeError('Required source context absent: '+marker)
 anchor="window.GestorFC.render=render;\nwindow.GestorFC.fontSettings18376="
 if html.count(anchor)!=1:raise RuntimeError('Unexpected 18.376 closing bridge count: '+str(html.count(anchor)))
 html=html.replace(anchor,UI+'\n'+anchor,1)
 js=subprocess.run(['node','--check','-'],input=UI,text=True,capture_output=True)
 if js.returncode:raise RuntimeError(js.stderr)
 p.write_text(html,encoding='utf-8')
 report={'ok':True,'version':'18.377.0','source':'v555CareerArchive/v538CareerArchive',
         'archiveRingNotExpanded':True,'readsOnlyOneYearAtATime':True,
         'recoversOldGlobalLeagueAndCupTotals':True,'reusesExistingCareerHistory':True,
         'avoidsCurrentClubMislabel':True,'doesNotModifySave':True,
         'sha256':hashlib.sha256(html.encode()).hexdigest()}
 (root/'history-scorers-18377-install.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))
if __name__=='__main__':main()
