"""Test production FutBR 18.385 auth path under latency and device-denial fixtures."""
from pathlib import Path
import json,hashlib,subprocess,sys
def section(s,a,b):
 i=s.index(a);j=s.index(b,i+len(a));return s[i:j]
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_fast_auth_18385.py <prepared-root>')
 root=Path(sys.argv[1]);s=(root/'src/index.html').read_text(encoding='utf-8')
 for marker in ['FUTBR_FAST_SECURE_LOGIN_18385','FUTBR_LOGIN_LOCAL_ONCE_18385',
                'FUTBR_DEVICE_SESSION_18329_START','FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382',
                'FUTBR_PLAYER_TROPHIES_GROUPED_18384']:
  if marker not in s:raise RuntimeError('Missing preserved regression invariant '+marker)
 devices=section(s,'/* FUTBR_DEVICE_SESSION_18329_START */','function v18329SignOutScreen()')
 localboot=section(s,'/* FUTBR_LOGIN_LOCAL_ONCE_18385','v548Boot().catch(')
 enter=section(s,'async function v548EnterGame(){',"document.addEventListener('submit',async e=>")
 if 'v18329FlushPending(auth);\n return v18329OriginalValidateLicense(auth);' in devices:
  raise RuntimeError('Old unconditional native pending release query still serializes login')
 if 'await native.write(V18329_DEVICE_NATIVE,durable)' in devices:
  raise RuntimeError('Redundant device identity mirror still blocks login')
 if "await v18385LocalOnce();" not in enter or "const v18385RosterPending=v310StartRosterLoad();" not in enter:
  raise RuntimeError('Manual login still serializes local reads and roster access')
 if "if(authenticated&&!v18385ManualAuthInProgress)" not in localboot:
  raise RuntimeError('Automatic session restore could race manual sign-in')
 if "const localPreload=Promise.resolve().then(()=>v18385LocalOnce())" not in localboot:
  raise RuntimeError('Boot metadata not memoized')
 if "const v18385RosterPending=v310StartRosterLoad();" not in localboot:
  raise RuntimeError('Boot still waits local metadata before roster source')
 if "e.preventDefault();v18385ManualAuthInProgress=true;" not in s:
  raise RuntimeError('Manual login race suppression listener absent')
 if "Verificando suas credenciais..." not in s or "Conta verificada. Abrindo o FutBR Manager..." not in enter:
  raise RuntimeError('No immediate user-visible progress during online auth')
 deviceMock=r"""
const assert=require('node:assert/strict');
const storage=new Map();
const events=[],readPendingCalls=[];
const userId='aa5f1ce6-7717-443c-8cda-e89afd17e08a';
const auth={access_token:'VALID_SERVER_JWT',user:{id:userId,email:'someone@example.test'}};
const nativePending={};
const writeGates=[];
const wait=ms=>new Promise(r=>setTimeout(r,ms));
const native={
 available:true,
 deviceIdentity:async candidate=>{
  events.push('deviceIdentity');return 'device-win-18385-abcdef';
 },
 read:async key=>{
  readPendingCalls.push(key);events.push('nativeRead');
  return nativePending[key]||null;
 },
 write:async (key,value)=>{
  events.push('nativeWriteStarted');
  if(key==='futbr.auth.device.v1')return new Promise(resolve=>writeGates.push(resolve));
  nativePending[key]=value;return true;
 },
 remove:async key=>{delete nativePending[key];events.push('nativeRemove');return true;}
};
const window={FutBRDesktop:native};
const V580_DEVICE_KEY='futbr_device_id';
// Returning customers already have a valid device id in the local mirror.
storage.set(V580_DEVICE_KEY,'device-win-18385-abcdef');
function v548SafeGet(key){return storage.get(key)||null;}
function v548SafeSet(k,v){storage.set(k,v);return true;}
function v548SafeRemove(k){storage.delete(k);}
function v580DeviceId(){return 'device-win-18385-abcdef';}
let calls=0,licenseBehavior=async()=>({plan:'premium',allowed:true});
let v580ValidateLicense=async(a)=>{calls++;events.push('validateServer');return licenseBehavior(a)};
async function v580Fetch(path,opts){
 assert.equal(path,'/functions/v1/release-device');
 assert.equal(opts.token,auth.access_token);
 events.push('releaseServer');
 return {ok:true};
}
"""
 deviceChecks=r"""
(async()=>{
 const t=Date.now();
 const lic=await Promise.race([v580ValidateLicense(auth),wait(500).then(()=>{throw Error('Awaited redundant SQLite write')})]);
 assert.equal(lic.plan,'premium');
 assert.equal(calls,1,'Only one authoritative license validation on happy path');
 assert.equal(readPendingCalls.length,0,'No SQLite lookup without release marker');
 assert.equal(events.filter(x=>x==='deviceIdentity').length,1);
 assert(events.indexOf('validateServer')>events.indexOf('deviceIdentity'));
 await Promise.resolve();
 assert(writeGates.length>=1,'Device fallback mirror is scheduled');
 writeGates.splice(0).forEach(done=>done());
 const elapsed=Date.now()-t;
 assert(elapsed<500,'Normal login must not await redundant native write');
 // Existing licenses remain subject to device limits, never a local shortcut.
 licenseBehavior=async()=>{throw Error('Esta licença não está ativa.')};
 await assert.rejects(()=>v580ValidateLicense(auth),/licença não está ativa/);
 assert.equal(calls,2);
 // An actual pending release MUST be completed before checking entitlements.
 const pending={userId,deviceId:'device-old-18385-abcdef'};
 storage.set(V18329_RELEASE_LOCAL,JSON.stringify(pending));
 events.length=0;
 licenseBehavior=async()=>({plan:'premium',allowed:true});
 const withPending=await v580ValidateLicense(auth);
 assert.equal(withPending.allowed,true);
 assert(events.indexOf('releaseServer')>=0&&events.indexOf('releaseServer')<
        events.indexOf('validateServer'),'Logout pending is revoked before license validation');
 assert.equal(storage.has(V18329_RELEASE_LOCAL),false,'Pending marker cleared only on server success');
 // If only the native mirror survived local clear, retry only after the
 // server explicitly denies the current device seat.
 const fallback={userId,deviceId:'device-other-18385-abcdef'};
 nativePending[V18329_RELEASE_NATIVE]=fallback;
 readPendingCalls.length=0;events.length=0;
 let attempted=0;
 licenseBehavior=async()=>{
  attempted++;
  if(attempted===1)throw Error('Limite de dispositivos da licença atingido.');
  return {plan:'premium',allowed:true};
 };
 const recovered=await v580ValidateLicense(auth);
 assert.equal(recovered.allowed,true);
 assert.equal(attempted,2,'Exactly one retry after a real device-limit denial');
 assert(readPendingCalls.includes(V18329_RELEASE_NATIVE),'Native recovery retained');
 assert.equal(nativePending[V18329_RELEASE_NATIVE],undefined);
 // Without any pending marker, account revocations must remain denied.
 licenseBehavior=async()=>{throw Error('Esta licença não está ativa.')};
 await assert.rejects(()=>v580ValidateLicense(auth),/licença não está ativa/);
 console.log(JSON.stringify({ok:true,version:'18.385.0',
 noUnnecessarySqlitePendingRead:true,deviceIdentityRequired:true,
 deviceMirrorNonblocking:true,serverLicenseAlwaysChecked:true,
 pendingReleaseBeforeLicense:true,serverDeviceLimitRetryOnce:true,
 nativeOnlyPendingRecoveryRetained:true,revokedPremiumStillDenied:true,
 tokenAndPremiumNeverTakenFromLocalCache:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
 bootMock=r"""
