#!/usr/bin/env python3
"""
Bulletproof Deployment Script for AI-Horizon Ed Platform

This script provides a completely automated, safe, and reversible deployment
process for the AI-Horizon Ed platform to Heroku.

Features:
- Pre-deployment validation
- Automated database migration
- Health checks
- Rollback capability
- Progress monitoring
- Error handling and recovery
"""

import os
import sys
import json
import subprocess
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the app directory to the path
sys.path.append(str(Path(__file__).parent / 'aih_edu'))

try:
    from aih_edu.bulletproof_schema import BulletproofSchemaManager
    from aih_edu.bulletproof_migration import BulletproofMigrationManager
except ImportError:
    print("Error: Could not import bulletproof modules. Make sure they exist in aih_edu/")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BulletproofDeploymentManager:
    """Manages bulletproof deployment to Heroku"""
    
    def __init__(self, app_name: str, local_db_path: str = "sqlite:///data/aih_edu.db"):
        self.app_name = app_name
        self.local_db_path = local_db_path
        self.deployment_id = self._generate_deployment_id()
        self.deployment_log = f"deployment_{self.deployment_id}.json"
        
        # Deployment state
        self.deployment_state = {
            'deployment_id': self.deployment_id,
            'app_name': app_name,
            'started_at': datetime.now().isoformat(),
            'status': 'initializing',
            'phases': {},
            'rollback_data': {},
            'errors': []
        }
    
    def _generate_deployment_id(self) -> str:
        """Generate unique deployment ID"""
        return f"deploy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _save_deployment_state(self):
        """Save deployment state to file"""
        with open(self.deployment_log, 'w') as f:
            json.dump(self.deployment_state, f, indent=2, default=str)
    
    def _run_command(self, command: str, check_output: bool = False) -> tuple:
        """Run a shell command safely"""
        try:
            if check_output:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True, 
                    timeout=300
                )
                return True, result.stdout, result.stderr
            else:
                result = subprocess.run(command, shell=True, timeout=300)
                return result.returncode == 0, "", ""
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def validate_prerequisites(self) -> Dict[str, Any]:
        """Validate all prerequisites for deployment"""
        validation = {
            'status': 'success',
            'checks': {},
            'issues': []
        }
        
        logger.info("Validating deployment prerequisites...")
        
        # Check Heroku CLI
        success, stdout, stderr = self._run_command("heroku --version", check_output=True)
        validation['checks']['heroku_cli'] = success
        if not success:
            validation['issues'].append("Heroku CLI not installed or not in PATH")
        
        # Check Git
        success, stdout, stderr = self._run_command("git --version", check_output=True)
        validation['checks']['git'] = success
        if not success:
            validation['issues'].append("Git not installed or not in PATH")
        
        # Check Heroku authentication
        success, stdout, stderr = self._run_command("heroku auth:whoami", check_output=True)
        validation['checks']['heroku_auth'] = success
        if not success:
            validation['issues'].append("Not authenticated with Heroku (run 'heroku login')")
        
        # Check app exists
        success, stdout, stderr = self._run_command(f"heroku apps:info {self.app_name}", check_output=True)
        validation['checks']['app_exists'] = success
        if not success:
            validation['issues'].append(f"Heroku app '{self.app_name}' does not exist")
        
        # Check local database
        validation['checks']['local_db'] = Path(self.local_db_path.replace('sqlite:///', '')).exists()
        if not validation['checks']['local_db']:
            validation['issues'].append(f"Local database not found: {self.local_db_path}")
        
        # Check deployment files
        deployment_files = ['requirements.txt', 'Procfile', 'runtime.txt']
        for file in deployment_files:
            exists = Path(file).exists()
            validation['checks'][f'file_{file}'] = exists
            if not exists:
                validation['issues'].append(f"Required deployment file missing: {file}")
        
        # Check app structure
        app_py = Path('aih_edu/app.py')
        validation['checks']['app_structure'] = app_py.exists()
        if not app_py.exists():
            validation['issues'].append("App file not found: aih_edu/app.py")
        
        if validation['issues']:
            validation['status'] = 'failed'
        
        return validation
    
    def backup_current_deployment(self) -> Dict[str, Any]:
        """Backup current deployment state"""
        backup_result = {
            'status': 'success',
            'backup_data': {},
            'errors': []
        }
        
        logger.info("Backing up current deployment...")
        
        try:
            # Get current environment variables
            success, stdout, stderr = self._run_command(
                f"heroku config --app {self.app_name} --json", 
                check_output=True
            )
            if success:
                backup_result['backup_data']['env_vars'] = json.loads(stdout)
            else:
                backup_result['errors'].append(f"Failed to backup env vars: {stderr}")
            
            # Get current addons
            success, stdout, stderr = self._run_command(
                f"heroku addons --app {self.app_name} --json", 
                check_output=True
            )
            if success:
                backup_result['backup_data']['addons'] = json.loads(stdout)
            else:
                backup_result['errors'].append(f"Failed to backup addons: {stderr}")
            
            # Get current releases
            success, stdout, stderr = self._run_command(
                f"heroku releases --app {self.app_name} --json --num 5", 
                check_output=True
            )
            if success:
                backup_result['backup_data']['recent_releases'] = json.loads(stdout)
            else:
                backup_result['errors'].append(f"Failed to backup releases: {stderr}")
            
            # Store backup in deployment state
            self.deployment_state['rollback_data'] = backup_result['backup_data']
            
        except Exception as e:
            backup_result['status'] = 'failed'
            backup_result['errors'].append(str(e))
        
        return backup_result
    
    def prepare_deployment_files(self) -> Dict[str, Any]:
        """Prepare and validate deployment files"""
        preparation = {
            'status': 'success',
            'actions': [],
            'issues': []
        }
        
        logger.info("Preparing deployment files...")
        
        try:
            # Ensure requirements.txt is in root and properly formatted
            req_path = Path('requirements.txt')
            if req_path.exists():
                # Read and validate requirements
                with open(req_path, 'r') as f:
                    content = f.read()
                
                # Check for sqlite3 (should not be included)
                if 'sqlite3' in content:
                    preparation['issues'].append("sqlite3 found in requirements.txt (should not be included)")
                
                # Check for psycopg2
                if 'psycopg2' not in content:
                    preparation['issues'].append("psycopg2-binary not found in requirements.txt")
                
                preparation['actions'].append("Validated requirements.txt")
            
            # Ensure Procfile is correctly configured
            procfile_path = Path('Procfile')
            if procfile_path.exists():
                with open(procfile_path, 'r') as f:
                    content = f.read()
                
                if 'cd aih_edu' not in content:
                    preparation['issues'].append("Procfile should include 'cd aih_edu'")
                
                if 'gunicorn' not in content:
                    preparation['issues'].append("Procfile should use gunicorn")
                
                preparation['actions'].append("Validated Procfile")
            
            # Ensure runtime.txt specifies Python version
            runtime_path = Path('runtime.txt')
            if runtime_path.exists():
                with open(runtime_path, 'r') as f:
                    content = f.read().strip()
                
                if not content.startswith('python-'):
                    preparation['issues'].append("runtime.txt should specify Python version")
                
                preparation['actions'].append("Validated runtime.txt")
            
            if preparation['issues']:
                preparation['status'] = 'failed'
        
        except Exception as e:
            preparation['status'] = 'failed'
            preparation['issues'].append(str(e))
        
        return preparation
    
    def deploy_to_heroku(self) -> Dict[str, Any]:
        """Deploy application to Heroku"""
        deployment = {
            'status': 'success',
            'steps': [],
            'errors': []
        }
        
        logger.info("Deploying to Heroku...")
        
        try:
            # Add changes to git
            logger.info("Adding changes to git...")
            success, stdout, stderr = self._run_command("git add .")
            if success:
                deployment['steps'].append("Added changes to git")
            else:
                deployment['errors'].append(f"Failed to add changes: {stderr}")
                deployment['status'] = 'failed'
                return deployment
            
            # Commit changes
            commit_msg = f"Bulletproof deployment {self.deployment_id}"
            success, stdout, stderr = self._run_command(f'git commit -m "{commit_msg}"')
            if success:
                deployment['steps'].append("Committed changes")
            else:
                # Check if there are no changes to commit
                if "nothing to commit" in stderr:
                    deployment['steps'].append("No new changes to commit")
                else:
                    deployment['errors'].append(f"Failed to commit: {stderr}")
            
            # Push to Heroku
            logger.info("Pushing to Heroku...")
            success, stdout, stderr = self._run_command(f"git push heroku HEAD:main")
            if success:
                deployment['steps'].append("Pushed to Heroku successfully")
            else:
                deployment['status'] = 'failed'
                deployment['errors'].append(f"Failed to push to Heroku: {stderr}")
                return deployment
            
            # Wait for deployment to complete
            logger.info("Waiting for deployment to complete...")
            time.sleep(10)
            
            deployment['steps'].append("Deployment completed")
        
        except Exception as e:
            deployment['status'] = 'failed'
            deployment['errors'].append(str(e))
        
        return deployment
    
    def setup_database(self) -> Dict[str, Any]:
        """Setup and migrate database"""
        db_setup = {
            'status': 'success',
            'steps': [],
            'errors': []
        }
        
        logger.info("Setting up database...")
        
        try:
            # Check if PostgreSQL addon exists
            success, stdout, stderr = self._run_command(
                f"heroku addons --app {self.app_name} --json", 
                check_output=True
            )
            
            has_postgres = False
            if success:
                addons = json.loads(stdout)
                has_postgres = any('postgres' in addon.get('addon_service', {}).get('name', '') for addon in addons)
            
            if not has_postgres:
                logger.info("Adding PostgreSQL addon...")
                success, stdout, stderr = self._run_command(
                    f"heroku addons:create heroku-postgresql:essential-0 --app {self.app_name}"
                )
                if success:
                    db_setup['steps'].append("Added PostgreSQL addon")
                    time.sleep(30)  # Wait for addon to be ready
                else:
                    db_setup['errors'].append(f"Failed to add PostgreSQL: {stderr}")
                    db_setup['status'] = 'failed'
                    return db_setup
            else:
                db_setup['steps'].append("PostgreSQL addon already exists")
            
            # Get DATABASE_URL
            success, stdout, stderr = self._run_command(
                f"heroku config:get DATABASE_URL --app {self.app_name}", 
                check_output=True
            )
            if success and stdout.strip():
                database_url = stdout.strip()
                db_setup['steps'].append("Retrieved DATABASE_URL")
            else:
                db_setup['errors'].append("Failed to get DATABASE_URL")
                db_setup['status'] = 'failed'
                return db_setup
            
            # Run database migration
            logger.info("Running database migration...")
            migration_manager = BulletproofMigrationManager(
                self.local_db_path, 
                database_url
            )
            
            migration_result = migration_manager.perform_full_migration()
            
            if migration_result['status'] == 'success':
                db_setup['steps'].append(f"Migrated {migration_result['summary']['total_records_migrated']} records")
                db_setup['migration_summary'] = migration_result['summary']
            else:
                db_setup['status'] = 'failed'
                db_setup['errors'].append(f"Migration failed: {migration_result.get('error', 'Unknown error')}")
        
        except Exception as e:
            db_setup['status'] = 'failed'
            db_setup['errors'].append(str(e))
        
        return db_setup
    
    def perform_health_checks(self) -> Dict[str, Any]:
        """Perform comprehensive health checks"""
        health_check = {
            'status': 'success',
            'checks': {},
            'issues': []
        }
        
        logger.info("Performing health checks...")
        
        try:
            # Check app is running
            success, stdout, stderr = self._run_command(
                f"heroku ps --app {self.app_name} --json", 
                check_output=True
            )
            if success:
                processes = json.loads(stdout)
                web_processes = [p for p in processes if p.get('type') == 'web']
                health_check['checks']['app_running'] = len(web_processes) > 0 and all(p.get('state') == 'up' for p in web_processes)
            else:
                health_check['checks']['app_running'] = False
                health_check['issues'].append("Failed to check app status")
            
            # Check app responds to HTTP requests
            app_url = f"https://{self.app_name}.herokuapp.com"
            success, stdout, stderr = self._run_command(
                f"curl -s -o /dev/null -w '%{{http_code}}' {app_url}/api/status", 
                check_output=True
            )
            if success and stdout.strip() == '200':
                health_check['checks']['http_response'] = True
            else:
                health_check['checks']['http_response'] = False
                health_check['issues'].append("App not responding to HTTP requests")
            
            # Check database connectivity
            success, stdout, stderr = self._run_command(
                f"heroku run 'cd aih_edu && python -c \"from utils.database import DatabaseManager; db = DatabaseManager(); print(db.get_resource_stats())\"' --app {self.app_name}",
                check_output=True
            )
            if success and 'total_resources' in stdout:
                health_check['checks']['database_connectivity'] = True
            else:
                health_check['checks']['database_connectivity'] = False
                health_check['issues'].append("Database connectivity issues")
            
            # Check logs for errors
            success, stdout, stderr = self._run_command(
                f"heroku logs --tail --num 50 --app {self.app_name}", 
                check_output=True
            )
            if success:
                error_count = stdout.lower().count('error')
                health_check['checks']['log_errors'] = error_count < 5
                health_check['error_count'] = error_count
                if error_count >= 5:
                    health_check['issues'].append(f"High error count in logs: {error_count}")
            
            if health_check['issues']:
                health_check['status'] = 'warning'
        
        except Exception as e:
            health_check['status'] = 'failed'
            health_check['issues'].append(str(e))
        
        return health_check
    
    def rollback_deployment(self) -> Dict[str, Any]:
        """Rollback deployment to previous state"""
        rollback = {
            'status': 'success',
            'steps': [],
            'errors': []
        }
        
        logger.info("Rolling back deployment...")
        
        try:
            # Get previous release
            success, stdout, stderr = self._run_command(
                f"heroku releases --app {self.app_name} --json --num 2", 
                check_output=True
            )
            
            if success:
                releases = json.loads(stdout)
                if len(releases) >= 2:
                    previous_release = releases[1]['version']
                    
                    # Rollback to previous release
                    success, stdout, stderr = self._run_command(
                        f"heroku rollback v{previous_release} --app {self.app_name}"
                    )
                    if success:
                        rollback['steps'].append(f"Rolled back to v{previous_release}")
                    else:
                        rollback['errors'].append(f"Failed to rollback: {stderr}")
                        rollback['status'] = 'failed'
                else:
                    rollback['errors'].append("No previous release to rollback to")
                    rollback['status'] = 'failed'
            else:
                rollback['errors'].append("Failed to get release history")
                rollback['status'] = 'failed'
        
        except Exception as e:
            rollback['status'] = 'failed'
            rollback['errors'].append(str(e))
        
        return rollback
    
    def perform_full_deployment(self) -> Dict[str, Any]:
        """Perform complete bulletproof deployment"""
        logger.info(f"Starting bulletproof deployment {self.deployment_id}")
        
        try:
            # Phase 1: Prerequisites validation
            logger.info("Phase 1: Validating prerequisites")
            prerequisites = self.validate_prerequisites()
            self.deployment_state['phases']['prerequisites'] = prerequisites
            self._save_deployment_state()
            
            if prerequisites['status'] != 'success':
                raise Exception(f"Prerequisites validation failed: {prerequisites['issues']}")
            
            # Phase 2: Backup current deployment
            logger.info("Phase 2: Backing up current deployment")
            backup = self.backup_current_deployment()
            self.deployment_state['phases']['backup'] = backup
            self._save_deployment_state()
            
            # Phase 3: Prepare deployment files
            logger.info("Phase 3: Preparing deployment files")
            preparation = self.prepare_deployment_files()
            self.deployment_state['phases']['preparation'] = preparation
            self._save_deployment_state()
            
            if preparation['status'] != 'success':
                raise Exception(f"File preparation failed: {preparation['issues']}")
            
            # Phase 4: Deploy to Heroku
            logger.info("Phase 4: Deploying to Heroku")
            deployment = self.deploy_to_heroku()
            self.deployment_state['phases']['deployment'] = deployment
            self._save_deployment_state()
            
            if deployment['status'] != 'success':
                raise Exception(f"Heroku deployment failed: {deployment['errors']}")
            
            # Phase 5: Setup database
            logger.info("Phase 5: Setting up database")
            db_setup = self.setup_database()
            self.deployment_state['phases']['database'] = db_setup
            self._save_deployment_state()
            
            if db_setup['status'] != 'success':
                raise Exception(f"Database setup failed: {db_setup['errors']}")
            
            # Phase 6: Health checks
            logger.info("Phase 6: Performing health checks")
            health_check = self.perform_health_checks()
            self.deployment_state['phases']['health_check'] = health_check
            self._save_deployment_state()
            
            # Complete deployment
            self.deployment_state['status'] = 'success'
            self.deployment_state['completed_at'] = datetime.now().isoformat()
            
            if health_check['status'] == 'warning':
                self.deployment_state['status'] = 'success_with_warnings'
                logger.warning("Deployment completed with warnings")
            
            logger.info("Bulletproof deployment completed successfully!")
            
            # Print summary
            self._print_deployment_summary()
        
        except Exception as e:
            self.deployment_state['status'] = 'failed'
            self.deployment_state['error'] = str(e)
            self.deployment_state['failed_at'] = datetime.now().isoformat()
            
            logger.error(f"Deployment failed: {e}")
            
            # Ask for rollback
            response = input("\nDeployment failed. Do you want to rollback? (y/n): ")
            if response.lower() == 'y':
                rollback_result = self.rollback_deployment()
                self.deployment_state['rollback'] = rollback_result
                
                if rollback_result['status'] == 'success':
                    logger.info("Rollback completed successfully")
                else:
                    logger.error("Rollback failed")
        
        finally:
            self._save_deployment_state()
        
        return self.deployment_state
    
    def _print_deployment_summary(self):
        """Print deployment summary"""
        print("\n" + "="*60)
        print("BULLETPROOF DEPLOYMENT SUMMARY")
        print("="*60)
        print(f"Deployment ID: {self.deployment_id}")
        print(f"App Name: {self.app_name}")
        print(f"Status: {self.deployment_state['status']}")
        print(f"Started: {self.deployment_state['started_at']}")
        print(f"Completed: {self.deployment_state.get('completed_at', 'N/A')}")
        
        if 'database' in self.deployment_state['phases']:
            db_summary = self.deployment_state['phases']['database'].get('migration_summary', {})
            if db_summary:
                print(f"\nDatabase Migration:")
                print(f"  Records migrated: {db_summary.get('total_records_migrated', 0)}")
                print(f"  Tables migrated: {db_summary.get('tables_migrated', 0)}")
        
        app_url = f"https://{self.app_name}.herokuapp.com"
        print(f"\nApp URL: {app_url}")
        print(f"Logs: heroku logs --tail --app {self.app_name}")
        print("="*60)


