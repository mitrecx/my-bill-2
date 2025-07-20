-- 消息系统数据库迁移脚本
-- 创建消息表
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id INTEGER REFERENCES users(id),
    receiver_id INTEGER NOT NULL REFERENCES users(id),
    message_type VARCHAR(50) NOT NULL, -- 'system', 'family_invitation', 'notification'
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    data JSONB, -- 存储额外数据，如邀请相关信息
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建消息操作表（用于记录用户对消息的操作）
CREATE TABLE IF NOT EXISTS message_actions (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES messages(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    action_type VARCHAR(50) NOT NULL, -- 'accept', 'reject', 'read'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 添加索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
CREATE INDEX IF NOT EXISTS idx_messages_is_read ON messages(is_read);
CREATE INDEX IF NOT EXISTS idx_message_actions_message_id ON message_actions(message_id);
CREATE INDEX IF NOT EXISTS idx_message_actions_user_id ON message_actions(user_id);

-- 确保用户只能属于一个家庭的约束
-- 首先检查是否已存在该约束
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'unique_user_family' 
        AND table_name = 'family_members'
    ) THEN
        -- 删除重复的family_members记录，只保留最新的
        DELETE FROM family_members 
        WHERE id NOT IN (
            SELECT DISTINCT ON (user_id) id 
            FROM family_members 
            ORDER BY user_id, joined_at DESC
        );
        
        -- 添加唯一约束
        ALTER TABLE family_members ADD CONSTRAINT unique_user_family UNIQUE (user_id);
    END IF;
END $$;