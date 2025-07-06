#!/bin/bash

# SPECjvm2008 批量测试脚本 - 对所有JDK运行基准测试
# 使用方法: ./run_all_jdks.sh

# 检查帮助参数
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "SPECjvm2008 批量基准测试脚本"
    echo ""
    echo "使用方法:"
    echo "  $0                    # 对所有JDK运行完整基准测试"
    echo "  $0 --help            # 显示此帮助信息"
    echo ""
    echo "功能:"
    echo "  - 自动检测所有可用的JDK版本"
    echo "  - 依次对每个JDK运行基准测试"
    echo "  - 同时测试系统默认JDK"
    echo "  - 生成综合测试报告"
    echo ""
    echo "输出:"
    echo "  - 每次运行都会创建带时间戳的新目录 output/run_YYYYMMDD_HHMMSS/"
    echo "  - 每个JDK的详细结果保存在该目录下的 [JDK名称]/ 子目录中"
    echo "  - 所有JDK的汇总报告保存在该目录下的 all_jdks_summary.txt"
    echo ""
    echo "注意: 完整测试可能需要较长时间，请确保有足够的时间完成测试。"
    exit 0
fi

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKLOAD_SCRIPT="$SCRIPT_DIR/run_workload.sh"
JDK_BASE_PATH="/home/miller/zju/sp_camp/Assignment2/JDK"
OUTPUT_BASE_DIR="/home/miller/zju/sp_camp/Assignment2/output"

# 创建带时间戳的运行目录
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RUN_DIR="$OUTPUT_BASE_DIR/run_$TIMESTAMP"
mkdir -p "$RUN_DIR"

echo "本次运行结果将保存在: $RUN_DIR"

# 检查run_workload.sh是否存在
if [ ! -f "$WORKLOAD_SCRIPT" ]; then
    echo "错误：找不到 run_workload.sh 脚本"
    echo "请确保 run_workload.sh 在当前目录中"
    exit 1
fi

# 检查JDK目录是否存在
if [ ! -d "$JDK_BASE_PATH" ]; then
    echo "错误：找不到JDK目录: $JDK_BASE_PATH"
    exit 1
fi

# 获取所有可用的JDK（排除install_packet目录）
available_jdks=($(ls -1 "$JDK_BASE_PATH" | grep -v install_packet))

if [ ${#available_jdks[@]} -eq 0 ]; then
    echo "错误：在 $JDK_BASE_PATH 中没有找到任何JDK"
    exit 1
fi

echo "=========================================="
echo "SPECjvm2008 批量基准测试"
echo "=========================================="
echo "找到 ${#available_jdks[@]} 个JDK版本："
for jdk in "${available_jdks[@]}"; do
    echo "  - $jdk"
done
echo ""

# 创建总结文件
summary_file="$RUN_DIR/all_jdks_summary.txt"
echo "SPECjvm2008 所有JDK基准测试总结" > "$summary_file"
echo "测试时间: $(date)" >> "$summary_file"
echo "运行目录: $RUN_DIR" >> "$summary_file"
echo "测试的JDK版本: ${available_jdks[*]}" >> "$summary_file"
echo "" >> "$summary_file"

# 记录开始时间
start_time=$(date +%s)

# 遍历所有JDK并运行测试
for jdk in "${available_jdks[@]}"; do
    echo "=========================================="
    echo "开始测试 JDK: $jdk"
    echo "=========================================="
    
    # 记录单个JDK测试开始时间
    jdk_start_time=$(date +%s)
    
    # 运行测试，指定输出目录为当前运行目录
    echo "正在运行: $WORKLOAD_SCRIPT $jdk"
    if OUTPUT_DIR="$RUN_DIR" "$WORKLOAD_SCRIPT" "$jdk"; then
        jdk_end_time=$(date +%s)
        jdk_duration=$((jdk_end_time - jdk_start_time))
        echo "JDK $jdk 测试完成，耗时: ${jdk_duration}秒"
        
        # 提取测试结果并添加到总结文件
        result_file="$RUN_DIR/$jdk/spec_results_summary.txt"
        if [ -f "$result_file" ]; then
            echo "=== $jdk 测试结果 ===" >> "$summary_file"
            grep "\[.*\] 分数:" "$result_file" >> "$summary_file" 2>/dev/null || echo "未找到分数信息" >> "$summary_file"
            echo "测试耗时: ${jdk_duration}秒" >> "$summary_file"
            echo "" >> "$summary_file"
        else
            echo "=== $jdk 测试结果 ===" >> "$summary_file"
            echo "错误：未找到结果文件" >> "$summary_file"
            echo "" >> "$summary_file"
        fi
    else
        echo "错误：JDK $jdk 测试失败"
        echo "=== $jdk 测试结果 ===" >> "$summary_file"
        echo "错误：测试失败" >> "$summary_file"
        echo "" >> "$summary_file"
    fi
    
    echo ""
done

# 同时测试系统默认JDK
echo "=========================================="
echo "开始测试系统默认JDK"
echo "=========================================="

jdk_start_time=$(date +%s)
if OUTPUT_DIR="$RUN_DIR" "$WORKLOAD_SCRIPT"; then
    jdk_end_time=$(date +%s)
    jdk_duration=$((jdk_end_time - jdk_start_time))
    echo "系统默认JDK测试完成，耗时: ${jdk_duration}秒"
    
    # 提取测试结果并添加到总结文件
    result_file="$RUN_DIR/system-default/spec_results_summary.txt"
    if [ -f "$result_file" ]; then
        echo "=== system-default 测试结果 ===" >> "$summary_file"
        grep "\[.*\] 分数:" "$result_file" >> "$summary_file" 2>/dev/null || echo "未找到分数信息" >> "$summary_file"
        echo "测试耗时: ${jdk_duration}秒" >> "$summary_file"
        echo "" >> "$summary_file"
    fi
else
    echo "错误：系统默认JDK测试失败"
    echo "=== system-default 测试结果 ===" >> "$summary_file"
    echo "错误：测试失败" >> "$summary_file"
    echo "" >> "$summary_file"
fi

# 计算总耗时
end_time=$(date +%s)
total_duration=$((end_time - start_time))

echo "=========================================="
echo "所有测试完成!"
echo "=========================================="
echo "总耗时: ${total_duration}秒"
echo "测试的JDK数量: $((${#available_jdks[@]} + 1))"
echo "本次运行目录: $RUN_DIR"
echo "结果汇总文件: $summary_file"
echo ""
echo "各JDK结果目录:"
for jdk in "${available_jdks[@]}"; do
    echo "  $jdk: $RUN_DIR/$jdk/"
done
echo "  system-default: $RUN_DIR/system-default/"
echo ""

# 在总结文件中添加总体信息
echo "=== 测试总结 ===" >> "$summary_file"
echo "总耗时: ${total_duration}秒" >> "$summary_file"
echo "测试完成时间: $(date)" >> "$summary_file"

echo "详细结果请查看各JDK目录中的spec_results_summary.txt文件"
