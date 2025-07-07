#!/usr/bin/env python3
"""
Setup Local PostgreSQL Database for AI-Horizon Ed Platform

This script creates a local PostgreSQL database with the same schema as SQLite
and optionally migrates the data. It's designed to be non-destructive - the 
SQLite database remains untouched.
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import sqlite3

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bulletproof_schema import BulletproofSchemaManager
from utils.config import config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LocalPostgresSetup:
    """Setup and manage local PostgreSQL database"""
    
    def __init__(self):
        # Get current user for database connection
        self.current_user = os.getenv('USER', 'postgres')
        
        # PostgreSQL connection details
        self.postgres_url = f"postgresql://{self.current_user}@localhost:5432/aih_edu_local"
        
        # SQLite database path
        self.sqlite_path = "data/aih_edu.db"
        
        # Initialize schema managers
        self.postgres_manager = None
        self.sqlite_manager = None
        
    def test_postgres_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            logger.info("Testing PostgreSQL connection...")
            self.postgres_manager = BulletproofSchemaManager(self.postgres_url)
            
            # Test connection
            with self.postgres_manager._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result and result[0] == 1:
                        logger.info("✅ PostgreSQL connection successful!")
                        return True
                    else:
                        logger.error("❌ PostgreSQL connection test failed")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection failed: {e}")
            return False
    
    def test_sqlite_connection(self) -> bool:
        """Test SQLite connection"""
        try:
            logger.info("Testing SQLite connection...")
            
            if not os.path.exists(self.sqlite_path):
                logger.warning(f"⚠️ SQLite database not found at {self.sqlite_path}")
                return False
                
            self.sqlite_manager = BulletproofSchemaManager(f"sqlite:///{self.sqlite_path}")
            
            # Test connection
            with self.sqlite_manager._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    logger.info("✅ SQLite connection successful!")
                    return True
                else:
                    logger.error("❌ SQLite connection test failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ SQLite connection failed: {e}")
            return False
    
    def create_postgres_schema(self) -> bool:
        """Create PostgreSQL schema using BulletproofSchemaManager"""
        try:
            logger.info("Creating PostgreSQL schema...")
            
            if not self.postgres_manager:
                logger.error("❌ PostgreSQL manager not initialized")
                return False
            
            # Create tables
            self.postgres_manager.create_tables()
            
            # Verify schema
            verification = self.postgres_manager.verify_schema()
            
            if verification['status'] == 'success':
                logger.info("✅ PostgreSQL schema created successfully!")
                logger.info(f"   Tables: {list(verification['tables'].keys())}")
                logger.info(f"   Indexes: {len(verification['indexes'])}")
                return True
            else:
                logger.error("❌ PostgreSQL schema verification failed")
                logger.error(f"   Status: {verification['status']}")
                logger.error(f"   Issues: {verification['issues']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ PostgreSQL schema creation failed: {e}")
            return False
    
    def get_sqlite_data(self) -> Dict[str, List[Dict]]:
        """Extract data from SQLite database"""
        data = {}
        
        try:
            logger.info("Extracting data from SQLite database...")
            
            with sqlite3.connect(self.sqlite_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                for table in tables:
                    logger.info(f"  Extracting data from table: {table}")
                    cursor.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    
                    table_data = []
                    for row in rows:
                        table_data.append(dict(row))
                    
                    data[table] = table_data
                    logger.info(f"    Found {len(table_data)} rows")
            
            return data
            
        except Exception as e:
            logger.error(f"❌ SQLite data extraction failed: {e}")
            return {}
    
    def migrate_data_to_postgres(self, data: Dict[str, List[Dict]]) -> bool:
        """Migrate data from SQLite to PostgreSQL"""
        try:
            logger.info("Migrating data to PostgreSQL...")
            
            # Table migration order (respecting foreign keys)
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
                'quiz_attempts'
            ]
            
            with self.postgres_manager._get_connection() as conn:
                with conn.cursor() as cursor:
                    
                    for table_name in migration_order:
                        if table_name in data and data[table_name]:
                            logger.info(f"  Migrating {table_name} ({len(data[table_name])} rows)")
                            
                            # Get table structure
                            cursor.execute(f"""
                                SELECT column_name 
                                FROM information_schema.columns 
                                WHERE table_name = '{table_name}'
                                ORDER BY ordinal_position
                            """)
                            columns = [row[0] for row in cursor.fetchall()]
                            
                            # Filter data to match PostgreSQL columns
                            for row in data[table_name]:
                                # Convert dates and handle None values
                                filtered_row = {}
                                for col in columns:
                                    if col in row:
                                        value = row[col]
                                        # Handle timestamp conversion
                                        if col.endswith('_date') or col.endswith('_activity'):
                                            if value and value != '':
                                                # Keep the value as string, PostgreSQL will convert
                                                filtered_row[col] = value
                                            else:
                                                filtered_row[col] = None
                                        else:
                                            filtered_row[col] = value
                                
                                # Skip id column (it's auto-generated)
                                if 'id' in filtered_row:
                                    del filtered_row['id']
                                
                                if filtered_row:  # Only insert if there's data
                                    # Build insert query
                                    cols = list(filtered_row.keys())
                                    placeholders = ', '.join(['%s'] * len(cols))
                                    insert_query = f"""
                                        INSERT INTO {table_name} ({', '.join(cols)})
                                        VALUES ({placeholders})
                                    """
                                    
                                    try:
                                        cursor.execute(insert_query, list(filtered_row.values()))
                                    except Exception as e:
                                        logger.warning(f"    Failed to insert row in {table_name}: {e}")
                                        continue
                            
                            logger.info(f"    ✅ {table_name} migration completed")
                
                conn.commit()
                logger.info("✅ Data migration completed successfully!")
                return True
                
        except Exception as e:
            logger.error(f"❌ Data migration failed: {e}")
            return False
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of data in both databases"""
        summary = {
            'sqlite': {},
            'postgres': {}
        }
        
        try:
            # SQLite summary
            if os.path.exists(self.sqlite_path):
                with sqlite3.connect(self.sqlite_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        summary['sqlite'][table] = count
            
            # PostgreSQL summary
            if self.postgres_manager:
                with self.postgres_manager._get_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'public'
                        """)
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        for table in tables:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            summary['postgres'][table] = count
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ Data summary failed: {e}")
            return summary
    
    def setup_complete_postgres(self) -> bool:
        """Complete setup process"""
        logger.info("🚀 Starting Local PostgreSQL Setup for AI-Horizon Ed")
        logger.info("=" * 60)
        
        # Step 1: Test connections
        logger.info("Step 1: Testing database connections...")
        if not self.test_postgres_connection():
            return False
        
        if not self.test_sqlite_connection():
            logger.warning("⚠️ SQLite database not available - will create empty PostgreSQL schema")
            
        # Step 2: Create PostgreSQL schema
        logger.info("\nStep 2: Creating PostgreSQL schema...")
        if not self.create_postgres_schema():
            return False
        
        # Step 3: Migrate data (if SQLite exists)
        if self.sqlite_manager:
            logger.info("\nStep 3: Migrating data from SQLite to PostgreSQL...")
            data = self.get_sqlite_data()
            if data:
                if not self.migrate_data_to_postgres(data):
                    logger.warning("⚠️ Data migration failed, but PostgreSQL schema is ready")
            else:
                logger.info("ℹ️ No data found in SQLite database")
        
        # Step 4: Summary
        logger.info("\nStep 4: Final summary...")
        summary = self.get_data_summary()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 LOCAL POSTGRESQL SETUP COMPLETE!")
        logger.info("=" * 60)
        
        logger.info("\nDatabase URL for local PostgreSQL:")
        logger.info(f"  {self.postgres_url}")
        
        logger.info("\nData Summary:")
        logger.info("  SQLite (Original):")
        for table, count in summary['sqlite'].items():
            logger.info(f"    {table}: {count} rows")
        
        logger.info("  PostgreSQL (New):")
        for table, count in summary['postgres'].items():
            logger.info(f"    {table}: {count} rows")
        
        logger.info("\nNext Steps:")
        logger.info("  1. Test your application with PostgreSQL:")
        logger.info(f"     export DATABASE_URL='{self.postgres_url}'")
        logger.info("     python app.py")
        logger.info("  2. If successful, consider using PostgreSQL for development")
        logger.info("  3. Your original SQLite database remains untouched")
        
        return True

def main():
    """Main function"""
    setup = LocalPostgresSetup()
    
    try:
        success = setup.setup_complete_postgres()
        if success:
            print("\n✅ Setup completed successfully!")
            print(f"PostgreSQL URL: {setup.postgres_url}")
            return 0
        else:
            print("\n❌ Setup failed!")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    exit(main()) 