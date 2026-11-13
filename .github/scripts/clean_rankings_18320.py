from pathlib import Path
import sys, json, re

VERSION='18.320'
MARK='FUTBR_RANK_CORE_18320_START'

CORE=r"""
/* FUTBR_RANK_CORE_18320_START */
/* Motor no escopo original da carreira. Sem timers, sem espera de 0% e sem patches globais. */
const v18320RankSnapshot={state:null,key:'',rows:[],records:Object.create(null),builds:0,hits:0,elapsedMs:0};
const v18320TitleKeys=['L','C','I','M','R','O'];
const v18320IntlKeys=new Set(['ucl','lib','uel','sud','uecl','concacaf','afc','caf','ofc','afc2','caf2']);
function v18320Category(key){
 const k=String(key||'').toLowerCase();
 if(k==='cwc'||k==='icup'||k==='club_world_cup'||k==='clubworldcup'||k==='mundial'||k==='supermundial'||k.includes('world_cup'))return 'M';
 if(k.includes('recopa')||k.includes('supercopa')||k.includes('supercup'))return 'R';
 if(k.startsWith('league:')||k.startsWith('liga:'))return 'L';
 if(k.startsWith('cup:')||k.startsWith('copa:'))return 'C';
 if(v18320IntlKeys.has(k)||k.startsWith('international:')||k.startsWith('continental:'))return 'I';
 return 'O';
}
function v18320Weight(key,rec){
 const k=String(key||'').toLowerCase(),cat=v18320Category(k);
 if(k==='cwc')return 30;if(k==='icup')return 20;
 if(k==='ucl'||k==='lib')return 20;
 if(['concacaf','afc','caf'].includes(k))return 16;
 if(k==='uel'||k==='sud')return 14;
 if(['uecl','afc2','caf2','ofc'].includes(k))return 10;
 if(cat==='M')return 20;if(cat==='I')return 12;
 if(cat==='R')return k.includes('supercopa')?4:7;
 if(cat==='L'){const div=Math.max(1,Number(k.split(':')[2])||1);return div===1?10:div===2?3:div===3?2:1;}
 if(cat==='C')return 7;
 const raw=Number(rec?.points);return Number.isFinite(raw)&&raw>0?Math.max(1,Math.min(10,Math.round(raw/15))):2;
}
function v18320RankSignature(s){
 const store=s.v18300ClubRankingStore,comps=s.competitions||{};
 let finished=0;
 for(const c of Object.values(comps))if(c?.champion)finished++;
 const titles=Object.keys(s.cupWinners||{}).length;
 const history=(s.worldHistory||[]).length+':'+(s.internationalHistory||[]).length+':'+(s.v652ClubPerformanceHistory||[]).length;
 return [Number(s.year)||0,Number(s.day)||0,s.seasonDone?1:0,store?.revision||0,store?.recordRevision||0,history,finished,titles,(s.teams||[]).length].join('|');
}
function v18320EnsureRanking(s){
 if(!s)return {rows:[],ready:true};
 const signature=v18320RankSignature(s),cache=v18320RankSnapshot;
 if(cache.state===s&&cache.key===signature&&cache.rows.length){cache.hits++;return {rows:cache.rows,ready:true};}
 const started=performance.now(),year=Number(s?.year)||2026;
 const windowRank=typeof E.rankWindow633==='function'?E.rankWindow633(s):{start:year-3,end:year};
 const rangeStart=Number(windowRank?.start)||((Number(s.year)||2026)-3);
 const rangeEnd=Number(windowRank?.end)||Number(s.year)||2026;
 const teams=new Map((s.teams||[]).map(t=>[String(t.id),t]));
 const titles=new Map(),unique=new Set(),perform=new Map();
 function addTitle(id,year,key,label,record){
  const yr=Number(year),club=String(id||'');
  if(!teams.has(club)||!Number.isFinite(yr)||yr<rangeStart||yr>rangeEnd)return;
  const tkey=String(key||'').toLowerCase();
  if(!tkey||tkey.startsWith('promotion:'))return;
  const sig=club+'|'+yr+'|'+tkey;
  if(unique.has(sig))return;unique.add(sig);
  const a=titles.get(club)||[],points=v18320Weight(tkey,record);
  a.push({year:yr,key:tkey,label:String(label||tkey),points});titles.set(club,a);
 }
 function addPerformance(id,pts){
  const club=String(id||'');if(!teams.has(club))return;
  const value=Number(pts);
  if(Number.isFinite(value))perform.set(club,(perform.get(club)||0)+value);
 }
 // Snapshot da carreira: historico por clube agregado em uma unica leitura.
 for(const h of s.v652ClubPerformanceHistory||[]){
  const year=Number(h?.year);if(!Number.isFinite(year)||year<rangeStart||year>rangeEnd)continue;
  for(const [id,rec] of Object.entries(h.clubs||{}))addPerformance(id,(Number(rec?.leaguePoints)||0)+(Number(rec?.cupPoints)||0));
 }
 for(const h of s.worldHistory||[]){
  const year=Number(h?.year);if(year<rangeStart||year>rangeEnd)continue;
  for(const row of h.countries||[]){
   const country=String(row?.country||'');
   addTitle(row?.champion,year,'league:'+country+':1','Liga nacional',row);
   addTitle(row?.secondChampion,year,'league:'+country+':2','Segunda divisao',row);
   addTitle(row?.cup,year,'cup:'+country,'Copa nacional',row);
  }
 }
 for(const h of s.internationalHistory||[]){
  const year=Number(h?.year);if(year<rangeStart||year>rangeEnd)continue;
  addTitle(h?.champion,year,String(h?.id||''),String(h?.name||h?.id||'Competicao'),h);
  for(const [id,value] of Object.entries(h?.points||{}))addPerformance(id,Number(value)||0);
 }
 for(const coach of Object.values(s.coaches||{})){
  for(const rec of coach?.titles||[]){
   const year=Number(rec?.year),club=String(rec?.club||rec?.clubId||'');
   if(club&&teams.has(club))addTitle(club,year,rec?.key||rec?.id,rec?.label||rec?.name,rec);
  }
 }
 if(Number(s.year)>=rangeStart&&Number(s.year)<=rangeEnd){
  for(const [country,club] of Object.entries(s.cupWinners||{}))
   addTitle(club,s.year,'cup:'+country,'Copa nacional',{});
  for(const [id,comp] of Object.entries(s.competitions||{})){
   if(!comp?.champion||id==='mls')continue;
   addTitle(comp.champion,s.year,String(comp.id||id),String(comp.name||id),comp);
  }
  // MLS usa o campeao dos playoffs, nao a lideranca da temporada regular.
  if(s.competitions?.mls?.champion)
   addTitle(s.competitions.mls.champion,s.year,'league:usa:1','MLS Cup',{});
 }
 const rows=[],records=Object.create(null),existing=s.v18300ClubRankingStore?.records||v86RankCache?.records||{};
 const catalog=new Map((WorldCatalog.countries||[]).map(x=>[String(x.id),x]));
 for(const t of teams.values()){
  const id=String(t.id),country=String(t.country||''),nation=catalog.get(country);
  const conf=String(nation?.confederation||E.country(country)?.confederation||'');
  if(!conf)continue;
  const st=t.stats||{},games=Math.max(0,Number(st.p)||0),wins=Number(st.w)||0,draws=Number(st.d)||0,losses=Number(st.l)||0;
  const saved=existing[id],snapshotGames=Number(saved?.games)||0;
  records[id]=snapshotGames>games?{games:snapshotGames,wins:Number(saved?.wins)||0,draws:Number(saved?.draws)||0,losses:Number(saved?.losses)||0}:{games,wins,draws,losses};
  const div=Math.max(1,Number(t.division)||1),tier=div===1?1:div===2?.45:div===3?.28:.18;
  const points=Number(st.pts)||wins*3+draws;
  const current=games>0?(12*Math.min(1,points/(games*3))+4*Math.min(1,wins/games))*tier:0;
  const perf=Math.round(((perform.get(id)||0)+current)*10)/10;
  const ledger=titles.get(id)||[],titlePoints=ledger.reduce((total,x)=>total+Number(x.points||0),0);
  const score=Math.round((perf+titlePoints)*10)/10;
  rows.push({id,name:String(t.name||id),short:String(t.short||''),country,conf,
   base:Number(t.base)||0,points:score,totalPoints:score,performancePoints:perf,
   titlePoints,titleCount:ledger.length,titles:ledger,
   globalRank:0,_approx:false});
 }
 rows.sort((a,b)=>b.totalPoints-a.totalPoints||b.performancePoints-a.performancePoints||b.titlePoints-a.titlePoints||b.base-a.base||a.name.localeCompare(b.name,'pt-BR'));
 const top=rows.slice(0,1000);top.forEach((r,i)=>{r.globalRank=i+1;});
 cache.state=s;cache.key=signature;cache.rows=top;cache.records=records;
 cache.builds++;cache.elapsedMs=Math.round(performance.now()-started);
 return {rows:top,ready:true};
}
function v18320Record(id){return v18320RankSnapshot.records?.[id]||{games:0,wins:0,draws:0,losses:0};}
window.GestorFC.rankClean18320={
 version:'18.320',
 status:()=>({builds:v18320RankSnapshot.builds,hits:v18320RankSnapshot.hits,elapsedMs:v18320RankSnapshot.elapsedMs,rows:v18320RankSnapshot.rows.length,version:'18.320'}),
 rows:()=>v18320RankSnapshot.rows
};
/* FUTBR_RANK_CORE_18320_END */
"""

