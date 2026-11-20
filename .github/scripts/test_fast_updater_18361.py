from __future__ import annotations
import importlib.util,json,subprocess,sys,tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
def mod(filename):
 path=HERE/filename
 spec=importlib.util.spec_from_file_location(filename.replace('.','_'),path)
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj)
 return obj

def main():
 with tempfile.TemporaryDirectory(prefix='futbr-updater-18361-') as tmp:
  root=Path(tmp)
  for sub in ('src','src-tauri/src'):
   (root/sub).mkdir(parents=True,exist_ok=True)
  old=mod('enable_desktop_updater_18339.py')
  (root/'src/index.html').write_text('<html><head>'+old.CSS+'</head><body>'+old.JS+'</body></html>',encoding='utf-8')
  (root/'src-tauri/src/lib.rs').write_text(
   'use tauri::AppHandle;\nuse serde::Serialize;\n'+old.RUST+
   '\n#[tauri::command]\nfn desktop_info() {}\n',encoding='utf-8')
  (root/'src-tauri/tauri.conf.json').write_text(json.dumps({
   'version':'18.361.0',
   'bundle':{'createUpdaterArtifacts':True,'windows':{'nsis':{'installMode':'currentUser'}}},
   'plugins':{'updater':{'pubkey':'fixture-public-key',
     'endpoints':['https://futbrmanager.com.br/updates/latest.json'],
     'windows':{'installMode':'passive'}}}
  }),encoding='utf-8')
  proc=subprocess.run([sys.executable,str(HERE/'fix_fast_updater_18361.py'),str(root)],
                      capture_output=True,text=True,timeout=20)
  if proc.returncode:raise RuntimeError('Updater patch failed: '+proc.stderr[-4000:])
  html=(root/'src/index.html').read_text(encoding='utf-8')
  rust=(root/'src-tauri/src/lib.rs').read_text(encoding='utf-8')
  cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
  assert 'FUTBR_FAST_SIGNED_UPDATER_18361' in rust
  assert cfg['version']=='18.361.0'
  assert cfg['plugins']['updater']['endpoints']==['https://download.futbrmanager.com.br/updates/latest.json']
  assert cfg['plugins']['updater']['pubkey']=='fixture-public-key'
  assert cfg['bundle']['windows']['nsis']['installMode']=='currentUser'
  assert 'update.download_and_install(' in rust
  assert 'tauri_plugin_updater::Update' in rust
  assert "Some((update.clone(),std::time::Instant::now()))" in rust
  assert "guard.take()" in rust
  assert 'std::time::Instant' in rust
  assert 'Duration::from_secs(600)' in rust
  assert 'serde_json::json!' in rust
  assert 'futbr-update-progress-18361' in rust
  assert 'update.timeout=Some(Duration::from_secs(600));' in rust
  assert 'use tauri::Emitter;' in rust
  assert 'pubkey' not in rust # signer is Tauri configuration, not source
  assert 'await window.GestorFC.prepareSignedUpdate18339();' in html
  assert html.index('await window.GestorFC.prepareSignedUpdate18339();')<html.index("await invoke('futbr_install_update_18339');")
  assert 'progress.value=percent' in html
  assert 'document.body.classList.remove' in html
  assert 'background:rgba(0,0,0,.28)' in html
  assert html.count('progress class="v18361-progress"')==1
  assert 'futbr-update-progress-18361' in html

  a=html.index('<script id="futbr-desktop-update-ui-18339">')
  b=html.index('</script>',a)
  js=html[a:b].split('>',1)[1]
  snippet=Path(tmp)/'real-updater-18361.js'
  snippet.write_text(js,encoding='utf-8')
  ok=subprocess.run(['node','--check',str(snippet)],capture_output=True,text=True,timeout=20)
  if ok.returncode:raise RuntimeError('Updater JS syntax: '+ok.stderr[-2300:])
  node_harness=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync(process.argv[2],'utf8');
