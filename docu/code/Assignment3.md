# Assignment3
本项目用于对Java程序进行性能分析，生成火焰图和结构化数据库，帮助识别性能瓶颈和热点函数。

## 相关依赖
需要在Assignment3文件夹下安装`perf-map-agent`和`FlameGraph`工具，详见github

## 工具组成

### 1. `generate.sh` - 主要的火焰图生成脚本
- 启动Java程序并进行性能采样
- 生成火焰图（SVG格式）
- 导出性能数据到SQLite数据库

### 2. `export_to_database.py` - 数据库导出脚本
- 解析perf script输出
- 将性能数据导入SQLite数据库
- 记录元数据和调用栈信息

### 3. `analyze_database.py` - 数据库分析脚本
- 分析数据库中的性能数据
- 识别热点函数和Java方法
- 生成进程信息统计

## 使用方法

### 基本用法

```bash
# 分析自定义Java程序（60秒采样）
./generate.sh TestFibonacci # TestFibonacci.class

# 指定采样时间
./generate.sh -t 30 TestFibonacci

# 运行SPECjvm2008基准测试
./generate.sh -s compress
./generate.sh -s derby
```

### 数据库分析

```bash
# 分析生成的数据库
python3 analyze_database.py flamegraph_work/程序名_时间戳/performance_data.sqlite
```

## 输出文件

### 火焰图
- **位置**: `flamegraph_work/程序名_时间戳/flamegraph.svg`
- **用途**: 可视化性能热点，函数调用关系和CPU使用情况

### 数据库
- **位置**: `flamegraph_work/程序名_时间戳/performance_data.sqlite`
- **表结构**:
  - `perf_samples`: 性能样本数据
  - `call_stacks`: 调用栈信息
  - `metadata`: 元数据信息

## 数据库结构详解

### 1. `perf_samples` 表 - 性能样本数据
存储每个性能采样点的基本信息。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INTEGER | 主键，自增 |
| `timestamp` | REAL | 采样时间戳（秒） |
| `pid` | INTEGER | 进程ID |
| `tid` | INTEGER | 线程ID |
| `comm` | TEXT | 进程/线程名称 |
| `raw_line` | TEXT | 原始perf输出行 |

**示例数据**:
```sql
SELECT * FROM perf_samples LIMIT 3;
-- 结果：
-- id | timestamp   | pid   | tid   | comm | raw_line
-- 1  | 18515.71055 | 38693 | 38695 | java | java   38693/38695   18515.710550:
```

### 2. `call_stacks` 表 - 调用栈信息
存储每个样本的函数调用栈详细信息。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `id` | INTEGER | 主键，自增 |
| `sample_id` | INTEGER | 关联的样本ID（外键） |
| `level` | INTEGER | 调用栈层级（0为最深层） |
| `ip` | TEXT | 指令指针地址 |
| `symbol` | TEXT | 函数/方法名 |
| `dso` | TEXT | 动态共享对象（库文件路径） |

**示例数据**:
```sql
SELECT * FROM call_stacks WHERE sample_id = 1 ORDER BY level;
-- 结果：
-- sample_id | level | ip           | symbol                    | dso
-- 1         | 0     | 7a21092cb793 | LTestFibonacci;::fibonacci| /tmp/perf-38693.map
-- 1         | 1     | ffffffff8aec | schedule                  | /proc/kcore
```

### 3. `metadata` 表 - 元数据信息
存储性能分析的配置和统计信息。

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `key` | TEXT | 元数据键名（主键） |
| `value` | TEXT | 元数据值 |

**标准元数据项**:
- `program_name`: 程序名称
- `record_seconds`: 采样时长
- `import_time`: 数据导入时间
- `perf_script_file`: 原始perf文件路径
- `sample_count`: 样本总数
- `stack_count`: 调用栈记录总数