from __future__ import annotations
import hashlib, json, re, sys
from pathlib import Path

ROSTER_SCRIPT_ID='gfc-roster-blob'
ASSET_REL='assets/data/rosters.v310.bin'
MANIFEST_REL='assets/data/player-base-manifest.json'
EXPECTED_MIN_RECORDS=2400
EXPECTED_MIN_PLAYERS=70000

def fail(msg): raise RuntimeError(msg)

def script_block(html, script_id):
    markers = (f'id="{script_id}"', f"id='{script_id}'")
    pos = -1
    for marker in markers:
        pos = html.find(marker)
        if pos >= 0:
            break
    if pos < 0:
        fail(f'script {script_id} not found')
    tag_start = html.rfind('<script', 0, pos)
    if tag_start < 0:
        fail(f'script start for {script_id} not found')
    content_start = html.find('>', pos)
    if content_start < 0:
        fail(f'script open tag for {script_id} is incomplete')
    content_start += 1
    content_end = html.find('</script>', content_start)
    if content_end < 0:
        fail(f'script end for {script_id} not found')
    return content_start, content_end

def engine_bytes(html):
    a=html.find('const Engine = (() => {')
    b=html.find("if(typeof module!=='undefined'&&module.exports)",a)
    if a<0 or b<a: fail('engine boundaries not found')
    return html[a:b].encode('utf-8')

def extract_json_const(html,name):
    m=re.search(r'const\s+'+re.escape(name)+r'\s*=\s*',html)
    if not m: fail(f'{name} not found')
    pos=m.end()
    if pos>=len(html) or html[pos]!='{': fail(f'{name} is not object')
    depth=0; quote=None; esc=False
    for i in range(pos,len(html)):
        ch=html[i]
        if quote:
            if esc: esc=False
            elif ch=='\\\\': esc=True
            elif ch==quote: quote=None
            continue
        if ch in ('"',"'"): quote=ch; continue
        if ch=='{': depth+=1
        elif ch=='}':
            depth-=1
            if depth==0: return json.loads(html[pos:i+1])
    fail(f'unclosed {name}')

def validate_blob(blob,index):
    players=0; sample={}
    for tid,pair in index.items():
        if not isinstance(pair,list) or len(pair)!=2: fail(f'bad index pair {tid}')
        start,length=map(int,pair)
        if start<0 or length<=0 or start+length>len(blob): fail(f'out of bounds {tid}')
        try: rec=json.loads(blob[start:start+length])
        except Exception as e: fail(f'invalid record {tid}: {e}')
        rows=rec.get('_p') or []
        if not isinstance(rows,list): fail(f'bad _p {tid}')
        players+=len(rows)
        if tid in ('t0','t6','t9','t12'):
            sample[tid]=[r[0] for r in rows[:5] if isinstance(r,list) and r]
    if len(index)<EXPECTED_MIN_RECORDS: fail(f'roster records too low: {len(index)}')
    if players<EXPECTED_MIN_PLAYERS: fail(f'base players too low: {players}')
    return players,sample

