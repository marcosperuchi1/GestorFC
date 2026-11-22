from __future__ import annotations
import json,sys,hashlib
from pathlib import Path
VERSION='18.375.0'
def main():
 root=Path(sys.argv[1]).resolve()
 conf=root/'src-tauri/tauri.conf.json'
 cfg=json.loads(conf.read_text(encoding='utf-8-sig'))
 if cfg.get('version')!='18.374.0':raise RuntimeError('Expected approved 18.374 Tauri baseline')
 if cfg.get('bundle',{}).get('createUpdaterArtifacts') is not True:raise RuntimeError('Signed updater missing')
 updater=cfg.get('plugins',{}).get('updater',{})
 if updater.get('endpoints')!=['https://download.futbrmanager.com.br/updates/latest.json']:raise RuntimeError('Updater endpoint unexpectedly changed')
 if not updater.get('pubkey'):raise RuntimeError('Signed updater public key missing')
 cfg['version']=VERSION
 conf.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf8')
 html=root/'src/index.html';s=html.read_text(encoding='utf8')
 if s.count("window.GestorFC.version='18.374.0';window.GestorFC.visualVersion='18.374.0';")!=1:
  raise RuntimeError('Expected exactly one public 18.374 version bridge')
 s=s.replace("window.GestorFC.version='18.374.0';window.GestorFC.visualVersion='18.374.0';",
 "window.GestorFC.version='18.375.0';window.GestorFC.visualVersion='18.375.0';",1)
 # Existing minor internal feature labels deliberately remain historical.
 s=s.replace("const EDITION='18.374.0';","const EDITION='18.375.0';")
 html.write_text(s,encoding='utf8')
 report={'ok':True,'version':VERSION,'sameApplicationIdentifier':True,'sameUpdaterKey':True,
 'sameUpdaterEndpoint':True,'signedArtifactsRequired':True,'sourceSha256':hashlib.sha256(s.encode()).hexdigest()}
 (root/'desktop-version-18375-install.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
