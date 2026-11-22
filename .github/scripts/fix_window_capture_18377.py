"""Enable Tauri fullscreen/window toggle and compact large-font settings."""
from pathlib import Path
import hashlib,json,subprocess,sys
MARK='FUTBR_WINDOW_OBS_HELP_18377'
RULES=r'''
/* FUTBR_WINDOW_OBS_HELP_18377 */
.v622-settings-page .panel-head{padding:11px 15px!important;gap:8px}
.v622-settings-page .panel-body{padding:10px 12px!important}
.v622-settings-page .v622-settings-grid{gap:8px!important;align-items:start}
.v622-settings-page .v622-setting-card{padding:11px 13px!important;min-height:0!important}
.v622-settings-page .v622-setting-card h3{margin:0 0 4px!important;line-height:1.22!important}
.v622-settings-page .v622-setting-card p{margin:3px 0 8px!important;line-height:1.3!important}
.v622-settings-page .v622-setting-card .field{margin-top:6px!important;gap:3px!important}
.v622-settings-page .v376-display-card .v376-mode-actions{margin-top:3px!important;gap:6px!important}
.v622-settings-page .v376-display-card .v376-mode-actions button{padding:6px 9px!important}
.v622-settings-page .v376-obs-guidance{margin:6px 0 0!important;max-width:100%;line-height:1.25!important;color:var(--muted)}
@media(min-width:780px){.v622-settings-page{max-height:calc(100dvh - 86px);overflow-y:auto;overscroll-behavior:contain;scrollbar-gutter:stable}}
@media(max-width:780px){.v622-settings-page .v622-settings-grid{grid-template-columns:minmax(0,1fr)!important}}
'''
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_window_capture_18377.py <prepared-root>')
 root=Path(sys.argv[1]).resolve();cap=root/'src-tauri/capabilities/default.json'
 data=json.loads(cap.read_text(encoding='utf-8-sig'))
 if data.get('windows')!=['main']:raise RuntimeError('Unexpected capability window scope')
 permissions=data.get('permissions',[])
 for permission in ('core:window:allow-set-fullscreen','core:window:allow-is-fullscreen'):
  if permission not in permissions:permissions.append(permission)
 data['permissions']=permissions
 cap.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 path=root/'src/index.html';html=path.read_text(encoding='utf-8')
 if MARK in html:raise RuntimeError('Already patched 18.377 window capture')
 if html.count('v375Style.textContent=`')!=1:raise RuntimeError('Existing Settings CSS injection changed')
 html=html.replace('v375Style.textContent=`','v375Style.textContent=`'+RULES,1)
 anchor=' <p class="tiny muted v376-mode-status" role="status" aria-live="polite"></p></div>`;' 
 if html.count(anchor)!=1:raise RuntimeError('Expected Window/fullscreen Settings card')
 helptext=' <p class="tiny muted v376-obs-guidance">Para lives no OBS: escolha <strong>Captura de janela</strong>, selecione <strong>FutBR Manager</strong> e experimente o método <strong>Windows 10/11 (1903+)</strong>. Não use Captura de jogo para esta janela WebView2.</p>'
 html=html.replace(anchor,' <p class="tiny muted v376-mode-status" role="status" aria-live="polite"></p>'+helptext+'</div>`;',1)
 js_check=subprocess.run(['node','--check','-'],input='const example=`'+RULES+'`;',text=True,capture_output=True)
 if js_check.returncode:raise RuntimeError('CSS string parsing failed: '+js_check.stderr)
 path.write_text(html,encoding='utf-8')
 report={'ok':True,'version':'18.377.0','aclPermission':'core:window:allow-set-fullscreen',
         'scopeOnlyMainWindow':True,'previousAclPreserved':True,'windowToggleNowAuthorized':True,
         'obsWindowCaptureInstructionsVisible':True,'obsActualCaptureNotClaimed':True,
         'settingsCardPaddingCompacted':True,'mobileLayoutPreserved':True,
         'sha256':hashlib.sha256(html.encode()).hexdigest()}
 (root/'window-capture-18377-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
