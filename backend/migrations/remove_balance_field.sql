-- 删除bills表中的balance字段
-- 执行时间: 2025-01-27

-- 删除balance字段
ALTER TABLE bills DROP COLUMN IF EXISTS balance;

-- 添加注释说明
-- 该字段已被移除，因为余额信息不再需要存储在账单记录中