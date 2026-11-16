from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

VERSION = "18.339.0"
FEED = "https://futbrmanager.com.br/updates/latest.json"
MARKER = "FUTBR_SIGNED_UPDATER_18339"


def once(source: str, before: str, after: str, label: str) -> str:
    count = source.count(before)
    if count != 1:
        raise RuntimeError(f"18.339 {label}: expected one anchor, found {count}")
    return source.replace(before, after, 1)


RUST = r'''
// FUTBR_SIGNED_UPDATER_18339: all downloads are verified by Tauri's
// Ed25519 updater before any Windows installer is allowed to run.
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct FutbrRelease18339 {
    version: String,
    current_version: String,
}

#[tauri::command]
async fn futbr_check_update_18339(app: AppHandle) -> Result<Option<FutbrRelease18339>, String> {
    use tauri_plugin_updater::UpdaterExt;
    let updater = app.updater_builder()
        .timeout(std::time::Duration::from_secs(15))
        .build().map_err(|e| e.to_string())?;
    let pending = updater.check().await.map_err(|e| e.to_string())?;
    Ok(pending.map(|update| FutbrRelease18339 {
        version: update.version.clone(),
        current_version: update.current_version.clone(),
    }))
}

#[tauri::command]
async fn futbr_install_update_18339(app: AppHandle) -> Result<(), String> {
    use tauri_plugin_updater::UpdaterExt;
    let updater = app.updater_builder()
        .timeout(std::time::Duration::from_secs(30))
        .build().map_err(|e| e.to_string())?;
    let update = updater.check().await.map_err(|e| e.to_string())?
        .ok_or_else(|| "Nenhuma atualização nova está disponível.".to_string())?;
    // Tauri validates the cryptographic .sig before starting the installer.
    // On Windows, Tauri quits after launching the signed NSIS update.
    update.download_and_install(|_chunk, _total| {}, || {})
        .await.map_err(|e| format!("Atualização recusada ou interrompida: {e}"))?;
    Ok(())
}

'''

SAVE_HOOK = r'''
/* FUTBR_SIGNED_UPDATER_18339_SAVE_GUARD
   This is inside the real career IIFE, so the native installer cannot exit
   before the active campaign has been committed to IndexedDB atomically. */
window.GestorFC=window.GestorFC||{};
window.GestorFC.prepareSignedUpdate18339=async function(){
 if(!state)return {saved:false};
 if(state.live||state.vacation?.active||v53Sim?.active||v53Sim?.starting||
    v53Sim?.syncing||v53Sim?.patching||v53Creating||v52Processing)
  throw Error('Pause as férias ou finalize a partida e a sincronização antes de atualizar.');
 // 18.338 verifies the career ID, season, day, manifest commit and save status.
 await ensureSaved();
 return {saved:true,year:state.year,day:state.day};
};
'''

CSS = r'''
<style id="futbr-desktop-update-style-18339">
#futbr-desktop-update-18339{position:fixed;right:16px;bottom:16px;z-index:2147483000;
 width:min(410px,calc(100vw - 32px));padding:16px 18px;border-radius:14px;
 border:1px solid #4a9f62;background:#102b1b;color:#f0fff4;
 box-shadow:0 12px 38px rgba(0,0,0,.5);font:13px/1.5 system-ui,Segoe UI,sans-serif}
#futbr-desktop-update-18339[hidden]{display:none!important}
#futbr-desktop-update-18339 .title{font-size:17px;font-weight:750;margin:0 0 6px}
#futbr-desktop-update-18339 .message{margin:5px 0 13px;opacity:.91}
#futbr-desktop-update-18339 .status{min-height:18px;font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}
#futbr-desktop-update-18339 .actions{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap}
#futbr-desktop-update-18339 button{border:1px solid #71957b;border-radius:8px;padding:8px 12px;
 cursor:pointer;background:#183b25;color:#f3fff6;font:inherit}
#futbr-desktop-update-18339 button.primary{background:#58d382;color:#0a2511;border-color:#58d382;font-weight:700}
#futbr-desktop-update-18339 button:disabled{opacity:.65;cursor:wait}
@media(max-width:760px){#futbr-desktop-update-18339{left:12px;right:12px;bottom:12px;width:auto}}
</style>
'''

