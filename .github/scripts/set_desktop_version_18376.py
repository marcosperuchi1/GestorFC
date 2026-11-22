from __future__ import annotations
import base64
import json
import os
import re
import sys
from pathlib import Path

VERSION='18.376.0'
FEED='https://futbrmanager.com.br/updates/latest.json'

def keyid(encoded):
    text=base64.b64decode(encoded,validate=True).decode('utf-8')
    lines=[l.strip() for l in text.splitlines() if re.fullmatch(r'RW[A-Za-z0-9+/=]+',l.strip())]
    if len(lines)!=1:raise RuntimeError('Public key does not contain one valid Minisign key')
    decoded=base64.b64decode(lines[0],validate=True)
    if len(decoded)!=42:raise RuntimeError('Unexpected Minisign pubkey length')
    return decoded[2:10]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: set_desktop_version_18376.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src-tauri/tauri.conf.json'
    cfg=json.loads(path.read_text(encoding='utf-8-sig'))
    if cfg.get('version')!='18.375.0':raise RuntimeError('Expected validated 18.375 signed-updater baseline in build pipeline')
    updater=cfg.get('plugins',{}).get('updater',{})
    expected=os.environ.get('FUTBR_UPDATER_PUBLIC_KEY','').strip()
    if not expected:raise RuntimeError('Derived public key must be provided by signed CI preflight')
    if keyid(expected)!=keyid(updater.get('pubkey','')):
        raise RuntimeError('Source updater config is not using derived signer public key')
    if updater.get('endpoints')!=['https://download.futbrmanager.com.br/updates/latest.json']:
        raise RuntimeError('Do not change the production signed updater endpoint')
    if cfg.get('bundle',{}).get('createUpdaterArtifacts') is not True:
        raise RuntimeError('Missing signed updater artifact generation')
    cfg['version']=VERSION
    html_path=root/'src/index.html'
    html=html_path.read_text(encoding='utf-8')
    if 'FUTBR_FONT_SETTINGS_18376' not in html or 'FUTBR_SUPPORT_UI_18375' not in html or 'FUTBR_TRANSFER_INTEREST_18375' not in html:
        raise RuntimeError('Missing new 18.375 features')
    # Preserve old feature-internal version markers while updating the public
    # edition and signed package version.
    if "const EDITION='18.375.0';" not in html:raise RuntimeError('Expected the 18.375 edition label')
    html=html.replace("const EDITION='18.375.0';","const EDITION='18.376.0';")
    if "window.GestorFC.version='18.375.0';window.GestorFC.visualVersion='18.375.0';" not in html:raise RuntimeError('Expected 18.375 visible updater bridge')
    html=html.replace("window.GestorFC.version='18.375.0';window.GestorFC.visualVersion='18.375.0';",
        "window.GestorFC.version='18.376.0';window.GestorFC.visualVersion='18.376.0';")
    html_path.write_text(html,encoding='utf-8')
    path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'ok':True,'version':VERSION,'updaterPublicMatchesDerivedPrivateSigner':True,
            'productionFeedPreserved':True,'sameAppIdentifier':True,
            'createUpdaterArtifacts':True,'canAutoUpdateFrom18375':True}
    (root/'desktop-version-18376-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
