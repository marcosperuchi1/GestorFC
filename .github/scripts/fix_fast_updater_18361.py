from __future__ import annotations
import json,sys
from pathlib import Path
V='18.361.0'
ORIG='https://futbrmanager.com.br/updates/latest.json'
DIRECT='https://download.futbrmanager.com.br/updates/latest.json'
MARK='FUTBR_FAST_SIGNED_UPDATER_18361'

def once(s,a,b,label):
 n=s.count(a)
 if n!=1:raise RuntimeError(f'18.361 {label}: expected one anchor, got {n}')
 return s.replace(a,b,1)

RUST_CACHE=r'''
// FUTBR_FAST_SIGNED_UPDATER_18361
// Only the checked HTTPS release metadata is cached; never cache the 43 MB
// installer or bypass Tauri Ed25519 signature verification.
static FUTBR_CHECKED_UPDATE_18361: std::sync::OnceLock<
 std::sync::Mutex<Option<(tauri_plugin_updater::Update,std::time::Instant)>>>
 =std::sync::OnceLock::new();
'''
RUST_INSTALL=r'''
#[tauri::command]
async fn futbr_install_update_18339(app: AppHandle) -> Result<(), String> {
    use tauri::Emitter;
    use tauri_plugin_updater::UpdaterExt;
    use std::time::{Duration,Instant};

    // Skip a second release manifest request for the same update, if its
    // signed metadata was checked fewer than ten minutes ago.
    let cached=FUTBR_CHECKED_UPDATE_18361.get()
        .and_then(|slot|slot.lock().ok())
        .and_then(|mut guard|guard.take())
        .and_then(|(update,at)|if at.elapsed()<Duration::from_secs(600)
                  {Some(update)}else{None});
    let mut update=match cached{
        Some(update)=>update,
        None=>{
            let updater=app.updater_builder().timeout(Duration::from_secs(20))
                .build().map_err(|e|e.to_string())?;
            updater.check().await.map_err(|e|e.to_string())?
                .ok_or_else(||"Nenhuma atualização nova está disponível.".to_string())?
        }
    };
    // The downloader is allowed to be slower than the small manifest check.
    update.timeout=Some(Duration::from_secs(600));
    let _=app.emit("futbr-update-progress-18361",
                   serde_json::json!({"phase":"starting"}));
    let app_progress=app.clone();
    let app_complete=app.clone();
    let mut bytes:u64=0;
    let mut last_event=Instant::now();
    let mut first=true;
    update.download_and_install(
        move |chunk,total|{
            bytes=bytes.saturating_add(chunk as u64);
            if first||last_event.elapsed()>=Duration::from_millis(160)||
                  total.map_or(false,|n|bytes>=n){
                let _=app_progress.emit("futbr-update-progress-18361",
                    serde_json::json!({"phase":"downloading",
                                      "bytes":bytes,"total":total}));
                last_event=Instant::now();first=false;
            }
        },
        move ||{
            let _=app_complete.emit("futbr-update-progress-18361",
                serde_json::json!({"phase":"verifying"}));
        },
    ).await.map_err(|e|format!("Atualização recusada ou interrompida: {e}"))?;
    // Windows closes the app only after opening its signed NSIS installer.
    Ok(())
}
'''
OLD_HANDLER=r'''   function status(s){root.querySelector('.status').textContent=s;}
   try{
    if(typeof window.GestorFC?.prepareSignedUpdate18339!=='function')
     throw Error('Proteção do salvamento indisponível. A atualização foi cancelada.');
    status('Confirmando o salvamento da carreira...');
    await window.GestorFC.prepareSignedUpdate18339();
    status('Baixando e verificando a assinatura da atualização. Não feche o jogo.');
    await invoke('futbr_install_update_18339');
    status('Instalador oficial iniciado.');
   }catch(error){
    status('Não foi possível atualizar: '+String(error?.message||error));
    go.disabled=later.disabled=false;
    document.body.classList.remove('futbr-update-installing18339');
    installing=false;
   }'''
