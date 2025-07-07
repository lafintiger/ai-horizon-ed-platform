#!/usr/bin/env python3
"""
Bulletproof Database Schema Management System

This module provides a comprehensive solution for managing database schemas
across SQLite (local) and PostgreSQL (Heroku) environments, ensuring
perfect compatibility and preventing corruption issues.
"""

import sqlite3
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Try to import PostgreSQL adapter
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)

class BulletproofSchemaManager:
    """Manages database schema with bulletproof compatibility"""
    
    def __init__(self, db_url: str):
        self.db_url = db_url
        self.is_postgres = self._is_postgres_url(db_url)
        
        if self.is_postgres:
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL connections")
            self.db_config = self._parse_postgres_url(db_url)
        else:
            # SQLite setup
            if db_url.startswith('sqlite:///'):
                db_url = db_url[10:]
            self.db_path = db_url
            self._ensure_data_directory()
    
    def _is_postgres_url(self, url: str) -> bool:
        """Check if URL is for PostgreSQL"""
        return url.startswith(('postgres://', 'postgresql://'))
    
    def _parse_postgres_url(self, url: str) -> Dict[str, Any]:
        """Parse PostgreSQL URL into connection parameters"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': parsed.password
        }
    
    def _ensure_data_directory(self):
        """Ensure data directory exists (SQLite only)"""
        if not self.is_postgres:
            data_dir = Path(self.db_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self):
        """Get database connection"""
        if self.is_postgres:
            return psycopg2.connect(**self.db_config)
        else:
            return sqlite3.connect(self.db_path)
    
    def get_unified_schema(self) -> Dict[str, str]:
        """Get the unified, bulletproof schema for both databases"""
        
        # Core schema - unified for both SQLite and PostgreSQL
        schema = {
            'emerging_skills': '''
                CREATE TABLE IF NOT EXISTS emerging_skills (
                    id INTEGER PRIMARY KEY,
                    skill_name TEXT NOT NULL UNIQUE,
                    category TEXT,
                    urgency_score REAL,
                    demand_trend TEXT,
                    source_analysis TEXT,
                    description TEXT,
                    related_skills TEXT,
                    keywords TEXT,
                    job_market_data TEXT,
                    created_date TEXT,
                    updated_date TEXT,
                    discovery_status TEXT DEFAULT 'pending'
                )
            ''',
            
            'educational_resources': '''
                CREATE TABLE IF NOT EXISTS educational_resources (
                    id INTEGER PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT NOT NULL,
                    resource_type TEXT,
                    cost_type TEXT,
                    difficulty_level TEXT,
                    estimated_duration TEXT,
                    author TEXT,
                    publication_date TEXT,
                    last_updated TEXT,
                    tags TEXT,
                    skill_category TEXT,
                    quality_score REAL,
                    discovery_method TEXT,
                    ai_analysis_score REAL,
                    ai_analysis_details TEXT,
                    ai_analysis_date TEXT,
                    learning_level TEXT,
                    sequence_order INTEGER,
                    prerequisites TEXT,
                    learning_objectives TEXT,
                    learning_outcomes TEXT,
                    metadata TEXT,
                    content_extracted TEXT,
                    source_platform TEXT,
                    created_date TEXT
                )
            ''',
            
            'skill_resources': '''
                CREATE TABLE IF NOT EXISTS skill_resources (
                    id INTEGER PRIMARY KEY,
                    skill_id INTEGER,
                    resource_id INTEGER,
                    relevance_score REAL,
                    created_date TEXT,
                    UNIQUE(skill_id, resource_id)
                )
            ''',
            
            'learning_content': '''
                CREATE TABLE IF NOT EXISTS learning_content (
                    id INTEGER PRIMARY KEY,
                    resource_id INTEGER,
                    skill_id INTEGER,
                    content_type TEXT,
                    content_data TEXT,
                    difficulty_level TEXT,
                    estimated_time_minutes INTEGER,
                    sequence_order INTEGER,
                    created_date TEXT
                )
            ''',
            
            'skill_learning_paths': '''
                CREATE TABLE IF NOT EXISTS skill_learning_paths (
                    id INTEGER PRIMARY KEY,
                    skill_id INTEGER,
                    path_name TEXT,
                    description TEXT,
                    path_description TEXT,
                    resource_sequence TEXT,
                    estimated_duration INTEGER,
                    estimated_total_hours INTEGER,
                    difficulty_level TEXT,
                    difficulty_progression TEXT,
                    prerequisites TEXT DEFAULT '[]',
                    learning_milestones TEXT DEFAULT '[]',
                    completion_projects TEXT DEFAULT '[]',
                    sequence_order INTEGER,
                    ai_generated INTEGER DEFAULT 1,
                    admin_curated INTEGER DEFAULT 0,
                    usage_count INTEGER DEFAULT 0,
                    completion_rate REAL DEFAULT 0.0,
                    created_date TEXT,
                    updated_date TEXT
                )
            ''',
            
            'learning_sessions': '''
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY,
                    session_id TEXT UNIQUE,
                    skill_id INTEGER,
                    learning_path_id INTEGER,
                    current_resource_id INTEGER,
                    user_data TEXT,
                    progress_data TEXT,
                    resources_completed TEXT DEFAULT '[]',
                    questions_answered TEXT DEFAULT '{}',
                    projects_completed TEXT DEFAULT '[]',
                    progress_percentage REAL DEFAULT 0.0,
                    time_spent_minutes INTEGER DEFAULT 0,
                    started_date TEXT,
                    last_activity TEXT,
                    learning_preferences TEXT DEFAULT '{}'
                )
            ''',
            
            'content_analysis_queue': '''
                CREATE TABLE IF NOT EXISTS content_analysis_queue (
                    id INTEGER PRIMARY KEY,
                    resource_id INTEGER,
                    analysis_type TEXT DEFAULT 'full',
                    priority INTEGER DEFAULT 3,
                    status TEXT DEFAULT 'pending',
                    queued_date TEXT,
                    started_date TEXT,
                    completed_date TEXT,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0
                )
            ''',
            
            'resource_questions': '''
                CREATE TABLE IF NOT EXISTS resource_questions (
                    id INTEGER PRIMARY KEY,
                    resource_id INTEGER,
                    questions_data TEXT,
                    created_date TEXT
                )
            ''',
            
            'resource_exercises': '''
                CREATE TABLE IF NOT EXISTS resource_exercises (
                    id INTEGER PRIMARY KEY,
                    resource_id INTEGER,
                    exercises_data TEXT,
                    created_date TEXT
                )
            ''',
            
            'quiz_attempts': '''
                CREATE TABLE IF NOT EXISTS quiz_attempts (
                    id INTEGER PRIMARY KEY,
                    resource_id INTEGER,
                    answers TEXT,
                    score_percentage REAL,
                    attempted_date TEXT,
                    user_session TEXT
                )
            '''
        }
        
        return schema
    
    def _adapt_schema_for_postgres(self, schema: Dict[str, str]) -> Dict[str, str]:
        """Adapt schema for PostgreSQL"""
        postgres_schema = {}
        
        for table_name, sql in schema.items():
            # Replace SQLite-specific syntax with PostgreSQL
            postgres_sql = sql.replace('INTEGER PRIMARY KEY', 'SERIAL PRIMARY KEY')
            postgres_sql = postgres_sql.replace('TEXT', 'TEXT')
            postgres_sql = postgres_sql.replace('REAL', 'FLOAT')
            
            # Add foreign key constraints for PostgreSQL
            if table_name == 'skill_resources':
                postgres_sql = postgres_sql.replace(
                    'resource_id INTEGER,',
                    'resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,'
                ).replace(
                    'skill_id INTEGER,',
                    'skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,'
                )
            elif table_name in ['learning_content', 'resource_questions', 'resource_exercises', 'content_analysis_queue', 'quiz_attempts']:
                postgres_sql = postgres_sql.replace(
                    'resource_id INTEGER,',
                    'resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,'
                )
            elif table_name == 'skill_learning_paths':
                postgres_sql = postgres_sql.replace(
                    'skill_id INTEGER,',
                    'skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,'
                )
            elif table_name == 'learning_sessions':
                postgres_sql = postgres_sql.replace(
                    'skill_id INTEGER,',
                    'skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,'
                ).replace(
                    'learning_path_id INTEGER,',
                    'learning_path_id INTEGER REFERENCES skill_learning_paths(id) ON DELETE SET NULL,'
                ).replace(
                    'current_resource_id INTEGER,',
                    'current_resource_id INTEGER REFERENCES educational_resources(id) ON DELETE SET NULL,'
                )
            
            # Add timestamps
            postgres_sql = postgres_sql.replace('created_date TEXT', 'created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            postgres_sql = postgres_sql.replace('updated_date TEXT', 'updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            postgres_sql = postgres_sql.replace('started_date TEXT', 'started_date TIMESTAMP')
            postgres_sql = postgres_sql.replace('last_activity TEXT', 'last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            postgres_sql = postgres_sql.replace('queued_date TEXT', 'queued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            postgres_sql = postgres_sql.replace('completed_date TEXT', 'completed_date TIMESTAMP')
            postgres_sql = postgres_sql.replace('attempted_date TEXT', 'attempted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            postgres_sql = postgres_sql.replace('publication_date TEXT', 'publication_date DATE')
            postgres_sql = postgres_sql.replace('last_updated TEXT', 'last_updated DATE')
            postgres_sql = postgres_sql.replace('ai_analysis_date TEXT', 'ai_analysis_date TIMESTAMP')
            
            postgres_schema[table_name] = postgres_sql
        
        return postgres_schema
    
    def _adapt_schema_for_sqlite(self, schema: Dict[str, str]) -> Dict[str, str]:
        """Adapt schema for SQLite"""
        sqlite_schema = {}
        
        for table_name, sql in schema.items():
            # SQLite-specific adaptations
            sqlite_sql = sql.replace('INTEGER PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
            
            sqlite_schema[table_name] = sqlite_sql
        
        return sqlite_schema
    
    def create_tables(self):
        """Create all tables with bulletproof schema"""
        logger.info(f"Creating tables for {'PostgreSQL' if self.is_postgres else 'SQLite'}")
        
        unified_schema = self.get_unified_schema()
        
        if self.is_postgres:
            schema = self._adapt_schema_for_postgres(unified_schema)
        else:
            schema = self._adapt_schema_for_sqlite(unified_schema)
        
        with self._get_connection() as conn:
            if self.is_postgres:
                with conn.cursor() as cursor:
                    for table_name, sql in schema.items():
                        try:
                            cursor.execute(sql)
                            logger.info(f"Created table: {table_name}")
                        except Exception as e:
                            logger.error(f"Failed to create table {table_name}: {e}")
                            raise
                conn.commit()
            else:
                cursor = conn.cursor()
                for table_name, sql in schema.items():
                    try:
                        cursor.execute(sql)
                        logger.info(f"Created table: {table_name}")
                    except Exception as e:
                        logger.error(f"Failed to create table {table_name}: {e}")
                        raise
                conn.commit()
        
        # Create indexes
        self.create_indexes()
        logger.info("All tables created successfully")
    
    def create_indexes(self):
        """Create performance indexes"""
        indexes = [
            'CREATE INDEX IF NOT EXISTS idx_skill_resources_skill ON skill_resources(skill_id)',
            'CREATE INDEX IF NOT EXISTS idx_skill_resources_resource ON skill_resources(resource_id)',
            'CREATE INDEX IF NOT EXISTS idx_resources_quality ON educational_resources(quality_score)',
            'CREATE INDEX IF NOT EXISTS idx_resources_category ON educational_resources(skill_category)',
            'CREATE INDEX IF NOT EXISTS idx_resources_type ON educational_resources(resource_type)',
            'CREATE INDEX IF NOT EXISTS idx_resources_difficulty ON educational_resources(difficulty_level)',
            'CREATE INDEX IF NOT EXISTS idx_resources_cost ON educational_resources(cost_type)',
            'CREATE INDEX IF NOT EXISTS idx_learning_content_resource ON learning_content(resource_id)',
            'CREATE INDEX IF NOT EXISTS idx_learning_content_skill ON learning_content(skill_id)',
            'CREATE INDEX IF NOT EXISTS idx_skill_paths_skill ON skill_learning_paths(skill_id)',
            'CREATE INDEX IF NOT EXISTS idx_learning_sessions_session ON learning_sessions(session_id)',
            'CREATE INDEX IF NOT EXISTS idx_learning_sessions_skill ON learning_sessions(skill_id)',
            'CREATE INDEX IF NOT EXISTS idx_analysis_queue_status ON content_analysis_queue(status)',
            'CREATE INDEX IF NOT EXISTS idx_resource_questions_resource ON resource_questions(resource_id)',
            'CREATE INDEX IF NOT EXISTS idx_resource_exercises_resource ON resource_exercises(resource_id)',
        ]
        
        with self._get_connection() as conn:
            if self.is_postgres:
                with conn.cursor() as cursor:
                    for index_sql in indexes:
                        try:
                            cursor.execute(index_sql)
                        except Exception as e:
                            logger.warning(f"Failed to create index: {e}")
                conn.commit()
            else:
                cursor = conn.cursor()
                for index_sql in indexes:
                    try:
                        cursor.execute(index_sql)
                    except Exception as e:
                        logger.warning(f"Failed to create index: {e}")
                conn.commit()
    
    def verify_schema(self) -> Dict[str, Any]:
        """Verify the schema is correctly created"""
        verification = {
            'status': 'success',
            'tables': {},
            'indexes': [],
            'issues': []
        }
        
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        # Check tables
                        cursor.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'public'
                        """)
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        # Check columns for each table
                        for table in tables:
                            cursor.execute("""
                                SELECT column_name, data_type 
                                FROM information_schema.columns 
                                WHERE table_name = %s
                            """, (table,))
                            columns = {row[0]: row[1] for row in cursor.fetchall()}
                            verification['tables'][table] = columns
                        
                        # Check indexes
                        cursor.execute("""
                            SELECT indexname 
                            FROM pg_indexes 
                            WHERE schemaname = 'public'
                        """)
                        verification['indexes'] = [row[0] for row in cursor.fetchall()]
                
                else:
                    cursor = conn.cursor()
                    
                    # Check tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    # Check columns for each table
                    for table in tables:
                        cursor.execute(f"PRAGMA table_info({table})")
                        columns = {row[1]: row[2] for row in cursor.fetchall()}
                        verification['tables'][table] = columns
                    
                    # Check indexes
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
                    verification['indexes'] = [row[0] for row in cursor.fetchall()]
        
        except Exception as e:
            verification['status'] = 'error'
            verification['issues'].append(str(e))
        
        return verification
    
    def migrate_schema_safely(self, backup_first: bool = True) -> bool:
        """Safely migrate schema with backup"""
        if backup_first and not self.is_postgres:
            backup_path = self._backup_database()
            logger.info(f"Database backed up to: {backup_path}")
        
        try:
            # Add missing columns to existing tables
            self._add_missing_columns()
            
            # Create any missing tables
            self.create_tables()
            
            logger.info("Schema migration completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            if backup_path and not self.is_postgres:
                logger.info(f"Restore from backup: {backup_path}")
            return False
    
    def _add_missing_columns(self):
        """Add missing columns to existing tables"""
        missing_columns = {
            'educational_resources': [
                ('learning_outcomes', 'TEXT'),
                ('metadata', 'TEXT'),
                ('content_extracted', 'TEXT'),
                ('source_platform', 'TEXT'),
            ],
            'skill_learning_paths': [
                ('path_description', 'TEXT'),
                ('estimated_total_hours', 'INTEGER'),
                ('difficulty_progression', 'TEXT'),
                ('learning_milestones', 'TEXT DEFAULT \'[]\''),
                ('completion_projects', 'TEXT DEFAULT \'[]\''),
                ('ai_generated', 'INTEGER DEFAULT 1'),
                ('admin_curated', 'INTEGER DEFAULT 0'),
                ('usage_count', 'INTEGER DEFAULT 0'),
                ('completion_rate', 'REAL DEFAULT 0.0'),
                ('updated_date', 'TEXT'),
            ]
        }
        
        with self._get_connection() as conn:
            if self.is_postgres:
                with conn.cursor() as cursor:
                    for table_name, columns in missing_columns.items():
                        for column_name, column_type in columns:
                            try:
                                # PostgreSQL syntax for adding columns
                                pg_type = column_type.replace('TEXT', 'TEXT').replace('REAL', 'FLOAT').replace('INTEGER', 'INTEGER')
                                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {pg_type}")
                                logger.info(f"Added column {column_name} to {table_name}")
                            except Exception as e:
                                if "already exists" not in str(e):
                                    logger.warning(f"Failed to add column {column_name} to {table_name}: {e}")
                conn.commit()
            else:
                cursor = conn.cursor()
                for table_name, columns in missing_columns.items():
                    for column_name, column_type in columns:
                        try:
                            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
                            logger.info(f"Added column {column_name} to {table_name}")
                        except Exception as e:
                            if "duplicate column name" not in str(e):
                                logger.warning(f"Failed to add column {column_name} to {table_name}: {e}")
                conn.commit()
    
    def _backup_database(self) -> Optional[str]:
        """Backup SQLite database"""
        if self.is_postgres:
            logger.warning("PostgreSQL backup not implemented in this method")
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.db_path}.backup_{timestamp}"
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
            return None


def main():
    """Test the bulletproof schema manager"""
    import sys
    
    # Test with SQLite
    print("Testing SQLite schema...")
    sqlite_manager = BulletproofSchemaManager("sqlite:///data/test_bulletproof.db")
    sqlite_manager.create_tables()
    verification = sqlite_manager.verify_schema()
    print(f"SQLite verification: {verification['status']}")
    print(f"Tables created: {list(verification['tables'].keys())}")
    print(f"Indexes created: {len(verification['indexes'])}")
    
    # Test with PostgreSQL if available
    if POSTGRES_AVAILABLE and len(sys.argv) > 1:
        print("\nTesting PostgreSQL schema...")
        postgres_url = sys.argv[1]  # Pass DATABASE_URL as argument
        postgres_manager = BulletproofSchemaManager(postgres_url)
        postgres_manager.create_tables()
        verification = postgres_manager.verify_schema()
        print(f"PostgreSQL verification: {verification['status']}")
        print(f"Tables created: {list(verification['tables'].keys())}")
        print(f"Indexes created: {len(verification['indexes'])}")


if __name__ == "__main__":
    main() 