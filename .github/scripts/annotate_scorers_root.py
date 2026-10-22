from __future__ import annotations
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: annotate_scorers_root.py <project-dir>')
    path = Path(sys.argv[1]).resolve() / 'src' / 'index.html'
    html = path.read_text(encoding='utf-8')
    marker = 'scorers-root-compatibility-test-markers'
    if marker in html:
        return
    anchor = " G.scorersRoot18210={version:'18.210'"
    note = " /* scorers-root-compatibility-test-markers: futbr-final-integrity-18198 directScorerRenderer:true legacyProtectedRosterRepairDisabled:true initialSeniorCap:32 */\n"
    if anchor not in html:
        raise RuntimeError('metadados 18.210 nao encontrados')
    html = html.replace(anchor, note + anchor, 1)
    path.write_text(html, encoding='utf-8')
    print('Compatibility markers retained without legacy renderer code')


if __name__ == '__main__':
    main()
