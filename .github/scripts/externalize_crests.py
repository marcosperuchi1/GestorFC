from __future__ import annotations
import base64, hashlib, json, re, sys
from pathlib import Path

DATA_RE = re.compile(r'^data:image/(png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=\\s]+)$', re.I)

def safe_name(value: str) -> str:
    s = re.sub(r'[^A-Za-z0-9._-]+', '_', str(value)).strip('._')
    return s[:140] or hashlib.sha1(str(value).encode('utf-8')).hexdigest()

def extract_data_uri(data: str, root: Path, source: str, club_id: str):
    m = DATA_RE.match(data or '')
    if not m:
        return None
    ext = m.group(1).lower()
    if ext == 'jpeg':
        ext = 'jpg'
    raw = base64.b64decode(re.sub(r'\\s+', '', m.group(2)), validate=False)
    digest = hashlib.sha1(str(club_id).encode('utf-8')).hexdigest()
    rel = Path('assets') / 'crests' / source / digest[:2] / f'{safe_name(club_id)}.{ext}'
    out = root / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    return rel.as_posix(), len(raw)

def script_match(html: str, script_id: str):
    pat = re.compile(r'(<script\\b[^>]*\\bid=["\\']' + re.escape(script_id) + r'["\\'][^>]*>)(.*?)(</script>)', re.I | re.S)
    m = pat.search(html)
    if not m:
        raise RuntimeError(f'Script {script_id} not found')
    return m

def replace_script_content(html: str, script_id: str, content: str) -> str:
    m = script_match(html, script_id)
    return html[:m.start(2)] + content + html[m.end(2):]

def parse_const_object(html: str, name: str):
    m = re.search(r'const\\s+' + re.escape(name) + r'\\s*=\\s*(\\{.*?\\});', html, re.S)
    if not m:
        raise RuntimeError(f'Const {name} not found')
    return m, json.loads(m.group(1))

def replace_const_object(html: str, name: str, obj) -> str:
    m, _ = parse_const_object(html, name)
    raw = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    return html[:m.start(1)] + raw + html[m.end(1):]

def externalize_blob(html: str, root: Path, script_id: str, index_name: str, source: str):
    sm = script_match(html, script_id)
    blob = sm.group(2)
    _, index = parse_const_object(html, index_name)
    rebuilt, new_index = [], {}
    offset = count = raw_bytes = 0
    for club_id, pair in index.items():
        start, length = int(pair[0]), int(pair[1])
        rec = json.loads(blob[start:start + length])
        data = rec.get('data') if isinstance(rec, dict) else None
        if isinstance(data, str):
            extracted = extract_data_uri(data, root, source, club_id)
            if extracted:
                rel, n = extracted
                rec.pop('data', None)
                rec['url'] = rel
                rec['offlineAsset'] = True
                count += 1
                raw_bytes += n
        compact = json.dumps(rec, ensure_ascii=False, separators=(',', ':'))
        new_index[club_id] = [offset, len(compact)]
        rebuilt.append(compact)
        offset += len(compact)
    html = replace_script_content(html, script_id, ''.join(rebuilt))
    html = replace_const_object(html, index_name, new_index)
    return html, count, raw_bytes

def externalize_portable_base(html: str, root: Path):
    sm = script_match(html, 'gfc-v1865-portable-base')
    obj = json.loads(sm.group(2))
    crests = obj.get('crests') or {}
    count = raw_bytes = 0
    for club_id, rec in crests.items():
        if not isinstance(rec, dict):
            continue
        data = rec.get('data')
        if not isinstance(data, str):
            continue
        extracted = extract_data_uri(data, root, 'v1865', club_id)
        if not extracted:
            continue
        rel, n = extracted
        rec.pop('data', None)
        rec['url'] = rel
        rec['offlineAsset'] = True
        count += 1
        raw_bytes += n
    html = replace_script_content(
        html,
        'gfc-v1865-portable-base',
        json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    )
    return html, count, raw_bytes

def patch_runtime(html: str) -> str:
    old = """v1894PortableCrestLookup=id=>{
 const r=v1894PortableRecord(id);
 return r&&typeof r.data==='string'&&/^data:image\\/(png|jpeg|webp);base64,[a-z0-9+/=]+$/i.test(r.data)?r:undefined;
};"""
    new = """v1894PortableCrestLookup=id=>{
 const r=v1894PortableRecord(id);
 return r&&((typeof r.data==='string'&&/^data:image\\/(png|jpeg|webp);base64,[a-z0-9+/=]+$/i.test(r.data))||(typeof r.url==='string'&&r.url))?r:undefined;
};"""
    if old not in html:
        raise RuntimeError('v1894PortableCrestLookup pattern not found')
    html = html.replace(old, new, 1)
    replacements = [
        ("if(Object.prototype.hasOwnProperty.call(v300CrestOverrides,id)&&v300CrestOverrides[id]?.data)return v300CrestOverrides[id];",
         "if(Object.prototype.hasOwnProperty.call(v300CrestOverrides,id)&&(v300CrestOverrides[id]?.data||v300CrestOverrides[id]?.url))return v300CrestOverrides[id];"),
        ("if(!v1894PortableCrestDeleted.has(id)&&v1894PortableCrestLookup){const portable=v1894PortableCrestLookup(id);if(portable?.data)return portable;}",
         "if(!v1894PortableCrestDeleted.has(id)&&v1894PortableCrestLookup){const portable=v1894PortableCrestLookup(id);if(portable?.data||portable?.url)return portable;}"),
        ("if(origin&&origin!==id){const linked=v300CrestRecord(origin);if(linked?.data)return linked;}",
         "if(origin&&origin!==id){const linked=v300CrestRecord(origin);if(linked?.data||linked?.url)return linked;}")
    ]
    for old_text,new_text in replacements:
        if old_text in html:
            html = html.replace(old_text,new_text,1)
    html = html.replace('loading="lazy" referrerpolicy="no-referrer" onerror=',
                        'loading="eager" decoding="async" fetchpriority="high" referrerpolicy="no-referrer" onerror=')
    return html

def main():
    if len(sys.argv) != 2:
        raise SystemExit('usage: externalize_crests.py <project-dir>')
    project = Path(sys.argv[1]).resolve()
    index = project / 'src' / 'index.html'
    html = index.read_text(encoding='utf-8')
    before = len(html.encode('utf-8'))
    total_count = total_raw = 0

    html, n, b = externalize_portable_base(html, project / 'src')
    total_count += n; total_raw += b
    html, n, b = externalize_blob(html, project / 'src', 'gfc-v1894-portable-crest-blob', 'V1894_PORTABLE_CREST_INDEX', 'v1894')
    total_count += n; total_raw += b
    html, n, b = externalize_blob(html, project / 'src', 'gfc-crest-blob', 'V300_CREST_INDEX', 'v300')
    total_count += n; total_raw += b
    html = patch_runtime(html)
    index.write_text(html, encoding='utf-8')
    after = index.stat().st_size

    assets = [p for p in (project / 'src' / 'assets' / 'crests').rglob('*') if p.is_file()]
    manifest = {
        'format': 'FUTBR_LOCAL_CREST_ASSETS_V1',
        'records_externalized': total_count,
        'asset_files': len(assets),
        'asset_bytes': sum(p.stat().st_size for p in assets),
        'html_bytes_before': before,
        'html_bytes_after': after,
        'html_bytes_saved': before - after,
    }
    out = project / 'src' / 'assets' / 'crests' / 'manifest.json'
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False))

    if total_count < 6000:
        raise RuntimeError(f'Poucos escudos externalizados: {total_count}')
    if after >= before * 0.60:
        raise RuntimeError(f'HTML nao reduziu o suficiente: {before} -> {after}')

if __name__ == '__main__':
    main()
