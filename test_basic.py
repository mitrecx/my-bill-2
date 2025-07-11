import os
import sys
import csv
import re
from datetime import datetime

# 简单的数据库连接测试
def test_database_connection():
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            database='bills_db',
            user='josie',
            password='bills123456'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version();')
        version = cursor.fetchone()
        print(f'✓ 数据库连接成功: {version[0]}')
        
        # 测试表是否存在
        cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        print(f'✓ 数据库表: {[t[0] for t in tables]}')
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f'✗ 数据库连接失败: {e}')
        return False

# 简单的CSV解析测试
def test_csv_parsing():
    print('\n测试CSV文件解析...')
    csv_files = []
    
    # 查找CSV文件
    bills_dir = '../bills'
    if os.path.exists(bills_dir):
        for file in os.listdir(bills_dir):
            if file.endswith('.csv'):
                csv_files.append(os.path.join(bills_dir, file))
    
    if not csv_files:
        print('✗ 未找到CSV文件')
        return False
    
    for csv_file in csv_files:
        print(f'\n解析文件: {csv_file}')
        try:
            # 尝试不同编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']
            parsed = False
            
            for encoding in encodings:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        # 读取前几行查看格式
                        lines = []
                        for i, line in enumerate(f):
                            lines.append(line.strip())
                            if i >= 5:  # 只读前6行
                                break
                        
                        print(f'  编码: {encoding}')
                        print(f'  总行数估计: ~{len(lines)}+ 行')
                        print('  前几行内容:')
                        for j, line in enumerate(lines[:3]):
                            print(f'    {j+1}: {line[:100]}...' if len(line) > 100 else f'    {j+1}: {line}')
                        
                        # 检测文件类型
                        header = lines[0] if lines else ''
                        if '记录时间' in header or '交易时间' in header:
                            if '记录时间' in header:
                                print('  → 检测为支付宝账单格式')
                            else:
                                print('  → 检测为京东账单格式')
                        else:
                            print('  → 未知格式，尝试通用解析')
                        
                        parsed = True
                        break
                        
                except UnicodeDecodeError:
                    continue
            
            if not parsed:
                print(f'  ✗ 无法解析文件编码')
            else:
                print(f'  ✓ 文件解析成功')
                
        except Exception as e:
            print(f'  ✗ 解析失败: {e}')
    
    return True

# 简单的数据插入测试
def test_data_insertion():
    print('\n测试数据插入...')
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            database='bills_db',
            user='josie',
            password='bills123456'
        )
        cursor = conn.cursor()
        
        # 创建测试用户和家庭
        cursor.execute("""
        INSERT INTO users (username, email, hashed_password, full_name) 
        VALUES ('test_user', 'test@example.com', 'hashed_password_123', '测试用户')
        ON CONFLICT (email) DO NOTHING
        RETURNING id;
        """)
        
        result = cursor.fetchone()
        if result:
            user_id = result[0]
            print(f'✓ 创建测试用户 ID: {user_id}')
        else:
            # 用户已存在，获取ID
            cursor.execute("SELECT id FROM users WHERE email = 'test@example.com'")
            user_id = cursor.fetchone()[0]
            print(f'✓ 使用现有测试用户 ID: {user_id}')
        
        # 创建测试家庭
        cursor.execute("""
        INSERT INTO families (name, description) 
        VALUES ('测试家庭', '用于测试的家庭')
        ON CONFLICT (name) DO NOTHING
        RETURNING id;
        """)
        
        result = cursor.fetchone()
        if result:
            family_id = result[0]
        else:
            cursor.execute("SELECT id FROM families WHERE name = '测试家庭'")
            family_id = cursor.fetchone()[0]
        
        print(f'✓ 使用家庭 ID: {family_id}')
        
        # 创建家庭成员关系
        cursor.execute("""
        INSERT INTO family_members (family_id, user_id, role)
        VALUES (%s, %s, 'admin')
        ON CONFLICT (family_id, user_id) DO NOTHING;
        """, (family_id, user_id))
        
        # 插入测试账单
        cursor.execute("""
        INSERT INTO bills (
            user_id, family_id, amount, transaction_time, transaction_type,
            merchant_name, description, source_type
        ) VALUES (
            %s, %s, 100.50, %s, '支出', '测试商户', '测试账单', 'test'
        ) RETURNING id;
        """, (user_id, family_id, datetime.now()))
        
        bill_id = cursor.fetchone()[0]
        print(f'✓ 创建测试账单 ID: {bill_id}')
        
        # 查询验证
        cursor.execute("""
        SELECT b.id, b.amount, b.merchant_name, u.username, f.name
        FROM bills b
        JOIN users u ON b.user_id = u.id
        JOIN families f ON b.family_id = f.id
        WHERE b.id = %s;
        """, (bill_id,))
        
        result = cursor.fetchone()
        if result:
            print(f'✓ 账单查询成功: ID={result[0]}, 金额={result[1]}, 商户={result[2]}, 用户={result[3]}, 家庭={result[4]}')
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f'✗ 数据插入测试失败: {e}')
        return False

if __name__ == '__main__':
    print('=== 账单管理系统基础功能测试 ===\n')
    
    # 检查psycopg2
    try:
        import psycopg2
        print('✓ psycopg2 已安装')
    except ImportError:
        print('✗ psycopg2 未安装，尝试安装...')
        os.system('pip3 install psycopg2-binary --user')
        try:
            import psycopg2
            print('✓ psycopg2 安装成功')
        except ImportError:
            print('✗ psycopg2 安装失败，请手动安装')
            sys.exit(1)
    
    success = True
    
    # 测试数据库连接
    if not test_database_connection():
        success = False
    
    # 测试CSV解析
    if not test_csv_parsing():
        success = False
    
    # 测试数据插入
    if not test_data_insertion():
        success = False
    
    print(f'\n=== 测试完成 ===')
    if success:
        print('✓ 所有测试通过！')
    else:
        print('✗ 部分测试失败') 