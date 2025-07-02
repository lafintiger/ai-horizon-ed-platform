#!/usr/bin/env python3
"""
Database Migration Script for Enhanced Learning Experience
Adds new columns and tables to existing database without losing data.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get database path"""
    return 'data/aih_edu.db'

def backup_database():
    """Create backup of existing database"""
    db_path = get_db_path()
    backup_path = f"data/aih_edu_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # Copy database file
    import shutil
    shutil.copy2(db_path, backup_path)
    logger.info(f"Database backed up to: {backup_path}")
    return backup_path

def add_enhanced_columns():
    """Add enhanced columns to educational_resources table"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check existing columns
        cursor.execute("PRAGMA table_info(educational_resources)")
        existing_columns = [col[1] for col in cursor.fetchall()]
        logger.info(f"Existing columns: {existing_columns}")
        
        # Add new columns if they don't exist
        new_columns = [
            ("difficulty_level", "TEXT DEFAULT 'unknown'"),
            ("cost_type", "TEXT DEFAULT 'unknown'"),
            ("estimated_duration", "INTEGER DEFAULT 0"),
            ("learning_objectives", "TEXT DEFAULT '[]'"),
            ("sequence_order", "INTEGER DEFAULT 0"),
            ("ai_analysis_date", "TIMESTAMP"),
            ("admin_reviewed", "BOOLEAN DEFAULT 0"),
            ("content_extracted", "TEXT"),
            ("source_platform", "TEXT")
        ]
        
        for col_name, col_def in new_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE educational_resources ADD COLUMN {col_name} {col_def}")
                    logger.info(f"Added column: {col_name}")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Failed to add column {col_name}: {e}")
        
        conn.commit()

def create_new_tables():
    """Create new learning experience tables"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create learning_content table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_content (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER REFERENCES educational_resources(id),
                skill_id INTEGER REFERENCES emerging_skills(id),
                content_type TEXT NOT NULL,
                content_data TEXT NOT NULL,
                ai_model_used TEXT,
                ai_generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                admin_approved BOOLEAN DEFAULT 0,
                admin_modified TEXT DEFAULT NULL,
                quality_score REAL DEFAULT 0.0,
                usage_count INTEGER DEFAULT 0,
                feedback_rating REAL DEFAULT 0.0,
                FOREIGN KEY (resource_id) REFERENCES educational_resources (id),
                FOREIGN KEY (skill_id) REFERENCES emerging_skills (id)
            )
        ''')
        logger.info("Created learning_content table")
        
        # Create skill_learning_paths table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skill_learning_paths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_id INTEGER REFERENCES emerging_skills(id),
                path_name TEXT NOT NULL,
                path_description TEXT,
                resource_sequence TEXT NOT NULL,
                estimated_duration INTEGER,
                difficulty_progression TEXT,
                prerequisites TEXT DEFAULT '[]',
                learning_milestones TEXT DEFAULT '[]',
                completion_projects TEXT DEFAULT '[]',
                ai_generated BOOLEAN DEFAULT 1,
                admin_curated BOOLEAN DEFAULT 0,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 0,
                completion_rate REAL DEFAULT 0.0,
                FOREIGN KEY (skill_id) REFERENCES emerging_skills (id)
            )
        ''')
        logger.info("Created skill_learning_paths table")
        
        # Create learning_sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                skill_id INTEGER REFERENCES emerging_skills(id),
                learning_path_id INTEGER REFERENCES skill_learning_paths(id),
                current_resource_id INTEGER REFERENCES educational_resources(id),
                resources_completed TEXT DEFAULT '[]',
                questions_answered TEXT DEFAULT '{}',
                projects_completed TEXT DEFAULT '[]',
                progress_percentage REAL DEFAULT 0.0,
                time_spent_minutes INTEGER DEFAULT 0,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                learning_preferences TEXT DEFAULT '{}',
                FOREIGN KEY (skill_id) REFERENCES emerging_skills (id),
                FOREIGN KEY (learning_path_id) REFERENCES skill_learning_paths (id),
                FOREIGN KEY (current_resource_id) REFERENCES educational_resources (id)
            )
        ''')
        logger.info("Created learning_sessions table")
        
        # Create content_analysis_queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_analysis_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER REFERENCES educational_resources(id),
                analysis_type TEXT DEFAULT 'full',
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                queued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_date TIMESTAMP,
                completed_date TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES educational_resources (id)
            )
        ''')
        logger.info("Created content_analysis_queue table")
        
        conn.commit()

