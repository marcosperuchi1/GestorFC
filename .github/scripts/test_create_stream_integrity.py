from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path

def die(msg): raise RuntimeError(msg)

def extract_balanced(src,start):
    p=start
    while p<len(src) and src[p].isspace(): p+=1
    if p>=len(src) or src[p] not in '{[': die('Inicio de objeto invalido')
    op=src[p];cl='}' if op=='{' else ']';depth=0;quote=None;esc=False
    for i in range(p,len(src)):
        ch=src[i]
        if quote:
            if esc: esc=False
            elif ch=='\\': esc=True
            elif ch==quote: quote=None
            continue
        if ch in ("'",'"','`'): quote=ch;continue
        if ch==op: depth+=1
        elif ch==cl:
            depth-=1
            if depth==0:return src[p:i+1]
    die('Objeto nao fechado')

def const_obj(src,name):
    m=re.search(r'const\\s+'+re.escape(name)+r'\\s*=\\s*',src)
    if not m: die(name+' ausente')
    return extract_balanced(src,m.end())

def function_block(src,name):
    m=re.search(r'function\\s+'+re.escape(name)+r'\\s*\\(',src)
    if not m: die(name+' ausente')
    b=src.find('{',m.end());depth=0;quote=None;esc=False
    for i in range(b,len(src)):
        ch=src[i]
        if quote:
            if esc: esc=False
            elif ch=='\\':esc=True
            elif ch==quote:quote=None
            continue
        if ch in ("'",'"','`'):quote=ch;continue
        if ch=='{':depth+=1
        elif ch=='}':
            depth-=1
            if depth==0:return src[m.start():i+1]
    die(name+' nao fechada')

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: test_create_stream_integrity.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); html=(root/'src'/'index.html').read_text(encoding='utf-8')

    bad="const key=m.key||'players',dst=rec.state[key]||(rec.state[key]={}),rows=m.bytes instanceof ArrayBuffer?"
    good="const key=m.key||'players',dst=rec.state[key]||(rec.state[key]={}),let rows=m.bytes instanceof ArrayBuffer?"
    # JS does not allow "const ..., let rows" in one declaration; actual expected form
    expected="const key=m.key||'players',dst=rec.state[key]||(rec.state[key]={});let rows=m.bytes instanceof ArrayBuffer?"
    if bad in html: die('create-stream ainda tenta reatribuir uma constante rows')
    if expected not in html:
        die('receptor create-stream corrigido nao encontrado')

    manifest=json.loads((root/'src/assets/data/player-base-manifest.json').read_text(encoding='utf-8'))
    asset=(root/'src'/manifest['asset']).resolve()
    if not asset.exists(): die('Base externa ausente')

    world=const_obj(html,'WorldCatalog')
    idx=const_obj(html,'V310_ROSTER_INDEX')
    sources=const_obj(html,'V310_ROSTER_SOURCES')
    dec=function_block(html,'v310DecodeCompactRoster')
    compact=function_block(html,'v124CompactColdPlayer')

    # The compact helper depends on these sets.
    m1=re.search(r"const v124SkipFalse=new Set\\((\\[[^;]+\\])\\);",html)
    m2=re.search(r"const v124SkipZero=new Set\\((\\[[^;]+\\])\\);",html)
    m3=re.search(r"const v124SkipEmpty=new Set\\((\\[[^;]+\\])\\);",html)
    if not (m1 and m2 and m3): die('sets de compactacao fria ausentes')

    a=html.find('const Engine = (() => {');b=html.find("if(typeof module!=='undefined'&&module.exports)",a)
    if a<0 or b<a: die('Engine ausente')
    engine=html[a:b]

    wa=html.find('const v18191wPlayerFields=')
    wb=html.find(" const V171_FORMAT='GFC_SHARDED_171'",wa)
    ua=html.find('const v18191uPlayerFields=')
    ub=html.find('// 5.3: one authoritative simulation',ua)
    if min(wa,wb,ua,ub)<0: die('codecs create-stream ausentes')
    wcodec=html[wa:wb]; ucodec=html[ua:ub]

    js=f"""
const fs=require('fs');
const WorldCatalog={world};
const V310_ROSTER_INDEX={idx};
const V310_ROSTER_SOURCES={sources};
{dec}
let BundledRosters={{}};
function v310WorkerLoadRosters(bytes){{
 const raw=new TextDecoder().decode(bytes),overrides=Object.create(null),cache=new Map(),keys=Object.keys(V310_ROSTER_INDEX);
 const read=id=>{{if(Object.prototype.hasOwnProperty.call(overrides,id))return overrides[id];if(cache.has(id))return cache.get(id);const x=V310_ROSTER_INDEX[id];if(!x)return undefined;const r=v310DecodeCompactRoster(JSON.parse(raw.slice(x[0],x[0]+x[1])));if(r)cache.set(id,r);return r;}};
 return new Proxy(overrides,{{get(t,p){{if(typeof p==='symbol')return Reflect.get(t,p);return read(String(p));}},set(t,p,v){{t[p]=v;cache.delete(p);return true;}},has(t,p){{return typeof p==='string'&&(Object.prototype.hasOwnProperty.call(t,p)||Object.prototype.hasOwnProperty.call(V310_ROSTER_INDEX,p));}},ownKeys(t){{return [...new Set([...keys,...Object.keys(t)])];}},getOwnPropertyDescriptor(t,p){{if(typeof p==='string'&&(Object.prototype.hasOwnProperty.call(t,p)||Object.prototype.hasOwnProperty.call(V310_ROSTER_INDEX,p)))return {{enumerable:true,configurable:true}};}}}});
}}
{engine}
const v124SkipFalse=new Set({m1.group(1)});
const v124SkipZero=new Set({m2.group(1)});
const v124SkipEmpty=new Set({m3.group(1)});
{compact}
{wcodec}
{ucodec}

const bytes=fs.readFileSync({json.dumps(str(asset))});
BundledRosters=v310WorkerLoadRosters(bytes);
const s=Engine.createCareer({{club:'t6',manager:'Stream Audit',difficulty:'normal',rosterData:BundledRosters,seed:123456789}});
const user=s.teams.find(t=>t.id===s.user),hot=new Set();
if(user)for(const id of [...(user.roster||[]),...(user.academy||[]),...(user.proReserve||[])])if(id)hot.add(id);

const rebuilt={{}},ids=Object.keys(s.players||{{}});
for(let i=0;i<ids.length;i+=1800){{
 const part=ids.slice(i,i+1800).map(id=>[id,hot.has(id)?s.players[id]:v124CompactColdPlayer(s.players[id])]);
 const packed=part.map(([id,p])=>v18191wPackPlayer(p,id));
 // This is exactly the transferable JSON-buffer shape sent by the Worker.
 let rows=JSON.parse(new TextDecoder().decode(new TextEncoder().encode(JSON.stringify(packed))));
 rows=rows.map(r=>{{const p=v18191uUnpackPlayer(r);return [p.id,p];}});
 for(const [id,p] of rows)rebuilt[id]=p;
}}
let refs=0,missing=0,clubsMissing=0;const samples=[];
for(const t of s.teams||[]){{
 let local=0;
 for(const id of t.roster||[]){{refs++;if(!rebuilt[id]){{missing++;local++;if(samples.length<12)samples.push({{club:t.name,id}});}}}}
 if(local)clubsMissing++;
}}
const userMissing=(user?.roster||[]).filter(id=>!rebuilt[id]).length;
const result={{ok:missing===0&&userMissing===0,originalPlayers:ids.length,rebuiltPlayers:Object.keys(rebuilt).length,rosterRefs:refs,missingRosterRefs:missing,clubsWithMissingPlayers:clubsMissing,userRosterMissing:userMissing,samples}};
console.log(JSON.stringify(result));
if(!result.ok)process.exit(2);
"""
    tmp=root/'.create-stream-integrity.js';tmp.write_text(js,encoding='utf-8')
    try:r=subprocess.run(['node','--max-old-space-size=2048',str(tmp)],capture_output=True,text=True,timeout=120)
    finally:tmp.unlink(missing_ok=True)
    if r.returncode: die('Integridade do create-stream falhou: '+(r.stderr or r.stdout)[-3000:])
    result=json.loads(r.stdout.strip().splitlines()[-1])
    if result['rebuiltPlayers']!=result['originalPlayers']: die('Quantidade de jogadores divergiu apos stream')
    (root/'create-stream-integrity-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__': main()