def main():
    """Main deployment script"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bulletproof deployment for AI-Horizon Ed')
    parser.add_argument('app_name', help='Heroku app name')
    parser.add_argument('--local-db', default='sqlite:///data/aih_edu.db', help='Local database path')
    parser.add_argument('--dry-run', action='store_true', help='Validate only, do not deploy')
    
    args = parser.parse_args()
    
    # Initialize deployment manager
    deployment_manager = BulletproofDeploymentManager(args.app_name, args.local_db)
    
    if args.dry_run:
        # Dry run - validation only
        print("Running deployment validation (dry run)...")
        prerequisites = deployment_manager.validate_prerequisites()
        preparation = deployment_manager.prepare_deployment_files()
        
        print(f"\nPrerequisites: {prerequisites['status']}")
        if prerequisites['issues']:
            print("Issues:")
            for issue in prerequisites['issues']:
                print(f"  - {issue}")
        
        print(f"\nFile Preparation: {preparation['status']}")
        if preparation['issues']:
            print("Issues:")
            for issue in preparation['issues']:
                print(f"  - {issue}")
        
        if prerequisites['status'] == 'success' and preparation['status'] == 'success':
            print("\n✅ Ready for deployment!")
        else:
            print("\n❌ Not ready for deployment. Fix issues above.")
    else:
        # Full deployment
        deployment_result = deployment_manager.perform_full_deployment()
        
        if deployment_result['status'] in ['success', 'success_with_warnings']:
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main() 