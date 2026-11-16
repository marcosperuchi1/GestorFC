#!/usr/bin/env python3
"""FutBR Mobile 18.337 - compact vertical lists for squads and competitions.

After mobile 18.336, preserve exact rows, action handlers and original stats.
Only Android view changes; desktop game engine and 18.334 fix stay intact.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

MARKER="futbr-mobile-lists-18337"
CSS=r"""
<style id="futbr-mobile-lists-18337">
/* A SINGLE COMPACT LIST: remove 18.336 generic cards on squad and league tables. */
html.futbr-android-alpha :is(#main-content,#modal-root) .table-scroll.futbr-mobile-list:has(table.futbr-mobile-slim) {
 display:block!important; width:100%!important; max-width:100%!important;
 min-width:0!important; height:auto!important; max-height:none!important;
 overflow-x:hidden!important; overflow-y:visible!important;
 position:static!important; padding:0!important; scrollbar-gutter:auto!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards.futbr-mobile-slim,
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim {
 display:block!important; width:100%!important; max-width:100%!important; min-width:0!important;
 height:auto!important; margin:0!important; border:0!important;
 border-collapse:collapse!important; background:transparent!important;
 table-layout:auto!important; overflow:visible!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim thead {
 display:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody {
 display:block!important; width:100%!important; min-width:0!important; max-width:100%!important;
 padding:0!important; margin:0!important; border:0!important;
 background:transparent!important; overflow:visible!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr {
 display:flex!important; flex-direction:row!important; align-items:center!important;
 justify-content:space-between!important; flex-wrap:nowrap!important;
 width:100%!important; min-width:0!important; max-width:100%!important;
 min-height:47px!important; height:auto!important; max-height:none!important;
 gap:7px!important; padding:7px 8px!important; margin:0!important;
 border:0!important; border-bottom:1px solid var(--line,#3a5343)!important;
 border-radius:0!important; box-shadow:none!important; outline:0!important;
 background:transparent!important; overflow:visible!important;
 content-visibility:visible!important; contain:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr:nth-child(even) {
 background:rgba(128,164,133,.045)!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr:active {
 background:rgba(92,192,122,.1)!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td {
 display:none!important; flex:none!important; align-items:center!important;
 justify-content:center!important; flex-direction:column!important;
 width:auto!important; max-width:none!important; min-width:0!important;
 height:auto!important; min-height:24px!important; max-height:none!important;
 order:0!important; margin:0!important; padding:0!important;
 border:0!important; background:transparent!important;
 font-size:12px!important; line-height:1.25!important;
 white-space:normal!important; overflow:visible!important;
 text-overflow:clip!important; text-align:center!important;
 overflow-wrap:anywhere!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-show {
 display:flex!important; visibility:visible!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-name {
 flex:1 1 0!important; align-items:flex-start!important; justify-content:center!important;
 order:1!important; text-align:left!important; min-width:64px!important;
 max-width:none!important; font-size:12.5px!important; font-weight:650!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-name::before {
 display:none!important; content:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-rank {
 order:0!important; flex:0 0 26px!important; font-weight:750!important;
 color:var(--muted,#a8bdac)!important; font-size:11px!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-metric {
 flex:0 0 auto!important; order:2!important; width:clamp(36px,6vw,52px)!important;
 font-size:12px!important; font-weight:700!important; color:var(--text,#f4fff5)!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-metric::before {
 display:block!important; content:attr(data-futbr-label)!important;
 min-width:0!important; font-size:9px!important; font-weight:450!important;
 color:var(--muted,#9db09f)!important; line-height:1.15!important;
 margin:0 0 3px!important; text-align:center!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-rank::before {
 display:none!important;content:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-action {
 order:5!important; flex:0 0 auto!important; width:auto!important;
 max-width:100px!important; padding-left:4px!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-action::before {
 display:none!important;content:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-empty {
 display:block!important; width:100%!important; max-width:100%!important;
 flex:1 1 100%!important; font-size:12px!important; text-align:left!important;
 padding:10px 0!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-empty::before {
 content:none!important;display:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr:has(>td.futbr-list-empty) {
 min-height:40px!important; padding:5px 10px!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-show :is(.table-button,.player-name,.v641-national-team-cell) {
 display:inline-flex!important; align-items:center!important;
 max-width:100%!important; width:auto!important;
 min-width:0!important; min-height:34px!important; height:auto!important;
 padding:3px 0!important; border:0!important;
 font-size:12px!important; font-weight:650!important;
 line-height:1.25!important; text-align:left!important;
 white-space:normal!important; overflow-wrap:anywhere!important;
 overflow:visible!important; text-overflow:clip!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-show :is(.role,.rating,.pill) {
 display:inline-flex!important; align-items:center!important; justify-content:center!important;
 height:auto!important; min-height:23px!important; max-width:100%!important;
 padding:2px 4px!important; font-size:11px!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-show :is(.star-badge,.v527-star-inline) {
 display:inline!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-action button {
 display:inline-flex!important; justify-content:center!important; align-items:center!important;
 min-height:34px!important; padding:6px 8px!important; font-size:11px!important;
}
/* Filters and summary are one row with comfortable spacing. */
html.futbr-android-alpha #app .v553-squad-head {
 padding:10px 12px!important; gap:10px!important;
}
html.futbr-android-alpha #app .v57-squad-filters {
 gap:9px!important; grid-template-columns:repeat(2,minmax(0,1fr))!important;
}
html.futbr-android-alpha #app .v57-squad-panel #squad-results {
 overflow:visible!important; width:100%!important; height:auto!important;
 min-height:0!important; max-height:none!important;
}
/* Other competition results that use cards instead of tables are restrained
   to a clean, vertically stacked score list without decorative tiles. */
html.futbr-android-alpha body.futbr-mobile-competition #v555-page :is(.result-card,.fixture-card,.match-card) {
 display:flex!important; flex-wrap:wrap!important; align-items:center!important;
 justify-content:space-between!important;
 width:100%!important; max-width:100%!important;
 min-height:43px!important; height:auto!important; max-height:none!important;
 margin:0!important; padding:9px 10px!important; gap:6px 12px!important;
 border:0!important; border-bottom:1px solid var(--line,#3a5343)!important;
 border-radius:0!important; box-shadow:none!important;
 background:transparent!important;
}
html.futbr-android-alpha body.futbr-mobile-competition #v555-page :is(.result-list,.fixtures,.fixture-list,.matches-list) {
 display:flex!important; flex-direction:column!important;
 width:100%!important; max-width:100%!important;
 min-width:0!important; gap:0!important;
 grid-template-columns:minmax(0,1fr)!important;
}
html.futbr-android-alpha body.futbr-mobile-competition #v555-page :is(.result-card,.fixture-card,.match-card) .score {
 font-size:14px!important; font-weight:750!important;
}
html.futbr-android-alpha #main-content :is(.table-scroll,table) {
 max-width:100%!important;
}
@media(max-width:530px) {
 html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr {
   gap:5px!important; padding:7px 4px!important;
 }
 html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-metric {
   width:34px!important; font-size:11px!important;
 }
 html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-rank {
   flex-basis:22px!important;
 }
 html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-slim tbody>tr>td.futbr-list-name {
   min-width:52px!important; font-size:11.5px!important;
 }
}
</style>
"""

JS=r"""
<script id="futbr-mobile-lists-script-18337">
(function(){
 if(!document.documentElement.classList.contains('futbr-android-alpha'))return;
 var queued=false,frame=0;
 function norm(v){return String(v||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/\s+/g,' ').trim();}
 function headers(table){
  var head=table.tHead;
  if(!head||!head.rows.length)return [];
  return Array.from(head.rows[head.rows.length-1].cells).map(function(cell){
   return norm(cell.textContent);
  });
 }
 function find(heads,patterns){
  for(var p of patterns){
   var ix=heads.findIndex(function(h){return p.test(h);});
   if(ix>=0)return ix;
  }return -1;
 }
 function eligible(table,head){
  var squad=!!table.closest('#squad-results,.v553-squad-page,.v133-national-squad-page,.v57-squad-page');
  if(squad)return 'squad';
  var hasTeam=head.some(function(h){return /^(clube|equipe|selecao|time|clubes|selecoes)$/.test(h);});
  var hasPoints=head.some(function(h){return /^(pts|pontos|pt|p)$/.test(h);});
  var hasMatches=head.some(function(h){return /^(j|jogos|pj|partidas)$/.test(h);});
  if(hasTeam&&hasPoints&&hasMatches)return 'table';
  var parent=table.closest('#v555-page');
  var competition=document.body.classList.contains('futbr-mobile-competition');
  if(parent&&competition&&head.length>=5)return 'competition';
  return null;
 }
 function chosen(head,kind){
  var name=find(head,[/^(atleta|nome|jogador|clube|equipe|selecao|time)$/,/^(mandante|casa|visitante)$/]);
  var rank=find(head,[/^(#|pos|posicao|classificacao|rank)$/]);
  var pos=find(head,[/^(pos|pos\.|posicao|funcao)$/]);
  var strength=find(head,[/^(forca|ovr|nota|rating)$/]);
  var fitness=find(head,[/^(fisico|forma|condicao)$/]);
  var points=find(head,[/^(pts|pontos|pt|p)$/]);
  var games=find(head,[/^(j|jogos|pj|partidas)$/]);
  var diff=find(head,[/^(sg|saldo|saldo de gols)$/]);
  var score=find(head,[/^(placar|resultado|score)$/]);
  var away=find(head,[/^(visitante|fora)$/]);
  var chosenIdx=[];
  function add(idx){if(idx>=0&&!chosenIdx.includes(idx))chosenIdx.push(idx);}
  if(kind==='squad'){
   add(name);add(pos);add(strength);add(fitness);
  }else if(kind==='table'){
   add(rank);add(name);add(points);add(games);add(diff);
  }else{
   add(rank);add(name);add(points);add(games);add(score);add(away);
  }
  if(!chosenIdx.length || (chosenIdx.length===1&&head.length>=5)){
   add(0);add(1);add(2);add(3);
  }
  if(name<0 && kind==='squad')add(0);
  return {indices:chosenIdx,name:name,rank:rank};
 }
 function updateCompetitionFlag(){
  var nav=document.querySelector('#app .sidebar [data-view].active,#app .sidebar [data-view][aria-current="page"]');
  var selected=nav&&nav.getAttribute('data-view');
  var tab=document.querySelector('#v555-page .tabs');
  var competition=selected==='competitions'||selected==='world'||selected==='rankings'||
    !!(document.querySelector('#v555-page .v641-national-rank-panel'));
  // Do not infer competition from a generic tab that appears in many pages.
  document.body.classList.toggle('futbr-mobile-competition',!!competition);
 }
 function decorate(table){
  if(!table||!table.tBodies||!table.tBodies.length)return;
  var head=headers(table),kind=eligible(table,head);
  if(!kind)return;
  var plan=chosen(head,kind),indices=plan.indices;
  table.classList.add('futbr-mobile-slim');
  table.dataset.futbrListKind=kind;
  for(var body of table.tBodies){
   for(var row of body.rows){
    if(row.dataset.futbrListDone==='18337')continue;
    row.dataset.futbrListDone='18337';
    if(row.cells.length===1 && row.cells[0].colSpan>1){
     row.cells[0].classList.add('futbr-list-show','futbr-list-empty');
     continue;
    }
    var visible=new Set(indices);
    var extraAction=-1;
    for(var i=0;i<row.cells.length;i++){
     var cell=row.cells[i];
     // Critical: never hide a button used to cut a national call-up, place
     // a transfer bid or open another gameplay action.
     if(cell.querySelector('button[data-action],a[data-action]') && !visible.has(i)){
      extraAction=i;
     }
    }
    if(extraAction>=0)visible.add(extraAction);
    for(var i=0;i<row.cells.length;i++){
     var cell=row.cells[i],active=visible.has(i);
     if(cell.colSpan>1){cell.classList.add('futbr-list-show','futbr-list-empty');continue;}
     cell.classList.toggle('futbr-list-show',active);
     if(!active)continue;
     if(i===plan.name || (plan.name<0&&i===0)){
      cell.classList.add('futbr-list-name');
     }else if(i===plan.rank && kind!=='squad'){
      cell.classList.add('futbr-list-rank');
     }else if(i===extraAction&&!indices.includes(i)){
      cell.classList.add('futbr-list-action');
     }else{
      cell.classList.add('futbr-list-metric');
     }
    }
  }
 }
 }
 function scan(){
  queued=false;
  updateCompetitionFlag();
  var tables=document.querySelectorAll('#main-content .table-scroll table,#modal-root .table-scroll table');
  for(var t of tables)decorate(t);
 }
 function schedule(){
  if(queued)return;queued=true;
  window.requestAnimationFrame(scan);
 }
 var obs=new MutationObserver(function(records){
  for(var rec of records){
   if(rec.addedNodes.length || rec.removedNodes.length){schedule();return;}
  }
 });
 var app=document.getElementById('app'),modal=document.getElementById('modal-root');
 if(app)obs.observe(app,{subtree:true,childList:true});
 if(modal)obs.observe(modal,{subtree:true,childList:true});
 document.addEventListener('click',function(evt){
  if(evt.target.closest && evt.target.closest('.sidebar [data-view]'))schedule();
 },true);
 schedule();
 window.FutBRMobile18337={version:'18.337',pcBase:'18.334',lists:true,scan:scan};
})();
</script>
"""
def main(project:Path)->None:
    project=project.resolve();p=project/'src'/'index.html'
    s=p.read_text(encoding='utf-8')
    for key in ('futbr-mobile-pages-18336','futbr-mobile-responsive-18335',
                'FUTBR_UNEMPLOYED_RESUME_18334_BEGIN'):
        if key not in s:raise RuntimeError('Missing prerequisite '+key)
    if MARKER in s:raise RuntimeError('already installed')
    if s.count('</body>')!=1:raise RuntimeError('invalid body')
    s=s.replace('</body>',CSS+JS+'</body>',1)
    p.write_text(s,encoding='utf-8')
    report={'mobile':'18.337','pc_base':'18.334','change':'squad and competition lists',
      'squad_fields':'name, position, strength, fitness',
      'standings_fields':'rank, club, points, games, goal difference',
      'original_button_handlers_preserved':True,'windows_modified':False}
    (project/'mobile-lists-18337-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: apply_mobile_lists_18337.py PROJECT')
    main(Path(sys.argv[1]))
