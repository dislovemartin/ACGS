-- Enhance principles table with Phase 1 constitutional fields

-- First, rename title to name if it exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'principles' AND column_name = 'title') THEN
        -- Drop the existing index on title
        DROP INDEX IF EXISTS ix_principles_title;
        -- Rename title column to name
        ALTER TABLE principles RENAME COLUMN title TO name;
        -- Create new index on name with unique constraint
        CREATE UNIQUE INDEX ix_principles_name ON principles(name);
    END IF;
END $$;

-- Add enhanced constitutional principle fields
ALTER TABLE principles ADD COLUMN IF NOT EXISTS priority_weight FLOAT;
ALTER TABLE principles ADD COLUMN IF NOT EXISTS scope JSONB;
ALTER TABLE principles ADD COLUMN IF NOT EXISTS normative_statement TEXT;
ALTER TABLE principles ADD COLUMN IF NOT EXISTS constraints JSONB;
ALTER TABLE principles ADD COLUMN IF NOT EXISTS rationale TEXT;
ALTER TABLE principles ADD COLUMN IF NOT EXISTS keywords JSONB;
ALTER TABLE principles ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE principles ADD COLUMN IF NOT EXISTS validation_criteria_nl TEXT;
ALTER TABLE principles ADD COLUMN IF NOT EXISTS constitutional_metadata JSONB;

-- Create indexes for enhanced searchability
CREATE INDEX IF NOT EXISTS ix_principles_priority_weight ON principles(priority_weight);
CREATE INDEX IF NOT EXISTS ix_principles_category ON principles(category);

-- Add comments to columns
COMMENT ON COLUMN principles.priority_weight IS 'Priority weight for principle prioritization (0.0 to 1.0)';
COMMENT ON COLUMN principles.scope IS 'JSON array defining contexts where principle applies';
COMMENT ON COLUMN principles.normative_statement IS 'Structured normative statement for constitutional interpretation';
COMMENT ON COLUMN principles.constraints IS 'JSON object defining formal constraints and requirements';
COMMENT ON COLUMN principles.rationale IS 'Detailed rationale and justification for the principle';
COMMENT ON COLUMN principles.keywords IS 'JSON array of keywords for principle categorization';
COMMENT ON COLUMN principles.category IS 'Category classification (e.g., Safety, Privacy, Fairness)';
COMMENT ON COLUMN principles.validation_criteria_nl IS 'Natural language validation criteria for testing';
COMMENT ON COLUMN principles.constitutional_metadata IS 'Metadata for constitutional compliance tracking';
