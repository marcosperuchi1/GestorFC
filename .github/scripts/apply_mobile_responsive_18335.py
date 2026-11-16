#!/usr/bin/env python3
"""FutBR Manager mobile 18.335: responsive controls scoped to Android only.

Apply after 18.334 gameplay patch and after prepare_android_alpha.py.
Do not modify simulation logic or the Windows build.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

MARKER = "futbr-mobile-responsive-18335"

STYLE = r"""
<style id="futbr-mobile-responsive-18335">
/* Mobile-only shell. Overrides desktop's forced-height welcome and auth. */
html.futbr-android-alpha, html.futbr-android-alpha body {
 width:100%!important; height:100%!important; min-width:0!important;
 margin:0!important; padding:0!important;
 overflow:hidden!important; overscroll-behavior:none!important;
 -webkit-text-size-adjust:100%;
}
html.futbr-android-alpha #app {
 position:fixed!important; inset:0!important;
 width:100vw!important; height:100dvh!important;
 max-width:100vw!important; max-height:100dvh!important;
 min-width:0!important; overflow:hidden!important;
}
html.futbr-android-alpha *,html.futbr-android-alpha *::before,
html.futbr-android-alpha *::after {box-sizing:border-box}
html.futbr-android-alpha :is(input,select,textarea,button) {
 max-width:100%; touch-action:manipulation;
}
html.futbr-android-alpha :is(input,select,textarea) {font-size:16px!important}
html.futbr-android-alpha .btn {min-height:38px}
html.futbr-android-alpha :is(.field,.field-row,.country-filters) {min-width:0}

/* Login. The desktop marketing column uses most of a phone screen, so
   remove only the marketing column; preserve complete login/registration. */
html.futbr-android-alpha #app .v548-auth {
 display:block!important; width:100%!important; height:100dvh!important;
 min-height:0!important; max-height:100dvh!important;
 overflow-x:hidden!important; overflow-y:auto!important;
 overscroll-behavior:contain;
 padding: max(8px,env(safe-area-inset-top)) max(10px,env(safe-area-inset-right))
  max(12px,env(safe-area-inset-bottom)) max(10px,env(safe-area-inset-left))!important;
}
html.futbr-android-alpha #app .v548-auth-shell {
 display:block!important; width:min(100%,660px)!important;
 min-width:0!important; height:auto!important; min-height:0!important;
 max-width:660px!important; max-height:none!important;
 margin:0 auto!important; gap:0!important;
 overflow:visible!important; transform:none!important;
}
html.futbr-android-alpha #app .v548-auth-brand {display:none!important}
html.futbr-android-alpha #app .v548-auth-card {
 display:block!important; width:100%!important; min-width:0!important;
 min-height:0!important; height:auto!important; max-height:none!important;
 margin:0!important; padding:14px clamp(12px,2.8vw,22px)!important;
 overflow:visible!important; transform:none!important;
}
html.futbr-android-alpha #app .v548-auth-card::before {
 content:"FutBR MANAGER  |  MOBILE ALPHA";
 display:block; color:#72e5a0; font-size:12px; font-weight:700;
 letter-spacing:.6px; margin-bottom:8px;
}
html.futbr-android-alpha #app .v548-auth-tabs {margin:0 0 9px!important}
html.futbr-android-alpha #app .v548-auth-card h2 {
 font-size:clamp(18px,3vw,23px)!important; margin:4px 0!important;
}
html.futbr-android-alpha #app .v548-auth-card>.subtext {
 font-size:12px!important; margin:0 0 8px!important;
}
html.futbr-android-alpha #app .v548-auth-form {
 gap:8px!important; width:100%!important; min-width:0!important;
}
html.futbr-android-alpha #app .v548-auth-form .field {gap:3px!important}
html.futbr-android-alpha #app .v548-auth-form :is(input,select) {
 min-height:42px!important; width:100%!important;
}
html.futbr-android-alpha #app .v548-auth-form .btn {min-height:42px!important}
html.futbr-android-alpha #app .v548-auth-foot {display:none!important}

/* Initial career menu. Remove desktop no-scroll + 640px fixed card.
   Every field remains available with one-finger vertical scrolling. */
