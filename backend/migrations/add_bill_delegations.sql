-- 账单代管授权：家庭成员可将账单增删改权限授予其他成员
CREATE TABLE IF NOT EXISTS bill_delegations (
    id SERIAL PRIMARY KEY,
    family_id INTEGER NOT NULL REFERENCES families(id) ON DELETE CASCADE,
    grantor_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    grantee_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    can_create BOOLEAN NOT NULL DEFAULT TRUE,
    can_update BOOLEAN NOT NULL DEFAULT TRUE,
    can_delete BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT bill_delegations_no_self CHECK (grantor_user_id != grantee_user_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_bill_delegations_grantor_grantee_active
    ON bill_delegations(grantor_user_id, grantee_user_id)
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_bill_delegations_grantee ON bill_delegations(grantee_user_id);
CREATE INDEX IF NOT EXISTS idx_bill_delegations_family ON bill_delegations(family_id);
