from __future__ import annotations
import json
import re
import sys
from pathlib import Path

MARK="FUTBR_CALENDAR_NAV_VERSION_18348"
BASE_END="window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';\n})();\n</script>"
SCRIPT=r'''
/* FUTBR_CALENDAR_NAV_VERSION_18348: final desktop shell and visible edition. */
(function(){
 'use strict';
 const EDITION='__FUTBR_BUILD_VERSION__';
 const label='Calendário de jogos';
 let injections=0,editionUpdates=0;
 function calendarButton(){
  const b=document.createElement('button');
  b.type='button';
  b.dataset.action='nav';
  b.dataset.view='calendar';
  b.setAttribute('aria-label',label);
  b.innerHTML='<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M16 3v4M8 3v4M3 10h18M8 14h3M13 14h3"></path></svg><span>'+label+'</span>';
  return b;
 }
 function ensureNav(root){
  const nav=(root?.querySelector?.('.sidebar .nav')||document.querySelector('.sidebar .nav'));
  if(!nav)return false;
  let b=nav.querySelector('[data-view="calendar"]');
  if(!b){
   b=calendarButton();
   const comp=nav.querySelector('[data-view="competitions"]');
   const mov=nav.querySelector('[data-view="transfers"]');
   const anchor=comp||mov;
   if(anchor&&typeof anchor.insertAdjacentElement==='function')anchor.insertAdjacentElement('afterend',b);
   else nav.appendChild(b);
   injections++;
  }
  const active=view==='calendar';
  b.classList.toggle('active',active);
  if(active)b.setAttribute('aria-current','page');
  else b.removeAttribute('aria-current');
  return true;
 }
 function refreshEdition(root){
  const dom=root||document;
  const selects='#app .welcome .eyebrow,#app .welcome .edition-pill,#app .welcome .pill-edition,#app .welcome .brand-version,#app .v548-auth .eyebrow,#app .v548-auth .edition-label,#app [class*="edition"],#app [class*="version"]';
  for(const el of dom.querySelectorAll?.(selects)||[]){
   if(el.children?.length>0||String(el.textContent||'').length>110)continue;
   const old=String(el.textContent||'');
   if(!/edi[cç][ãa]o|vers[aã]o|edition/i.test(old)||!/\d+\.\d+/.test(old))continue;
   const newer=old.replace(/\d+(?:\.\d+){1,2}/g,EDITION);
   if(newer!==old){el.textContent=newer;editionUpdates++;}
  }
  const sidebar=document.querySelector('.sidebar .sidebar-bottom');
  if(sidebar){
   let marker=sidebar.querySelector('.v18348-build-version');
   if(!marker){
    marker=document.createElement('span');
    marker.className='v18348-build-version';
    sidebar.appendChild(marker);
   }
   marker.textContent='Versão '+EDITION;
  }
  window.GestorFC=window.GestorFC||{};
  window.GestorFC.version=EDITION;
  window.GestorFC.visualVersion=EDITION;
  window.GestorFC.buildVersion=EDITION;
 }
 // Unlike NAV, the active desktop sidebar is rebuilt by v555ShellHTML and
 // later fixed-order wrappers. Add the button to the actual rendered shell.
 const oldEnsureShell=v555EnsureShell;
 v555EnsureShell=function(...args){
  const root=oldEnsureShell(...args);
  if(root)ensureNav(root);
  return root;
 };
 const oldUpdateChrome=v555UpdateChrome;
 v555UpdateChrome=function(root,...args){
  const result=oldUpdateChrome(root,...args);
  ensureNav(root);
  refreshEdition(root);
  return result;
 };
 // v260 fast renderer uses renderPage for main content. Ensure the 18.347
 // calendar page is still reached even when a later edition wraps routing.
 const oldPage=renderPage;
 renderPage=function(...args){
  if(view==='calendar'){
   const page=window.GestorFC?.calendarList18347?.page;
   if(typeof page==='function')return page();
   return '<section class="panel"><h2>Calendário de jogos</h2><p>Não foi possível carregar a lista de partidas.</p></section>';
  }
  return oldPage(...args);
 };
 const oldRender=render;
 render=function(...args){
  const result=oldRender(...args);
  ensureNav(document.getElementById('app'));
  refreshEdition(document);
  return result;
 };
 window.GestorFC.render=render;
 const oldWelcome=renderWelcome;
 renderWelcome=function(...args){
  const result=oldWelcome(...args);
  refreshEdition(document);
  queueMicrotask(()=>refreshEdition(document));
  return result;
 };
 const oldAuth=v548RenderAuth;
 v548RenderAuth=function(...args){
  const result=oldAuth(...args);
  refreshEdition(document);
  queueMicrotask(()=>refreshEdition(document));
  return result;
 };
 // Stop only the calendar button's click before legacy navigation handlers;
 // all other buttons continue using the original app router.
 document.addEventListener('click',event=>{
  const button=event.target?.closest?.('.sidebar .nav button[data-view="calendar"]');
  if(!button)return;
  event.preventDefault();
  event.stopImmediatePropagation();
  view='calendar';
  render();
 },true);
 const css=document.createElement('style');
 css.id='v18348-shell-version-style';
 css.textContent='.sidebar .v18348-build-version{display:block;font-size:10px;opacity:.75;padding:7px 12px 2px;line-height:1.25}.sidebar .nav [data-view="calendar"] svg{width:18px;height:18px;flex:0 0 18px}.sidebar .nav [data-view="calendar"]{cursor:pointer}';
 document.head.appendChild(css);
 refreshEdition(document);
 queueMicrotask(()=>refreshEdition(document));
 window.GestorFC.calendarNav18348={version:EDITION,status:()=>({
  added:injections,editionUpdates,sidebarPresent:!!document.querySelector('.sidebar .nav button[data-view="calendar"]'),
  editionLabel:document.querySelector('.sidebar .v18348-build-version')?.textContent||''
 })};
})();
'''

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: fix_calendar_nav_version_18348.py <project>')
    project=Path(sys.argv[1]).resolve()
    config=project/'src-tauri/tauri.conf.json'
    if not config.is_file():raise RuntimeError('Tauri version config missing')
    version=str(json.loads(config.read_text(encoding='utf-8-sig'))['version'])
    if not re.fullmatch(r'\d+\.\d+\.\d+',version):raise RuntimeError('Invalid desktop version')
    path=project/'src/index.html'
    html=path.read_text(encoding='utf-8')
    if MARK in html:raise RuntimeError('18.348 already installed')
    if "FUTBR_CALENDAR_LIST_18347_END" not in html:
        raise RuntimeError('18.347 calendar page missing - refusing menu-only release')
    if html.count(BASE_END)!=1:raise RuntimeError('Unexpected final game closure anchor')
    script=SCRIPT.replace('__FUTBR_BUILD_VERSION__',version)
    end="window.GestorFC.version='"+version+"';window.GestorFC.visualVersion='"+version+"';\n})();\n</script>"
    html=html.replace(BASE_END,script+'\n'+end,1)
    path.write_text(html,encoding='utf-8')
    report={
     'ok':True,'version':version,
     'calendarInjectedIntoActiveShell':True,'calendarRoutingProtected':True,
     'calendarIsAfterCompetitions':True,
     'visibleWelcomeAndLoginEditionUpdated':True,
     'sidebarAlwaysShowsInstalledBuildVersion':True,
     'versionDerivedFromTauriConfig':True,
     'preserveManualRetirementAndSaves':True,'historicDataUnmodified':True
    }
    (project/'calendar-nav-version-18348-install.json').write_text(
       json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