html.futbr-android-alpha #app .welcome,
html.futbr-android-alpha #app .welcome.v570-career-start {
 display:block!important; width:100%!important; max-width:100vw!important;
 height:100dvh!important; min-height:0!important; max-height:100dvh!important;
 margin:0!important;
 overflow-x:hidden!important; overflow-y:auto!important;
 overscroll-behavior-y:contain;
 padding:max(8px,env(safe-area-inset-top)) max(10px,env(safe-area-inset-right))
 max(20px,env(safe-area-inset-bottom)) max(10px,env(safe-area-inset-left))!important;
}
html.futbr-android-alpha #app .welcome .welcome-top,
html.futbr-android-alpha #app .welcome.v570-career-start .welcome-top {
 height:auto!important; min-height:36px!important; max-height:none!important;
 flex:0 0 auto!important; width:100%!important; margin:0 0 8px!important;
 padding:0!important;
}
html.futbr-android-alpha #app .welcome .welcome-top .brand {min-width:0}
html.futbr-android-alpha #app .welcome .welcome-top .brandname {
 font-size:clamp(13px,2vw,17px)!important; white-space:normal!important;
}
html.futbr-android-alpha #app .welcome .welcome-top :is(.eyebrow,small,.pill) {
 font-size:10px!important;
}
html.futbr-android-alpha #app .welcome .welcome-main,
html.futbr-android-alpha #app .welcome.v570-career-start .welcome-main {
 display:block!important; width:100%!important; height:auto!important;
 min-height:0!important; max-height:none!important; min-width:0!important;
 grid-template-columns:minmax(0,1fr)!important; gap:0!important;
 padding:0!important; margin:0!important; overflow:visible!important;
 transform:none!important; align-items:stretch!important;
}
html.futbr-android-alpha #app .welcome .welcome-copy {display:none!important}
html.futbr-android-alpha #app .welcome .setup-card,
html.futbr-android-alpha #app .welcome.v570-career-start .setup-card,
html.futbr-android-alpha #app .welcome.v570-career-start .setup-card.v648-stable-card {
 display:block!important; position:relative!important;
 width:100%!important; max-width:none!important; min-width:0!important;
 height:auto!important; max-height:none!important; min-height:0!important;
 flex:0 0 auto!important; align-self:stretch!important;
 margin:0 auto!important; padding:clamp(10px,2.2vw,18px)!important;
 overflow:visible!important; transform:none!important;
}
html.futbr-android-alpha #app .welcome .setup-card>* {
 max-width:100%!important; min-width:0!important;
}
html.futbr-android-alpha #app .welcome .setup-card>.mt24:has([data-action="new-career"]) {
 margin:12px 0 0!important; flex:0 0 auto!important;
}
html.futbr-android-alpha #app .welcome .setup-card .v658-career-hero {
 height:auto!important; min-height:0!important; max-height:140px!important;
 overflow:hidden!important; padding:8px!important;
}
html.futbr-android-alpha #app .welcome .setup-card .v658-career-hero img {
 max-height:95px!important; object-fit:contain!important;
}
html.futbr-android-alpha #app .welcome .setup-card :is(.country-filters,.field-row) {
 display:grid!important; grid-template-columns:repeat(2,minmax(0,1fr))!important;
 gap:8px!important; width:100%!important;
}
html.futbr-android-alpha #app .welcome .setup-card :is(input,select,textarea) {
 min-width:0!important; width:100%!important;
 min-height:40px!important; font-size:16px!important;
}
html.futbr-android-alpha #app .welcome .setup-card :is(button,.btn) {
 min-width:0; min-height:40px!important;
}
html.futbr-android-alpha #app .welcome .welcome-bottom {display:none!important}
html.futbr-android-alpha #app .welcome .v643-start-mode,
html.futbr-android-alpha #app .welcome #v643-national-start {
 width:100%!important; min-width:0!important; height:auto!important;
 min-height:0!important; max-height:none!important;
 overflow:visible!important; flex:0 0 auto!important;
}

/* Actual match/career shell: hide the long desktop nav in a touch drawer.
   Keep the original game buttons and all the data-action handlers. */
html.futbr-android-alpha #app:has(>.sidebar) {
 display:flex!important; flex-direction:row!important;
 align-items:stretch!important; overflow:hidden!important;
}
html.futbr-android-alpha #app>.sidebar {
 position:fixed!important; top:0!important; left:0!important;
 bottom:0!important; width:min(290px,84vw)!important;
 max-width:min(290px,84vw)!important; height:100dvh!important;
 max-height:100dvh!important; margin:0!important;
 z-index:10050!important; overflow-x:hidden!important;
 overflow-y:auto!important; transform:translateX(-104%)!important;
 transition:transform .2s ease!important;
 box-shadow:14px 0 30px rgba(0,0,0,.35);
}
/* Lift the career shell above the backdrop, but permit clicks only on the drawer.
   The backdrop lives outside #app, which creates its own fixed stacking context. */
