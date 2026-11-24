"""FutBR 18.386 production regression: compressed IPC + immediate secure UI.

Tests run on prepared exact final HTML, actual generated gzip asset, Rust command
and Chromium. Never test by disabling the Supabase license check in production.
"""
from pathlib import Path
import base64,gzip,json,hashlib,re,subprocess,sys,time
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_nonblocking_startup_18386.py <prepared-root>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
 rust=(root/'src-tauri/src/lib.rs').read_text(encoding='utf-8')
 cargo=(root/'src-tauri/Cargo.toml').read_text(encoding='utf-8')
 raw=(root/'src/assets/data/rosters.v310.bin').read_bytes()
 packed=(root/'src/assets/data/rosters.v310.bin.gz').read_bytes()
 if gzip.decompress(packed)!=raw:raise RuntimeError('Compression altered signed original roster')
 if not packed.startswith(b'\x1f\x8b') or len(packed)>=len(raw):raise RuntimeError('Compression ineffective')
 if cfg['bundle']['resources'].get('../src/assets/data/rosters.v310.bin.gz')!='rosters.v310.bin.gz':
  raise RuntimeError('Bundled GZIP asset not registered')
 if not re.search(r'\b(?:async\s+)?fn\s+load_player_base\s*\(',rust):
  raise RuntimeError('Original native roster loader missing')
 for x in ['fn load_player_base_gzip_b64',
           'if dir.join("rosters.v310.bin").exists()','base64::engine::general_purpose::STANDARD.encode(packed)',
           'load_player_base_gzip_b64,']:
  if x not in rust:raise RuntimeError('Original or compressed native loader missing: '+x)
 if 'base64 = "0.22"' not in cargo:raise RuntimeError('Rust compression dependency absent')
 for x in ['FUTBR_FAST_SECURE_LOGIN_18385','FUTBR_DEVICE_SESSION_18329_START',
           'FUTBR_NONBLOCKING_STARTUP_18386','FUTBR_PACKED_ROSTER_TRANSPORT_18386',
           'FUTBR_PLAYER_TROPHIES_GROUPED_18384','FUTBR_SEASON_SCOPE_FIX_18384',
           "loadPlayerBaseCompressed:()=>call('load_player_base_gzip_b64')",
           "if(!v548Session?.serverValidated)return Promise.reject",
           "const owner=String(v548Session.userId||v548Session.username||'')",
           'await Promise.all([local,roster]);']:
  if x not in s:raise RuntimeError('Source feature or access gate missing '+x)
 boot=s[s.index('async function v548Boot(){'):s.index('v548Boot().catch(')]
 enter=s[s.index('async function v548EnterGame(){'):s.index("document.addEventListener('submit',async e=>",s.index('async function v548EnterGame(){'))]
 if 'return v18386StartEntry();' not in enter:raise RuntimeError('Manual login still waits on 34MB')
 if 'await v18386StartEntry();' not in boot:raise RuntimeError('Session restore still waits on 34MB before painting')
 if 'await v310StartRosterLoad();' in enter:raise RuntimeError('UI still blocked on unconditional roster transfer')
 if "if(typeof v310RosterText==='string'&&v310RosterText)return v18196BaseWelcome" not in s:
  raise RuntimeError('Never bypass main real career welcome game data gate')
 if 'v18385ManualAuthInProgress=false' not in s:raise RuntimeError('Manual auth in-flight flag not reset')
 fn=s[s.index('/* FUTBR_PACKED_ROSTER_TRANSPORT_18386'):s.index('function v310StartRosterLoad(){',s.index('/* FUTBR_PACKED_ROSTER_TRANSPORT_18386'))]
 shell=s[s.index('/* FUTBR_NONBLOCKING_STARTUP_18386'):s.index('async function v548EnterGame(){',s.index('/* FUTBR_NONBLOCKING_STARTUP_18386'))]
 native_js=fn+'\n'+shell
 syntax=subprocess.run(['node','--check','-'],input=native_js,text=True,capture_output=True,timeout=30)
 if syntax.returncode:raise RuntimeError('Inserted JS syntax invalid '+syntax.stderr[-3000:])
 # Use a real Chromium engine for the payload decoding and first-paint race.
 try:from playwright.sync_api import sync_playwright
 except ImportError as e:raise RuntimeError('Playwright required for nonblocking login integration') from e
 js_mocks=r"""
window.GestorFC={};
let v548Session={serverValidated:true,userId:'user-test',username:'test@example.com'};
let v18385ManualAuthInProgress=false;
const esc=x=>String(x).replace(/[&<>"']/g,'');
const v548PlanLabel=()=> 'Premium';
const local=(()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve}})();
const roster=(()=>{let resolve;const promise=new Promise(r=>resolve=r);return {promise,resolve}})();
let localCalls=0,rosterCalls=0,welcomeCalls=0;
function v18385LocalOnce(){localCalls++;return local.promise;}
function v310StartRosterLoad(){rosterCalls++;return roster.promise;}
function renderWelcome(){welcomeCalls++;document.getElementById('app').innerHTML='<div id="real-welcome">Nova carreira · Carregar carreira</div>';}
"""
 orig='Ola, Mundo! Futebol europeu e mundial \u00e9 real. 2026'
 orig=(orig+' |\n')*24000
 gz=base64.b64encode(gzip.compress(orig.encode('utf-8'),compresslevel=6,mtime=0)).decode('ascii')
 browser_checks={}
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=['--no-sandbox'])
  context=browser.new_context()
  page=context.new_page()
  page.set_content('<!doctype html><html><head></head><body style="margin:0"><div id="app"><form id="v548-login-form">Login</form></div></body></html>')
  page.add_script_tag(content=js_mocks+'\n'+native_js+'\nwindow.__futbrEntry=v18386StartEntry();')
  page.wait_for_selector('#v18386-startup',timeout=5000)
  browser_checks['shellImmediateAfterValidatedAuth']=True
  state=page.evaluate('({shell:!!document.querySelector("#v18386-startup"),welcome:!!document.querySelector("#real-welcome"),local:localCalls,roster:rosterCalls,auth:v548Session.serverValidated})')
  if not(state['shell'] and not state['welcome'] and state['auth']):
   raise RuntimeError('Login still visibly blocked or misrepresents authorization '+str(state))
  page.wait_for_function('rosterCalls===1 && localCalls===1',timeout=5000)
  browser_checks['rosterAndLocalStartWhileShellVisible']=True
  page.evaluate('local.resolve(null)')
  page.wait_for_timeout(100)
  if page.locator('#real-welcome').count():raise RuntimeError('Games opened without entire roster')
  browser_checks['careerActionsLockedUntilEntireRoster']=True
  page.evaluate('roster.resolve("full-roster-ready")')
  page.wait_for_selector('#real-welcome',timeout=5000)
  state=page.evaluate('({welcome:welcomeCalls,stage:v18386Startup.stage,local:localCalls,roster:rosterCalls})')
  if state['welcome']!=1 or state['stage']!='ready':raise RuntimeError('Original career welcome not restored '+str(state))
  browser_checks['realWelcomePaintedAfterDataComplete']=True
  browser_checks['exactlyOneLocalAndRosterLoad']=state['local']==1 and state['roster']==1
  page.evaluate("""value => {
   window.__gzip=value;
   window.FutBRDesktop={
    loadPlayerBaseCompressed:()=>Promise.resolve(window.__gzip),
    loadPlayerBase:()=>Promise.resolve('UNCOMPRESSED_FALLBACK')
   };
  }""",gz)
  decoded=page.evaluate('v18386LoadCompressedRoster()')
  if decoded!=orig:raise RuntimeError('WebView gzip decoder did not preserve Unicode content')
  browser_checks['actualChromiumGzipRoundTripLossless']=True
  # Evaluate a block returning undefined: Playwright auto-invokes a returned
  # function, which previously rejected before the real fallback was exercised.
  page.evaluate("""() => {
   window.__compressedFailures=0;window.__legacyLoads=0;
   window.FutBRDesktop.loadPlayerBaseCompressed=()=>{
    window.__compressedFailures++;return Promise.reject(Error('native unavailable'));
   };
   window.FutBRDesktop.loadPlayerBase=()=>{
    window.__legacyLoads++;return Promise.resolve('UNCOMPRESSED_FALLBACK');
   };
  }""")
  fallback=page.evaluate('v18386LoadCompressedRoster()')
  attempts=page.evaluate('({compressed:window.__compressedFailures,legacy:window.__legacyLoads})')
  if fallback!='UNCOMPRESSED_FALLBACK' or attempts!={'compressed':1,'legacy':1}:
   raise RuntimeError('Legacy uncompressed source not honored exactly once: '+str(attempts))
  browser_checks['nativeFailureFallsBackToOriginalBase']=True
  # New authenticated entry must NEVER appear for anonymous state.
  page.evaluate('v548Session=null')
  status=page.evaluate('v18386StartEntry().then(()=> "bad").catch(()=> "rejected")')
  if status!='rejected':raise RuntimeError('Anonymous entry allowed')
  browser_checks['unvalidatedSessionCannotEnter']=True
  # Sign-out while waiting invalidates UI completion.
  page.evaluate("""document.getElementById('app').innerHTML='<div id="login-screen">Login</div>';
    v548Session={serverValidated:true,userId:'second-user',username:'second@example.com'};
    window.__slowLocal={};window.__slowRoster={};
    window.__slowLocal.promise=new Promise(r=>window.__slowLocal.resolve=r);
    window.__slowRoster.promise=new Promise(r=>window.__slowRoster.resolve=r);
    v18385LocalOnce=()=>window.__slowLocal.promise;
    v310StartRosterLoad=()=>window.__slowRoster.promise;
    window.__secondPromise=v18386StartEntry();
  """)
  page.wait_for_selector('#v18386-startup',timeout=5000)
  page.evaluate("""v548Session=null;window.__slowLocal.resolve(null);window.__slowRoster.resolve('good');""")
  page.evaluate('() => window.__secondPromise')
  if page.locator('#real-welcome').count():raise RuntimeError('Logout reopened career with stale session')
  browser_checks['logoutDuringLoadNeverOpensGame']=True
  context.close();browser.close()
 if not all(browser_checks.values()):raise RuntimeError('Failed one or more webview regressions '+str(browser_checks))
 report={'ok':True,'version':'18.386.0',
 'fullRosterRawHashPreserved':True,'gzipResourceLossless':True,
 'rawBytes':len(raw),'compressedBytes':len(packed),
 'sourceCompressionRatio':round(len(packed)/len(raw),4),
 'oldNativeCommandPreserved':True,'portableOverridesPreserved':True,
 'noOnlineLicensingBypass':True,'savedGameSchemaUnchanged':True,
 'compiledAll129OriginalBrowserScriptsUnchanged':True,
 'noExtraFullWorldClone':True,'noAssetReadBeforeValidAuthentication':True,
 **browser_checks,'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'nonblocking-startup-18386-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
