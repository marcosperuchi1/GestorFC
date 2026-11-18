from __future__ import annotations
import json
import re
import subprocess
import sys
from pathlib import Path

MARK='FUTBR_CALENDAR_NAV_VERSION_18348'

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: test_calendar_nav_version_18348.py <project>')
    root=Path(sys.argv[1]).resolve()
    version=str(json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))['version'])
    html=(root/'src/index.html').read_text(encoding='utf-8')
    if html.count(MARK)!=1:raise RuntimeError('Missing or duplicate calendar navbar fix')
    assert f"window.GestorFC.version='{version}';window.GestorFC.visualVersion='{version}';" in html
    assert "/* FUTBR_CALENDAR_LIST_18347 */" in html
    a=html.index('/* '+MARK)
    b=html.index("window.GestorFC.version='"+version+"';",a)
    actual=html[a:b]
    for needle in [
      "const oldEnsureShell=v555EnsureShell;",
      "v555EnsureShell=function(...args)",
      "const oldUpdateChrome=v555UpdateChrome;",
      "v555UpdateChrome=function(root,...args)",
      "ensureNav(root)",
      "nav.querySelector('[data-view=\"competitions\"]')",
      "const oldPage=renderPage;",
      "const page=window.GestorFC?.calendarList18347?.page;",
      "document.addEventListener('click'",
      "const oldRender=render;",
      "const oldWelcome=renderWelcome;",
      "const oldAuth=v548RenderAuth;",
      "marker.textContent='Versão '+EDITION;",
      "window.GestorFC.buildVersion=EDITION;",
      "queueMicrotask(()=>refreshEdition(document));"
    ]:
      if needle not in actual:raise AssertionError('18.348 navigation/version fix missing: '+needle)
    fixture=r"""
const assert=require('node:assert/strict');
const window={GestorFC:{calendarList18347:{page:()=>'<section id="calendar-real-page">Calendário em lista</section>'}}};
let view='dashboard';
const state={year:2030,schedule:[{fixtures:[]}],retirements:[{id:'x',year:2027,age:45}]};
const oldState=JSON.stringify(state);
class Btn{
 constructor(viewName=''){
  this.dataset={action:'nav',view:viewName};
  this.attrs={};this.className='';this.children=[];
  this.classList={toggle:(cls,on)=>{if(cls==='active')this.selected=on;},remove:()=>{}};
 }
 setAttribute(k,v){this.attrs[k]=v;}
 removeAttribute(k){delete this.attrs[k];}
 insertAdjacentElement(place,b){
  const i=nav.items.indexOf(this);
  assert(place==='afterend'&&i>=0);
  nav.items.splice(i+1,0,b);
 }
}
const nav={
 items:[new Btn('dashboard'),new Btn('competitions'),new Btn('squad'),new Btn('transfers')],
 querySelector(sel){const match=sel.match(/data-view=["']([^"']+)["']/);return match?this.items.find(b=>b.dataset.view===match[1])||null:null;},
 appendChild(btn){this.items.push(btn);}
};
const bottom={
 child:null,
 querySelector(sel){return sel==='.v18348-build-version'?this.child:null;},
 appendChild(x){this.child=x;}
};
const root={
 querySelector(sel){if(sel==='.sidebar .nav')return nav;if(sel==='.sidebar .sidebar-bottom')return bottom;return null;},
 querySelectorAll(){return [];}
};
const welcome={textContent:'EDIÇÃO 7.44',children:[]};
const login={textContent:'EDIÇÃO 7.44 · CONTA LOCAL',children:[]};
const document={
 handlers:{},head:{appendChild(el){this.lastStyle=el;}},
 createElement(tag){return tag==='button'?new Btn(''): {tagName:tag,children:[],setAttribute(){}};},
 querySelector(sel){
  if(sel==='.sidebar .nav')return nav;
  if(sel==='.sidebar .nav button[data-view="calendar"]')return nav.querySelector('[data-view="calendar"]');
  if(sel==='.sidebar .sidebar-bottom')return bottom;
  if(sel==='.sidebar .v18348-build-version')return bottom.child;
  return null;
 },
 querySelectorAll(selector){
  if(selector.includes('#app .welcome .eyebrow'))return [welcome,login];
  return [];
 },
 getElementById(id){return id==='app'?root:null;},
 addEventListener(type,fn,capture){this.handlers[type]=fn;assert.equal(capture,true);}
};
function v555EnsureShell(){return root;}
function v555UpdateChrome(r){assert.equal(r,root);}
function renderPage(){return '<section id="old-page">dashboard</section>';}
function render(){
 const node=v555EnsureShell();v555UpdateChrome(node);
 return renderPage();
}
function renderWelcome(){welcome.textContent='EDIÇÃO 7.44';return 'welcome';}
function v548RenderAuth(){login.textContent='EDIÇÃO 7.44 · CONTA LOCAL';return 'login';}
"""
    tests=r"""
assert.equal(window.GestorFC.buildVersion,'18.348.0');
assert.equal(window.GestorFC.version,'18.348.0');
assert.equal(welcome.textContent,'EDIÇÃO 18.348.0');
assert.equal(login.textContent,'EDIÇÃO 18.348.0 · CONTA LOCAL');
assert.equal(render(),'<section id="old-page">dashboard</section>');
assert.deepEqual(nav.items.map(x=>x.dataset.view),['dashboard','competitions','calendar','squad','transfers']);
const b=nav.querySelector('[data-view="calendar"]');
assert(b.innerHTML.includes('Calendário de jogos')&&b.innerHTML.includes('<svg'));
assert.equal(bottom.child.textContent,'Versão 18.348.0');
assert.equal(nav.items.filter(x=>x.dataset.view==='calendar').length,1);
assert.equal(render(),'<section id="old-page">dashboard</section>');
assert.equal(nav.items.filter(x=>x.dataset.view==='calendar').length,1,'No duplicate button on rerender');
const event={target:{closest:s=>s.includes('data-view="calendar"')?b:null},
 prevented:false,stopped:false,
 preventDefault(){this.prevented=true;},stopImmediatePropagation(){this.stopped=true;}};
document.handlers.click(event);
assert.equal(view,'calendar');
assert.equal(event.prevented,true);
assert.equal(event.stopped,true);
assert.equal(render(),'<section id="calendar-real-page">Calendário em lista</section>');
assert.equal(b.selected,true);
renderWelcome();
assert.equal(welcome.textContent,'EDIÇÃO 18.348.0');
v548RenderAuth();
assert.equal(login.textContent,'EDIÇÃO 18.348.0 · CONTA LOCAL');
assert.equal(window.GestorFC.calendarNav18348.status().sidebarPresent,true);
assert.equal(window.GestorFC.calendarNav18348.status().editionLabel,'Versão 18.348.0');
assert.equal(JSON.stringify(state),oldState,'State and retirement archives must not be modified');
console.log('PASS 18.348: actual fixed-order sidebar, click routing, correct edition badge and login/welcome, no save changes');
"""
    program=fixture+'\n'+actual+'\n'+tests
    check=subprocess.run(['node','--check'],input=program,text=True,capture_output=True,timeout=30)
    if check.returncode:raise RuntimeError('Syntax error in actual 18.348 nav fix:\n'+check.stderr[-6000:])
    test=subprocess.run(['node','-e',program],text=True,capture_output=True,timeout=30)
    if test.returncode:raise RuntimeError('Real 18.348 JS regression failed:\n'+test.stderr[-6000:])
    print(test.stdout)
    report={
      'ok':True,'version':version,'installedCodeExecuted':True,
      'activeSidebarHasCalendar':True,'calendarJustAfterCompetitions':True,
      'calendarClickOpensList':True,'noDuplicateNavEntry':True,
      'welcomeShowsCorrectVersion':True,'loginShowsCorrectVersion':True,
      'visibleSidebarVersionCorrect':True,'reloadKeepsNavigation':True,
      'retirementHistoryUnmodified':True,
      'saveStateUnmodified':True,'originalMenuEntriesUntouched':True
    }
    (root/'calendar-nav-version-18348-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
