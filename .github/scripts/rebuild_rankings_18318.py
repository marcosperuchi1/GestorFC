from pathlib import Path
import sys, json

MARK = 'FUTBR_RANK_REBUILD_18318'
PATCH = r"""
<script id="futbr-ranking-18318">
/* FUTBR_RANK_REBUILD_18318 */
(()=>{
'use strict';
const G=window.GestorFC=window.GestorFC||{};
let lastState=null,lastKey='',snapshot=null;
const stats={builds:0,hits:0,errors:0,ms:0};
const filters={query:'',conf:'all',country:'all',page:0};
const number=x=>{const n=Number(x);return Number.isFinite(n)?n:0;};
const clean=x=>String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
const norm=x=>String(x??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
function category(name){
 const n=norm(name);
 if(/mundial|world club|club world|intercontinental/.test(n))return 'M';
 if(/libertadores|champions|sudamericana|sul-americana|europa league|conference league|continental|concacaf|afc |caf |ofc |uefa |international/.test(n))return 'I';
 if(/estadual|regional|state cup|state league/.test(n))return 'R';
 if(/copa|cup|pokal|coupe|coppa|taca|taça/.test(n))return 'C';
 if(/liga|league|serie |série |division|divisao|divisão|premier|bundesliga|ligue |laliga|calcio|campeonato/.test(n))return 'L';
 return 'O';
}
function titleIndex(s,teams){
 const titles=new Map(),seen=new Set();
 function add(id,yr,name,key){
  if(!teams.has(id))return;
  const unique=String(key||[yr,name,id].join('|'));
  if(seen.has(unique))return;
  seen.add(unique);
  const code=category(name),item=titles.get(id)||{L:0,C:0,I:0,M:0,R:0,O:0};
  item[code]++;titles.set(id,item);
 }
 for(const h of s.worldHistory||[])for(const row of h?.countries||[]){
  const year=number(h.year),ct=String(row?.country||'');
  add(row?.champion,year,ct+' league','l:'+year+':'+ct);
  add(row?.secondChampion,year,ct+' second division','l2:'+year+':'+ct);
  add(row?.cup,year,ct+' cup','c:'+year+':'+ct);
 }
 for(const h of s.internationalHistory||[])add(h?.champion,number(h?.year),String(h?.name||h?.id||'international'),'i:'+h?.year+':'+h?.id);
 for(const [ct,id] of Object.entries(s.cupWinners||{}))add(id,number(s.year),ct+' cup','c:'+s.year+':'+ct);
 for(const [key,c] of Object.entries(s.competitions||{}))if(c?.champion)add(c.champion,number(s.year),String(c.name||c.title||c.id||key),'x:'+s.year+':'+key);
 return titles;
}
function makeSnapshot(s){
 const start=performance.now();
 const teams=new Map((s.teams||[]).map(t=>[String(t.id),t]));
 let rows=[];
 const st=s.v18300ClubRankingStore;
 if(st?.rows&&Array.isArray(st.order)&&st.order.length){
  rows=st.order.map(id=>st.rows[id]).filter(Boolean);
 }else if(typeof E!=='undefined'&&typeof E.clubRankingRows633==='function'){
  rows=E.clubRankingRows633(s)||[];
 }
 if(!rows.length)throw Error('Base de clubes ainda nao disponivel');
 const titles=titleIndex(s,teams),records=st?.records||{};
 const result=[];
 for(const base of rows){
  const t=teams.get(String(base.id));if(!t)continue;
  const p=Number(base.performancePoints??base.points)||0;
  const total=Number(base.totalPoints??base.points)||0;
  const ledger=titles.get(String(base.id))||{L:0,C:0,I:0,M:0,R:0,O:0};
  const weighted=ledger.L*6+ledger.C*4+ledger.I*12+ledger.M*20+ledger.R*2+ledger.O;
  const oldBonus=number(base.titlePoints);
  const bonus=Math.max(oldBonus,weighted);
  const score=Math.round((total-oldBonus+bonus)*100)/100;
  const rec=records[base.id]||{};
  result.push({id:String(base.id),name:String(t.name||base.name||base.id),
    country:String(t.country||base.country||''),conf:String(base.conf||t.conf||''),
    games:number(rec.games),wins:number(rec.wins),draws:number(rec.draws),losses:number(rec.losses),
    performance:Math.round(p*100)/100,ledger,bonus,score,base:number(t.base)});
 }
 result.sort((a,b)=>b.score-a.score||b.performance-a.performance||b.bonus-a.bonus||b.base-a.base||a.name.localeCompare(b.name,'pt-BR'));
 const ranked=result.slice(0,1000);
 stats.builds++;stats.ms=Math.round(performance.now()-start);
 return ranked;
}
function getSnapshot(){
 const s=state;if(!s)return [];
 const st=s.v18300ClubRankingStore;
 const key=[s.year,st?.revision,st?.recordRevision,st?.order?.length,s.worldHistory?.length,s.internationalHistory?.length,Object.keys(s.cupWinners||{}).length,Object.keys(s.competitions||{}).filter(k=>s.competitions[k]?.champion).length].join(':');
 if(s===lastState&&key===lastKey&&snapshot){stats.hits++;return snapshot;}
 const next=makeSnapshot(s);lastState=s;lastKey=key;snapshot=next;return next;
}
const format=n=>number(n).toLocaleString('pt-BR',{maximumFractionDigits:2});
function page(){
 let result=[];let error='';
 try{result=getSnapshot();}catch(e){stats.errors++;error=String(e?.message||e);console.warn('[18.318] ranking',e);}
 const tabs=typeof v677RankingTabs==='function'?v677RankingTabs():'';
 if(error)return '<div class="v677-ranking-hub">'+tabs+'<div class="v677-ranking-content"><section class="panel"><div class="panel-body">Ranking indisponível: '+clean(error)+'</div></section></div></div>';
 const countries=[...new Set(result.map(r=>r.country).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
 const confs=[...new Set(result.map(r=>r.conf).filter(Boolean))].sort();
 const found=result.filter(r=>(filters.conf==='all'||r.conf===filters.conf)&&(filters.country==='all'||r.country===filters.country)&&(!filters.query||norm(r.name).includes(norm(filters.query))));
 const pages=Math.max(1,Math.ceil(found.length/50));filters.page=Math.min(Math.max(0,filters.page),pages-1);
 const visible=found.slice(filters.page*50,(filters.page+1)*50);
 const option=(value,label,chosen)=>'<option value="'+clean(value)+'"'+(chosen===value?' selected':'')+'>'+clean(label)+'</option>';
 const tableRows=visible.map((r,i)=>{
  const count=k=>format(r.ledger[k]);
  const rank=result.indexOf(r)+1;
  return '<tr><td>'+(rank)+'</td><td><b>'+clean(r.name)+'</b></td><td>'+clean(r.country)+'</td><td>'+clean(r.conf)+'</td><td>'+format(r.games)+'</td><td>'+format(r.wins)+'</td><td>'+format(r.draws)+'</td><td>'+format(r.losses)+'</td><td>'+format(r.performance)+'</td><td>'+count('L')+'</td><td>'+count('C')+'</td><td>'+count('I')+'</td><td>'+count('M')+'</td><td>'+count('R')+'</td><td>'+count('O')+'</td><td>'+format(r.bonus)+'</td><td><b>'+format(r.score)+'</b></td></tr>';
 }).join('');
 const style='<style id="v18318-style">.v18318-wrap{padding:14px 2px}.v18318-controls{display:grid;grid-template-columns:minmax(180px,1fr) 170px 170px;gap:8px;margin:12px 0}.v18318-controls label{display:block;font-size:11px;margin-bottom:4px}.v18318-controls input,.v18318-controls select{width:100%;padding:9px;border-radius:8px;background:var(--panel,#421919);color:inherit;border:1px solid #8c5151}.v18318-scroller{overflow:auto;max-height:62vh;border:1px solid #895050;border-radius:12px}.v18318-scroller table{width:100%;min-width:1080px;border-collapse:collapse;font-size:12px}.v18318-scroller th,.v18318-scroller td{padding:9px 7px;text-align:center;border-bottom:1px solid #704040;white-space:nowrap}.v18318-scroller th{position:sticky;top:0;background:#512222;z-index:2}.v18318-scroller td:nth-child(2),.v18318-scroller th:nth-child(2){text-align:left}.v18318-scroller tr:nth-child(even){background:rgba(255,255,255,.035)}.v18318-footer{display:flex;justify-content:space-between;align-items:center;padding:10px 4px}.v18318-footer button{padding:7px 12px;border:1px solid #895050;border-radius:8px;background:transparent;color:inherit;cursor:pointer}.v18318-footer button:disabled{opacity:.4}@media(max-width:800px){.v18318-controls{grid-template-columns:1fr}}</style>';
 return '<div class="v677-ranking-hub">'+tabs+'<div class="v677-ranking-content">'+style+'<div class="v18318-wrap"><h2>Ranking de Clubes</h2><div class="tiny muted">Top 1.000 consolidado · '+result.length+' clubes · cálculo armazenado em memória</div><div class="v18318-controls"><div><label>BUSCAR CLUBE</label><input data-v18318="query" value="'+clean(filters.query)+'" placeholder="Nome do clube"></div><div><label>CONFEDERAÇÃO</label><select data-v18318="conf">'+option('all','Todas',filters.conf)+confs.map(c=>option(c,c,filters.conf)).join('')+'</select></div><div><label>PAÍS</label><select data-v18318="country">'+option('all','Todos',filters.country)+countries.map(c=>option(c,c,filters.country)).join('')+'</select></div></div><div class="v18318-scroller"><table><thead><tr>'+['#','CLUBE','PAÍS','CONF.','J','V','E','D','DESEMPENHO','L','C','I','M','R','O','BÔNUS TÍTULOS','COEF.'].map(v=>'<th>'+v+'</th>').join('')+'</tr></thead><tbody>'+tableRows+'</tbody></table></div><div class="v18318-footer"><span class="tiny">Página '+(filters.page+1)+' de '+pages+' · '+found.length+' clubes</span><div><button data-v18318-page="prev" '+(filters.page===0?'disabled':'')+'>Anterior</button> <button data-v18318-page="next" '+(filters.page===pages-1?'disabled':'')+'>Próxima</button></div></div></div></div></div>';
}
function refresh(){
 try{v18221InvalidateClubRanking?.('18.318');}catch(e){}
 try{const el=document.querySelector('#v555-page');if(el&&view==='clubrankings')el.innerHTML=page();}catch(e){console.warn('[18.318] refresh',e);}
}
document.addEventListener('input',e=>{
 if(e.target?.dataset?.v18318!=='query')return;
 const el=e.target;filters.query=el.value;filters.page=0;
 // Debounce and preserve focus and cursor.
 clearTimeout(refresh.queryTimer);refresh.queryTimer=setTimeout(()=>{if(document.activeElement===el){const sel=el.selectionStart;refresh();const next=document.querySelector('[data-v18318="query"]');if(next){next.focus();next.setSelectionRange(sel,sel);}}else refresh();},180);
},true);
document.addEventListener('change',e=>{
 const k=e.target?.dataset?.v18318;if(k!=='conf'&&k!=='country')return;
 filters[k]=e.target.value;filters.page=0;refresh();
},true);
document.addEventListener('click',e=>{
 const action=e.target?.closest?.('[data-v18318-page]')?.dataset?.v18318Page;
 if(!action)return;e.preventDefault();e.stopPropagation();
 filters.page+=action==='next'?1:-1;refresh();
},true);
// Replace the legacy ranking page and its background warm-up; all other rankings are untouched.
v18221ClubRankPage=function(){return page();};
v18221ScheduleClubRankPrewarm=function(){};
G.rankRebuild18318={version:'18.318',stats,rows:()=>getSnapshot(),refresh,reset:()=>{lastState=null;lastKey='';snapshot=null;},filters};
})();
</script>
"""
def main():
    root=Path(sys.argv[1]); path=root/'src'/'index.html'
    html=path.read_text(encoding='utf-8')
    if MARK in html:return
    required=('function v18221ClubRankPage(', 'function v18221ScheduleClubRankPrewarm(', 'FUTBR_RANK_ROLLOVER_18316')
    for marker in required:
        if marker not in html:raise RuntimeError('Missing ranking dependency: '+marker)
    html=html.replace('</body>',PATCH+'\n</body>',1)
    path.write_text(html,encoding='utf-8')
    (root/'ranking-rebuild-18318-install.json').write_text(json.dumps({'ok':True,'version':'18.318','replacesLegacyView':True,'memorySnapshot':True,'titleColumns':['L','C','I','M','R','O']},indent=2),encoding='utf-8')
if __name__=='__main__':main()
