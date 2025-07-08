#!/bin/bash
#
# 增强版 Java 火焰图生成脚本
# 支持更全面的系统调用和内核事件采集
#

set -e

# 配置

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERF_MAP_AGENT_DIR="$SCRIPT_DIR/perf-map-agent"
FLAMEGRAPH_DIR="$SCRIPT_DIR/FlameGraph"
WORK_DIR="$SCRIPT_DIR/flamegraph_work"
SPECJVM_DIR="/home/miller/zju/sp_camp/SPEC/SPECjvm2008"
OUTPUT_DIR="$SCRIPT_DIR/output"

# 默认配置
export PERF_RECORD_SECONDS=${PERF_RECORD_SECONDS:-60}
export PERF_RECORD_FREQ=${PERF_RECORD_FREQ:-99}

# 检查和设置系统配置

setup_system_config() {
    echo "检查系统配置..."
    
    # 检查当前权限设置
    PARANOID=$(cat /proc/sys/kernel/perf_event_paranoid)
    KPTR_RESTRICT=$(cat /proc/sys/kernel/kptr_restrict)
    
    echo "当前 perf_event_paranoid: $PARANOID"
    echo "当前 kptr_restrict: $KPTR_RESTRICT"
    
    # 如果权限过于严格，尝试临时放宽
    if [ "$PARANOID" -gt 2 ]; then
        echo "权限过于严格，尝试临时调整..."
        echo "需要 root 权限来调整系统配置"
        
        # 备份原始值
        echo "$PARANOID" > /tmp/original_perf_paranoid.bak
        echo "$KPTR_RESTRICT" > /tmp/original_kptr_restrict.bak
        
        # 临时放宽权限以获得更丰富的性能数据
        sudo sysctl -w kernel.perf_event_paranoid=1
        sudo sysctl -w kernel.kptr_restrict=0
        
        echo "系统配置已临时调整为更宽松的设置"
        echo "这将允许收集更全面的性能数据包括内核符号"
    fi
}

restore_system_config() {
    # 恢复原始系统配置
    if [ -f /tmp/original_perf_paranoid.bak ]; then
        ORIGINAL_PARANOID=$(cat /tmp/original_perf_paranoid.bak)
        ORIGINAL_KPTR=$(cat /tmp/original_kptr_restrict.bak)
        
        echo "恢复系统配置..."
        sudo sysctl -w kernel.perf_event_paranoid=$ORIGINAL_PARANOID
        sudo sysctl -w kernel.kptr_restrict=$ORIGINAL_KPTR
        
        rm -f /tmp/original_perf_paranoid.bak /tmp/original_kptr_restrict.bak
        echo "系统配置已恢复"
    fi
}

# 参数解析

if [ $# -eq 0 ]; then
    echo "用法: $0 [-s] [-t seconds] <program_name>"
    echo ""
    echo "  -s              运行 SPECjvm2008 模式"
    echo "  -t seconds      采集时间 (默认: 60秒)"
    echo "  program_name    程序名称"
    echo ""
    echo "示例:"
    echo "  $0 TestFibonacci"
    echo "  $0 -s compress"
    echo "  $0 -t 30 TestFibonacci"
    exit 1
fi

RUN_SPEC=false
RECORD_TIME=60
PROGRAM_NAME=""

# 解析参数
while [ $# -gt 0 ]; do
    case "$1" in
        -s)
            RUN_SPEC=true
            shift
            ;;
        -t)
            shift
            RECORD_TIME="$1"
            [ -z "$RECORD_TIME" ] && { echo "错误: -t 参数需要提供时间值"; exit 1; }
            shift
            ;;
        -*)
            echo "错误: 未知参数 $1"
            exit 1
            ;;
        *)
            PROGRAM_NAME="$1"
            shift
            ;;
    esac
done

[ -z "$PROGRAM_NAME" ] && { echo "错误: 需要提供程序名称"; exit 1; }

export PERF_RECORD_SECONDS=$RECORD_TIME

# 初始化和检查

echo "启动火焰图生成 - $PROGRAM_NAME"
echo "采集时间: ${PERF_RECORD_SECONDS}秒"

# 检查依赖
[ ! -x "$FLAMEGRAPH_DIR/stackcollapse-perf.pl" ] && { echo "错误: FlameGraph 未找到"; exit 1; }
[ ! -f "$PERF_MAP_AGENT_DIR/out/attach-main.jar" ] && { echo "错误: perf-map-agent 未找到"; exit 1; }
command -v perf >/dev/null || { echo "错误: perf 工具未安装"; exit 1; }

# 设置系统配置
setup_system_config

# 设置清理函数
cleanup() {
    echo "清理资源..."
    restore_system_config
    [ -n "$JAVA_PID" ] && kill -9 "$JAVA_PID" 2>/dev/null || true
}
trap cleanup INT TERM

# 设置 JAVA_HOME
if [ -z "$JAVA_HOME" ]; then
    for path in /usr/lib/jvm/default-java /etc/alternatives/java_sdk; do
        [ -d "$path" ] && { JAVA_HOME="$path"; break; }
    done
    [ -z "$JAVA_HOME" ] && { echo "错误: 无法找到 JAVA_HOME"; exit 1; }
fi

# 创建程序目录
PROGRAM_WORK_DIR="$WORK_DIR/${PROGRAM_NAME}_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$PROGRAM_WORK_DIR"
echo "工作目录: $PROGRAM_WORK_DIR"

