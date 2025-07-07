# Assignment2 - SPECjvm2008 自动化基准测试系统

本项目实现了一个完整的 SPECjvm2008 自动化基准测试系统，支持多种 JDK 的自动化性能测试，将 JDK 的性能表现可视化（柱状图和箱线图），并使用配对 t 检验等统计方法对 JDK 之间的性能差异进行显著性检验。

## 功能特性

### 1. 自动化测试
- **多JDK支持**: 自动检测并测试所有可用的JDK版本
- **多轮测试**: 支持多次iteration以提高结果可靠性
- **多种workload**: 自定义运行的工作负载
- **结果归档**: 每次运行自动创建带时间戳的目录结构

### 2. 性能差异可视化
- **柱状图**: 显示各JDK的平均性能和标准差
- **箱线图**: 展示性能分布和异常值
- **优化坐标系**: 突出JVM间的性能差异
- **相对性能标签**: 显示相对于最佳性能的百分比

### 3. 统计分析
- **正态性检验**: Shapiro-Wilk检验数据分布
- **方差分析**: ANOVA检验JVM间整体差异
- **配对t检验**: 两两比较JVM性能
- **多重比较校正**: Bonferroni校正控制第一类错误

## 目录结构

```
Assignment2/
├── JDK/                     # JDK安装目录
│   ├── bisheng-jdk/
│   ├── dragonwell/
│   └── TencentKona/
├── config/                  # 配置文件
│   └── path_config.properties
├── scripts/                 # 分析脚本
│   ├── extract_and_plot.py    # 性能可视化
│   └── hypothesis_testing.py  # 统计分析
├── output/                  # 测试结果
│   ├── run_YYYYMMDD_HHMMSS/
│   │   ├── JDK1/
│   │   │   ├── log_*.txt
│   │   │   └── SPECjvm2008.*/
│   │   └── all_jdks_summary.txt
├── img/                     # 可视化图表
│   └── run_YYYYMMDD_HHMMSS/
│       ├── jvm_performance_comparison.png
│       └── jvm_boxplot.png
├── Analysis/                # 统计分析结果
│   ├── run_YYYYMMDD_HHMMSS/
│   │   └── statistical_analysis.txt
│   └── summary_report.txt
├── run_workload.sh         # 单JDK测试脚本
├── run_all_jdks.sh         # 批量测试脚本
```

## 系统要求

### Python 环境依赖
```bash
# 必需的 Python 包
pip install matplotlib>=3.3.0
pip install numpy>=1.19.0
pip install scipy>=1.5.0
pip install pathlib2  # Python < 3.4 需要
```

### 快速环境配置
```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 验证安装
python -c "import matplotlib, numpy, scipy; print('环境配置成功')"
```

## 使用方法

### 1. 运行单个JDK测试
```bash
./run_workload.sh                    # 使用系统默认JDK
./run_workload.sh TencentKona        # 使用指定JDK
```

### 2. 批量测试所有JDK
```bash
./run_all_jdks.sh
```

### 3. 性能可视化分析
```bash
python scripts/extract_and_plot.py
```

### 4. 统计假设检验
```bash
python scripts/hypothesis_testing.py
```

## 使用示例

### 完整测试流程示例

1. **准备 JDK 环境**：
   在 `JDK/` 目录中准备好 openjdk、bisheng-jdk、dragonwell 和 TencentKona 等 JDK 版本。

2. **配置测试参数**：
   修改 `run_workload.sh` 脚本中的 `workload` 变量为 `compress`，表示测试 compress 工作负载；设置 `iteration` 为 3，表示每个 JDK 运行该工作负载迭代 3 次。

3. **执行批量测试**：
   ```bash
   ./run_all_jdks.sh
   ```

4. **查看测试结果**：
   在 `output/` 目录下会生成 `run_YYYYMMDD_HHMMSS/` 格式的结果目录，每个 JDK 的测试结果存放在各自的子目录中。

