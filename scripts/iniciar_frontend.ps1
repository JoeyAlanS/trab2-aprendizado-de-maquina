param([ValidateRange(1024, 65535)][int]$Porta = 8501)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw 'Ambiente não encontrado. Siga a instalação no README.'
}
Push-Location -LiteralPath $projectRoot
try {
    & $pythonExe -m streamlit run app/app.py --server.address 127.0.0.1 --server.port $Porta
    if ($LASTEXITCODE -ne 0) { throw 'Não foi possível iniciar o frontend.' }
}
finally {
    Pop-Location
}
