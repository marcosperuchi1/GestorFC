from __future__ import annotations
import re
from pathlib import Path


path=Path('.github/workflows/build-desktop-rc1-clean.yml')
text=path.read_text(encoding='utf-8')
text=text.replace('permissions:\n  contents: read','permissions:\n  contents: write',1)

pattern_diag=re.compile(
    r"      - name: Publicar diagnostico antecipado\n"
    r"        uses: actions/upload-artifact@v4\n"
    r"        with:\n"
    r"(?:          .*\n)+?"
    r"(?=      - name: Testar round-trip do save compacto)",
    re.M,
)
diag='''      - name: Preservar diagnostico no pacote final
        shell: pwsh
        run: |
          Write-Host 'Diagnostico e testes serao incluidos no pacote final; upload intermediario desativado para nao consumir Actions Storage.'

'''
text,n_diag=pattern_diag.subn(diag,text,count=1)
if n_diag!=1:
    raise RuntimeError(f'bloco de diagnostico esperado 1, encontrado {n_diag}')

pattern_final=re.compile(
    r"      - name: Publicar artifacts\n"
    r"        uses: actions/upload-artifact@v4\n"
    r"        with:\n"
    r"(?:          .*\n?)+?\Z",
    re.M,
)
final='''      - name: Publicar ultimo build em Release
        shell: pwsh
        working-directory: ${{ env.FUTBR_PROJECT }}
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          $ErrorActionPreference = 'Stop'
          $tag = 'futbr-desktop-latest'
          $title = 'FutBR Manager - Ultimo build de teste'
          gh release view $tag --repo $env:GITHUB_REPOSITORY *> $null
          if ($LASTEXITCODE -ne 0) {
            gh release create $tag --repo $env:GITHUB_REPOSITORY --title $title --notes 'Pacote mais recente gerado pelo pipeline de testes do FutBR Manager.' --target $env:GITHUB_SHA
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o release.' }
          } else {
            gh release edit $tag --repo $env:GITHUB_REPOSITORY --title $title --notes 'Pacote mais recente gerado pelo pipeline de testes do FutBR Manager.' --target $env:GITHUB_SHA
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao atualizar o release.' }
          }
          Get-ChildItem artifacts -File | ForEach-Object {
            Write-Host "Publicando $($_.Name)"
            gh release upload $tag $_.FullName --clobber --repo $env:GITHUB_REPOSITORY
            if ($LASTEXITCODE -ne 0) { throw "Falha ao publicar $($_.Name)" }
          }
'''
text,n_final=pattern_final.subn(final,text,count=1)
if n_final!=1:
    raise RuntimeError(f'bloco final esperado 1, encontrado {n_final}')

if 'actions/upload-artifact@v4' in text:
    raise RuntimeError('upload-artifact ainda permanece no workflow')
if 'Publicar ultimo build em Release' not in text:
    raise RuntimeError('publicacao por release nao instalada')
path.write_text(text,encoding='utf-8')
print('workflow configurado para release unico sem Actions Storage')
