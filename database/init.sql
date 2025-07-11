-- 多用户家庭账单管理系统数据库初始化脚本
-- 创建时间: 2025-01-11

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 家庭表
CREATE TABLE families (
    id SERIAL PRIMARY KEY,
    family_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 家庭成员关系表
CREATE TABLE family_members (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member', -- 'admin', 'member', 'viewer'
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(family_id, user_id)
);

-- 账单分类表
CREATE TABLE bill_categories (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    category_name VARCHAR(100) NOT NULL,
    parent_id INTEGER REFERENCES bill_categories(id),
    color VARCHAR(7), -- 颜色代码
    icon VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(family_id, category_name)
);

-- 账单记录表（核心表，支持多用户）
CREATE TABLE bills (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id), -- 谁上传的这条记录
    source_type VARCHAR(20) NOT NULL, -- 'alipay', 'jd', 'cmb'
    original_filename VARCHAR(255), -- 原始文件名
    
    -- 标准化字段
    transaction_time TIMESTAMP NOT NULL,
    merchant_name VARCHAR(255),
    transaction_desc TEXT,
    amount DECIMAL(12,2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    transaction_type VARCHAR(50), -- '收入', '支出', '不计收支'
    payment_method VARCHAR(100),
    category_id INTEGER REFERENCES bill_categories(id),
    
    -- 源数据字段（JSON格式存储原始数据）
    raw_data JSONB,
    
    -- 元数据
    balance DECIMAL(12,2), -- 余额（银行账单特有）
    order_id VARCHAR(100),
    counter_party VARCHAR(255), -- 交易对手
    remark TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 文件上传记录表
CREATE TABLE upload_records (
    id SERIAL PRIMARY KEY,
    family_id INTEGER REFERENCES families(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id),
    filename VARCHAR(255) NOT NULL,
    file_size INTEGER,
    source_type VARCHAR(20),
    total_records INTEGER, -- 解析出的记录总数
    success_records INTEGER, -- 成功导入的记录数
    failed_records INTEGER, -- 失败的记录数
    status VARCHAR(20) DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引优化查询性能
CREATE INDEX idx_bills_family_user ON bills(family_id, user_id);
CREATE INDEX idx_bills_transaction_time ON bills(transaction_time);
CREATE INDEX idx_bills_source_type ON bills(source_type);
CREATE INDEX idx_bills_amount ON bills(amount);
CREATE INDEX idx_bills_category ON bills(category_id);
CREATE INDEX idx_family_members_family_user ON family_members(family_id, user_id);
CREATE INDEX idx_upload_records_family_user ON upload_records(family_id, user_id);

-- 插入默认的账单分类
INSERT INTO bill_categories (family_id, category_name, color, icon) VALUES 
(NULL, '食品酒饮', '#FF6B6B', 'food'),
(NULL, '服饰内衣', '#4ECDC4', 'clothing'),
(NULL, '日用百货', '#45B7D1', 'daily'),
(NULL, '数码电器', '#96CEB4', 'digital'),
(NULL, '交通出行', '#FFEAA7', 'transport'),
(NULL, '医疗保健', '#DDA0DD', 'medical'),
(NULL, '教育培训', '#98D8C8', 'education'),
(NULL, '运动户外', '#F7DC6F', 'sports'),
(NULL, '住房物业', '#BB8FCE', 'housing'),
(NULL, '投资理财', '#85C1E9', 'investment'),
(NULL, '转账红包', '#F8C471', 'transfer'),
(NULL, '其他', '#D5DBDB', 'other');

-- 创建更新时间触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要的表添加更新时间触发器
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_families_updated_at BEFORE UPDATE ON families
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at BEFORE UPDATE ON bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 添加一些约束检查
ALTER TABLE bills ADD CONSTRAINT check_amount_not_zero CHECK (amount != 0);
ALTER TABLE bills ADD CONSTRAINT check_source_type CHECK (source_type IN ('alipay', 'jd', 'cmb'));
ALTER TABLE family_members ADD CONSTRAINT check_role CHECK (role IN ('admin', 'member', 'viewer'));
ALTER TABLE upload_records ADD CONSTRAINT check_status CHECK (status IN ('processing', 'completed', 'failed'));

-- 添加注释
COMMENT ON TABLE users IS '用户表，存储系统用户信息';
COMMENT ON TABLE families IS '家庭表，一个家庭可以有多个成员';
COMMENT ON TABLE family_members IS '家庭成员关系表，定义用户与家庭的关联关系';
COMMENT ON TABLE bill_categories IS '账单分类表，支持分层分类';
COMMENT ON TABLE bills IS '账单记录表，存储所有账单交易记录';
COMMENT ON TABLE upload_records IS '文件上传记录表，跟踪文件上传和解析状态'; 