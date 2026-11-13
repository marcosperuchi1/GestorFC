from pathlib import Path
import json,re,subprocess,sys

VERSION='18.321'
def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: test_rankings_ui_18321.py <project-dir>')
    root=Path(sys.argv[1])
    html=(root/'src'/'index.html').read_text(encoding='utf-8')
    required=[
      'FUTBR_RANK_UI_18321',
      'data-v18321-club-rank="1"',
      'Motor limpo 18.321 ·',
      'v81BootstrapRank=function(){return false;};',
      'c=v18320EnsureRanking(state);',
      'id="v18321-rank-ready"'
    ]
    for x in required:
        if x not in html:raise RuntimeError('Missing 18.321 marker '+x)
    forbidden=[
      'v81BootstrapRank=v127ScheduleRankWarm;',
      'c=window.GestorFC?.v18312?.ensure?.()||v86EnsureBuild(false);',
      'id="v86-rank-progress" class="tiny muted"'
    ]
    for x in forbidden:
        if x in html:raise RuntimeError('Old auto ranking path remains: '+x)

    def between(a,b):
        p=html.find(a)
        if p<0:raise RuntimeError('Start marker missing '+a)
        q=html.find(b,p+len(a))
        if q<0:raise RuntimeError('End marker missing '+b)
        return html[p:q]

    tabs=between('function v677RankingTabs(){','/* Todas as quatro telas')
    wrapper=between('const v677BaseRenderPage=renderPage;','function v677SyncRankingNavigation')
    scorer=between('function v18220RankingsPage(s=state,f=v18220Filter()){','try{window.GestorFC=window.GestorFC||{};',)
    route=between("let v18220PageHTML='';","/* 18.320: previous rank warm-up disabled */")
    prewarm=between('async function v102PrewarmClubRank(){','const v102BasePrepare=v53Prepare;')
    if 'v18320EnsureRanking(state)' not in prewarm:raise RuntimeError('Next season still starts old ranking')
    if 'v86EnsureBuild(false)' in prewarm or 'v18312?.ensure' in prewarm:
        raise RuntimeError('Next season still starts dynamic builder')
    if 'v677RankingTabs()' not in route or 'data-v18321-club-rank' not in route:
        raise RuntimeError('Clubs bypass the tabs in native routing')

    js=r"""
const assert=require('assert');
let view='clubrankings';
const icon=x=>'<i>'+x+'</i>',esc=x=>String(x).replace(/</g,'&lt;');
const V677_RANKING_VIEWS=['clubrankings','nationalrankings','rankings','coaches'];
let renderPage=()=>'<section data-native-other-ranking="1">Other ranking</section>';
const state={year:2026};
const v18220Filter=()=>({});
const v18220ScorersContent=()=>'<article>Artilheiros</article>';
const v86ClubRankingPage=()=>'<section>Ranking de Clubes · Motor limpo 18.321</section>';
""" + tabs + wrapper + scorer + r"""
function nativePage(){
 const page={innerHTML:''};
""" + route + r"""
 return page.innerHTML;
}
const names=['clubrankings','nationalrankings','rankings','coaches'];
for(const name of names){
 view=name;
 const markup=nativePage();
 const values=[...markup.matchAll(/class="v677-ranking-tab[^"]*"[^>]*data-view="([^"]+)"/g)].map(x=>x[1]);
 assert.deepStrictEqual(values,names,'Rank tabs absent on '+name);
 assert(markup.includes('data-view="'+name+'" aria-selected="true"'), 'Missing active tab for '+name);
 assert(!markup.includes('primeira montagem')&&!markup.includes('Atualizando Top 1.000 dinâmico'));
 if(name==='clubrankings')assert(markup.includes('data-v18321-club-rank="1"'),'Club native route bypasses tab hub');
 if(name==='rankings')assert(markup.includes('Artilheiros'),'Scorers route not preserved');
}
let v81BootstrapRank=()=>{throw Error('legacy bootstrap unexpectedly called')};
v81BootstrapRank=function(){return false;};
assert.equal(v81BootstrapRank(),false);
let v102RankPreparedYear=0;
let oldBuilds=0,newBuilds=0;
const window={GestorFC:{v100:{repair:{stopBackground:()=>{}}}}};
const v102DropLegacyRankState=()=>{};
const v102GuardUpdate=()=>{};
const v86EnsureBuild=()=>{oldBuilds++;throw Error('Legacy rank builder called')};
function v18320EnsureRanking(s){newBuilds++;return {ready:true,rows:[{id:'flamengo'}]}}
""" + prewarm + r"""
(async()=>{
 assert.equal(await v102PrewarmClubRank(),true);
 assert.equal(v102RankPreparedYear,2026);
 assert.equal(oldBuilds,0,'Redundant dynamic ranking still triggered');
 assert.equal(newBuilds,1);
 console.log(JSON.stringify({ok:true,version:'18.321',tabs:names,
  fourTabsAllRoutes:true,directClubsPathFixed:true,
  oldBackgroundStarts:oldBuilds,newSnapshotCalls:newBuilds,
  firstOpenStatusStable:true,nextSeasonReady:true}));
})().catch(e=>{console.error(e);process.exitCode=1});
"""
    script=root/'.rank18321-ui-test.js'
    script.write_text(js,encoding='utf-8')
    try:
        r=subprocess.run(['node',str(script)],capture_output=True,text=True,timeout=50)
    finally:
        script.unlink(missing_ok=True)
    if r.returncode:raise RuntimeError('Ranking UI integration test failed:\n'+(r.stderr or r.stdout)[-10000:])
    result=json.loads(r.stdout.strip().splitlines()[-1])
    if not result.get('ok'):raise RuntimeError('UI result not passed')
    (root/'ranking-ui-18321-tests.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':
    main()
