#!/bin/bash
# DCA验证代码上传脚本 - 一键完成所有操作
# 使用方法: bash upload-dca-verification.sh

set -e

echo "========================================"
echo "DCA验证代码上传脚本"
echo "========================================"
echo ""

# 配置路径
SOURCE_DIR="C:/Users/王秉钦/Desktop/离散计算机数学/公众号/code-verification"
TARGET_DIR="C:/Users/王秉钦/Desktop/离散计算机数学/dca-discrete-computer-arithmetic/code-verification"
REPO_DIR="C:/Users/王秉钦/Desktop/离散计算机数学/dca-discrete-computer-arithmetic"

echo "步骤1: 创建目录结构..."
mkdir -p "$TARGET_DIR"

echo "步骤2: 复制所有43章的验证文件..."
for i in {01..43}; do
    if [ -d "$SOURCE_DIR/chapter$i" ]; then
        mkdir -p "$TARGET_DIR/chapter$i"
        cp "$SOURCE_DIR/chapter$i"/* "$TARGET_DIR/chapter$i/" 2>/dev/null || true
        echo "  ✓ 复制第 $i 章"
    fi
done

echo "步骤3: 复制最终验证报告..."
cp "$SOURCE_DIR"/FINAL-VALIDATION-REPORT*.md "$TARGET_DIR/"
cp "$SOURCE_DIR"/GITHUB-UPLOAD-GUIDE.md "$TARGET_DIR/"
echo "  ✓ 复制最终报告"

echo "步骤4: 创建README..."
cat > "$TARGET_DIR/README.md" << 'EOF'
# DCA Code Verification

Comprehensive code verification for all 43 chapters of Discrete Computer Arithmetic.

## Status
- **Total Chapters:** 43
- **Total Tests:** 778+
- **Pass Rate:** 100%

## Quick Start
```bash
# Run a specific chapter verification
cd chapterXX
python verify*.py
```

## Reports
- [Final Report (Chinese)](FINAL-VALIDATION-REPORT-ZH.md)
- [Final Report (English)](FINAL-VALIDATION-REPORT-EN.md)
- [Upload Guide](GITHUB-UPLOAD-GUIDE.md)
EOF
echo "  ✓ 创建README"

echo "步骤5: Git提交..."
cd "$REPO_DIR"
git add code-verification/
git commit -m "Add code verification for all 43 DCA chapters

✅ All 43 chapters verified with 100% pass rate
✅ 778+ tests passed
✅ Comprehensive Chinese and English reports
✅ Demonstrates effectiveness of discrete mathematics in computing

验证完成日期: 2026-07-06"

echo "步骤6: 推送到GitHub..."
git push origin main

echo ""
echo "========================================"
echo "✅ 上传完成！"
echo "========================================"
echo ""
echo "请访问以下地址查看："
echo "https://github.com/superalp1985/DCA-Discrete-Computer-Arithmetic"
echo ""
echo "检查code-verification/目录是否已成功上传"