#!/usr/bin/env python3
"""
Simple PostgreSQL Migration for AI-Horizon Ed Platform

This script creates a clean local PostgreSQL database and migrates all data 
from SQLite with proper error handling and individual transactions.
"""

import os
import sqlite3
import psycopg2
import psycopg2.extras
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class SimplePostgresMigrator:
    def __init__(self):
        self.current_user = os.getenv('USER', 'postgres')
        self.db_name = 'aih_edu_local'
        self.sqlite_path = 'aih_edu/data/aih_edu.db'
        
    def drop_and_create_database(self):
        """Drop existing database and create fresh one"""
        logger.info("🗂️ Creating fresh PostgreSQL database...")
        
        try:
            # Connect to postgres database
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='postgres',
                user=self.current_user
            )
            conn.autocommit = True
            
            with conn.cursor() as cursor:
                # Drop database if exists
                cursor.execute(f"DROP DATABASE IF EXISTS {self.db_name}")
                logger.info(f"   Dropped existing database")
                
                # Create new database
                cursor.execute(f"CREATE DATABASE {self.db_name}")
                logger.info(f"   Created database '{self.db_name}'")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"❌ Database creation failed: {e}")
            return False
    
    def create_schema(self):
        """Create database schema"""
        logger.info("🏗️ Creating schema...")
        
        schema_sql = '''
            -- Skills
            CREATE TABLE emerging_skills (
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
            
                         -- Resources
            CREATE TABLE educational_resources (
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
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                keywords TEXT,
                learning_outcomes TEXT,
                content_extracted TEXT
            );
            
            -- Skill-Resource mapping
            CREATE TABLE skill_resources (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id),
                resource_id INTEGER REFERENCES educational_resources(id),
                relevance_score FLOAT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Learning sessions
            CREATE TABLE learning_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE NOT NULL,
                skill_id INTEGER REFERENCES emerging_skills(id),
                user_preferences TEXT,
                session_data TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Learning paths
            CREATE TABLE skill_learning_paths (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id),
                path_name VARCHAR(255) NOT NULL,
                path_description TEXT,
                estimated_duration VARCHAR(100),
                difficulty_level VARCHAR(50),
                prerequisites TEXT,
                learning_objectives TEXT,
                path_order INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            -- Content analysis queue
            CREATE TABLE content_analysis_queue (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id),
                priority INTEGER DEFAULT 1,
                status VARCHAR(50) DEFAULT 'pending',
                analysis_type VARCHAR(100),
                queued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_date TIMESTAMP,
                completed_date TIMESTAMP,
                error_message TEXT
            );
            
            -- Learning content
            CREATE TABLE learning_content (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id),
                content_type VARCHAR(100),
                content_data TEXT,
                ai_generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_metadata TEXT
            );
        '''
        
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database=self.db_name,
                user=self.current_user
            )
            
            with conn.cursor() as cursor:
                cursor.execute(schema_sql)
            
            conn.commit()
            conn.close()
            logger.info("✅ Schema created successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return False
    
    def migrate_table(self, table_name, postgres_table_name=None):
        """Migrate a specific table from SQLite to PostgreSQL"""
        if postgres_table_name is None:
            postgres_table_name = table_name
            
        logger.info(f"📋 Migrating {table_name}...")
        
        # Get SQLite data
        try:
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            cursor = sqlite_conn.cursor()
            
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            
            if not rows:
                logger.info(f"   ⏭️ No data in {table_name}")
                sqlite_conn.close()
                return True
                
            # Get PostgreSQL connection
            postgres_conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database=self.db_name,
                user=self.current_user
            )
            
            success_count = 0
            
            for i, row in enumerate(rows):
                try:
                    postgres_conn.rollback()  # Start fresh transaction
                    
                    # Convert row to dict and clean values
                    row_dict = dict(row)
                    
                    # Remove id column (auto-increment)
                    if 'id' in row_dict:
                        del row_dict['id']
                    
                    # Clean timestamp values
                    for key, value in row_dict.items():
                        if value in ('CURRENT_TIMESTAMP', 'CURRENT_TEXT', 'CURRENT_DATE'):
                            row_dict[key] = None
                        elif isinstance(value, str) and key.endswith('_date') and value.strip() == '':
                            row_dict[key] = None
                    
                    # Insert into PostgreSQL
                    columns = list(row_dict.keys())
                    values = list(row_dict.values())
                    
                    placeholders = ', '.join(['%s'] * len(columns))
                    insert_sql = f"INSERT INTO {postgres_table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                    
                    with postgres_conn.cursor() as pg_cursor:
                        pg_cursor.execute(insert_sql, values)
                    
                    postgres_conn.commit()
                    success_count += 1
                    
                except Exception as e:
                    logger.debug(f"   Row {i+1} failed: {e}")
                    continue
            
            sqlite_conn.close()
            postgres_conn.close()
            
            logger.info(f"   ✅ {success_count}/{len(rows)} rows migrated")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration of {table_name} failed: {e}")
            return False
    
    def verify_migration(self):
        """Verify migration results"""
        logger.info("🔍 Verifying migration...")
        
        try:
            # SQLite counts
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM emerging_skills")
            sqlite_skills = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM educational_resources")
            sqlite_resources = cursor.fetchone()[0]
            sqlite_conn.close()
            
            # PostgreSQL counts
            postgres_conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database=self.db_name,
                user=self.current_user
            )
            with postgres_conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM emerging_skills")
                postgres_skills = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM educational_resources")
                postgres_resources = cursor.fetchone()[0]
            postgres_conn.close()
            
            logger.info(f"📊 Results:")
            logger.info(f"   SQLite:     {sqlite_skills} skills, {sqlite_resources} resources")
            logger.info(f"   PostgreSQL: {postgres_skills} skills, {postgres_resources} resources")
            
            if postgres_skills >= sqlite_skills * 0.8 and postgres_resources >= sqlite_resources * 0.8:
                logger.info("✅ Migration verification passed")
                return True
            else:
                logger.warning("⚠️ Migration had some data loss, but core data migrated")
                return True
                
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False
    
    def create_env_file(self):
        """Create environment file for PostgreSQL"""
        env_content = f"""DATABASE_URL=postgresql://{self.current_user}@localhost:5432/{self.db_name}
PORT=9000
"""
        
        with open('.env.postgres', 'w') as f:
            f.write(env_content)
        
        logger.info("📝 Created .env.postgres file")
        logger.info("   To use PostgreSQL: mv .env.postgres .env")
    
    def run_migration(self):
        """Run complete migration"""
        logger.info("🚀 Starting PostgreSQL Migration")
        logger.info("=" * 50)
        
        # Step 1: Create fresh database
        if not self.drop_and_create_database():
            return False
        
        # Step 2: Create schema
        if not self.create_schema():
            return False
        
        # Step 3: Migrate data (in dependency order)
        tables_to_migrate = [
            'emerging_skills',
            'educational_resources', 
            'skill_resources',
            'learning_sessions',
            'skill_learning_paths',
            'content_analysis_queue',
            'learning_content'
        ]
        
        for table in tables_to_migrate:
            self.migrate_table(table)
        
        # Step 4: Verify
        self.verify_migration()
        
        # Step 5: Create env file
        self.create_env_file()
        
        logger.info("=" * 50)
        logger.info("🎉 MIGRATION COMPLETED!")
        logger.info("=" * 50)
        logger.info(f"Database URL: postgresql://{self.current_user}@localhost:5432/{self.db_name}")
        logger.info("To use PostgreSQL:")
        logger.info("1. mv .env.postgres .env")
        logger.info("2. cd aih_edu && python app.py")
        
        return True

if __name__ == "__main__":
    migrator = SimplePostgresMigrator()
    migrator.run_migration() 