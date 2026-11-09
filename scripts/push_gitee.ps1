# Push longshot-split to Gitee (https://gitee.com/BingKaiWEI/longshot-split).
# Usage:  powershell -ExecutionPolicy Bypass -File scripts/push_gitee.ps1
# Requires: a repo named longshot-split under https://gitee.com/BingKaiWEI
#           (create it once in the Gitee web UI), then your Gitee credentials.

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

git remote remove gitee 2>$null
git remote add gitee https://gitee.com/BingKaiWEI/longshot-split.git
git push gitee master
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[!] push failed: Gitee credentials missing or repo not created." -ForegroundColor Yellow
    Write-Host "    1. Create the repo at https://gitee.com/projects/new (name: longshot-split)"
    Write-Host "    2. Re-run this script and enter your Gitee username/password (or token) when prompted."
    exit 1
}
Write-Host "[ok] pushed to gitee (master)" -ForegroundColor Green
