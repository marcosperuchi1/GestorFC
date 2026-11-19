from __future__ import annotations
import importlib.util
import io
import json
import pathlib
import subprocess
import sys
import tempfile
import zipfile

SCRIPTS=pathlib.Path(__file__).resolve().parent

def load(name):
    path=SCRIPTS/(name+'.py')
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def main():
    # Run before a costly Windows installation build. Source fixture is
    # reconstructed from the shipped archive, using the verified 18.338
    # checkpoint-aware saver (not the obsolete 18.125 save implementation).
    parts=sorted(pathlib.Path('.').glob('FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.part*'))
    if not parts:raise RuntimeError('Missing source archive')
    with zipfile.ZipFile(io.BytesIO(b''.join(p.read_bytes() for p in parts))) as archive:
        file=next(n for n in archive.namelist() if n.endswith('/src/index.html'))
        src=archive.read(file).decode('utf-8-sig')
    def section(a,b):
        i=src.index(a);j=src.index(b,i)
        return src[i:j]
    offer=section('function v636GenerateCoachOffer(s,afterUserMatch=false){','function v636CoachOfferModal(')
    jobs=section('function availableJobs(s){','function takeJob(s,id){')
    checkpoint=load('optimize_long_career_saves_18338').NEW_ENSURE
    fixture='\n'.join([
        '/* FUTBR_NATIVE_MIRROR_18354 */',
        '/* FUTBR_UNEMPLOYED_TURBO_18327 */',
        '/* FUTBR_UNEMPLOYED_RESUME_18334_BEGIN */',
        '/* FUTBR_OOMSAFE_ARCHIVE_18352 */',
        jobs,'function takeJob(s,id){}',
        offer,'function v636CoachOfferModal(){}',
        checkpoint,'async function archiveCurrent(){}',
        "const EDITION='18.354.0';",
        "window.GestorFC.version='18.354.0';window.GestorFC.visualVersion='18.354.0';"
    ])
    with tempfile.TemporaryDirectory() as temp:
        root=pathlib.Path(temp)
        (root/'src').mkdir()
        (root/'src'/'index.html').write_text(fixture,encoding='utf-8')
        proc=subprocess.run([sys.executable,str(SCRIPTS/'fix_job_saveexit_18355.py'),str(root)],
                            capture_output=True,text=True,timeout=40)
        if proc.returncode:raise RuntimeError('18355 patch fixture failed: '+proc.stderr[-2500:])
        verify=subprocess.run([sys.executable,str(SCRIPTS/'test_job_saveexit_18355.py'),str(root)],
                              capture_output=True,text=True,timeout=40)
        if verify.returncode:raise RuntimeError('18355 runtime regression: '+(verify.stderr or verify.stdout)[-4000:])
        result=json.loads(verify.stdout.strip().splitlines()[-1])
    print(json.dumps({'ok':True,'patchMatchesActual18338Saver':True,**result}))

if __name__=='__main__':main()
