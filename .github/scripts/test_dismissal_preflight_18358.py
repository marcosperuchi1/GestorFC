from __future__ import annotations
import importlib.util,io,json,subprocess,sys,tempfile,zipfile
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parent
def mod(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
def one(s,old,new,label):
    count=s.count(old)
    if count!=1:raise RuntimeError(f'18.358 preflight {label}: expected one anchor, got {count}')
    return s.replace(old,new,1)
def main():
    parts=sorted(Path('.').glob('FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.part*'))
    if not parts:raise RuntimeError('Original game archive unavailable')
    with zipfile.ZipFile(io.BytesIO(b''.join(x.read_bytes() for x in parts))) as z:
        f=next(n for n in z.namelist() if n.endswith('/src/index.html'))
        src=z.read(f).decode('utf-8-sig')
    resume=mod('fix_unemployed_resume_18334')
    job=mod('fix_jobwait_18356')
    src=one(src,'const v18112BaseChrome=v555UpdateChrome;',
            resume.HELPER+'\nconst v18112BaseChrome=v555UpdateChrome;',
            '18.334 helper')
    src=one(src,resume.OLD_WAIT,resume.NEW_WAIT,'18.334 waiting guard')
    src=one(src,'/* FUTBR_UNEMPLOYED_RESUME_18334_END */',
            '/* FUTBR_UNEMPLOYED_RESUME_18334_END */\n'+job.HELPER,
            '18.356 recovery helper')
    src=one(src,'function v18334ShouldWait(){',
            'function v18334ShouldWait(){\n v18356ReconcileRollover();',
            '18.356 old wait handler')
    src=one(src,'async function v89RunJobWait(){',
            'async function v89RunJobWait(){\n v18356ReconcileRollover();',
            '18.356 original job-wait entry')
    src+='\n/* FUTBR_JOB_SAVE_EXIT_18355 */\n'
    src+="\nconst EDITION='18.356.0';\n"
    src+="window.GestorFC.version='18.356.0';window.GestorFC.visualVersion='18.356.0';\n"
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);(root/'src').mkdir()
        (root/'src/index.html').write_text(src,encoding='utf-8')
        for script in ['fix_dismissal_handoff_18357.py','fix_dismissal_button_18358.py',
                       'test_dismissal_button_18358.py']:
            p=subprocess.run([sys.executable,str(SCRIPTS/script),str(root)],
                             capture_output=True,text=True,timeout=55)
            if p.returncode:raise RuntimeError('18.358 preflight '+script+' failed: '+(p.stderr or p.stdout)[-6000:])
        report=json.loads((root/'dismissal-button-18358-tests.json').read_text(encoding='utf-8'))
    print(json.dumps({'ok':True,'appliedToOriginalGameSource':True,
      'previous18357HandoffRetained':True,'nodeRegressionPassed':True,
      **report},ensure_ascii=False))
if __name__=='__main__':main()
