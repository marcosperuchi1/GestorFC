from __future__ import annotations

import json
import sys
from pathlib import Path

VERSION = "18.344"
MARKER = "FUTBR_CAREER_ISOLATION_18344"

RESTORE = r"""
function v18344RestoreStarterCoach(s,club,me){
 // A career starting at a national team must never displace a club's seed coach.
 // The normal world constructor temporarily gives the selected club to c0.
 const original=Object.values(s.coaches||{}).find(c=>
  c&&c.id!==me.id&&String(c.name||'')===String(club.initialCoachName||'')&&
  (c.jobs||[]).some(j=>String(j?.club||'')===String(club.id)));
 if(!original)throw Error('Nao foi possivel recuperar o tecnico inicial do clube '+club.name+'.');
 for(const j of original.jobs||[]){
  if(String(j?.club||'')!==String(club.id))continue;
  if(Number(j.year??j.startYear)!==Number(s.year)||Number(j.day??j.startDay)!==0)continue;
  if(String(j.end||'').includes('Substitu')){delete j.end;delete j.endYear;delete j.endDay;}
 }
 original.clubId=club.id;
 original.unemployedSince=null;
 original.jobStart=0;
 original.jobYear=s.year;
 club.coachId=original.id;
 if(club.tactics){
  if(original.formation)club.tactics.formation=original.formation;
  if(original.style)club.tactics.style=original.style;
 }
 if(s.coachMoves)s.coachMoves=s.coachMoves.filter(m=>m.coachId!==me.id);
 return original;
}
"""

def replace_exact(data: str, old: str, new: str, what: str) -> str:
    n=data.count(old)
    if n!=1: raise RuntimeError(f"18.344 expected one {what}; found {n}")
    return data.replace(old,new,1)

def main():
    if len(sys.argv)!=2: raise SystemExit("usage: fix_career_isolation_18344.py <project>")
    project=Path(sys.argv[1]).resolve()
    path=project/"src/index.html"
    html=path.read_text(encoding="utf-8")
    if MARKER in html: raise RuntimeError("18.344 applied twice")
    restore_anchor="function v643ConvertNewCareerToNational(s,code){"
    html=replace_exact(html,restore_anchor,RESTORE+"\n"+restore_anchor,"national conversion")
    html=replace_exact(
      html,
      "if(old.coachId===me.id)old.coachId=null;me.clubId=null;me.jobs=[];me.nationalTeamCode=code;",
      "if(old.coachId===me.id)v18344RestoreStarterCoach(s,old,me);me.clubId=null;me.jobs=[];me.nationalTeamCode=code;",
      "initial coach displacement"
    )
    html=replace_exact(
      html,
      "s.v636CoachCareer=[];s.v636CareerTracker=null;s.v636TrackingInitialized=true;",
      "s.v636CoachCareer=[];s.v217CareerLedger={version:1,jobs:[],rows:[],updatedYear:s.year,updatedDay:s.day};s.v636CareerTracker=null;s.v636TrackingInitialized=true;",
      "national start ledger clearing"
    )
    # This ledger is an in-memory recovery cache, NOT shared across save identities.
    html=replace_exact(
      html,
      "const shadow={jobs:[],rows:[]};\n let restoring=false,saveQueued=false;",
      """const shadow={jobs:[],rows:[]};
 let restoring=false,saveQueued=false;
 // FUTBR_CAREER_ISOLATION_18344: each save owns its own recovery cache.
 let shadowCareerId=null;
 function guardCareer(s){
  const id=String(s?.created||s?.v18344CareerId||'');
  if(!id)return;
  if(shadowCareerId!==id){
   shadow.jobs=[];shadow.rows=[];shadowCareerId=id;
   saveQueued=false;
  }
 }""",
      "isolated career shadow"
    )
    html=replace_exact(
      html,
      "function remember(s){",
      "function remember(s){guardCareer(s);",
      "career shadow remember guard"
    )
    html=replace_exact(
      html,
      "function repair(s=state){",
      "function repair(s=state){guardCareer(s);",
      "career shadow repair guard"
    )
    html=replace_exact(
      html,
      "const baseCreate=E.createCareer;E.createCareer=function(options={}){const s=baseCreate(options);try{remember(s);repair(s);}catch(e){}return s;};",
      """const baseCreate=E.createCareer;E.createCareer=function(options={}){
   // New universe means new cache. National careers first pass through a club
   // constructor: do not persist the temporary club spell as career history.
   shadow.jobs=[];shadow.rows=[];shadowCareerId=null;saveQueued=false;
   const s=baseCreate(options);
   guardCareer(s);
   if(options?.v643StartType!=='national')try{remember(s);repair(s);}catch(e){}
   return s;
  };""",
      "new career shadow reset"
    )
    path.write_text(html,encoding="utf-8")
    report={"ok":True,"version":VERSION,"clubStarterCoachRestored":True,
      "nationalStartsWithNoClubSpell":True,"newCareerShadowReset":True,
      "savedCareersKeepTheirOwnHistory":True,"fullHistoricalArchivePreserved":True}
    (project/"career-isolation-18344-install.json").write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":main()
