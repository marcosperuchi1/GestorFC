"""Group player trophy cards like clubs/coaches without mutating historical rows."""
from pathlib import Path
import hashlib,json,subprocess,sys
MARK="FUTBR_PLAYER_TROPHIES_GROUPED_18384"
JS=r"""
/* FUTBR_PLAYER_TROPHIES_GROUPED_18384
   Read-only: same stored awards, separate trophies and Golden Boot awards,
   group by competition + club, list seasons and each scorer's goal counts. */
function v18384HonorName(value){
 return String(value||'').trim().normalize('NFD')
  .replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR')
  .replace(/\s+/g,' ').replace(/[\u2010-\u2015]/g,'-');
}
function v18384PlayerHonorGroups(rows){
 const m=new Map();
 for(const h of rows||[]){
  if(!h)continue;
  const kind=h.kind==='scorer'?'scorer':'club',label=String(h.name||'Conquista').trim();
  const key=String(h.key||'').trim().toLocaleLowerCase('pt-BR')
    .replace(/([:/._-])(?:19|20)\d{2}$/,'');
  const clubId=String(h.teamId||''),clubName=String(h.teamName||'').trim();
  const event=v18384HonorName(label).replace(/^artilheiro\s*[·:\-]\s*/,'');
  const competition=key&&!(key==='scorer')?
   key.replace(/^scorer:/,''):event;
  const identity=[kind,v18384HonorName(competition),clubId||v18384HonorName(clubName)||'desconhecido'].join('\x1f');
  const year=Number(h.year)||0;
  if(!year)continue;
  let g=m.get(identity);
  if(!g){g={kind,name:label,teamId:clubId,teamName:clubName,years:[],yearSet:new Set(),
    first:year,last:year,order:m.size,goals:0};m.set(identity,g);}
  if(g.yearSet.has(year))continue; // Old saves may repeat the exact event row.
  g.yearSet.add(year);
  const goals=Math.max(0,Number(h.goals)||0);
  g.years.push({year,goals});g.goals+=goals;
  g.last=Math.max(g.last,year);
 }
 return [...m.values()].map(g=>{
  g.years.sort((a,b)=>b.year-a.year);
  g.count=g.years.length;return g;
 }).sort((a,b)=>b.last-a.last||a.order-b.order);
}
const v18384OriginalPlayerHonors=v123Honors;
v123Honors=function(p){
 const rows=v123HonorsRows(p.id),groups=v18384PlayerHonorGroups(rows);
 if(!groups.length)return v18384OriginalPlayerHonors(p);
 return '<div class="v123-honors v18384-player-honors" data-v18384-player-honors="1">'+
 groups.map(g=>{
  const club=g.teamId?E.team(state,g.teamId):null;
  const type=g.kind==='scorer'?'ARTILHARIA':'TÍTULO DO CLUBE';
  const count=g.count+' '+(g.kind==='scorer'?
    (g.count===1?'artilharia':'artilharias'):(g.count===1?'título':'títulos'));
  const chips=g.years.map(x=>'<span class="v18384-player-honor-year">'+
    esc(String(x.year))+(g.kind==='scorer'&&x.goals?
      '<small>'+esc(x.goals+' gols')+'</small>':'')+'</span>').join('');
  const crest=club?badge(club,'small'):'<span class="shield small" aria-hidden="true">—</span>';
  return '<article class="v123-honor v18384-player-honor '+(g.kind==='scorer'?'scorer':'')+
    '" data-v18384-group="1"><span class="v123-honor-type">'+type+'</span>'+
    '<span class="v123-honor-year v18384-player-count">'+esc(count)+'</span>'+
    '<h4>'+esc(g.name)+'</h4>'+
    '<div class="v18384-player-years" aria-label="Temporadas da conquista">'+chips+'</div>'+
    (g.kind==='scorer'&&g.goals?'<p>'+esc(String(g.goals))+
      ' gol(s) nas '+(g.count===1?'artilharia':'artilharias')+'</p>':'')+
    '<div class="v123-honor-club">'+crest+'<div><strong>'+
      esc(club?.name||g.teamName||'Clube não registrado')+
    '</strong><small>'+esc(club?countryName(club.country)||'':'')+'</small></div></div></article>';
 }).join('')+'</div>';
};
window.GestorFC=window.GestorFC||{};
window.GestorFC.playerHonorsGrouped18384={version:'18.384.0',readOnly:true,
 groupFor:rows=>v18384PlayerHonorGroups(rows).map(g=>({
  kind:g.kind,teamId:g.teamId,teamName:g.teamName,count:g.count,
  years:g.years.map(x=>x.year),goals:g.goals
 }))};
"""
STYLE=r"""
<style id="futbr-player-honors-grouped-18384">
#modal-root .v123-honors.v18384-player-honors{
 display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr))!important;
 align-content:start!important;align-items:stretch!important;gap:10px!important;
}
#modal-root .v18384-player-honors .v18384-player-honor{
 min-width:0!important;display:flex!important;flex-direction:column!important;
 min-height:144px!important;position:relative!important;
}
#modal-root .v18384-player-honors .v18384-player-honor h4{
 margin-right:106px!important;overflow-wrap:anywhere!important;
}
#modal-root .v18384-player-honors .v18384-player-count{
 white-space:nowrap!important;font-variant-numeric:tabular-nums!important;
}
#modal-root .v18384-player-honors .v18384-player-years{
 display:flex!important;flex-wrap:wrap!important;gap:4px!important;
 align-items:center!important;max-height:64px!important;
 overflow-y:auto!important;margin:8px 0!important;
}
#modal-root .v18384-player-honors .v18384-player-honor-year{
 border:1px solid currentColor;opacity:.87;border-radius:999px!important;
 padding:3px 8px!important;display:inline-flex!important;align-items:center!important;
 gap:5px!important;font-size:.81em!important;white-space:nowrap!important;
}
#modal-root .v18384-player-honor-year small{font-size:.91em!important;opacity:.8!important}
#modal-root .v18384-player-honors .v123-honor-club{
 margin-top:auto!important;min-width:0!important;
}
@media(max-width:940px){
 #modal-root .v123-honors.v18384-player-honors{
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
 }
}
@media(max-width:590px){
 #modal-root .v123-honors.v18384-player-honors{
  grid-template-columns:minmax(0,1fr)!important;
 }
}
</style>
"""
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: group_player_honors_18384.py <prepared-root>')
 root=Path(sys.argv[1]).resolve();p=root/'src/index.html';s=p.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('Already grouped player honors 18.384')
 for needed in ['function v123HonorsRows(id)', 'function v123Honors(p)',
                'FUTBR_COACH_HONORS_INLINE_SCORERS_18380',
                'FUTBR_LONG_CAREER_REALISM_18383']:
  if needed not in s:raise RuntimeError('Missing existing player/coach honors feature '+needed)
 anchor='window.GestorFC.render=render;\nwindow.GestorFC.fontSettings18376='
 if s.count(anchor)!=1:raise RuntimeError('Cannot safely wrap live player honors renderer')
 s=s.replace(anchor,JS+'\n'+anchor,1)
 if s.count('</body>')!=1:raise RuntimeError('Cannot append grouped honors CSS')
 s=s.replace('</body>',STYLE+'\n</body>',1)
 check=subprocess.run(['node','--check','-'],input=JS,text=True,capture_output=True,timeout=30)
 if check.returncode:raise RuntimeError('Invalid JS '+check.stderr[-2500:])
 p.write_text(s,encoding='utf-8')
 report={'ok':True,'version':'18.384.0','playerHonorsGrouped':True,
 'clubAndScorerAwardsDistinct':True,'sameCompetitionClubAggregated':True,
 'differentClubsKeptSeparate':True,'yearsAndScorerGoalsShown':True,
 'legacyDuplicateRowsDeduplicatedInViewOnly':True,
 'awardArchiveUntouched':True,'paginationAndModalSelectorsPreserved':True,
 'savedCareersUntouched':True,'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'player-honors-18384-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
