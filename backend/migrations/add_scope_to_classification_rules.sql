-- 分类规则支持 personal（个人）与 family（家庭）两种作用域
ALTER TABLE classification_rules
    ADD COLUMN IF NOT EXISTS scope VARCHAR(20) NOT NULL DEFAULT 'family';

UPDATE classification_rules
SET scope = 'family'
WHERE family_id IS NOT NULL;

ALTER TABLE classification_rules
    ALTER COLUMN family_id DROP NOT NULL;

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS uq_classification_rules_family_rule_source_type;

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS check_classification_rule_scope;

ALTER TABLE classification_rules
    ADD CONSTRAINT check_classification_rule_scope
    CHECK (scope IN ('personal', 'family'));

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS check_classification_rule_scope_family_id;

ALTER TABLE classification_rules
    ADD CONSTRAINT check_classification_rule_scope_family_id
    CHECK (
        (scope = 'personal' AND family_id IS NULL)
        OR (scope = 'family' AND family_id IS NOT NULL)
    );

DROP INDEX IF EXISTS uq_classification_rules_personal;
CREATE UNIQUE INDEX uq_classification_rules_personal
    ON classification_rules (created_by, rule_text, source_type, transaction_type)
    WHERE scope = 'personal';

DROP INDEX IF EXISTS uq_classification_rules_family;
CREATE UNIQUE INDEX uq_classification_rules_family
    ON classification_rules (family_id, rule_text, source_type, transaction_type)
    WHERE scope = 'family';
