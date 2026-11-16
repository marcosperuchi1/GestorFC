#!/usr/bin/env python3
"""FutBR Mobile 18.336: readable internal pages, no horizontal-scrolling tables.

Requires tested 18.335 Android patch and Windows gameplay 18.334. The
generated patch applies to Android assets only, not desktop distributions.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

MARK = "futbr-mobile-pages-18336"

CSS = r"""
<style id="futbr-mobile-pages-18336">
/* 18.336 - central scrolling belongs to the career, not to a cropped panel. */
html.futbr-android-alpha #app .main-wrap>.main,
html.futbr-android-alpha #app .main-wrap>#main-content {
  width:100%!important; min-width:0!important; max-width:100vw!important;
  flex:1 1 auto!important; height:auto!important; min-height:0!important;
  max-height:none!important; padding:12px clamp(12px,2.2vw,20px) 22px!important;
  overflow-y:auto!important; overflow-x:hidden!important;
  overscroll-behavior-y:contain; -webkit-overflow-scrolling:touch;
  scrollbar-gutter:auto!important;
}
html.futbr-android-alpha #app #v555-page {
  display:block!important; min-height:0!important; height:auto!important;
  max-height:none!important; min-width:0!important; max-width:100%!important;
  overflow:visible!important; contain:none!important;
}
html.futbr-android-alpha #app #main-content>.panel,
html.futbr-android-alpha #app #v555-page>.panel,
html.futbr-android-alpha #app #v555-page>section,
html.futbr-android-alpha #app #v555-page>div {
  width:100%!important; max-width:100%!important;
  min-width:0!important;
}
html.futbr-android-alpha #app #main-content :is(.panel,.panel-head,.panel-body,
  .filters,.field,.field-row,.tabs,.stack,.main-grid,.two-col) {
  min-width:0!important; max-width:100%;
}
/* The desktop's 18.613/18.614 fixed-height squad code hides roster entries.
   Force one vertical career scroller; do not make squad table an inner viewport. */
html.futbr-android-alpha body.v613-squad-view #app #v555-page .v553-squad-page,
html.futbr-android-alpha body.v614-squad-view #app #v555-page .v553-squad-page,
html.futbr-android-alpha #app #v555-page .v553-squad-page {
  display:block!important; flex:none!important;
  height:auto!important; min-height:0!important; max-height:none!important;
  width:100%!important; max-width:100%!important;
  overflow:visible!important; contain:none!important;
}
html.futbr-android-alpha body.v613-squad-view #app #v555-page .v57-squad-panel,
html.futbr-android-alpha body.v614-squad-view #app #v555-page .v57-squad-panel,
html.futbr-android-alpha #app #v555-page .v57-squad-panel {
  display:block!important; flex:none!important;
  height:auto!important; min-height:0!important; max-height:none!important;
  width:100%!important; max-width:100%!important;
  overflow:visible!important; contain:none!important;
}
html.futbr-android-alpha body.v613-squad-view #app #v555-page #squad-results,
html.futbr-android-alpha body.v614-squad-view #app #v555-page #squad-results,
html.futbr-android-alpha #app #v555-page #squad-results {
  display:block!important; flex:none!important;
  height:auto!important; min-height:0!important; max-height:none!important;
  width:100%!important; max-width:100%!important;
  overflow:visible!important; contain:none!important;
}
html.futbr-android-alpha body.v613-squad-view #app #v555-page #squad-results>.table-scroll,
html.futbr-android-alpha body.v614-squad-view #app #v555-page #squad-results>.table-scroll,
html.futbr-android-alpha #app #v555-page #squad-results>.table-scroll {
  display:block!important; flex:none!important;
  width:100%!important; height:auto!important;
  min-height:0!important; max-height:none!important;
  overflow:visible!important; position:static!important;
  scrollbar-gutter:auto!important; contain:none!important;
}
/* Squad filters are readable, not the 7-9px desktop micro-inputs. */
html.futbr-android-alpha #app .v553-squad-head {
  display:flex!important; align-items:stretch!important;
  flex-direction:column!important; gap:12px!important;
  padding:12px!important; height:auto!important; min-height:0!important;
}
html.futbr-android-alpha #app .v57-squad-toolbar {
  display:flex!important; align-items:stretch!important;
  flex-direction:column!important; gap:10px!important;
}
html.futbr-android-alpha #app .v57-squad-summary {
  display:flex!important; min-width:0!important; flex-wrap:wrap!important;
  gap:8px!important; align-items:center!important;
}
html.futbr-android-alpha #app .v57-squad-summary .pill,
html.futbr-android-alpha #app .v57-squad-summary .tiny {
  font-size:11px!important; line-height:1.35!important;
}
html.futbr-android-alpha #app .v57-squad-filters {
  width:100%!important; margin:0!important; display:grid!important;
  grid-template-columns:repeat(2,minmax(0,1fr))!important;
  gap:10px!important; align-items:end!important;
}
html.futbr-android-alpha #app .v57-squad-filters .field,
html.futbr-android-alpha #app .v57-squad-filters .field.compact {
  min-width:0!important; width:100%!important; margin:0!important;
  display:flex!important; flex-direction:column!important; gap:4px!important;
}
html.futbr-android-alpha #app .v57-squad-filters label {
  font-size:11px!important; line-height:1.4!important;
}
html.futbr-android-alpha #app .v57-squad-filters select {
  width:100%!important; height:40px!important; min-height:40px!important;
  padding:5px 10px!important; font-size:14px!important;
}
html.futbr-android-alpha #app .v553-squad-head>.btn {
  flex:none!important; margin:0!important; align-self:stretch!important;
  min-height:40px!important; font-size:13px!important;
}
/* Every large table is converted into an accessible vertical card list by
   the JS below. Preserve each existing <tr>, <td> and data-action handler. */
