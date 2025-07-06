#!/bin/bash

# SPECjvm2008 自动化测试脚本
# 使用方法: 
#   ./run_workload.sh                    # 使用系统默认JDK
#   ./run_workload.sh bisheng-jdk1.8.0_452  # 使用指定JDK
#   ./run_workload.sh dragonwell-8.25.24     # 使用指定JDK

# 解析命令行参数
JDK_NAME=""
if [ $# -gt 0 ]; then
    if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
        echo "SPECjvm2008 自动化测试脚本"
        echo ""
        echo "使用方法:"
        echo "  $0                    # 使用系统默认JDK"
        echo "  $0 [JDK名称]          # 使用指定JDK"
        echo ""
        echo "可用的JDK版本:"
        ls -1 "/home/miller/zju/sp_camp/Assignment2/JDK" 2>/dev/null | grep -v install_packet | sed 's/^/  /'
        echo ""
        echo "示例:"
        echo "  $0 bisheng-jdk1.8.0_452"
        echo "  $0 dragonwell-8.25.24"
        exit 0
    fi
    JDK_NAME="$1"
fi

# JDK 设置
JDK_BASE_PATH="/home/miller/zju/sp_camp/Assignment2/JDK"
if [ -n "$JDK_NAME" ]; then
    # 使用指定的JDK
    JAVA_HOME="$JDK_BASE_PATH/$JDK_NAME"
    if [ ! -d "$JAVA_HOME" ]; then
        echo "错误：找不到指定的JDK: $JAVA_HOME"
        echo "可用的JDK版本："
        ls -1 "$JDK_BASE_PATH" 2>/dev/null || echo "  无"
        exit 1
    fi
    
    # 检查java可执行文件
    if [ -f "$JAVA_HOME/bin/java" ]; then
        JAVA_EXE="$JAVA_HOME/bin/java"
    elif [ -f "$JAVA_HOME/jre/bin/java" ]; then
        JAVA_EXE="$JAVA_HOME/jre/bin/java"
    else
        echo "错误：在 $JAVA_HOME 中找不到java可执行文件"
        exit 1
    fi
    
    echo "使用指定JDK: $JDK_NAME"
    echo "   路径: $JAVA_HOME"
else
    # 使用系统默认JDK
    JAVA_EXE="java"
    echo "使用系统默认JDK"
fi

# 要运行的 workload 列表
workloads=("derby")

# 配置文件路径
config_file="/home/miller/zju/sp_camp/Assignment2/config/path_config.properties"

# 指定 SPECjvm2008 的绝对路径
spec_path="/home/miller/zju/sp_camp/SPEC/SPECjvm2008"

# 每个 workload 的迭代次数
iterations=3

# 根据JDK创建输出目录
if [ -n "$JDK_NAME" ]; then
    if [ -n "$OUTPUT_DIR" ]; then
        output_dir="$OUTPUT_DIR/$JDK_NAME"
    else
        output_dir="/home/miller/zju/sp_camp/Assignment2/output/$JDK_NAME"
    fi
    jdk_label="$JDK_NAME"
else
    if [ -n "$OUTPUT_DIR" ]; then
        output_dir="$OUTPUT_DIR/openjdk"
    else
        output_dir="/home/miller/zju/sp_camp/Assignment2/output/openjdk"
    fi
    jdk_label="openjdk"
fi

# 创建输出目录
mkdir -p "$output_dir"

# 输出文件名
output_file="$output_dir/spec_results_summary.txt"
echo "SPECjvm2008 自动测试汇总 - JDK: $jdk_label" > "$output_file"
echo "时间: $(date)" >> "$output_file"
echo "" >> "$output_file"

# 检查 SPECjvm2008 路径是否存在
if [ ! -f "$spec_path/run-specjvm.sh" ]; then
    echo "错误：找不到 $spec_path/run-specjvm.sh，请检查 spec_path 是否正确。"
    exit 1
fi

# 收集系统信息
echo "=== 系统信息 ===" >> "$output_file"
echo "JRE 版本:" >> "$output_file"
$JAVA_EXE -version 2>&1 | tee -a "$output_file" > /dev/null
echo "" >> "$output_file"

echo "操作系统:" >> "$output_file"
grep PRETTY_NAME /etc/os-release >> "$output_file"
echo "" >> "$output_file"

echo "CPU 信息:" >> "$output_file"
lscpu | grep -E 'Model name|CPU\(s\)|Thread|Core|Socket' >> "$output_file"
echo "" >> "$output_file"

echo "内存信息:" >> "$output_file"
free -h | grep Mem >> "$output_file"
echo "" >> "$output_file"

# 遍历运行每个 workload
for wl in "${workloads[@]}"; do
    echo "=== 正在运行 workload: $wl ==="
    log_file="log_${wl}.txt"

    # 运行基准测试并设置环境变量
    cd "$spec_path"
    if [ -n "$JAVA_HOME" ]; then
        export JAVA_HOME="$JAVA_HOME"
    fi
    
    # 获取绝对路径（先确保目录存在）
    mkdir -p "$output_dir"
    abs_output_dir="$(realpath "$output_dir")"
    abs_log_file="$abs_output_dir/$log_file"
    
    $JAVA_EXE  -jar SPECjvm2008.jar -Dspecjvm.result.dir="$abs_output_dir" -pf "$config_file" -i "$iterations"  "$wl" > "$abs_log_file" 2>&1

    # 从日志中提取分数
    score=$(grep "Score on $wl:" "$abs_log_file" | grep -oE '[0-9]+(\.[0-9]+)? ops/m' | head -1)
    if [ -z "$score" ]; then
        # 尝试另一种提取方式
        score=$(grep "result:" "$abs_log_file" | grep "ops/m" | tail -1 | grep -oE '[0-9]+(\.[0-9]+)? ops/m' | head -1)
    fi

    # 写入汇总文件
    if [ -n "$score" ]; then
        echo "[$wl] 分数: $score" >> "$output_file"
        echo "$wl 测试完成 - 分数: $score"
    else
        echo "[$wl] 分数: 获取失败，请检查 $abs_log_file" >> "$output_file"
        echo "$wl 测试失败，详细信息请查看 $abs_log_file"
    fi
    echo "" >> "$output_file"
done

echo ""
echo "所有测试完成，汇总结果写入：$output_file"
