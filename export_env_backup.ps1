# export_env_backup.ps1
# NotebookLM & Google Workspace MCP 환경 및 세션 백업 스크립트

$backupDir = "$HOME\Desktop\Antigravity_MCP_Backup_Temp"
if (Test-Path $backupDir) { Remove-Item -Recurse -Force $backupDir }

New-Item -ItemType Directory -Path "$backupDir\.gemini\config" -Force | Out-Null
New-Item -ItemType Directory -Path "$backupDir\.notebooklm" -Force | Out-Null
New-Item -ItemType Directory -Path "$backupDir\.gdrive" -Force | Out-Null

Write-Host "📦 세션 및 설정 백업 중..." -ForegroundColor Cyan

# 1. MCP 설정 복사
if (Test-Path "$HOME\.gemini\config\mcp_config.json") {
    Copy-Item "$HOME\.gemini\config\mcp_config.json" "$backupDir\.gemini\config\" -Force
}

# 2. NotebookLM 3개 계정 로그인 세션 복사
if (Test-Path "$HOME\.notebooklm") {
    Copy-Item -Recurse "$HOME\.notebooklm\*" "$backupDir\.notebooklm\" -Force
}

# 3. Google Drive 설정/토큰 복사
if (Test-Path "$HOME\.gdrive") {
    Copy-Item -Recurse "$HOME\.gdrive\*" "$backupDir\.gdrive\" -Force
}

# 4. 압축 생성
$zipPath = "$HOME\Desktop\Antigravity_MCP_Backup.zip"
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path "$backupDir\*" -DestinationPath $zipPath -Force
Remove-Item -Recurse -Force $backupDir

Write-Host "✅ 백업이 성공적으로 완료되었습니다!" -ForegroundColor Green
Write-Host "📁 백업 파일 위치: $zipPath" -ForegroundColor Yellow
Write-Host "💡 새 컴퓨터로 이동 시 이 ZIP 파일과 'import_env_restore.ps1'을 실행하시면 로그인 없이 즉시 복원됩니다." -ForegroundColor Cyan
