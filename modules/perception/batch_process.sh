#!/bin/bash
# 批量处理本地视频文件 (优化版：从local SSD读取)

VIDEO_DIR="../../data/videos"
OUTPUT_CSV="../../data/detections/batch_all_detections.csv"
PYTHON_BIN="/Users/boyangli/Repo/sentinel-map/.venv/bin/python"
SCRIPT="detect_and_extract.py"
LOG_FILE="batch_local_$(date +%Y%m%d_%H%M%S).log"

# 检查视频目录
if [ ! -d "$VIDEO_DIR" ]; then
    echo "❌ 错误: 找不到视频目录 $VIDEO_DIR"
    echo "请确保外部存储设备已连接"
    exit 1
fi

# 获取视频列表
VIDEO_FILES=("$VIDEO_DIR"/*.MP4)
TOTAL=${#VIDEO_FILES[@]}

if [ $TOTAL -eq 0 ]; then
    echo "❌ 错误: 没有找到视频文件"
    exit 1
fi

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         批量处理本地视频 - Local SSD (Optimized)            ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📹 总视频数: $TOTAL"
echo "📂 输出CSV: $OUTPUT_CSV"
echo "📝 日志文件: $LOG_FILE"
echo "⚙️  设备: MPS"
echo ""
echo "▶️  开始批量处理..."
echo ""

# Delete output CSV if exists (fresh start)
if [ -f "$OUTPUT_CSV" ]; then
    rm "$OUTPUT_CSV"
    echo "🗑️  Removed existing CSV for fresh start"
fi

# 计数器
SUCCESS=0
FAILED=0
START_TIME=$(date +%s)

# 处理每个视频
for i in "${!VIDEO_FILES[@]}"; do
    VIDEO="${VIDEO_FILES[$i]}"
    CURRENT=$((i + 1))
    BASENAME=$(basename "$VIDEO")
    
    echo "════════════════════════════════════════════════════════════════"
    echo "[$CURRENT/$TOTAL] 处理: $BASENAME"
    echo "════════════════════════════════════════════════════════════════"
    
    # 运行检测
    $PYTHON_BIN $SCRIPT \
        --video "$VIDEO" \
        --output-csv "$OUTPUT_CSV" \
        --device mps \
        --conf 0.25 \
        --sample-fps 1 \
        2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        SUCCESS=$((SUCCESS + 1))
        echo "✅ 成功 ($SUCCESS/$TOTAL)"
    else
        FAILED=$((FAILED + 1))
        echo "❌ 失败 ($FAILED/$TOTAL)"
    fi
    
    echo ""
done

# 计算耗时
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
MINUTES=$((ELAPSED / 60))
SECONDS=$((ELAPSED % 60))

# 最终报告
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                      批处理完成                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo "✅ 成功: $SUCCESS/$TOTAL"
echo "❌ 失败: $FAILED/$TOTAL"
echo "⏱️  耗时: ${MINUTES}分${SECONDS}秒"
echo "📊 输出: $OUTPUT_CSV"
echo "📝 日志: $LOG_FILE"
echo ""
echo "下一步:"
echo "  1. 检查 $OUTPUT_CSV"
echo "  2. 运行: cd ../ingestion && ./bin/producer -csv $OUTPUT_CSV -batch"
echo "  3. 运行: cd ../../analytics && dbt run"
