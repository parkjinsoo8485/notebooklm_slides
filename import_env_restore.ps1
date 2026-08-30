# import_env_restore.ps1
# 새 컴퓨터에서 1-클릭 환경 설치 및 세션 복원 스크립트

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "🚀 Antigravity MCP 환경 자동 설치 & 복원을 시작합니다" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. 필수 Python 패키지 및 Playwright 브라우저 설치
Write-Host "`n📦 [1/3] 필수 패키지 및 브라우저 엔진 자동 설치..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install "notebooklm-py[mcp]" playwright
python -m playwright install chromium

# 2. 백업 파일이 있으면 세션 자동 복원
$currentDir = $PSScriptRoot
$zipPath = Join-Path $currentDir "Antigravity_MCP_Backup.zip"

if (Test-Path $zipPath) {
    Write-Host "`n📂 [2/3] 백업 파일($zipPath)에서 세션 및 설정 복원 중..." -ForegroundColor Yellow
    $tempExtract = Join-Path $currentDir "Temp_Restore"
    if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
    
    Expand-Archive -Path $zipPath -DestinationPath $tempExtract -Force

    if (Test-Path "$tempExtract\.gemini") {
        New-Item -ItemType Directory -Path "$HOME\.gemini\config" -Force | Out-Null
        Copy-Item -Recurse "$tempExtract\.gemini\*" "$HOME\.gemini\" -Force
    }

    if (Test-Path "$tempExtract\.notebooklm") {
        New-Item -ItemType Directory -Path "$HOME\.notebooklm" -Force | Out-Null
        Copy-Item -Recurse "$tempExtract\.notebooklm\*" "$HOME\.notebooklm\" -Force
    }

    if (Test-Path "$tempExtract\.gdrive") {
        New-Item -ItemType Directory -Path "$HOME\.gdrive" -Force | Out-Null
        Copy-Item -Recurse "$tempExtract\.gdrive\*" "$HOME\.gdrive\" -Force
    }

    Remove-Item -Recurse -Force $tempExtract
    Write-Host "✅ 로그인 세션 및 MCP 설정 복원 완료!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ [2/3] 백업 ZIP 파일이 없어 기본 3개 프로필만 생성합니다." -ForegroundColor Yellow
    python -m notebooklm profile create account1
    python -m notebooklm profile create account2
    python -m notebooklm profile create account3
}

# 3. 연결 및 프로필 검증
Write-Host "`n🔍 [3/3] NotebookLM 프로필 연결 상태 검증..." -ForegroundColor Yellow
python -m notebooklm profile list

Write-Host "`n🎉 모든 환경설정이 완료되었습니다! Antigravity에서 즉시 사용하실 수 있습니다." -ForegroundColor Green