JS = r'''
<script id="futbr-desktop-update-ui-18339">
(()=>{
 'use strict';
 if(!window.FutBRDesktop?.available)return;
 const invoke=window.__TAURI__?.core?.invoke||window.__TAURI__?.invoke;
 if(typeof invoke!=='function')return;
 let root=null,checking=false,installing=false,dismissed=false;
 function ensurePanel(){
  if(root)return root;
  if(!document.body)return null;
  root=document.createElement('aside');
  root.id='futbr-desktop-update-18339';
  root.hidden=true;
  root.setAttribute('role','status');
  root.setAttribute('aria-live','polite');
  root.innerHTML='<div class="title">Atualização do FutBR Manager</div>'+
   '<div class="message">Existe uma nova versão oficial disponível para o Windows.</div>'+
   '<div class="status" aria-live="polite"></div>'+
   '<div class="actions"><button class="primary" type="button" data-v18339-install>Salvar e atualizar</button>'+
   '<button type="button" data-v18339-later>Depois</button></div>';
  document.body.appendChild(root);
  root.querySelector('[data-v18339-later]').addEventListener('click',()=>{
   if(!installing){dismissed=true;root.hidden=true;}
  });
  root.querySelector('[data-v18339-install]').addEventListener('click',async()=>{
   if(installing)return;
   installing=true;
   const go=root.querySelector('[data-v18339-install]');
   const later=root.querySelector('[data-v18339-later]');
   go.disabled=later.disabled=true;
   function status(s){root.querySelector('.status').textContent=s;}
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
    installing=false;
   }
  });
  return root;
 }
 async function check(){
  if(checking||installing||dismissed)return null;
  checking=true;
  try{
   const update=await invoke('futbr_check_update_18339');
   if(update&&!dismissed){
    const panel=ensurePanel();
    if(panel){
     panel.querySelector('.message').textContent='Versão '+update.version+
      ' disponível (instalada: '+update.currentVersion+'). Seus saves serão protegidos antes da instalação.';
     panel.hidden=false;
    }
   }
   return update;
  }catch(error){
   // Offline or no release yet: keep gameplay/login fast and uninterrupted.
   console.info('[FutBR 18.339] Verificação de atualização indisponível:',String(error));
   return null;
  }finally{checking=false;}
 }
 window.FutBRUpdater18339={check};
 if(document.readyState==='loading')
  document.addEventListener('DOMContentLoaded',()=>setTimeout(check,5000),{once:true});
 else setTimeout(check,5000);
})();
</script>
'''


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: enable_desktop_updater_18339.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    pubkey = os.environ.get("FUTBR_UPDATER_PUBLIC_KEY", "").strip().replace("\\n", "\n")
    private_key = os.environ.get("TAURI_SIGNING_PRIVATE_KEY", "").strip()
    if not (pubkey and private_key):
        raise RuntimeError(
            "Para compilar o autoatualizador assinado, configure a variable "
            "FUTBR_UPDATER_PUBLIC_KEY e o secret TAURI_SIGNING_PRIVATE_KEY no GitHub. "
            "Nunca publique a chave privada no repositório."
        )
    if not re.search(r"(^|\n)RW[A-Za-z0-9+/=]{30,}", pubkey):
        raise RuntimeError("A chave pública do updater não parece um arquivo Minisign válido.")
    cfg_path = project / "src-tauri" / "tauri.conf.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    cfg["version"] = VERSION
    cfg.setdefault("bundle", {})["createUpdaterArtifacts"] = True
    cfg.setdefault("plugins", {})["updater"] = {
        "pubkey": pubkey,
        "endpoints": [FEED],
        "windows": {"installMode": "passive"},
    }
    cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")

    cargo_file = project / "src-tauri" / "Cargo.toml"
    cargo = cargo_file.read_text(encoding="utf-8")
    if "tauri-plugin-updater" not in cargo:
        cargo = once(cargo, "[dependencies]", '[dependencies]\ntauri-plugin-updater = "2"', "Cargo dependency")
    cargo_file.write_text(cargo, encoding="utf-8")

    rust_file = project / "src-tauri" / "src" / "lib.rs"
    rust = rust_file.read_text(encoding="utf-8")
    if MARKER in rust:
        raise RuntimeError("Updater 18.339 already applied; source must be clean")
    rust = once(rust, "#[tauri::command]\nfn desktop_info", RUST + "#[tauri::command]\nfn desktop_info", "Rust command anchor")
    rust = once(
        rust, "            desktop_info,",
        "            futbr_check_update_18339,\n            futbr_install_update_18339,\n            desktop_info,",
        "Rust invocation registration"
    )
    rust = once(
        rust, "tauri::Builder::default()",
        "tauri::Builder::default()\n        .plugin(tauri_plugin_updater::Builder::new().build())",
        "Rust plugin initialization"
    )
    rust_file.write_text(rust, encoding="utf-8")

    html_file = project / "src" / "index.html"
    html = html_file.read_text(encoding="utf-8")
    for marker in ("FUTBR_LONG_CAREER_SAVE_18338_BEGIN", "FUTBR_CHAMPIONS_RETIREMENT_18322", "function ensureSaved(){"):
        if marker not in html:
            raise RuntimeError("Validated 18.338 source is missing: " + marker)
    career_anchor = "window.GestorFC.version='18.155';window.GestorFC.visualVersion='18.155';\n})();\n</script>"
    html = once(html, career_anchor, SAVE_HOOK + "\n" + career_anchor, "career save guard")
    html = once(html, "</head>", CSS + "\n</head>", "update styles")
    html = once(html, "</body>", JS + "\n</body>", "update UI")
    html_file.write_text(html, encoding="utf-8")
    report = {
        "ok": True, "version": VERSION,
        "feed": FEED, "signedUpdater": True,
        "currentCareerSavedBeforeInstall": True, "careerHistoryPreserved": True,
        "checksNewVersionsAtStartup": True, "explicitUserConsent": True,
        "doesNotRunDuringVacation": True, "privateKeyStoredInRepository": False,
    }
    (project / "desktop-updater-18339-install.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
