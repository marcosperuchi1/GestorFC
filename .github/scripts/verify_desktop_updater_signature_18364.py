from __future__ import annotations
import base64, hashlib, json, re, sys
from pathlib import Path

VERSION='18.364.0'
INSTALLER='FutBR-Manager-18.364-Windows.exe'
FEED='https://download.futbrmanager.com.br/updates/latest.json'

def public_id(wrapped):
    source=base64.b64decode(wrapped.strip(),validate=True).decode('utf-8')
    lines=[line.strip() for line in source.splitlines() if re.fullmatch(r'RW[A-Za-z0-9+/=]+',line.strip())]
    if len(lines)!=1:raise RuntimeError('Updater configuration does not contain exactly one minisign public key')
    decoded=base64.b64decode(lines[0],validate=True)
    if len(decoded)!=42:raise RuntimeError('Malformed updater public key')
    return decoded[2:10]

def signed_id(signature):
    source=signature.strip()
    try:source=base64.b64decode(source,validate=True).decode('utf-8')
    except (ValueError,UnicodeDecodeError):pass
    for line in source.splitlines():
        try:decoded=base64.b64decode(line.strip(),validate=True)
        except ValueError:continue
        if len(decoded)>=74 and decoded[:2] in (b'ED',b'Ed'):
            return decoded[2:10]
    raise RuntimeError('Malformed or missing minisign installer signature')

def main():
    if len(sys.argv)!=2:raise SystemExit('usage: verify_desktop_updater_signature_18364.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
    artifacts=root/'artifacts'
    manifest=json.loads((artifacts/'latest.json').read_text(encoding='utf-8'))
    signature=(artifacts/(INSTALLER+'.sig')).read_text(encoding='utf-8').strip()
    manifest_signature=manifest['platforms']['windows-x86_64']['signature'].strip()
    if manifest.get('version')!=VERSION or cfg.get('version')!=VERSION:
        raise RuntimeError('Packaged Tauri version or manifest is not 18.364')
    if manifest_signature!=signature:raise RuntimeError('Published manifest does not use exactly the built signature')
    updater=cfg.get('plugins',{}).get('updater',{})
    if updater.get('endpoints')!=[FEED]:raise RuntimeError('Updater endpoint has changed')
    if public_id(updater.get('pubkey',''))!=signed_id(signature):
        raise RuntimeError('SECURITY BLOCK: embedded updater public key does not match NSIS installer private signing key')
    if root.joinpath('src-tauri','target','release','bundle','nsis').is_dir() is False:
        raise RuntimeError('Unsigned or missing NSIS build')
    if not manifest['platforms']['windows-x86_64']['url'].startswith('https://download.futbrmanager.com.br/updates/'):
        raise RuntimeError('Updater asset is not HTTPS')
    installer=artifacts/INSTALLER
    digest=hashlib.sha256(installer.read_bytes()).hexdigest()
    if digest!=(artifacts/'SHA256SUMS.txt').read_text(encoding='ascii').strip().split()[0]:
        raise RuntimeError('Installer SHA-256 does not match the checksum manifest')
    for name in ('initial-nationalities-18340-tests.json','scorers-submit-18340-tests.json','desktop-version-18364-install.json','welcome-national-preview-18342-tests.json','season-save-18343-tests.json','career-isolation-18344-tests.json','serie-c-champion-18345-tests.json','retirement-vacation-18346-tests.json','calendar-list-18347-tests.json','calendar-nav-version-18348-tests.json','incremental-saves-calendar-18349-tests.json','calendar-retirement-18350-tests.json','serie-c-phases-history-18351-tests.json','oomsafe-save-18352-tests.json','serie-c-full-history-18353-tests.json','job-save-exit-18355-tests.json','jobwait-season-18356-tests.json','dismissal-handoff-18357-tests.json','dismissal-button-18358-tests.json','dismissal-control-18359-tests.json','vacation-finalize-18360-tests.json','fast-updater-18361-tests.json','native-save-mirror-18354-tests.json','archive-root-shards-18354-tests.json','core-transitions-18362-tests.json','jobwait-state-18363-tests.json','vacation-handoff-18364-tests.json'):
        report=json.loads((artifacts/name).read_text(encoding='utf-8'))
        if not report.get('ok'):raise RuntimeError('Mandatory preserved game regression failed: '+name)
    fast=json.loads((artifacts/'fast-updater-18361-tests.json').read_text(encoding='utf-8'))
    if not all(fast.get(k) for k in ('ok','cachedOnlyTrustedMetadata','saveBeforeInstall','secondHTTPManifestCheckAvoided','liveDownloadPercentage','signedInstallerRemainsOnlyNativePath','noInstallerPrefetch','samePerUserInstaller','progressDoesNotBypassSave','directCDN')):
        raise RuntimeError('18.364 fast updater and career preservation verification missing')
    core=json.loads((artifacts/'core-transitions-18362-tests.json').read_text(encoding='utf-8'))
    if not all(core.get(k) for k in ('ok','outerPromiseRequired','noEarlyUnlock','firstUnemployedDayUsesLiveWorld')):raise RuntimeError('18.364 Worker completion regression failed')
    job=json.loads((artifacts/'jobwait-state-18363-tests.json').read_text(encoding='utf-8'))
    if not all(job.get(k) for k in ('ok','screenshot2027Day42Recovered','loadedUnemployedCareerRecovered',
        'realDayfastUsed','blocksActualWorkerAndSave','stopButtonAccessible')):
        raise RuntimeError('18.364 unemployed job-wait regression failed')
    handoff=json.loads((artifacts/'vacation-handoff-18364-tests.json').read_text(encoding='utf-8'))
    if not all(handoff.get(k) for k in ('ok','screenshot2026Day97Handoff','sendsOriginalWorkerPauseEnd','noSecondWorkerUntilOriginalPromise','automaticJobSearchAfterCheckpoint','failedVacationDoesNotStartWorker','wrongCareerCannotAutoSearch')):
        raise RuntimeError('18.364 actual dismissed-holiday Worker handoff regression failed')
    result={'ok':True,'version':VERSION,'installedUpdaterTrustMatchesSignature':True,
            'installerSha256Verified':True,'manifestSignatureExact':True,'careerSavesPreserved':True,
            'oneTimeManualInstallRequiredForBroken18339And18340':True,
            'publicKeyDerivedFromConfiguredSigner':True}
    (artifacts/'updater-18364-signature-tests.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))

if __name__=='__main__':main()
