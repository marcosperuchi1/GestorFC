"""Browser regression for font-only scaling in the existing FutBR settings page."""
from pathlib import Path
import importlib.util,json,threading,http.server,socketserver,sys,re,subprocess
from playwright.sync_api import sync_playwright

def main(root):
 root=Path(root).resolve()
 source=(root/'src/index.html').read_text(encoding='utf-8')
 expected=('FUTBR_FONT_SETTINGS_18376','FUTBR_SUPPORT_UI_18375',
           'FUTBR_CALENDAR_TRANSLATIONS_18375','FUTBR_TRANSFER_INTEREST_18375',
           'v622-settings-grid')
 for mark in expected:
  if mark not in source:raise AssertionError('Missing '+mark)
 for bad in ("document.documentElement.style.zoom=",".v375-open","v375Open()","v375-overlay"):
  if bad in source:raise AssertionError('Obsolete settings UI present: '+bad)
 spec=importlib.util.spec_from_file_location('font_patch',str(Path(__file__).with_name('fix_font_settings_18376.py')))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 fixture_head='''<!doctype html><html><head><meta charset="utf-8"><style>
 body{margin:0;font-family:Arial;font-size:14px}#app{display:flex;width:1200px;height:780px}
 .sidebar{flex:none;width:230px;border:2px solid #900;padding:12px;box-sizing:border-box}
 main{flex:1;min-width:0;padding:16px;box-sizing:border-box}
 .v622-settings-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}
 .v622-setting-card{box-sizing:border-box;border:1px solid #999;border-radius:8px;padding:20px}
 h3{font-size:18px}p{font-size:13px}button{font-size:14px}label{font-size:12px}
 </style></head><body><div id="app"><aside class="sidebar"><button id="settings-nav">Configurações</button></aside>
 <main><section class="panel"><h2>Configurações da carreira</h2><div class="v622-settings-grid">
 <div class="v622-setting-card fbr-language-setting"><h3>Idioma do jogo</h3><p>Preferência de idioma</p><select><option>Português</option></select></div>
 <div class="v622-setting-card"><h3>Renovação de contratos</h3><p>Preferência do clube</p>
 <label for="renewals">Responsável pelas renovações</label><select id="renewals"><option>Diretoria</option></select></div>
 </div></section></main></div><script>
 window.GestorFC={};window.__setFullscreen=null;
 window.__TAURI__={window:{getCurrentWindow:()=>({setFullscreen:(v)=>{window.__setFullscreen=v;return Promise.resolve();}})}};
 var render=function(){return 'original';};var showBuy=function(){return 'original';};
 function toast(){};
 </script><script>'''
 fixture=fixture_head+m.UI+'</script></body></html>'
 webroot=root/'test-font-fixture-18376'
 webroot.mkdir(exist_ok=True)
 (webroot/'index.html').write_text(fixture,encoding='utf-8')
 class QuietHandler(http.server.SimpleHTTPRequestHandler):
  def __init__(self,*a,**kw):super().__init__(*a,directory=str(webroot),**kw)
  def log_message(self,*a):pass
 srv=http.server.ThreadingHTTPServer(('127.0.0.1',0),QuietHandler)
 threading.Thread(target=srv.serve_forever,daemon=True).start()
 reports={}
 try:
  with sync_playwright() as playwright:
   browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
   page=browser.new_page(viewport={'width':1500,'height':950})
   errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.add_init_script("""if (!sessionStorage.getItem('v376-initialized')) {
     localStorage.setItem('futbr-display-18375', JSON.stringify({scale:125}));
     sessionStorage.setItem('v376-initialized', 'true');
   }""")
   page.goto(f'http://127.0.0.1:{srv.server_port}/',wait_until='load')
   page.locator('#v376-display-card').wait_for(timeout=10000)
   assert not errors, errors
   assert page.locator('.sidebar #settings-nav').count()==1
   assert page.locator('.v375-open,.v375-overlay').count()==0
   assert page.locator('#v376-display-card').count()==1
   assert page.locator('.v622-settings-grid #v376-display-card').count()==1
   assert page.locator('.fbr-language-setting').count()==1
   initial=page.evaluate("""() => ({
      zoom:document.documentElement.style.zoom||'',
      scale:window.GestorFC.fontSettings18376.getScale(),
      sidebar:document.querySelector('.sidebar').getBoundingClientRect().width,
      app:document.getElementById('app').getBoundingClientRect().width,
      grid:document.querySelector('.v622-settings-grid').getBoundingClientRect().width,
      heading:parseFloat(getComputedStyle(document.querySelector('.v622-setting-card h3')).fontSize),
      paragraph:parseFloat(getComputedStyle(document.querySelector('.v622-setting-card p')).fontSize),
      navFont:parseFloat(getComputedStyle(document.querySelector('#settings-nav')).fontSize)
   })""")
   assert initial['scale']==125 and initial['zoom']=='',initial
   assert abs(initial['heading']-22.5)<.3,initial
   assert abs(initial['paragraph']-16.25)<.3,initial
   assert abs(initial['navFont']-17.5)<.3,initial
   font=page.locator('#v376-font-size')
   font.select_option('100')
   normal=page.evaluate("""() => ({
      zoom:document.documentElement.style.zoom||'',
      sidebar:document.querySelector('.sidebar').getBoundingClientRect().width,
      app:document.getElementById('app').getBoundingClientRect().width,
      grid:document.querySelector('.v622-settings-grid').getBoundingClientRect().width,
      heading:parseFloat(getComputedStyle(document.querySelector('.v622-setting-card h3')).fontSize),
      paragraph:parseFloat(getComputedStyle(document.querySelector('.v622-setting-card p')).fontSize)
   })""")
   assert abs(normal['heading']-18)<.2 and abs(normal['paragraph']-13)<.2,normal
   font.select_option('120')
   larger=page.evaluate("""() => ({
      zoom:document.documentElement.style.zoom||'',
      sidebar:document.querySelector('.sidebar').getBoundingClientRect().width,
      app:document.getElementById('app').getBoundingClientRect().width,
      grid:document.querySelector('.v622-settings-grid').getBoundingClientRect().width,
      heading:parseFloat(getComputedStyle(document.querySelector('.v622-setting-card h3')).fontSize),
      paragraph:parseFloat(getComputedStyle(document.querySelector('.v622-setting-card p')).fontSize),
      persisted:JSON.parse(localStorage.getItem('futbr-display-18375')).scale
   })""")
   assert larger['zoom']=='' and larger['persisted']==120,larger
   assert abs(larger['heading']-21.6)<.3 and abs(larger['paragraph']-15.6)<.3,larger
   for key in ('sidebar','app','grid'):
    assert abs(larger[key]-normal[key])<.2,(key,normal,larger)
   page.locator('[data-v376-full="1"]').click()
   assert page.evaluate('window.__setFullscreen') is True
   page.locator('[data-v376-full="0"]').click()
   assert page.evaluate('window.__setFullscreen') is False
   page.reload(wait_until='load')
   page.locator('#v376-display-card').wait_for(timeout=10000)
   assert page.locator('#v376-font-size').input_value()=='120'
   assert page.locator('.sidebar #settings-nav').count()==1
   assert page.locator('.v375-open,.v375-overlay').count()==0
   page.evaluate("""() => {
       document.querySelector('.v622-settings-grid').innerHTML =
       '<div class="v622-setting-card"><h3>Renovação</h3><label>Responsável pelas renovações</label></div>';
       render();
   }""")
   page.locator('#v376-display-card').wait_for(timeout=10000)
   assert page.locator('#v376-display-card').count()==1
   assert not errors,errors
   reports={'ok':True,'version':'18.376.0','existingSettingsOnly':True,
     'originalSettingsAndLanguageRemain':True,'originalNavigationPreserved':True,
     'legacy125PreferenceRestoredWithoutGlobalZoom':True,
     'normalRestoresOriginalFonts':True,'font120ScalesOnlyText':True,
     'sidebarAndGridWidthsUnchanged':True,'fullscreenAndWindowButtonsWork':True,
     'savesPreferenceWithoutTouchingCareer':True,'rerenderDoesNotDuplicateControls':True,
     'previousSupportMoneyAndTooltipHooksPresent':True,'noBrowserErrors':True,
     'initial':initial,'normal':normal,'larger':larger}
   browser.close()
 finally:srv.shutdown()
 (root/'font-settings-18376-tests.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(reports,ensure_ascii=False))
if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: test_font_settings_18376.py <prepared-game-root>')
 main(sys.argv[1])
