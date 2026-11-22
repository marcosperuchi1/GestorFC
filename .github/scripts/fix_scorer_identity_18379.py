"""FutBR 18.379: render historical scorer clubs with real crest/link and never duplicate flags in player-name cells.

The correction changes the rankings view only; it never edits saved player, club,
competition, or historical scorer objects.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

MARK = "FUTBR_SCORER_IDENTITY_18379"
JS = r"""
/* FUTBR_SCORER_IDENTITY_18379
   Identity resolution is read-only, bounded by one player and the existing team
   catalogue. No writes to stats, club arrays or any saved career objects. */
function v18379CleanScorerName(name){
 const raw=String(name??'');
 const clean=raw.replace(/(?:\s*[\u{1F1E6}-\u{1F1FF}]{2})+\s*$/gu,'').trim();
 return clean||raw;
}
function v18379ClubNameKey(name){
 return String(name??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'')
  .toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').replace(/\s+/g,' ').trim();
}
function v18379ClubSimpleKey(name){
 return v18379ClubNameKey(name).replace(/\b(?:fc|fk|cf|sc|nk|ks|afc|sd|futbol|futebol|football|club|clube)\b/g,'')
   .replace(/\s+/g,' ').trim();
}
const v18379ClubIndexes=new WeakMap();
function v18379ClubIndex(s){
 if(!s||typeof s!=='object')return null;
 const teams=Array.isArray(s.teams)?s.teams:[];
 const cached=v18379ClubIndexes.get(s);
 if(cached&&cached.teams===teams&&cached.length===teams.length)return cached;
 const index={teams,length:teams.length,ids:new Map(),names:new Map(),shortNames:new Map(),loose:new Map()};
 function put(map,key,team){
  if(!key)return;
  if(!map.has(key))map.set(key,team);
  else if(map.get(key)?.id!==team.id)map.set(key,null);
 }
 for(const team of teams){
  if(!team||!team.id)continue;
  index.ids.set(String(team.id),team);
  const names=[team.name,...(Array.isArray(team.aliases)?team.aliases:[])];
  for(const name of names){
   put(index.names,v18379ClubNameKey(name),team);
   put(index.shortNames,v18379ClubSimpleKey(name),team);
  }
 }
 v18379ClubIndexes.set(s,index);
 return index;
}
function v18379FindClub(index,id,name){
 if(!index)return null;
 const direct=index.ids.get(String(id??''));if(direct)return direct;
 const key=v18379ClubNameKey(name);
 if(!key)return null;
 const exact=index.names.get(key);if(exact)return exact;
 const simple=v18379ClubSimpleKey(name);
 if(!simple)return null;
 const normal=index.shortNames.get(simple);if(normal)return normal;
 if(simple.length<5)return null;
 if(index.loose.has(simple))return index.loose.get(simple);
 let match=null,ambiguous=false;
 for(const [candidate,team] of index.shortNames){
  if(!team||candidate.length<5)continue;
  if(candidate.startsWith(simple+' ')||candidate.endsWith(' '+simple)||
     simple.startsWith(candidate+' ')||simple.endsWith(' '+candidate)){
   if(match&&match.id!==team.id){ambiguous=true;break;}
   match=team;
  }
 }
 index.loose.set(simple,ambiguous?null:match);
 return ambiguous?null:match;
}
function v18379HistoricalPlayerClubs(s,row,year,index,add){
 const y=Number(year);
 const packed=s?.v555CareerArchive?.[y];
 const encoded=packed?.p?.[row.id];
 if(typeof encoded==='string'&&encoded){
  for(const segment of encoded.split(';')){
   const id=segment.split('|',1)[0];
   if(id)add(id,packed?.n?.[id]||'',index);
  }
 }
 const old=s?.v538CareerArchive?.[y]?.[row.id];
 if(Array.isArray(old))for(const data of old){
  if(data)add(data.teamId||data.clubId||'',data.teamName||data.clubName||'',index);
 }
}
const v18379PreviousClubHTML=v18220ClubHTML;
v18220ClubHTML=function(s,row,kind){
 if(!s||!row)return v18379PreviousClubHTML(s,row,kind);
 if(kind==='national'||String(kind||'').startsWith('nat|'))return v18379PreviousClubHTML(s,row,kind);
 const index=v18379ClubIndex(s),filter=v18220Filter(),year=filter.year,chosen=[];
 const seen=new Set();
 function add(id,name){
  const team=v18379FindClub(index,id,name);
  if(team&&!seen.has(String(team.id))){seen.add(String(team.id));chosen.push(team);}
 }
 // A prior season must not be mislabeled with a player's CURRENT club.
 const prior=year!=='all'&&Number(year)>=2026&&Number(year)<Number(s.year);
 if(prior&&typeof v18377YearStats==='function'){
  const hist=v18377YearStats(s,Number(year))?.players?.[row.id];
  for(const [id,name] of Object.entries(hist?.clubs||{}))add(id,name);
 }
 if(prior&&chosen.length===0){
  for(const [id,name] of Object.entries(row.clubs||{}))add(id,name);
 }
 if(year==='all'||(!prior&&Number(year)===Number(s.year))){
  const current=s.players?.[row.id],currentTeam=current?.clubId;
  if(currentTeam)add(currentTeam,'');
  if(chosen.length===0){
   const old=Object.entries(row.clubs||{});
   // Global ranking shows the most recent known club, as before, but as a link.
   for(let i=old.length-1;i>=0;i--){
    add(old[i][0],old[i][1]);
    if(chosen.length)break;
   }
  }
  if(chosen.length===0){
   // Read just this player's compact annual records; never enumerate entire
   // career archives or reconstruct the world. Newest historical club wins.
   const maxYear=Math.min(2100,Number(s.year)||2026);
   for(let y=maxYear;y>=2026&&chosen.length===0;y--)v18379HistoricalPlayerClubs(s,row,y,index,add);
  }
 }
 if(chosen.length===0){
  const previous=v18379PreviousClubHTML(s,row,kind);
  if(/<button\b|club-crest/.test(previous))return previous;
  // A genuinely unresolvable historical identity must not navigate to a
  // different club. Show an explicit placeholder instead of a fictitious badge.
  return '<span class="v18379-unknown-club" title="Clube histórico sem identificação segura no cadastro"><span class="shield small" aria-hidden="true">?</span> '+previous+'</span>';
 }
 const display=prior?chosen:chosen.slice(0,1);
 return '<div class="v538-scorer-club v18379-club-links">'+display.map(team=>{
  let image='';
  try{image=typeof badge==='function'?badge(team,'small'):'';}catch(_e){}
  let link='';
  try{link=typeof teamButton==='function'?teamButton(team):'';}catch(_e){}
  if(!link)link='<button type="button" class="table-button player-name" data-action="team" data-team="'+v18220Esc(team.id)+'">'+v18220Esc(team.name)+'</button>';
  return '<span class="v18379-club-entry">'+image+link+'</span>';
 }).join('<span class="muted"> / </span>')+'</div>';
};
window.GestorFC=window.GestorFC||{};
window.GestorFC.scorerIdentity18379={
 version:'18.379.0',displayName:v18379CleanScorerName,
 resolveClub:(s,id,name)=>v18379FindClub(v18379ClubIndex(s),id,name)?.id||null
};
"""

def main():
 if len(sys.argv)!=2:
  raise SystemExit("usage: fix_scorer_identity_18379.py <prepared-game-root>")
 root=Path(sys.argv[1]).resolve()
 target=root/'src/index.html'
 html=target.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('18.379 scorer identity already present')
 for required in ('FUTBR_SCORER_HISTORY_RECOVERY_18377',
                  'FUTBR_MONEY_AUTOUPDATE_18378',
                  'FUTBR_SCORERS_IN_SCOPE_18220_START'):
  if required not in html:raise RuntimeError('Required previous version missing: '+required)
 start=html.index('/* FUTBR_SCORERS_IN_SCOPE_18220_START */')
 end=html.index('/* FUTBR_SCORERS_IN_SCOPE_18220_END */',start)
 helper=html[start:end]
 needle='v18220Esc(row.name)'
 if helper.count(needle)!=2:raise RuntimeError('Expected two scorer name display cells, got '+str(helper.count(needle)))
 helper=helper.replace(needle,'v18220Esc(v18379CleanScorerName(row.name))')
 html=html[:start]+helper+html[end:]
 anchor="window.GestorFC.render=render;\nwindow.GestorFC.fontSettings18376="
 if html.count(anchor)!=1:raise RuntimeError('Scorers and native settings closure changed')
 html=html.replace(anchor,JS+'\n'+anchor,1)
 if html.count(MARK)!=1:raise RuntimeError('18.379 marker missing or repeated')
 for section in (JS,):
  check=subprocess.run(['node','--check','-'],input=section,text=True,capture_output=True)
  if check.returncode:raise RuntimeError('18.379 JavaScript syntax: '+check.stderr[-3000:])
 target.write_text(html,encoding='utf-8')
 report={
  'ok':True,'version':'18.379.0','viewOnlyChanges':True,
  'historicClubIdsPreferred':True,'uniqueTeamNameFallback':True,
  'archivedPlayerYearLookupOnly':True,'readOnlySavedStats':True,
  'existingGameCrestAndTeamActionsUsed':True,'nationalityColumnPreserved':True,
  'nameFlagsDeduplicatedForDisplay':True,'unresolvedClubsNotMislabeled':True,
  'sourceSha256':hashlib.sha256(html.encode()).hexdigest()
 }
 (root/'scorer-identity-18379-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
