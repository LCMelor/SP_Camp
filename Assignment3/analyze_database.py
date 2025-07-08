#!/usr/bin/env python3
"""
性能数据库分析脚本
分析SQLite数据库中的性能数据，识别热点函数和分析执行时间
"""

import sqlite3
from pathlib import Path
import sys

def analyze_hotspots(cursor):
    """分析热点函数"""
    print(f"\n=== 热点函数分析 (Top 10) ===")
    
    # 统计函数出现频率
    cursor.execute('''
        SELECT symbol, dso, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM call_stacks), 2) as percentage
        FROM call_stacks 
        WHERE symbol != '' AND symbol != '[unknown]'
        GROUP BY symbol, dso
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    results = cursor.fetchall()
    
    print(f"{'排名':<4} {'函数名':<50} {'调用次数':<8} {'占比%':<8} {'DSO'}")
    print("-" * 120)
    
    for i, (symbol, dso, count, percentage) in enumerate(results, 1):
        # 截断过长的函数名
        short_symbol = symbol[:47] + "..." if len(symbol) > 50 else symbol
        short_dso = dso[:30] + "..." if dso and len(dso) > 30 else (dso or "")
        
        print(f"{i:<4} {short_symbol:<50} {count:<8} {percentage:<8} {short_dso}")

def analyze_java_hotspots(cursor):
    """分析Java热点函数"""
    print(f"\n=== Java 热点函数分析 (Top 10) ===")
    
    cursor.execute('''
        SELECT symbol, COUNT(*) as count,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM call_stacks), 2) as percentage
        FROM call_stacks 
        WHERE symbol LIKE '%L%::%' OR symbol LIKE '%::%'
        GROUP BY symbol
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    results = cursor.fetchall()
    
    print(f"{'排名':<4} {'Java方法':<60} {'调用次数':<8} {'占比%':<8}")
    print("-" * 90)
    
    for i, (symbol, count, percentage) in enumerate(results, 1):
        # 清理Java方法名显示
        clean_symbol = symbol.replace('L', '').replace(';::', '.')
        short_symbol = clean_symbol[:57] + "..." if len(clean_symbol) > 60 else clean_symbol
        
        print(f"{i:<4} {short_symbol:<60} {count:<8} {percentage:<8}")

def analyze_process_info(cursor):
    """分析进程信息"""
    print(f"\n=== 进程信息分析 ===")
    
    cursor.execute('''
        SELECT comm, COUNT(*) as samples, 
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM perf_samples), 2) as percentage
        FROM perf_samples
        GROUP BY comm
        ORDER BY samples DESC
    ''')
    
    results = cursor.fetchall()
    
    print(f"{'进程名':<20} {'样本数':<8} {'占比%':<8}")
    print("-" * 40)
    
    for comm, samples, percentage in results:
        print(f"{comm:<20} {samples:<8} {percentage:<8}")

def get_metadata(cursor):
    """获取元数据信息"""
    cursor.execute('SELECT key, value FROM metadata')
    metadata = dict(cursor.fetchall())
    
    print("=== 数据库基本信息 ===")
    print(f"程序名称: {metadata.get('program_name', 'N/A')}")
    print(f"采集时间: {metadata.get('record_seconds', 'N/A')} 秒")
    print(f"导入时间: {metadata.get('import_time', 'N/A')}")
    print(f"样本总数: {metadata.get('sample_count', 'N/A')}")
    print(f"调用栈记录: {metadata.get('stack_count', 'N/A')}")

def main():
    if len(sys.argv) != 2:
        print("用法: python3 analyze_database.py <数据库文件>")
        sys.exit(1)
    
    db_file = Path(sys.argv[1])
    if not db_file.exists():
        print(f"错误: 数据库文件 {db_file} 不存在")
        sys.exit(1)
    
    # 连接数据库
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # 验证表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if 'perf_samples' not in tables or 'call_stacks' not in tables:
            print("错误: 数据库缺少必要的表结构")
            sys.exit(1)
        
        # 执行分析
        get_metadata(cursor)
        analyze_process_info(cursor)
        analyze_hotspots(cursor)
        analyze_java_hotspots(cursor)
        
        print(f"\n分析完成！")
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
