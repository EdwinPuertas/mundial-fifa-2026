# ============================================================
# Script de despliegue: GitHub + Vercel
# Modelo Predictivo Mundial FIFA 2026
# ============================================================
# EJECUTAR desde la carpeta mundial2026-deploy en PowerShell:
#   cd ruta\a\mundial2026-deploy
#   .\deploy.ps1
# ============================================================

$REPO_NAME = "mundial-fifa-2026"
$GITHUB_USER = "EdwinPuertas"
$BRANCH = "main"

Write-Host "`n=== PASO 1: Inicializar repositorio Git ===" -ForegroundColor Cyan
git init
git config user.name $GITHUB_USER
git add .
git commit -m "feat: Modelo Predictivo Mundial FIFA 2026 - Dashboard v2"

Write-Host "`n=== PASO 2: Crear repo en GitHub ===" -ForegroundColor Cyan
Write-Host "Abre en el navegador: https://github.com/new" -ForegroundColor Yellow
Write-Host "  - Nombre del repo: $REPO_NAME" -ForegroundColor Yellow
Write-Host "  - Visibilidad: Public" -ForegroundColor Yellow
Write-Host "  - NO marques 'Initialize this repository'" -ForegroundColor Yellow
Write-Host "`nPresiona ENTER cuando hayas creado el repo en GitHub..." -ForegroundColor Green
Read-Host

Write-Host "`n=== PASO 3: Conectar y subir a GitHub ===" -ForegroundColor Cyan
git remote add origin "https://github.com/$GITHUB_USER/$REPO_NAME.git"
git branch -M $BRANCH
git push -u origin $BRANCH

Write-Host "`n=== PASO 4: Desplegar en Vercel ===" -ForegroundColor Cyan
Write-Host "Abre: https://vercel.com/new" -ForegroundColor Yellow
Write-Host "  1. Selecciona 'Import Git Repository'" -ForegroundColor Yellow
Write-Host "  2. Elige el repo: $GITHUB_USER/$REPO_NAME" -ForegroundColor Yellow
Write-Host "  3. Framework Preset: Other" -ForegroundColor Yellow
Write-Host "  4. Haz clic en 'Deploy'" -ForegroundColor Yellow
Write-Host "`n✅ En 30 segundos tu dashboard estará en:" -ForegroundColor Green
Write-Host "   https://$REPO_NAME.vercel.app" -ForegroundColor Magenta
