param(
    [string]$Password = "Satya@677",
    [switch]$SkipPackages
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$StageRoot = Join-Path $ProjectRoot "publish"
$Python = Join-Path $ProjectRoot "venv\Scripts\python.exe"

Write-Host "==> Building publish folder: $StageRoot"

if ($SkipPackages) {
    if (-not (Test-Path $StageRoot)) {
        throw "publish folder missing. Run deploy without -SkipPackages first."
    }
    Write-Host "==> Skipping build; using existing publish folder."
} else {
    if (Test-Path $StageRoot) {
        Remove-Item $StageRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path $StageRoot | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $StageRoot "logs") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $StageRoot "data") | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $StageRoot "data\exports") | Out-Null

    $copyItems = @(
        "app",
        "sql",
        "runserver.py",
        "web.config",
        "requirements.txt",
        ".env"
    )

    foreach ($item in $copyItems) {
        $source = Join-Path $ProjectRoot $item
        if (-not (Test-Path $source)) {
            if ($item -eq ".env") {
                Copy-Item (Join-Path $ProjectRoot ".env.example") (Join-Path $StageRoot ".env")
                continue
            }
            Write-Warning "Skipping missing item: $item"
            continue
        }
        Copy-Item $source (Join-Path $StageRoot $item) -Recurse -Force
    }

    $envFile = Join-Path $StageRoot ".env"
    if (Test-Path $envFile) {
        $envText = Get-Content $envFile -Raw
        $prodOrigins = "http://satya567-001-site16.ctempurl.com,https://satya567-001-site16.ctempurl.com,https://onboarding.erphubspot.com,http://localhost,http://127.0.0.1"
        if ($envText -match "(?m)^CORS_ORIGINS=.*$") {
            $envText = [regex]::Replace($envText, "(?m)^CORS_ORIGINS=.*$", "CORS_ORIGINS=$prodOrigins")
        } else {
            $envText += "`nCORS_ORIGINS=$prodOrigins`n"
        }
        Set-Content -Path $envFile -Value $envText -NoNewline
    }

    Write-Host "==> Installing Python packages into publish\packages (this may take a few minutes)..."
    $packagesDir = Join-Path $StageRoot "packages"
    New-Item -ItemType Directory -Path $packagesDir | Out-Null
    & $Python -m pip install --upgrade pip | Out-Null
    & $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") -t $packagesDir --no-cache-dir
}

$publishUrl = "https://win9080.site4now.net:8172/msdeploy.axd?site=satya567-001-site16"
$siteName = "satya567-001-site16"
$userName = "satya567-001"
$msdeploy = "${env:ProgramFiles}\IIS\Microsoft Web Deploy V3\msdeploy.exe"

if (-not (Test-Path $msdeploy)) {
    $msdeploy = "${env:ProgramFiles(x86)}\IIS\Microsoft Web Deploy V3\msdeploy.exe"
}

Write-Host "==> Deploying via Web Deploy to $siteName ..."
& $msdeploy `
    -verb:sync `
    -source:contentPath="$StageRoot" `
    -dest:contentPath="$siteName",computerName="$publishUrl",userName="$userName",password="$Password",authType="Basic" `
    -allowUntrusted `
    -retryAttempts:3 `
    -retryInterval:5000

Write-Host "==> Deploy finished."
Write-Host "URL: http://satya567-001-site16.ctempurl.com/health"