def replace_once(text,old,new,label):
    n=text.count(old)
    if n!=1: fail(f'{label}: expected 1 occurrence, got {n}')
    return text.replace(old,new,1)

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: externalize_player_base.py <project-dir>')
    project=Path(sys.argv[1]).resolve()
    index_path=project/'src'/'index.html'
    html=index_path.read_text(encoding='utf-8')
    before_size=len(html.encode('utf-8'))
    engine_before=hashlib.sha256(engine_bytes(html)).hexdigest()

    content_start,content_end=script_block(html,ROSTER_SCRIPT_ID)
    blob=html[content_start:content_end]
    roster_index=extract_json_const(html,'V310_ROSTER_INDEX')
    players,sample=validate_blob(blob,roster_index)
    t6_start,t6_len=map(int,roster_index['t6'])
    t6_bootstrap=json.loads(blob[t6_start:t6_start+t6_len])
    blob_bytes=blob.encode('utf-8')
    blob_sha=hashlib.sha256(blob_bytes).hexdigest()

    asset=project/'src'/ASSET_REL
    asset.parent.mkdir(parents=True,exist_ok=True)
    asset.write_bytes(blob_bytes)

    marker=json.dumps({'external':ASSET_REL,'sha256':blob_sha,'bytes':len(blob_bytes),'records':len(roster_index),'players':players},separators=(',',':'))
    html=html[:content_start] + marker + html[content_end:]

    old_decl="const v310RosterNode=document.getElementById('gfc-roster-blob')?.firstChild||null;"
    bootstrap=json.dumps({'t6':t6_bootstrap},ensure_ascii=False,separators=(',',':'))
    new_decl=f"""const V310_BOOTSTRAP_ROSTERS={bootstrap};
const V310_ROSTER_ASSET='{ASSET_REL}',V310_ROSTER_EXPECTED_BYTES={len(blob_bytes)};
let v310RosterText='',v310RosterLoadPromise=null,v310RosterLoadError=null;
function v310AcceptRosterText(text){{
 if(typeof text!=='string'||new TextEncoder().encode(text).byteLength!==V310_ROSTER_EXPECTED_BYTES)throw Error('Base local de jogadores incompleta.');
 v310RosterText=text;v310RosterLoadError=null;return text;
}}
function v310StartRosterLoad(){{
 if(v310RosterText)return Promise.resolve(v310RosterText);
 if(v310RosterLoadPromise)return v310RosterLoadPromise;
 const early=globalThis.__FUTBR_ROSTER_PRELOAD__;
 v310RosterLoadPromise=(early||fetch(V310_ROSTER_ASSET,{{cache:'force-cache'}}).then(r=>{{if(!r.ok)throw Error('Falha ao abrir a base local de jogadores ('+r.status+').');return r.text();}}))
  .then(v310AcceptRosterText).catch(e=>{{v310RosterLoadError=e;v310RosterLoadPromise=null;throw e;}});
 try{{delete globalThis.__FUTBR_ROSTER_PRELOAD__;}}catch(e){{}}
 return v310RosterLoadPromise;
}}
function v310EnsureRosterTextSync(){{
 if(v310RosterText)return v310RosterText;
 try{{
  const x=new XMLHttpRequest();x.open('GET',V310_ROSTER_ASSET,false);x.send(null);
  if((x.status>=200&&x.status<300)||x.status===0)return v310AcceptRosterText(x.responseText||'');
  throw Error('HTTP '+x.status);
 }}catch(e){{v310RosterLoadError=e;throw Error('A base local de jogadores não pôde ser carregada. Reinstale ou extraia novamente o FutBR Manager.');}}
}}
function v310RosterSlice(start,length){{return v310EnsureRosterTextSync().slice(start,start+length);}}
async function v310RosterRawBytes(){{
 const r=await fetch(V310_ROSTER_ASSET,{{cache:'force-cache'}});if(!r.ok)throw Error('Falha ao ler a base local de jogadores ('+r.status+').');
 const b=await r.arrayBuffer();if(b.byteLength!==V310_ROSTER_EXPECTED_BYTES)throw Error('Base local de jogadores com tamanho inválido.');return b;
}}
function v310ReleaseRosterSource(){{v310RosterText='';v310RosterLoadPromise=null;v310RosterCache.clear();try{{delete globalThis.__FUTBR_ROSTER_PRELOAD__;}}catch(e){{}}}}
v310StartRosterLoad().catch(e=>console.error('[FutBR] base local de jogadores:',e?.message||e));"""
    html=replace_once(html,old_decl,new_decl,'replace roster node')

    html=replace_once(
        html,
        "try{if(x&&v310RosterNode)r=v310DecodeCompactRoster(JSON.parse(v310RosterNode.data.slice(x[0],x[0]+x[1])));else{const t=V310_TEAM_BY_ID.get(id);if(t)r=v205FallbackRoster(t);}}catch(e){r=undefined;}",
        "try{if(V310_BOOTSTRAP_ROSTERS[id])r=v310DecodeCompactRoster(V310_BOOTSTRAP_ROSTERS[id]);else if(x)r=v310DecodeCompactRoster(JSON.parse(v310RosterSlice(x[0],x[1])));else{const t=V310_TEAM_BY_ID.get(id);if(t)r=v205FallbackRoster(t);}}catch(e){if(x)throw e;r=undefined;}",
        'patch roster record'
    )
    html=replace_once(html,"function v310RosterRawBytes(){if(!v310RosterNode)return null;return new TextEncoder().encode(v310RosterNode.data).buffer;}",'','remove old raw bytes')
    html=replace_once(
        html,
        "const bounds=V310_ROSTER_INDEX[id];if(!bounds||!v310RosterNode)return null;\n let item=null;\n try{item=v310DecodeCompactRoster(JSON.parse(v310RosterNode.data.slice(bounds[0],bounds[0]+bounds[1])));}catch(e){console.warn('[FutBR] Roster source error',id,e?.message||e);}",
        "const bounds=V310_ROSTER_INDEX[id];if(!bounds)return null;\n let item=null;\n try{item=V310_BOOTSTRAP_ROSTERS[id]?v310DecodeCompactRoster(V310_BOOTSTRAP_ROSTERS[id]):v310DecodeCompactRoster(JSON.parse(v310RosterSlice(bounds[0],bounds[1])));}catch(e){console.warn('[FutBR] Roster source error',id,e?.message||e);throw e;}",
        'patch original roster'
    )
    html=replace_once(
        html,
        "const id=++v53RpcId;if(streamed)v250CreateStreams.set(id,{state:null,total:0,done:0,ended:false});\n const result=await new Promise((resolve,reject)=>{v53RPC.set(id,{resolve,reject});try{",
        "const id=++v53RpcId;if(streamed)v250CreateStreams.set(id,{state:null,total:0,done:0,ended:false});\n const v18160RosterBytes=op==='create'?await v310RosterRawBytes():null;\n const result=await new Promise((resolve,reject)=>{v53RPC.set(id,{resolve,reject});try{",
        'prepare async roster bytes'
    )
    html=replace_once(html,"if(op==='create'){const b=v310RosterRawBytes();if(b){msg.baseRosterBytes=b;transfer.push(b);}}","if(op==='create'){const b=v18160RosterBytes;if(b){msg.baseRosterBytes=b;transfer.push(b);}}",'send roster bytes')

    old_worker="function v310WorkerLoadRosters(bytes){const raw=new TextDecoder().decode(bytes),O={};for(const [id,x] of Object.entries(V310_ROSTER_INDEX)){try{O[id]=v310DecodeCompactRoster(JSON.parse(raw.slice(x[0],x[0]+x[1])));}catch(e){}}return O;}"
    new_worker="""function v310WorkerLoadRosters(bytes){
 const raw=new TextDecoder().decode(bytes),overrides=Object.create(null),cache=new Map(),keys=Object.keys(V310_ROSTER_INDEX);
 const read=id=>{if(Object.prototype.hasOwnProperty.call(overrides,id))return overrides[id];if(cache.has(id)){const r=cache.get(id);cache.delete(id);cache.set(id,r);return r;}const x=V310_ROSTER_INDEX[id];if(!x)return undefined;let r;try{r=v310DecodeCompactRoster(JSON.parse(raw.slice(x[0],x[0]+x[1])));}catch(e){throw Error('Registro de elenco inválido: '+id);}if(r){cache.set(id,r);if(cache.size>96)cache.delete(cache.keys().next().value);}return r;};
 return new Proxy(overrides,{get(t,p){if(typeof p==='symbol')return Reflect.get(t,p);return read(String(p));},set(t,p,v){if(typeof p!=='string')return Reflect.set(t,p,v);t[p]=v;cache.delete(p);return true;},has(t,p){return typeof p==='string'&&(Object.prototype.hasOwnProperty.call(t,p)||Object.prototype.hasOwnProperty.call(V310_ROSTER_INDEX,p));},ownKeys(t){return [...new Set([...keys,...Object.keys(t)])];},getOwnPropertyDescriptor(t,p){if(typeof p==='string'&&(Object.prototype.hasOwnProperty.call(t,p)||Object.prototype.hasOwnProperty.call(V310_ROSTER_INDEX,p)))return {enumerable:true,configurable:true};}});
}"""
    html=replace_once(html,old_worker,new_worker,'lazy worker roster decoder')
    html=replace_once(
        html,
        "if(op==='create'||op==='next'){\n  // Once the state has reached the UI, the Worker must not keep a second full world alive.",
        "if(op==='create'||op==='next'){\n  if(op==='create')try{v310ReleaseRosterSource();}catch(e){}\n  // Once the state has reached the UI, the Worker must not keep a second full world alive.",
        'release roster source'
    )

    preload=f"<script id=\"futbr-player-base-preload\">globalThis.__FUTBR_ROSTER_PRELOAD__=fetch('{ASSET_REL}',{{cache:'force-cache'}}).then(r=>{{if(!r.ok)throw Error('Base local '+r.status);return r.text();}});</script>\n"
    if '</head>' not in html: fail('head close not found')
    html=html.replace('</head>',preload+'</head>',1)

    engine_after=hashlib.sha256(engine_bytes(html)).hexdigest()
    if engine_after!=engine_before: fail('Engine changed while externalizing player base')
    if 'v310RosterNode' in html: fail('stale v310RosterNode reference remains')

    index_path.write_text(html,encoding='utf-8')
    manifest={
        'format':'FUTBR_PLAYER_BASE_EXTERNAL_V1','asset':ASSET_REL,'sha256':blob_sha,'bytes':len(blob_bytes),
        'records':len(roster_index),'players':players,'sample':sample,'engine_sha256':engine_before,
        'html_bytes_before':before_size,'html_bytes_after':index_path.stat().st_size,
        'html_bytes_saved':before_size-index_path.stat().st_size,'worker_decoder':'lazy-lru-96',
        'authoritative_career_state':'unchanged','bootstrap_records':['t6']
    }
    (project/'src'/MANIFEST_REL).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False))

if __name__=='__main__': main()
