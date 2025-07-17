-- 添加source_filename字段到bills表
-- 执行时间: 2025-07-17

ALTER TABLE bills ADD COLUMN source_filename VARCHAR;

-- 添加注释
COMMENT ON COLUMN bills.source_filename IS '记录来源文件名';

-- 为现有记录设置默认值（可选）
-- UPDATE bills SET source_filename = 'unknown' WHERE source_filename IS NULL;