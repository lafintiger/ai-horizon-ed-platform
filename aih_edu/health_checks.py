#!/usr/bin/env python3
"""
Comprehensive Health Check System for AI-Horizon Ed Platform

This module provides extensive health monitoring and validation
for the platform, ensuring all components are functioning correctly.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Database and app imports
try:
    from utils.database import DatabaseManager
    from utils.config import config
except ImportError:
    # Handle imports when running from different directories
    import sys
    sys.path.append(str(Path(__file__).parent))
    try:
        from utils.database import DatabaseManager
        from utils.config import config
    except ImportError:
        print("Warning: Could not import database modules. Health checks will be limited.")
        DatabaseManager = None
        config = None

logger = logging.getLogger(__name__)

class HealthCheckManager:
    """Manages comprehensive health checks for the platform"""
    
    def __init__(self):
        self.checks = {}
        self.db_manager = None
        if DatabaseManager:
            try:
                self.db_manager = DatabaseManager()
            except Exception as e:
                logger.warning(f"Could not initialize database manager: {e}")
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'summary': {},
            'issues': [],
            'warnings': []
        }
        
        # Define all checks to run
        check_functions = [
            ('database_connectivity', self.check_database_connectivity),
            ('database_schema', self.check_database_schema),
            ('database_data_integrity', self.check_database_data_integrity),
            ('environment_variables', self.check_environment_variables),
            ('file_system', self.check_file_system),
            ('dependencies', self.check_dependencies),
            ('api_endpoints', self.check_api_endpoints),
            ('memory_usage', self.check_memory_usage),
            ('disk_space', self.check_disk_space)
        ]
        
        # Run each check
        for check_name, check_function in check_functions:
            try:
                logger.info(f"Running health check: {check_name}")
                check_result = check_function()
                health_report['checks'][check_name] = check_result
                
                # Aggregate issues and warnings
                if check_result.get('status') == 'failed':
                    health_report['overall_status'] = 'unhealthy'
                    health_report['issues'].extend(check_result.get('issues', []))
                elif check_result.get('status') == 'warning':
                    if health_report['overall_status'] == 'healthy':
                        health_report['overall_status'] = 'degraded'
                    health_report['warnings'].extend(check_result.get('warnings', []))
                
            except Exception as e:
                logger.error(f"Health check {check_name} failed with exception: {e}")
                health_report['checks'][check_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'issues': [f"Health check crashed: {e}"]
                }
                health_report['overall_status'] = 'unhealthy'
                health_report['issues'].append(f"Health check {check_name} crashed: {e}")
        
        # Generate summary
        health_report['summary'] = self._generate_summary(health_report['checks'])
        
        return health_report
    
    def check_database_connectivity(self) -> Dict[str, Any]:
        """Check database connectivity and basic operations"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        if not self.db_manager:
            check_result['status'] = 'failed'
            check_result['issues'].append("Database manager not available")
            return check_result
        
        try:
            # Test basic connectivity
            start_time = time.time()
            stats = self.db_manager.get_resource_stats()
            connection_time = time.time() - start_time
            
            check_result['details']['connection_time_ms'] = round(connection_time * 1000, 2)
            check_result['details']['database_type'] = 'postgresql' if hasattr(self.db_manager, 'is_postgres') and self.db_manager.is_postgres else 'sqlite'
            check_result['details']['total_resources'] = stats.get('total_resources', 0)
            
            # Check connection time
            if connection_time > 5.0:
                check_result['status'] = 'warning'
                check_result['warnings'].append(f"Slow database connection: {connection_time:.2f}s")
            elif connection_time > 10.0:
                check_result['status'] = 'failed'
                check_result['issues'].append(f"Very slow database connection: {connection_time:.2f}s")
            
            # Test write operation
            try:
                # Try a simple write operation (logging a search)
                self.db_manager.log_search('health_check', {'type': 'health_check'}, 0)
                check_result['details']['write_access'] = True
            except Exception as e:
                check_result['status'] = 'warning'
                check_result['warnings'].append(f"Database write test failed: {e}")
                check_result['details']['write_access'] = False
        
        except Exception as e:
            check_result['status'] = 'failed'
            check_result['issues'].append(f"Database connectivity test failed: {e}")
        
        return check_result
    
    def check_database_schema(self) -> Dict[str, Any]:
        """Check database schema integrity"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        if not self.db_manager:
            check_result['status'] = 'failed'
            check_result['issues'].append("Database manager not available")
            return check_result
        
        try:
            # Expected tables
            expected_tables = [
                'emerging_skills',
                'educational_resources',
                'skill_resources',
                'learning_content',
                'skill_learning_paths',
                'learning_sessions',
                'content_analysis_queue',
                'resource_questions',
                'resource_exercises'
            ]
            
            # Check which tables exist
            existing_tables = []
            missing_tables = []
            
            for table in expected_tables:
                try:
                    # Try to query the table
                    with self.db_manager._get_connection() as conn:
                        if hasattr(self.db_manager, 'is_postgres') and self.db_manager.is_postgres:
                            with conn.cursor() as cursor:
                                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                                cursor.fetchone()
                        else:
                            cursor = conn.cursor()
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            cursor.fetchone()
                    
                    existing_tables.append(table)
                except Exception:
                    missing_tables.append(table)
            
            check_result['details']['existing_tables'] = existing_tables
            check_result['details']['missing_tables'] = missing_tables
            check_result['details']['table_count'] = len(existing_tables)
            
            # Evaluate results
            if missing_tables:
                if len(missing_tables) > len(expected_tables) // 2:
                    check_result['status'] = 'failed'
                    check_result['issues'].append(f"Many tables missing: {missing_tables}")
                else:
                    check_result['status'] = 'warning'
                    check_result['warnings'].append(f"Some tables missing: {missing_tables}")
            
            # Check for essential tables
            essential_tables = ['emerging_skills', 'educational_resources']
            missing_essential = [t for t in essential_tables if t in missing_tables]
            if missing_essential:
                check_result['status'] = 'failed'
                check_result['issues'].append(f"Essential tables missing: {missing_essential}")
        
        except Exception as e:
            check_result['status'] = 'failed'
            check_result['issues'].append(f"Schema check failed: {e}")
        
        return check_result
    
    def check_database_data_integrity(self) -> Dict[str, Any]:
        """Check database data integrity"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        if not self.db_manager:
            check_result['status'] = 'failed'
            check_result['issues'].append("Database manager not available")
            return check_result
        
        try:
            # Get basic statistics
            stats = self.db_manager.get_resource_stats()
            check_result['details']['total_resources'] = stats.get('total_resources', 0)
            
            # Check if we have data
            if stats.get('total_resources', 0) == 0:
                check_result['status'] = 'warning'
                check_result['warnings'].append("No educational resources found in database")
            
            # Check skills
            try:
                skills = self.db_manager.get_emerging_skills(limit=10)
                check_result['details']['total_skills'] = len(skills)
                
                if len(skills) == 0:
                    check_result['status'] = 'warning'
                    check_result['warnings'].append("No emerging skills found in database")
            except Exception as e:
                check_result['warnings'].append(f"Could not check skills: {e}")
            
            # Check skill-resource relationships
            try:
                # Try to get resources for skills
                if len(skills) > 0:
                    skill_id = skills[0]['id']
                    resources = self.db_manager.get_resources_for_skill(skill_id)
                    check_result['details']['sample_skill_resources'] = len(resources)
            except Exception as e:
                check_result['warnings'].append(f"Could not check skill-resource relationships: {e}")
            
            # Check for orphaned records (basic check)
            try:
                with self.db_manager._get_connection() as conn:
                    if hasattr(self.db_manager, 'is_postgres') and self.db_manager.is_postgres:
                        with conn.cursor() as cursor:
                            # Check for skill_resources without corresponding skills
                            cursor.execute("""
                                SELECT COUNT(*) FROM skill_resources sr
                                LEFT JOIN emerging_skills es ON sr.skill_id = es.id
                                WHERE es.id IS NULL
                            """)
                            orphaned_skill_resources = cursor.fetchone()[0]
                            check_result['details']['orphaned_skill_resources'] = orphaned_skill_resources
                            
                            if orphaned_skill_resources > 0:
                                check_result['status'] = 'warning'
                                check_result['warnings'].append(f"Found {orphaned_skill_resources} orphaned skill-resource relationships")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT COUNT(*) FROM skill_resources sr
                            LEFT JOIN emerging_skills es ON sr.skill_id = es.id
                            WHERE es.id IS NULL
                        """)
                        orphaned_skill_resources = cursor.fetchone()[0]
                        check_result['details']['orphaned_skill_resources'] = orphaned_skill_resources
                        
                        if orphaned_skill_resources > 0:
                            check_result['status'] = 'warning'
                            check_result['warnings'].append(f"Found {orphaned_skill_resources} orphaned skill-resource relationships")
            
            except Exception as e:
                check_result['warnings'].append(f"Could not check for orphaned records: {e}")
        
        except Exception as e:
            check_result['status'] = 'failed'
            check_result['issues'].append(f"Data integrity check failed: {e}")
        
        return check_result
    
    def check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        # Required environment variables
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY'
        ]
        
        # Optional but recommended
        optional_vars = [
            'OPENAI_API_KEY',
            'ANTHROPIC_API_KEY',
            'PERPLEXITY_API_KEY',
            'YOUTUBE_API_KEY',
            'GITHUB_TOKEN'
        ]
        
        # Check required variables
        missing_required = []
        for var in required_vars:
            if not os.getenv(var):
                missing_required.append(var)
        
        check_result['details']['missing_required'] = missing_required
        
        if missing_required:
            check_result['status'] = 'failed'
            check_result['issues'].append(f"Required environment variables missing: {missing_required}")
        
        # Check optional variables
        missing_optional = []
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)
        
        check_result['details']['missing_optional'] = missing_optional
        
        if missing_optional:
            check_result['warnings'].append(f"Optional environment variables missing: {missing_optional}")
        
        # Check DATABASE_URL format
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            if database_url.startswith(('postgres://', 'postgresql://')):
                check_result['details']['database_type'] = 'postgresql'
            elif database_url.startswith('sqlite:'):
                check_result['details']['database_type'] = 'sqlite'
            else:
                check_result['warnings'].append("DATABASE_URL format not recognized")
        
        return check_result
    
    def check_file_system(self) -> Dict[str, Any]:
        """Check file system access and required files"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check required files
            required_files = [
                'app.py',
                'utils/database.py',
                'utils/config.py',
                'templates/',
                'static/'
            ]
            
            missing_files = []
            existing_files = []
            
            for file_path in required_files:
                path = Path(file_path)
                if path.exists():
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)
            
            check_result['details']['existing_files'] = existing_files
            check_result['details']['missing_files'] = missing_files
            
            if missing_files:
                check_result['status'] = 'warning'
                check_result['warnings'].append(f"Missing files: {missing_files}")
            
            # Check data directory (for SQLite)
            data_dir = Path('data')
            if data_dir.exists():
                check_result['details']['data_directory_exists'] = True
                # Check if data directory is writable
                try:
                    test_file = data_dir / 'write_test.tmp'
                    test_file.write_text('test')
                    test_file.unlink()
                    check_result['details']['data_directory_writable'] = True
                except Exception:
                    check_result['details']['data_directory_writable'] = False
                    check_result['warnings'].append("Data directory not writable")
            else:
                check_result['details']['data_directory_exists'] = False
                # Try to create it
                try:
                    data_dir.mkdir(exist_ok=True)
                    check_result['details']['data_directory_created'] = True
                except Exception as e:
                    check_result['warnings'].append(f"Could not create data directory: {e}")
        
        except Exception as e:
            check_result['status'] = 'failed'
            check_result['issues'].append(f"File system check failed: {e}")
        
        return check_result
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check Python dependencies"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        # Required modules
        required_modules = [
            'flask',
            'flask_cors',
            'requests',
            'json',
            'sqlite3',
            'datetime',
            'pathlib'
        ]
        
        # Optional modules
        optional_modules = [
            'psycopg2',
            'anthropic',
            'openai'
        ]
        
        missing_required = []
        missing_optional = []
        imported_modules = []
        
        # Test required modules
        for module in required_modules:
            try:
                __import__(module)
                imported_modules.append(module)
            except ImportError:
                missing_required.append(module)
        
        # Test optional modules
        for module in optional_modules:
            try:
                __import__(module)
                imported_modules.append(module)
            except ImportError:
                missing_optional.append(module)
        
        check_result['details']['imported_modules'] = imported_modules
        check_result['details']['missing_required'] = missing_required
        check_result['details']['missing_optional'] = missing_optional
        
        if missing_required:
            check_result['status'] = 'failed'
            check_result['issues'].append(f"Required modules missing: {missing_required}")
        
        if missing_optional:
            check_result['warnings'].append(f"Optional modules missing: {missing_optional}")
        
        return check_result
    
    def check_api_endpoints(self) -> Dict[str, Any]:
        """Check API endpoint availability (basic)"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        # This is a basic check - in a real environment, you might make HTTP requests
        # For now, we'll just check if the Flask app components are importable
        
        try:
            # Check if Flask app can be imported
            import app
            check_result['details']['app_importable'] = True
            
            # Check if database routes are available
            if hasattr(app, 'db_manager'):
                check_result['details']['database_manager_available'] = True
            else:
                check_result['warnings'].append("Database manager not found in app")
        
        except ImportError as e:
            check_result['status'] = 'failed'
            check_result['issues'].append(f"Could not import Flask app: {e}")
        except Exception as e:
            check_result['warnings'].append(f"API endpoint check issue: {e}")
        
        return check_result
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            import psutil
            
            # Get memory information
            memory = psutil.virtual_memory()
            
            check_result['details']['total_memory_gb'] = round(memory.total / (1024**3), 2)
            check_result['details']['available_memory_gb'] = round(memory.available / (1024**3), 2)
            check_result['details']['memory_percent_used'] = memory.percent
            
            # Check memory usage
            if memory.percent > 90:
                check_result['status'] = 'failed'
                check_result['issues'].append(f"High memory usage: {memory.percent}%")
            elif memory.percent > 80:
                check_result['status'] = 'warning'
                check_result['warnings'].append(f"Elevated memory usage: {memory.percent}%")
        
        except ImportError:
            check_result['warnings'].append("psutil not available - cannot check memory usage")
        except Exception as e:
            check_result['warnings'].append(f"Memory check failed: {e}")
        
        return check_result
    
    def check_disk_space(self) -> Dict[str, Any]:
        """Check disk space"""
        check_result = {
            'status': 'healthy',
            'details': {},
            'issues': [],
            'warnings': []
        }
        
        try:
            import shutil
            
            # Check disk usage
            total, used, free = shutil.disk_usage('.')
            
            check_result['details']['total_space_gb'] = round(total / (1024**3), 2)
            check_result['details']['used_space_gb'] = round(used / (1024**3), 2)
            check_result['details']['free_space_gb'] = round(free / (1024**3), 2)
            check_result['details']['space_percent_used'] = round((used / total) * 100, 2)
            
            # Check disk usage
            percent_used = (used / total) * 100
            if percent_used > 95:
                check_result['status'] = 'failed'
                check_result['issues'].append(f"Very low disk space: {percent_used:.1f}% used")
            elif percent_used > 85:
                check_result['status'] = 'warning'
                check_result['warnings'].append(f"Low disk space: {percent_used:.1f}% used")
        
        except Exception as e:
            check_result['warnings'].append(f"Disk space check failed: {e}")
        
        return check_result
    
    def _generate_summary(self, checks: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of all checks"""
        summary = {
            'total_checks': len(checks),
            'healthy_checks': 0,
            'warning_checks': 0,
            'failed_checks': 0,
            'critical_issues': [],
            'recommendations': []
        }
        
        for check_name, check_result in checks.items():
            status = check_result.get('status', 'unknown')
            
            if status == 'healthy':
                summary['healthy_checks'] += 1
            elif status == 'warning':
                summary['warning_checks'] += 1
            elif status == 'failed':
                summary['failed_checks'] += 1
                summary['critical_issues'].extend(check_result.get('issues', []))
        
        # Generate recommendations
        if summary['failed_checks'] > 0:
            summary['recommendations'].append("Address failed health checks immediately")
        
        if summary['warning_checks'] > 0:
            summary['recommendations'].append("Review warnings and consider improvements")
        
        # Database-specific recommendations
        if 'database_connectivity' in checks:
            db_check = checks['database_connectivity']
            if db_check.get('details', {}).get('connection_time_ms', 0) > 1000:
                summary['recommendations'].append("Consider database performance optimization")
        
        return summary
    
    def save_health_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Save health report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"health_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Health report saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save health report: {e}")


