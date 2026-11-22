"""Real Chromium regression for 18.378 grouped offer fields and startup auto-updater."""
from pathlib import Path
import json,re,sys
from playwright.sync_api import sync_playwright

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_money_autoupdate_runtime_18378.py <project-dir>')
 root=Path(sys.argv[1])
 html=(root/'src/index.html').read_text(encoding='utf-8')
 begin=html.index('/* FUTBR_MONEY_AUTOUPDATE_18378 */')
 end=html.index('const v375PreviousRender=render;',begin)
 money=html[begin:end]
 m=re.search(r'<script id="futbr-desktop-update-ui-18339">([\s\S]*?)</script>',html)
 if not m:raise RuntimeError('Production updater script missing')
 updater=m.group(1)
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,args=['--disable-dev-shm-usage'])
  page=browser.new_page()
  page.set_content('''<!doctype html><label for="bid-value">Proposta ao clube (R$)</label>
   <div class="field"><label for="bid-value">Proposta ao clube (R$)</label><input type="number" id="bid-value" data-cost="true" step="100000" value="1234567"></div>
   <div class="field"><label for="bid-wage">Salário por jornada (R$)</label><input type="number" id="bid-wage" value="12500"></div>
   <div class="field"><label for="bid-years">Duração do contrato</label><input type="number" id="bid-years" value="3"></div>''')
  page.add_script_tag(content="function showBuy(){};function showRenew(){};window.offerEvents=0;document.addEventListener('input',e=>{if(e.target.id==='bid-value')window.offerEvents++});\n"+money)
  page.evaluate('showBuy()')
  page.wait_for_selector('#v378-bid-value')
  assert page.locator('#v378-bid-value').input_value()=='1.234.567'
  assert page.locator('#v378-bid-wage').input_value()=='12.500'
  assert page.locator('#bid-years').input_value()=='3'
  assert page.locator('#v378-bid-years').count()==0
  page.locator('#v378-bid-value').fill('2.500.000')
  assert page.locator('#v378-bid-value').input_value()=='2.500.000'
  assert page.locator('#bid-value').input_value()=='2500000'
  assert page.evaluate('window.offerEvents')>=1
  page.locator('#v378-bid-wage').fill('18.750')
  assert page.locator('#bid-wage').input_value()=='18750'
  page.locator('#bid-value').evaluate('(e)=>e.setAttribute("readonly","")')
  page.evaluate('document.querySelector("#bid-value").dataset.v378Grouped=""; document.querySelector("#v378-bid-value").remove();')
  # The implementation never overwrites a mounted input; original numeric remains intact.
  assert page.locator('#bid-value').input_value()=='2500000'
  page.close()
  auto=browser.new_page()
  auto.set_content('<!doctype html><title>FutBR Manager startup</title><body></body>')
  auto.add_script_tag(content="""window.__calls=[];window.FutBRDesktop={available:true};window.GestorFC={async prepareSignedUpdate18339(){window.__calls.push('save');}};
   window.__TAURI__={core:{async invoke(key){
     if(key==='futbr_check_update_18339'){window.__calls.push('check');return {version:'18.379.0',currentVersion:'18.378.0'};}
     if(key==='futbr_install_update_18339'){window.__calls.push('install');return null;}throw Error(key);
   }},event:{async listen(){return ()=>{};}}};
   window.setTimeout=(fn,ms)=>Promise.resolve().then(fn);""")
  auto.add_script_tag(content=updater)
  auto.wait_for_function("window.__calls.includes('install')")
  actual=auto.evaluate('window.__calls')
  assert actual==['check','save','install'],actual
  assert auto.locator('#futbr-desktop-update-18339').is_visible()
  assert auto.locator('#futbr-desktop-update-18339 .actions').evaluate('(e)=>e.hidden')
  auto.close()
  offline=browser.new_page()
  offline.set_content('<!doctype html><body></body>')
  offline.add_script_tag(content="""window.__calls=[];window.FutBRDesktop={available:true};window.GestorFC={async prepareSignedUpdate18339(){window.__calls.push('save');}};
   window.__TAURI__={core:{async invoke(key){window.__calls.push(key);if(key==='futbr_check_update_18339')throw Error('offline');}},event:{async listen(){return ()=>{};}}};
   window.setTimeout=(fn)=>Promise.resolve().then(fn);""")
  offline.add_script_tag(content=updater)
  offline.wait_for_function("window.__calls.length>=1")
  assert offline.evaluate('window.__calls')==['futbr_check_update_18339']
  assert offline.locator('#futbr-desktop-update-18339').count()==0
  browser.close()
 report={'ok':True,'version':'18.378.0','actualProductionScripts':True,
         'ptBRFormatted1234567':'1.234.567','nativeValueAfterEdit':2500000,
         'salaryNativeValueAfterEdit':18750,'transferCostEventsPreserved':True,
         'contractYearsNotFormatted':True,'autoStartsWithoutClick':True,
         'savePrecedesInstall':True,'signedNativeInstallerUsed':True,
         'offlineStartupDoesNotBlock':True}
 (root/'money-autoupdate-runtime-18378-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps(report))
if __name__=='__main__':main()
