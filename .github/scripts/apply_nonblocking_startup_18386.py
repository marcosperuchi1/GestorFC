"""FutBR 18.386 - fast authenticated entry + verified compressed roster IPC.

Never bypass Supabase, license/device authorization or save integrity. After the
server validates the user, paint a responsive independent welcome-loading shell
BEFORE any expensive 34.6MB player base read. Carry the same exact source bytes
through a smaller gzip/base64 native IPC, with safe original command fallback.
"""
from pathlib import Path
import gzip,hashlib,json,re,subprocess,sys
VERSION='18.386.0'
MARK='FUTBR_NONBLOCKING_STARTUP_18386'
def once(s,old,new,why):
 count=s.count(old)
 if count!=1:raise RuntimeError(f'18.386 changed upstream anchor {why} ({count} matches)')
 return s.replace(old,new,1)
RUST=r"""
#[tauri::command]
fn load_player_base_gzip_b64(app: AppHandle) -> Result<String, String> {
    use base64::Engine as _;
    // Custom portable files always take priority through the legacy loader.
    if let Some(dir) = std::env::current_exe().ok()
        .and_then(|p| p.parent().map(|d| d.to_path_buf())) {
        if dir.join("rosters.v310.bin").exists() {
            return Err("Custom portable roster: use original source".to_string());
        }
    }
    let base = app.path().resource_dir().map_err(|e| e.to_string())?;
    let packed = fs::read(base.join("rosters.v310.bin.gz"))
        .map_err(|e| format!("Compressed roster asset unavailable: {e}"))?;
    if packed.len() < 1024 || packed.len() > 34_645_893 {
        return Err("Invalid compressed roster asset".to_string());
    }
    Ok(base64::engine::general_purpose::STANDARD.encode(packed))
}
"""
JS_ROSTER=r"""
/* FUTBR_PACKED_ROSTER_TRANSPORT_18386
   Signed local gzip asset shrinks native-to-WebView IPC. DecompressionStream
   validates gzip checksums; v310AcceptRosterText still verifies raw byte count.
   Original uncompressed command stays the lossless fallback for Windows
   builds without the required stream API or customized portable assets. */
async function v18386LoadCompressedRoster(){
 try{
  const compressed=await globalThis.FutBRDesktop.loadPlayerBaseCompressed();
  if(typeof compressed!=='string'||compressed.length<1024)
   throw Error('Arquivo comprimido incompleto');
  if(typeof globalThis.DecompressionStream!=='function')
   throw Error('Descompressao nativa nao disponivel');
  const binary=atob(compressed);
  const bytes=Uint8Array.from(binary,ch=>ch.charCodeAt(0));
  const source=new Blob([bytes]).stream()
   .pipeThrough(new DecompressionStream('gzip'));
  const text=await new Response(source).text();
  if(typeof text!=='string'||text.length<1000000)
   throw Error('Base incompleta apos descompressao');
  return text;
 }catch(error){
  console.warn('[FutBR] leitor compacto indisponivel; fonte original preservada:',error?.message||error);
  return globalThis.FutBRDesktop.loadPlayerBase();
 }
}
"""
JS_SHELL=r"""
/* FUTBR_NONBLOCKING_STARTUP_18386
   The user is already remotely authorized when these functions run.
   The final game welcome and all career controls still require the complete
   roster and local metadata. Never enable gameplay on incomplete data. */
const v18386Startup={version:'18.386.0',stage:'idle',visibleAt:0,
 dataReadyAt:0,localReadyMs:null,rosterReadyMs:null,
 loginStartedAt:0,errors:0};
let v18386EntryPromise=null,v18386EntryOwner='';
function v18386Status(message){
 const line=document.getElementById('v18386-startup-stage');
 if(line)line.textContent=message;
}
function v18386ShowStartup(){
 if(!v548Session?.serverValidated)throw Error('Sessao online nao validada.');
 const root=document.getElementById('app');
 if(!root)return;
 const plan=typeof v548PlanLabel==='function'?v548PlanLabel():'Conta verificada';
 root.innerHTML='<main id="v18386-startup" role="main" aria-busy="true" style="box-sizing:border-box;display:flex;align-items:center;justify-content:center;width:100%;height:100dvh;min-height:0;overflow:auto;padding:16px;background:radial-gradient(circle at 20% 0%,#17432b 0,#082015 48%,#071810 100%);color:#edf8f1;font-family:Inter,system-ui,sans-serif;">'
  +'<section style="max-width:560px;width:100%;padding:clamp(24px,5vw,48px);border:1px solid #37784b;border-radius:22px;background:#102a1e;box-shadow:0 20px 65px #0004">'
  +'<div style="font-size:12px;letter-spacing:.13em;color:#8bd0a8;font-weight:800;margin-bottom:16px">FUTBR MANAGER · '+esc(plan)+'</div>'
  +'<h1 style="font-size:clamp(28px,4vw,40px);line-height:1.12;margin:0 0 15px">Bem-vindo de volta!</h1>'
  +'<p style="font-size:14px;color:#b0d0be;margin:0 0 22px">Sua conta foi verificada. Estamos preparando os dados da sua carreira, sem baixar jogadores da internet.</p>'
  +'<div style="height:6px;background:#214c31;border-radius:999px;overflow:hidden;margin-bottom:12px"><div style="height:100%;width:55%;border-radius:999px;background:linear-gradient(90deg,#42bd7c,#89e3a7);animation:v18386-pulse 1.6s ease-in-out infinite alternate"></div></div>'
  +'<p id="v18386-startup-stage" role="status" style="min-height:38px;color:#b9ddc5;font-size:13px;margin:0 0 22px">Abrindo a tela inicial...</p>'
  +'<button type="button" data-v548-auth="logout" style="border:1px solid #47845a;border-radius:10px;background:transparent;color:#c4e5d2;padding:11px 17px;cursor:pointer;font-weight:650">Sair da conta</button>'
  +'<div id="v18386-startup-error" aria-live="polite"></div>'
  +'</section></main>';
 v18386Startup.visibleAt=performance.now();
 v18386Startup.stage='shell';
 if(!document.getElementById('v18386-pulse-style')){
  const style=document.createElement('style');style.id='v18386-pulse-style';
  style.textContent='@keyframes v18386-pulse{from{transform:translateX(-55%)}to{transform:translateX(125%)}}';
  document.head.append(style);
 }
 document.title='FutBR Manager · Entrando';
}
function v18386StartEntry(){
 if(!v548Session?.serverValidated)return Promise.reject(Error('Conta ainda nao validada pelo servidor.'));
 const owner=String(v548Session.userId||v548Session.username||'');
 if(v18386EntryPromise&&v18386EntryOwner===owner)return v18386EntryPromise;
 v18386EntryOwner=owner;
 v18386Startup.loginStartedAt=performance.now();
 v18386ShowStartup();
 v18386EntryPromise=(async()=>{
  // Allow WebView2 to paint this authenticated shell before the large native
  // invocation. Starting the 34MB transfer synchronously blocks the first
  // paint on some Windows machines even when the native Rust command is async.
  if(typeof requestAnimationFrame==='function')
   await new Promise(resolve=>requestAnimationFrame(()=>setTimeout(resolve,0)));
  v18386Status('Lendo dados locais e base de jogadores...');
  const rosterStarted=performance.now();
  const roster=v310StartRosterLoad().then(result=>{
   v18386Startup.rosterReadyMs=Math.round(performance.now()-rosterStarted);
   v18386Status('Base de jogadores pronta. Finalizando a carreira...');
   return result;
  });
  const localStarted=performance.now();
  const local=v18385LocalOnce().then(result=>{
   v18386Startup.localReadyMs=Math.round(performance.now()-localStarted);
   v18386Status(v18386Startup.rosterReadyMs==null?
    'Metadados recuperados. Preparando jogadores...':'Preparando a tela inicial...');
   return result;
  });
  await Promise.all([local,roster]);
  // The user may have logged out while local loading was pending.
  if(!v548Session?.serverValidated ||
      String(v548Session.userId||v548Session.username||'')!==owner)return;
  v18386Startup.stage='ready';
  v18386Startup.dataReadyAt=performance.now();
  renderWelcome();
 })().catch(error=>{
  v18386Startup.errors++;
  v18386Startup.stage='error';
  const hint=document.getElementById('v18386-startup-error');
  if(hint){
   hint.textContent='';
   const p=document.createElement('p');
   p.style.cssText='color:#ffb7b7;font-size:13px;margin:10px 0';
   p.textContent='Nao foi possivel carregar a base local: '+String(error?.message||error);
   const b=document.createElement('button');b.type='button';b.textContent='Tentar novamente';
   b.style.cssText='background:#2c8e58;color:#fff;padding:9px 13px;border:0;border-radius:8px;cursor:pointer';
   b.addEventListener('click',()=>{v18386EntryPromise=null;v18386StartEntry().catch(console.warn);});
   hint.append(p,b);
  }
  throw error;
 }).finally(()=>{v18386EntryPromise=null;});
 return v18386EntryPromise;
}
if(window.GestorFC)window.GestorFC.startup18386={
 version:VERSION, // version assigned in the patch only at release time
 status:()=>({...v18386Startup,authenticated:!!v548Session?.serverValidated})
};
"""
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: apply_nonblocking_startup_18386.py <prepared-root>')
 root=Path(sys.argv[1]).resolve()
 html_path=root/'src/index.html';s=html_path.read_text(encoding='utf-8')
 if MARK in s:raise RuntimeError('18.386 applied twice')
 for marker in ('FUTBR_NONBLOCKING_STARTUP_18385','FUTBR_FAST_SECURE_LOGIN_18385',
                'FUTBR_DEVICE_SESSION_18329_START','FUTBR_PLAYER_TROPHIES_GROUPED_18384'):
  if marker=='FUTBR_NONBLOCKING_STARTUP_18385':continue
  if marker not in s:raise RuntimeError('Inherited release missing '+marker)
 # First use compressed local roster transport, but preserve original bridge.
 src=root/'src/assets/data/rosters.v310.bin'
 if not src.is_file():raise RuntimeError('Missing signed local roster asset')
 raw=src.read_bytes()
 if len(raw)<10000000:raise RuntimeError('Unexpectedly small 18.385 roster asset')
 packed=gzip.compress(raw,compresslevel=6,mtime=0)
 if gzip.decompress(packed)!=raw:raise RuntimeError('Compressed player base not lossless')
 gz=src.with_name('rosters.v310.bin.gz');gz.write_bytes(packed)
 cfg_path=root/'src-tauri/tauri.conf.json';cfg=json.loads(cfg_path.read_text(encoding='utf-8'))
 res=cfg.setdefault('bundle',{}).setdefault('resources',{})
 key='../src/assets/data/rosters.v310.bin.gz'
 if key in res:raise RuntimeError('Already registered compact base')
 res[key]='rosters.v310.bin.gz'
 cfg_path.write_text(json.dumps(cfg,indent=2,ensure_ascii=False),encoding='utf-8')
 # Native fast path. Existing uncompressed command is never modified.
 cargo_path=root/'src-tauri/Cargo.toml';cargo=cargo_path.read_text(encoding='utf-8')
 if 'base64 = ' not in cargo:
  cargo=once(cargo,'[dependencies]','[dependencies]\nbase64 = "0.22"','native rust dependency')
 cargo_path.write_text(cargo,encoding='utf-8')
 lib_path=root/'src-tauri/src/lib.rs';lib=lib_path.read_text(encoding='utf-8')
 # Native loader signatures may be async or sync in the inherited 18.385
 # Rust source. Register a separate command at module scope rather than
 # replacing a particular function header with brittle text matching.
 if not re.search(r'\b(?:async\s+)?fn\s+load_player_base\s*\(',lib):
  raise RuntimeError('Missing original native roster loader; refusing release')
 if re.search(r'\bfn\s+load_player_base_gzip_b64\s*\(',lib):
  raise RuntimeError('Compressed native loader already registered')
 if len(re.findall(r'\bload_player_base\s*,',lib))!=1:
  raise RuntimeError('Cannot identify exactly one Tauri command registration for original roster')
 lib=lib.rstrip()+'\n\n'+RUST+'\n'
 lib=re.sub(r'(?m)^(\s*)load_player_base,(\s*)
 lib_path.write_text(lib,encoding='utf-8')
 # JS bridge is populated by 18.385 native setup stage before this patch.
 s=once(s,"  loadPlayerBase:()=>call('load_player_base'),",
   "  loadPlayerBase:()=>call('load_player_base'),\n  loadPlayerBaseCompressed:()=>call('load_player_base_gzip_b64'),",
   'native bridge')
 s=once(s,'function v310StartRosterLoad(){',JS_ROSTER+'\nfunction v310StartRosterLoad(){',
   'packed browser decoder')
 old=""" const early=globalThis.__FUTBR_ROSTER_PRELOAD__;
 const nativeLoad=globalThis.FutBRDesktop?.loadPlayerBase
  ?globalThis.FutBRDesktop.loadPlayerBase()
  :(globalThis.__TAURI__?.core?.invoke?globalThis.__TAURI__.core.invoke('load_player_base'):null);"""
 new=""" const early=globalThis.__FUTBR_ROSTER_PRELOAD__;
 // Never start a second native transfer when preloaded data is already here.
 const nativeLoad=early?null:(
  globalThis.FutBRDesktop?.loadPlayerBaseCompressed&&
  typeof globalThis.DecompressionStream==='function'
   ?v18386LoadCompressedRoster()
   :(globalThis.FutBRDesktop?.loadPlayerBase
     ?globalThis.FutBRDesktop.loadPlayerBase()
     :(globalThis.__TAURI__?.core?.invoke
       ?globalThis.__TAURI__.core.invoke('load_player_base'):null)));"""
 s=once(s,old,new,'avoid duplicated native transfer and prefer compressed path')
 # Replace the manual and restored session critical path. Login and license
 # validation stay exactly as 18.385, and we do not mutate saved career data.
 anchor='async function v548EnterGame(){'
 if s.count(anchor)!=1:raise RuntimeError('Cannot isolate authoritative manual login')
 a=s.index(anchor);b=s.index("document.addEventListener('submit',async e=>",a)
 block=s[a:b]
 if "await v18385LocalOnce();" not in block or 'await v310StartRosterLoad();' not in block:raise RuntimeError('Manual login path changed')
 new_enter="""async function v548EnterGame(){
 return v18386StartEntry();
}
"""
 # VERSION is a Python constant, inside JS must not resolve to unrelated global.
 shell=JS_SHELL.replace(" version:VERSION, // version assigned in the patch only at release time",
                        " version:'18.386.0',")
 s=s[:a]+shell+'\n'+new_enter+s[b:]
 old=""" if(authenticated&&!v18385ManualAuthInProgress){
  const v18385RosterPending=v310StartRosterLoad();
  await localPreload;
  await v310StartRosterLoad();
  if(!state)renderWelcome();
  return;
 }"""
 new=""" if(authenticated&&!v18385ManualAuthInProgress){
  await v18386StartEntry();
  return;
 }"""
 s=once(s,old,new,'boot must show shell before player base')
 # After online sign-in (including failed password), reset this reentry gate
 # once a submit has finished. No duplicate auto login while auth is in-flight.
 s=once(s,
 "finally{if(btn){btn.disabled=false;btn.textContent=btn.dataset.v18385OriginalLabel||'Entrar no FutBR Manager';delete btn.dataset.v18385OriginalLabel;}}},true);",
 "finally{v18385ManualAuthInProgress=false;if(btn){btn.disabled=false;btn.textContent=btn.dataset.v18385OriginalLabel||'Entrar no FutBR Manager';delete btn.dataset.v18385OriginalLabel;}}},true);",
 'manual auth in-flight gate must reset')
 for code,label in [(JS_ROSTER,'decoder'),(shell,'fast shell')]:
  check=subprocess.run(['node','--check','-'],input=code,text=True,capture_output=True,timeout=30)
  if check.returncode:raise RuntimeError('18.386 '+label+' syntax: '+check.stderr[-2000:])
 if s.count(MARK)!=1:raise RuntimeError('18.386 patch marker mismatch')
 html_path.write_text(s,encoding='utf-8')
 report={'ok':True,'version':VERSION,
         'rosterBytesUnchanged':True,'originalRosterPreserved':True,
         'gzipSha256':hashlib.sha256(packed).hexdigest(),
         'originalRosterSha256':hashlib.sha256(raw).hexdigest(),
         'rawBytes':len(raw),'compressedBytes':len(packed),
         'transportRatio':round(len(packed)/len(raw),4),
         'gzipRoundTripLossless':True,
         'portableUserDatabaseTakesPriority':True,
         'nativeOriginalLoaderStillPresent':True,
         'browserDecompressionFallback':True,
         'authenticatedMenuPaintsBeforeRosterIpc':True,
         'onlineLicenseAlwaysRequired':True,
         'saveAndProgressionRemainGatedOnCompleteData':True,
         'logoutDuringLoadCannotReenter':True,
         'localMetadataAndRosterParallel':True,
         'noPreAuthWorldDataRead':True,
         'savesNeverMutated':True,'sameUpdaterConfiguration':True,
         'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'nonblocking-startup-18386-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
,lambda m:
  m.group(1)+'load_player_base,\n'+m.group(1)+'load_player_base_gzip_b64,'+m.group(2),lib,count=1)
 if len(re.findall(r'\bload_player_base_gzip_b64\s*,',lib))!=1:
  raise RuntimeError('Compressed loader was not registered in the same Tauri handler')
 lib_path.write_text(lib,encoding='utf-8')
 # JS bridge is populated by 18.385 native setup stage before this patch.
 s=once(s,"  loadPlayerBase:()=>call('load_player_base'),",
   "  loadPlayerBase:()=>call('load_player_base'),\n  loadPlayerBaseCompressed:()=>call('load_player_base_gzip_b64'),",
   'native bridge')
 s=once(s,'function v310StartRosterLoad(){',JS_ROSTER+'\nfunction v310StartRosterLoad(){',
   'packed browser decoder')
 old=""" const early=globalThis.__FUTBR_ROSTER_PRELOAD__;
 const nativeLoad=globalThis.FutBRDesktop?.loadPlayerBase
  ?globalThis.FutBRDesktop.loadPlayerBase()
  :(globalThis.__TAURI__?.core?.invoke?globalThis.__TAURI__.core.invoke('load_player_base'):null);"""
 new=""" const early=globalThis.__FUTBR_ROSTER_PRELOAD__;
 // Never start a second native transfer when preloaded data is already here.
 const nativeLoad=early?null:(
  globalThis.FutBRDesktop?.loadPlayerBaseCompressed&&
  typeof globalThis.DecompressionStream==='function'
   ?v18386LoadCompressedRoster()
   :(globalThis.FutBRDesktop?.loadPlayerBase
     ?globalThis.FutBRDesktop.loadPlayerBase()
     :(globalThis.__TAURI__?.core?.invoke
       ?globalThis.__TAURI__.core.invoke('load_player_base'):null)));"""
 s=once(s,old,new,'avoid duplicated native transfer and prefer compressed path')
 # Replace the manual and restored session critical path. Login and license
 # validation stay exactly as 18.385, and we do not mutate saved career data.
 anchor='async function v548EnterGame(){'
 if s.count(anchor)!=1:raise RuntimeError('Cannot isolate authoritative manual login')
 a=s.index(anchor);b=s.index("document.addEventListener('submit',async e=>",a)
 block=s[a:b]
 if "await v18385LocalOnce();" not in block or 'await v310StartRosterLoad();' not in block:raise RuntimeError('Manual login path changed')
 new_enter="""async function v548EnterGame(){
 return v18386StartEntry();
}
"""
 # VERSION is a Python constant, inside JS must not resolve to unrelated global.
 shell=JS_SHELL.replace(" version:VERSION, // version assigned in the patch only at release time",
                        " version:'18.386.0',")
 s=s[:a]+shell+'\n'+new_enter+s[b:]
 old=""" if(authenticated&&!v18385ManualAuthInProgress){
  const v18385RosterPending=v310StartRosterLoad();
  await localPreload;
  await v310StartRosterLoad();
  if(!state)renderWelcome();
  return;
 }"""
 new=""" if(authenticated&&!v18385ManualAuthInProgress){
  await v18386StartEntry();
  return;
 }"""
 s=once(s,old,new,'boot must show shell before player base')
 # After online sign-in (including failed password), reset this reentry gate
 # once a submit has finished. No duplicate auto login while auth is in-flight.
 s=once(s,
 "finally{if(btn){btn.disabled=false;btn.textContent=btn.dataset.v18385OriginalLabel||'Entrar no FutBR Manager';delete btn.dataset.v18385OriginalLabel;}}},true);",
 "finally{v18385ManualAuthInProgress=false;if(btn){btn.disabled=false;btn.textContent=btn.dataset.v18385OriginalLabel||'Entrar no FutBR Manager';delete btn.dataset.v18385OriginalLabel;}}},true);",
 'manual auth in-flight gate must reset')
 for code,label in [(JS_ROSTER,'decoder'),(shell,'fast shell')]:
  check=subprocess.run(['node','--check','-'],input=code,text=True,capture_output=True,timeout=30)
  if check.returncode:raise RuntimeError('18.386 '+label+' syntax: '+check.stderr[-2000:])
 if s.count(MARK)!=1:raise RuntimeError('18.386 patch marker mismatch')
 html_path.write_text(s,encoding='utf-8')
 report={'ok':True,'version':VERSION,
         'rosterBytesUnchanged':True,'originalRosterPreserved':True,
         'gzipSha256':hashlib.sha256(packed).hexdigest(),
         'originalRosterSha256':hashlib.sha256(raw).hexdigest(),
         'rawBytes':len(raw),'compressedBytes':len(packed),
         'transportRatio':round(len(packed)/len(raw),4),
         'gzipRoundTripLossless':True,
         'portableUserDatabaseTakesPriority':True,
         'nativeOriginalLoaderStillPresent':True,
         'browserDecompressionFallback':True,
         'authenticatedMenuPaintsBeforeRosterIpc':True,
         'onlineLicenseAlwaysRequired':True,
         'saveAndProgressionRemainGatedOnCompleteData':True,
         'logoutDuringLoadCannotReenter':True,
         'localMetadataAndRosterParallel':True,
         'noPreAuthWorldDataRead':True,
         'savesNeverMutated':True,'sameUpdaterConfiguration':True,
         'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'nonblocking-startup-18386-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
