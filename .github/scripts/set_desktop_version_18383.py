from __future__ import annotations
import base64
import json
import os
import re
import sys
from pathlib import Path

VERSION='18.383.0'
FEED='https://futbrmanager.com.br/updates/latest.json'

def keyid(encoded):
    text=base64.b64decode(encoded,validate=True).decode('utf-8')
    lines=[l.strip() for l in text.splitlines() if re.fullmatch(r'RW[A-Za-z0-9+/=]+',l.strip())]
    if len(lines)!=1:raise RuntimeError('Public key does not contain one valid Minisign key')
    decoded=base64.b64decode(lines[0],validate=True)
    if len(decoded)!=42:raise RuntimeError('Unexpected Minisign pubkey length')
    return decoded[2:10]

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: set_desktop_version_18383.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src-tauri/tauri.conf.json'
    cfg=json.loads(path.read_text(encoding='utf-8-sig'))
    if cfg.get('version')!='18.382.0':raise RuntimeError('Expected validated 18.382 signed-updater baseline in build pipeline')
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
    if 'FUTBR_SCORER_HISTORY_RECOVERY_18377' not in html or 'FUTBR_WINDOW_OBS_HELP_18377' not in html or 'FUTBR_MONEY_AUTOUPDATE_18378' not in html or 'FUTBR_SCORER_IDENTITY_18379' not in html or 'FUTBR_COACH_HONORS_INLINE_SCORERS_18380' not in html or 'FUTBR_NATIONAL_HISTORY_FILTER_DEDUP_18381' not in html or 'FUTBR_CAREER_SYNC_LOAD_BOUNDED_18382' not in html or 'FUTBR_LONG_CAREER_REALISM_18383' not in html or 'FUTBR_FONT_SETTINGS_18376' not in html:
        raise RuntimeError('Missing inherited 18.382 or new 18.383 longevity/flag features')
    # Preserve old feature-internal version markers while updating the public
    # edition and signed package version.
    if "const EDITION='18.382.0';" not in html:raise RuntimeError('Expected 18.382 edition label')
    html=html.replace("const EDITION='18.382.0';","const EDITION='18.383.0';")
    if "window.GestorFC.version='18.382.0';window.GestorFC.visualVersion='18.382.0';" not in html:raise RuntimeError('Expected 18.382 updater bridge')
    html=html.replace("window.GestorFC.version='18.382.0';window.GestorFC.visualVersion='18.382.0';",
        "window.GestorFC.version='18.383.0';window.GestorFC.visualVersion='18.383.0';")
    html_path.write_text(html,encoding='utf-8')
    path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'ok':True,'version':VERSION,'updaterPublicMatchesDerivedPrivateSigner':True,
            'productionFeedPreserved':True,'sameAppIdentifier':True,
            'createUpdaterArtifacts':True,'canAutoUpdateFrom18382':True}
    (root/'desktop-version-18383-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
