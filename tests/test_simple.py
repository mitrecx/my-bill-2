import os
import subprocess
import csv
from datetime import datetime

def test_database_connection():
    print('测试数据库连接...')
    try:
        # 使用psql命令测试连接
        result = subprocess.run([
            '/usr/bin/psql', '-h', 'localhost', '-U', 'josie', '-d', 'bills_db', 
            '-c', 'SELECT version();'
        ], env={'PGPASSWORD': 'bills123456'}, 
        capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print('✓ 数据库连接成功')
            print(f'  版本信息: {result.stdout.strip().split(chr(10))[2].strip()}')
            return True
        else:
            print(f'✗ 数据库连接失败: {result.stderr}')
            return False
    except Exception as e:
        print(f'✗ 数据库连接测试异常: {e}')
        return False

def test_tables():
    print('\n测试数据库表结构...')
    try:
        result = subprocess.run([
            '/usr/bin/psql', '-h', 'localhost', '-U', 'josie', '-d', 'bills_db', 
            '-c', "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
        ], env={'PGPASSWORD': 'bills123456'}, 
        capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            tables = []
            lines = result.stdout.strip().split('\n')
            for line in lines[2:-2]:  # 跳过表头和表尾
                table_name = line.strip()
                if table_name and table_name != '':
                    tables.append(table_name)
            
            print(f'✓ 数据库表: {tables}')
            return len(tables) > 0
        else:
            print(f'✗ 查询表结构失败: {result.stderr}')
            return False
    except Exception as e:
        print(f'✗ 表结构测试异常: {e}')
        return False

def test_csv_files():
    print('\n测试CSV文件解析...')
    bills_dir = '../bills'
    
    if not os.path.exists(bills_dir):
        print(f'✗ 账单目录不存在: {bills_dir}')
        return False
    
    files = os.listdir(bills_dir)
    csv_files = [f for f in files if f.endswith('.csv')]
    
    if not csv_files:
        print('✗ 未找到CSV文件')
        return False
    
    print(f'找到CSV文件: {csv_files}')
    
    for csv_file in csv_files:
        file_path = os.path.join(bills_dir, csv_file)
        print(f'\n解析文件: {csv_file}')
        
        # 尝试不同编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
        success = False
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 读取前几行
                    lines = []
                    for i in range(min(5, sum(1 for _ in f))):
                        f.seek(0)
                        for j, line in enumerate(f):
                            if j == i:
                                lines.append(line.strip())
                                break
                    
                    print(f'  编码: {encoding} ✓')
                    print(f'  前3行:')
                    for i, line in enumerate(lines[:3]):
                        display_line = line[:80] + '...' if len(line) > 80 else line
                        print(f'    {i+1}: {display_line}')
                    
                    # 检测文件类型
                    header = lines[0] if lines else ''
                    if '记录时间' in header:
                        print('  → 支付宝账单格式')
                    elif '交易时间' in header:
                        print('  → 京东账单格式')
                    else:
                        print('  → 未知格式')
                    
                    success = True
                    break
                    
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f'  编码 {encoding} 失败: {e}')
                continue
        
        if success:
            print(f'  ✓ 文件解析成功')
        else:
            print(f'  ✗ 文件解析失败')
    
    return True

def test_data_insertion():
    print('\n测试数据插入...')
    try:
        # 创建测试用户
        sql_commands = [
            "INSERT INTO users (username, email, password_hash, full_name) VALUES ('test_user', 'test@example.com', 'hashed_password_123', '测试用户') ON CONFLICT (email) DO UPDATE SET username = EXCLUDED.username RETURNING id;",
            "INSERT INTO families (family_name, description) VALUES ('测试家庭', '用于测试的家庭') RETURNING id;"
        ]
        
        for sql in sql_commands:
            result = subprocess.run([
                '/usr/bin/psql', '-h', 'localhost', '-U', 'josie', '-d', 'bills_db', 
                '-c', sql
            ], env={'PGPASSWORD': 'bills123456'}, 
            capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                print(f'✗ SQL执行失败: {result.stderr}')
                return False
        
        print('✓ 测试数据插入成功')
        
        # 查询测试数据
        result = subprocess.run([
            '/usr/bin/psql', '-h', 'localhost', '-U', 'josie', '-d', 'bills_db', 
            '-c', "SELECT u.username, f.family_name FROM users u, families f WHERE u.email = 'test@example.com' AND f.family_name = '测试家庭' LIMIT 1;"
        ], env={'PGPASSWORD': 'bills123456'}, 
        capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print('✓ 数据查询验证成功')
            print(f'  查询结果: {result.stdout.strip()}')
            return True
        else:
            print(f'✗ 数据查询失败: {result.stderr}')
            return False
            
    except Exception as e:
        print(f'✗ 数据插入测试异常: {e}')
        return False

if __name__ == '__main__':
    print('=== 账单管理系统基础功能测试 (简化版) ===\n')
    
    success = True
    
    # 测试数据库连接
    if not test_database_connection():
        success = False
    
    # 测试表结构
    if not test_tables():
        success = False
    
    # 测试CSV文件
    if not test_csv_files():
        success = False
    
    # 测试数据插入
    if not test_data_insertion():
        success = False
    
    print(f'\n=== 测试完成 ===')
    if success:
        print('✓ 所有测试通过！')
        print('\n后端基础功能验证成功，可以开始前端开发了！')
    else:
        print('✗ 部分测试失败，需要检查配置') 