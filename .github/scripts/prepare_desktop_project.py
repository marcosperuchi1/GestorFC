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
    nsis=cfg.setdefault("bundle",{}).setdefault("windows",{}).setdefault("nsis",{})
    if nsis.get("installMode")=="perUser":
        nsis["installMode"]="currentUser"
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

'''
        lib=replace_once(lib,"#[tauri::command]\nfn desktop_info",native+"#[tauri::command]\nfn desktop_info","native commands")
        lib=replace_once(
            lib,
            "            kv_commit_manifest,\n            desktop_info,",
            "            kv_commit_manifest,\n            kv_put_many,\n            open_external_url,\n            close_game,\n            desktop_info,",
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
        "  openDataFolder:()=>call('open_data_folder'),\n  writeMany:entries=>call('kv_put_many',{entries:entries||[]}),\n  openUrl:url=>call('open_external_url',{url:String(url)}),\n  closeGame:()=>call('close_game')",
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
  if(event.target?.closest?.('[data-futbr-buy-premium]')){event.preventDefault();event.stopImmediatePropagation();window.FutBRDesktop.openUrl(PURCHASE_URL).catch(()=>alert('Acesse https://futbrmanager.com.br/'));}
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
