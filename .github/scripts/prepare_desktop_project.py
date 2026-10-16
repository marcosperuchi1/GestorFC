from __future__ import annotations
import json, re, sys
from pathlib import Path

def replace_once(text, old, new, label):
    n=text.count(old)
    if n!=1:
        raise RuntimeError(f"{label}: esperado 1, encontrado {n}")
    return text.replace(old,new,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: prepare_desktop_project.py <project-dir>")
    project=Path(sys.argv[1]).resolve()

    # Tauri config
    cfg_path=project/"src-tauri"/"tauri.conf.json"
    cfg=json.loads(cfg_path.read_text(encoding="utf-8-sig"))
    bundle=cfg.setdefault("bundle",{})
    nsis=bundle.setdefault("windows",{}).setdefault("nsis",{})
    if nsis.get("installMode")=="perUser":
        nsis["installMode"]="currentUser"
    nsis["installerIcon"]="icons/icon.ico"
    nsis["uninstallerIcon"]="icons/icon.ico"
    resources=bundle.get("resources")
    if not isinstance(resources,dict):
        resources={}
        bundle["resources"]=resources
    resources["../src/assets/data/rosters.v310.bin"]="rosters.v310.bin"
    cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding="utf-8")

    # Windows GUI subsystem
    main_path=project/"src-tauri"/"src"/"main.rs"
    main_rs=main_path.read_text(encoding="utf-8")
    attr='#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]'
    if attr not in main_rs:
        main_rs=attr+"\n"+main_rs
    main_path.write_text(main_rs,encoding="utf-8")

    # Native commands
    lib_path=project/"src-tauri"/"src"/"lib.rs"
    lib=lib_path.read_text(encoding="utf-8")
    lib=replace_once(lib,"use serde::Serialize;","use serde::{Deserialize, Serialize};","serde imports")
    if "struct KvWrite" not in lib:
        lib=replace_once(
            lib,
            "struct DesktopDb(Mutex<Connection>);",
            """struct DesktopDb(Mutex<Connection>);

#[derive(Deserialize)]
struct KvWrite {
    key: String,
    value: serde_json::Value,
}""",
            "KvWrite"
        )
    if "fn kv_put_many(" not in lib:
        native=r'''
#[tauri::command]
fn kv_put_many(entries: Vec<KvWrite>, db: State<'_, DesktopDb>) -> Result<(), String> {
    let mut conn = db.0.lock().map_err(|_| "Banco ocupado".to_string())?;
    let tx = conn.transaction().map_err(|e| e.to_string())?;
    {
        let mut stmt = tx.prepare(
            "INSERT INTO kv(key,value,updated_at) VALUES(?1,?2,unixepoch('now')*1000)
             ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at"
        ).map_err(|e| e.to_string())?;
        for entry in entries {
            let value = serde_json::to_string(&entry.value).map_err(|e| e.to_string())?;
            stmt.execute(params![entry.key, value]).map_err(|e| e.to_string())?;
        }
    }
    tx.commit().map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn open_external_url(url: String) -> Result<(), String> {
    let lower = url.to_ascii_lowercase();
    if !(lower == "https://futbrmanager.com.br"
        || lower.starts_with("https://futbrmanager.com.br/")) {
        return Err("Endereco externo nao permitido.".to_string());
    }
    open::that(url).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn close_game(app: AppHandle) -> Result<(), String> {
    app.exit(0);
    Ok(())
}

#[tauri::command]
fn open_premium_site(app: AppHandle) -> Result<(), String> {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.minimize();
    }
    open::that("https://futbrmanager.com.br/#planos").map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn load_player_base(app: AppHandle) -> Result<String, String> {
    let exe_dir = std::env::current_exe()
        .ok()
        .and_then(|p| p.parent().map(|d| d.to_path_buf()));
    if let Some(dir) = exe_dir {
        let portable = dir.join("rosters.v310.bin");
        if portable.exists() {
            return fs::read_to_string(&portable)
                .map_err(|e| format!("Falha ao ler a base local portátil: {e}"));
        }
    }
    let resource_dir = app.path().resource_dir().map_err(|e| e.to_string())?;
    let bundled = resource_dir.join("rosters.v310.bin");
    fs::read_to_string(&bundled)
        .map_err(|e| format!("Falha ao ler a base local instalada: {e}"))
}

'''
        lib=replace_once(lib,"#[tauri::command]\nfn desktop_info",native+"#[tauri::command]\nfn desktop_info","native commands")
        lib=replace_once(
            lib,
            "            kv_commit_manifest,\n            desktop_info,",
            "            kv_commit_manifest,\n            kv_put_many,\n            open_external_url,\n            close_game,\n            load_player_base,\n            desktop_info,",
            "handler commands"
        )
    lib_path.write_text(lib,encoding="utf-8")

    # Frontend patch
    index_path=project/"src"/"index.html"
    html=index_path.read_text(encoding="utf-8")

    # remove literal backslash-n artifacts near desktop bridge
    html=html.replace('<body class="">\\n<script id="futbr-desktop-native-bridge">','<body class=""><script id="futbr-desktop-native-bridge">')
    html=html.replace('</script>\\n\n<div id="app"','</script>\n<div id="app"')
    html=html.replace('\\n<style id="futbr-desktop-native-style">','<style id="futbr-desktop-native-style">')
    html=html.replace('</style>\\n<script id="futbr-desktop-native-ui">','</style><script id="futbr-desktop-native-ui">')

    # Hot storage remains IndexedDB; native DB is manual mirror only.
    html=html.replace('window.FutBRDesktop?.available','window.FutBRDesktop?.directStorage')
    html=html.replace('if(!window.FutBRDesktop?.directStorage)return;\n const baseUpdate','if(!window.FutBRDesktop?.available)return;\n const baseUpdate')
    html=html.replace(' const api={\n  available,',' const api={\n  available,\n  directStorage:false,')
    html=replace_once(
        html,
        "  openDataFolder:()=>call('open_data_folder')",
        "  openDataFolder:()=>call('open_data_folder'),\n  writeMany:entries=>call('kv_put_many',{entries:entries||[]}),\n  openUrl:url=>call('open_external_url',{url:String(url)}),\n  openPremium:()=>call('open_premium_site'),\n  loadPlayerBase:()=>call('load_player_base'),\n  closeGame:()=>call('close_game')",
        "desktop api"
    )

    html=html.replace("const PRICE = 'R$ 24,99';","const PRICE = 'R$ 19,90';")
    html=html.replace("purchasePriceBRL: 24.99","purchasePriceBRL: 19.90")

    viewport=r'''
<style id="futbr-desktop-viewport-lock">
html.futbr-desktop,html.futbr-desktop body{width:100%!important;height:100%!important;min-height:0!important;max-height:100%!important;margin:0!important;padding:0!important;overflow:hidden!important;overscroll-behavior:none!important}
html.futbr-desktop #app{position:fixed!important;inset:0!important;width:100vw!important;height:100dvh!important;min-height:0!important;max-height:100dvh!important;overflow:hidden!important}
html.futbr-desktop .main-wrap{height:100dvh!important;min-height:0!important;max-height:100dvh!important;overflow:hidden!important}
@media(min-width:761px){html.futbr-desktop body.v54-competitions-view .main{height:calc(100dvh - 66px)!important;min-height:calc(100dvh - 66px)!important;max-height:calc(100dvh - 66px)!important;overflow:hidden!important}}
</style>
'''
    if 'futbr-desktop-viewport-lock' not in html:
        html=replace_once(html,'</head>',viewport+'\n</head>','viewport css')

    auth_theme=r'''
<style id="futbr-desktop-auth-green">
html.futbr-desktop .v548-auth{
 height:100dvh!important;min-height:0!important;overflow:hidden!important;
 padding:clamp(12px,2.3vh,28px)!important;
 background:radial-gradient(circle at 12% 10%,rgba(60,184,106,.19),transparent 35%),radial-gradient(circle at 86% 86%,rgba(17,103,63,.22),transparent 40%),#06140c!important;
 --bg:#06140c;--panel:#0d2116;--panel2:#12301f;--line:#2f6847;--text:#f0f7f2;--muted:#b2cbbb;--dim:#7fa28d;--accent:#65d98d;--accent2:#b9efc9;--gold:#d8d98a;--red:#ff9a92
}
html.futbr-desktop .v548-auth-shell{width:min(1180px,100%)!important;max-height:100%!important;min-height:0!important;gap:20px!important;align-items:stretch!important}
html.futbr-desktop .v548-auth-brand,html.futbr-desktop .v548-auth-card{background:linear-gradient(145deg,rgba(94,214,137,.055),transparent 58%),#0c2116!important;border-color:#397a53!important;box-shadow:0 22px 70px rgba(0,0,0,.36)!important;min-height:0!important}
html.futbr-desktop .v548-auth-brand:before{background:linear-gradient(90deg,#5fd489,#9ee3b5 56%,#c8dc84)!important}
html.futbr-desktop .v548-auth-card{overflow:hidden!important}
html.futbr-desktop .v548-plan-card{background:rgba(0,0,0,.16)!important;border-color:#315e43!important}
html.futbr-desktop .v548-plan-card.premium{background:rgba(91,189,122,.08)!important;border-color:#5ab378!important}
html.futbr-desktop .v548-auth-tabs{background:rgba(0,0,0,.16)!important;border-color:#315e43!important}
html.futbr-desktop .v548-auth-tabs button.active{background:rgba(101,217,141,.13)!important;color:#83e4a5!important}
html.futbr-desktop .v548-auth .field input{background:#07170e!important;border-color:#315e43!important;color:#f4faf6!important}
html.futbr-desktop .v548-auth .field input:focus{border-color:#65d98d!important;box-shadow:0 0 0 2px rgba(101,217,141,.12)!important}
html.futbr-desktop .v548-auth .btn.primary{background:#58d382!important;border-color:#58d382!important;color:#062010!important}
html.futbr-desktop .futbr-desktop-close-auth{margin-top:10px!important;padding-top:9px!important;border-top-color:#315e43!important}
@media (max-height:940px) and (min-width:841px){
 html.futbr-desktop .v548-auth{padding:12px 18px!important}
 html.futbr-desktop .v548-auth-shell{height:calc(100dvh - 24px)!important;gap:16px!important}
 html.futbr-desktop .v548-auth-brand{padding:24px 28px!important}
 html.futbr-desktop .v548-auth-brand h1{font-size:clamp(38px,5.1vh,56px)!important;line-height:1!important;margin:14px 0 10px!important}
 html.futbr-desktop .v548-auth-brand>p{font-size:11px!important;line-height:1.55!important}
 html.futbr-desktop .v548-plan-grid{padding-top:14px!important;gap:9px!important}
 html.futbr-desktop .v548-plan-card{padding:12px!important}
 html.futbr-desktop .v548-plan-card ul{margin-top:7px!important;font-size:9px!important;line-height:1.45!important}
 html.futbr-desktop .v548-auth-card{padding:22px 26px!important}
 html.futbr-desktop .v548-auth-card h2{font-size:24px!important}
 html.futbr-desktop .v548-auth-card>.subtext{margin:5px 0 14px!important}
 html.futbr-desktop .v548-auth-tabs{margin-bottom:14px!important}
 html.futbr-desktop .v548-auth-form{gap:9px!important}
 html.futbr-desktop .v548-auth-form .field{gap:4px!important}
 html.futbr-desktop .v548-auth-form .field input{min-height:36px!important;padding:8px 10px!important}
 html.futbr-desktop .v548-auth-form .btn{min-height:36px!important}
 html.futbr-desktop .v548-auth-error{margin-top:7px!important;min-height:16px!important}
 html.futbr-desktop .v548-auth-foot{margin-top:10px!important;padding-top:10px!important;line-height:1.45!important}
}
@media (max-height:760px) and (min-width:841px){
 html.futbr-desktop .v548-auth-brand{padding:18px 22px!important}
 html.futbr-desktop .v548-auth-brand h1{font-size:36px!important;margin:8px 0!important}
 html.futbr-desktop .v548-auth-brand>p{display:none!important}
 html.futbr-desktop .v548-plan-grid{padding-top:8px!important}
 html.futbr-desktop .v548-plan-card ul{font-size:8px!important;line-height:1.3!important}
 html.futbr-desktop .v548-auth-card{padding:16px 22px!important}
}
</style>
'''
    if 'futbr-desktop-auth-green' not in html:
        html=replace_once(html,'</head>',auth_theme+'\\n</head>','green auth theme')

    start_theme=r'''
<style id="futbr-desktop-start-green">
html.futbr-desktop .welcome.v570-career-start{
 --bg:#06140c!important;--panel:#0b2115!important;--panel2:#102d1c!important;--line:#2e6846!important;
 --text:#f2f8f4!important;--muted:#b5cdbd!important;--dim:#7fa18d!important;--accent:#62d88c!important;--accent2:#a8e9bc!important;--gold:#d8d487!important;
 width:100%!important;height:100dvh!important;min-height:0!important;overflow:hidden!important;
 background:radial-gradient(circle at 10% 18%,rgba(73,196,116,.15),transparent 30%),radial-gradient(circle at 86% 82%,rgba(18,116,68,.18),transparent 38%),#06140c!important;
 color:#f2f8f4!important
}
html.futbr-desktop .welcome.v570-career-start .welcome-top{background:transparent!important}
html.futbr-desktop .welcome.v570-career-start .setup-card{
 background:linear-gradient(145deg,rgba(88,211,130,.04),transparent 56%),#0a2014!important;
 border-color:#34794f!important;box-shadow:0 22px 60px rgba(0,0,0,.34)!important
}
html.futbr-desktop .welcome.v570-career-start .v658-career-hero{
 background:radial-gradient(circle at 50% 42%,rgba(74,205,118,.14),transparent 46%),#07180f!important
}
html.futbr-desktop .welcome.v570-career-start .career-mode-card,
html.futbr-desktop .welcome.v570-career-start .v744-financial-field,
html.futbr-desktop .welcome.v570-career-start input,
html.futbr-desktop .welcome.v570-career-start select{
 background:#0b1912!important;border-color:#2d6946!important;color:#f2f8f4!important
}
html.futbr-desktop .welcome.v570-career-start .career-mode-card.active{
 border-color:#5fd78a!important;background:#0c2919!important
}
html.futbr-desktop .welcome.v570-career-start .btn.primary,
html.futbr-desktop .welcome.v570-career-start [data-action="new-career"]{
 background:#58cf80!important;border-color:#58cf80!important;color:#05200f!important
}
html.futbr-desktop .welcome.v570-career-start .v658-career-hero img.futbr125-hero-logo{
 filter:drop-shadow(0 18px 30px rgba(0,0,0,.32))!important
}
</style>
'''
    if 'futbr-desktop-start-green' not in html:
        html=replace_once(html,'</head>',start_theme+'\\n</head>','green start theme')

    performance=r'''
<style id="futbr-desktop-rc-performance-ui">
html.futbr-desktop .futbr-desktop-close-auth{margin-top:14px;padding-top:12px;border-top:1px solid var(--line,#ffffff22)}
html.futbr-desktop .futbr-desktop-close-auth .btn{width:100%;min-height:34px}
</style>
<script id="futbr-desktop-rc-performance-ui">
(()=>{
 if(!window.FutBRDesktop?.available)return;
 const BASE='gestor_fc_mundo_v205_clean',INDEX=BASE+':futbr125:index',PURCHASE_URL='https://futbrmanager.com.br/#planos';
 let nativeSync=null;
 function localGet(key){return openDB().then(db=>new Promise((resolve,reject)=>{const r=db.transaction('saves','readonly').objectStore('saves').get(key);r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);}));}
 function manifestKeys(m){if(!m||m.format!=='GFC_SHARDED_171')return [];return Object.values(m.collections||{}).flatMap(spec=>Array.isArray(spec?.keys)?spec.keys:[]);}
 async function syncActiveSaveToDisk(){
  if(nativeSync)return nativeSync;
  nativeSync=(async()=>{const manifest=await localGet(BASE).catch(()=>null);if(!manifest)return false;const keys=[INDEX,BASE,BASE+':meta',BASE+':previous',...manifestKeys(manifest)],unique=[...new Set(keys)];
   for(let i=0;i<unique.length;i+=6){const entries=[];for(const key of unique.slice(i,i+6)){const value=await localGet(key).catch(()=>undefined);if(value!==undefined)entries.push({key,value});}if(entries.length)await window.FutBRDesktop.writeMany(entries);if(i+6<unique.length)await new Promise(r=>setTimeout(r,0));}return true;})().finally(()=>{nativeSync=null;});
  return nativeSync;
 }
 window.FutBRDesktop.syncActiveSave=syncActiveSaveToDisk;
 document.addEventListener('click',event=>{
  const action=event.target?.closest?.('[data-action]')?.dataset?.action;
  if(action==='futbr125-save-current'||action==='futbr125-save-and-exit')setTimeout(()=>syncActiveSaveToDisk().catch(console.warn),900);
 },true);
 function decorateCloseButton(){const card=document.querySelector('.v548-auth .v548-auth-card');if(!card||card.querySelector('[data-futbr-desktop-close]'))return;card.insertAdjacentHTML('beforeend','<div class="futbr-desktop-close-auth"><button type="button" class="btn ghost" data-futbr-desktop-close="1">Fechar o jogo</button></div>');}
 const mo=new MutationObserver(()=>decorateCloseButton());mo.observe(document.documentElement,{subtree:true,childList:true});decorateCloseButton();
 document.addEventListener('click',event=>{
  if(event.target?.closest?.('[data-futbr-desktop-close]')){event.preventDefault();event.stopImmediatePropagation();Promise.resolve(syncActiveSaveToDisk()).catch(()=>{}).finally(()=>window.FutBRDesktop.closeGame());return;}
  if(event.target?.closest?.('[data-futbr-buy-premium]')){event.preventDefault();event.stopImmediatePropagation();window.FutBRDesktop.openPremium().catch(()=>window.FutBRDesktop.openUrl(PURCHASE_URL)).catch(()=>alert('Acesse https://futbrmanager.com.br/'));}
 },true);
 document.documentElement.dataset.futbrStorage='indexeddb-hot-sqlite-manual-sync';
})();
</script>
'''
    if 'futbr-desktop-rc-performance-ui' not in html:
        html=replace_once(html,'</body>',performance+'\n</body>','performance ui')

    warmup=r'''
<script id="futbr-desktop-crest-warmup">
(()=>{if(!window.FutBRDesktop?.available)return;const seen=new Set(),local=src=>typeof src==='string'&&/^(?:\.\/)?assets\/crests\//.test(src);
function warm(src,p='low'){if(!local(src)||seen.has(src))return;seen.add(src);const i=new Image();try{i.fetchPriority=p}catch(_){}i.decoding='async';i.src=src}
function scan(root=document){root.querySelectorAll?.('img[src]').forEach(i=>warm(i.getAttribute('src')||'','high'))}
const mo=new MutationObserver(ms=>ms.forEach(m=>m.addedNodes.forEach(n=>n.nodeType===1&&scan(n))));addEventListener('DOMContentLoaded',()=>{scan();mo.observe(document.body,{subtree:true,childList:true})},{once:true});})();
</script>
'''
    if 'futbr-desktop-crest-warmup' not in html:
        html=replace_once(html,'</body>',warmup+'\n</body>','crest warmup')

    index_path.write_text(html,encoding="utf-8")
    print("desktop project patched")

if __name__=="__main__":
    main()
