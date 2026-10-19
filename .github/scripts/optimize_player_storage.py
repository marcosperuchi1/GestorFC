from __future__ import annotations
import sys
from pathlib import Path

FIELDS=[
'name','pos','age','skills','potential','fitness','morale','contract','wage','injury','ban','yellows','reds','cardCount','listed','xp','goals','assists','apps','cupGoals','totalGoals','totalApps','real','clubId','ageEstimated','positionEstimated','natCode','nationalityKnown','star','starYears','worldGoals','traitSeed','traitAge','archetype','squad','starCandidate','seasonRatingSum58','seasonRatingCount58','seasonMinutes58','naturalPosition','specificPositionEstimated','secondaryPositions','initialFiller','supportFictional','providerId','sourceOrder','editorOvr','editorOvrApplied','databaseOvr','dob','identityKey','localized','initialRealAcademy','proReserve','matchLoad545','startStreak545','careerMinutes','lastMatchRating','performanceXP58','seasonGain','seasonStartOverall'
]

def fail(msg): raise RuntimeError(msg)

def replace_once(text,old,new,label):
    n=text.count(old)
    if n!=1: fail(f'{label}: esperado 1, encontrado {n}')
    return text.replace(old,new,1)

def helper(prefix='v18191'):
    fields=','.join(repr(x) for x in FIELDS)
    return f"""const {prefix}PlayerFields=[{fields}],{prefix}PlayerFieldSet=new Set({prefix}PlayerFields),{prefix}PlayerFormat='FUTBR_PLAYERS_PACKED_GZIP_V1';
function {prefix}ArrayBufferToBase64(ab){{const u=new Uint8Array(ab);let s='';for(let i=0;i<u.length;i+=32768)s+=String.fromCharCode(...u.subarray(i,i+32768));return btoa(s);}}
function {prefix}Base64ToBytes(s){{const b=atob(String(s||'')),u=new Uint8Array(b.length);for(let i=0;i<b.length;i++)u[i]=b.charCodeAt(i);return u;}}
function {prefix}PackPlayer(p,id){{const vals=new Array({prefix}PlayerFields.length);let lo=0,hi=0;for(let i=0;i<{prefix}PlayerFields.length;i++){{const k={prefix}PlayerFields[i],has=Object.prototype.hasOwnProperty.call(p,k);vals[i]=has?p[k]:null;if(has){{if(i<32)lo=(lo|(1<<i))>>>0;else hi=(hi|(1<<(i-32)))>>>0;}}}}const extra={{}};for(const k in p)if(k!=='id'&&!{prefix}PlayerFieldSet.has(k))extra[k]=p[k];return Object.keys(extra).length?[String(id),lo,hi,vals,extra]:[String(id),lo,hi,vals];}}
function {prefix}UnpackPlayer(r){{const [id,lo,hi,vals,extra]=r,p={{id:String(id)}};for(let i=0;i<{prefix}PlayerFields.length;i++){{const has=i<32?((lo>>>i)&1):((hi>>>(i-32))&1);if(has)p[{prefix}PlayerFields[i]]=vals[i];}}if(extra&&typeof extra==='object')Object.assign(p,extra);return p;}}
async function {prefix}EncodePlayerChunk(rows){{const packed=rows.map(([id,p])=>{prefix}PackPlayer(p,id)),text=JSON.stringify(packed);if(typeof CompressionStream==='function'){{const ab=await new Response(new Blob([text]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer();return {{format:{prefix}PlayerFormat,encoding:'gzip-base64',data:{prefix}ArrayBufferToBase64(ab),count:packed.length}};}}return {{format:{prefix}PlayerFormat,encoding:'json',data:text,count:packed.length}};}}
async function {prefix}DecodePlayerChunk(chunk){{if(!chunk||chunk.format!=={prefix}PlayerFormat)return chunk;let text;if(chunk.encoding==='gzip-base64'){{if(typeof DecompressionStream!=='function')throw Error('Este sistema nao consegue descompactar o bloco de jogadores.');const u={prefix}Base64ToBytes(chunk.data);text=await new Response(new Blob([u]).stream().pipeThrough(new DecompressionStream('gzip'))).text();}}else text=String(chunk.data||'[]');return JSON.parse(text).map(r=>{{const p={prefix}UnpackPlayer(r);return [p.id,p];}});}}
"""

