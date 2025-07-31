"""
添加系统配置表

Revision ID: add_system_config_table
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""

# 创建系统配置表的SQL
CREATE_SYSTEM_CONFIG_TABLE = """
CREATE TABLE IF NOT EXISTS system_configs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT,
    config_type VARCHAR(20) NOT NULL DEFAULT 'string',
    description VARCHAR(255),
    is_encrypted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_system_configs_key ON system_configs(config_key);
CREATE INDEX IF NOT EXISTS idx_system_configs_type ON system_configs(config_type);

-- 插入默认配置
INSERT OR IGNORE INTO system_configs (config_key, config_value, config_type, description, is_encrypted) VALUES
('default_password', '123456', 'string', '新用户默认密码', TRUE),
('password_reset_enabled', 'true', 'bool', '是否启用密码重置功能', FALSE),
('max_login_attempts', '5', 'int', '最大登录尝试次数', FALSE);
"""

if __name__ == "__main__":
    import sqlite3
    import os
    
    # 获取数据库路径
    db_path = os.path.join(os.path.dirname(__file__), "..", "database.db")
    
    try:
        # 连接数据库并执行SQL
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 执行创建表的SQL
        cursor.executescript(CREATE_SYSTEM_CONFIG_TABLE)
        
        conn.commit()
        print("✅ 系统配置表创建成功")
        
        # 验证表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='system_configs';")
        result = cursor.fetchone()
        if result:
            print("✅ 系统配置表验证成功")
            
            # 查看插入的默认数据
            cursor.execute("SELECT config_key, description FROM system_configs;")
            configs = cursor.fetchall()
            print("📋 默认配置:")
            for config in configs:
                print(f"  - {config[0]}: {config[1]}")
        else:
            print("❌ 系统配置表验证失败")
            
    except Exception as e:
        print(f"❌ 创建系统配置表失败: {e}")
    finally:
        if 'conn' in locals():
            conn.close()