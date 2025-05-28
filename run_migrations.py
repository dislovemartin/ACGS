#!/usr/bin/env python3
"""
Simple migration runner for ACGS-PGP
This script runs Alembic migrations without Docker complexity
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def wait_for_postgres(host="localhost", port="5433", user="acgs_user", password="acgs_password", max_attempts=30):
    """Wait for PostgreSQL to be ready"""
    print(f"Waiting for PostgreSQL at {host}:{port}...")
    
    for attempt in range(max_attempts):
        try:
            # Use pg_isready if available, otherwise try psql
            result = subprocess.run([
                "pg_isready", 
                "-h", host, 
                "-p", str(port), 
                "-U", user
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PostgreSQL is ready!")
                return True
                
        except FileNotFoundError:
            # pg_isready not available, try psql
            try:
                env = os.environ.copy()
                env["PGPASSWORD"] = password
                result = subprocess.run([
                    "psql", 
                    "-h", host, 
                    "-p", str(port), 
                    "-U", user, 
                    "-d", "acgs_pgp_db",
                    "-c", "SELECT 1;"
                ], capture_output=True, text=True, env=env)
                
                if result.returncode == 0:
                    print("✅ PostgreSQL is ready!")
                    return True
                    
            except FileNotFoundError:
                print("⚠️  Neither pg_isready nor psql found, trying Python connection...")
                try:
                    import psycopg2
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        user=user,
                        password=password,
                        database="acgs_pgp_db"
                    )
                    conn.close()
                    print("✅ PostgreSQL is ready!")
                    return True
                except Exception as e:
                    pass
        
        print(f"⏳ Attempt {attempt + 1}/{max_attempts} - PostgreSQL not ready yet...")
        time.sleep(2)
    
    print("❌ PostgreSQL failed to become ready")
    return False

def run_migrations():
    """Run Alembic migrations"""
    print("🔄 Running Alembic migrations...")
    
    # Set up environment
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://acgs_user:acgs_password@localhost:5433/acgs_pgp_db"
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    try:
        # Run alembic upgrade
        result = subprocess.run([
            sys.executable, "-m", "alembic",
            "-c", "alembic.ini",
            "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Migration failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ACGS-PGP Migration Runner")
    print("=" * 40)
    
    # Wait for PostgreSQL
    if not wait_for_postgres():
        sys.exit(1)
    
    # Run migrations
    if not run_migrations():
        sys.exit(1)
    
    print("🎉 All done! Database is ready.")

if __name__ == "__main__":
    main()
