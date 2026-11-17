from __future__ import annotations
import json
import sys
from pathlib import Path

VERSION="18.345"
MARK="FUTBR_SERIEC_FINAL_CHAMPION_18345"

def once(source, before, after, label):
    n=source.count(before)
    if n!=1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {n}")
    return source.replace(before,after,1)

BRA_GUARDS=r'''
/* FUTBR_SERIEC_FINAL_CHAMPION_18345: do not freeze first phase or award a provisional title. */
function v18345CFirstPhaseFinished(C){
 if(!Array.isArray(C?.firstGroups)||!C.firstGroups.length)return false;
 const rounds=C.format==='two-groups-14'?2:1;
 return C.firstGroups.every((g,i)=>Array.isArray(g)&&g.length>1&&g.every(id=>
  Number(C.firstStandings?.[i]?.[id]?.p||0)>=(g.length-1)*rounds));
}
function v18345CQuadPhaseFinished(C){
 return C?.quadGroups?.length===2&&C.quadGroups.every((g,i)=>
  Array.isArray(g)&&g.length===4&&g.every(id=>Number(C.quadStandings?.[i]?.[id]?.p||0)>=6));
}
'''

FINAL_VERIFIER=r'''
/* FUTBR_SERIEC_VERIFIED_FINAL_18345: only the 2nd completed leg establishes the title. */
function v18345SerieCWinner(s){
 const tie=s?.braLower?.serieC?.finalTie;
 if(!tie?.a||!tie?.b||String(tie.a)===String(tie.b))return null;
 const legs=[null,null];
 for(const stage of s.schedule||[])for(const f of stage?.fixtures||[]){
  if(f?.v661Brazil!=='C'||f?.v661Phase!=='final'||Number(f.v661Tie||0)!==0)continue;
  const leg=Number(f.v661Leg);
  if(leg!==1&&leg!==2)continue;
  if(legs[leg-1])return null;
  legs[leg-1]=f;
 }
 if(legs.some(f=>!f?.result))return null;
 const goals={[tie.a]:0,[tie.b]:0};
 for(const f of legs){
  if(!Object.prototype.hasOwnProperty.call(goals,f.home)||
     !Object.prototype.hasOwnProperty.call(goals,f.away)||f.home===f.away)return null;
  const h=Number(f.result.home),a=Number(f.result.away);
  if(!Number.isFinite(h)||!Number.isFinite(a)||h<0||a<0)return null;
  goals[f.home]+=h;goals[f.away]+=a;
 }
 if(goals[tie.a]!==goals[tie.b])return goals[tie.a]>goals[tie.b]?tie.a:tie.b;
 // Aggregate tie: the second leg must contain a penalty/qualification decision.
 const f=legs[1],r=f.result;
 if(Array.isArray(r.pens)&&r.pens.length>=2){
  const ph=Number(r.pens[0]),pa=Number(r.pens[1]);
  if(Number.isFinite(ph)&&Number.isFinite(pa)&&ph!==pa)
   return ph>pa?f.home:f.away;
 }
 for(const id of [r.qualifier,tie.winner])
  if(String(id)===String(tie.a)||String(id)===String(tie.b))return id;
 return null;
}
window.GestorFC=window.GestorFC||{};
window.GestorFC.v18345SerieCWinner=v18345SerieCWinner;
function v18345CleanCClubTitles(s,winner){
 let changed=0;
 for(const c of Object.values(s.coaches||{})){
  if(!Array.isArray(c?.titles)||!c.titles.length)continue;
  const old=c.titles,keep=[];let delta=0;
  for(const r of old){
   const wrong=Number(r?.year)===Number(s.year)&&r?.key==='league:bra:3'&&
    (!winner||String(r.club)!==String(winner));
   if(wrong){delta+=Number(r.points)||0;changed++;}else keep.push(r);
  }
  if(keep.length!==old.length){
   c.titles=keep;c.bonusPoints=Math.max(0,(Number(c.bonusPoints)||0)-delta);
   if(typeof E.coachRating==='function')c.points=E.coachRating(c);
  }
 }
 return changed;
}
function v18345SyncCArchives(s,winner,runner){
 let changed=0,year=Number(s.year);
 if(Array.isArray(s.v18322Champions)){
  const filtered=[];
  for(const row of s.v18322Champions){
   if(Number(row?.year)===year&&row?.competition==='league:bra:3'){
    if(!winner){changed++;continue;}
    if(String(row.champion)!==String(winner)||String(row.runner||'')!==String(runner||'')){
     row.champion=String(winner);row.championName=E.team(s,winner)?.name||String(winner);
     row.runner=runner?String(runner):null;row.runnerName=runner?(E.team(s,runner)?.name||String(runner)):'';
     changed++;
    }
   }
   filtered.push(row);
  }
  if(filtered.length!==s.v18322Champions.length)s.v18322Champions=filtered;
 }
 if(Array.isArray(s.v98LeagueTitleHistory)){
  const filtered=[];
  for(const row of s.v98LeagueTitleHistory){
   if(Number(row?.year)===year&&row?.country==='bra'&&Number(row?.division)===3){
    if(!winner){changed++;continue;}
    if(String(row.champion)!==String(winner)){row.champion=winner;changed++;}
   }
   filtered.push(row);
  }
  if(filtered.length!==s.v98LeagueTitleHistory.length)s.v98LeagueTitleHistory=filtered;
 }
 const yearRow=(s.worldHistory||[]).find(h=>Number(h?.year)===year)?.countries?.find(c=>c?.country==='bra');
 if(yearRow?.divisionChampions&&Object.prototype.hasOwnProperty.call(yearRow.divisionChampions,'3')){
  if(winner){if(String(yearRow.divisionChampions['3'])!==String(winner)){yearRow.divisionChampions['3']=winner;changed++;}}
  else{delete yearRow.divisionChampions['3'];changed++;}
 }
 if(Number(s.braLowerLast?.year)===year&&String(s.braLowerLast.cChampion||'')!==String(winner||'')){
  s.braLowerLast.cChampion=winner;changed++;
 }
 return changed;
}
'''

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: fix_seriec_champion_18345.py <project>")
    root=Path(sys.argv[1]).resolve()
    file=root/"src/index.html"
    html=file.read_text(encoding="utf-8")
    if MARK in html:raise RuntimeError("18.345 fix was already installed")
    html=once(
       html,
       "function v661EnsureCQuadrangular(s){const C=s.braLower?.serieC;if(!C||C.quadGroups.length)return;",
       BRA_GUARDS+"\nfunction v661EnsureCQuadrangular(s){const C=s.braLower?.serieC;if(!C||C.quadGroups.length||!v18345CFirstPhaseFinished(C))return;",
       "prevent premature Serie C qualification"
    )
    html=once(
       html,
       "if(!C.promoted.length&&C.quadGroups.length===2){const a=v661Order(s,C.quadGroups[0],C.quadStandings[0]),b=v661Order(s,C.quadGroups[1],C.quadStandings[1]);C.promoted=[...a.slice(0,2),...b.slice(0,2)];C.finalTie={a:a[0],b:b[0],score:[0,0],winner:null,results:[]};}",
       "if(v18345CQuadPhaseFinished(C)){const a=v661Order(s,C.quadGroups[0],C.quadStandings[0]),b=v661Order(s,C.quadGroups[1],C.quadStandings[1]);C.promoted=[...a.slice(0,2),...b.slice(0,2)];if(!C.finalTie)C.finalTie={a:a[0],b:b[0],score:[0,0],winner:null,results:[]};}",
       "create Serie C final independently of premature promoted list"
    )
    html=once(
       html,
       "v661EnsureCQuadrangular(s);if(!C.promoted.length&&C.quadGroups.length===2){const a=v661Order(s,C.quadGroups[0],C.quadStandings[0]),b=v661Order(s,C.quadGroups[1],C.quadStandings[1]);C.promoted=[...a.slice(0,2),...b.slice(0,2)];if(!C.champion&&!C.finalTie)C.champion=a[0];}if(!C.relegated.length){",
       "v661EnsureCQuadrangular(s);if(!C.promoted.length&&v18345CQuadPhaseFinished(C)){const a=v661Order(s,C.quadGroups[0],C.quadStandings[0]),b=v661Order(s,C.quadGroups[1],C.quadStandings[1]);C.promoted=[...a.slice(0,2),...b.slice(0,2)];}if(!C.relegated.length&&v18345CFirstPhaseFinished(C)){",
       "remove provisional Serie C champion and standings rollover"
    )
    html=once(
       html,
       "function v99RepairBrazilLowerChampions(s){",
       FINAL_VERIFIER+"\nfunction v99RepairBrazilLowerChampions(s){",
       "install authoritative Serie C final resolver"
    )
    html=once(
       html,
       "if(C?.finalTie){const w=v99TieWinner(s,C.finalTie,'C');if(w&&String(C.champion)!==String(w)){C.champion=w;C.runnerUp=String(w)===String(C.finalTie.a)?C.finalTie.b:C.finalTie.a;changed++;}if(w)v99RepairLeagueCoachTitle(s,3,w,'Brasileirao Serie C');}",
       """if(C){
    const w=v18345SerieCWinner(s),runner=w?(String(w)===String(C.finalTie.a)?C.finalTie.b:C.finalTie.a):null;
    if(String(C.champion||'')!==String(w||'')||String(C.runnerUp||'')!==String(runner||'')){
     C.champion=w;C.runnerUp=runner;changed++;
    }
    changed+=v18345CleanCClubTitles(s,w);
    changed+=v18345SyncCArchives(s,w,runner);
    if(w)v99RepairLeagueCoachTitle(s,3,w,'Brasileirao Serie C');
   }""",
       "replace unsafe partial-final result reconciliation"
    )
    html=once(
       html,
       "const div=Number(selectedDivision());if(div===3||div===4){const id=div===3?state.braLower?.serieC?.champion:state.braLower?.serieD?.champion,t=id?E.team(state,id):null;if(t)return {team:t,label:'Campeão',v99Lower:true};}",
       """const div=Number(selectedDivision());
      if(div===3&&state.braLower?.serieC){
       const id=v18345SerieCWinner(state),t=id?E.team(state,id):null;
       return t?{team:t,label:'Campeão',v99Lower:true}:null;
      }
      if(div===4){const id=state.braLower?.serieD?.champion,t=id?E.team(state,id):null;if(t)return {team:t,label:'Campeão',v99Lower:true};}""",
       "do not show generic first-phase leader as champion in competition UI"
    )
    # Optional on raw source smoke; required by the full 18.345 desktop pipeline.
    history_anchor="const champ=brazilLower?(brazilLower.champion||null):isMls?(mls?.champion||null):list[0]?.id;"
    if "FUTBR_CHAMPIONS_RETIREMENT_18322" in html:
        html=once(
          html,history_anchor,
          "const champ=brazilLower?(div===3?(window.GestorFC?.v18345SerieCWinner?.(s)||null):(brazilLower.champion||null)):isMls?(mls?.champion||null):list[0]?.id;",
          "champions history must read official Serie C final"
        )
    file.write_text(html,encoding="utf-8")
    report={"ok":True,"version":VERSION,"phaseOneQualifiedOnlyAfterComplete":True,
      "quadrangularCompleteBeforeFinal":True,"finalCreatedEvenWithProvisionalPromotions":True,
      "twoLegFinalAuthoritative":True,"noProvisionalChampion":True,
      "historicWinnerAndCoachTitlesReconciled":True,
      "legacyArchivesAndSavesPreserved":True}
    (root/"serie-c-champion-18345-install.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":main()