html.futbr-android-alpha.futbr-mobile-nav-open #app {
 z-index:10055!important; pointer-events:none!important;
}
html.futbr-android-alpha.futbr-mobile-nav-open #app>.sidebar {
 transform:translateX(0)!important; pointer-events:auto!important;
}
html.futbr-android-alpha #app>.main-wrap {
 display:flex!important; flex-direction:column!important; flex:1 1 auto!important;
 width:100vw!important; min-width:0!important; max-width:100vw!important;
 height:100dvh!important; min-height:0!important; max-height:100dvh!important;
 margin:0!important; padding:0!important; overflow:hidden!important;
}
html.futbr-android-alpha #app .main-wrap>.topbar {
 display:flex!important; flex:0 0 auto!important; min-width:0!important;
 width:100%!important; min-height:48px!important; max-height:none!important;
 height:auto!important; padding:5px 8px 5px 52px!important;
 gap:6px!important; flex-wrap:wrap!important; align-items:center!important;
}
html.futbr-android-alpha #app .main-wrap>.topbar .club-top,
html.futbr-android-alpha #app .main-wrap>.topbar .top-actions {
 min-width:0!important; max-width:100%!important; flex-wrap:wrap!important;
}
html.futbr-android-alpha #app .main-wrap>.topbar .topbar-title {
 font-size:clamp(12px,1.8vw,16px)!important; line-height:1.15!important;
}
html.futbr-android-alpha #app .main-wrap>.topbar .topbar-meta {
 font-size:10px!important; line-height:1.3!important;
}
html.futbr-android-alpha #app .main-wrap>.topbar :is(button,.btn) {
 min-height:36px!important; font-size:11px!important;
}
html.futbr-android-alpha #app .main-wrap>.main,
html.futbr-android-alpha #app .main-wrap>#main-content {
 display:block!important; flex:1 1 auto!important; min-height:0!important;
 width:100%!important; min-width:0!important; max-width:100vw!important;
 height:auto!important; max-height:none!important;
 padding:8px!important; margin:0!important;
 overflow-x:auto!important; overflow-y:auto!important;
 overscroll-behavior:contain;
 -webkit-overflow-scrolling:touch;
}
html.futbr-android-alpha #app #v555-page,
html.futbr-android-alpha #app #main-content {min-width:0!important}
html.futbr-android-alpha #app :is(.panel,.panel-body,.card,.main-grid,.two-col) {
 max-width:100%; min-width:0;
}
html.futbr-android-alpha #app :is(.table-scroll,.table-wrap,.table-responsive) {
 overflow-x:auto!important; max-width:100%!important;
 -webkit-overflow-scrolling:touch;
}
/* Preserve data tables and tactics, letting their contents scroll rather
   than shrinking every row to illegible text. */
html.futbr-android-alpha #app #main-content table {
 max-width:none; font-size:12px;
}
html.futbr-android-alpha #app .main .btn {min-height:36px}
html.futbr-android-alpha #app .main :is(input,select,textarea) {max-width:100%}

/* Modal overlays must be reachable on short landscape devices. */
html.futbr-android-alpha #modal-root {
 position:fixed!important; inset:0!important; z-index:11000!important;
 pointer-events:none;
}
html.futbr-android-alpha #modal-root .overlay {
 pointer-events:auto!important; overflow-x:hidden!important;
 overflow-y:auto!important; align-items:flex-start!important;
 padding:max(6px,env(safe-area-inset-top)) 8px max(8px,env(safe-area-inset-bottom))!important;
}
html.futbr-android-alpha #modal-root .modal {
 width:min(96vw,920px)!important; min-width:0!important;
 max-width:min(96vw,920px)!important; max-height:calc(100dvh - 14px)!important;
 overflow-x:auto!important; overflow-y:auto!important;
 margin:auto!important;
}
html.futbr-android-alpha #modal-root button {min-height:36px}

