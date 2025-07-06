#!/usr/bin/env python3
"""
Database Schema Migration Script for AI-Horizon Ed Platform
Safely migrates from old schema to new schema without data loss
"""

import sqlite3
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseMigrator:
    def __init__(self, db_path: str = "data/aih_edu.db"):
        self.db_path = db_path
        self.backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def backup_database(self):
        """Create a backup of the current database"""
        try:
            if os.path.exists(self.db_path):
                shutil.copy2(self.db_path, self.backup_path)
                logger.info(f"✅ Database backed up to: {self.backup_path}")
                return True
            else:
                logger.info("ℹ️ No existing database to backup")
                return True
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return False
    
    def check_schema_version(self):
        """Check which schema version we're dealing with"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if the table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='educational_resources'")
                if not cursor.fetchone():
                    logger.info("ℹ️ No educational_resources table found - fresh database")
                    return "fresh"
                
                # Check for old schema indicators
                cursor.execute("PRAGMA table_info(educational_resources)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'duration_minutes' in columns and 'popularity_score' in columns:
                    logger.info("🔍 Detected OLD schema")
                    return "old"
                elif 'tags' in columns and 'cost_type' in columns:
                    logger.info("🔍 Detected NEW schema")
                    return "new"
                else:
                    logger.info("🔍 Detected MIXED schema - needs migration")
                    return "mixed"
                    
        except Exception as e:
            logger.error(f"❌ Schema check failed: {e}")
            return "unknown"
    
    def migrate_data(self):
        """Migrate data from old schema to new schema"""
        try:
            # Check current schema
            schema_version = self.check_schema_version()
            
            if schema_version == "new":
                logger.info("✅ Database already has correct schema")
                return True
            
            if schema_version == "fresh":
                logger.info("✅ Fresh database - will be initialized with correct schema")
                return True
                
            # Backup first
            if not self.backup_database():
                return False
            
            logger.info("🔄 Starting schema migration...")
            
            # Extract existing data
            old_data = self.extract_existing_data()
            
            # Create new database with correct schema
            self.create_new_schema()
            
            # Migrate data to new schema
            self.migrate_to_new_schema(old_data)
            
            logger.info("🎉 Schema migration completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            # Restore backup if available
            if os.path.exists(self.backup_path):
                shutil.copy2(self.backup_path, self.db_path)
                logger.info("🔄 Database restored from backup")
            return False
    
    def extract_existing_data(self):
        """Extract data from old schema database"""
        data = {'skills': [], 'resources': [], 'mappings': []}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Extract skills
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='emerging_skills'")
                if cursor.fetchone():
                    cursor.execute("SELECT * FROM emerging_skills")
                    for row in cursor.fetchall():
                        skill_data = dict(row)
                        # Parse JSON fields
                        if skill_data.get('job_market_data'):
                            skill_data['job_market_data'] = json.loads(skill_data['job_market_data'])
                        if skill_data.get('related_skills'):
                            skill_data['related_skills'] = json.loads(skill_data['related_skills'])
                        data['skills'].append(skill_data)
                
                # Extract resources
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='educational_resources'")
                if cursor.fetchone():
                    cursor.execute("SELECT * FROM educational_resources")
                    for row in cursor.fetchall():
                        resource_data = dict(row)
                        # Map old fields to new fields
                        migrated_resource = self.map_old_to_new_resource(resource_data)
                        data['resources'].append(migrated_resource)
                
                # Extract mappings
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='skill_resources'")
                if cursor.fetchone():
                    cursor.execute("SELECT * FROM skill_resources")
                    for row in cursor.fetchall():
                        data['mappings'].append(dict(row))
                
        except Exception as e:
            logger.error(f"❌ Data extraction failed: {e}")
            
        logger.info(f"📊 Extracted {len(data['skills'])} skills, {len(data['resources'])} resources, {len(data['mappings'])} mappings")
        return data
    
    def map_old_to_new_resource(self, old_resource: Dict) -> Dict:
        """Map old resource schema to new resource schema"""
        new_resource = {
            'title': old_resource.get('title', ''),
            'description': old_resource.get('description', ''),
            'url': old_resource.get('url', ''),
            'resource_type': old_resource.get('resource_type', 'unknown'),
            'cost_type': 'free',  # Default
            'difficulty_level': 'intermediate',  # Default
            'estimated_duration': f"{old_resource.get('duration_minutes', 30)} minutes",
            'author': old_resource.get('author', ''),
            'tags': old_resource.get('keywords', ''),
            'skill_category': old_resource.get('skill_category', ''),
            'quality_score': old_resource.get('quality_score', 0.0),
            'discovery_method': 'migration',
            'learning_level': old_resource.get('learning_level', 'intermediate'),
            'prerequisites': [],
            'learning_objectives': []
        }
        
        # Handle metadata JSON field
        if old_resource.get('metadata'):
            try:
                metadata = json.loads(old_resource['metadata'])
                new_resource.update(metadata)
            except:
                pass
        
        return new_resource
    
    def create_new_schema(self):
        """Create database with correct new schema"""
        # Remove old database
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Initialize with new schema using DatabaseManager
        from utils.database import DatabaseManager
        db_manager = DatabaseManager(self.db_path)
        logger.info("✅ Created new database with correct schema")
    
    def migrate_to_new_schema(self, old_data: Dict):
        """Insert old data into new schema"""
        from utils.database import DatabaseManager
        db_manager = DatabaseManager(self.db_path)
        
        # Add skills
        skill_id_mapping = {}
        for skill_data in old_data['skills']:
            try:
                skill_id = db_manager.add_emerging_skill(skill_data)
                skill_id_mapping[skill_data.get('id')] = skill_id
                logger.info(f"✅ Migrated skill: {skill_data['skill_name']}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to migrate skill {skill_data['skill_name']}: {e}")
        
        # Add resources
        resource_id_mapping = {}
        for resource_data in old_data['resources']:
            try:
                resource_id = db_manager.add_resource(resource_data)
                if resource_id:
                    resource_id_mapping[resource_data.get('id')] = resource_id
                    logger.info(f"✅ Migrated resource: {resource_data['title']}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to migrate resource {resource_data['title']}: {e}")
        
        # Add mappings
        for mapping in old_data['mappings']:
            try:
                old_skill_id = mapping.get('skill_id')
                old_resource_id = mapping.get('resource_id')
                
                new_skill_id = skill_id_mapping.get(old_skill_id)
                new_resource_id = resource_id_mapping.get(old_resource_id)
                
                if new_skill_id and new_resource_id:
                    db_manager.link_skill_to_resource(
                        new_skill_id, 
                        new_resource_id, 
                        mapping.get('relevance_score', 1.0)
                    )
                    logger.info(f"✅ Migrated mapping: skill {new_skill_id} -> resource {new_resource_id}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to migrate mapping: {e}")

def main():
    """Main migration function"""
    logger.info("🚀 Starting Database Schema Migration")
    
    # Ensure data directory exists
    Path("data").mkdir(parents=True, exist_ok=True)
    
    # Create migrator and run migration
    migrator = DatabaseMigrator()
    
    if migrator.migrate_data():
        logger.info("🎉 Database migration completed successfully!")
        logger.info(f"💾 Backup saved to: {migrator.backup_path}")
        logger.info("✅ Your database is now ready for deployment!")
        return True
    else:
        logger.error("❌ Database migration failed!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 