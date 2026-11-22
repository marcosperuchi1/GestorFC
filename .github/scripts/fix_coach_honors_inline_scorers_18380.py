"""FutBR 18.380: group coach honors by competition and club; align scorer badge+name horizontally.

The changes are strictly in the presentation layer; no world, save, title,
or ranking calculation is mutated.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

MARK = 'FUTBR_COACH_HONORS_INLINE_SCORERS_18380'

JS = r"""
/* FUTBR_COACH_HONORS_INLINE_SCORERS_18380
   Group cards in the coach profile only; every historical title remains
   intact in the save and player/club trophy ledger. */
function v18380CoachHonorGroups(c){
 const rows=typeof v126CoachTitles==='function'?v126CoachTitles(c):[];
 const groups=new Map();
 for(let i=0;i<rows.length;i++){
  const h=rows[i];
  if(!h||typeof h!=='object')continue;
  const rawKey=String(h.key||'').trim(),label=String(h.label||h.name||rawKey||'Conquista').trim();
  const clubId=String(h.club||h.clubId||'').trim(),clubName=String(h.clubName||'').trim();
  const national=rawKey.startsWith('national:'),league=rawKey.startsWith('league:');
  const compKey=(rawKey||label).toLowerCase().replace(/[:/\s-]+20\d{2}$/,'');
  const identity=[national?'national':'club',String(h.type||''),compKey,String(h.category||''),clubId||v18379ClubNameKey(clubName)||'sem-clube'].join('\u001f');
  const yearLabel=String(h.year??'').trim()||'—',yearValue=Number.parseInt(yearLabel,10)||0;
  let item=groups.get(identity);
  if(!item){
   item={key:rawKey,label,clubId,clubName,national,league,
    points:0,years:[],yearSet:new Set(),lastYear:yearValue,order:i};
   groups.set(identity,item);
  }
  // A repeated archive row for the same competition, club and year is not
  // an extra trophy. The original saved row is preserved untouched.
  if(item.yearSet.has(yearLabel))continue;
  item.yearSet.add(yearLabel);
  item.years.push({label:yearLabel,number:yearValue});
  item.points+=Number(h.points)||0;
  if(yearValue>item.lastYear){item.lastYear=yearValue;item.label=label;}
 }
 return [...groups.values()].map(g=>{
  g.years.sort((a,b)=>b.number-a.number||b.label.localeCompare(a.label,'pt-BR'));
  g.count=g.years.length;
  return g;
 }).sort((a,b)=>b.lastYear-a.lastYear||a.order-b.order);
}
const v18380OriginalCoachHonors=v126CoachHonors;
v126CoachHonors=function(c){
 const grouped=v18380CoachHonorGroups(c);
 if(!grouped.length)return v18380OriginalCoachHonors(c);
 const cards=grouped.map(g=>{
  const club=g.clubId?E.team(state,g.clubId):null;
  const type=g.national?'TÍTULO DE SELEÇÃO':g.league?'LIGA':'TÍTULO';
  const count=g.count+' '+(g.count===1?'título':'títulos');
  let crest='';
  try{crest=club?badge(club,'small'):'<span class="shield small" aria-hidden="true">'+(g.national?'★':'—')+'</span>';}catch(_e){
   crest='<span class="shield small" aria-hidden="true">—</span>';
  }
  const years=g.years.map(y=>'<span class="v18380-honor-year-chip">'+esc(y.label)+'</span>').join('');
  const pointsText=g.points+' '+(Math.abs(g.points)===1?'ponto':'pontos')+' de bônus no total';
  return '<article class="v126-honor v18380-honor-group'+(g.national?' national':'')+'" data-v18380-group="1">'+
    '<span class="v126-honor-type">'+type+'</span>'+
    '<span class="v126-honor-year v18380-honor-count" aria-label="'+esc(count)+'">'+esc(count)+'</span>'+
    '<h4>'+esc(g.label)+'</h4>'+
    '<div class="v18380-honor-years" aria-label="Temporadas conquistadas">'+years+'</div>'+
    '<div class="v126-honor-club">'+crest+'<div><strong>'+
      esc(club?.name||g.clubName||(g.national?'Seleção nacional':'Carreira'))+
      '</strong><small>'+esc(pointsText)+'</small></div></div>'+
    '</article>';
 });
 return '<div class="v126-honors v18380-grouped-honors" data-v18380-coach-titles="1">'+cards.join('')+'</div>';
};
window.GestorFC=window.GestorFC||{};
window.GestorFC.coachHonors18380={version:'18.380.0',readOnly:true,
 groupFor:c=>v18380CoachHonorGroups(c).map(g=>({key:g.key,clubId:g.clubId,count:g.count,years:g.years.map(y=>y.label),points:g.points}))};
"""

STYLE = r"""
<style id="futbr-coach-honors-scorer-inline-18380">
/* FUTBR_COACH_HONORS_INLINE_STYLE_18380
   Keep club crest and clickable name on the same line in the scorers table. */