def main():
    if len(sys.argv)!=2: raise SystemExit('usage: optimize_player_storage.py <project-dir>')
    project=Path(sys.argv[1]).resolve(); path=project/'src'/'index.html'
    html=path.read_text(encoding='utf-8')
    if 'FUTBR_PLAYERS_PACKED_GZIP_V1' in html:
        print('packed player storage already present'); return

    worker_anchor=" const V171_FORMAT='GFC_SHARDED_171',V171_SHARDS="
    if worker_anchor not in html: fail('worker V171 anchor ausente')
    html=html.replace(worker_anchor,' '+helper('v18191w')+worker_anchor,1)

    old_decode=""" async function v171DecodeManifest(x){
  const s={...(x.root||{})};
  for(const [key,spec] of Object.entries(x.collections||{})){
   const dst=spec?.isArray?new Array(Number(spec.length)||0):{},keys=spec?.keys||[];
   for(let i=0;i<keys.length;i+=8){
    const chunks=await Promise.all(keys.slice(i,i+8).map(k=>read(k)));
    for(const rows of chunks||[])for(const [id,row] of rows||[]){
     if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;
    }
    if(i+8<keys.length)await new Promise(r=>setTimeout(r,0));
   }
   s[key]=dst;
  }
  return s;
 }"""
    new_decode=""" async function v171DecodeManifest(x){
  const s={...(x.root||{})};
  for(const [key,spec] of Object.entries(x.collections||{})){
   const dst=spec?.isArray?new Array(Number(spec.length)||0):{},keys=spec?.keys||[];
   for(let i=0;i<keys.length;i+=8){
    const chunks=await Promise.all(keys.slice(i,i+8).map(k=>read(k)));
    for(let rows of chunks||[]){
     if(key==='players'&&rows?.format===v18191wPlayerFormat)rows=await v18191wDecodePlayerChunk(rows);
     for(const [id,row] of rows||[]){if(Array.isArray(dst))dst[Number(id)]=row;else dst[id]=row;}
    }
    if(i+8<keys.length)await new Promise(r=>setTimeout(r,0));
   }
   s[key]=dst;
  }
  return s;
 }"""
    html=replace_once(html,old_decode,new_decode,'worker packed-player decoder')

    save_worker=html.find('async function save(s){')
    if save_worker<0: fail('worker save ausente')
    loop_start=html.find("const v18181Stable=new Set(['v538CareerArchive'",save_worker)
    loop_end=html.find(' const manifest=',loop_start)
    if loop_start<0 or loop_end<0: fail('worker shard loop ausente')
    worker_loop="""const v18181Stable=new Set(['v538CareerArchive','v555CareerArchive','scorerArchive']);for(const key of V171_SHARDS){const value=s[key];if(value==null)continue;const sameSeason=old?.format===V171_FORMAT&&Number(old.year)===Number(s.year)&&!s.seasonDone&&v18181Stable.has(key)&&old.collections?.[key];if(sameSeason){collections[key]=old.collections[key];continue;}const isArray=Array.isArray(value),keys=[],limit=key==='players'?1800:key==='teams'?380:key==='coaches'?500:key==='schedule'?4:key==='competitionStats'?4:key==='allTimeStats'?650:(key==='v538CareerArchive'||key==='v555CareerArchive'||key==='scorerArchive'?1:120);let rows=[],chunk=0,done=0,pending=[];const commit=async(force=false)=>{if(!pending.length)return;const target=key==='players'?4:key==='allTimeStats'?6:4;if(!force&&pending.length<target)return;await v18181RawWriteMany(pending.splice(0,pending.length));await new Promise(r=>setTimeout(r,0));};const flush=async()=>{if(!rows.length)return;const raw=rows;rows=[];const payload=key==='players'?await v18191wEncodePlayerChunk(raw):raw,ck=v171ShardKey(token,key,chunk++);keys.push(ck);pending.push({key:ck,value:payload});done++;await commit(false);};for(const id in value){if(!safe(id))continue;rows.push([id,value[id]]);if(rows.length>=limit)await flush();}await flush();await commit(true);collections[key]={isArray,length:isArray?value.length:0,keys,...(key==='players'?{encoding:v18191wPlayerFormat}:null)};}"""
    html=html[:loop_start]+worker_loop+html[loop_end:]

    main_anchor='async function v18183DbWriteMany(entries){'
    if main_anchor not in html: fail('main batch write anchor ausente')
    html=html.replace(main_anchor,helper('v18191m')+main_anchor,1)

    ws=html.find(' async function writeCollection(token,key,value,limit){',html.find(main_anchor))
    if ws<0: ws=html.find('async function writeCollection(token,key,value,limit){',html.find(main_anchor))
    we=html.find('  async function saveSharded(',ws)
    if we<0: we=html.find(' async function saveSharded(',ws)
    if ws<0 or we<0: fail('main writeCollection ausente')
    new_write="""async function writeCollection(token,key,value,limit){
  const isArray=Array.isArray(value),keys=[];let rows=[],idx=0,writes=0,pending=[];
  const commit=async(force=false)=>{
   if(!pending.length)return;const target=key==='players'?4:key==='allTimeStats'?8:6;if(!force&&pending.length<target)return;
   const batch=pending.splice(0,pending.length);await v18183DbWriteMany(batch);await new Promise(r=>setTimeout(r,0));
  };
  const flush=async()=>{
   if(!rows.length)return;const raw=rows;rows=[];const payload=key==='players'?await v18191mEncodePlayerChunk(raw):raw,ck=shardKey(token,key,idx++);keys.push(ck);pending.push({key:ck,value:payload});writes++;
   if(key==='players')stats.playerChunksWritten++;
   if(v18121NewSeasonPreparation&&(key!=='players'||writes===1||writes%10===0)){v53Sim.progress=key==='players'?'Salvando jogadores compactados · bloco '+writes:'Salvando '+key+' da nova temporada';try{v53PaintStatus();}catch(e){}}
   await commit(false);
  };
  for(const id in (value||{})){rows.push([id,value[id]]);if(rows.length>=limit)await flush();}
  await flush();await commit(true);return {isArray,length:isArray?value.length:0,keys,...(key==='players'?{encoding:v18191mPlayerFormat}:null)};
 }
 """
    html=html[:ws]+new_write+html[we:]
    html=html.replace("const limit=key==='players'?2400:key==='teams'?420", "const limit=key==='players'?1800:key==='teams'?420",1)

    marker="G.v171={version:V,freshCareerOnly:true,storageKey:KEY,memory:{"
    if marker in html:
        html=html.replace(marker,"G.v171={version:V,freshCareerOnly:true,storageKey:KEY,playerStorage:{format:'FUTBR_PLAYERS_PACKED_GZIP_V1',lossless:true,unknownFields:'extra',gzip:true},memory:{",1)

    path.write_text(html,encoding='utf-8')
    print('packed player storage applied')

if __name__=='__main__': main()
