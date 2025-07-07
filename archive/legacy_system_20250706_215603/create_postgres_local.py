#!/usr/bin/env python3
"""
Create Local PostgreSQL Database for AI-Horizon Ed Platform

This script creates a local PostgreSQL database named 'aih_edu_local' and migrates 
all data from the SQLite database. It provides a complete testing environment
with PostgreSQL locally.
"""

import os
import sys
import json
import logging
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

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

class PostgreSQLMigrator:
    """Migrate SQLite data to local PostgreSQL"""
    
    def __init__(self):
        self.current_user = os.getenv('USER', 'postgres')
        self.db_name = 'aih_edu_local'
        self.sqlite_path = 'data/aih_edu.db'
        self.postgres_url = f"postgresql://{self.current_user}@localhost:5432/{self.db_name}"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        logger.info("🔍 Checking prerequisites...")
        
        # Check if psycopg2 is available
        if not POSTGRES_AVAILABLE:
            logger.error("❌ psycopg2 not available. Install with: pip install psycopg2-binary")
            return False
        
        # Check if PostgreSQL is running
        try:
            result = subprocess.run(['pg_isready'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.error("❌ PostgreSQL is not running. Start with: brew services start postgresql@14")
                return False
        except FileNotFoundError:
            logger.error("❌ PostgreSQL not found. Install with: brew install postgresql@14")
            return False
        
        # Check if SQLite database exists
        if not os.path.exists(self.sqlite_path):
            logger.error(f"❌ SQLite database not found at {self.sqlite_path}")
            return False
            
        logger.info("✅ All prerequisites met")
        return True
    
    def create_database(self) -> bool:
        """Create the PostgreSQL database"""
        logger.info(f"🗃️ Creating database '{self.db_name}'...")
        
        try:
            # Connect to default postgres database
            default_url = f"postgresql://{self.current_user}@localhost:5432/postgres"
            
            with psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user=self.current_user
            ) as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    # Check if database exists
                    cursor.execute(
                        "SELECT 1 FROM pg_database WHERE datname = %s",
                        (self.db_name,)
                    )
                    
                    if cursor.fetchone():
                        logger.info(f"   Database '{self.db_name}' already exists")
                        return True
                    
                    # Create database
                    cursor.execute(f"CREATE DATABASE {self.db_name}")
                    logger.info(f"✅ Database '{self.db_name}' created successfully")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Failed to create database: {e}")
            return False
    
    def create_schema(self) -> bool:
        """Create the database schema"""
        logger.info("🏗️ Creating database schema...")
        
        schema_sql = '''
            -- Emerging Skills Table
            CREATE TABLE IF NOT EXISTS emerging_skills (
                id SERIAL PRIMARY KEY,
                skill_name VARCHAR(255) NOT NULL UNIQUE,
                category VARCHAR(100),
                urgency_score FLOAT,
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
                quality_score FLOAT,
                discovery_method VARCHAR(100),
                ai_analysis_score FLOAT,
                ai_analysis_details TEXT,
                ai_analysis_date TIMESTAMP,
                learning_level VARCHAR(50),
                sequence_order INTEGER,
                prerequisites TEXT,
                learning_objectives TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Skill Resources Junction Table
            CREATE TABLE IF NOT EXISTS skill_resources (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                relevance_score FLOAT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(skill_id, resource_id)
            );
            
            -- Search Analytics Table
            CREATE TABLE IF NOT EXISTS search_analytics (
                id SERIAL PRIMARY KEY,
                search_query VARCHAR(500),
                search_filters TEXT,
                results_count INTEGER,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_session VARCHAR(100)
            );
            
            -- Resource Questions Table
            CREATE TABLE IF NOT EXISTS resource_questions (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                question_text TEXT NOT NULL,
                correct_answer TEXT NOT NULL,
                wrong_answers TEXT,
                explanation TEXT,
                difficulty_level VARCHAR(50),
                ai_generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                question_type VARCHAR(50) DEFAULT 'multiple_choice'
            );
            
            -- Quiz Attempts Table
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                user_session VARCHAR(100),
                score FLOAT,
                total_questions INTEGER,
                correct_answers INTEGER,
                attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                time_spent_seconds INTEGER
            );
            
            -- Learning Sessions Table
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                user_preferences TEXT,
                session_data TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Learning Paths Table
            CREATE TABLE IF NOT EXISTS skill_learning_paths (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                path_name VARCHAR(255) NOT NULL,
                path_description TEXT,
                estimated_duration VARCHAR(100),
                difficulty_level VARCHAR(50),
                prerequisites TEXT,
                learning_objectives TEXT,
                path_order INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Content Analysis Queue Table
            CREATE TABLE IF NOT EXISTS content_analysis_queue (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                priority INTEGER DEFAULT 1,
                status VARCHAR(50) DEFAULT 'pending',
                analysis_type VARCHAR(100),
                queued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_date TIMESTAMP,
                completed_date TIMESTAMP,
                error_message TEXT
            );
            
            -- Learning Content Table
            CREATE TABLE IF NOT EXISTS learning_content (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                content_type VARCHAR(100),
                content_data TEXT,
                ai_generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_metadata TEXT
            );
        '''
        
        try:
            with psycopg2.connect(
                host='localhost',
                port=5432,
                database=self.db_name,
                user=self.current_user
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                    
                    # Create indexes
                    indexes = [
                        'CREATE INDEX IF NOT EXISTS idx_skill_resources_skill ON skill_resources(skill_id)',
                        'CREATE INDEX IF NOT EXISTS idx_skill_resources_resource ON skill_resources(resource_id)',
                        'CREATE INDEX IF NOT EXISTS idx_resources_quality ON educational_resources(quality_score)',
                        'CREATE INDEX IF NOT EXISTS idx_resources_category ON educational_resources(skill_category)',
                        'CREATE INDEX IF NOT EXISTS idx_resources_type ON educational_resources(resource_type)',
                        'CREATE INDEX IF NOT EXISTS idx_resources_difficulty ON educational_resources(difficulty_level)',
                        'CREATE INDEX IF NOT EXISTS idx_resources_cost ON educational_resources(cost_type)',
                        'CREATE INDEX IF NOT EXISTS idx_search_date ON search_analytics(search_date)',
                        'CREATE INDEX IF NOT EXISTS idx_quiz_resource ON quiz_attempts(resource_id)',
                        'CREATE INDEX IF NOT EXISTS idx_learning_session ON learning_sessions(session_id)'
                    ]
                    
                    for index_sql in indexes:
                        cursor.execute(index_sql)
                    
                conn.commit()
                logger.info("✅ Database schema created successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to create schema: {e}")
            return False
    
    def get_sqlite_data(self) -> Dict[str, List[Dict]]:
        """Extract all data from SQLite database"""
        logger.info("📖 Extracting data from SQLite database...")
        
        data = {}
        
        try:
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    logger.info(f"  📋 Extracting {table}...")
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    table_data = []
                    for row in rows:
                        table_data.append(dict(row))
                    
                    data[table] = table_data
                    logger.info(f"    ✅ {len(table_data)} rows extracted")
                
                return data
                
        except Exception as e:
            logger.error(f"❌ Failed to extract SQLite data: {e}")
            return {}
    
    def migrate_data(self, data: Dict[str, List[Dict]]) -> bool:
        """Migrate data to PostgreSQL"""
        logger.info("🚀 Migrating data to PostgreSQL...")
        
        try:
            with psycopg2.connect(
                host='localhost',
                port=5432,
                database=self.db_name,
                user=self.current_user
            ) as conn:
                with conn.cursor() as cursor:
                    # Migration order (respecting foreign key constraints)
                    migration_order = [
                        'emerging_skills',
                        'educational_resources',
                        'skill_resources',
                        'search_analytics',
                        'resource_questions',
                        'quiz_attempts',
                        'learning_sessions',
                        'skill_learning_paths',
                        'content_analysis_queue',
                        'learning_content'
                    ]
                    
                    for table_name in migration_order:
                        if table_name in data:
                            table_data = data[table_name]
                            logger.info(f"  🔄 Migrating {table_name} ({len(table_data)} rows)...")
                            
                            if table_data:
                                # Get column names
                                columns = list(table_data[0].keys())
                                
                                # Skip 'id' column for auto-increment
                                if 'id' in columns:
                                    columns.remove('id')
                                
                                # Create INSERT statement
                                placeholders = ', '.join(['%s'] * len(columns))
                                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                                
                                # Insert data
                                success_count = 0
                                for i, row in enumerate(table_data):
                                    try:
                                        values = []
                                        for col in columns:
                                            value = row.get(col)
                                            # Handle timestamp/date conversion issues
                                            if value in ('CURRENT_TIMESTAMP', 'CURRENT_TEXT', 'CURRENT_DATE'):
                                                values.append(None)  # Let PostgreSQL use DEFAULT
                                            elif col.endswith('_date') and isinstance(value, str) and value.strip() == '':
                                                values.append(None)
                                            else:
                                                values.append(value)
                                        cursor.execute(insert_sql, values)
                                        success_count += 1
                                    except Exception as e:
                                        logger.warning(f"    ⚠️ Row {i+1} failed: {e}")
                                        continue
                                
                                logger.info(f"    ✅ {success_count}/{len(table_data)} rows migrated")
                            else:
                                logger.info(f"    ⏭️ No data to migrate for {table_name}")
                    
                conn.commit()
                logger.info("✅ Data migration completed successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False
    
    def verify_migration(self) -> bool:
        """Verify the migration was successful"""
        logger.info("🔍 Verifying migration...")
        
        try:
            # Check SQLite counts
            with sqlite3.connect(self.sqlite_path) as sqlite_conn:
                sqlite_cursor = sqlite_conn.cursor()
                sqlite_cursor.execute("SELECT COUNT(*) FROM emerging_skills")
                sqlite_skills = sqlite_cursor.fetchone()[0]
                sqlite_cursor.execute("SELECT COUNT(*) FROM educational_resources")
                sqlite_resources = sqlite_cursor.fetchone()[0]
            
            # Check PostgreSQL counts
            with psycopg2.connect(
                host='localhost',
                port=5432,
                database=self.db_name,
                user=self.current_user
            ) as postgres_conn:
                with postgres_conn.cursor() as postgres_cursor:
                    postgres_cursor.execute("SELECT COUNT(*) FROM emerging_skills")
                    postgres_skills = postgres_cursor.fetchone()[0]
                    postgres_cursor.execute("SELECT COUNT(*) FROM educational_resources")
                    postgres_resources = postgres_cursor.fetchone()[0]
            
            logger.info(f"📊 Verification Results:")
            logger.info(f"  SQLite:     {sqlite_skills} skills, {sqlite_resources} resources")
            logger.info(f"  PostgreSQL: {postgres_skills} skills, {postgres_resources} resources")
            
            if sqlite_skills == postgres_skills and sqlite_resources == postgres_resources:
                logger.info("✅ Migration verified successfully!")
                return True
            else:
                logger.error("❌ Migration verification failed - record counts don't match")
                return False
                
        except Exception as e:
            logger.error(f"❌ Migration verification failed: {e}")
            return False
    
    def create_env_file(self) -> bool:
        """Create .env file with PostgreSQL settings"""
        logger.info("📝 Creating .env file...")
        
        env_content = f"""# PostgreSQL Configuration for Local Testing
DATABASE_URL={self.postgres_url}
PORT=9000
"""
        
        try:
            with open('.env.postgres', 'w') as f:
                f.write(env_content)
            
            logger.info("✅ .env.postgres file created")
            logger.info("To use PostgreSQL, run: mv .env.postgres .env")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create .env file: {e}")
            return False
    
    def run_complete_migration(self) -> bool:
        """Run the complete migration process"""
        logger.info("🚀 Starting Complete PostgreSQL Migration")
        logger.info("=" * 60)
        
        # Step 1: Prerequisites
        if not self.check_prerequisites():
            return False
        
        # Step 2: Create database
        if not self.create_database():
            return False
        
        # Step 3: Create schema
        if not self.create_schema():
            return False
        
        # Step 4: Extract data
        data = self.get_sqlite_data()
        if not data:
            logger.error("❌ Failed to extract data from SQLite")
            return False
        
        # Step 5: Migrate data
        if not self.migrate_data(data):
            return False
        
        # Step 6: Verify migration
        if not self.verify_migration():
            return False
        
        # Step 7: Create env file
        if not self.create_env_file():
            return False
        
        logger.info("=" * 60)
        logger.info("🎉 POSTGRESQL MIGRATION COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"Database URL: {self.postgres_url}")
        logger.info("To use PostgreSQL:")
        logger.info("1. mv .env.postgres .env")
        logger.info("2. python app.py")
        logger.info("=" * 60)
        
        return True

if __name__ == "__main__":
    migrator = PostgreSQLMigrator()
    success = migrator.run_complete_migration()
    
    if not success:
        sys.exit(1) 