from __future__ import annotations
import base64, gzip, hashlib, json, os, re, subprocess, sys, zipfile
from pathlib import Path

root = Path.cwd()
work = Path(os.environ.get('RUNNER_TEMP', str(root / '.tmp'))) / 'futbr-season-inspection'
work.mkdir(parents=True, exist_ok=True)
zip_path = work / 'source.zip'
with zip_path.open('wb') as out:
    for part in sorted(root.glob('FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.part*')):
        out.write(part.read_bytes())
expected = (root / 'FutBR_Manager_Desktop_RC1_TAURI_SOURCE.zip.sha256.txt').read_text().split()[0].lower()
assert hashlib.sha256(zip_path.read_bytes()).hexdigest() == expected
with zipfile.ZipFile(zip_path) as z:
    z.extractall(work)
project = work / 'FutBR_Manager_Desktop_RC1'
scripts = root / '.github/scripts'
for name, pattern in [('consolidate_initial_database.py', 'consolidate_initial_database.py.gz.b64.part*'), ('test_initial_database.py', 'test_initial_database.py.gz.b64')]:
    b64 = ''.join(p.read_text() for p in sorted(scripts.glob(pattern)))
    (scripts / name).write_bytes(gzip.decompress(base64.b64decode(b64)))
chain = ['prepare_desktop_project', 'fix_root_gameplay', 'fix_gameplay_parity', 'fix_national_match_parity', 'hide_how_to_play_ui', 'externalize_crests', 'externalize_player_base', 'consolidate_initial_database', 'harden_save_storage', 'optimize_save_load', 'optimize_long_career_memory', 'optimize_player_storage', 'optimize_direct_load', 'add_relational_history_storage', 'finalize_prebuilt_boot', 'fix_scorers_in_scope', 'optimize_rankings_in_scope', 'finalize_rankings_18230', 'stabilize_rankings_18230', 'fix_incremental_club_ranking', 'strip_legacy_save_warning', 'stabilize_incremental_ranking_18300']
for name in chain:
    print('APPLY', name, flush=True)
    subprocess.run([sys.executable, str(scripts / (name + '.py')), str(project)], check=True)
html = (project / 'src/index.html').read_text(encoding='utf-8')
out = work / 'diagnostics'
out.mkdir(exist_ok=True)
lines = html.splitlines()
# Keep the complete assembled source in small text parts, in this private repository only.
parts = []
start = 0
while start < len(lines):
    end = start
    size = 0
    while end < len(lines) and end - start < 160 and (size < 70000 or end == start):
        size += len(lines[end]) + 1
        end += 1
    name = f'source-{len(parts):04d}.txt'
    (out / name).write_text('\n'.join(lines[start:end]), encoding='utf-8')
    parts.append({'file': name, 'start': start + 1, 'end': end})
    start = end
terms = ['Sincronizando a carreira', 'Carregando Nova Temporada', 'v169', 'async function save(s)', 'async function saveSharded', 'function nextSeason', 'nextSeason=', 'nextSeason =', 'function v53', 'v53PatchQueue', 'postMessage', 'v555CareerArchive', 'hydrate', 'reconcile', 'syncing', 'synchron', 'onmessage', 'terminate()', 'structuredClone', 'JSON.stringify']
hits = {}
for term in terms:
    found = []
    for i, line in enumerate(lines):
        pos = line.find(term)
        if pos >= 0:
            part = next(p for p in parts if p['start'] <= i + 1 <= p['end'])
            found.append({'line': i+1, 'file': part['file'], 'localLine': i+2-part['start'], 'text': line[max(0,pos-140):pos+420]})
    hits[term] = found
(out / 'locations.json').write_text(json.dumps(hits, ensure_ascii=False, indent=2), encoding='utf-8')
(out / 'parts.json').write_text(json.dumps(parts, indent=2), encoding='utf-8')
(out / 'summary.json').write_text(json.dumps({'sourceCommit': os.environ.get('GITHUB_SHA'), 'characters': len(html), 'lines': len(lines), 'parts': len(parts), 'pipeline': chain}, indent=2), encoding='utf-8')
for name in ['desktop-bridge.js', 'native-storage.js']:
    for path in (project / 'src').rglob(name):
        (out / name).write_bytes(path.read_bytes())
(out / 'native-lib.rs').write_bytes((project / 'src-tauri/src/lib.rs').read_bytes())
with open(os.environ['GITHUB_ENV'], 'a', encoding='utf-8') as env:
    env.write(f'FUTBR_INSPECT_PROJECT={project}\nFUTBR_INSPECT_DIST={out}\n')
print(json.dumps({'characters': len(html), 'lines': len(lines), 'parts': len(parts)}), flush=True)
