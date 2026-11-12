from __future__ import annotations
import json, sys
from pathlib import Path
VERSION='18.314'
def once(src, old, new, label):
    n=src.count(old)
    if n != 1: raise RuntimeError(f'{label}: esperado 1, encontrado {n}')
    return src.replace(old,new,1)
def main():
    if len(sys.argv)!=2: raise SystemExit('usage: fix_rank_details_18314.py <project-dir>')
    root=Path(sys.argv[1]).resolve(); path=root/'src'/'index.html'; html=path.read_text(encoding='utf-8')
    if 'FUTBR_RANK_CACHE_18314' in html:
        print('18.314 already applied'); return
    old="function currentRankKey(){const c=typeof v86RankCache!=='undefined'?v86RankCache:null,f=typeof v632ClubFilter!=='undefined'?v632ClubFilter:{};return [c?.stamp,c?.day,c?.titleRevision,c?.dirty?1:0,c?.refreshing?1:0,c?.rows?.length||0,f?.query||'',f?.conf||'all',f?.country||'all',Number(f?.page)||0].join('|');}"
    new="function currentRankKey(){const c=typeof v86RankCache!=='undefined'?v86RankCache:null,f=typeof v632ClubFilter!=='undefined'?v632ClubFilter:{};return [c?.stamp,c?.day,c?.titleRevision,c?.dirty?1:0,c?.refreshing?1:0,c?.building?1:0,c?.ready?1:0,Number(c?.progress)||0,Number(c?.refreshDone)||0,Number(c?.refreshCount)||0,c?.rows?.length||0,f?.query||'',f?.conf||'all',f?.country||'all',Number(f?.page)||0].join('|');}"
    html=once(html,old,new,'ranking render cache key')
    html += """
<script id="gfc-v18314-ranking-cache-fix">
/* FUTBR_RANK_CACHE_18314 */
window.GestorFC=window.GestorFC||{};
window.GestorFC.v18314={version:'18.314',ranking:{detailsAfter100:true,cacheTracksBuildState:true,visualUnchanged:true},status:()=>({ready:!!v86RankCache?.ready,building:!!v86RankCache?.building,progress:Number(v86RankCache?.progress)||0,refreshing:!!v86RankCache?.refreshing,refreshDone:Number(v86RankCache?.refreshDone)||0,refreshCount:Number(v86RankCache?.refreshCount)||0})};
</script>
"""
    path.write_text(html,encoding='utf-8')
    report={'ok':True,'version':VERSION,'rankingDetailsAfter100':True,'cacheTracks':['building','ready','progress','refreshDone','refreshCount'],'visualUnchanged':True}
    (root/'ranking-cache-18314-install.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__': main()
