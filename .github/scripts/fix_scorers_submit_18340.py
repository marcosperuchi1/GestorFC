from __future__ import annotations
import json
import sys
from pathlib import Path

MARKER = 'FUTBR_SCORER_SEARCH_SUBMIT_18340'

CANONICAL = '''<div class="field grow"><label for="score-query">Buscar atleta</label><input id="score-query" data-v641-score-query value="'+v18220Esc(f.query)+'" placeholder="Nome do jogador"></div>'''
CANONICAL_NEW = '''<div class="field grow"><label for="score-query">Buscar atleta</label><div class="flex" style="gap:8px;align-items:center"><input id="score-query" type="search" style="flex:1;min-width:0" data-v641-score-query value="'+v18220Esc(v18340ScorerDraft===null?f.query:v18340ScorerDraft)+'" placeholder="Nome do jogador"><button class="btn small" type="button" data-v18340-score-search="1">Pesquisar</button></div></div>'''

FALLBACK = '''<div class="field grow"><label for="score-query">Buscar atleta</label><input id="score-query" data-v641-score-query value="${esc(f.query)}" placeholder="Nome do jogador"></div>'''
FALLBACK_NEW = '''<div class="field grow"><label for="score-query">Buscar atleta</label><div class="flex" style="gap:8px;align-items:center"><input id="score-query" type="search" style="flex:1;min-width:0" data-v641-score-query value="${esc(v18340ScorerDraft===null?f.query:v18340ScorerDraft)}" placeholder="Nome do jogador"><button class="btn small" type="button" data-v18340-score-search="1">Pesquisar</button></div></div>'''

OLD_INPUT = "document.addEventListener('input',event=>{const el=event.target;if(el?.dataset?.v641ScoreQuery!==undefined){scorerFilter.query=el.value;scorerFilter.page=0;v96ScheduleScorerSearch(el);}},true);"

NEW_EVENTS = r'''
/* FUTBR_SCORER_SEARCH_SUBMIT_18340: the filter applies ONLY on button click or Enter.
   Keeping a draft also avoids losing typed text when another filter re-renders. */
let v18340ScorerDraft=null;
function v18340CommitScorerSearch(input){
 if(!input||view!=='rankings')return false;
 const query=String(input.value??'').trim();
 v18340ScorerDraft=null;
 if(query===String(scorerFilter.query??''))return false;
 scorerFilter.query=query;scorerFilter.page=0;
 const scroll=document.querySelector('.v615-ranking-scroll')?.scrollTop||0;
 render();
 requestAnimationFrame(()=>{
  const found=document.querySelector('[data-v641-score-query]');
  const sc=document.querySelector('.v615-ranking-scroll');
  if(sc)sc.scrollTop=scroll;
  if(found)try{found.focus({preventScroll:true});found.setSelectionRange?.(found.value.length,found.value.length);}catch(e){}
 });
 return true;
}
document.addEventListener('input',event=>{
 const el=event.target;
 if(el?.dataset?.v641ScoreQuery!==undefined)v18340ScorerDraft=String(el.value??'');
},true);
document.addEventListener('keydown',event=>{
 const el=event.target;
 if(event.key==='Enter'&&!event.isComposing&&el?.dataset?.v641ScoreQuery!==undefined){
  event.preventDefault();event.stopPropagation();
  v18340CommitScorerSearch(el);
 }
},true);
document.addEventListener('click',event=>{
 const button=event.target?.closest?.('[data-v18340-score-search]');
 if(!button)return;
 event.preventDefault();event.stopPropagation();
 const input=button.parentElement?.querySelector?.('[data-v641-score-query]')||
  document.querySelector('[data-v641-score-query]');
 v18340CommitScorerSearch(input);
},true);
'''

def replace_one(src, before, after, label):
    count=src.count(before)
    if count!=1:
        raise RuntimeError(f'18.340 {label}: expected one anchor, found {count}')
    return src.replace(before, after, 1)


def main():
    if len(sys.argv)!=2:
        raise SystemExit('usage: fix_scorers_submit_18340.py <project-dir>')
    root=Path(sys.argv[1]).resolve()
    path=root/'src/index.html'
    html=path.read_text(encoding='utf-8')
    if MARKER in html:raise RuntimeError('Scorer search already modified; expected clean build')
    if 'FUTBR_SCORERS_IN_SCOPE_18220_START' not in html:
        raise RuntimeError('Canonical scorers UI missing; do not patch legacy overlay')
    html=replace_one(html, CANONICAL, CANONICAL_NEW, 'canonical scorers search markup')
    html=replace_one(html, FALLBACK, FALLBACK_NEW, 'fallback scorers markup')
    html=replace_one(html, OLD_INPUT, NEW_EVENTS, 'reactive scorer input handler')
    path.write_text(html,encoding='utf-8')
    report={'ok':True,'version':'18.340','onInputOnlySaveDraft':True,
            'onButtonSearch':True,'onEnterSearch':True,
            'noRecomputePerKeypress':True,'allowsClearingQuery':True,
            'preservesFilters':True,'preservesStatistics':True,
            'clickAndEnterBothSupported':True}
    (root/'scorers-submit-18340-install.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