def create_enhanced_indexes():
    """Create indexes for enhanced performance"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        indexes = [
            ('idx_resources_difficulty', 'educational_resources(difficulty_level)'),
            ('idx_resources_cost', 'educational_resources(cost_type)'),
            ('idx_resources_sequence', 'educational_resources(sequence_order)'),
            ('idx_resources_ai_analyzed', 'educational_resources(ai_analysis_date)'),
            ('idx_learning_content_resource', 'learning_content(resource_id)'),
            ('idx_learning_content_skill', 'learning_content(skill_id)'),
            ('idx_learning_content_type', 'learning_content(content_type)'),
            ('idx_skill_paths_skill', 'skill_learning_paths(skill_id)'),
            ('idx_learning_sessions_session', 'learning_sessions(session_id)'),
            ('idx_learning_sessions_skill', 'learning_sessions(skill_id)'),
            ('idx_analysis_queue_status', 'content_analysis_queue(status)'),
            ('idx_analysis_queue_priority', 'content_analysis_queue(priority)')
        ]
        
        for index_name, index_def in indexes:
            try:
                cursor.execute(f'CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}')
                logger.info(f"Created index: {index_name}")
            except sqlite3.OperationalError as e:
                logger.warning(f"Failed to create index {index_name}: {e}")
        
        conn.commit()

def populate_enhanced_data():
    """Populate enhanced data for existing resources"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get all resources
        cursor.execute("SELECT id, url, resource_type FROM educational_resources")
        resources = cursor.fetchall()
        
        logger.info(f"Populating enhanced data for {len(resources)} resources...")
        
        for resource_id, url, resource_type in resources:
            # Determine source platform
            source_platform = 'web'
            if 'youtube.com' in url or 'youtu.be' in url:
                source_platform = 'youtube'
            elif 'coursera.org' in url:
                source_platform = 'coursera'
            elif 'udemy.com' in url:
                source_platform = 'udemy'
            elif 'github.com' in url:
                source_platform = 'github'
            elif 'edx.org' in url:
                source_platform = 'edx'
            
            # Determine basic difficulty (will be enhanced by AI later)
            difficulty_level = 'intermediate'  # Default
            if 'beginner' in resource_type.lower() or 'intro' in resource_type.lower():
                difficulty_level = 'beginner'
            elif 'advanced' in resource_type.lower() or 'expert' in resource_type.lower():
                difficulty_level = 'advanced'
            
            # Determine cost type
            cost_type = 'unknown'
            if source_platform in ['youtube', 'github']:
                cost_type = 'free'
            elif source_platform in ['coursera', 'udemy', 'edx']:
                cost_type = 'freemium'  # Often have free content with paid options
            
            # Update resource
            cursor.execute('''
                UPDATE educational_resources 
                SET source_platform = ?, difficulty_level = ?, cost_type = ?
                WHERE id = ?
            ''', (source_platform, difficulty_level, cost_type, resource_id))
        
        conn.commit()
        logger.info("Enhanced data populated for all resources")

def verify_migration():
    """Verify the migration was successful"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check educational_resources columns
        cursor.execute("PRAGMA table_info(educational_resources)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['difficulty_level', 'cost_type', 'source_platform']
        missing_columns = [col for col in required_columns if col not in columns]
        
        if missing_columns:
            logger.error(f"Migration incomplete. Missing columns: {missing_columns}")
            return False
        
        # Check new tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['learning_content', 'skill_learning_paths', 'learning_sessions', 'content_analysis_queue']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            logger.error(f"Migration incomplete. Missing tables: {missing_tables}")
            return False
        
        # Check data integrity
        cursor.execute("SELECT COUNT(*) FROM educational_resources")
        resource_count = cursor.fetchone()[0]
        
        logger.info(f"Migration verification successful!")
        logger.info(f"- Educational resources: {resource_count}")
        logger.info(f"- Enhanced columns: {len(required_columns)} added")
        logger.info(f"- New tables: {len(required_tables)} created")
        
        return True

def main():
    """Run the complete migration"""
    logger.info("Starting database migration for enhanced learning experience...")
    
    try:
        # Step 1: Backup existing database
        backup_path = backup_database()
        
        # Step 2: Add enhanced columns
        add_enhanced_columns()
        
        # Step 3: Create new tables
        create_new_tables()
        
        # Step 4: Create enhanced indexes
        create_enhanced_indexes()
        
        # Step 5: Populate enhanced data
        populate_enhanced_data()
        
        # Step 6: Verify migration
        if verify_migration():
            logger.info("✅ Database migration completed successfully!")
            logger.info(f"📁 Backup saved: {backup_path}")
            logger.info("🚀 Enhanced learning experience ready!")
        else:
            logger.error("❌ Migration verification failed!")
            return 1
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        logger.error(f"Database backup available at: {backup_path if 'backup_path' in locals() else 'N/A'}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 