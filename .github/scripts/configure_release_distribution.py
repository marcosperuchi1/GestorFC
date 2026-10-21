from __future__ import annotations
from pathlib import Path


path=Path('.github/workflows/build-desktop-rc1-clean.yml')
text=path.read_text(encoding='utf-8')

old_permissions='permissions:\n  contents: read'
new_permissions='permissions:\n  contents: write'
if old_permissions in text:
    text=text.replace(old_permissions,new_permissions,1)
elif new_permissions not in text:
    raise RuntimeError('bloco de permissoes do workflow nao encontrado')

start=text.find('      - name: Publicar diagnostico antecipado\n')
end=text.find('      - name: Testar round-trip do save compacto\n',start)
if start<0 or end<0:
    raise RuntimeError('bloco de diagnostico nao encontrado')
diag='''      - name: Preservar diagnostico no pacote final
        shell: pwsh
        run: |
          Write-Host 'Diagnostico e testes serao incluidos no pacote final; upload intermediario desativado para nao consumir Actions Storage.'

'''
text=text[:start]+diag+text[end:]

start=text.find('      - name: Publicar artifacts\n')
if start<0:
    raise RuntimeError('bloco final de artifacts nao encontrado')
final='''      - name: Publicar ultimo build em Release
        shell: pwsh
        working-directory: ${{ env.FUTBR_PROJECT }}
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          $ErrorActionPreference = 'Stop'
          $PSNativeCommandUseErrorActionPreference = $false
          $tag = 'futbr-desktop-latest'
          $title = 'FutBR Manager - Build #${{ github.run_number }}'
          $notes = 'Pacote mais recente gerado pelo pipeline de testes do FutBR Manager. Substitui automaticamente o build anterior.'

          gh release view $tag --repo $env:GITHUB_REPOSITORY *> $null
          if ($LASTEXITCODE -eq 0) {
            gh release delete $tag --yes --cleanup-tag --repo $env:GITHUB_REPOSITORY
            if ($LASTEXITCODE -ne 0) { throw 'Falha ao remover o release anterior.' }
          }

          gh release create $tag --repo $env:GITHUB_REPOSITORY --title $title --notes $notes --target $env:GITHUB_SHA --latest
          if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o release mais recente.' }

          Get-ChildItem artifacts -File | ForEach-Object {
            Write-Host "Publicando $($_.Name)"
            gh release upload $tag $_.FullName --clobber --repo $env:GITHUB_REPOSITORY
            if ($LASTEXITCODE -ne 0) { throw "Falha ao publicar $($_.Name)" }
          }
'''
text=text[:start]+final

if 'actions/upload-artifact@v4' in text:
    raise RuntimeError('upload-artifact ainda permanece no workflow')
if 'Publicar ultimo build em Release' not in text:
    raise RuntimeError('publicacao por release nao instalada')
path.write_text(text,encoding='utf-8')
print('workflow configurado para release unico sem Actions Storage')
