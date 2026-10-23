param([string]$Tectonic = '')

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not $Tectonic) {
    $portableCompiler = Join-Path $projectRoot 'tmp\tools\tectonic\tectonic.exe'
    if (Test-Path -LiteralPath $portableCompiler) { $Tectonic = $portableCompiler }
    else {
        $compilerCommand = Get-Command tectonic -ErrorAction SilentlyContinue
        if ($compilerCommand) { $Tectonic = $compilerCommand.Source }
    }
}
if (-not $Tectonic -or -not (Test-Path -LiteralPath $Tectonic)) {
    throw 'Tectonic não encontrado. Consulte relatorio/README.md ou informe -Tectonic com o executável.'
}
Push-Location -LiteralPath $projectRoot
try {
    & $pythonExe scripts/gerar_relatorio.py
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao regenerar as figuras e tabelas.' }
    New-Item -ItemType Directory -Path 'tmp/latex-build','output/pdf' -Force | Out-Null
    & $Tectonic relatorio/main.tex --outdir tmp/latex-build --keep-logs
    if ($LASTEXITCODE -ne 0) { throw 'Compilação LaTeX reprovada; o PDF entregue foi preservado.' }
    Copy-Item -LiteralPath 'tmp/latex-build/main.pdf' -Destination 'output/pdf/relatorio_ciencias_natureza.pdf'
    Write-Output 'PDF gerado em output/pdf/relatorio_ciencias_natureza.pdf'
}
finally { Pop-Location }
