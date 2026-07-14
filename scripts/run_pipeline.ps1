<#
.SYNOPSIS
    Executa o pipeline de alfabetização de ponta a ponta no Windows/PowerShell.
.DESCRIPTION
    Valida o ambiente virtual e o .env, roda testes opcionais, executa o
    pipeline (validate-config, batch, silver, gold) e propaga o código de erro.
.PARAMETER SkipTests
    Não executa a suíte de testes antes do pipeline.
.EXAMPLE
    ./scripts/run_pipeline.ps1
    ./scripts/run_pipeline.ps1 -SkipTests
#>

[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "== Pipeline de Alfabetizacao ==" -ForegroundColor Cyan

# 1. Valida o ambiente virtual.
if (-not $env:VIRTUAL_ENV) {
    $venv = Join-Path $ProjectRoot ".venv\Scripts\Activate.ps1"
    if (Test-Path $venv) {
        Write-Host "Ativando .venv..." -ForegroundColor Yellow
        & $venv
    } else {
        Write-Warning "Ambiente virtual (.venv) nao encontrado. Prosseguindo com o Python do sistema."
    }
}

# 2. Valida o .env.
if (-not (Test-Path (Join-Path $ProjectRoot ".env"))) {
    Write-Warning ".env nao encontrado. Copie o .env.example e ajuste as variaveis."
}

# 3. Testes opcionais.
if (-not $SkipTests) {
    Write-Host "Executando testes..." -ForegroundColor Yellow
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) { Write-Error "Testes falharam."; exit $LASTEXITCODE }
}

# 4. Pipeline.
$steps = @("validate-config", "batch", "silver", "gold")
foreach ($step in $steps) {
    Write-Host ">> $step" -ForegroundColor Green
    python -m src.cli $step
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Etapa '$step' falhou (codigo $LASTEXITCODE)."
        exit $LASTEXITCODE
    }
}

# 5. Resumo.
Write-Host "== Pipeline concluido com sucesso ==" -ForegroundColor Cyan
python scripts/generate_monitoring_report.py
exit 0
