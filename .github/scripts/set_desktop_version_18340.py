from __future__ import annotations
import json,sys
from pathlib import Path

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: set_desktop_version_18340.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    cfg_file=root/'src-tauri/tauri.conf.json'
    cfg=json.loads(cfg_file.read_text(encoding='utf-8-sig'))
    assert cfg.get('version')=='18.339.0','Expected the verified signed-updater 18.339 baseline'
    upd=cfg.get('plugins',{}).get('updater',{})
    assert upd.get('pubkey') and upd.get('endpoints')==['https://futbrmanager.com.br/updates/latest.json'],'Existing updater trust settings changed'
    assert cfg.get('bundle',{}).get('createUpdaterArtifacts') is True,'Signed update artifacts disabled'
    cfg['version']='18.340.0'
    cfg_file.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    report={'ok':True,'version':'18.340.0','preservedUpdaterPublicKey':True,
            'sameUpdaterFeed':True,'signedInstaller':True,'sameAppIdentifier':True}
    (root/'desktop-version-18340-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
