from __future__ import annotations
import re
import sys
from pathlib import Path


def fail(message: str) -> None:
    raise RuntimeError(message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: esperado 1, encontrado {count}")
    return text.replace(old, new, 1)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: fix_scorers_safe_state.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    pattern = re.compile(
        r'(<script id="futbr-scorers-render-root-18211">)([\s\S]*?)(</script>)',
        re.I,
    )
    match = pattern.search(html)
    if not match:
        fail("script 18.211 ausente")
    script = match.group(2)

    script = replace_once(
        script,
        " let cacheState=null,cacheStamp='',cacheRows=[];\n function escSafe",
        " let cacheState=null,cacheStamp='',cacheRows=[];\n function v18212State(){try{return typeof state!=='undefined'?state:(window.state||null);}catch(e){try{return window.state||null;}catch(_){return null;}}}\n function escSafe",
        "helper de estado seguro",
    )
    script = replace_once(
        script,
        " function liveRows(){\n  const s=state;if(!s)return [];",
        " function liveRows(){\n  const s=v18212State();if(!s)return [];",
        "estado seguro em liveRows",
    )
    script = replace_once(
        script,
        " function fallbackContent(error=null){\n  const rows=liveRows().slice(0,100);",
        " function fallbackContent(error=null){\n  const s=v18212State(),rows=liveRows().slice(0,100);",
        "estado seguro no fallback",
    )
    script = script.replace("state?.players?.[row.id]", "s?.players?.[row.id]")
    script = script.replace("E.team(state,p.clubId)", "E.team(s,p.clubId)")
    script = script.replace("state?.year", "s?.year")
    script = replace_once(
        script,
        "preservesPerformanceArchitecture:true,lastRichError:''",
        "preservesPerformanceArchitecture:true,safeStateLookup:true,lastRichError:''",
        "marcador de estado seguro",
    )

    for forbidden in (
        "const s=state;if(!s)return [];",
        "state?.players?.[row.id]",
        "E.team(state,p.clubId)",
    ):
        if forbidden in script:
            fail("acesso inseguro ainda presente: " + forbidden)
    for required in (
        "function v18212State()",
        "const s=v18212State();if(!s)return [];",
        "safeStateLookup:true",
    ):
        if required not in script:
            fail("marcador seguro ausente: " + required)

    html = html[:match.start()] + match.group(1) + script + match.group(3) + html[match.end():]
    index_path.write_text(html, encoding="utf-8")
    print("Scorers state lookup made safe for WebView/login runtime")


if __name__ == "__main__":
    main()