# 设置输出文件路径
PERF_FLAME_OUTPUT="$PROGRAM_WORK_DIR/flamegraph.svg"
PERF_DATA_FILE="$PROGRAM_WORK_DIR/perf.data"

mkdir -p "$WORK_DIR"

# 启动程序

cd "$SCRIPT_DIR"
if [ "$RUN_SPEC" = true ]; then
    echo "启动 SPECjvm2008: $PROGRAM_NAME"
    cd "$SPECJVM_DIR"
    java -XX:+PreserveFramePointer -XX:+UnlockDiagnosticVMOptions \
         -XX:+DebugNonSafepoints -XX:-OptimizeStringConcat \
         -jar SPECjvm2008.jar -Dspecjvm.result.dir="$OUTPUT_DIR" \
         -ikv --lagom -i 1 -bt 16 $PROGRAM_NAME &
else
    echo "启动 Java 程序: $PROGRAM_NAME"
    java -XX:+PreserveFramePointer -XX:+UnlockDiagnosticVMOptions \
         -XX:+DebugNonSafepoints -XX:-OptimizeStringConcat \
         $PROGRAM_NAME &
fi

JAVA_PID=$!
sleep 2
kill -0 "$JAVA_PID" 2>/dev/null || { echo "错误: 程序启动失败"; exit 1; }
echo "程序已启动，PID: $JAVA_PID"

# 性能采样和火焰图生成

echo "开始性能采样 ($PERF_RECORD_SECONDS 秒)..."

# 文件路径
STACKS="$PROGRAM_WORK_DIR/out-$JAVA_PID.stacks"
PERF_MAP_FILE="/tmp/perf-$JAVA_PID.map"
ATTACH_JAR="$PERF_MAP_AGENT_DIR/out/attach-main.jar"

# 获取进程信息
TARGET_UID=$(awk '/^Uid:/{print $2}' /proc/$JAVA_PID/status)
TARGET_GID=$(awk '/^Gid:/{print $2}' /proc/$JAVA_PID/status)

# 1. 性能数据采集 - 简化采样配置
echo "采集性能数据..."
sudo perf record \
    -F $PERF_RECORD_FREQ \
    -o "$PERF_DATA_FILE" \
    -g \
    --call-graph dwarf,16384 \
    -p $JAVA_PID \
    -- sleep $PERF_RECORD_SECONDS

# 2. 创建 Java 符号映射
echo "创建 Java 符号映射..."
sudo rm -f "$PERF_MAP_FILE"
(cd "$PERF_MAP_AGENT_DIR/out" && \
 sudo -u "#$TARGET_UID" -g "#$TARGET_GID" \
 "$JAVA_HOME/bin/java" -cp "$ATTACH_JAR:$JAVA_HOME/lib/tools.jar" \
 net.virtualvoid.perf.AttachOnce $JAVA_PID)
sudo chown root:root "$PERF_MAP_FILE" 2>/dev/null || true

# 3. 生成堆栈信息
echo "处理性能数据..."
sudo perf script -i "$PERF_DATA_FILE" \
    --show-kernel-path \
    --kallsyms=/proc/kallsyms \
    --fields comm,pid,tid,time,ip,sym,dso \
    > "$STACKS"

# 4. 生成火焰图
echo "生成火焰图..."
"$FLAMEGRAPH_DIR/stackcollapse-perf.pl" "$STACKS" | \
"$FLAMEGRAPH_DIR/flamegraph.pl" \
    --color=java \
    --title="$PROGRAM_NAME - Performance Profile" \
    --subtitle="Java性能分析火焰图, 采样时间: ${PERF_RECORD_SECONDS}s" \
    --width=1400 \
    --fontsize=10 \
    --hash \
    > "$PERF_FLAME_OUTPUT"

echo "火焰图已生成: $PERF_FLAME_OUTPUT"

# 5. 导出数据库
if command -v python3 >/dev/null 2>&1 && [ -f "$SCRIPT_DIR/export_to_database.py" ]; then
    echo "导出性能数据到数据库..."
    if python3 "$SCRIPT_DIR/export_to_database.py" \
        "$STACKS" \
        "$PROGRAM_WORK_DIR" \
        --program-name "$PROGRAM_NAME" \
        --record-seconds "$PERF_RECORD_SECONDS"; then
        echo "数据库导出成功: $PROGRAM_WORK_DIR/performance_data.sqlite"
    else
        echo "数据库导出失败，请检查错误信息"
    fi
else
    echo "跳过数据库导出: 缺少 python3 或 export_to_database.py"
fi

# 6. 清理临时文件
echo "清理临时文件..."
sudo rm -f "$PERF_DATA_FILE"
echo "清理完成"

echo ""
echo "生成的文件:"
echo "  火焰图: $PERF_FLAME_OUTPUT"
if [ -f "$PROGRAM_WORK_DIR/performance_data.sqlite" ]; then
    echo "  数据库: $PROGRAM_WORK_DIR/performance_data.sqlite"
fi

# 主动终止Java程序
if [ -n "$JAVA_PID" ] && kill -0 "$JAVA_PID" 2>/dev/null; then
    echo "终止Java程序 (PID: $JAVA_PID)..."
    kill -TERM "$JAVA_PID" 2>/dev/null || true
    sleep 2
    # 如果程序还在运行，强制终止
    if kill -0 "$JAVA_PID" 2>/dev/null; then
        kill -KILL "$JAVA_PID" 2>/dev/null || true
    fi
fi

# 手动清理
cleanup

echo "完成"
