#!/usr/bin/env python3
"""
Comprehensive test data loading script for ACGS-PGP Phase 1 remediation.
Loads test data for all microservices and validates database connectivity.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
import asyncpg
from datetime import datetime, timezone

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "backend"))

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://acgs_user:acgs_password@localhost:5433/acgs_pgp_db"
)

class TestDataLoader:
    def __init__(self):
        self.connection = None
        self.data_dir = project_root / "data"
        
    async def connect(self):
        """Connect to PostgreSQL database."""
        try:
            # Parse the DATABASE_URL to extract connection parameters
            if DATABASE_URL.startswith("postgresql+asyncpg://"):
                url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
            else:
                url = DATABASE_URL.replace("postgresql://", "postgresql://")
            
            self.connection = await asyncpg.connect(url)
            print("✅ Database connection established")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    async def close(self):
        """Close database connection."""
        if self.connection:
            await self.connection.close()
            print("✅ Database connection closed")
    
    async def load_test_users(self) -> bool:
        """Load test users with different roles."""
        try:
            with open(self.data_dir / "test_users.json", "r") as f:
                data = json.load(f)
            
            users_loaded = 0
            for user_data in data["test_users"]:
                # Check if user already exists
                existing = await self.connection.fetchrow(
                    "SELECT id FROM users WHERE username = $1 OR email = $2",
                    user_data["username"], user_data["email"]
                )
                
                if existing:
                    print(f"⚠️  User {user_data['username']} already exists, skipping")
                    continue
                
                # Hash password (simplified for testing)
                import hashlib
                hashed_password = hashlib.sha256(user_data["password"].encode()).hexdigest()
                
                await self.connection.execute("""
                    INSERT INTO users (username, email, hashed_password, full_name, role, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6)
                """, 
                    user_data["username"],
                    user_data["email"], 
                    hashed_password,
                    user_data["full_name"],
                    user_data["role"],
                    user_data["is_active"]
                )
                users_loaded += 1
                print(f"✅ Loaded user: {user_data['username']} ({user_data['role']})")
            
            print(f"✅ Test users loaded: {users_loaded}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load test users: {e}")
            return False
    
    async def load_test_principles(self) -> bool:
        """Load test principles with enhanced Phase 1 fields."""
        try:
            with open(self.data_dir / "test_ac_principles.json", "r") as f:
                data = json.load(f)
            
            # Get admin user ID
            admin_user = await self.connection.fetchrow(
                "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
            )
            admin_user_id = admin_user["id"] if admin_user else None
            
            principles_loaded = 0
            for principle_data in data["test_principles"]:
                # Check if principle already exists
                existing = await self.connection.fetchrow(
                    "SELECT id FROM principles WHERE title = $1",
                    principle_data["title"]
                )
                
                if existing:
                    print(f"⚠️  Principle '{principle_data['title']}' already exists, skipping")
                    continue
                
                await self.connection.execute("""
                    INSERT INTO principles (
                        title, description, content, priority_weight, scope,
                        normative_statement, constraints, rationale, status,
                        version, created_by_user_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                """,
                    principle_data["title"],
                    principle_data["description"],
                    principle_data["content"],
                    principle_data["priority_weight"],
                    principle_data["scope"],
                    principle_data["normative_statement"],
                    json.dumps(principle_data["constraints"]),
                    principle_data["rationale"],
                    principle_data["status"],
                    principle_data["version"],
                    admin_user_id
                )
                principles_loaded += 1
                print(f"✅ Loaded principle: {principle_data['title']}")
            
            print(f"✅ Test principles loaded: {principles_loaded}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load test principles: {e}")
            return False
    
    async def load_test_meta_rules(self) -> bool:
        """Load test meta-rules for constitutional governance."""
        try:
            with open(self.data_dir / "test_ac_meta_rules.json", "r") as f:
                data = json.load(f)
            
            # Get admin user ID
            admin_user = await self.connection.fetchrow(
                "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
            )
            admin_user_id = admin_user["id"] if admin_user else None
            
            meta_rules_loaded = 0
            for meta_rule_data in data["test_meta_rules"]:
                # Check if meta-rule already exists
                existing = await self.connection.fetchrow(
                    "SELECT id FROM ac_meta_rules WHERE name = $1",
                    meta_rule_data["name"]
                )
                
                if existing:
                    print(f"⚠️  Meta-rule '{meta_rule_data['name']}' already exists, skipping")
                    continue
                
                await self.connection.execute("""
                    INSERT INTO ac_meta_rules (
                        rule_type, name, description, rule_definition, threshold,
                        stakeholder_roles, decision_mechanism, status,
                        created_by_user_id
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                    meta_rule_data["rule_type"],
                    meta_rule_data["name"],
                    meta_rule_data["description"],
                    json.dumps(meta_rule_data["rule_definition"]),
                    meta_rule_data["threshold"],
                    json.dumps(meta_rule_data["stakeholder_roles"]),
                    meta_rule_data["decision_mechanism"],
                    meta_rule_data["status"],
                    admin_user_id
                )
                meta_rules_loaded += 1
                print(f"✅ Loaded meta-rule: {meta_rule_data['name']}")
            
            print(f"✅ Test meta-rules loaded: {meta_rules_loaded}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load test meta-rules: {e}")
            return False

    async def load_test_environmental_factors(self) -> bool:
        """Load test environmental factors for contextual analysis."""
        try:
            with open(self.data_dir / "test_environmental_factors.json", "r") as f:
                data = json.load(f)
            
            factors_loaded = 0
            for factor_data in data["test_environmental_factors"]:
                # Check if factor already exists
                existing = await self.connection.fetchrow(
                    "SELECT id FROM environmental_factors WHERE name = $1",
                    factor_data["factor_name"]
                )

                if existing:
                    print(f"⚠️  Environmental factor '{factor_data['factor_name']}' already exists, skipping")
                    continue

                # Create value JSON that includes all the factor data
                value_json = {
                    "value": factor_data["value"],
                    "description": factor_data["description"],
                    "impact_level": factor_data["impact_level"],
                    "affects_principles": factor_data["affects_principles"],
                    "metadata": factor_data["metadata"]
                }

                await self.connection.execute("""
                    INSERT INTO environmental_factors (
                        factor_type, name, value, source
                    ) VALUES ($1, $2, $3, $4)
                """,
                    factor_data["factor_type"],
                    factor_data["factor_name"],
                    json.dumps(value_json),
                    "test_data_loader"
                )
                factors_loaded += 1
                print(f"✅ Loaded environmental factor: {factor_data['factor_name']}")
            
            print(f"✅ Test environmental factors loaded: {factors_loaded}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load test environmental factors: {e}")
            return False

    async def validate_data_integrity(self) -> bool:
        """Validate that all test data was loaded correctly."""
        try:
            # Check users
            user_count = await self.connection.fetchval("SELECT COUNT(*) FROM users")
            print(f"📊 Users in database: {user_count}")
            
            # Check principles
            principle_count = await self.connection.fetchval("SELECT COUNT(*) FROM principles")
            print(f"📊 Principles in database: {principle_count}")
            
            # Check meta-rules
            meta_rule_count = await self.connection.fetchval("SELECT COUNT(*) FROM ac_meta_rules")
            print(f"📊 Meta-rules in database: {meta_rule_count}")
            
            # Check environmental factors
            factor_count = await self.connection.fetchval("SELECT COUNT(*) FROM environmental_factors")
            print(f"📊 Environmental factors in database: {factor_count}")
            
            # Validate enhanced principle fields
            enhanced_principles = await self.connection.fetch("""
                SELECT title, priority_weight, scope, normative_statement 
                FROM principles 
                WHERE priority_weight IS NOT NULL AND scope IS NOT NULL
            """)
            print(f"📊 Principles with enhanced fields: {len(enhanced_principles)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Data validation failed: {e}")
            return False

async def main():
    """Main function to load all test data."""
    print("🚀 Starting ACGS-PGP Phase 1 Test Data Loading...")
    
    loader = TestDataLoader()
    
    try:
        # Connect to database
        if not await loader.connect():
            return False
        
        # Load test data in order
        success = True
        success &= await loader.load_test_users()
        success &= await loader.load_test_principles()
        success &= await loader.load_test_meta_rules()
        success &= await loader.load_test_environmental_factors()
        
        # Validate data integrity
        if success:
            success &= await loader.validate_data_integrity()
        
        if success:
            print("✅ All test data loaded successfully!")
        else:
            print("❌ Some test data loading failed")
        
        return success
        
    finally:
        await loader.close()

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