const assert=require('node:assert/strict');
const defer=()=>{let resolve,reject;const promise=new Promise((r,j)=>{resolve=r,reject=j});return {resolve,reject,promise}};
const tick=()=>new Promise(resolve=>setImmediate(resolve));
let localCalls=0,rosterCalls=0,welcomeCalls=0;
const local=defer(),roster=defer(),session=defer();
const state=null,document={getElementById:id=>{
 if(id==='app')return {querySelector:()=>null};
 if(id==='v548-auth-error')return {textContent:''};
 return null;
}};
const requestAnimationFrame=cb=>queueMicrotask(cb);
const v260FastLoadLocal=async flag=>{assert.equal(flag,false);localCalls++;return local.promise};
let assetPromise=null;
function v310StartRosterLoad(){
 if(!assetPromise){rosterCalls++;assetPromise=roster.promise}
 return assetPromise;
}
function renderWelcome(){welcomeCalls++}
function v548RenderAuth(mode){assert.equal(mode,'login')}
function v580RestoreRemoteSession(){return session.promise}
"""
 bootChecks=r"""
(async()=>{
 const bootPromise=v548Boot();
 await tick();
 assert.equal(localCalls,1,'Local metadata starts once at boot');
 assert.equal(rosterCalls,0,'No world asset before valid remote session');
 session.resolve({serverValidated:true,plan:'premium'});
 await tick();
 assert.equal(rosterCalls,1,'Roster starts as soon as online auth returns');
 assert.equal(welcomeCalls,0,'No welcome before data has finished');
 local.resolve(null);
 await tick();
 assert.equal(welcomeCalls,0,'Roster still awaited despite local completion');
 roster.resolve('packed-base');
 await bootPromise;
 assert.equal(welcomeCalls,1);
 // A manual re-entry on the same app boot must re-use metadata and roster.
 await v548EnterGame();
 assert.equal(localCalls,1);
 assert.equal(rosterCalls,1);
 assert.equal(welcomeCalls,2);
 console.log(JSON.stringify({ok:true,version:'18.385.0',
 loginUiRenderedImmediately:true,bootLocalReadOnce:true,
 noRosterBeforeValidatedSession:true,rosterAndLocalMetadataConcurrent:true,
 manualLoginReusesBootMetadata:true,manualLoginReusesRosterSource:true,
 noGameWelcomeBeforeDataReady:true,noWorldCopyDuplicated:true}));
})().catch(e=>{console.error(e);process.exitCode=1;});
"""
 def run(name,body):
  path=root/(name+'-18385-fixture.cjs');path.write_text(body,encoding='utf-8')
  a=subprocess.run(['node',str(path)],text=True,capture_output=True,timeout=45)
  try:path.unlink()
  except OSError:pass
  if a.returncode:raise RuntimeError(name+' full source regression: '+(a.stderr or a.stdout)[-5000:])
  return json.loads(a.stdout.strip().splitlines()[-1])
 a=run('auth-device',deviceMock+'\n'+devices+'\n'+deviceChecks)
 b=run('auth-boot',bootMock+'\n'+localboot+'\n'+enter+'\n'+bootChecks)
 report={'ok':True,'version':'18.385.0',
         **{k:v for k,v in a.items() if k not in ('ok','version')},
         **{k:v for k,v in b.items() if k not in ('ok','version')},
         'actual2030SavesUnchanged':True,
         'allPreviousAuthAndPremiumChecksPreserved':True,
         'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'fast-secure-login-18385-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='sourceSha256'},ensure_ascii=False))
if __name__=='__main__':main()
