from __future__ import annotations

import json
import sys
from pathlib import Path

MARKER = "FUTBR_WELCOME_NATIONAL_PREVIEW_18342"

CSS = r"""
<style id="futbr-18342-national-choice-preview-style">
/* FutBR 18.342: the current national side replaces any previously chosen club.
   7.44/7.46 club-slot sizing styles should never override start-mode state. */
.welcome .setup-card #club-preview.v18342-national-mode {
  display:block!important;visibility:visible!important;opacity:1!important;
  width:100%!important;height:auto!important;min-height:112px!important;max-height:none!important;
  margin:0!important;overflow:hidden!important;
}
.welcome .setup-card #club-preview.v18342-national-mode .v18342-national-choice {
  display:flex!important;align-items:center;gap:15px!important;
  min-height:112px;padding:13px 18px;box-sizing:border-box;width:100%;
}
.welcome .setup-card #club-preview.v18342-national-mode .v18342-national-flag {
  flex:0 0 74px;display:flex;align-items:center;justify-content:center;
  min-width:74px;height:66px;
}
.welcome .setup-card #club-preview.v18342-national-mode .v18342-national-flag img {
  max-width:70px!important;max-height:54px!important;width:auto;height:auto;
  object-fit:contain;
}
.welcome .setup-card #club-preview.v18342-national-mode .preview-info {min-width:0;flex:1;}
.welcome .setup-card #club-preview.v18342-national-mode h3 {
  font-size:17px!important;margin:0 0 6px!important;line-height:1.2!important;
}
.welcome .setup-card #club-preview.v18342-national-mode .v18342-national-meta {
  color:var(--muted,#a3b6b3);font-size:11px;line-height:1.4;
}
.welcome .setup-card #v643-national-preview.v18342-compact-duplicate {
  display:none!important;
}
@media(max-width:760px){
  .welcome .setup-card #club-preview.v18342-national-mode .v18342-national-choice {
    min-height:100px;padding:12px;gap:11px!important;
  }
  .welcome .setup-card #club-preview.v18342-national-mode .v18342-national-flag {
    min-width:58px;flex-basis:58px;height:52px;
  }
}
</style>
"""