/* Drawer menu affordance. Appears only while a career sidebar is present. */
html.futbr-android-alpha #futbr-mobile-nav-button {
 display:none; position:fixed; top:max(7px,env(safe-area-inset-top));
 left:max(8px,env(safe-area-inset-left));
 width:38px; height:38px; min-width:38px; z-index:10040;
 border:1px solid #4d9465; border-radius:10px;
 background:#102d1b; color:#e9ffec;
 font:700 23px/1 system-ui,sans-serif; align-items:center; justify-content:center;
 box-shadow:0 2px 10px #0008;
}
html.futbr-android-alpha:has(#app>.sidebar) #futbr-mobile-nav-button {
 display:flex!important;
}
html.futbr-android-alpha #futbr-mobile-nav-shade {
 display:none; position:fixed; inset:0; border:0; padding:0;
 background:rgba(0,0,0,.6); z-index:10045;
}
html.futbr-android-alpha.futbr-mobile-nav-open #futbr-mobile-nav-shade {
 display:block!important;
}
@media(max-width:540px) {
 html.futbr-android-alpha #app .welcome .setup-card :is(.country-filters,.field-row) {
  grid-template-columns:minmax(0,1fr)!important;
 }
 html.futbr-android-alpha #app .v548-auth-card {padding:11px!important}
 html.futbr-android-alpha #app .main-wrap>.topbar .top-actions {
  width:100%!important; padding-left:0!important;
 }
}
@media(prefers-reduced-motion:reduce) {
 html.futbr-android-alpha #app>.sidebar {transition:none!important}
}
</style>
"""

SCRIPT = r"""
<script id="futbr-mobile-touch-navigation-18335">
(function(){
 if(!document.documentElement.classList.contains('futbr-android-alpha'))return;
 var root=document.documentElement;
 var shade=document.createElement('button');
 shade.id='futbr-mobile-nav-shade';
 shade.type='button';
 shade.tabIndex=-1;
 shade.setAttribute('aria-label','Fechar menu');
 var button=document.createElement('button');
 button.id='futbr-mobile-nav-button';
 button.type='button';
 button.textContent='\u2630';
 button.setAttribute('aria-label','Abrir menu do jogo');
 button.setAttribute('aria-expanded','false');
 function close(){
  root.classList.remove('futbr-mobile-nav-open');
  button.setAttribute('aria-expanded','false');
 }
 button.addEventListener('click',function(){
  var next=!root.classList.contains('futbr-mobile-nav-open');
  root.classList.toggle('futbr-mobile-nav-open',next);
  button.setAttribute('aria-expanded',String(next));
 });
 shade.addEventListener('click',close);
 document.body.appendChild(shade);
 document.body.appendChild(button);
 document.addEventListener('click',function(event){
  if(event.target.closest && event.target.closest('.sidebar [data-action="nav"]'))close();
 },true);
 document.addEventListener('keydown',function(event){if(event.key==='Escape')close();});
 document.addEventListener('focusin',function(event){
  if(!event.target.matches || !event.target.matches('input,select,textarea'))return;
  var field=event.target;
  setTimeout(function(){
   if(field.isConnected && field.scrollIntoView)
    field.scrollIntoView({block:'nearest',inline:'nearest',behavior:'auto'});
  },140);
 },true);
 window.FutBRMobile18335={version:'18.335',pcBase:'18.334',
  landscape:true,closeMenu:close,scrollableWelcome:true};
})();
</script>
"""

def main(project:Path):
    project=project.resolve()
    path=project/'src'/'index.html'
    text=path.read_text(encoding='utf-8')
    if text.count(MARKER):raise RuntimeError('Mobile layout patch already applied')
    for marker in ('futbr-android-alpha-bootstrap-v1',
                   'FUTBR_UNEMPLOYED_RESUME_18334_BEGIN',
                   'FUTBR_SCOUT_RESPONSIVE_18331'):
        if marker not in text:raise RuntimeError('Missing prerequisite '+marker)
    if text.count('</body>')!=1:raise RuntimeError('Invalid body closing tag')
    text=text.replace('</body>', STYLE+SCRIPT+'</body>',1)
    path.write_text(text,encoding='utf-8')
    report={'mobile_version':'18.335','pc_gameplay':'18.334',
            'menu':'touch drawer','auth':'scrollable single column',
            'welcome':'responsive full-width, vertical scroll',
            'gameplay':'full-screen content with drawer',
            'fix_unemployed_18334':True,'windows_modified':False}
    (project/'mobile-responsive-18335-report.json').write_text(
        json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':
    if len(sys.argv)!=2:raise SystemExit('usage: apply_mobile_responsive_18335.py <project>')
    main(Path(sys.argv[1]))