def main():
    """Run health checks from command line"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run health checks for AI-Horizon Ed platform')
    parser.add_argument('--save', action='store_true', help='Save report to file')
    parser.add_argument('--output', help='Output filename')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    # Run health checks
    health_manager = HealthCheckManager()
    report = health_manager.run_all_checks()
    
    # Print results
    print(f"\nHealth Check Report - {report['timestamp']}")
    print("=" * 50)
    print(f"Overall Status: {report['overall_status'].upper()}")
    print(f"Total Checks: {report['summary']['total_checks']}")
    print(f"Healthy: {report['summary']['healthy_checks']}")
    print(f"Warnings: {report['summary']['warning_checks']}")
    print(f"Failed: {report['summary']['failed_checks']}")
    
    if report['issues']:
        print(f"\nCritical Issues:")
        for issue in report['issues']:
            print(f"  ❌ {issue}")
    
    if report['warnings']:
        print(f"\nWarnings:")
        for warning in report['warnings']:
            print(f"  ⚠️  {warning}")
    
    if report['summary']['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['summary']['recommendations']:
            print(f"  💡 {rec}")
    
    # Save report if requested
    if args.save:
        health_manager.save_health_report(report, args.output)
    
    # Exit with appropriate code
    if report['overall_status'] == 'unhealthy':
        sys.exit(1)
    elif report['overall_status'] == 'degraded':
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main() 