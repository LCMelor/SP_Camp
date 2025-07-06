#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SPECjvm2008 日志数据提取和可视化工具
从 log_compress.txt 文件中提取 iteration 数据并生成性能对比图表
"""

import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import re

def find_run_directories(base_output_dir="/home/miller/zju/sp_camp/Assignment2/output"):
    """查找所有run_*目录"""
    base_path = Path(base_output_dir)
    run_dirs = []
    
    if base_path.exists():
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith('run_'):
                run_dirs.append(item)
    
    return sorted(run_dirs)

def extract_iteration_scores(run_dir):
    """从指定run目录中提取 iteration 得分"""
    run_path = Path(run_dir)
    jdk_data = {}
    
    print(f"处理运行目录: {run_path.name}")
    
    for jdk_dir in run_path.iterdir():
        if not jdk_dir.is_dir():
            continue
            
        # 查找日志文件
        log_files = list(jdk_dir.glob("log_*.txt"))
        if not log_files:
            print(f"  {jdk_dir.name}: 未找到日志文件")
            continue
            
        log_file = log_files[0]
        workload_name = log_file.stem.replace('log_', '')
        
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 提取 iteration 结果
        pattern = r'Iteration \d+ \((?:\d+s|\d+ operation)\) result: (\d+\.\d+) ops/m'
        matches = re.findall(pattern, content)
        
        if matches:
            scores = [float(score) for score in matches]
            jdk_data[jdk_dir.name] = {
                'scores': scores,
                'mean': np.mean(scores),
                'std': np.std(scores, ddof=1) if len(scores) > 1 else 0,
                'workload': workload_name
            }
            print(f"  {jdk_dir.name}: {len(scores)} iterations, 均值: {np.mean(scores):.2f} ops/m")
        else:
            print(f"  {jdk_dir.name}: 在 {log_file.name} 中未找到iteration结果")
    
    return jdk_data

def create_performance_chart(jdk_data, run_name, output_dir="/home/miller/zju/sp_camp/Assignment2/img"):
    """绘制性能对比柱状图"""
    if not jdk_data:
        print("No data found")
        return
    
    # 创建输出目录
    run_img_dir = Path(output_dir) / run_name
    run_img_dir.mkdir(parents=True, exist_ok=True)
    
    # 准备数据
    jdk_names = [name.replace('-', ' ').replace('_', ' ') for name in jdk_data.keys()]
    mean_scores = [data['mean'] for data in jdk_data.values()]
    std_scores = [data['std'] for data in jdk_data.values()]
    
    # 创建图表
    plt.style.use('seaborn-v0_8')
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 计算Y轴范围以突出差异
    min_score, max_score = min(mean_scores), max(mean_scores)
    max_std = max(std_scores) if std_scores else 0
    score_range = max_score - min_score
    
    if score_range > 0:
        y_margin = max(score_range * 0.1, max_std * 1.5)
        y_min = max(0, min_score - y_margin)
        y_max = max_score + max_std + y_margin
    else:
        y_min = 0
        y_max = max_score + max_std + max_score * 0.1
    
    # 绘制柱状图
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
    bars = ax.bar(jdk_names, mean_scores, yerr=std_scores, capsize=8, 
                 color=colors[:len(jdk_names)], alpha=0.8, 
                 edgecolor='black', linewidth=1.5)
    
    ax.set_ylim(y_min, y_max)
    
    # 添加数值标签和相对性能
    best_score = max(mean_scores)
    for bar, mean, std in zip(bars, mean_scores, std_scores):
        height = bar.get_height()
        # 主要数值标签
        ax.text(bar.get_x() + bar.get_width()/2., height + std + (y_max - y_min)*0.01,
               f'{mean:.2f}±{std:.2f}', ha='center', va='bottom', 
               fontweight='bold', fontsize=11)
        
        # 相对性能标签
        if mean == best_score:
            label, color = 'BEST', 'darkgreen'
        else:
            label, color = f'{(mean/best_score)*100:.1f}%', 'black'
        
        ax.text(bar.get_x() + bar.get_width()/2., height - (height - y_min)*0.1,
               label, ha='center', va='top', fontsize=9, color='white', 
               fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', 
               facecolor=color, alpha=0.7))
    
    # 获取工作负载名称
    workload_name = next(iter(jdk_data.values())).get('workload', 'unknown')
    
    # 设置图表格式
    ax.set_title(f'SPECjvm2008 Performance Comparison - {run_name}\n({workload_name} workload)', 
                fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('JVM Implementation', fontsize=12, fontweight='bold')
    ax.set_ylabel('Performance Score (ops/m)', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # 保存图表
    output_path = run_img_dir / 'jvm_performance_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"  Chart saved to: {output_path}")
    plt.close()

def create_simple_boxplot(jdk_data, run_name, output_dir="/home/miller/zju/sp_camp/Assignment2/img"):
    """生成箱线图"""
    if not jdk_data:
        print("No data found for boxplot")
        return
    
    # 创建输出目录
    run_img_dir = Path(output_dir) / run_name
    run_img_dir.mkdir(parents=True, exist_ok=True)
    
    # 准备数据
    jdk_names = [name.replace('-', ' ').replace('_', ' ') for name in jdk_data.keys()]
    all_scores = [data['scores'] for data in jdk_data.values()]
    
    # 创建箱线图
    plt.figure(figsize=(10, 6))
    
    # 绘制箱线图
    bp = plt.boxplot(all_scores, tick_labels=jdk_names, patch_artist=True,
                     notch=False, showmeans=True)
    
    # 设置颜色
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57', '#FF9FF3']
    for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    # 获取工作负载名称
    workload_name = next(iter(jdk_data.values())).get('workload', 'unknown')
    
    # 设置样式
    plt.title(f'JVM Performance Distribution - {run_name}\n({workload_name} workload)', 
              fontsize=14, fontweight='bold')
    plt.xlabel('JVM Implementation', fontweight='bold')
    plt.ylabel('Performance Score (ops/m)', fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # 保存图表
    output_path = run_img_dir / 'jvm_boxplot.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"  Boxplot saved to: {output_path}")
    plt.close()

def print_performance_ranking(jdk_data, run_name):
    """打印性能排名"""
    if not jdk_data:
        return
    
    # 按性能排序
    sorted_jdks = sorted(jdk_data.items(), key=lambda x: x[1]['mean'], reverse=True)
    
    print(f"  === {run_name} Performance Ranking ===")
    for i, (jdk_name, data) in enumerate(sorted_jdks, 1):
        display_name = jdk_name.replace('-', ' ').replace('_', ' ')
        print(f"  {i}. {display_name}: {data['mean']:.2f}±{data['std']:.2f} ops/m")

def main():
    """主函数"""
    print("=== SPECjvm2008 Log Data Analysis ===")
    print("正在查找和分析所有运行结果...")
    
    # 查找所有run目录
    run_dirs = find_run_directories()
    
    if not run_dirs:
        print("没有找到任何run_*目录!")
        print("请确保已经运行过 run_all_jdks.sh 脚本")
        return
    
    print(f"找到 {len(run_dirs)} 个运行目录:")
    for run_dir in run_dirs:
        print(f"  - {run_dir.name}")
    print()
    
    # 处理每个run目录
    for run_dir in run_dirs:
        print(f"======== 分析 {run_dir.name} ========")
        
        # 提取数据
        jdk_data = extract_iteration_scores(run_dir)
        
        if not jdk_data:
            print(f"  {run_dir.name} 中没有找到测试数据!")
            continue
        
        # 创建图表
        print(f"  创建性能对比柱状图...")
        create_performance_chart(jdk_data, run_dir.name)
        
        print(f"  创建箱线图...")
        create_simple_boxplot(jdk_data, run_dir.name)
        
        # 打印排名
        print_performance_ranking(jdk_data, run_dir.name)
    
    print("\n=== 所有分析完成! ===")
    print(f"结果图表保存在 img/ 目录下的各个子目录中")
if __name__ == "__main__":
    main()
