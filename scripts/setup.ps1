$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$ServerDir = Join-Path $RootDir "server"
$RequirementsFile = Join-Path $RootDir "requirements.txt"
$EnvExampleFile = Join-Path $RootDir ".env.example"
$EnvFile = Join-Path $RootDir ".env"

Write-Host "==> Prüfe benötigte Tools"
$tools = @("node", "npm", "python3", "pip")
$missing = @()
foreach ($tool in $tools) {
  if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
    $missing += $tool
  }
}
if ($missing.Count -gt 0) {
  throw "Fehlende Tools: $($missing -join ', ')"
}
Write-Host "✅ Alle benötigten Tools sind vorhanden."

Write-Host "==> Installiere JS-Abhängigkeiten"
if (-not (Test-Path (Join-Path $ServerDir "package-lock.json"))) {
  Push-Location $ServerDir
  npm install --package-lock-only
  Pop-Location
}
Push-Location $ServerDir
npm ci
Pop-Location
Write-Host "✅ JavaScript-Abhängigkeiten installiert."

Write-Host "==> Installiere Python-Abhängigkeiten"
if (Test-Path $RequirementsFile) {
  $lines = Get-Content $RequirementsFile | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith("#") }
  if ($lines.Count -gt 0) {
    pip install -r $RequirementsFile
    Write-Host "✅ Python-Abhängigkeiten installiert."
  }
  else {
    Write-Host "ℹ️ requirements.txt ist leer (oder enthält nur Kommentare)."
  }
}
else {
  Write-Host "⚠️ requirements.txt nicht gefunden."
}

Write-Host "==> Erzeuge .env falls nötig"
if (-not (Test-Path $EnvExampleFile)) {
  throw ".env.example fehlt im Repo-Root."
}
if (-not (Test-Path $EnvFile)) {
  Copy-Item $EnvExampleFile $EnvFile
  Write-Host "✅ .env wurde aus .env.example erstellt."
}
else {
  Write-Host "ℹ️ .env existiert bereits."
}

Write-Host "🎉 Setup abgeschlossen."