NEW_HANDLER=r'''   function status(s){root.querySelector('.status').textContent=s;}
   const progress=root.querySelector('.v18361-progress');
   let unlisten=null,received=0,expected=0,downloadStart=0;
   function mb(n){return (Math.max(0,n)/1048576).toFixed(1)+' MB';}
   function onProgress(data){
    if(!data||!installing)return;
    if(data.phase==='starting')status('Conectando ao servidor de atualização...');
    else if(data.phase==='downloading'){
     if(!downloadStart)downloadStart=Date.now();
     received=Math.max(received,Number(data.bytes)||0);
     expected=Math.max(expected,Number(data.total)||0);
     progress.hidden=false;
     if(expected>0){
      const percent=Math.min(100,Math.round(100*received/expected));
      progress.value=percent;
      const seconds=Math.max(1,(Date.now()-downloadStart)/1000);
      status('Baixando atualização: '+percent+'% ('+mb(received)+' de '+
             mb(expected)+') · '+mb(received/seconds)+'/s');
     }else{
      progress.removeAttribute('value');
      status('Baixando atualização: '+mb(received)+' recebidos...');
     }
    }else if(data.phase==='verifying'){
     progress.hidden=false;progress.value=100;
     status('Download concluído. Validando assinatura e preparando instalação...');
    }
   }
   try{
    if(typeof window.GestorFC?.prepareSignedUpdate18339!=='function')
     throw Error('Proteção do salvamento indisponível. A atualização foi cancelada.');
    status('Confirmando o salvamento da carreira...');
    await window.GestorFC.prepareSignedUpdate18339();
    // A UI may lack the event API; the original signed installer still works.
    if(typeof listen==='function')try{
     unlisten=await listen('futbr-update-progress-18361',e=>onProgress(e?.payload));
    }catch(error){console.info('[18.361] Eventos de progresso:',String(error));}
    status('Iniciando download oficial. Esta etapa depende da conexão.');
    await invoke('futbr_install_update_18339');
    status('Instalador oficial iniciado.');
   }catch(error){
    status('Não foi possível atualizar: '+String(error?.message||error));
    go.disabled=later.disabled=false;
    progress.hidden=true;
    document.body.classList.remove('futbr-update-installing18339');
    installing=false;
   }finally{
    if(typeof unlisten==='function')try{unlisten();}catch(_error){}
   }'''

