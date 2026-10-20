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

def const_obj(src,name,after=0):
    m=re.search(r'const\s+'+re.escape(name)+r'\s*=\s*',src[after:])
    if not m: die(name+' ausente')
    return extract_balanced(src,after+m.end())

def function_block(src,name):
    m=re.search(r'function\s+'+re.escape(name)+r'\s*\(',src)
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
    if len(sys.argv)!=2: raise SystemExit('usage: test_create_performance.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); html=(root/'src'/'index.html').read_text(encoding='utf-8')
    manifest=json.loads((root/'src/assets/data/player-base-manifest.json').read_text(encoding='utf-8'))
    asset=(root/'src'/manifest['asset']).resolve()
    if not asset.exists(): die('Base externa ausente')

    world=const_obj(html,'WorldCatalog',0)
    idx=const_obj(html,'V310_ROSTER_INDEX',0)
    sources=const_obj(html,'V310_ROSTER_SOURCES',0)
    dec=function_block(html,'v310DecodeCompactRoster')
    a=html.find('const Engine = (() => {');b=html.find("if(typeof module!=='undefined'&&module.exports)",a)
    if a<0 or b<a: die('Engine ausente')
    engine=html[a:b]

    ca=html.find('const v18191mPlayerFields=')
    cb=html.find('async function v18183DbWriteMany',ca)
    if ca<0 or cb<ca: die('Codec compacto principal ausente')
    codec=html[ca:cb]

    js=f"""
const fs=require('fs');const {{performance}}=require('perf_hooks');
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
{codec}
(async()=>{{
 const bytes=fs.readFileSync({json.dumps(str(asset))});BundledRosters=v310WorkerLoadRosters(bytes);
 const t0=performance.now();const s=Engine.createCareer({{club:'t6',manager:'Benchmark',difficulty:'normal',rosterData:BundledRosters,seed:123456789}});const createMs=performance.now()-t0;
 const players=Object.keys(s.players||{{}}).length,academy=(s.teams||[]).reduce((n,t)=>n+(t.academy?.length||0),0);
 const rosterSizes=(s.teams||[]).map(t=>({{id:t.id,name:t.name,roster:(t.roster||[]).length,academy:(t.academy||[]).length}}));
 const maxRoster=Math.max(0,...rosterSizes.map(x=>x.roster)),clubsOver32=rosterSizes.filter(x=>x.roster>32);
 if(clubsOver32.length)throw Error('Clubes acima do teto de 32: '+JSON.stringify(clubsOver32.slice(0,20)));
 const ids=Object.keys(s.players||{{}});let encodedChars=0,chunks=0;const t1=performance.now();
 for(let i=0;i<ids.length;i+=900){{const rows=ids.slice(i,i+900).map(id=>[id,s.players[id]]);const enc=await v18191mEncodePlayerChunk(rows);encodedChars+=String(enc.data||'').length;chunks++;}}
 const saveCodecMs=performance.now()-t1,result={{ok:true,createMs:Math.round(createMs),players,academy,maxRoster,clubsOver32:clubsOver32.length,heapMiB:Math.round(process.memoryUsage().heapUsed/1048576),rssMiB:Math.round(process.memoryUsage().rss/1048576),saveCodecMs:Math.round(saveCodecMs),playerChunks:chunks,playerBase64MiB:Math.round(encodedChars/1048576*100)/100}};
 console.log(JSON.stringify(result));
}})().catch(e=>{{console.error(e);process.exit(1);}});
"""
    tmp=root/'.create-performance-test.js';tmp.write_text(js,encoding='utf-8')
    try:r=subprocess.run(['node','--max-old-space-size=2048',str(tmp)],capture_output=True,text=True,timeout=90)
    finally:tmp.unlink(missing_ok=True)
    if r.returncode:die('Benchmark falhou: '+r.stderr[-2000:])
    result=json.loads(r.stdout.strip().splitlines()[-1])
    if result['players']<195000 or result['players']>215000:die(f"Populacao inicial fora da base consolidada esperada: {result['players']}")
    if result['academy']<40000 or result['academy']>50000:die(f"Academias consolidadas fora da faixa esperada: {result['academy']}")
    if result['createMs']>20000:die(f"Criacao muito lenta no runner: {result['createMs']} ms")
    if result['playerBase64MiB']>20:die(f"Save compacto de jogadores grande demais: {result['playerBase64MiB']} MiB")
    if result['saveCodecMs']>12000:die(f"Codec do save lento demais: {result['saveCodecMs']} ms")
    (root/'create-performance-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
