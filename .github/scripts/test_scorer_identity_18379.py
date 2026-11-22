"""Exercise real 18.379 scorer UI and archive source with a focused game-state fixture."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

def main():
 if len(sys.argv)!=2:raise SystemExit("usage: test_scorer_identity_18379.py <prepared-root>")
 root=Path(sys.argv[1]).resolve()
 html=(root/'src/index.html').read_text(encoding='utf-8')
 begin=html.index("/* FUTBR_SCORERS_IN_SCOPE_18220_START */")
 end=html.index("/* FUTBR_SCORERS_IN_SCOPE_18220_END */",begin)+len("/* FUTBR_SCORERS_IN_SCOPE_18220_END */")
 base=html[begin:end]
 begin=html.index("/* FUTBR_SCORER_HISTORY_RECOVERY_18377",end)
 end=html.index("window.GestorFC.render=render;",begin)
 patched=html[begin:end]
 assert base.count('v18220Esc(v18379CleanScorerName(row.name))')==2
 for marker in ["FUTBR_SCORER_IDENTITY_18379","v18379FindClub","v18379HistoricalPlayerClubs"]:
  if marker not in patched:raise RuntimeError("Missing release patch: "+marker)
 mock=r"""
const assert=require('node:assert/strict');
global.window=global;window.GestorFC={};
let state=null;
let scorerFilter={kind:'all',country:'all',division:'all',year:'all',query:'',nationality:'all',page:0};
const C=[{id:'ukr',name:'Ucrania'}],WorldCatalog={countries:C};
const NAT={UKR:['Ucrania'],POL:['Polonia'],CZE:['Tchequia'],SRB:['Servia']};
const E={
 normName:x=>String(x||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(),
 team:(s,id)=>(s.teams||[]).find(t=>String(t.id)===String(id))||null
};
function esc(x){return String(x??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}
function nation(code){return '<span class="nationality">'+({UKR:'🇺🇦',POL:'🇵🇱',CZE:'🇨🇿'}[code]||'')+' '+esc(code)+'</span>';}
function badge(team){return '<span class="club-crest" data-crest="'+esc(team.id)+'"></span>';}
function teamButton(team){return '<button data-action="team" data-team="'+esc(team.id)+'">'+esc(team.name)+'</button>';}
function v640Flag(code){return code}
function v677RankingTabs(){return '<nav>RANKINGS</nav>'}
function v320Players(s){return Object.values(s.players||{})}
"""
 test=r"""
const s={
 year:2033,day:30,seasonDone:false,teams:[
  {id:'tv',name:'NK Veres Rivne',short:'VER',color:'#289a50'},
  {id:'ts',name:'Slovan Varnsdorf',short:'SV',color:'#234'},
  {id:'tb',name:'FC Balkany Zorya',short:'FBZ',color:'#f05'},
  {id:'te',name:'Ekstraklasa',short:'EKS',color:'#aaa'},
  {id:'td',name:'FK Varnsdorf',short:'FVK',color:'#bbb'}
 ],
 players:{
  p4:{id:'p4',name:'Jogador ativo',natCode:'SRB',clubId:'tv'}
 },
 allTimeStats:{
  p1:{id:'p1',name:'Milan Jovanovic 🇺🇦',natCode:'UKR',goals:106,apps:352,clubs:{tv:'Veres'}},
  p2:{id:'p2',name:'Milan Jovanovic 🇵🇱',natCode:'POL',goals:105,apps:326,clubs:{unknown:'Slovan Varnsdorf'}},
  p3:{id:'p3',name:'Lazar Jovanovic 🇨🇿',natCode:'CZE',goals:91,apps:298,clubs:{unknown:'Copa desconhecida'}},
  p4:{id:'p4',name:'Jogador ativo',natCode:'SRB',goals:87,apps:295,clubs:{}},
  p5:{id:'p5',name:'Milan Retirado 🇵🇱',natCode:'POL',goals:79,apps:238,clubs:{unknown:'Ekstraklasa'}},
  p6:{id:'p6',name:'Atleta sem clube',natCode:'POL',goals:73,apps:249,clubs:{unknown:'Grupo sem clube real'}}
 },
 scorerArchive:[],competitionStats:{},v640National:{playerStats:{}},
 v555CareerArchive:{
  2026:{n:{tb:'FC Balkany Zorya',ts:'Slovan Varnsdorf'},p:{
    p3:'tb|26|18|3|1|0;ts|4|2|0|0|0'
  }}
 },
 v538CareerArchive:{2027:{p3:[{teamId:'tb',teamName:'FC Balkany Zorya',apps:28,goals:8}]}}
};
state=s;
const immutableBefore=JSON.stringify(s);
const htmlGlobal=v18220ScorersContent(s,scorerFilter);
assert(htmlGlobal.includes('data-crest="tv"')&&htmlGlobal.includes('data-team="tv"'),'Veres linked by ID');
assert(htmlGlobal.includes('data-crest="ts"')&&htmlGlobal.includes('data-team="ts"'),'Slovan Varnsdorf linked by name');
assert(htmlGlobal.includes('data-crest="tb"')&&htmlGlobal.includes('data-team="tb"'),'Archived Balkany team resolved by player ID');
assert(htmlGlobal.includes('data-crest="te"')&&htmlGlobal.includes('data-team="te"'),'Legacy Ekstraklasa catalogue team has working link');
assert(!htmlGlobal.includes('Milan Jovanovic 🇺🇦')&&!htmlGlobal.includes('Milan Jovanovic 🇵🇱'),'Trailing duplicated name flags hidden');
assert(htmlGlobal.includes('🇺🇦 UKR')&&htmlGlobal.includes('🇵🇱 POL'),'Nationality column kept');
assert(htmlGlobal.includes('Atleta sem clube'),'Unknown athlete kept');
assert(htmlGlobal.includes('v18379-unknown-club'),'Unresolvable team not mapped to a wrong club');
assert(htmlGlobal.includes('data-action="player"')||htmlGlobal.includes('Milan Jovanovic'),'Scorer rows not lost');

scorerFilter={...scorerFilter,year:'2026'};
const past=v18220Collect(s,scorerFilter);
assert(past.some(p=>p.id==='p3'&&p.goals===20),'Historic scorer goals preserved');
const sourcePast=v18220ClubHTML(s,past.find(p=>p.id==='p3'),'all');
assert(sourcePast.includes('data-team="tb"')&&sourcePast.includes('data-team="ts"'),'2026 historical teams rendered with both club links');
assert(!sourcePast.includes('data-team="tv"'),'Do not mislabel 2026 season with current club');
assert.equal(JSON.stringify(s),immutableBefore,'Rendering must not modify saved world');
assert.equal(v18379CleanScorerName('João da Silva 🇧🇷 🇺🇦'),'João da Silva','Remove only trailing flags');
assert.equal(v18379CleanScorerName('José de Ávila'),'José de Ávila','Preserve normal diacritics');
const lookup=window.GestorFC.scorerIdentity18379;
assert.equal(lookup.resolveClub(s,'','Veres'),'tv','Unique partial historical team alias resolution');
assert.equal(lookup.resolveClub(s,'ts','Grupo errado'),'ts','Club id takes precedence over conflicting text');
console.log(JSON.stringify({ok:true,version:'18.379.0',
 realRankingsRendererExecuted:true,existingBadgeAndTeamButton:true,
 careerArchiveSinglePlayerLookup:true,linkedOriginalAndHistoricalTeams:true,
 multipleHistoricClubsLinked:true,playerNameFlagsDeduplicated:true,
 nationalityColumnUnchanged:true,allTimeStatsUnmodified:true,
 historicalTotalsUnmodified:true,unmatchedClubNotFalselyLinked:true,
 testedClubExamples:['Veres','Slovan Varnsdorf','Balkany Zorya','Ekstraklasa']}));
"""
 runner=root/'scorer-identity-18379-fixture.cjs'
 runner.write_text(mock+"\n"+base+"\n"+patched+"\n"+test,encoding='utf-8')
 result=subprocess.run(['node',str(runner)],text=True,capture_output=True,timeout=120)
 try:runner.unlink()
 except OSError:pass
 if result.returncode:raise RuntimeError('FutBR 18.379 actual-source regression: '+(result.stderr or result.stdout)[-4500:])
 report=json.loads(result.stdout.strip().splitlines()[-1])
 report['sourceSha256']=hashlib.sha256(html.encode('utf-8')).hexdigest()
 (root/'scorer-identity-18379-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
