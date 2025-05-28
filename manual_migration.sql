-- Manual migration to add missing AC enhancement tables and fields

-- Add Constitutional Council fields to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS is_constitutional_council_member BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE users ADD COLUMN IF NOT EXISTS constitutional_council_appointed_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS constitutional_council_term_expires TIMESTAMP WITH TIME ZONE;

-- Create ac_meta_rules table
CREATE TABLE IF NOT EXISTS ac_meta_rules (
    id SERIAL PRIMARY KEY,
    rule_type VARCHAR(100) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_definition JSONB NOT NULL,
    threshold VARCHAR(50),
    stakeholder_roles JSONB,
    decision_mechanism VARCHAR(100),
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by_user_id INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_ac_meta_rules_id ON ac_meta_rules(id);
CREATE INDEX IF NOT EXISTS ix_ac_meta_rules_rule_type ON ac_meta_rules(rule_type);
CREATE INDEX IF NOT EXISTS ix_ac_meta_rules_name ON ac_meta_rules(name);
CREATE INDEX IF NOT EXISTS ix_ac_meta_rules_status ON ac_meta_rules(status);

-- Create ac_amendments table
CREATE TABLE IF NOT EXISTS ac_amendments (
    id SERIAL PRIMARY KEY,
    principle_id INTEGER NOT NULL REFERENCES principles(id),
    amendment_type VARCHAR(50) NOT NULL,
    proposed_changes TEXT NOT NULL,
    justification TEXT,
    proposed_content TEXT,
    proposed_status VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'proposed',
    voting_started_at TIMESTAMP WITH TIME ZONE,
    voting_ends_at TIMESTAMP WITH TIME ZONE,
    votes_for INTEGER NOT NULL DEFAULT 0,
    votes_against INTEGER NOT NULL DEFAULT 0,
    votes_abstain INTEGER NOT NULL DEFAULT 0,
    required_threshold VARCHAR(50),
    consultation_period_days INTEGER,
    public_comment_enabled BOOLEAN NOT NULL DEFAULT true,
    stakeholder_groups JSONB,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    proposed_by_user_id INTEGER NOT NULL REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_ac_amendments_id ON ac_amendments(id);
CREATE INDEX IF NOT EXISTS ix_ac_amendments_amendment_type ON ac_amendments(amendment_type);
CREATE INDEX IF NOT EXISTS ix_ac_amendments_status ON ac_amendments(status);

-- Create ac_amendment_votes table
CREATE TABLE IF NOT EXISTS ac_amendment_votes (
    id SERIAL PRIMARY KEY,
    amendment_id INTEGER NOT NULL REFERENCES ac_amendments(id),
    voter_id INTEGER NOT NULL REFERENCES users(id),
    vote VARCHAR(20) NOT NULL,
    reasoning TEXT,
    voted_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ac_amendment_votes_id ON ac_amendment_votes(id);
CREATE INDEX IF NOT EXISTS ix_ac_amendment_votes_vote ON ac_amendment_votes(vote);

-- Create ac_amendment_comments table
CREATE TABLE IF NOT EXISTS ac_amendment_comments (
    id SERIAL PRIMARY KEY,
    amendment_id INTEGER NOT NULL REFERENCES ac_amendments(id),
    commenter_id INTEGER REFERENCES users(id),
    commenter_name VARCHAR(255),
    commenter_email VARCHAR(255),
    stakeholder_group VARCHAR(100),
    comment_text TEXT NOT NULL,
    sentiment VARCHAR(20),
    is_public BOOLEAN NOT NULL DEFAULT true,
    is_moderated BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_ac_amendment_comments_id ON ac_amendment_comments(id);
CREATE INDEX IF NOT EXISTS ix_ac_amendment_comments_sentiment ON ac_amendment_comments(sentiment);

-- Create ac_conflict_resolutions table
CREATE TABLE IF NOT EXISTS ac_conflict_resolutions (
    id SERIAL PRIMARY KEY,
    conflict_type VARCHAR(100) NOT NULL,
    principle_ids JSONB NOT NULL,
    context VARCHAR(255),
    conflict_description TEXT NOT NULL,
    severity VARCHAR(20) NOT NULL,
    resolution_strategy VARCHAR(100) NOT NULL,
    resolution_details JSONB,
    precedence_order JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'identified',
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    identified_by_user_id INTEGER REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_ac_conflict_resolutions_id ON ac_conflict_resolutions(id);
CREATE INDEX IF NOT EXISTS ix_ac_conflict_resolutions_conflict_type ON ac_conflict_resolutions(conflict_type);
CREATE INDEX IF NOT EXISTS ix_ac_conflict_resolutions_severity ON ac_conflict_resolutions(severity);
CREATE INDEX IF NOT EXISTS ix_ac_conflict_resolutions_status ON ac_conflict_resolutions(status);

-- Update alembic version to reflect the applied migrations
UPDATE alembic_version SET version_num = 'h3c4d5e6f7g8';