def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_fast_updater_18361.py <project>')
 root=Path(sys.argv[1])
 hp=root/'src/index.html';rp=root/'src-tauri/src/lib.rs';cp=root/'src-tauri/tauri.conf.json'
 html=hp.read_text(encoding='utf-8');rust=rp.read_text(encoding='utf-8')
 cfg=json.loads(cp.read_text(encoding='utf-8-sig'))
 if MARK in rust:raise RuntimeError('18.361 updater already installed')
 if cfg.get('version')!=V:raise RuntimeError('Set 18.361 version before speed patch')
 updater=cfg.get('plugins',{}).get('updater',{})
 if updater.get('endpoints')!=[ORIG]:raise RuntimeError('Source Tauri feed not trusted 18.360')
 if not updater.get('pubkey') or cfg.get('bundle',{}).get('createUpdaterArtifacts') is not True:
  raise RuntimeError('Signed update trust must remain intact')
 if cfg.get('bundle',{}).get('windows',{}).get('nsis',{}).get('installMode')!='currentUser':
  raise RuntimeError('NSIS per-user installation must remain intact')
 updater['endpoints']=[DIRECT]
 cp.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
 a=rust.index('// FUTBR_SIGNED_UPDATER_18339')
 b=rust.index('#[tauri::command]\nfn desktop_info',a)
 rs=rust[a:b]
 rs=once(rs,'#[derive(Serialize)]\n#[serde(rename_all = "camelCase")]\nstruct FutbrRelease18339',
         RUST_CACHE+'\n#[derive(Serialize)]\n#[serde(rename_all = "camelCase")]\nstruct FutbrRelease18339',
         'release metadata cache injection')
 rs=once(rs,
  'let pending = updater.check().await.map_err(|e| e.to_string())?;\n    Ok(pending.map(|update| FutbrRelease18339 {',
  '''let pending = updater.check().await.map_err(|e| e.to_string())?;
    if let Some(ref update)=pending{
        let slot=FUTBR_CHECKED_UPDATE_18361.get_or_init(||
            std::sync::Mutex::new(None));
        if let Ok(mut guard)=slot.lock(){
            *guard=Some((update.clone(),std::time::Instant::now()));
        }
    }
    Ok(pending.map(|update| FutbrRelease18339 {''',
  'cache checked update without caching binary')
 i=rs.index('#[tauri::command]\nasync fn futbr_install_update_18339(')
 j=rs.index('\n}\n',i)+3
 if 'update.download_and_install(|_chunk, _total| {}, || {})' not in rs[i:j]:
  raise RuntimeError('Could not identify official Tauri signed installer call')
 rs=rs[:i]+RUST_INSTALL+rs[j:]
 rust=rust[:a]+rs+rust[b:]
 rp.write_text(rust,encoding='utf-8')
 a=html.index('<style id="futbr-desktop-update-style-18339">')
 b=html.index('</style>',a)+len('</style>')
 css=html[a:b]
 css=once(css,'background:rgba(0,0,0,.65)','background:rgba(0,0,0,.28)','non-frozen overlay')
 css=once(css,'</style>','''#futbr-desktop-update-18339 .v18361-progress{display:block;width:100%;height:10px;
margin:8px 0 5px;accent-color:#58d382}
#futbr-desktop-update-18339 .v18361-progress[hidden]{display:none}
#futbr-desktop-update-18339 .status{font-variant-numeric:tabular-nums}
</style>''','download meter styling')
 html=html[:a]+css+html[b:]
 a=html.index('<script id="futbr-desktop-update-ui-18339">')
 b=html.index('</script>',a)+len('</script>')
 js=html[a:b]
 js=once(js,' const invoke=window.__TAURI__?.core?.invoke||window.__TAURI__?.invoke;',
         ''' const invoke=window.__TAURI__?.core?.invoke||window.__TAURI__?.invoke;
 const listen=window.__TAURI__?.event?.listen;''','event subscription')
 js=once(js,
  '''   '<div class="status" aria-live="polite"></div>'+
   '<div class="actions">''',
  '''   '<div class="status" aria-live="polite"></div>'+
   '<progress class="v18361-progress" max="100" value="0" hidden></progress>'+
   '<div class="actions">''','progress meter')
 js=once(js,OLD_HANDLER,NEW_HANDLER,'signed updater UI')
 html=html[:a]+js+html[b:]
 if 'FUTBR_VACATION_FINALIZE_LIGHT_18360' in html:
  html=once(html,"const EDITION='18.360.0';","const EDITION='18.361.0';",'visible edition')
  html=once(html,"window.GestorFC.version='18.360.0';window.GestorFC.visualVersion='18.360.0';",
            "window.GestorFC.version='18.361.0';window.GestorFC.visualVersion='18.361.0';",'runtime version')
 hp.write_text(html,encoding='utf-8')
 out={'ok':True,'version':V,'noDuplicateCheckWithinMinutes':10,
      'officialCDNFeed':DIRECT,'metadataOnlyCache':True,'noInstallerPrefetch':True,
      'downloadProgressThrottleMs':160,'signatureVerificationPreserved':True,
      'safeCareerSaveBeforeInstall':True,'nsisPerUserPreserved':True,
      'noLargeGameMemoryAllocation':True}
 (root/'fast-updater-18361-install.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':main()
