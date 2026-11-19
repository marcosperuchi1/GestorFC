from __future__ import annotations
import importlib.util,io,json,subprocess,sys,tempfile,zipfile
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parent

def mod(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj

def one(src,old,new,what):
    n=src.count(old)
    if n!=1:raise RuntimeError(f'Preflight {what}: found {n}, expected 1')
    return src.replace(old,new,1)

def main():
    parts=sorted(Path('.').glob('FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.part*'))
    if not parts:raise RuntimeError('Source archive parts absent')
    with zipfile.ZipFile(io.BytesIO(b''.join(p.read_bytes() for p in parts))) as z:
        name=next(n for n in z.namelist() if n.endswith('/src/index.html'))
        s=z.read(name).decode('utf-8-sig')
    s=one(s,"const compactHumanMatch=!!manualOverlaySnapshot;",
          "const compactHumanMatch=!!manualOverlaySnapshot,v18311LiveVacation=mode==='vacation'&&!!options?.liveStateNoPreSave;",
          '18.311 live-state selector')
    s=one(s,
      "const canLoadSaved=!!saveOK&&(mode==='day'||mode==='dayfast'||mode==='nationaljump'||mode==='nextmatch'||mode==='vacation');",
      "const canLoadSaved=!v18311LiveVacation&&!!saveOK&&(mode==='day'||mode==='dayfast'||mode==='nationaljump'||mode==='nextmatch'||mode==='vacation');",
      '18.311 live-state load')
    s=one(s,
      "async function v89RunJobWait(){",
      "async function v89RunJobWait(){",
      'unemployed action scope')
    s=one(s,
      "await v53StartSimulation('day');",
      "await v53StartSimulation('dayfast');",
      '18.327 fast job-wait route')
    s=one(s,
      "if((mode==='day'||mode==='vacation')&&state){if(mode==='day')v636AfterRound(state,before);",
      "if((mode==='day'||mode==='dayfast'||mode==='vacation')&&state){if(mode==='day'||mode==='dayfast')v636AfterRound(state,before);",
      '18.327 offer hook')
    resume=mod('fix_unemployed_resume_18334')
    s=one(s,"const v18112BaseChrome=v555UpdateChrome;",
      resume.HELPER+"\nconst v18112BaseChrome=v555UpdateChrome;",
      '18.334 unemployed recovery helper')
    s=one(s,resume.OLD_WAIT,resume.NEW_WAIT,'18.334 guard')
    # The 18.311 pipeline inserts the fast block ahead of the 18.168
    # rollover fallback. Preflight reproduces the exact text anchor being
    # patched; the full build separately validates the 18.311 implementation.
    s=one(s,
      'const v168BaseStartSimulation=v53StartSimulation;',
      "const v168BaseStartSimulation=v53StartSimulation;\n/* 18.311 preflight marker */\nif(v168DeferredRolloverSave&&state&&mode==='vacation'){}",
      '18.311 deferred vacation branch anchor')
    s+='\n/* FUTBR_UNEMPLOYED_TURBO_18327 */\n'
    s+='\n/* FUTBR_LONG_CAREER_SAVE_18338_BEGIN */\n'
    s+='\n/* FUTBR_JOB_SAVE_EXIT_18355 */\n'
    s+="\nconst EDITION='18.355.0';\n"
    s+="window.GestorFC.version='18.355.0';window.GestorFC.visualVersion='18.355.0';\n"
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);(root/'src').mkdir()
        (root/'src'/'index.html').write_text(s,encoding='utf-8')
        p=subprocess.run([sys.executable,str(SCRIPTS/'fix_jobwait_18356.py'),str(root)],
              capture_output=True,text=True,timeout=45)
        if p.returncode:raise RuntimeError('18.356 patch failed: '+(p.stderr or p.stdout)[-4000:])
        t=subprocess.run([sys.executable,str(SCRIPTS/'test_jobwait_18356.py'),str(root)],
              capture_output=True,text=True,timeout=50)
        if t.returncode:raise RuntimeError('18.356 runtime regression failed: '+(t.stderr or t.stdout)[-4000:])
        report=json.loads(t.stdout.strip().splitlines()[-1])
    print(json.dumps({'ok':True,'sourceAnchorsPresent':True,'patchApplied':True,
      'runTimeNodeHarness':True,**report},ensure_ascii=False))

if __name__=='__main__':main()
