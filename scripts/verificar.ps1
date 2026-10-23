$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Ambiente não encontrado. Siga a instalação no README.'
}

Push-Location -LiteralPath $projectRoot
try {
    & $pythonExe -m ruff check .
    if ($LASTEXITCODE -ne 0) { throw 'Lint reprovado.' }
    & $pythonExe -m ruff format --check .
    if ($LASTEXITCODE -ne 0) { throw 'Formatação reprovada.' }
    & $pythonExe -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw 'Testes reprovados.' }
    & $pythonExe -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependências inconsistentes.' }
}
finally {
    Pop-Location
}
