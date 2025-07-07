#!/usr/bin/env python3
"""
Setup Local PostgreSQL Database for AI-Horizon Ed Platform Testing

This script creates a local PostgreSQL database named 'aih_edu_test' and migrates 
all data from the SQLite database. It provides an easy way to test the application
with PostgreSQL locally before deploying to production.
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import PostgreSQL dependencies
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalPostgresTestSetup:
    """Setup and manage local PostgreSQL database for testing"""
    
    def __init__(self):
        # Get current user for database connection
        self.current_user = os.getenv('USER', 'postgres')
        
        # PostgreSQL connection details
        self.db_name = 'aih_edu_test'
        self.postgres_url = f"postgresql://{self.current_user}@localhost:5432/{self.db_name}"
        
        # SQLite database path
        self.sqlite_path = "data/aih_edu.db"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check if psycopg2 is available
        if not POSTGRES_AVAILABLE:
            logger.error("❌ psycopg2 not available. Install with: pip install psycopg2-binary")
            return False
        else:
            logger.info("✅ psycopg2 is available")
        
        # Check if PostgreSQL is running
        try:
            result = subprocess.run(['pg_isready'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✅ PostgreSQL is running")
            else:
                logger.error("❌ PostgreSQL is not running. Start it with: brew services start postgresql")
                return False
        except FileNotFoundError:
            logger.error("❌ PostgreSQL not found. Install with: brew install postgresql")
            return False
        
        # Check if SQLite database exists
        if os.path.exists(self.sqlite_path):
            logger.info("✅ SQLite database found")
        else:
            logger.warning(f"⚠️ SQLite database not found at {self.sqlite_path}")
            logger.info("   Will create empty PostgreSQL database")
        
        return True
    
    def test_postgres_connection(self) -> bool:
        """Test PostgreSQL connection to default database"""
        try:
            # Connect to default postgres database first
            default_url = f"postgresql://{self.current_user}@localhost:5432/postgres"
            with psycopg2.connect(default_url) as conn:
                logger.info("✅ PostgreSQL connection successful")
                return True
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    def create_database(self) -> bool:
        """Create the test database"""
        try:
            logger.info(f"🗃️ Creating database '{self.db_name}'...")
            
            # Connect to default postgres database
            default_url = f"postgresql://{self.current_user}@localhost:5432/postgres"
            
            conn = psycopg2.connect(default_url)
            conn.autocommit = True
            cursor = conn.cursor()
            
            try:
                # Check if database exists
                cursor.execute("""
                    SELECT 1 FROM pg_database WHERE datname = %s
                """, (self.db_name,))
                
                if cursor.fetchone():
                    logger.info(f"   Database '{self.db_name}' already exists")
                    # Ask user if they want to recreate it
                    response = input(f"   Recreate database '{self.db_name}'? (y/N): ").strip().lower()
                    if response == 'y':
                        logger.info(f"   Dropping existing database '{self.db_name}'...")
                        cursor.execute(f'DROP DATABASE IF EXISTS "{self.db_name}"')
                        cursor.execute(f'CREATE DATABASE "{self.db_name}"')
                        logger.info(f"✅ Database '{self.db_name}' recreated")
                    else:
                        logger.info(f"   Using existing database '{self.db_name}'")
                else:
                    cursor.execute(f'CREATE DATABASE "{self.db_name}"')
                    logger.info(f"✅ Database '{self.db_name}' created")
            finally:
                cursor.close()
                conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create database schema"""
        try:
            logger.info("📋 Creating database schema...")
            
            # Define the schema (compatible with both SQLite and PostgreSQL)
            schema_sql = """
            -- Emerging Skills Table
            CREATE TABLE IF NOT EXISTS emerging_skills (
                id SERIAL PRIMARY KEY,
                skill_name VARCHAR(255) NOT NULL UNIQUE,
                category VARCHAR(100),
                urgency_score REAL,
                demand_trend VARCHAR(50),
                source_analysis TEXT,
                description TEXT,
                related_skills TEXT,
                keywords TEXT,
                job_market_data TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                discovery_status VARCHAR(50) DEFAULT 'pending'
            );
            
            -- Educational Resources Table
            CREATE TABLE IF NOT EXISTS educational_resources (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                url VARCHAR(1000) NOT NULL,
                resource_type VARCHAR(100),
                cost_type VARCHAR(50),
                difficulty_level VARCHAR(50),
                estimated_duration VARCHAR(100),
                author VARCHAR(255),
                publication_date DATE,
                last_updated DATE,
                tags TEXT,
                skill_category VARCHAR(100),
                quality_score REAL,
                discovery_method VARCHAR(100),
                ai_analysis_score REAL,
                ai_analysis_details TEXT,
                ai_analysis_date TIMESTAMP,
                learning_level VARCHAR(50),
                sequence_order INTEGER,
                prerequisites TEXT,
                learning_objectives TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Skill Resources Mapping
            CREATE TABLE IF NOT EXISTS skill_resources (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                relevance_score REAL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(skill_id, resource_id)
            );
            
            -- Learning Content
            CREATE TABLE IF NOT EXISTS learning_content (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                content_type VARCHAR(50) NOT NULL,
                title VARCHAR(500),
                content TEXT,
                metadata TEXT,
                quality_score REAL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Skill Learning Paths
            CREATE TABLE IF NOT EXISTS skill_learning_paths (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                path_name VARCHAR(255) NOT NULL,
                path_description TEXT,
                difficulty_level VARCHAR(50),
                estimated_duration VARCHAR(100),
                path_order INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Learning Sessions
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL UNIQUE,
                skill_id INTEGER REFERENCES emerging_skills(id),
                user_id VARCHAR(255),
                session_data TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Content Analysis Queue
            CREATE TABLE IF NOT EXISTS content_analysis_queue (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                analysis_type VARCHAR(50) NOT NULL,
                priority INTEGER DEFAULT 5,
                status VARCHAR(50) DEFAULT 'pending',
                queued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_date TIMESTAMP,
                completed_date TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            );
            
            -- Resource Questions
            CREATE TABLE IF NOT EXISTS resource_questions (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                question_text TEXT NOT NULL,
                question_type VARCHAR(50),
                options TEXT,
                correct_answer TEXT,
                explanation TEXT,
                difficulty_level VARCHAR(20),
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Resource Exercises
            CREATE TABLE IF NOT EXISTS resource_exercises (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                exercise_type VARCHAR(50) NOT NULL,
                title VARCHAR(255),
                description TEXT,
                content TEXT,
                solution TEXT,
                difficulty_level VARCHAR(20),
                estimated_time INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Quiz Attempts
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id),
                user_session VARCHAR(255),
                answers TEXT,
                score REAL,
                total_questions INTEGER,
                correct_answers INTEGER,
                attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Search Logs
            CREATE TABLE IF NOT EXISTS search_logs (
                id SERIAL PRIMARY KEY,
                query TEXT NOT NULL,
                filters TEXT,
                result_count INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Create indexes for better performance
            CREATE INDEX IF NOT EXISTS idx_educational_resources_skill_category ON educational_resources(skill_category);
            CREATE INDEX IF NOT EXISTS idx_educational_resources_learning_level ON educational_resources(learning_level);
            CREATE INDEX IF NOT EXISTS idx_educational_resources_quality_score ON educational_resources(quality_score);
            CREATE INDEX IF NOT EXISTS idx_skill_resources_skill_id ON skill_resources(skill_id);
            CREATE INDEX IF NOT EXISTS idx_skill_resources_resource_id ON skill_resources(resource_id);
            CREATE INDEX IF NOT EXISTS idx_resource_questions_resource_id ON resource_questions(resource_id);
            CREATE INDEX IF NOT EXISTS idx_resource_exercises_resource_id ON resource_exercises(resource_id);
            """
            
            with psycopg2.connect(self.postgres_url) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                    conn.commit()
            
            logger.info("✅ Database schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return False
    
    def migrate_data_from_sqlite(self) -> bool:
        """Migrate data from SQLite to PostgreSQL"""
        if not os.path.exists(self.sqlite_path):
            logger.info("ℹ️ No SQLite database found, skipping data migration")
            return True
        
        try:
            logger.info("📦 Migrating data from SQLite...")
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            sqlite_cursor = sqlite_conn.cursor()
            
            # Connect to PostgreSQL
            postgres_conn = psycopg2.connect(self.postgres_url)
            postgres_cursor = postgres_conn.cursor()
            
            # Migration order (respecting foreign keys)
            migration_order = [
                'emerging_skills',
                'educational_resources',
                'skill_resources',
                'learning_content',
                'skill_learning_paths',
                'learning_sessions',
                'content_analysis_queue',
                'resource_questions',
                'resource_exercises',
                'quiz_attempts',
                'search_logs'
            ]
            
            total_migrated = 0
            
            for table_name in migration_order:
                try:
                    # Check if table exists in SQLite
                    sqlite_cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name=?
                    """, (table_name,))
                    
                    if not sqlite_cursor.fetchone():
                        logger.info(f"   Skipping {table_name} (not found in SQLite)")
                        continue
                    
                    # Get data from SQLite
                    sqlite_cursor.execute(f"SELECT * FROM {table_name}")
                    rows = sqlite_cursor.fetchall()
                    
                    if not rows:
                        logger.info(f"   Skipping {table_name} (no data)")
                        continue
                    
                    logger.info(f"   Migrating {table_name} ({len(rows)} rows)")
                    
                    # Get column names from PostgreSQL
                    postgres_cursor.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        ORDER BY ordinal_position
                    """, (table_name,))
                    
                    pg_columns = [row[0] for row in postgres_cursor.fetchall()]
                    
                    # Filter columns that exist in both databases
                    sqlite_columns = [desc[0] for desc in sqlite_cursor.description]
                    common_columns = [col for col in pg_columns if col in sqlite_columns and col != 'id']
                    
                    if not common_columns:
                        logger.warning(f"   No common columns found for {table_name}")
                        continue
                    
                    # Prepare insert statement
                    placeholders = ', '.join(['%s'] * len(common_columns))
                    columns_str = ', '.join(common_columns)
                    insert_sql = f"""
                        INSERT INTO {table_name} ({columns_str}) 
                        VALUES ({placeholders})
                    """
                    
                    # Migrate data
                    migrated_count = 0
                    for row in rows:
                        try:
                            # Extract values for common columns
                            values = []
                            for col in common_columns:
                                value = row[col]
                                # Handle JSON fields
                                if col in ['metadata', 'session_data', 'filters', 'options'] and value:
                                    if isinstance(value, str):
                                        try:
                                            json.loads(value)  # Validate JSON
                                            values.append(value)
                                        except:
                                            values.append(json.dumps(value))
                                    else:
                                        values.append(json.dumps(value))
                                else:
                                    values.append(value)
                            
                            postgres_cursor.execute(insert_sql, values)
                            migrated_count += 1
                            
                        except Exception as e:
                            logger.warning(f"     Failed to migrate row in {table_name}: {e}")
                            continue
                    
                    postgres_conn.commit()
                    total_migrated += migrated_count
                    logger.info(f"   ✅ Migrated {migrated_count} rows to {table_name}")
                    
                except Exception as e:
                    logger.error(f"   ❌ Failed to migrate {table_name}: {e}")
                    continue
            
            # Close connections
            sqlite_conn.close()
            postgres_conn.close()
            
            logger.info(f"✅ Data migration completed: {total_migrated} total rows migrated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False
    
    def verify_setup(self) -> Dict[str, Any]:
        """Verify the PostgreSQL setup"""
        logger.info("🔍 Verifying PostgreSQL setup...")
        
        verification = {
            'status': 'success',
            'tables': {},
            'total_records': 0,
            'issues': []
        }
        
        try:
            with psycopg2.connect(self.postgres_url) as conn:
                with conn.cursor() as cursor:
                    # Check tables
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                        ORDER BY table_name
                    """)
                    
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        verification['tables'][table] = count
                        verification['total_records'] += count
                    
                    logger.info(f"✅ Found {len(tables)} tables with {verification['total_records']} total records")
                    
                    for table, count in verification['tables'].items():
                        logger.info(f"   {table}: {count} rows")
        
        except Exception as e:
            verification['status'] = 'failed'
            verification['issues'].append(str(e))
            logger.error(f"❌ Verification failed: {e}")
        
        return verification
    
    def create_env_file(self) -> None:
        """Create .env file for PostgreSQL configuration"""
        logger.info("⚙️ Creating .env file for PostgreSQL configuration...")
        
        env_content = f"""# AI-Horizon Ed PostgreSQL Test Configuration
# Generated by setup_local_postgres_test.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Database Configuration - PostgreSQL
DATABASE_URL={self.postgres_url}

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=test-secret-key-local-only
PORT=9000

# Logging
LOG_LEVEL=INFO

# Note: To switch back to SQLite, change DATABASE_URL to:
# DATABASE_URL=sqlite:///data/aih_edu.db
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        logger.info("✅ .env file created")
        logger.info(f"   Database URL: {self.postgres_url}")
    
    def run_complete_setup(self) -> bool:
        """Run the complete setup process"""
        logger.info("🚀 Starting Local PostgreSQL Test Setup for AI-Horizon Ed")
        logger.info("=" * 70)
        
        # Step 1: Check prerequisites
        if not self.check_prerequisites():
            logger.error("❌ Prerequisites not met. Please fix the issues above.")
            return False
        
        # Step 2: Test PostgreSQL connection
        logger.info("\n📡 Testing PostgreSQL connection...")
        if not self.test_postgres_connection():
            return False
        
        # Step 3: Create database
        logger.info("\n🗃️ Setting up database...")
        if not self.create_database():
            return False
        
        # Step 4: Create schema
        logger.info("\n📋 Creating database schema...")
        if not self.create_schema():
            return False
        
        # Step 5: Migrate data
        logger.info("\n📦 Migrating data...")
        if not self.migrate_data_from_sqlite():
            logger.warning("⚠️ Data migration failed, but database is ready")
        
        # Step 6: Verify setup
        logger.info("\n🔍 Verifying setup...")
        verification = self.verify_setup()
        
        # Step 7: Create configuration
        logger.info("\n⚙️ Setting up configuration...")
        self.create_env_file()
        
        # Final summary
        logger.info("\n" + "=" * 70)
        logger.info("🎉 LOCAL POSTGRESQL TEST SETUP COMPLETE!")
        logger.info("=" * 70)
        
        logger.info(f"\n📍 Database Information:")
        logger.info(f"   URL: {self.postgres_url}")
        logger.info(f"   Database: {self.db_name}")
        logger.info(f"   Status: {verification['status']}")
        
        logger.info(f"\n📊 Data Summary:")
        for table, count in verification['tables'].items():
            logger.info(f"   {table}: {count} rows")
        
        logger.info(f"\n🚀 Next Steps:")
        logger.info(f"   1. Start the application: python app.py")
        logger.info(f"   2. The app will now use PostgreSQL instead of SQLite")
        logger.info(f"   3. To switch back to SQLite, edit .env and change DATABASE_URL")
        
        logger.info(f"\n⚠️ Note:")
        logger.info(f"   This is a test database for local development")
        logger.info(f"   Your original SQLite database remains unchanged")
        
        return True

def main():
    """Main function"""
    setup = LocalPostgresTestSetup()
    success = setup.run_complete_setup()
    
    if success:
        print("\n✅ Setup completed successfully!")
        print("You can now run the application with PostgreSQL.")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 