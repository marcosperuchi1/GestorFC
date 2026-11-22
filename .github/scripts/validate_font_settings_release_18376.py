"""Fail-closed checks for the 18.376 typography-only Windows update."""
from pathlib import Path
import hashlib,json,subprocess,sys
from validate_support_release_18375 import extract_executable_scripts

VERSION='18.376.0'
REQUIRED={
 'font-settings-18376-install.json':(
  'ok','fontOnlyNoGlobalZoom','oneExistingSettingsPage',
  'noAdditionalSidebarButton','modeWindowAndFullscreenInExistingSettings',
  'legacyFontPreferenceReused','other18375SupportFixesPreserved','saveAndWorldNotTouched'),
 'font-settings-18376-tests.json':(
  'ok','existingSettingsOnly','originalSettingsAndLanguageRemain',
  'originalNavigationPreserved','legacy125PreferenceRestoredWithoutGlobalZoom',
  'normalRestoresOriginalFonts','font120ScalesOnlyText',
  'sidebarAndGridWidthsUnchanged','fullscreenAndWindowButtonsWork',
  'savesPreferenceWithoutTouchingCareer','rerenderDoesNotDuplicateControls',
  'previousSupportMoneyAndTooltipHooksPresent','noBrowserErrors')
}
def verify_release_reports(project,artifacts=None):
 root=Path(project).resolve()
 source=(root/'src/index.html').read_text(encoding='utf-8')
 cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf-8'))
 if cfg.get('version')!=VERSION:raise RuntimeError('Tauri package version does not match 18.376')
 for mark in ('FUTBR_FONT_SETTINGS_18376','FUTBR_SUPPORT_UI_18375',
              'FUTBR_TRANSFER_INTEREST_18375','FUTBR_CALENDAR_TRANSLATIONS_18375',
              'FUTBR_UNEMPLOYED_CALENDAR_18374','FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN'):
  if mark not in source:raise RuntimeError('Mandatory prior game feature missing: '+mark)
 for old in ('document.documentElement.style.zoom=','v375Open()','.v375-open','v375-overlay'):
  if old in source:raise RuntimeError('Broken global zoom/duplicate menu still exists: '+old)
 if source.count("window.GestorFC.version='18.376.0';window.GestorFC.visualVersion='18.376.0';")!=1:
  raise RuntimeError('Game UI does not expose same version as signed package')
 if cfg.get('plugins',{}).get('updater',{}).get('endpoints')!=['https://download.futbrmanager.com.br/updates/latest.json']:
  raise RuntimeError('Automatic updater endpoint changed')
 if cfg.get('bundle',{}).get('createUpdaterArtifacts') is not True:
  raise RuntimeError('Signed update artifacts generation disabled')
 directories=[Path(artifacts).resolve()] if artifacts else []
 directories.append(root)
 checks={}
 for name,fields in REQUIRED.items():
  path=next((d/name for d in directories if (d/name).is_file()),None)
  if path is None:raise RuntimeError('Mandatory font settings test report missing: '+name)
  report=json.loads(path.read_text(encoding='utf-8'))
  if report.get('version')!=VERSION or any(report.get(k) is not True for k in fields):
   raise RuntimeError('Font/settings regression did not pass: '+name)
  checks[name]=True
 scripts,ignored=extract_executable_scripts(source)
 if len(scripts)<129:raise RuntimeError('Executable source script count unexpectedly reduced')
 verify=subprocess.run(['node','-e',
  'const vm=require("vm"),fs=require("fs");JSON.parse(fs.readFileSync(0,"utf8")).forEach((s,i)=>new vm.Script(s,{filename:"script-"+i+".js"}));'],
  input=json.dumps(scripts),text=True,capture_output=True,timeout=120)
 if verify.returncode:raise RuntimeError('JavaScript syntax check failed: '+verify.stderr[-4000:])
 oldreport=root/'support-release-18375-tests.json'
 if not oldreport.is_file() and artifacts:
  oldreport=Path(artifacts)/'support-release-18375-tests.json'
 if not oldreport.is_file():raise RuntimeError('Preserved 18.375 support checks unavailable')
 old=json.loads(oldreport.read_text(encoding='utf-8'))
 if old.get('ok') is not True:raise RuntimeError('18.375 tests were not preserved')
 result={'ok':True,'version':VERSION,'fontOnlyNoGlobalZoom':True,
         'singleNativeSettingsScreen':True,'gameSavesUntouched':True,
         'sameUpdaterIdentity':True,'existingBrowserPreferenceMigrated':True,
         'allBrowserAssertionsPassed':True,'priorSupportTestsPreserved':True,
         'executableScripts':len(scripts),'inertDataScripts':ignored,
         'sourceSha256':hashlib.sha256(source.encode('utf-8')).hexdigest(),
         'checks':checks}
 (root/'font-settings-release-18376-tests.json').write_text(
  json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(result,ensure_ascii=False))
 return result

if __name__=='__main__':
 if len(sys.argv)!=2:raise SystemExit('usage: validate_font_settings_release_18376.py <root>')
 verify_release_reports(sys.argv[1])
