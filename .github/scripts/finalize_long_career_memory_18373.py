"""Finalize the integrated 18.373 edition after the memory corrections."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


def finalize(source: str) -> tuple[str, dict]:
    markers = [
        'FUTBR_VACATION_DURABLE_CHECKPOINT_18373',
        'FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN',
        'FUTBR_PACKED_ARCHIVE_PATHS_18373',
        'FUTBR_VACATION_HISTORY_WRITER_18373',
        'FUTBR_JOBWAIT_SINGLE_OWNER_18373',
        'FUTBR_JOBWAIT_PARTIAL_UI_GUARDS_18373',
        'FUTBR_VACATION_BOUNDED_BOOT_18373',
        'FUTBR_PLAYER_CHECKPOINT_REUSE_18373',
        'FUTBR_PLAYER_FAST_SHAPES_18373',
        'FUTBR_CAREER_PROMOTION_OFFERS_18372',
        'FUTBR_NATIVE_CONFIRMATIONS_18372_BEGIN',
    ]
    for marker in markers:
        if marker not in source:
            raise RuntimeError('18.373 integrated source is missing ' + marker)
    # All three shipped codecs must build the decoded object in one operation.
    # Runtime shape and legacy roundtrip assertions live in the reuse unit.
    for prefix in ('v18191w', 'v18191u', 'v18191m'):
        signature = f'function {prefix}UnpackPlayer(r){{'
        match = re.search(rf'function {prefix}UnpackPlayer\(r\)\{{([\s\S]*?)\n\}}', source)
        if source.count(signature) != 1 or not match or any(fragment not in match.group(1) for fragment in (
                'FUTBR_PLAYER_FAST_SHAPES_18373', 'return Object.fromEntries(entries);')):
            raise RuntimeError('18.373 fast player decoder is missing or duplicated: ' + prefix)
    for marker in ['TEST_ONLY_LONG_CAREER_MEMORY_18373', 'TEST_ONLY_NAMED_MEMORY_18373',
                   'TEST_ONLY_PROMOTION_FLOW_18372', 'TEST_ONLY_NATIVE_CONFIRMATIONS_18372',
                   'TEST_ONLY_PLAYER_CHECKPOINT_REUSE_18373']:
        if marker in source:
            raise RuntimeError('A test fixture must never be shipped: ' + marker)
    if "const EDITION='18.373.0';" not in source:
        old = "const EDITION='18.372.0';"
        if source.count(old) != 1:
            raise RuntimeError('Expected the approved 18.372 edition before finalization')
        source = source.replace(old, "const EDITION='18.373.0';", 1)
        old = "window.GestorFC.version='18.372.0';window.GestorFC.visualVersion='18.372.0';"
        if source.count(old) != 1:
            raise RuntimeError('Expected the approved 18.372 visual edition')
        source = source.replace(old,
            "window.GestorFC.version='18.373.0';window.GestorFC.visualVersion='18.373.0';", 1)
    ui_start = source.index('let state=null,saved=null')
    ui_end = source.index('</script>', ui_start)
    runtime = source.index('/* FUTBR_SAVE_MEMORY_RUNTIME_18373_BEGIN')
    owner = source.index('/* FUTBR_JOBWAIT_SINGLE_OWNER_18373\n')
    guards = source.index('/* FUTBR_JOBWAIT_PARTIAL_UI_GUARDS_18373 */')
    boot = source.index('/* FUTBR_VACATION_BOUNDED_BOOT_18373 */')
    if not ui_start < boot < owner < runtime < guards < ui_end:
        raise RuntimeError('The new runtime/ownership/guards are outside the real career closure')
    scripts = []
    for attrs, body in re.findall(r'<script\b([^>]*)>([\s\S]*?)</script>', source, flags=re.I):
        if not body.strip() or re.search(r'type\s*=\s*[\'"](?:application/(?:json|ld\+json|octet-stream)|importmap)', attrs, re.I):
            continue
        scripts.append(body)
    check = subprocess.run(['node', '-e',
        "const vm=require('vm'),fs=require('fs');const s=JSON.parse(fs.readFileSync(0,'utf8'));"
        "s.forEach((code,i)=>new vm.Script(code,{filename:'inline-'+i+'.js'}));"
        "process.stdout.write(JSON.stringify({parsedScripts:s.length}));"],
        input=json.dumps(scripts), text=True, capture_output=True, timeout=90)
    if check.returncode:
        raise RuntimeError('Integrated JavaScript syntax check failed:\n' + check.stderr)
    parsed = json.loads(check.stdout)
    return source, {
        'ok': True, 'version': '18.373.0',
        'allMemoryCorrectionsIntegrated': all(marker in source for marker in markers[:9]),
        'actualCareerScopeVerified': True,
        'priorCareerAndDialogCorrectionsPreserved': all(marker in source for marker in markers[9:]),
        'vacationBoundedBootIntegrated': 'msg.vacationBoot18373=v18373VacationBoot;msg.vacationCheckpoint=false;' in source,
        'playerCheckpointReuseIntegrated': 'sha256-player-packed-json-v1' in source,
        'playerFastUnpackersIntegrated': True,
        'historicalRolloverWriterInstalled': 'await v18373WriteCheckpointHistories(world,old,meta.token)' in source,
        'testHooksExcluded': True,
        'editionUpdated': "const EDITION='18.373.0';" in source,
        **parsed,
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: finalize_long_career_memory_18373.py <project>')
    root = Path(sys.argv[1])
    path = root / 'src/index.html'
    source, report = finalize(path.read_text(encoding='utf-8'))
    path.write_text(source, encoding='utf-8')
    (root / 'long-career-memory-18373-install.json').write_text(
        json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
