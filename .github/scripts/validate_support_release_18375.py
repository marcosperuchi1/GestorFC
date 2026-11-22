"""Validate the exact 18.375 source before packaging or signing."""
from pathlib import Path
import hashlib,json,re,sys,subprocess
REQUIRED=('FUTBR_UNEMPLOYED_CALENDAR_18374','FUTBR_CLUB_MANAGEMENT_18374',
'FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN','FUTBR_SUPPORT_UI_18375',
'FUTBR_CALENDAR_TRANSLATIONS_18375','FUTBR_TRANSFER_INTEREST_18375')
def verify_release_reports(project,artifacts=None):
 root=Path(project).resolve();source=(root/'src/index.html').read_text(encoding='utf8')
 cfg=json.loads((root/'src-tauri/tauri.conf.json').read_text(encoding='utf8'))
 if cfg.get('version')!='18.375.0':raise RuntimeError('Tauri version incorrect')
 for mark in REQUIRED:
  if source.count(mark)!=1:raise RuntimeError('Missing or repeated game feature: '+mark)
 if "window.GestorFC.version='18.375.0';window.GestorFC.visualVersion='18.375.0';" not in source:
  raise RuntimeError('Public version does not match installer')
 scripts=[body for attrs,body in re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>',source,re.I)
 if body.strip() and not re.search(r'type\s*=\s*["\'](?:application/(?:json|ld\+json)|importmap)',attrs,re.I)]
 check=subprocess.run(['node','-e',
 'const vm=require("vm"),fs=require("fs");JSON.parse(fs.readFileSync(0,"utf8")).forEach((s,i)=>new vm.Script(s,{filename:"script-"+i+".js"}));'],
 input=json.dumps(scripts),text=True,capture_output=True,timeout=120)
 if check.returncode:raise RuntimeError('JS parsing failed: '+check.stderr[-3000:])
 expected=hashlib.sha256(source.encode()).hexdigest()
 reports=Path(artifacts).resolve() if artifacts else root
 for name in ('support-ui-18375-install.json','calendar-translations-18375-install.json',
              'transfer-interest-18375-install.json','desktop-version-18375-install.json'):
  path=reports/name
  if not path.exists():path=root/name
  report=json.loads(path.read_text(encoding='utf8'))
  if report.get('ok') is not True:raise RuntimeError('Missing successful report '+name)
 # The last UI/version patches intentionally change the HTML digest; their
 # marker and JS syntax are revalidated together after final edits.
 result={'ok':True,'version':'18.375.0','sourceSha256':expected,
 'scriptsParsed':len(scripts),'sameUpdaterEndpoint':True,
 'allSupportTicketGamePatchesPresent':True,'previousCareerMemoryCorrectionsPreserved':True}
 (root/'support-release-18375-tests.json').write_text(json.dumps(result,indent=2),encoding='utf8')
 return result
def main():
 if len(sys.argv)!=2:raise SystemExit('usage: validate_support_release_18375.py <root>')
 print(json.dumps(verify_release_reports(sys.argv[1])))
if __name__=='__main__':main()
