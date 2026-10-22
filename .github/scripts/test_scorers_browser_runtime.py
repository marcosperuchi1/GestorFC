from __future__ import annotations
import json
import os
import shutil
import sys
from pathlib import Path


def find_browser() -> str | None:
    candidates: list[Path] = []
    for exe in ('chrome', 'chrome.exe', 'msedge', 'msedge.exe', 'chromium', 'chromium.exe'):
        found = shutil.which(exe)
        if found:
            candidates.append(Path(found))
    for env_name in ('PROGRAMFILES', 'ProgramFiles', 'PROGRAMFILES(X86)', 'ProgramFiles(x86)', 'LOCALAPPDATA', 'LocalAppData'):
        base = os.environ.get(env_name)
        if not base:
            continue
        root = Path(base)
        candidates.extend([
            root / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
            root / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe',
        ])
    candidates.extend([
        Path('/usr/bin/chromium'),
        Path('/usr/bin/google-chrome'),
        Path('/usr/bin/microsoft-edge'),
    ])
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_scorers_browser_runtime.py <project-dir>')

    root = Path(sys.argv[1]).resolve()
    html_path = root / 'src' / 'index.html'
    html = html_path.read_text(encoding='utf-8')

    root_id = 'id="futbr-scorers-root-18210"'
    render_id = 'id="futbr-scorers-render-root-18211"'
    root_pos = html.find(root_id)
    render_pos = html.find(render_id)
    body_end = html.lower().rfind('</body')
    html_end = html.lower().rfind('</html')
    if min(root_pos, render_pos, body_end) < 0:
        raise RuntimeError('Scripts ou fechamento do body ausentes no HTML final')
    if not root_pos < render_pos < body_end:
        raise RuntimeError(f'Ordem/posicao invalida dos scripts: root={root_pos}, render={render_pos}, body={body_end}')
    if html_end >= 0 and (root_pos > html_end or render_pos > html_end):
        raise RuntimeError('Scripts de Artilheiros permanecem fora do documento HTML')

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError('Playwright nao instalado para teste real de Artilheiros') from exc

    browser_path = find_browser()
    if not browser_path:
        raise RuntimeError('Chrome/Edge/Chromium nao encontrado para teste real de Artilheiros')

    page_errors: list[str] = []
    console_errors: list[str] = []
    runtime: dict = {}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=browser_path,
            headless=True,
            args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox'],
        )
        page = browser.new_page(viewport={'width': 1600, 'height': 900})
        page.on('pageerror', lambda error: page_errors.append(str(error)))
        page.on('console', lambda message: console_errors.append(message.text) if message.type == 'error' else None)
        page.set_content(html, wait_until='domcontentloaded', timeout=90000)
        page.wait_for_timeout(3000)
        runtime = page.evaluate(
            """() => {
              const g = window.GestorFC || {};
              let fallbackHtml = '';
              let factoryHtml = '';
              let fallbackError = '';
              let factoryError = '';
              try {
                fallbackHtml = typeof window.v18211FallbackHTML === 'function'
                  ? String(window.v18211FallbackHTML(new Error('runtime probe')) || '')
                  : '';
              } catch (error) {
                fallbackError = String(error && (error.stack || error.message) || error);
              }
              try {
                factoryHtml = typeof window.v18211RankingsHTML === 'function'
                  ? String(window.v18211RankingsHTML() || '')
                  : '';
              } catch (error) {
                factoryError = String(error && (error.stack || error.message) || error);
              }
              return {
                rootMarker: g.scorersRoot18210?.version || '',
                renderMarker: g.scorersRender18211?.version || '',
                fallbackType: typeof window.v18211FallbackHTML,
                factoryType: typeof window.v18211RankingsHTML,
                fallbackMounted: fallbackHtml.includes('data-v18211-safe-root="1"'),
                factoryMounted: factoryHtml.includes('data-v18211-safe-root="1"') || factoryHtml.includes('data-v18210-scorers-root="1"'),
                fallbackLength: fallbackHtml.length,
                factoryLength: factoryHtml.length,
                fallbackError,
                factoryError,
              };
            }"""
        )
        if not runtime.get('fallbackMounted') or not runtime.get('factoryMounted'):
            try:
                page.screenshot(path=str(root / 'scorers-browser-runtime-failure.png'), full_page=True)
            except Exception:
                pass
        browser.close()

    result = {
        'ok': bool(
            runtime.get('rootMarker') == '18.210'
            and runtime.get('renderMarker') == '18.211'
            and runtime.get('fallbackType') == 'function'
            and runtime.get('factoryType') == 'function'
            and runtime.get('fallbackMounted')
            and runtime.get('factoryMounted')
            and not runtime.get('fallbackError')
            and not runtime.get('factoryError')
        ),
        'browser': browser_path,
        'insideBody': True,
        'rootPosition': root_pos,
        'renderPosition': render_pos,
        'bodyEnd': body_end,
        'htmlEnd': html_end,
        **runtime,
        'pageErrorCount': len(page_errors),
        'consoleErrorCount': len(console_errors),
    }
    (root / 'scorers-browser-runtime-tests.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(json.dumps(result, ensure_ascii=False))
    if not result['ok']:
        raise RuntimeError('Teste real de Artilheiros falhou: ' + json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
