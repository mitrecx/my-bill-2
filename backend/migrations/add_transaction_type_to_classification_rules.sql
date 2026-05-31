-- 为分类规则增加交易类型（支出/收入/不计收支）
ALTER TABLE classification_rules
    ADD COLUMN IF NOT EXISTS transaction_type VARCHAR(20) NOT NULL DEFAULT 'all';

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS check_classification_rule_transaction_type;

ALTER TABLE classification_rules
    ADD CONSTRAINT check_classification_rule_transaction_type
    CHECK (transaction_type IN ('expense', 'income', 'transfer', 'all'));

-- 扩展唯一约束：同一用户下 rule_text + source_type + transaction_type 不可重复
ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS uq_classification_rules_user_rule_source;

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS unique_rule_per_user;

ALTER TABLE classification_rules
    ADD CONSTRAINT uq_classification_rules_user_rule_source_type
    UNIQUE (created_by, rule_text, source_type, transaction_type);