html.futbr-android-alpha :is(#main-content,#modal-root) .table-scroll.futbr-mobile-list {
  width:100%!important; max-width:100%!important; min-width:0!important;
  height:auto!important; max-height:none!important;
  overflow-x:visible!important; overflow-y:visible!important;
  position:static!important; display:block!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards,
html.futbr-android-alpha #app #squad-results table.futbr-mobile-cards {
  display:block!important; width:100%!important; min-width:0!important;
  max-width:100%!important; height:auto!important; max-height:none!important;
  margin:0!important; table-layout:auto!important;
  overflow:visible!important; border-spacing:0!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards thead {
  position:absolute!important; width:1px!important; height:1px!important;
  padding:0!important; margin:-1px!important;
  overflow:hidden!important; clip-path:inset(50%)!important;
  white-space:nowrap!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody {
  display:grid!important; width:100%!important; min-width:0!important;
  grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr))!important;
  align-items:start!important; gap:12px!important;
  overflow:visible!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr {
  display:grid!important; grid-template-columns:repeat(2,minmax(0,1fr))!important;
  align-items:start!important; gap:8px 12px!important;
  width:100%!important; min-width:0!important; max-width:100%!important;
  height:auto!important; min-height:0!important; max-height:none!important;
  padding:12px!important; border:1px solid var(--line,#365044)!important;
  border-radius:12px!important; box-shadow:0 3px 12px #0000001b!important;
  background:var(--panel,#14221a)!important;
  overflow:visible!important; content-visibility:visible!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td {
  display:flex!important; flex-direction:row!important;
  justify-content:space-between!important; align-items:center!important;
  flex-wrap:wrap!important; gap:4px 8px!important;
  min-width:0!important; max-width:100%!important; width:100%!important;
  min-height:26px!important; height:auto!important; max-height:none!important;
  padding:2px 0!important; margin:0!important;
  overflow:visible!important; text-align:left!important; border:0!important;
  font-size:12px!important; line-height:1.4!important;
  white-space:normal!important; overflow-wrap:anywhere!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td::before {
  content:attr(data-futbr-label)!important; display:inline!important;
  min-width:0!important; max-width:100%!important;
  font-size:10px!important; font-weight:500!important; line-height:1.2!important;
  color:var(--muted,#a4b8aa)!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td.futbr-mobile-primary {
  grid-column:1/-1!important; justify-content:flex-start!important;
  padding:2px 0 7px!important; border-bottom:1px solid var(--line,#3a4c41)!important;
  font-size:14px!important; font-weight:700!important;
  order:-1!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td.futbr-mobile-primary::before {
  display:none!important; content:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td[colspan] {
  grid-column:1/-1!important; display:block!important;
  padding:7px 4px!important; font-size:12px!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr:has(>td[colspan]) {
  grid-column:1/-1!important; display:block!important;
  border-radius:8px!important; padding:7px 12px!important;
  background:var(--panel2,#22392a)!important; box-shadow:none!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td :is(.player-name,.table-button) {
  max-width:100%!important; white-space:normal!important;
  font-size:13px!important; height:auto!important; min-height:30px!important;
  overflow:visible!important; text-overflow:clip!important;
  overflow-wrap:anywhere!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td :is(.rating,.role,.pill) {
  height:auto!important; min-height:24px!important; font-size:11px!important;
  flex:0 1 auto!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td :is(button,select) {
  min-height:32px!important; min-width:0!important; max-width:100%!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards .col-wage,
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards .col-value,
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards .col-morale,
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards .col-contract {
  display:flex!important; visibility:visible!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) table.futbr-mobile-cards tbody>tr>td[hidden] {
  display:none!important;
}
/* Simple, narrow tables with few columns also remain inside the screen. */
html.futbr-android-alpha :is(#main-content,#modal-root) .table-scroll.futbr-mobile-compact {
  width:100%!important; min-width:0!important; max-width:100%!important;
  overflow-x:hidden!important; overflow-y:visible!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) .futbr-mobile-compact table {
  width:100%!important; min-width:0!important; max-width:100%!important;
  table-layout:fixed!important;
}
html.futbr-android-alpha :is(#main-content,#modal-root) .futbr-mobile-compact td,
html.futbr-android-alpha :is(#main-content,#modal-root) .futbr-mobile-compact th {
  max-width:100%!important; min-width:0!important;
  padding:8px 5px!important; overflow-wrap:anywhere!important;
  white-space:normal!important; font-size:11px!important;
}
/* Touch-first navigation: no squeezed horizontal nav bar on phones. */
html.futbr-android-alpha #app>.sidebar {
  width:min(300px,88vw)!important; max-width:min(300px,88vw)!important;
  padding:max(12px,env(safe-area-inset-top)) 0 max(12px,env(safe-area-inset-bottom))!important;
}
html.futbr-android-alpha #app>.sidebar .brand {
  padding:10px 16px 14px!important; margin-bottom:8px!important;
}
html.futbr-android-alpha #app>.sidebar nav.nav {
  display:flex!important; flex-direction:column!important; align-items:stretch!important;
  justify-content:flex-start!important; width:100%!important;
  max-height:none!important; min-height:0!important; height:auto!important;
  overflow:visible!important; padding:4px 13px 12px!important;
  gap:7px!important;
}
html.futbr-android-alpha #app>.sidebar nav.nav>.v556-nav-group,
html.futbr-android-alpha #app>.sidebar .v556-nav-group {
  display:flex!important; flex-direction:column!important;
  align-items:stretch!important; gap:5px!important;
  min-width:0!important; max-width:100%!important;
}
html.futbr-android-alpha #app>.sidebar .v556-nav-sub {
  display:none; flex-direction:column!important;
  align-items:stretch!important; width:100%!important;
  padding:3px 0 5px 12px!important; gap:5px!important;
}
html.futbr-android-alpha #app>.sidebar .v556-nav-group.open>.v556-nav-sub {
  display:flex!important;
}
html.futbr-android-alpha #app>.sidebar nav.nav button {
  display:flex!important; align-items:center!important;
  width:100%!important; min-height:44px!important; height:auto!important;
  padding:9px 13px!important; margin:0!important;
  border-radius:9px!important; text-align:left!important;
  gap:11px!important; font-size:13px!important; line-height:1.3!important;
  white-space:normal!important;
}
html.futbr-android-alpha #app>.sidebar nav.nav button.v556-nav-child {
  min-height:40px!important; padding:8px 12px!important;
  font-size:12px!important;
}
html.futbr-android-alpha #app>.sidebar .sidebar-bottom {
  margin-top:12px!important; padding:12px 15px!important;
}
/* Fit cards, grids and inputs across other game screens. Prefer vertical
   movement over squeezing desktop columns or allowing sideways scrolling. */
html.futbr-android-alpha #main-content :is(.v5-workbench,.v5-control-grid,
  .v5-overview,.main-grid,.two-col,.three-col,.grid-2,.grid-3,
  .v57-performance-grid,.stat-grid,.stats-grid,.dashboard-grid) {
  grid-template-columns:minmax(0,1fr)!important;
  min-width:0!important; max-width:100%!important; width:100%!important;
}
html.futbr-android-alpha #main-content :is(.tabs,.filters,.page-title,
  .panel-head,.toolbar,.flex.between,.top-actions,.pill-row) {
  flex-wrap:wrap!important; min-width:0!important;
  max-width:100%!important; gap:8px!important;
}
html.futbr-android-alpha #main-content .tabs {
  display:flex!important; width:100%!important;
  overflow:visible!important; gap:7px!important; padding:5px 0 9px!important;
}
html.futbr-android-alpha #main-content .tabs :is(.tab,button) {
  flex:0 1 auto!important; min-width:0!important;
  min-height:38px!important; height:auto!important;
  padding:8px 12px!important; font-size:12px!important;
}
html.futbr-android-alpha #main-content .filters {
  display:flex!important; align-items:end!important; gap:10px!important;
  width:100%!important; padding:6px 0!important;
}
html.futbr-android-alpha #main-content .filters>.field {
  flex:1 1 125px!important; width:auto!important; min-width:0!important;
}
html.futbr-android-alpha #main-content :is(.panel,.panel-body,.card) {
  min-width:0!important; max-width:100%!important;
}
html.futbr-android-alpha #main-content :is(.v5-board,.v5-pitch,.pitch,.tactics-board,
  .v5-workbench>.panel) {
  max-width:100%!important; min-width:0!important; width:100%!important;
}
html.futbr-android-alpha #main-content :is(.bracket,.bracket-grid,
 .bracket-rounds,.bracket-stage,.bracket-columns) {
  max-width:100%!important; min-width:0!important;
  grid-template-columns:minmax(0,1fr)!important;
  grid-auto-flow:row!important;
}
html.futbr-android-alpha #main-content :is(h1,h2,h3,.page-title,.panel-head,
  .table-scroll,.card,.notice) {
  overflow-wrap:anywhere;
}
html.futbr-android-alpha #modal-root .modal-body {
  max-width:100%!important; min-width:0!important;
  overflow-x:hidden!important; overflow-y:auto!important;
}
html.futbr-android-alpha #modal-root :is(.modal-tabs,.tabs) {
  display:flex!important; flex-wrap:wrap!important;
  width:100%!important; gap:7px!important;
}
html.futbr-android-alpha #modal-root :is(.modal-tabs,.tabs) button {
  min-height:36px!important; height:auto!important;
}
/* Status/top area: balanced touch targets without compressing all menus. */
html.futbr-android-alpha #app .main-wrap>.topbar {
  gap:10px!important; padding:9px 12px 9px 58px!important;
}
html.futbr-android-alpha #app .main-wrap>.topbar .top-actions {
  gap:8px!important; flex-wrap:wrap!important;
}
html.futbr-android-alpha #app .main-wrap>.topbar :is(button,.btn) {
  min-height:40px!important; padding:8px 10px!important;
  font-size:12px!important;
}
html.futbr-android-alpha #futbr-mobile-nav-button {
  width:43px!important; height:43px!important;
  min-width:43px!important; top:max(9px,env(safe-area-inset-top))!important;
  left:max(10px,env(safe-area-inset-left))!important;
}
@media(max-width:530px) {
  html.futbr-android-alpha #main-content .v57-squad-filters {
    grid-template-columns:minmax(0,1fr)!important;
  }
  html.futbr-android-alpha :is(#main-content,#modal-root)
    table.futbr-mobile-cards tbody {
    grid-template-columns:minmax(0,1fr)!important;
  }
}
</style>
"""

JS = r"""
<script id="futbr-mobile-table-cards-18336">
(function(){
 if(!document.documentElement.classList.contains('futbr-android-alpha'))return;
 var scheduled=false;
 function getHeader(table){
  var thead=table.tHead;
  if(!thead || !thead.rows.length)return [];
  var row=thead.rows[thead.rows.length-1];
  return Array.from(row.cells).map(function(cell){
   return (cell.textContent||'').replace(/\s+/g,' ').trim().slice(0,28);
  });
 }
 function primaryIndex(headers){
  var re=/^(atleta|nome|jogador|clube|sele(c|ç)(a|ã)o|equipe|t(e|é)cnico)/i;
  var idx=headers.findIndex(function(s){return re.test(s);});
  return idx<0?0:idx;
 }
 function decorate(table){
  if(!table || !table.tBodies || !table.tBodies.length)return;
  var headers=getHeader(table);
  var first=table.tBodies[0].rows[0];
  var cells=first?first.cells.length:0;
  var count=Math.max(headers.length,cells);
  var wrap=table.closest('.table-scroll');
  if(!wrap)return;
  if(count<=4){
   wrap.classList.add('futbr-mobile-compact');
   return;
  }
  wrap.classList.add('futbr-mobile-list');
  table.classList.add('futbr-mobile-cards');
  var prime=primaryIndex(headers);
  for(var body of table.tBodies){
   for(var row of body.rows){
    if(row.dataset.futbrMobileRow==='18336')continue;
    row.dataset.futbrMobileRow='18336';
    if(row.cells.length===1 && row.cells[0].colSpan>1)continue;
    for(var i=0;i<row.cells.length;i++){
     var cell=row.cells[i];
     if(!cell || cell.colSpan>1)continue;
     var label=headers[i]||('Campo '+(i+1));
     cell.setAttribute('data-futbr-label',label);
     if(i===prime)cell.classList.add('futbr-mobile-primary');
    }
   }
  }
 }
 function scan(){
  scheduled=false;
  var tables=document.querySelectorAll(
   '#main-content .table-scroll > table, #main-content .table-scroll table,'+
   '#modal-root .table-scroll > table, #modal-root .table-scroll table');
  for(var table of tables)decorate(table);
 }
 function requestScan(){
  if(scheduled)return;
  scheduled=true;
  requestAnimationFrame(scan);
 }
 var app=document.getElementById('app');
 var root=document.getElementById('modal-root');
 var observer=new MutationObserver(function(records){
  for(var i=0;i<records.length;i++){
   if(records[i].addedNodes && records[i].addedNodes.length){
    requestScan();return;
   }
   if(records[i].removedNodes && records[i].removedNodes.length){
    requestScan();return;
   }
  }
 });
 if(app)observer.observe(app,{subtree:true,childList:true});
 if(root)observer.observe(root,{subtree:true,childList:true});
 requestScan();
 window.FutBRMobile18336={
  version:'18.336',pcBase:'18.334',squadCards:true,
  verticalScreens:true,menuSpacing:true,scan:scan
 };
})();
</script>
"""

def main(project: Path) -> None:
    project=project.resolve()
    html=project/'src'/'index.html'
    src=html.read_text(encoding='utf-8')
    for prereq in ('futbr-mobile-responsive-18335',
                   'FUTBR_UNEMPLOYED_RESUME_18334_BEGIN',
                   'FUTBR_SCOUT_RESPONSIVE_18331'):
        if prereq not in src:raise RuntimeError('Missing prerequisite '+prereq)
    if MARK in src:raise RuntimeError('18.336 patch already applied')
    if src.count('</body>')!=1:raise RuntimeError('Invalid HTML body')
    html.write_text(src.replace('</body>',CSS+JS+'</body>',1),encoding='utf-8')
    report={'ok':True,'mobile':'18.336','pc_base':'18.334',
     'squad':'full-height-unlocked and vertical cards',
     'internal_tables':'responsive cards with actual headers',
     'nav':'touch-spaced drawer','scroll':'vertical per screen',
     'original_data_actions_preserved':True,'windows_modified':False}
    (project/'mobile-pages-18336-report.json').write_text(
        json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: apply_mobile_internal_pages_18336.py PROJECT')
    main(Path(sys.argv[1]))
