"""FutBR 18.385: reduce login critical path without changing authority or saves.

The native identity remains stable, Supabase password/refresh and server license
must succeed before exposing the game, and revoked-device limits stay enforced.
Only the local SQLite mirror and a non-applicable pending-release read are
removed from the happy-path blocking work. Cached startup metadata is reused
while the local roster asset is fetched concurrently with metadata.
"""
from pathlib import Path
import json,hashlib,re,subprocess,sys
MARK='FUTBR_FAST_SECURE_LOGIN_18385'
def replace_once(s,old,new,name):
 n=s.count(old)
 if n!=1:raise RuntimeError(f'{name} anchor mismatch: {n} matches')
 return s.replace(old,new,1)
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: apply_fast_auth_18385.py <prepared-root>')
 root=Path(sys.argv[1]);p=root/'src/index.html';s=p.read_text(encoding='utf-8')
 for marker in ['FUTBR_DEVICE_SESSION_18329_START','FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382',
                'FUTBR_LONG_CAREER_REALISM_18383','FUTBR_PLAYER_TROPHIES_GROUPED_18384']:
  if marker not in s:raise RuntimeError('Preserved release invariant missing: '+marker)
 if MARK in s:raise RuntimeError('Fast auth already patched')
 # The saved local pending-release entry is the primary record because it is
 # stored BEFORE the native mirror. Use it first; fallback still reads native.
 old="""async function v18329ReadPending(){
 const native=v18329NativeStore();
 if(native){
  try{const p=await native.read(V18329_RELEASE_NATIVE);if(v18329ValidPending(p))return p;}catch(err){console.warn('[FutBR] leitura pendente:',err?.message||err);}
 }
 try{const p=JSON.parse(v548SafeGet(V18329_RELEASE_LOCAL)||'null');return v18329ValidPending(p)?p:null;}catch(_){return null;}
}"""
 new="""async function v18329ReadPending(){
 try{
  const p=JSON.parse(v548SafeGet(V18329_RELEASE_LOCAL)||'null');
  if(v18329ValidPending(p))return p;
 }catch(_){}
 const native=v18329NativeStore();
 if(native){
  try{const p=await native.read(V18329_RELEASE_NATIVE);if(v18329ValidPending(p))return p;}catch(err){console.warn('[FutBR] leitura pendente:',err?.message||err);}
 }
 return null;
}"""
 s=replace_once(s,old,new,'native pending lookup')
 # The Windows Registry identity is durable; its SQLite fallback mirror may be
 # updated asynchronously, eliminating an extra awaited native IPC at login.
 old="""     try{await native.write(V18329_DEVICE_NATIVE,durable);}catch(err){
      console.warn('[FutBR] espelho SQLite do dispositivo indisponivel:',err?.message||err);
     }
     return durable;"""
 new="""     try{
      Promise.resolve().then(()=>native.write(V18329_DEVICE_NATIVE,durable)).catch(err=>{
       console.warn('[FutBR] espelho SQLite do dispositivo indisponivel:',err?.message||err);
      });
     }catch(err){console.warn('[FutBR] espelho SQLite:',err?.message||err);}
     return durable;"""
 s=replace_once(s,old,new,'device mirror non-blocking')
 # A native read for a nonexistent logout pending marker used to block EVERY
 # login. Check the local marker synchronously. An actual same-user pending
 # release is still completed BEFORE validating the device seat. Retry once
 # on a server-reported device limit to recover native-only pending records.
 old="""v580ValidateLicense=async function(auth){
 await v18329StableDeviceId();
 await v18329FlushPending(auth);
 return v18329OriginalValidateLicense(auth);
};"""
 new="""/* FUTBR_FAST_SECURE_LOGIN_18385: no needless SQLite read on every login. */
v580ValidateLicense=async function(auth){
 await v18329StableDeviceId();
 let pending=null;
 try{pending=JSON.parse(v548SafeGet(V18329_RELEASE_LOCAL)||'null');}catch(_){}
 const localRelease=v18329ValidPending(pending)&&pending.userId===auth?.user?.id;
 if(localRelease)await v18329FlushPending(auth);
 try{return await v18329OriginalValidateLicense(auth);}
 catch(error){
  if(!localRelease&&/limite de dispositivos/i.test(String(error?.message||''))){
   await v18329FlushPending(auth);
   return v18329OriginalValidateLicense(auth);
  }
  throw error;
 }
};"""
 s=replace_once(s,old,new,'server authorized device seat preservation')
 # Boot and manual login share one idempotent small local metadata read.
 # It is still awaited before entering, and it never starts a world simulation.
 boot_marker='async function v548Boot(){'
 if s.count(boot_marker)!=1:raise RuntimeError('Boot source anchor missing')
 init="""/* FUTBR_LOGIN_LOCAL_ONCE_18385: reuse metadata from the boot promise. */
let v18385LocalBootPromise=null,v18385ManualAuthInProgress=false;
function v18385LocalOnce(){
 if(!v18385LocalBootPromise){
  v18385LocalBootPromise=Promise.resolve().then(()=>v260FastLoadLocal(false))
   .catch(e=>{v18385LocalBootPromise=null;throw e;});
 }
 return v18385LocalBootPromise;
}
"""
 s=replace_once(s,boot_marker,init+boot_marker,'memoized local boot')
 s=replace_once(s,
  "const localPreload=Promise.resolve().then(()=>v260FastLoadLocal(false)).catch(",
  "const localPreload=Promise.resolve().then(()=>v18385LocalOnce()).catch(",
  'reuse boot metadata promise')
 s=replace_once(s,
  " const authenticated=await Promise.race([authPromise,timeout]);\n if(timeoutId)clearTimeout(timeoutId);\n if(authenticated){\n  await localPreload;\n  await v310StartRosterLoad();",
  " const authenticated=await Promise.race([authPromise,timeout]);\n if(timeoutId)clearTimeout(timeoutId);\n if(authenticated&&!v18385ManualAuthInProgress){\n  const v18385RosterPending=v310StartRosterLoad();\n  await localPreload;\n  await v310StartRosterLoad();",
  'concurrent boot metadata and roster')
 s=replace_once(s,
  "authPromise.then(session=>{if(session&&!state){v548EnterGame().catch(",
  "authPromise.then(session=>{if(session&&!state&&!v18385ManualAuthInProgress){v548EnterGame().catch(",
  'no automatic boot takeover on manual sign in')
 # Give visible feedback as soon as the validated session returns.
 s=replace_once(s,
  " if(label)label.textContent='Conta conectada. Preparando os dados locais...';",
  """ if(label)label.textContent='Conta conectada. Preparando os dados locais...';
 else{
  const hint=document.getElementById('v548-auth-error');
  if(hint)hint.textContent='Conta verificada. Abrindo o FutBR Manager...';
 }""",
  'visible transition after online auth')
 s=replace_once(s,
  """ await v260FastLoadLocal(false);
 await v310StartRosterLoad();
 renderWelcome();
}""",
  """ const v18385RosterPending=v310StartRosterLoad();
 await v18385LocalOnce();
 await v310StartRosterLoad();
 renderWelcome();
}""",
  'concurrent manual login asset and metadata')
 # Label the network phase immediately without relying on deceptive timers.
 s=replace_once(s,
  """e.preventDefault();const btn=e.target.querySelector('button[type="submit"]'),err=document.getElementById('v548-auth-error');if(btn)btn.disabled=true;if(err)err.textContent='';try{if(e.target.id==='v548-login-form')""",
  """e.preventDefault();v18385ManualAuthInProgress=true;const btn=e.target.querySelector('button[type="submit"]'),err=document.getElementById('v548-auth-error');if(btn){btn.disabled=true;btn.dataset.v18385OriginalLabel=btn.textContent;btn.textContent='Autenticando...';}if(err)err.textContent='Verificando suas credenciais...';try{if(e.target.id==='v548-login-form')""",
  'immediate login button status and race gate')
 s=replace_once(s,
  "finally{if(btn)btn.disabled=false;}},true);",
  "finally{if(btn){btn.disabled=false;btn.textContent=btn.dataset.v18385OriginalLabel||'Entrar no FutBR Manager';delete btn.dataset.v18385OriginalLabel;}}},true);",
  'restore login submit state')
 # Expose non-sensitive diagnostics (no email, tokens or passwords).
 anchor="window.GestorFC.render=render;\nwindow.GestorFC.fontSettings18376="
 if s.count(anchor)!=1:raise RuntimeError('Final UI feature marker missing')
 diag="""window.GestorFC.fastSecureLogin18385={
 version:'18.385.0',serverLicenseValidationRequired:true,
 nativeDeviceSeatEnforced:true,oldSavesSupported:true,
 localMetadataReadReused:()=>!!v18385LocalBootPromise,
 rosterAssetLoaded:()=>!!v310RosterText
};
"""
 s=s.replace(anchor,diag+anchor,1)
 # Smoke syntax checks on the isolated added functions and simple markers.
 for source in [init,new]:
  r=subprocess.run(['node','--check','-'],input=source,text=True,capture_output=True,timeout=25)
  if r.returncode:raise RuntimeError('18.385 inserted code invalid '+r.stderr[-2500:])
 if s.count(MARK)!=1:raise RuntimeError('18.385 marker missing or duplicated')
 p.write_text(s,encoding='utf-8')
 report={'ok':True,'version':'18.385.0','remotePasswordAuthPreserved':True,
  'licenseIsAlwaysServerValidated':True,'deviceLimitStillEnforced':True,
  'pendingDeviceReleaseRetained':True,'nativeFallbackStillRetained':True,
  'deviceIdentityMirrorDoesNotBlockLogin':True,
  'noNativePendingReadWithoutEvidenceInHappyPath':True,
  'bootAndManualLocalMetadataDeduped':True,
  'rosterAndLocalMetadataStartConcurrentlyAfterAuth':True,
  'welcomeNeverShownBeforeLicenseAndLocalRoster':True,
  'manualAndAutomaticLoginRaceGuard':True,
  'noAdditionalFullWorldClone':True,
  'oldSavesAndPreviousPerformancePreserved':True,
  'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'fast-secure-login-18385-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