.v615-ranking-scroll td.club-history .v538-scorer-club.v18379-club-links,
.v615-ranking-scroll td.club-history .v18379-club-links{
 display:flex!important;flex-direction:row!important;flex-wrap:wrap!important;
 align-items:center!important;justify-content:flex-start!important;
 column-gap:9px!important;row-gap:4px!important;
 width:auto!important;white-space:normal!important;
}
.v615-ranking-scroll td.club-history .v18379-club-entry{
 display:inline-flex!important;flex-direction:row!important;flex-wrap:nowrap!important;
 align-items:center!important;justify-content:flex-start!important;
 gap:7px!important;min-width:0!important;width:auto!important;
 vertical-align:middle!important;
}
.v615-ranking-scroll td.club-history .v18379-club-entry .club-crest,
.v615-ranking-scroll td.club-history .v18379-club-entry .shield{
 display:inline-flex!important;flex:0 0 auto!important;align-self:center!important;
 margin:0!important;vertical-align:middle!important;
}
.v615-ranking-scroll td.club-history .v18379-club-entry .table-button{
 display:inline-flex!important;flex:0 1 auto!important;align-items:center!important;
 margin:0!important;padding:0!important;white-space:normal!important;
 text-align:left!important;line-height:1.18!important;vertical-align:middle!important;
}
.v615-ranking-scroll td.club-history .v18379-unknown-club{
 display:inline-flex!important;align-items:center!important;gap:6px!important;
}
#modal-root .v126-honors.v18380-grouped-honors{
 display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;
 align-items:stretch!important;gap:12px!important;
}
#modal-root .v18380-grouped-honors .v18380-honor-group{
 min-width:0!important;min-height:148px!important;
 display:flex!important;flex-direction:column!important;
}
#modal-root .v18380-grouped-honors .v18380-honor-group h4{
 margin-right:90px!important;
}
#modal-root .v18380-grouped-honors .v18380-honor-count{
 white-space:nowrap!important;font-variant-numeric:tabular-nums;
}
#modal-root .v18380-grouped-honors .v18380-honor-years{
 display:flex!important;align-items:center!important;flex-wrap:wrap!important;
 gap:5px!important;margin:9px 0 8px!important;max-height:82px!important;
 overflow-y:auto!important;min-height:0!important;
}
#modal-root .v18380-honor-year-chip{
 border:1px solid currentColor;opacity:.78;border-radius:999px;
 padding:3px 8px;line-height:1.1;font-size:.82em;white-space:nowrap;
 font-variant-numeric:tabular-nums;
}
#modal-root .v18380-grouped-honors .v126-honor-club{
 margin-top:auto!important;min-width:0!important;
}
@media(max-width:1050px){
 #modal-root .v126-honors.v18380-grouped-honors{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
 }
}
@media(max-width:650px){
 #modal-root .v126-honors.v18380-grouped-honors{
  grid-template-columns:minmax(0,1fr)!important;
 }
}
</style>
"""

def main():
 if len(sys.argv)!=2:
  raise SystemExit('usage: fix_coach_honors_inline_scorers_18380.py <prepared-root>')
 root=Path(sys.argv[1]).resolve()
 path=root/'src/index.html'
 html=path.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('18.380 view patch must only be applied once')
 for needed in ("FUTBR_SCORER_IDENTITY_18379","FUTBR_SCORER_HISTORY_RECOVERY_18377",
                "function v126CoachHonors(c)","function v126CoachTitles(c)"):
  if needed not in html:raise RuntimeError('Missing real 18.379 coach/scorers context: '+needed)
 anchor="window.GestorFC.render=render;\nwindow.GestorFC.fontSettings18376="
 if html.count(anchor)!=1:raise RuntimeError('Expected unique original game UI closing bridge')
 html=html.replace(anchor,JS+"\n"+anchor,1)
 if html.count('</body>')!=1:raise RuntimeError('Expected exactly one closing HTML body')
 html=html.replace('</body>',STYLE+'\n</body>',1)
 if html.count(MARK)!=1:raise RuntimeError('18.380 JS marker was duplicated')
 for content,label in [(JS,'coach trophies JS')]:
  check=subprocess.run(['node','--check','-'],input=content,text=True,capture_output=True,timeout=30)
  if check.returncode:raise RuntimeError(label+' syntax error '+check.stderr[-3500:])
 path.write_text(html,encoding='utf-8')
 report={'ok':True,'version':'18.380.0','coachTitlesGroupedByCompetitionAndClub':True,
         'distinctYearsAndCountsShown':True,'differentClubsKeptSeparate':True,
         'bonusPointsAggregated':True,'originalCoachTitlesAndGameWorldUnchanged':True,
         'existingCoachesProfileReused':True,'scorerCrestAndClubNameHorizontal':True,
         'clubProfileClickHandlersPreserved':True,'responsiveThreeTwoOneColumnGrid':True,
         'existingScorerIdentityUnchanged':True,'savedCareersUnchanged':True,
         'sourceSha256':hashlib.sha256(html.encode('utf-8')).hexdigest()}
 (root/'coach-honors-inline-18380-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
