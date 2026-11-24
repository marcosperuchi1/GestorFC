"""Isolated smoke test for FutBR 18.386, requiring no Windows installer.

Runs the SAME UI and gzip decoder functions from the shipping patch, in real
Chromium with artificially slow local metadata and player base.
"""
from pathlib import Path
import base64,gzip,importlib.util,json,subprocess,sys
from playwright.sync_api import sync_playwright
modulepath=Path(__file__).with_name('apply_nonblocking_startup_18386.py')
spec=importlib.util.spec_from_file_location('futbr186',modulepath)
patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
js=patch.JS_ROSTER+'\n'+patch.JS_SHELL.replace(
 " version:VERSION, // version assigned in the patch only at release time",
 " version:'18.386.0',")
jscheck=subprocess.run(['node','--check','-'],input=js,text=True,capture_output=True,timeout=30)
if jscheck.returncode:raise RuntimeError('Production JS syntax '+jscheck.stderr)
mocks=r"""
window.GestorFC={};
let v548Session={serverValidated:true,userId:'fixture',username:'fixture@example.invalid'};
const esc=x=>String(x).replace(/[&<>"']/g,'');
const v548PlanLabel=()=>'Premium';
const wait=()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve}};
const meta=wait(),roster=wait();
let metaCalls=0,rosterCalls=0,welcomeCalls=0;
function v18385LocalOnce(){metaCalls++;return meta.promise}
function v310StartRosterLoad(){rosterCalls++;return roster.promise}
function renderWelcome(){welcomeCalls++;document.getElementById('app').innerHTML='<section id="full-menu">Carregar carreira</section>'}
"""
source="Brasil, Premier League, Libertadores, jogadores: \u00e1 \u00e9 \u00ed \u00f3 \u00fa\n"*28000
encoded=base64.b64encode(gzip.compress(source.encode('utf-8'),6,mtime=0)).decode('ascii')
assert len(source)>1000000 and len(encoded)>1024
result={}
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
 page=browser.new_page()
 page.set_content('<!doctype html><html><head></head><body style="margin:0"><div id="app"><form id="login">Login</form></div></body></html>')
 page.add_script_tag(content=mocks+'\n'+js+'\nwindow.__started=v18386StartEntry()')
 page.wait_for_selector('#v18386-startup',timeout=5000)
 page.wait_for_function('metaCalls===1&&rosterCalls===1',timeout=5000)
 assert page.locator('#login').count()==0
 assert page.locator('#full-menu').count()==0
 result['firstPaintBeforeBothSlowLoads']=True
 page.evaluate('meta.resolve(null)')
 page.wait_for_timeout(40)
 assert page.locator('#full-menu').count()==0
 page.evaluate('roster.resolve("good")')
 page.wait_for_selector('#full-menu',timeout=5000)
 assert page.evaluate('welcomeCalls')==1
 result['gameGatedUntilAllDataReady']=True
 page.evaluate("""data=>{window.__packed=data;window.FutBRDesktop={
 loadPlayerBaseCompressed:()=>Promise.resolve(window.__packed),
 loadPlayerBase:()=>Promise.resolve('FALLBACK_OK')
 }}""",encoded)
 assert page.evaluate('v18386LoadCompressedRoster()')==source
 result['unicodeGzipRoundtrip']=True
 page.evaluate("""() => {window.FutBRDesktop.loadPlayerBaseCompressed=()=>Promise.reject(Error('unsupported'))}""")
 assert page.evaluate('v18386LoadCompressedRoster()')=='FALLBACK_OK'
 result['legacyLocalFallback']=True
 page.evaluate('v548Session=null')
 assert page.evaluate('v18386StartEntry().then(()=>false,()=>true)')
 result['authorizationGateStillRequired']=True
 page.close();browser.close()
print(json.dumps({'ok':True,'version':'18.386.0',**result,'scenario':'isolated Chromium frontend only'},ensure_ascii=False))
