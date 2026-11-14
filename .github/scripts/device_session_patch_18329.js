
/* FUTBR_DEVICE_SESSION_18329_START */
// Stable per-installation identity. Never store Auth tokens in the native KV.
const V18329_DEVICE_NATIVE='futbr.auth.device.v1';
const V18329_RELEASE_NATIVE='futbr.auth.pending_release.v1';
const V18329_RELEASE_LOCAL='futbr_auth_pending_release_v18329';
let v18329DevicePromise=null,v18329LogoutRunning=false;
function v18329ValidDeviceId(id){
 return typeof id==='string'&&/^[a-z0-9][a-z0-9-]{12,254}$/i.test(id);
}
function v18329NativeStore(){
 const native=window.FutBRDesktop;
 return native?.available&&typeof native.read==='function'&&typeof native.write==='function'?native:null;
}
async function v18329StableDeviceId(){
 if(v18329DevicePromise)return v18329DevicePromise;
 v18329DevicePromise=(async()=>{
  const native=v18329NativeStore();
  const legacy=v548SafeGet(V580_DEVICE_KEY);
  if(native){
   try{
    const persisted=await native.read(V18329_DEVICE_NATIVE);
    if(v18329ValidDeviceId(persisted)){
     v548SafeSet(V580_DEVICE_KEY,persisted);
     return persisted;
    }
    const id=v18329ValidDeviceId(legacy)?legacy:v580DeviceId();
    await native.write(V18329_DEVICE_NATIVE,id);
    v548SafeSet(V580_DEVICE_KEY,id);
    return id;
   }catch(err){
    console.warn('[FutBR] dispositivo no banco nativo indisponivel:',err?.message||err);
   }
  }
  const id=v18329ValidDeviceId(legacy)?legacy:v580DeviceId();
  v548SafeSet(V580_DEVICE_KEY,id);
  return id;
 })();
 return v18329DevicePromise;
}
function v18329ValidPending(p){
 return !!(p&&typeof p==='object'&&/^[0-9a-f-]{36}$/i.test(String(p.userId||''))&&v18329ValidDeviceId(p.deviceId));
}
async function v18329ReadPending(){
 const native=v18329NativeStore();
 if(native){
  try{const p=await native.read(V18329_RELEASE_NATIVE);if(v18329ValidPending(p))return p;}catch(err){console.warn('[FutBR] leitura pendente:',err?.message||err);}
 }
 try{const p=JSON.parse(v548SafeGet(V18329_RELEASE_LOCAL)||'null');return v18329ValidPending(p)?p:null;}catch(_){return null;}
}
async function v18329WritePending(p){
 if(!v18329ValidPending(p))return;
 v548SafeSet(V18329_RELEASE_LOCAL,JSON.stringify(p));
 const native=v18329NativeStore();
 if(native)try{await native.write(V18329_RELEASE_NATIVE,p);}catch(err){console.warn('[FutBR] pendencia no banco nativo:',err?.message||err);}
}
async function v18329ClearPending(){
 v548SafeRemove(V18329_RELEASE_LOCAL);
 const native=v18329NativeStore();
 if(native&&typeof native.remove==='function')try{await native.remove(V18329_RELEASE_NATIVE);}catch(err){console.warn('[FutBR] limpeza pendente:',err?.message||err);}
}
async function v18329ReleaseDevice(token,id){
 const data=await v580Fetch('/functions/v1/release-device',{
  token,body:{device_id:id}
 });
 if(data?.ok!==true)throw Error('Servidor nao confirmou a liberacao do dispositivo.');
 return data;
}
async function v18329FlushPending(auth){
 if(!auth?.access_token||!auth?.user?.id)return;
 const pending=await v18329ReadPending();
 if(!pending||pending.userId!==auth.user.id)return;
 try{
  await v18329ReleaseDevice(auth.access_token,pending.deviceId);
  await v18329ClearPending();
 }catch(err){console.warn('[FutBR] dispositivo sera liberado ao reconectar:',err?.message||err);}
}
// Existing license endpoint stays authoritative. Resolve the persistent device ID
// first, so its synchronous v580DeviceId() reads the right value.
const v18329OriginalValidateLicense=v580ValidateLicense;
v580ValidateLicense=async function(auth){
 await v18329StableDeviceId();
 await v18329FlushPending(auth);
 return v18329OriginalValidateLicense(auth);
};
function v18329SignOutScreen(){
 const el=document.createElement('div');
 el.className='v18329-signout-overlay';
 el.textContent='Encerrando sessao e liberando o dispositivo...';
 el.setAttribute('role','status');
 el.style.cssText='position:fixed;inset:0;display:flex;align-items:center;justify-content:center;padding:30px;background:rgba(18,5,9,.94);color:white;font:700 15px system-ui;z-index:2147483200;text-align:center';
 document.body.appendChild(el);
 return el;
}
async function v18329SignOut(){
 if(v18329LogoutRunning)return;
 v18329LogoutRunning=true;
 const screen=v18329SignOutScreen();
 const saved=v580GetRemoteSession();
 let token=saved?.access_token;
 const userId=saved?.user?.id;
 const isAuthor=v548Session?.plan==='author'||saved?.license?.plan==='author';
 let released=true,authLoggedOut=true;
 try{
  // Keep the current career safe, and stop simulating before leaving.
  try{
   if(state?.vacation){state.vacation.active=false;state.vacation.paused=true;}
   vacationEpoch++;
   if(v53Sim?.active||v53Sim?.starting){v53Sim.pause=true;v53Worker?.postMessage({op:'pause'});}
   if(state){const result=persist();if(result?.catch)result.catch(err=>console.warn('[FutBR] save ao sair:',err));}
  }catch(err){console.warn('[FutBR] preparando logout:',err?.message||err);}
  // Access tokens expire during long careers. Refresh before revoking the
  // device/session so a normal sign-out does not leave old sessions behind.
  if(saved?.refresh_token&&(!token||Number(saved.expiresAt||0)<=Date.now()+30000)){
   try{
    const fresh=await v580Fetch('/auth/v1/token?grant_type=refresh_token',{
     body:{refresh_token:saved.refresh_token}
    });
    if(fresh?.access_token)token=fresh.access_token;
   }catch(err){console.warn('[FutBR] renovacao para logout:',err?.message||err);}
  }
  if(token&&userId){
   const id=await v18329StableDeviceId();
   const pending={userId,deviceId:id};
   await v18329WritePending(pending);
   try{
    await v18329ReleaseDevice(token,id);
    await v18329ClearPending();
   }catch(err){released=false;console.warn('[FutBR] liberacao pendente:',err?.message||err);}
   // Author account cleans up legacy sessions on sign-out; regular players
   // sign out only this session and do not disturb other devices.
   try{
    await v580Fetch('/auth/v1/logout?scope='+(isAuthor?'global':'local'),{token});
   }catch(err){authLoggedOut=false;console.warn('[FutBR] revogacao remota pendente:',err?.message||err);}
  }
 }finally{
  v580SaveRemoteSession(null);
  v548SafeRemove(V548_AUTH_SESSION);
  v548Session=null;
  try{stopTimer();}catch(_){}
  try{closeModal();}catch(_){}
  try{v548RenderAuth('login',released&&authLoggedOut?'Sessao encerrada.':'Voce saiu deste computador. Uma liberacao remota ficou pendente para a proxima conexao.');}
  finally{screen.remove();v18329LogoutRunning=false;}
 }
}
// Window capture precedes the legacy document capture listeners, which used to
// delete local tokens without contacting Supabase. Block only the logout click.
window.addEventListener('click',event=>{
 const button=event.target?.closest?.('[data-v548-auth="logout"]');
 if(!button)return;
 event.preventDefault();
 event.stopImmediatePropagation();
 v18329SignOut().catch(err=>{console.error('[FutBR] logout:',err);});
},true);
window.GestorFC.deviceSessions18329={
 version:'18.329',stableId:v18329StableDeviceId,signOut:v18329SignOut,
 status:()=>({busy:v18329LogoutRunning,nativeStorage:!!v18329NativeStore(),
  releaseOnLogout:true,authorGlobalSignOut:true})
};
/* FUTBR_DEVICE_SESSION_18329_END */
