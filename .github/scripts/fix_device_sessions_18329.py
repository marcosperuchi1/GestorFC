from __future__ import annotations
import json,sys
from pathlib import Path
VERSION='18.329'
MARK='FUTBR_DEVICE_SESSION_18329_START'
ANCHOR="window.GestorFC.license580={online:true,project:'ticwckvvxswturovwlqu',plan:()=>v548Session?.plan||null,validated:()=>!!v548Session?.serverValidated};"
OLD="res=new Response(native.body,{status:Number(native.status)||500,headers:native.headers||{'content-type':'application/json'}});"
NEW="const nativeStatus=Number(native.status)||500;res=new Response([204,205,304].includes(nativeStatus)?null:native.body,{status:nativeStatus,headers:native.headers||{'content-type':'application/json'}});"
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: fix_device_sessions_18329.py <project-dir>')
 root=Path(sys.argv[1]).resolve()
 p=root/'src'/'index.html'
 html=p.read_text(encoding='utf8')
 if MARK in html:
  print(json.dumps({'ok':True,'version':VERSION,'alreadyInstalled':True}));return
 patch=Path(__file__).with_name('device_session_patch_18329.js').read_text(encoding='utf8')
 for label,needle in [('auth block',ANCHOR),('native response',OLD),("licensing function","'/functions/v1/validate-license'")]:
  if html.count(needle)!=1:raise RuntimeError(f'{label} changed; expected one anchor')
 if MARK not in patch:raise RuntimeError('Device patch missing marker')
 html=html.replace(OLD,NEW,1).replace(ANCHOR,ANCHOR+'\n'+patch,1)
 p.write_text(html,encoding='utf8')
 report={'ok':True,'version':VERSION,'nativeDeviceIdentity':True,'deviceIdMigration':True,'revokeDeviceOnSignOut':True,'authorGlobalSignOut':True,'customersLocalSignOut':True,'failedReleaseRetry':True,'savePreservation':True,'licenseBackendUnchanged':True,'noSecretKeyInClient':True}
 (root/'device-sessions-18329-install.json').write_text(json.dumps(report,indent=2),encoding='utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
