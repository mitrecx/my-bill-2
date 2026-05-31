-- 分类规则交易类型仅保留 expense/income/transfer，移除 all
UPDATE classification_rules
SET transaction_type = 'expense'
WHERE transaction_type = 'all';

ALTER TABLE classification_rules
    ALTER COLUMN transaction_type SET DEFAULT 'expense';

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS check_classification_rule_transaction_type;

ALTER TABLE classification_rules
    ADD CONSTRAINT check_classification_rule_transaction_type
    CHECK (transaction_type IN ('expense', 'income', 'transfer'));