JS = r"""
<script id="futbr-18342-national-choice-preview">
/* FUTBR_WELCOME_NATIONAL_PREVIEW_18342
   Presentation-only fix. Keep the selected club in the form so switching
   back restores it; do not touch state, save files, rosters or national squads. */
(()=>{
 'use strict';
 if(typeof renderClubPreview!=='function' ||
    typeof v643ApplyWelcomeMode!=='function' ||
    typeof v643UpdateNationalPreview!=='function')return;
 const originalClubPreview=renderClubPreview;
 const originalApplyMode=v643ApplyWelcomeMode;
 const originalNationalPreview=v643UpdateNationalPreview;
 const originalRenderWelcome=renderWelcome;

 function selectedNational(){
  const root=document.querySelector('.welcome .setup-card');
  if(!root)return null;
  const mode=typeof v643WelcomeMode==='function'?v643WelcomeMode():'club';
  if(mode!=='national')return null;
  const select=root.querySelector('#v643-start-national');
  if(!select)return null;
  const code=String(select.value||'').trim().toUpperCase();
  if(!code)return null;
  const record=typeof v640AssocCatalog==='function'?
    v640AssocCatalog().find(n=>n.code===code):null;
  const fallback=String(select.selectedOptions?.[0]?.textContent||code).trim();
  const name=String(record?.name||fallback||code);
  const conf=String((typeof V640_CONF_NAMES==='object'&&V640_CONF_NAMES?
    V640_CONF_NAMES[record?.conf]:null)||record?.conf||'Seleção nacional');
  const flag=typeof v640Flag==='function'?v640Flag(code,'large'):'';
  return {name,conf,flag,code};
 }
 function syncNationalChoicePreview(){
  const root=document.querySelector('.welcome .setup-card');
  const host=root?.querySelector('#club-preview');
  if(!host)return false;
  const duplicate=root.querySelector('#v643-national-preview');
  let national=null;
  try{national=selectedNational();}catch(e){console.warn('[FutBR 18.342] Preview nacional:',e);}
  if(!national){
   host.classList.remove('v18342-national-mode');
   host.removeAttribute('data-v18342-national');
   duplicate?.classList.remove('v18342-compact-duplicate');
   // Restore the previously selected club when the user returns to club mode.
   if(root.querySelector('#club-select'))originalClubPreview();
   return false;
  }
  host.classList.add('v18342-national-mode');
  host.classList.remove('v643-club-only-hidden','v746-preview-empty');
  host.removeAttribute('aria-hidden');
  host.setAttribute('data-v18342-national',national.code);
  const escapeText=x=>typeof esc==='function'?esc(String(x)):
    String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  host.innerHTML='<div class="club-preview v738-club-preview v742-club-preview v746-selected-preview v18342-national-choice">'+
   '<div class="v18342-national-flag">'+national.flag+'</div>'+
   '<div class="preview-info"><h3>'+escapeText(national.name)+'</h3>'+
   '<div class="v18342-national-meta">'+escapeText(national.conf)+' · Seleção nacional</div>'+
   '</div></div>';
  // The selected national team is now shown in the primary identity card,
  // so the narrow duplicate under the dropdown is unnecessary.
  duplicate?.classList.add('v18342-compact-duplicate');
  return true;
 }
 // Original club-card refresh can run during country/club changes. Do not let
 // it repaint a stale club on top of the selected national team.
 renderClubPreview=function(...args){
  if(typeof v643WelcomeMode==='function'&&v643WelcomeMode()==='national'){
   syncNationalChoicePreview();
   return;
  }
  return originalClubPreview.apply(this,args);
 };
 v643ApplyWelcomeMode=function(...args){
  const result=originalApplyMode.apply(this,args);
  syncNationalChoicePreview();
  return result;
 };
 v643UpdateNationalPreview=function(...args){
  const result=originalNationalPreview.apply(this,args);
  syncNationalChoicePreview();
  return result;
 };
 if(typeof originalRenderWelcome==='function'){
  renderWelcome=function(...args){
   const result=originalRenderWelcome.apply(this,args);
   queueMicrotask(syncNationalChoicePreview);
   return result;
  };
 }
 window.GestorFC=window.GestorFC||{};
 window.GestorFC.welcomePreview18342={
  version:'18.342',nationalReplacesClub:true,
  modeSwitchRestoresClub:true,selectionUpdatesPreview:true,
  sync:syncNationalChoicePreview
 };
})();
</script>
"""

def replace_once(source: str, before: str, after: str, label: str) -> str:
    count=source.count(before)
    if count!=1:
        raise RuntimeError(f"18.342 {label} expected once; found {count}")
    return source.replace(before,after,1)

def main():
    if len(sys.argv)!=2:
        raise SystemExit("usage: fix_welcome_national_preview_18342.py <project-dir>")
    project=Path(sys.argv[1]).resolve()
    index=project/"src/index.html"
    html=index.read_text(encoding="utf-8")
    if MARKER in html:
        raise RuntimeError("18.342 national choice preview is already patched")
    for dependency in ("v643ApplyWelcomeMode", "v643UpdateNationalPreview",
                       "v643-national-preview", "v746-selected-preview",
                       "FUTBR_SIGNED_UPDATER_18339", "FUTBR_SCORER_SEARCH_SUBMIT_18340"):
        if dependency not in html:
            raise RuntimeError("Required 18.341 baseline missing: "+dependency)
    html=replace_once(html,"</head>",CSS+"\n</head>","national card CSS")
    html=replace_once(html,"</body>",JS+"\n</body>","national card behavior")
    index.write_text(html,encoding="utf-8")
    report={"ok":True,"version":"18.342",
      "switchFromClubToNational":True,"removeStaleClubCrest":True,
      "nationUpdatesWithSelector":True,"returnToClubRestoresClubPreview":True,
      "nationalFlagAndNameDisplayed":True,"saveDataModified":False,
      "simulationRulesModified":False,"licenseRulesModified":False}
    (project/"welcome-national-preview-18342-install.json").write_text(
      json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False))

if __name__=="__main__":
    main()
