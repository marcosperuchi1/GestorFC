from __future__ import annotations
import json, os, sys
from pathlib import Path


def find_browser() -> str | None:
    candidates = []
    for env_name in ('PROGRAMFILES', 'PROGRAMFILES(X86)', 'LOCALAPPDATA'):
        base = os.environ.get(env_name)
        if not base:
            continue
        b = Path(base)
        candidates.extend([
            b / 'Google' / 'Chrome' / 'Application' / 'chrome.exe',
            b / 'Microsoft' / 'Edge' / 'Application' / 'msedge.exe',
        ])
    # Linux fallback makes this test runnable locally as well.
    candidates.extend([Path('/usr/bin/chromium'), Path('/usr/bin/google-chrome'), Path('/usr/bin/microsoft-edge')])
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit('usage: test_runtime_boot.py <project-dir>')
    root = Path(sys.argv[1]).resolve()
    html_path = root / 'src' / 'index.html'
    html = html_path.read_text(encoding='utf-8')

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError('Playwright nao instalado para smoke test do boot') from exc

    browser_path = find_browser()
    if not browser_path:
        raise RuntimeError('Chrome/Edge/Chromium nao encontrado para smoke test do boot')

    page_errors: list[str] = []
    console_errors: list[str] = []
    body_text = ''
    auth_count = 0
    login_count = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            executable_path=browser_path,
            headless=True,
            args=['--disable-gpu', '--disable-dev-shm-usage', '--no-sandbox'],
        )
        page = browser.new_page(viewport={'width': 1600, 'height': 900})
        page.on('pageerror', lambda err: page_errors.append(str(err)))
        page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)
        # Executa exatamente o HTML final sem depender de servidor ou bridge Tauri.
        # O login precisa existir mesmo sem a base/native bridge.
        page.set_content(html, wait_until='domcontentloaded', timeout=90000)
        page.wait_for_timeout(3000)
        auth_count = page.locator('.v548-auth').count()
        login_count = page.locator('#v548-login-form').count()
        body_text = page.locator('body').inner_text(timeout=10000)
        if auth_count < 1 or login_count < 1:
            try:
                page.screenshot(path=str(root / 'runtime-boot-failure.png'), full_page=True)
            except Exception:
                pass
        browser.close()

    fatal_messages = [
        'Nao foi possivel montar a tela inicial',
        'Não foi possível montar a tela inicial',
    ]
    fatal_visible = any(msg in body_text for msg in fatal_messages)
    roster_failures = [
        msg for msg in page_errors + console_errors
        if 'base local de jogadores ainda está sendo preparada' in msg.lower()
        or 'base local de jogadores ainda esta sendo preparada' in msg.lower()
        or 'base instalada no boot' in msg.lower()
    ]

    result = {
        'ok': bool(auth_count and login_count and not fatal_visible and not roster_failures),
        'browser': browser_path,
        'authCount': auth_count,
        'loginFormCount': login_count,
        'fatalVisible': fatal_visible,
        'rosterFailures': roster_failures[:20],
        # Erros antigos nao relacionados ficam apenas como diagnostico; este teste
        # e focado no boot que o usuario realmente enxerga.
        'pageErrorCount': len(page_errors),
        'consoleErrorCount': len(console_errors),
    }
    (root / 'runtime-boot-tests.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    if not result['ok']:
        raise RuntimeError('Smoke test real do boot falhou: ' + json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
