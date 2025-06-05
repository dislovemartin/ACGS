#!/usr/bin/env python3

"""
ACGS Staging Database Setup Script
Creates the necessary database tables for staging environment
"""

import psycopg2
import sys

def create_staging_database():
    """Create the staging database tables"""
    
    print("Setting up ACGS staging database...")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host="localhost",
            port=5435,
            database="acgs_staging",
            user="acgs_user",
            password="acgs_staging_password_2024_phase3_secure"
        )
        
        cursor = conn.cursor()
        
        # Drop existing tables if they exist to avoid conflicts
        drop_tables_sql = """
        DROP TABLE IF EXISTS ac_amendments CASCADE;
        DROP TABLE IF EXISTS ac_amendment_votes CASCADE;
        DROP TABLE IF EXISTS ac_amendment_comments CASCADE;
        DROP TABLE IF EXISTS policy_rules CASCADE;
        DROP TABLE IF EXISTS policies CASCADE;
        DROP TABLE IF EXISTS refresh_tokens CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        DROP TABLE IF EXISTS principles CASCADE;
        DROP TABLE IF EXISTS constitutional_principles CASCADE;
        DROP TABLE IF EXISTS governance_synthesis_runs CASCADE;
        DROP TABLE IF EXISTS formal_verification_runs CASCADE;
        DROP TABLE IF EXISTS alembic_version CASCADE;
        DROP TABLE IF EXISTS policy_decisions CASCADE;
        """

        cursor.execute(drop_tables_sql)
        conn.commit()
        print("✅ Dropped existing tables")

        # Create basic tables that are needed
        create_tables_sql = """
        -- Create users table
        CREATE TABLE users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            is_superuser BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create policies table
        CREATE TABLE policies (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            description TEXT,
            high_level_content TEXT,
            version INTEGER DEFAULT 1,
            status VARCHAR(50) DEFAULT 'draft',
            source_principle_ids JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by_user_id INTEGER REFERENCES users(id)
        );

        -- Create policy_rules table
        CREATE TABLE policy_rules (
            id SERIAL PRIMARY KEY,
            rule_name VARCHAR(255),
            datalog_content TEXT NOT NULL UNIQUE,
            version INTEGER NOT NULL DEFAULT 1,
            policy_id INTEGER REFERENCES policies(id),
            compilation_hash VARCHAR(64),
            last_compiled_at TIMESTAMP WITH TIME ZONE,
            compilation_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            compilation_metrics JSONB,
            source_principle_ids JSONB,
            status VARCHAR(50) NOT NULL DEFAULT 'pending_synthesis',
            verification_status VARCHAR(50) NOT NULL DEFAULT 'not_verified',
            verified_at TIMESTAMP WITH TIME ZONE,
            verification_feedback JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            synthesized_by_gs_run_id VARCHAR(100),
            verified_by_fv_run_id VARCHAR(100)
        );
        
        -- Create refresh_tokens table
        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id SERIAL PRIMARY KEY,
            token VARCHAR(500) UNIQUE NOT NULL,
            user_id INTEGER REFERENCES users(id),
            expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Create principles table (matching the Principle model)
        CREATE TABLE IF NOT EXISTS principles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            description TEXT,
            content TEXT NOT NULL,
            version INTEGER DEFAULT 1,
            status VARCHAR(50) DEFAULT 'draft',
            priority_weight FLOAT,
            scope JSONB,
            normative_statement TEXT,
            constraints JSONB,
            rationale TEXT,
            keywords JSONB,
            category VARCHAR(100),
            validation_criteria_nl TEXT,
            constitutional_metadata JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            created_by_user_id INTEGER REFERENCES users(id)
        );

        -- Create constitutional_principles table
        CREATE TABLE IF NOT EXISTS constitutional_principles (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            description TEXT,
            principle_text TEXT NOT NULL,
            category VARCHAR(100),
            priority INTEGER DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create governance_synthesis_runs table
        CREATE TABLE IF NOT EXISTS governance_synthesis_runs (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(100) UNIQUE NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'pending',
            input_principles JSONB,
            output_rules JSONB,
            synthesis_metrics JSONB,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT
        );
        
        -- Create formal_verification_runs table
        CREATE TABLE IF NOT EXISTS formal_verification_runs (
            id SERIAL PRIMARY KEY,
            run_id VARCHAR(100) UNIQUE NOT NULL,
            policy_rule_id INTEGER REFERENCES policy_rules(id),
            verification_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            verification_results JSONB,
            verification_metrics JSONB,
            started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            error_message TEXT
        );
        
        -- Create alembic_version table for migration tracking
        CREATE TABLE IF NOT EXISTS alembic_version (
            version_num VARCHAR(32) NOT NULL,
            CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
        );
        
        -- Insert a version number to indicate manual setup
        INSERT INTO alembic_version (version_num) VALUES ('staging_manual_setup') 
        ON CONFLICT (version_num) DO NOTHING;
        """
        
        cursor.execute(create_tables_sql)
        conn.commit()
        
        print("✅ Staging database tables created successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Created {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating staging database: {e}")
        return False

def test_database_connection():
    """Test the database connection"""
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5435,
            database="acgs_staging",
            user="acgs_user",
            password="acgs_staging_password_2024_phase3_secure"
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"✅ Database connection successful!")
        print(f"PostgreSQL version: {version[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    print("ACGS Staging Database Setup")
    print("===========================")
    
    # Test connection first
    if not test_database_connection():
        print("❌ Cannot connect to database. Make sure PostgreSQL is running.")
        sys.exit(1)
    
    # Create tables
    if create_staging_database():
        print("✅ Staging database setup completed successfully!")
    else:
        print("❌ Staging database setup failed!")
        sys.exit(1)
