from __future__ import annotations
import json
import re
import sys
from pathlib import Path


def find_function(src: str, name: str) -> str | None:
    patterns = [
        re.compile(r"function\s+" + re.escape(name) + r"\s*\("),
        re.compile(re.escape(name) + r"\s*=\s*function\s*\("),
    ]
    match = None
    for pattern in patterns:
        match = pattern.search(src)
        if match:
            break
    if not match:
        return None
    brace = src.find("{", match.end())
    if brace < 0:
        return None
    depth = 0
    quote = None
    escaped = False
    template_depth = 0
    for i in range(brace, len(src)):
        ch = src[i]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote and template_depth == 0:
                quote = None
            elif quote == "`" and ch == "$" and i + 1 < len(src) and src[i + 1] == "{":
                template_depth += 1
            elif quote == "`" and ch == "}" and template_depth:
                template_depth -= 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return src[match.start(): i + 1]
    return None


def contexts(src: str, token: str, radius: int = 800, limit: int = 20) -> list[dict]:
    out = []
    start = 0
    while len(out) < limit:
        pos = src.find(token, start)
        if pos < 0:
            break
        out.append({
            "position": pos,
            "context": src[max(0, pos - radius): min(len(src), pos + len(token) + radius)],
        })
        start = pos + len(token)
    return out


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: diagnose_scorers_root.py <project-dir>")
    project = Path(sys.argv[1]).resolve()
    html_path = project / "src" / "index.html"
    html = html_path.read_text(encoding="utf-8")

    script_ids = []
    for m in re.finditer(r"<script(?:\s+[^>]*?id=[\"']([^\"']+)[\"'])?[^>]*>", html, re.I):
        script_ids.append({"id": m.group(1) or "", "position": m.start()})

    named = {}
    for name in [
        "scorersPage",
        "renderPage",
        "v677RankingTabs",
        "v18198ScorersPage",
        "v18198ClubRows",
        "v18198Merge",
        "v18203CollectRows",
        "v18203Scorers",
        "v18203Paint",
        "v3ApplyMatch",
        "v640RecordNationalPlayerStats",
    ]:
        block = find_function(html, name)
        if block:
            named[name] = block

    function_hits = []
    for m in re.finditer(r"function\s+([A-Za-z_$][\w$]*)\s*\(", html):
        name = m.group(1)
        block = find_function(html[m.start():], name)
        if not block:
            continue
        if any(token in block for token in ("competitionStats", "scorerArchive", "allTimeStats")):
            function_hits.append({"name": name, "position": m.start(), "block": block[:24000]})
        if len(function_hits) >= 50:
            break

    report = {
        "htmlBytes": len(html.encode("utf-8")),
        "scriptIds": script_ids,
        "counts": {
            "scorersPageFunction": len(re.findall(r"function\s+scorersPage\s*\(", html)),
            "renderPageFunction": len(re.findall(r"function\s+renderPage\s*\(", html)),
            "renderPageAssignments": html.count("renderPage=function"),
            "competitionStats": html.count("competitionStats"),
            "scorerFilter": html.count("scorerFilter"),
            "viewRankings": html.count("view='rankings'") + html.count('view="rankings"'),
        },
        "namedFunctions": named,
        "statsFunctions": function_hits,
        "contexts": {
            "competitionStats": contexts(html, "competitionStats", 1100, 30),
            "scorerFilter": contexts(html, "scorerFilter", 900, 20),
            "scorersPageCalls": contexts(html, "scorersPage()", 1000, 20),
            "viewRankings": contexts(html, "view==='rankings'", 1000, 20),
            "rankingTabs": contexts(html, "v677RankingTabs", 1000, 20),
        },
    }

    json_path = project / "scorers-root-diagnostic.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "FUTBR MANAGER - DIAGNOSTICO DA ORIGEM DE ARTILHEIROS",
        f"HTML bytes: {report['htmlBytes']}",
        f"Contagens: {json.dumps(report['counts'], ensure_ascii=False)}",
        "",
        "ORDEM DOS SCRIPTS COM ID:",
    ]
    for item in script_ids:
        if item["id"]:
            lines.append(f"{item['position']:>10}  {item['id']}")
    for name, block in named.items():
        lines.extend(["", "=" * 90, f"FUNCAO {name}", "=" * 90, block])
    for item in function_hits:
        lines.extend(["", "#" * 90, f"FUNCAO COM ESTATISTICAS: {item['name']} @ {item['position']}", "#" * 90, item['block']])
    (project / "scorers-root-diagnostic.txt").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "ok": True,
        "htmlBytes": report["htmlBytes"],
        "counts": report["counts"],
        "namedFunctions": list(named),
        "statsFunctions": [x["name"] for x in function_hits],
        "scriptIds": [x["id"] for x in script_ids if x["id"]][-20:],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
