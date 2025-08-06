-- 删除bills表中的merchant_name和order_id字段
-- 注意：这些字段的信息仍然保留在raw_data中

-- 删除merchant_name字段
ALTER TABLE bills DROP COLUMN IF EXISTS merchant_name;

-- 删除order_id字段
ALTER TABLE bills DROP COLUMN IF EXISTS order_id;

-- 添加注释说明
COMMENT ON TABLE bills IS '账单表 - 已移除merchant_name和order_id字段，相关信息保留在raw_data中';