REMOVE_SCRIPTS=['gfc-v18314-ranking-cache-fix','gfc-v18315-sparse-title-ranking',
                'gfc-v18316-rank-rollover-carry','gfc-v18317-title-engine',
                'futbr-ranking-18318']

def once(text,old,new,label):
    n=text.count(old)
    if n!=1:raise RuntimeError(label+': expected 1, found '+str(n))
    return text.replace(old,new,1)

def main():
    root=Path(sys.argv[1]).resolve();p=root/'src'/'index.html'
    html=p.read_text(encoding='utf-8')
    if MARK in html:print('18.320 already installed');return
    for script_id in REMOVE_SCRIPTS:
        regex=r'\s*<script id="'+re.escape(script_id)+r'">[\s\S]*?</script>'
        html,n=re.subn(regex,'',html,count=1)
        if n!=1:raise RuntimeError('Legacy script not found: '+script_id)
    old_start='function v86ClubRankingPage(){'
    old_end='// Desliga inteiramente o cache mundial'
    start=html.find(old_start);end=html.find(old_end,start)
    if start<0 or end<0:raise RuntimeError('Native ranking code anchors not found')
    renderer=html[start:end]
    renderer=once(renderer,'try{c=v86EnsureBuild(false);}','try{c=v18320EnsureRanking(state);}','Engine substitution')
    renderer=once(renderer,'rr=v86Record(r.id)','rr=v18320Record(r.id)','Record substitution')
    status_start=renderer.find(' const status=')
    status_end=renderer.find(' const body=rows.map',status_start)
    if status_start<0 or status_end<0:raise RuntimeError('Status rendering anchors not found')
    renderer=(renderer[:status_start]+
      ' const status="Motor limpo 18.320 · Top 1.000 consolidado · "+nf.format(base.length)+" clubes · temporada "+(Number(state?.year)||0);\n'+
      renderer[status_end:])
    html=html[:start]+CORE+'\n'+renderer+html[end:]
    html=once(html,"else if(view==='clubrankings')v18220PageHTML=v18221ClubRankPage();",
         "else if(view==='clubrankings')v18220PageHTML=v86ClubRankingPage();",
         'Native main page route')
    html=once(html,"if(view!=='clubrankings')v18221ScheduleClubRankPrewarm();",
         "/* 18.320: previous rank warm-up disabled */",
         'Disable historical warmup')
    for marker in [MARK,"v18220PageHTML=v86ClubRankingPage()","Motor limpo 18.320"]:
        if marker not in html:raise RuntimeError('Missing clean engine marker '+marker)
    for old_id in REMOVE_SCRIPTS:
        if '<script id="'+old_id+'">' in html:raise RuntimeError('Legacy ranking script remains: '+old_id)
    p.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,'engine':'native lexical scope',
      'rankRoute':'v86ClubRankingPage (original page writer)',
      'removedScripts':REMOVE_SCRIPTS,'oldPrewarmDisabled':True,
      'browserVisibleMarker':'Motor limpo 18.320',
      'titleColumns':v18320_keys(),'buildsWithoutPreexistingCaches':True}
    (root/'ranking-clean-18320-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
def v18320_keys():return ['L','C','I','M','R','O']
if __name__=='__main__':main()
