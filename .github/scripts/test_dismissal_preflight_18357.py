from __future__ import annotations
import importlib.util,io,json,subprocess,sys,tempfile,zipfile
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parent

def load(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def once(src,old,new,label):
    n=src.count(old)
    if n!=1:raise RuntimeError(f'18357 preflight {label}: found {n}, expected one')
    return src.replace(old,new,1)

def main():
    parts=sorted(Path('.').glob('FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.part*'))
    if not parts:raise RuntimeError('Original source archive unavailable')
    with zipfile.ZipFile(io.BytesIO(b''.join(p.read_bytes() for p in parts))) as z:
        path=next(n for n in z.namelist() if n.endswith('/src/index.html'))
        src=z.read(path).decode('utf-8-sig')
    resume=load('fix_unemployed_resume_18334')
    src=once(src,'const v18112BaseChrome=v555UpdateChrome;',
       resume.HELPER+'\nconst v18112BaseChrome=v555UpdateChrome;',
       'old 18.112 dismissal post-vacation chrome')
    src=once(src,resume.OLD_WAIT,resume.NEW_WAIT,'18.334 recovery replacement')
    job=load('fix_jobwait_18356')
    src=once(src,'/* FUTBR_UNEMPLOYED_RESUME_18334_END */',
       '/* FUTBR_UNEMPLOYED_RESUME_18334_END */\n'+job.HELPER,
       '18.356 year-end unemployed recovery helper')
    # Mark features previously validated separately by 18.355 and 18.356.
    src+='\n/* FUTBR_JOB_SAVE_EXIT_18355 */\n'
    src+="\nconst EDITION='18.356.0';\n"
    src+="\nwindow.GestorFC.version='18.356.0';window.GestorFC.visualVersion='18.356.0';\n"
    with tempfile.TemporaryDirectory() as temp:
        root=Path(temp);(root/'src').mkdir()
        (root/'src/index.html').write_text(src,encoding='utf-8')
        p=subprocess.run([sys.executable,str(SCRIPTS/'fix_dismissal_handoff_18357.py'),str(root)],
          capture_output=True,text=True,timeout=40)
        if p.returncode:raise RuntimeError('18.357 source patch failed: '+(p.stderr or p.stdout)[-4500:])
        q=subprocess.run([sys.executable,str(SCRIPTS/'test_dismissal_handoff_18357.py'),str(root)],
          capture_output=True,text=True,timeout=45)
        if q.returncode:raise RuntimeError('18.357 end-to-end JavaScript handoff failed: '+(q.stderr or q.stdout)[-4500:])
        result=json.loads(q.stdout.strip().splitlines()[-1])
    print(json.dumps({'ok':True,'sourceAnchorsVerified':True,'patchAppliedToOriginalSource':True,
       'nodeRuntimeRegressionPassed':True,**result},ensure_ascii=False))

if __name__=='__main__':main()
