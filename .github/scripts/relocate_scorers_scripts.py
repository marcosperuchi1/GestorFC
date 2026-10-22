from __future__ import annotations
import re
import sys
from pathlib import Path


SCRIPT_IDS = (
    "futbr-scorers-root-18210",
    "futbr-scorers-render-root-18211",
)


def fail(message: str) -> None:
    raise RuntimeError(message)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: relocate_scorers_scripts.py <project-dir>")

    project = Path(sys.argv[1]).resolve()
    index_path = project / "src" / "index.html"
    html = index_path.read_text(encoding="utf-8")

    scripts: list[str] = []
    for script_id in SCRIPT_IDS:
        pattern = re.compile(
            r"\s*<script\b(?=[^>]*\bid=[\"']"
            + re.escape(script_id)
            + r"[\"'])[^>]*>[\s\S]*?</script>\s*",
            re.I,
        )
        matches = list(pattern.finditer(html))
        if len(matches) != 1:
            fail(f"{script_id}: esperado 1 script, encontrado {len(matches)}")
        scripts.append(matches[0].group(0).strip())
        html = pattern.sub("\n", html, count=1)

    body_matches = list(re.finditer(r"</body\s*>", html, re.I))
    if not body_matches:
        fail("fechamento </body> ausente")
    body_pos = body_matches[-1].start()
    injection = "\n\n" + "\n\n".join(scripts) + "\n"
    html = html[:body_pos] + injection + html[body_pos:]

    body_end = html.lower().rfind("</body")
    html_end = html.lower().rfind("</html")
    positions = {script_id: html.find(f'id="{script_id}"') for script_id in SCRIPT_IDS}
    if any(position < 0 or position > body_end for position in positions.values()):
        fail(f"scripts fora do body: {positions}, body={body_end}")
    if not positions[SCRIPT_IDS[0]] < positions[SCRIPT_IDS[1]] < body_end:
        fail("ordem dos scripts de Artilheiros incorreta")
    if html_end >= 0 and any(position > html_end for position in positions.values()):
        fail("script de Artilheiros permanece depois do </html>")

    index_path.write_text(html, encoding="utf-8")
    print({
        "ok": True,
        "scripts": positions,
        "bodyEnd": body_end,
        "htmlEnd": html_end,
        "insideBody": True,
    })


if __name__ == "__main__":
    main()
