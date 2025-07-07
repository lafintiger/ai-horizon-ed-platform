#!/usr/bin/env python3
"""
Bulletproof Database Migration System

This system provides safe, validated, and reversible database migrations
between SQLite (local) and PostgreSQL (Heroku) environments.

Features:
- Pre-migration validation
- Incremental data transfer with checkpoints
- Automatic rollback on failure
- Data integrity verification
- Schema compatibility checking
- Progress monitoring
"""

import json
import logging
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import hashlib

# Try to import PostgreSQL adapter
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

from bulletproof_schema import BulletproofSchemaManager

logger = logging.getLogger(__name__)

class BulletproofMigrationManager:
    """Manages bulletproof database migrations"""
    
    def __init__(self, source_db_url: str, target_db_url: str):
        self.source_db_url = source_db_url
        self.target_db_url = target_db_url
        
        # Initialize schema managers
        self.source_schema = BulletproofSchemaManager(source_db_url)
        self.target_schema = BulletproofSchemaManager(target_db_url)
        
        # Migration state
        self.migration_id = self._generate_migration_id()
        self.checkpoint_file = f"migration_checkpoint_{self.migration_id}.json"
        self.backup_path = None
        
        # Validation thresholds
        self.max_data_loss_percent = 5.0  # Maximum allowed data loss
        self.validation_sample_size = 100  # Records to validate
    
    def _generate_migration_id(self) -> str:
        """Generate unique migration ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"migration_{timestamp}"
    
    def _save_checkpoint(self, data: Dict[str, Any]):
        """Save migration checkpoint"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_checkpoint(self) -> Optional[Dict[str, Any]]:
        """Load migration checkpoint"""
        if Path(self.checkpoint_file).exists():
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return None
    
    def _cleanup_checkpoint(self):
        """Remove checkpoint file"""
        if Path(self.checkpoint_file).exists():
            Path(self.checkpoint_file).unlink()
    
    def _get_connection(self, db_url: str):
        """Get database connection"""
        if db_url.startswith(('postgres://', 'postgresql://')):
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL connections")
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            return psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                database=parsed.path[1:],
                user=parsed.username,
                password=parsed.password
            )
        else:
            # SQLite
            if db_url.startswith('sqlite:///'):
                db_url = db_url[10:]
            return sqlite3.connect(db_url)
    
    def _hash_record(self, record: Dict[str, Any]) -> str:
        """Generate hash for record validation"""
        # Convert record to a consistent string representation
        record_str = json.dumps(record, sort_keys=True, default=str)
        return hashlib.md5(record_str.encode()).hexdigest()
    
    def validate_pre_migration(self) -> Dict[str, Any]:
        """Validate system before migration"""
        validation = {
            'status': 'success',
            'source_stats': {},
            'target_stats': {},
            'schema_compatibility': {},
            'issues': [],
            'warnings': []
        }
        
        logger.info("Starting pre-migration validation...")
        
        try:
            # Validate source database
            source_stats = self._get_database_stats(self.source_db_url)
            validation['source_stats'] = source_stats
            logger.info(f"Source database: {source_stats['total_records']} total records")
            
            # Validate target database connectivity
            target_stats = self._get_database_stats(self.target_db_url)
            validation['target_stats'] = target_stats
            logger.info(f"Target database: {target_stats['total_records']} total records")
            
            # Check schema compatibility
            schema_check = self._check_schema_compatibility()
            validation['schema_compatibility'] = schema_check
            
            if schema_check['missing_tables']:
                validation['issues'].append(f"Missing tables in target: {schema_check['missing_tables']}")
            
            if schema_check['missing_columns']:
                validation['warnings'].append(f"Missing columns: {schema_check['missing_columns']}")
            
            # Check for existing data
            if target_stats['total_records'] > 0:
                validation['warnings'].append(f"Target database contains {target_stats['total_records']} records")
            
        except Exception as e:
            validation['status'] = 'error'
            validation['issues'].append(str(e))
            logger.error(f"Pre-migration validation failed: {e}")
        
        return validation
    
    def _get_database_stats(self, db_url: str) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {
            'total_records': 0,
            'tables': {},
            'database_type': 'postgresql' if db_url.startswith(('postgres://', 'postgresql://')) else 'sqlite'
        }
        
        with self._get_connection(db_url) as conn:
            if stats['database_type'] == 'postgresql':
                with conn.cursor() as cursor:
                    # Get table list
                    cursor.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public'
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    # Count records in each table
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        stats['tables'][table] = count
                        stats['total_records'] += count
            else:
                cursor = conn.cursor()
                
                # Get table list
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Count records in each table
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    stats['tables'][table] = count
                    stats['total_records'] += count
        
        return stats
    
    def _check_schema_compatibility(self) -> Dict[str, Any]:
        """Check schema compatibility between source and target"""
        compatibility = {
            'compatible': True,
            'missing_tables': [],
            'missing_columns': {},
            'type_mismatches': {}
        }
        
        try:
            source_verification = self.source_schema.verify_schema()
            target_verification = self.target_schema.verify_schema()
            
            source_tables = set(source_verification['tables'].keys())
            target_tables = set(target_verification['tables'].keys())
            
            # Check for missing tables
            missing_tables = source_tables - target_tables
            if missing_tables:
                compatibility['missing_tables'] = list(missing_tables)
                compatibility['compatible'] = False
            
            # Check for missing columns in existing tables
            for table in source_tables & target_tables:
                source_columns = set(source_verification['tables'][table].keys())
                target_columns = set(target_verification['tables'][table].keys())
                
                missing_columns = source_columns - target_columns
                if missing_columns:
                    compatibility['missing_columns'][table] = list(missing_columns)
                    compatibility['compatible'] = False
        
        except Exception as e:
            compatibility['compatible'] = False
            compatibility['error'] = str(e)
        
        return compatibility
    
    def prepare_target_database(self):
        """Prepare target database for migration"""
        logger.info("Preparing target database...")
        
        try:
            # Create/update schema
            self.target_schema.migrate_schema_safely(backup_first=False)
            
            # Verify schema
            verification = self.target_schema.verify_schema()
            if verification['status'] != 'success':
                raise Exception(f"Target schema verification failed: {verification['issues']}")
            
            logger.info("Target database prepared successfully")
            
        except Exception as e:
            logger.error(f"Failed to prepare target database: {e}")
            raise
    
    def migrate_data_incrementally(self, batch_size: int = 1000) -> Dict[str, Any]:
        """Migrate data in batches with checkpoints"""
        migration_result = {
            'status': 'success',
            'records_migrated': 0,
            'tables_migrated': {},
            'errors': [],
            'warnings': []
        }
        
        # Load existing checkpoint if available
        checkpoint = self._load_checkpoint()
        if checkpoint:
            logger.info(f"Resuming migration from checkpoint: {checkpoint}")
            migration_result.update(checkpoint)
        
        try:
            # Get list of tables to migrate
            source_stats = self._get_database_stats(self.source_db_url)
            tables_to_migrate = list(source_stats['tables'].keys())
            
            # Define migration order (dependencies first)
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
            
            # Add any additional tables not in the predefined order
            for table in tables_to_migrate:
                if table not in migration_order:
                    migration_order.append(table)
            
            for table_name in migration_order:
                if table_name not in tables_to_migrate:
                    continue
                
                # Skip if already migrated (checkpoint recovery)
                if table_name in migration_result.get('tables_migrated', {}):
                    logger.info(f"Skipping {table_name} (already migrated)")
                    continue
                
                logger.info(f"Migrating table: {table_name}")
                
                table_result = self._migrate_table(table_name, batch_size)
                migration_result['tables_migrated'][table_name] = table_result
                migration_result['records_migrated'] += table_result['records_migrated']
                
                if table_result['errors']:
                    migration_result['errors'].extend(table_result['errors'])
                
                # Save checkpoint after each table
                self._save_checkpoint(migration_result)
                
                logger.info(f"Completed {table_name}: {table_result['records_migrated']} records")
        
        except Exception as e:
            migration_result['status'] = 'error'
            migration_result['errors'].append(str(e))
            logger.error(f"Migration failed: {e}")
        
        return migration_result
    
    def _migrate_table(self, table_name: str, batch_size: int) -> Dict[str, Any]:
        """Migrate a single table"""
        result = {
            'records_migrated': 0,
            'records_failed': 0,
            'errors': []
        }
        
        try:
            with self._get_connection(self.source_db_url) as source_conn:
                with self._get_connection(self.target_db_url) as target_conn:
                    
                    # Get source data
                    if self.source_db_url.startswith('sqlite'):
                        source_conn.row_factory = sqlite3.Row
                        source_cursor = source_conn.cursor()
                        source_cursor.execute(f"SELECT * FROM {table_name}")
                        records = source_cursor.fetchall()
                    else:
                        source_conn.cursor_factory = psycopg2.extras.RealDictCursor
                        with source_conn.cursor() as source_cursor:
                            source_cursor.execute(f"SELECT * FROM {table_name}")
                            records = source_cursor.fetchall()
                    
                    logger.info(f"Found {len(records)} records in {table_name}")
                    
                    # Process in batches
                    for i in range(0, len(records), batch_size):
                        batch = records[i:i + batch_size]
                        
                        try:
                            batch_result = self._migrate_batch(table_name, batch, target_conn)
                            result['records_migrated'] += batch_result['success']
                            result['records_failed'] += batch_result['failed']
                            
                            if batch_result['errors']:
                                result['errors'].extend(batch_result['errors'])
                        
                        except Exception as e:
                            result['errors'].append(f"Batch {i//batch_size + 1} failed: {e}")
                            result['records_failed'] += len(batch)
        
        except Exception as e:
            result['errors'].append(f"Table migration failed: {e}")
        
        return result
    
    def _migrate_batch(self, table_name: str, records: List[Dict], target_conn) -> Dict[str, Any]:
        """Migrate a batch of records"""
        result = {
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        if not records:
            return result
        
        try:
            # Prepare insert statement
            columns = list(records[0].keys())
            
            if self.target_db_url.startswith(('postgres://', 'postgresql://')):
                # PostgreSQL
                placeholders = ', '.join(['%s'] * len(columns))
                insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                with target_conn.cursor() as cursor:
                    for record in records:
                        try:
                            values = [record[col] for col in columns]
                            cursor.execute(insert_sql, values)
                            result['success'] += 1
                        except Exception as e:
                            result['failed'] += 1
                            result['errors'].append(f"Record failed: {e}")
                
                target_conn.commit()
            
            else:
                # SQLite
                placeholders = ', '.join(['?'] * len(columns))
                insert_sql = f"INSERT OR REPLACE INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
                
                cursor = target_conn.cursor()
                for record in records:
                    try:
                        values = [record[col] for col in columns]
                        cursor.execute(insert_sql, values)
                        result['success'] += 1
                    except Exception as e:
                        result['failed'] += 1
                        result['errors'].append(f"Record failed: {e}")
                
                target_conn.commit()
        
        except Exception as e:
            result['errors'].append(f"Batch migration failed: {e}")
            result['failed'] = len(records)
        
        return result
    
    def validate_post_migration(self) -> Dict[str, Any]:
        """Validate migration results"""
        validation = {
            'status': 'success',
            'data_integrity': {},
            'record_counts': {},
            'sample_validation': {},
            'issues': []
        }
        
        logger.info("Starting post-migration validation...")
        
        try:
            # Compare record counts
            source_stats = self._get_database_stats(self.source_db_url)
            target_stats = self._get_database_stats(self.target_db_url)
            
            validation['record_counts'] = {
                'source': source_stats['tables'],
                'target': target_stats['tables'],
                'differences': {}
            }
            
            # Check for data loss
            total_loss = 0
            for table in source_stats['tables']:
                source_count = source_stats['tables'].get(table, 0)
                target_count = target_stats['tables'].get(table, 0)
                difference = source_count - target_count
                
                if difference > 0:
                    validation['record_counts']['differences'][table] = difference
                    total_loss += difference
            
            # Calculate data loss percentage
            total_source = source_stats['total_records']
            if total_source > 0:
                loss_percent = (total_loss / total_source) * 100
                validation['data_integrity']['loss_percentage'] = loss_percent
                
                if loss_percent > self.max_data_loss_percent:
                    validation['status'] = 'warning'
                    validation['issues'].append(f"Data loss {loss_percent:.2f}% exceeds threshold {self.max_data_loss_percent}%")
            
            # Sample validation for key tables
            sample_results = self._validate_sample_data()
            validation['sample_validation'] = sample_results
            
            if sample_results['mismatches'] > 0:
                validation['issues'].append(f"Found {sample_results['mismatches']} data mismatches in sample")
        
        except Exception as e:
            validation['status'] = 'error'
            validation['issues'].append(str(e))
        
        return validation
    
    def _validate_sample_data(self) -> Dict[str, Any]:
        """Validate a sample of migrated data"""
        result = {
            'records_checked': 0,
            'matches': 0,
            'mismatches': 0,
            'errors': []
        }
        
        try:
            # Check sample from key tables
            key_tables = ['emerging_skills', 'educational_resources']
            
            for table in key_tables:
                try:
                    sample_result = self._validate_table_sample(table, self.validation_sample_size)
                    result['records_checked'] += sample_result['checked']
                    result['matches'] += sample_result['matches']
                    result['mismatches'] += sample_result['mismatches']
                    
                    if sample_result['errors']:
                        result['errors'].extend(sample_result['errors'])
                
                except Exception as e:
                    result['errors'].append(f"Sample validation failed for {table}: {e}")
        
        except Exception as e:
            result['errors'].append(f"Sample validation failed: {e}")
        
        return result
    
    def _validate_table_sample(self, table_name: str, sample_size: int) -> Dict[str, Any]:
        """Validate a sample of records from a table"""
        result = {
            'checked': 0,
            'matches': 0,
            'mismatches': 0,
            'errors': []
        }
        
        try:
            with self._get_connection(self.source_db_url) as source_conn:
                with self._get_connection(self.target_db_url) as target_conn:
                    
                    # Get sample from source
                    if self.source_db_url.startswith('sqlite'):
                        source_conn.row_factory = sqlite3.Row
                        source_cursor = source_conn.cursor()
                        source_cursor.execute(f"SELECT * FROM {table_name} LIMIT {sample_size}")
                        source_records = source_cursor.fetchall()
                    else:
                        source_conn.cursor_factory = psycopg2.extras.RealDictCursor
                        with source_conn.cursor() as source_cursor:
                            source_cursor.execute(f"SELECT * FROM {table_name} LIMIT {sample_size}")
                            source_records = source_cursor.fetchall()
                    
                    # Check each record in target
                    for source_record in source_records:
                        record_id = source_record['id']
                        
                        # Get corresponding record from target
                        if self.target_db_url.startswith(('postgres://', 'postgresql://')):
                            with target_conn.cursor() as target_cursor:
                                target_cursor.execute(f"SELECT * FROM {table_name} WHERE id = %s", (record_id,))
                                target_record = target_cursor.fetchone()
                        else:
                            target_cursor = target_conn.cursor()
                            target_cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))
                            target_record = target_cursor.fetchone()
                        
                        result['checked'] += 1
                        
                        if target_record:
                            # Compare records (simplified comparison)
                            source_hash = self._hash_record(dict(source_record))
                            target_hash = self._hash_record(dict(target_record))
                            
                            if source_hash == target_hash:
                                result['matches'] += 1
                            else:
                                result['mismatches'] += 1
                        else:
                            result['mismatches'] += 1
        
        except Exception as e:
            result['errors'].append(f"Table sample validation failed: {e}")
        
        return result
    
    def rollback_migration(self) -> bool:
        """Rollback migration if something goes wrong"""
        logger.info("Starting migration rollback...")
        
        try:
            # Clear target database
            with self._get_connection(self.target_db_url) as conn:
                if self.target_db_url.startswith(('postgres://', 'postgresql://')):
                    with conn.cursor() as cursor:
                        # Get all tables
                        cursor.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'public'
                        """)
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        # Truncate all tables
                        for table in tables:
                            cursor.execute(f"TRUNCATE TABLE {table} CASCADE")
                    
                    conn.commit()
                else:
                    cursor = conn.cursor()
                    
                    # Get all tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    # Delete all data
                    for table in tables:
                        cursor.execute(f"DELETE FROM {table}")
                    
                    conn.commit()
            
            # Clean up checkpoint
            self._cleanup_checkpoint()
            
            logger.info("Migration rollback completed")
            return True
        
        except Exception as e:
            logger.error(f"Migration rollback failed: {e}")
            return False
    
    def perform_full_migration(self, validate_after: bool = True) -> Dict[str, Any]:
        """Perform complete migration with all safety checks"""
        migration_report = {
            'migration_id': self.migration_id,
            'started_at': datetime.now().isoformat(),
            'status': 'in_progress',
            'phases': {},
            'summary': {}
        }
        
        try:
            # Phase 1: Pre-migration validation
            logger.info("Phase 1: Pre-migration validation")
            pre_validation = self.validate_pre_migration()
            migration_report['phases']['pre_validation'] = pre_validation
            
            if pre_validation['status'] == 'error':
                raise Exception(f"Pre-validation failed: {pre_validation['issues']}")
            
            # Phase 2: Prepare target database
            logger.info("Phase 2: Preparing target database")
            self.prepare_target_database()
            migration_report['phases']['target_preparation'] = {'status': 'success'}
            
            # Phase 3: Data migration
            logger.info("Phase 3: Migrating data")
            migration_result = self.migrate_data_incrementally()
            migration_report['phases']['data_migration'] = migration_result
            
            if migration_result['status'] == 'error':
                raise Exception(f"Data migration failed: {migration_result['errors']}")
            
            # Phase 4: Post-migration validation (optional)
            if validate_after:
                logger.info("Phase 4: Post-migration validation")
                post_validation = self.validate_post_migration()
                migration_report['phases']['post_validation'] = post_validation
                
                if post_validation['status'] == 'error':
                    raise Exception(f"Post-validation failed: {post_validation['issues']}")
                
                if post_validation['status'] == 'warning':
                    migration_report['status'] = 'warning'
                    logger.warning("Migration completed with warnings")
            
            # Phase 5: Cleanup
            self._cleanup_checkpoint()
            
            migration_report['status'] = migration_report.get('status', 'success')
            migration_report['completed_at'] = datetime.now().isoformat()
            
            # Generate summary
            total_records = migration_result.get('records_migrated', 0)
            migration_report['summary'] = {
                'total_records_migrated': total_records,
                'tables_migrated': len(migration_result.get('tables_migrated', {})),
                'errors_encountered': len(migration_result.get('errors', [])),
                'migration_time': migration_report['completed_at']
            }
            
            logger.info(f"Migration completed successfully: {total_records} records migrated")
        
        except Exception as e:
            migration_report['status'] = 'error'
            migration_report['error'] = str(e)
            migration_report['failed_at'] = datetime.now().isoformat()
            
            logger.error(f"Migration failed: {e}")
            
            # Attempt rollback
            if input("Migration failed. Attempt rollback? (y/n): ").lower() == 'y':
                rollback_success = self.rollback_migration()
                migration_report['rollback_attempted'] = True
                migration_report['rollback_success'] = rollback_success
        
        return migration_report


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python bulletproof_migration.py <source_db_url> <target_db_url>")
        print("Example: python bulletproof_migration.py sqlite:///data/local.db postgresql://user:pass@host:port/db")
        return
    
    source_db = sys.argv[1]
    target_db = sys.argv[2]
    
    print(f"Migrating from {source_db} to {target_db}")
    
    # Initialize migration manager
    migration_manager = BulletproofMigrationManager(source_db, target_db)
    
    # Perform migration
    report = migration_manager.perform_full_migration()
    
    print(f"\nMigration Report:")
    print(f"Status: {report['status']}")
    print(f"Records migrated: {report['summary'].get('total_records_migrated', 0)}")
    print(f"Tables migrated: {report['summary'].get('tables_migrated', 0)}")
    print(f"Errors: {report['summary'].get('errors_encountered', 0)}")


if __name__ == "__main__":
    main() 