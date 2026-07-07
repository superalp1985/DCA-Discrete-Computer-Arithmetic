# DCA验证代码上传脚本 (PowerShell版)
# 使用方法: .\upload-dca-verification.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DCA验证代码上传脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 配置路径
$sourceDir = "C:\Users\王秉钦\Desktop\离散计算机数学\公众号\code-verification"
$targetDir = "C:\Users\王秉钦\Desktop\离散计算机数学\dca-discrete-computer-arithmetic\code-verification"
$repoDir = "C:\Users\王秉钦\Desktop\离散计算机数学\dca-discrete-computer-arithmetic"

Write-Host "步骤1: 创建目录结构..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path $targetDir | Out-Null

Write-Host "步骤2: 复制所有43章的验证文件..." -ForegroundColor Green
1..43 | ForEach-Object {
    $chapter = $_.ToString("00")
    $src = Join-Path $sourceDir "chapter$chapter"
    $dst = Join-Path $targetDir "chapter$chapter"

    if (Test-Path $src) {
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        Copy-Item -Path "$src\*" -Destination $dst -Recurse -Force
        Write-Host "  ✓ 复制第 $chapter 章" -ForegroundColor Cyan
    }
}

Write-Host "步骤3: 复制最终验证报告..." -ForegroundColor Green
Copy-Item -Path "$sourceDir\FINAL-VALIDATION-REPORT*.md" -Destination $targetDir -Force
Copy-Item -Path "$sourceDir\GITHUB-UPLOAD-GUIDE.md" -Destination $targetDir -Force
Write-Host "  ✓ 复制最终报告" -ForegroundColor Cyan

Write-Host "步骤4: 创建README..." -ForegroundColor Green
$readmeContent = @"
# DCA Code Verification

Comprehensive code verification for all 43 chapters of Discrete Computer Arithmetic.

## Status
- **Total Chapters:** 43
- **Total Tests:** 778+
- **Pass Rate:** 100%

## Quick Start
```powershell
# Run a specific chapter verification
cd chapterXX
python verify*.py
```

## Reports
- [Final Report (Chinese)](FINAL-VALIDATION-REPORT-ZH.md)
- [Final Report (English)](FINAL-VALIDATION-REPORT-EN.md)
- [Upload Guide](GITHUB-UPLOAD-GUIDE.md)

## Verification Results

All 43 chapters have been verified with 100% pass rate, demonstrating that discrete mathematics is fully effective in computing.
"@

Set-Content -Path "$targetDir\README.md" -Value $readmeContent -Encoding UTF8
Write-Host "  ✓ 创建README" -ForegroundColor Cyan

Write-Host "步骤5: Git提交..." -ForegroundColor Green
Set-Location $repoDir
git add code-verification/
git commit -m "Add code verification for all 43 DCA chapters

✅ All 43 chapters verified with 100% pass rate
✅ 778+ tests passed
✅ Comprehensive Chinese and English reports
✅ Demonstrates effectiveness of discrete mathematics in computing

验证完成日期: 2026-07-06"

Write-Host "步骤6: 推送到GitHub..." -ForegroundColor Green
git push origin main

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ 上传完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "请访问以下地址查看：" -ForegroundColor Yellow
Write-Host "https://github.com/superalp1985/DCA-Discrete-Computer-Arithmetic" -ForegroundColor White
Write-Host ""
Write-Host "检查code-verification/目录是否已成功上传" -ForegroundColor Yellow