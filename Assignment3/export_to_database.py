#!/usr/bin/env python3
"""
性能数据导出到 SQLite 数据库
将 perf script 输出的原始数据转换为结构化的 SQLite 数据库
"""

import sys
import sqlite3
import re
import argparse
from pathlib import Path
import json
from datetime import datetime

def create_database_schema(cursor):
    """创建数据库表结构"""
    
    # 主要的性能样本表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perf_samples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL NOT NULL,
            pid INTEGER NOT NULL,
            tid INTEGER NOT NULL,
            comm TEXT NOT NULL,
            raw_line TEXT
        )
    ''')
    
    # 调用栈表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS call_stacks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_id INTEGER NOT NULL,
            level INTEGER NOT NULL,
            ip TEXT NOT NULL,
            symbol TEXT NOT NULL,
            dso TEXT,
            FOREIGN KEY (sample_id) REFERENCES perf_samples (id)
        )
    ''')
    
    # 元数据表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # 创建基本索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_samples_timestamp ON perf_samples(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_samples_pid ON perf_samples(pid)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stacks_sample_id ON call_stacks(sample_id)')

def parse_perf_script_line(line):
    """解析 perf script 输出的一行"""
    original_line = line
    line = line.strip()
    if not line or line.startswith('#'):
        return None, None
    
    # 检查是否是调用栈行（以空格或制表符开头）
    if original_line.startswith((' ', '\t')):
        # 调用栈行格式: "地址 符号 (dso)"
        # 例如: "    7a21092cb793 LTestFibonacci;::fibonacci (/tmp/perf-38693.map)"
        stack_match = re.match(r'([0-9a-fA-F]+)\s+(.+)', line)
        if stack_match:
            ip = stack_match.group(1)
            rest = stack_match.group(2)
            
            # 解析符号和 DSO
            symbol = rest
            dso = ""
            if '(' in rest and ')' in rest:
                parts = rest.rsplit('(', 1)
                if len(parts) == 2:
                    symbol = parts[0].strip()
                    dso = parts[1].rstrip(')').strip()
            
            return 'stack', {'ip': ip, 'symbol': symbol, 'dso': dso}
    else:
        # 主样本行格式: "comm pid/tid timestamp:"
        # 例如: "java   38693/38695   18515.710550:"
        sample_match = re.match(r'(.+?)\s+(\d+)/(\d+)\s+([0-9.]+):\s*(.*)$', line)
        if sample_match:
            comm = sample_match.group(1).strip()
            pid = int(sample_match.group(2))
            tid = int(sample_match.group(3))
            timestamp = float(sample_match.group(4))
            event_info = sample_match.group(5).strip() if sample_match.group(5) else ''
            
            return 'sample', {
                'timestamp': timestamp,
                'pid': pid,
                'tid': tid,
                'comm': comm,
                'raw_line': line
            }
    
    return None, None

def import_perf_data(perf_script_file, db_file, program_name, record_seconds):
    """导入 perf script 数据到 SQLite 数据库"""
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 创建表结构
    create_database_schema(cursor)
    
    # 插入元数据
    metadata = {
        'program_name': program_name,
        'record_seconds': str(record_seconds),
        'import_time': datetime.now().isoformat(),
        'perf_script_file': str(perf_script_file)
    }
    
    for key, value in metadata.items():
        cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', (key, value))
    
    print(f"正在导入性能数据到数据库: {db_file}")
    
    sample_count = 0
    stack_count = 0
    current_sample_id = None
    stack_level = 0
    
    try:
        with open(perf_script_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    line_type, data = parse_perf_script_line(line)
                    
                    if line_type == 'sample':
                        # 插入主样本
                        cursor.execute('''
                            INSERT INTO perf_samples 
                            (timestamp, pid, tid, comm, raw_line)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            data['timestamp'], data['pid'], data['tid'],
                            data['comm'], data['raw_line']
                        ))
                        current_sample_id = cursor.lastrowid
                        sample_count += 1
                        stack_level = 0
                        
                    elif line_type == 'stack' and current_sample_id:
                        # 插入调用栈
                        cursor.execute('''
                            INSERT INTO call_stacks 
                            (sample_id, level, ip, symbol, dso)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (
                            current_sample_id, stack_level, data['ip'],
                            data['symbol'], data['dso']
                        ))
                        stack_level += 1
                        stack_count += 1
                        
                except Exception as e:
                    print(f"警告: 解析第 {line_num} 行失败: {e}")
                    continue
    
    except FileNotFoundError:
        print(f"错误: 文件 {perf_script_file} 不存在")
        return False
    except Exception as e:
        print(f"错误: 导入数据时发生异常: {e}")
        return False
    
    # 最终提交
    conn.commit()
    
    # 更新统计信息
    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', 
                   ('sample_count', str(sample_count)))
    cursor.execute('INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)', 
                   ('stack_count', str(stack_count)))
    
    conn.commit()
    conn.close()
    
    print(f"数据库导入完成!")
    print(f"  - 样本数量: {sample_count}")
    print(f"  - 调用栈记录: {stack_count}")
    print(f"  - 数据库文件: {db_file}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='将 perf script 数据导出到 SQLite 数据库')
    parser.add_argument('perf_script_file', help='perf script 输出文件路径')
    parser.add_argument('output_dir', help='输出目录')
    parser.add_argument('--program-name', required=True, help='程序名称')
    parser.add_argument('--record-seconds', type=int, default=60, help='采集时间')
    
    args = parser.parse_args()
    
    perf_script_file = Path(args.perf_script_file)
    output_dir = Path(args.output_dir)
    
    if not perf_script_file.exists():
        print(f"错误: 文件 {perf_script_file} 不存在")
        sys.exit(1)
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成数据库文件名
    db_file = output_dir / f"performance_data.sqlite"
    
    # 导入数据
    success = import_perf_data(perf_script_file, db_file, args.program_name, args.record_seconds)
    
    if success:
        print(f"\n数据库文件: {db_file}")
        print("数据已成功导出到数据库")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
