#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JVM性能统计显著性检验
核心统计方法：配对t检验、ANOVA、多重比较校正
自动处理output中的每个run子目录，并将结果输出到Analysis中对应的子目录
"""

import numpy as np
from pathlib import Path
import re
from scipy.stats import ttest_rel, f_oneway, shapiro
from datetime import datetime
from itertools import combinations

def find_run_directories(base_output_dir="/home/miller/zju/sp_camp/Assignment2/output"):
    """查找所有run_*目录"""
    base_path = Path(base_output_dir)
    run_dirs = []
    
    if base_path.exists():
        for item in base_path.iterdir():
            if item.is_dir() and item.name.startswith('run_'):
                run_dirs.append(item)
    
    return sorted(run_dirs)

def extract_performance_data(run_dir):
    """提取指定run目录中的JVM性能数据"""
    jvm_data = {}
    run_path = Path(run_dir)
    
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
        
        # 提取iteration结果
        pattern = r'Iteration \d+ \((?:\d+s|\d+ operation)\) result: (\d+\.\d+) ops/m'
        matches = re.findall(pattern, content)
        
        if matches:
            scores = [float(score) for score in matches]
            jvm_data[jdk_dir.name] = {
                'scores': scores,
                'workload': workload_name,
                'mean': np.mean(scores),
                'std': np.std(scores, ddof=1) if len(scores) > 1 else 0
            }
            print(f"  {jdk_dir.name}: {len(scores)} iterations, 均值: {np.mean(scores):.2f} ops/m")
        else:
            print(f"  {jdk_dir.name}: 在 {log_file.name} 中未找到iteration结果")
    
    return jvm_data

def statistical_tests(jvm_data, run_name, output_file=None, alpha=0.05):
    """执行统计假设检验"""
    
    output_lines = []
    
    def log(text=""):
        print(text)
        output_lines.append(text)
    
    # 基本信息
    workload_name = next(iter(jvm_data.values())).get('workload', 'unknown')
    jvm_names = list(jvm_data.keys())
    
    log("=" * 60)
    log(f"统计显著性检验结果 - {run_name}")
    log("=" * 60)
    log(f"工作负载: {workload_name}")
    log(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log()
    
    # 1. 基本统计信息
    log("基本统计信息:")
    log("-" * 40)
    for name, data in jvm_data.items():
        scores = data['scores']
        log(f"  {name}: {len(scores)} 样本, 均值={data['mean']:.2f}, 标准差={data['std']:.2f}")
    
    # 2. 正态性检验
    log(f"\n正态性检验 (Shapiro-Wilk, α={alpha}):")
    log("-" * 40)
    for name, data in jvm_data.items():
        scores = data['scores']
        if len(scores) >= 3:
            _, p_value = shapiro(scores)
            status = "正态分布" if p_value > alpha else "非正态分布"
            log(f"  {name}: p={p_value:.4f}, {status}")
        else:
            log(f"  {name}: 样本量不足，跳过正态性检验")
    
    # 3. ANOVA分析
    log(f"\n单因素方差分析 (ANOVA):")
    log("-" * 40)
    jvm_scores = [data['scores'] for data in jvm_data.values()]
    f_stat, p_anova = f_oneway(*jvm_scores)
    anova_significant = p_anova < alpha
    
    log(f"  F统计量: {f_stat:.4f}")
    log(f"  p值: {p_anova:.6f}")
    log(f"  结论: {'有显著差异' if anova_significant else '无显著差异'}")
    
    # 4. 配对t检验（如果样本量相同）
    sample_sizes = [len(data['scores']) for data in jvm_data.values()]
    t_test_results = []
    corrected_significant = []
    
    if len(set(sample_sizes)) == 1 and sample_sizes[0] > 1:
        log(f"\n配对t检验:")
        log("-" * 40)
        
        n_comparisons = len(list(combinations(jvm_names, 2)))
        
        for jvm1, jvm2 in combinations(jvm_names, 2):
            data1, data2 = jvm_data[jvm1]['scores'], jvm_data[jvm2]['scores']
            t_stat, p_value = ttest_rel(data1, data2)
            
            t_test_results.append((jvm1, jvm2, t_stat, p_value))
            
            significant = p_value < alpha
            status = "显著" if significant else "不显著"
            log(f"  {jvm1} vs {jvm2}: t={t_stat:.4f}, p={p_value:.6f}, {status}")
        
        # 5. Bonferroni多重比较校正
        log(f"\nBonferroni多重比较校正:")
        log("-" * 40)
        
        corrected_alpha = alpha / n_comparisons
        log(f"  原始α: {alpha:.3f}")
        log(f"  比较次数: {n_comparisons}")
        log(f"  校正后α: {corrected_alpha:.6f}")
        log(f"  校正后结果:")
        
        for jvm1, jvm2, t_stat, p_value in t_test_results:
            significant = p_value < corrected_alpha
            if significant:
                corrected_significant.append((jvm1, jvm2))
            
            status = "显著" if significant else "不显著"
            log(f"    {jvm1} vs {jvm2}: p={p_value:.6f}, {status}")
    else:
        log(f"\n配对t检验: 样本量不同，无法进行")
    
    # 5. 结论
    log(f"\n统计分析结论:")
    log("-" * 40)
    
    if anova_significant:
        log(f"✓ ANOVA显示JVM间存在显著差异")
        if corrected_significant:
            log(f"✓ 经Bonferroni校正后仍显著的JVM对:")
            for jvm1, jvm2 in corrected_significant:
                mean1, mean2 = jvm_data[jvm1]['mean'], jvm_data[jvm2]['mean']
                log(f"  - {jvm1} ({mean1:.2f}) vs {jvm2} ({mean2:.2f})")
        else:
            log(f"⚠ 经Bonferroni校正后无显著差异")
    else:
        log(f"○ ANOVA显示JVM间无显著差异")
    
    # 6. 性能排名
    log(f"\n性能排名:")
    log("-" * 40)
    sorted_jvms = sorted(jvm_data.items(), key=lambda x: x[1]['mean'], reverse=True)
    for i, (name, data) in enumerate(sorted_jvms, 1):
        log(f"  {i}. {name}: {data['mean']:.2f}±{data['std']:.2f} ops/m")
    
    # 保存结果
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        log(f"\n结果已保存到: {output_file}")
    
    return {
        'anova_significant': anova_significant,
        'corrected_significant_pairs': corrected_significant,
        'ranking': sorted_jvms
    }

def main():
    """主函数"""
    print("JVM性能统计假设检验分析")
    print("=" * 60)
    
    # 查找所有run目录
    run_dirs = find_run_directories()
    
    if not run_dirs:
        print("错误: 没有找到任何run_*目录!")
        print("请确保已经运行过测试脚本")
        return
    
    print(f"找到 {len(run_dirs)} 个运行目录:")
    for run_dir in run_dirs:
        print(f"  - {run_dir.name}")
    print()
    
    # 创建Analysis目录
    analysis_base_dir = Path("/home/miller/zju/sp_camp/Assignment2/Analysis")
    analysis_base_dir.mkdir(parents=True, exist_ok=True)
    
    # 处理每个run目录
    all_results = {}
    
    for run_dir in run_dirs:
        print(f"\n{'='*60}")
        print(f"分析运行: {run_dir.name}")
        print('='*60)
        
        # 提取数据
        jvm_data = extract_performance_data(run_dir)
        
        if len(jvm_data) < 2:
            print(f"  跳过: JVM数量不足 (需要至少2个JVM)")
            continue
        
        # 执行统计检验
        output_file = analysis_base_dir / run_dir.name / "statistical_analysis.txt"
        results = statistical_tests(jvm_data, run_dir.name, output_file)
        all_results[run_dir.name] = results
    
    # 生成总结报告
    if all_results:
        print(f"\n{'='*60}")
        print("总结报告")
        print('='*60)
        
        summary_file = analysis_base_dir / "summary_report.txt"
        summary_lines = [
            "SPECjvm2008 JVM性能统计分析总结报告",
            "=" * 60,
            f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"总运行次数: {len(all_results)}",
            ""
        ]
        
        for run_name, results in all_results.items():
            summary_lines.extend([
                f"运行: {run_name}",
                "-" * 40
            ])
            
            if results['anova_significant']:
                summary_lines.append("✓ ANOVA显示JVM间存在显著差异")
                if results['corrected_significant_pairs']:
                    summary_lines.append("✓ 经Bonferroni校正后仍有显著差异的JVM对:")
                    for jvm1, jvm2 in results['corrected_significant_pairs']:
                        summary_lines.append(f"  - {jvm1} vs {jvm2}")
                else:
                    summary_lines.append("⚠ 经Bonferroni校正后无显著差异")
            else:
                summary_lines.append("○ ANOVA显示JVM间无显著差异")
            
            summary_lines.append("性能排名:")
            for i, (name, data) in enumerate(results['ranking'][:3], 1):
                summary_lines.append(f"  {i}. {name}: {data['mean']:.2f} ops/m")
            summary_lines.append("")
        
        # 保存和显示总结
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(summary_lines))
        
        for line in summary_lines:
            print(line)
        
        print(f"总结报告已保存到: {summary_file}")
    
    print(f"\n分析完成! 详细结果请查看 Analysis/ 目录")

if __name__ == "__main__":
    main()
