param(
    [string]$ApiUrl,
    [string]$NodeVersion = "20.19.0"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $repoRoot "frontend"
$toolsDir = Join-Path $HOME "tools"
$nodeZipName = "node-v$NodeVersion-win-x64.zip"
$nodeFolderName = "node-v$NodeVersion-win-x64"
$nodeZipPath = Join-Path $toolsDir $nodeZipName
$nodeExtractPath = Join-Path $toolsDir $nodeFolderName
$nodeStablePath = Join-Path $toolsDir "node"
$nodeDownloadUrl = "https://nodejs.org/dist/v$NodeVersion/$nodeZipName"
$envLocalPath = Join-Path $frontendDir ".env.local"
$defaultApiUrl = "https://73edpnyeqs6gl3eh4gyfnwoji40ldhgo.lambda-url.ap-southeast-2.on.aws"

if (-not (Test-Path $frontendDir)) {
    throw "Could not find frontend directory at $frontendDir"
}

if ([string]::IsNullOrWhiteSpace($ApiUrl)) {
    $prompt = "Enter API base URL (Enter for default: $defaultApiUrl)"
    $ApiUrl = Read-Host $prompt
}

if ([string]::IsNullOrWhiteSpace($ApiUrl)) {
    $ApiUrl = $defaultApiUrl
    Write-Host "Using default API URL (same as app fallback)." -ForegroundColor DarkGray
}

if (-not $ApiUrl.StartsWith("http://") -and -not $ApiUrl.StartsWith("https://")) {
    throw "API URL must start with http:// or https://"
}

New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null

if (-not (Test-Path $nodeExtractPath)) {
    Write-Host "Downloading portable Node.js v$NodeVersion..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri $nodeDownloadUrl -OutFile $nodeZipPath
    Write-Host "Extracting Node.js..." -ForegroundColor Cyan
    Expand-Archive -Path $nodeZipPath -DestinationPath $toolsDir -Force
}

if (Test-Path $nodeStablePath) {
    Remove-Item -Recurse -Force $nodeStablePath
}

Copy-Item -Recurse -Force $nodeExtractPath $nodeStablePath

$env:Path = "$nodeStablePath;$nodeStablePath\node_modules\npm\bin;$env:Path"

Write-Host "Writing frontend/.env.local..." -ForegroundColor Cyan
"REACT_APP_API_URL=$ApiUrl" | Set-Content -Path $envLocalPath -Encoding ascii

Push-Location $frontendDir
try {
    Write-Host "Using Node:" -ForegroundColor Cyan
    & "$nodeStablePath\node.exe" -v
    Write-Host "Using npm:" -ForegroundColor Cyan
    & "$nodeStablePath\npm.cmd" -v

    Write-Host "Installing frontend dependencies..." -ForegroundColor Cyan
    & "$nodeStablePath\npm.cmd" install

    Write-Host "Starting local dev server..." -ForegroundColor Green
    Write-Host "Open http://localhost:3000 once startup completes." -ForegroundColor Green
    & "$nodeStablePath\npm.cmd" start
}
finally {
    Pop-Location
}
