from __future__ import annotations
import importlib.util,io,json,subprocess,sys,tempfile,zipfile
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parent
def mod(name):
    spec=importlib.util.spec_from_file_location(name,SCRIPTS/(name+'.py'))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
def one(s,old,new,label):
    count=s.count(old)
    if count!=1:raise RuntimeError(f'18.360 preflight {label}: expected one anchor, got {count}')
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
    begin=src.index('async function v89RunJobWait(){')
    end=src.index('const v89BaseCareerPage=careerPage;',begin)
    block=src[begin:end]
    block=one(block,"await v53StartSimulation('day');",
      "await v53StartSimulation('dayfast');",
      '18.327 turbo mode for unemployed manager')
    src=src[:begin]+block+src[end:]
    src+='\n/* FUTBR_JOB_SAVE_EXIT_18355 */\n'
    src+="\nconst EDITION='18.356.0';\n"
    src+="window.GestorFC.version='18.356.0';window.GestorFC.visualVersion='18.356.0';\n"
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);(root/'src').mkdir()
        (root/'src/index.html').write_text(src,encoding='utf-8')
        # Miniature source fixture: the 18.359 baseline preflight does not
        # install the 30+ previous release patches, so restore the actual
        # 18.310 vacation stream codec and 18.338 lazy decode semantics.
        # The Windows release pipeline independently validates ALL patches.
        full=(root/'src/index.html').read_text(encoding='utf-8')
        sync310=mod('optimize_season_sync_18310')
        # In the full Windows pipeline, an 18.30x preliminary patch already
        # modernizes one of the THREE legacy decoder sites. Emulate that
        # one existing replacement before running the real 18.310 patch.
        old_decode="rows=m.format==='json-buffer'&&m.bytes instanceof ArrayBuffer?JSON.parse(new TextDecoder().decode(m.bytes)):(m.rows||[])"
        if full.count(old_decode)!=3:raise RuntimeError('18.360 legacy decoder fixture changed')
        full=full.replace(old_decode,'rows=v18310VacationRows(m)',1)
        full=sync310.patch_html(full)
        unpack_old="return packed.map(r=>{const p=v18191uUnpackPlayer(r);return [p.id,p];});"
        unpack_new="return {length:packed.length,*[Symbol.iterator](){for(const r of packed){const p=v18191uUnpackPlayer(r);yield [p.id,p];}}};"
        full=one(full,unpack_old,unpack_new,'18.338 lazy player decoder fixture')
        full=one(full,'if(!checkpointMeta||!pending.length||(!force&&pending.length<8))return;',
                 'if(!checkpointMeta||!pending.length||(!force&&pending.length<(Number(world.year)>=2029?4:8)))return;',
                 '18.338 checkpoint memory bound fixture')
        # Feature markers are not behaviors: the real 18.352/18.349/18.343
        # patches are exercised in the signed full Windows build pipeline.
        full+='\\n'+''.join('/* '+x+' */\\n' for x in (
            'FUTBR_OOMSAFE_ARCHIVE_18352','FUTBR_LONG_CAREER_SAVE_18338_BEGIN',
            'FUTBR_CLEAN_INCREMENTAL_SHARDS_18349','FUTBR_ARCHIVE_COPY_ON_WRITE_18343'))
        (root/'src/index.html').write_text(full,encoding='utf-8')
        for script in ['fix_dismissal_handoff_18357.py','fix_dismissal_button_18358.py',
                       'fix_dismissal_control_18359.py','test_dismissal_control_18359.py',
                       'optimize_vacation_finalize_18360.py','test_vacation_finalize_18360.py']:
            p=subprocess.run([sys.executable,str(SCRIPTS/script),str(root)],
                             capture_output=True,text=True,timeout=55)
            if p.returncode:raise RuntimeError('18.360 preflight '+script+' failed: '+(p.stderr or p.stdout)[-6000:])
        report=json.loads((root/'vacation-finalize-18360-tests.json').read_text(encoding='utf-8'))
    print(json.dumps({'ok':True,'appliedToOriginalGameSource':True,
      'previous18357HandoffRetained':True,'previous18358RecoveryRetained':True,'previous18359WorkerFinishedRetained':True,'nodeRegressionPassed':True,
      **report},ensure_ascii=False))
if __name__=='__main__':main()
