#!/bin/bash

# 要运行的 workload 列表
workloads=("compiler.compiler" "crypto" "scimark.fft.small" "startup.helloworld" "scimark.monte_carlo" "sunflow")

# 配置文件路径
config_file="/home/miller/zju/sp_camp/Assignment1/config/path_config.properties"

# 指定 SPECjvm2008 的绝对路径
spec_path="/home/miller/zju/sp_camp/SPEC/SPECjvm2008"

#  每个 workload 的迭代次数
iterations=1

#  输出文件名
output_file="/home/miller/zju/sp_camp/Assignment1/output/spec_results_summary.txt"
echo "SPECjvm2008 自动测试汇总" > "$output_file"
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
java -version 2>&1 | tee -a "$output_file" > /dev/null
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
    ./run-specjvm.sh -i "$iterations" "$wl" -pf "$config_file" > "/home/miller/zju/sp_camp/Assignment1/output/$log_file" 2>&1

    # 从日志中提取分数
    score=$(grep "Score on $wl:" "/home/miller/zju/sp_camp/Assignment1/output/$log_file" | grep -oE '[0-9]+(\.[0-9]+)? ops/m' | head -1)
    if [ -z "$score" ]; then
        # 尝试另一种提取方式
        score=$(grep "result:" "/home/miller/zju/sp_camp/Assignment1/output/$log_file" | grep "ops/m" | tail -1 | grep -oE '[0-9]+(\.[0-9]+)? ops/m' | head -1)
    fi

    # 写入汇总文件
    if [ -n "$score" ]; then
        echo "[$wl] 分数: $score" >> "$output_file"
        echo "$wl 测试完成 - 分数: $score"
    else
        echo "[$wl] 分数: 获取失败，请检查 output/$log_file" >> "$output_file"
        echo "$wl 测试失败，详细信息请查看 output/$log_file"
    fi
    echo "" >> "$output_file"
done

echo ""
echo "所有测试完成，汇总结果写入：$output_file"
