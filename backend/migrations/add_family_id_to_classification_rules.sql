-- 分类规则从用户级改为家庭级共享
ALTER TABLE classification_rules
    ADD COLUMN IF NOT EXISTS family_id INTEGER REFERENCES families(id);

UPDATE classification_rules cr
SET family_id = fm.family_id
FROM family_members fm
WHERE cr.family_id IS NULL
  AND fm.user_id = cr.created_by;

-- 同一家庭内合并重复规则（保留 id 较大/较新的记录）
DELETE FROM classification_rules a
USING classification_rules b
WHERE a.family_id IS NOT NULL
  AND b.family_id IS NOT NULL
  AND a.family_id = b.family_id
  AND a.rule_text = b.rule_text
  AND a.source_type = b.source_type
  AND a.transaction_type = b.transaction_type
  AND a.id < b.id;

DELETE FROM classification_rules WHERE family_id IS NULL;

ALTER TABLE classification_rules
    ALTER COLUMN family_id SET NOT NULL;

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS uq_classification_rules_user_rule_source_type;

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS uq_classification_rules_user_rule_source;

ALTER TABLE classification_rules
    DROP CONSTRAINT IF EXISTS unique_rule_per_user;

ALTER TABLE classification_rules
    ADD CONSTRAINT uq_classification_rules_family_rule_source_type
    UNIQUE (family_id, rule_text, source_type, transaction_type);

CREATE INDEX IF NOT EXISTS idx_classification_rules_family_id
    ON classification_rules (family_id);
