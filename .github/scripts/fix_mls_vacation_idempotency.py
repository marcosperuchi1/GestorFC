from __future__ import annotations
import re, sys
from pathlib import Path


def function_bounds(src: str, name: str) -> tuple[int, int]:
    match=re.search(r"function\s+"+re.escape(name)+r"\s*\(",src)
    if not match:
        raise RuntimeError(f"funcao ausente: {name}")
    brace=src.find("{",match.end());depth=0;quote=None;escaped=False
    for index in range(brace,len(src)):
        ch=src[index]
        if quote:
            if escaped:escaped=False
            elif ch=="\\":escaped=True
            elif ch==quote:quote=None
            continue
        if ch in ("'",'"',"`"):quote=ch;continue
        if ch=="{":depth+=1
        elif ch=="}":
            depth-=1
            if depth==0:return match.start(),index+1
    raise RuntimeError(f"funcao nao fechada: {name}")


def main() -> None:
    if len(sys.argv)!=2:
        raise SystemExit("usage: fix_mls_vacation_idempotency.py <project-dir>")
    root=Path(sys.argv[1]).resolve();path=root/"src"/"index.html"
    html=path.read_text(encoding="utf-8")
    if "preserveCompletedStages:true" in html:
        print("MLS idempotency fix already present")
        return
    start,end=function_bounds(html,"v18200MLSPruneObsoleteFuture")
    replacement=r'''function v18200MLSPruneObsoleteFuture(s,required){
    if(required==null||!Array.isArray(s?.schedule))return 0;const day=Math.max(0,Number(s.day)||0),old=s.schedule;let before=0,removed=0,keptRequired=false;
    s.schedule=old.filter((d,i)=>{
      if(i<day||d?.type!=='mlsplayoff')return true;
      // Uma fase com qualquer resultado e historica e nunca pode ser apagada.
      // A normalizacao anterior ja elimina somente copias vazias do mesmo round.
      if((d.fixtures||[]).some(f=>f?.result))return true;
      const r=Number(d.round);
      if(r<Number(required)){removed++;if(i<day)before++;return false;}
      if(r===Number(required)){if(keptRequired){removed++;return false;}keptRequired=true;}
      return true;
    });
    s.day=Math.max(0,day-before);return removed;
  }'''
    html=html[:start]+replacement+html[end:]
    html=html.rstrip()+"\n<script id=\"futbr-mls-idempotency-18202\">window.GestorFC=window.GestorFC||{};window.GestorFC.mlsIdempotency18202={version:'18.202',preserveCompletedStages:true,removeOnlyEmptyDuplicates:true};</script>\n"
    path.write_text(html,encoding="utf-8")
    print("MLS completed-stage preservation 18.202 applied")


if __name__=="__main__":
    main()