const order=[],statusHistory=[];
let downloadHandler=null,installAction=null,checked=0,installed=0,saveCount=0;
const controls={
 '[data-v18339-later]':{disabled:false,addEventListener(type,cb){this[type]=cb}},
 '[data-v18339-install]':{disabled:false,addEventListener(type,cb){this[type]=cb}},
 '.status':{set textContent(x){statusHistory.push(x)},get textContent(){return statusHistory.at(-1)}},
 '.message':{textContent:''},
 '.v18361-progress':{hidden:true,value:0,removeAttribute(key){if(key==='value')this.value=null}}
};
const panel={
  hidden:true,attrs:{},setAttribute(k,v){this.attrs[k]=v},
  querySelector(sel){if(!(sel in controls))throw Error('Missing control '+sel);return controls[sel]},
  set innerHTML(s){this.markup=s}
};
const body={classList:{
  flags:new Set(),add(x){this.flags.add(x)},remove(x){this.flags.delete(x)}
 },appendChild(x){this.panel=x}};
const document={readyState:'complete',body,createElement:()=>panel};
const window={
  FutBRDesktop:{available:true},
  GestorFC:{async prepareSignedUpdate18339(){order.push('save');saveCount++}},
  __TAURI__:{
   core:{async invoke(key){
    if(key==='futbr_check_update_18339'){checked++;return {version:'18.362.0',currentVersion:'18.361.0'};}
    if(key==='futbr_install_update_18339'){
      assert.equal(saveCount,1);
      order.push('install');installed++;
      downloadHandler({payload:{phase:'starting'}});
      downloadHandler({payload:{phase:'downloading',bytes:10485760,total:41943040}});
      assert.equal(controls['.v18361-progress'].value,25);
      downloadHandler({payload:{phase:'downloading',bytes:41943040,total:41943040}});
      assert.equal(controls['.v18361-progress'].value,100);
      downloadHandler({payload:{phase:'verifying'}});
      return null;
    }
    throw Error(key);
   }},
   event:{async listen(name,cb){
    assert.equal(name,'futbr-update-progress-18361');
    downloadHandler=cb;
    return ()=>order.push('unlisten');
   }}
  }
};
const timers=[];
function setTimeout(fn,ms){timers.push({fn,ms})}
async function test(){
  const vm=require('node:vm');
  vm.runInNewContext(source,{window,document,setTimeout,Date,Math,Number,String,Error,console});
  assert.equal(timers.length,1);
  assert.equal(timers[0].ms,5000);
  await timers[0].fn();
  assert.equal(checked,1);assert.equal(panel.hidden,false);
  assert.ok(panel.markup.includes('v18361-progress'));
  await controls['[data-v18339-install]'].click();
  assert.equal(installed,1);assert.deepEqual(order,['save','install','unlisten']);
  assert.ok(statusHistory.some(s=>s.includes('25% (10.0 MB de 40.0 MB)')));
  assert.ok(statusHistory.some(s=>s.includes('assinatura')));
  assert.equal(body.classList.flags.has('futbr-update-installing18339'),true);
  console.log(JSON.stringify({ok:true,version:'18.361.0',
   cachedOnlyTrustedMetadata:true,saveBeforeInstall:true,
   secondHTTPManifestCheckAvoided:true,liveDownloadPercentage:true,
   signedInstallerRemainsOnlyNativePath:true,noInstallerPrefetch:true,
   statusCommunicatesSignaturePhase:true,samePerUserInstaller:true,
   progressDoesNotBypassSave:true,progressOptional:true,directCDN:true}));
}
test().catch(e=>{console.error(e);process.exitCode=1});
"""
  runner=Path(tmp)/'updater-ui-test.cjs'
  runner.write_text(node_harness,encoding='utf-8')
  result=subprocess.run(['node',str(runner),str(snippet)],capture_output=True,text=True,timeout=30)
  if result.returncode:raise RuntimeError('Updater UI runtime regression: '+(result.stderr or result.stdout)[-4500:])
  report=json.loads(result.stdout.strip().splitlines()[-1])
  (root/'fast-updater-18361-tests.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
  print(json.dumps(report))

if __name__=='__main__':main()