5. **生成性能可视化图表**：
   ```bash
   python scripts/extract_and_plot.py
   ```
   在 `img/` 目录中会生成对应的性能可视化图表。

6. **进行统计分析**：
   ```bash
   python scripts/hypothesis_testing.py
   ```
   对运行结果进行统计假设检验，验证 JVM 之间的性能差异是否显著。

## 核心脚本说明

### run_workload.sh
- 单个JDK的测试脚本
- 支持参数配置运行的JDK
- 修改脚本内`workload`变量自定义运行的工作负载
- 修改脚本内`iteration`变量自定义迭代次数

### run_all_jdks.sh  
- 批量测试脚本，自动检测`JDK/`目录下所有可用的JDK
- 每次运行在`output`目录下创建带时间戳的`run_*`目录作为一次运行的子目录
- 生成综合测试报告，记录每个JDK的最终得分
- 在每个JDK子目录下生成运行日志与系统信息文档

### extract_and_plot.py
- 自动遍历`output`目录下的所有`run_*`子目录
- 提取每个JDK运行的性能得分，并计算多轮迭代的平均得分作为最终得分
- 生成优化的性能对比图表
- 按运行分组保存图表

### hypothesis_testing.py
- 对每个run目录进行统计分析
- 正态性检验、ANOVA、配对t检验
- Bonferroni多重比较校正
- 生成详细的统计报告


## Bouns Problems
### 1.Why is there run to run performance variation?
每次运行时，CPU核心、内存、缓存等资源存在不一致性。在多核场景下，不同线程在不同核心上运行，会与其他进程进行竞争。JVM内部的JIT编译的时机不同，导致运行时间不同。每次运行时缓存的内部情况不同，运行时hit数量有所差异，导致性能表现不一致。

### 2.What contributes to run-to-run variation?
每次运行测试时，系统中会有其他进程（系统日志，系统更新等），这些进程的存在会影响操作系统对任务的调度，导致不同运行之间会有不同的调度情况以及上下文切换次数，这些额外的调度与上下文切换会占用运行时间，进而影响性能表现。同时在多核CPU上，被分配到同一个核上的不同线程会竞争缓存资源，发生原本属于工作负载的一些缓存内容被替换，导致运行时发生的cache miss情况增多，影响性能表现。CPU根据系统负载调整处理器频率的动态频率调整策略会导致不同运行之间CPU的频率不完全一致，工作负载运行速度不一致，产生性能表现不同的情况。

### 3.How do we validate the factors contributing to run-to-run variation?
采用控制变量法，每次只固定一个影响因素。例如使用 `taskset `绑定固定CPU核心运行测试,将其与对照组的数据做统计假设检验，验证该因素是否对运行的性能表现有显著性影响

### 4.What are the pros and cons of using arithmetic mean versus geometric mean in summarizing scores?
算数平均数是所有样本的得分之和除以样本数，它的计算方式简单，容易理解。但不同场景下的分数差异可能会较大，算数平均数会受到极端值的较大影响，导致最终平均值和极端值相近，不能反映较小值的特性，不适用跨越多个数量级的数值之间计算平均数。
几何平均数是所有得分的乘积开n次方,在这种计算方式下，各个得分的权重相等，避免了高分测试项占据主导地位，更能反映多个子基准的相对性能变化趋势。缺点是对负数值不适用，反映的是相对水平，计算方式复杂。

### 5.Why does SPECjvm2008 use geometric mean? (In fact, it uses hierarchical geometric mean)
在不同的子基准测试中得分差异往往较大，差距有时在多个数量级上。若使用算数平均数，会导致得分基本由高分子基准主导，导致整体性能被误判。且由于在SPECjvm2008中每个种类的工作负载数量不同，为避免同一种类的工作负载在最终的得分中占据过大权重，平等地反映各个应用领域的表现，所以先对每个种类的工作负载求出组内几何平均值作为结果，再将各个组的结果求出几何平均值作为最终得分，也就是分层几何平均。