-- 添加order_id字段到bills表
-- 执行时间: 2025-01-27

ALTER TABLE bills ADD COLUMN order_id VARCHAR;

-- 添加注释
COMMENT ON COLUMN bills.order_id IS '订单ID字段，用于存储来源系统的订单标识';

-- 为现有记录设置默认值（可选）
-- UPDATE bills SET order_id = NULL WHERE order_id IS NULL;