from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: test_device_sessions_18329.py <project-dir>')
 root=Path(sys.argv[1]);html=(root/'src'/'index.html').read_text(encoding='utf-8')
 start=html.index('/* FUTBR_DEVICE_SESSION_18329_START */')
 end=html.index('/* FUTBR_DEVICE_SESSION_18329_END */',start)+len('/* FUTBR_DEVICE_SESSION_18329_END */')
 patch=html[start:end]
 assert 'v580ValidateLicense=async function(auth)' in patch
 assert "'/functions/v1/release-device'" in patch
 assert "'/auth/v1/logout?scope='" in patch
 assert 'FUTBR_DEVICE_SESSION_18329' in patch
 assert "const V580_DEVICE_KEY='gestorfc_device_v580';" in html
 assert "'/functions/v1/validate-license'" in html
 assert '[204,205,304].includes(nativeStatus)?null:native.body' in html
 assert "v548Session=null" in patch
 rust=(root/'src-tauri'/'src'/'lib.rs').read_text(encoding='utf-8')
 assert 'fn device_identity(preferred_id: String)' in rust
 assert r'HKCU\Software\FutBRManager\Identity' in rust
 assert 'request.path == "/functions/v1/release-device"' in rust
 assert 'device_identity,' in rust
 assert "deviceIdentity:preferredId=>call('device_identity'" in html
 test=r'''
const assert=require('node:assert/strict');
const local=new Map(),disk=new Map(),registry=new Map(),calls=[];
const USER='11111111-1111-4111-8111-111111111111';
let failRelease=false, authFailure=false, renderLogin=0, persisted=0, vacationEpoch=0;
const V580_DEVICE_KEY='gestorfc_device_v580',V580_REMOTE_SESSION='gestorfc_supabase_session_v580',V548_AUTH_SESSION='gestor_fc_session_v548';
const window={listeners:{},GestorFC:{},addEventListener(name,callback,capture){this.listeners[name]={callback,capture};}};
const document={body:{children:[],appendChild(x){this.children.push(x)}},createElement(){return {removed:false,style:{},setAttribute(){},remove(){this.removed=true}}}};
const navigator={platform:'Win32'},crypto=require('node:crypto').webcrypto;
function v548SafeGet(k){return local.get(k)||''}
function v548SafeSet(k,v){local.set(k,v);return true}
function v548SafeRemove(k){local.delete(k)}
function v580DeviceId(){let id=v548SafeGet(V580_DEVICE_KEY);if(id)return id;id=crypto.randomUUID();v548SafeSet(V580_DEVICE_KEY,id);return id}
function v580GetRemoteSession(){try{return JSON.parse(v548SafeGet(V580_REMOTE_SESSION)||'null')}catch(e){return null}}
function v580SaveRemoteSession(x){if(!x)v548SafeRemove(V580_REMOTE_SESSION);else v548SafeSet(V580_REMOTE_SESSION,JSON.stringify(x))}
async function v580Fetch(path,args){calls.push({path,token:args?.token,body:args?.body});if(path.includes('/functions/v1/release-device')){
 if(failRelease)throw Error('network unavailable');return {ok:true,released:true}
}if(path.includes('/auth/v1/token?grant_type=refresh_token')){return {access_token:'refreshed-token'}}else if(path.includes('/auth/v1/logout')){if(authFailure)throw Error('auth unavailable');return {}}
throw Error('unexpected endpoint '+path)}
let v580ValidateLicense=async function(auth){calls.push({path:'/functions/v1/validate-license',deviceId:v580DeviceId()});return {plan:'author',allowed:true}};
let v548Session={plan:'author',username:'author'};
function v548RenderAuth(){renderLogin++;v548Session=null}
function stopTimer(){}
function closeModal(){}
function persist(){persisted++;return Promise.resolve()}
let state={vacation:{active:false,paused:false}},v53Sim={active:false,starting:false},v53Worker={postMessage(){}},vacationLoop=false;
window.FutBRDesktop={available:true,read:async k=>disk.get(k),write:async(k,value)=>{disk.set(k,value)},remove:async k=>{disk.delete(k)},deviceIdentity:async preferredId=>{if(!registry.has('DeviceId'))registry.set('DeviceId',preferredId);return registry.get('DeviceId')}};
''' + patch + r'''
(async()=>{
 const auth={access_token:'token-author',user:{id:USER}};
 // Migrate the original localStorage ID on the first upgraded boot.
 const prior='gf-1234567890abcdef1234567890';
 v548SafeSet(V580_DEVICE_KEY,prior);
 await v580ValidateLicense(auth);
 assert.equal(calls.at(-1).deviceId,prior);
 assert.equal(disk.get(V18329_DEVICE_NATIVE),prior);
 assert.equal(registry.get('DeviceId'),prior);
 // A full reinstall resets both WebView and native SQLite; registry remains.
 local.delete(V580_DEVICE_KEY);disk.delete(V18329_DEVICE_NATIVE);v18329DevicePromise=null;
 await v580ValidateLicense(auth);
 assert.equal(calls.at(-1).deviceId,prior);
 assert.equal(v548SafeGet(V580_DEVICE_KEY),prior);
 assert.equal(disk.get(V18329_DEVICE_NATIVE),prior);
 // Logout uses a top-level capture listener before legacy document capture.
 assert.equal(window.listeners.click.capture,true);
 v580SaveRemoteSession({access_token:'token-author',user:{id:USER},license:{plan:'author'}});
 await v18329SignOut();
 assert.equal(calls.at(-2).path,'/functions/v1/release-device');
 assert.equal(calls.at(-2).body.device_id,prior);
 assert.equal(calls.at(-1).path,'/auth/v1/logout?scope=global');
 assert.equal(v580GetRemoteSession(),null);
 assert.equal(disk.has(V18329_RELEASE_NATIVE),false);
 assert.equal(disk.get(V18329_DEVICE_NATIVE),prior);
 assert.equal(renderLogin,1);
 assert.equal(persisted,1);
 // Player logout is local only and does not revoke unrelated sessions.
 v548Session={plan:'premium'};
 v580SaveRemoteSession({access_token:'token-premium',user:{id:USER},license:{plan:'premium'}});
 await v18329SignOut();
 assert.equal(calls.at(-1).path,'/auth/v1/logout?scope=local');
 // Long careers may leave an expired JWT: refresh it before remote logout.
 v548Session={plan:'author'};
 v580SaveRemoteSession({access_token:'expired',refresh_token:'refresh-valid',expiresAt:0,user:{id:USER},license:{plan:'author'}});
 await v18329SignOut();
 assert.equal(calls.at(-3).path,'/auth/v1/token?grant_type=refresh_token');
 assert.equal(calls.at(-2).token,'refreshed-token');
 assert.equal(calls.at(-1).token,'refreshed-token');
 assert.equal(calls.at(-1).path,'/auth/v1/logout?scope=global');
 // If offline, the device release is queued without storing credentials.
 failRelease=true;v548Session={plan:'author'};
 v580SaveRemoteSession({access_token:'token-author',user:{id:USER},license:{plan:'author'}});
 await v18329SignOut();
 assert.ok(disk.get(V18329_RELEASE_NATIVE),'offline release not queued');
 assert.equal(v580GetRemoteSession(),null);
 assert.equal(disk.get(V18329_RELEASE_NATIVE).deviceId,prior);
 assert.equal(disk.get(V18329_RELEASE_NATIVE).access_token,undefined);
 // At next successful login, release the pending device first, then validate.
 failRelease=false;let oldN=calls.length;
 await v580ValidateLicense(auth);
 const latest=calls.slice(oldN);
 assert.equal(latest.length,2);
 assert.equal(latest[0].path,'/functions/v1/release-device');
 assert.equal(latest[1].path,'/functions/v1/validate-license');
 assert.equal(disk.has(V18329_RELEASE_NATIVE),false);
 // Another account cannot consume the release pending for this user.
 await v18329WritePending({userId:USER,deviceId:prior});
 oldN=calls.length;
 await v580ValidateLicense({access_token:'token-other',user:{id:'22222222-2222-4222-8222-222222222222'}});
 assert.equal(calls.length,oldN+1);
 assert.equal(disk.has(V18329_RELEASE_NATIVE),true);
 await v18329ClearPending();
 const output={ok:true,version:'18.329',migration:true,persistentNativeIdAcrossReinstall:true,
  authorGlobalSignOut:true,customerLocalSignOut:true,expiredTokenRefresh:true,releaseBeforeSignOut:true,
  registryIdentityAcrossReinstall:true,releaseDeviceAllowedByNativeProxy:true,
  offlineReleaseRetry:true,onlyAuthenticatedOwner:true,noPersistedAccessToken:true,savePreserved:true};
 console.log(JSON.stringify(output));
})().catch(e=>{console.error(e);process.exitCode=1});
'''
 p=root/'test-device-sessions-18329.cjs';p.write_text(test,encoding='utf-8')
 try:
  check=subprocess.run(['node','--check',str(p)],capture_output=True,text=True,timeout=20)
  if check.returncode:raise RuntimeError(check.stderr)
  run=subprocess.run(['node',str(p)],capture_output=True,text=True,timeout=30)
 finally:p.unlink(missing_ok=True)
 if run.returncode:raise RuntimeError((run.stderr or run.stdout)[-4000:])
 output=json.loads(run.stdout.strip().splitlines()[-1]);assert output['ok']
 (root/'device-sessions-18329-tests.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
 print(json.dumps(output))
if __name__=='__main__':main()
