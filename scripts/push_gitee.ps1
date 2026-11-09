# Push longshot-split to Gitee.
# Usage:  powershell -ExecutionPolicy Bypass -File scripts/push_gitee.ps1 [-GiteeUrl <ssh-or-https-remote>]
# Default remote: SSH git@gitee.com:BingKaiWei/longshot-split.git
#   (this machine's ~/.ssh/id_ed25519 is already registered on Gitee, so SSH needs no password;
#    note the Gitee login name is "BingKaiWei" — different casing from GitHub's "BingKaiWEI")
# Prerequisite: create the empty repo once at https://gitee.com/projects/new (name: longshot-split).
# If you prefer HTTPS, pass -GiteeUrl https://gitee.com/BingKaiWei/longshot-split.git
#   (you will be prompted for username + private token as the password).

param(
    [string]$GiteeUrl = "git@gitee.com:BingKaiWei/longshot-split.git"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

git remote remove gitee 2>$null
git remote add gitee $GiteeUrl
git push gitee master
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[!] push failed: repo not created yet, or remote/credentials problem." -ForegroundColor Yellow
    Write-Host "    1. Create the repo at https://gitee.com/projects/new (name: longshot-split, do NOT init README)"
    Write-Host "    2. Re-run this script. Current remote: $GiteeUrl"
    exit 1
}
Write-Host "[ok] pushed to gitee (master) -> $GiteeUrl" -ForegroundColor Green
