-- 添加is_admin字段到users表
ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;

-- 将test用户设置为管理员（用于测试）
UPDATE users SET is_admin = TRUE WHERE username = 'test';

-- 提交更改
COMMIT;