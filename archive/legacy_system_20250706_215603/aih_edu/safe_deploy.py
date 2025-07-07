#!/usr/bin/env python3
"""
Safe Deployment Script for AI-Horizon Ed Platform
Ensures everything works locally before deploying to Heroku
"""

import os
import sys
import json
import requests
import subprocess
from datetime import datetime
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SafeDeployer:
    def __init__(self):
        self.heroku_app = "ai-horizon-ed-platform-50ef91ff7701"
        self.heroku_url = f"https://{self.heroku_app}.herokuapp.com"
        self.local_url = "http://127.0.0.1:9000"
        self.tests_passed = []
        self.tests_failed = []
        
    def run_command(self, command, description=""):
        """Run a shell command and return success/failure"""
        try:
            logger.info(f"🔧 {description}")
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ {description} - SUCCESS")
                return True, result.stdout
            else:
                logger.error(f"❌ {description} - FAILED")
                logger.error(f"Error: {result.stderr}")
                return False, result.stderr
        except Exception as e:
            logger.error(f"❌ {description} - EXCEPTION: {e}")
            return False, str(e)
    
    def check_local_app_running(self):
        """Check if local app is running"""
        try:
            response = requests.get(f"{self.local_url}/api/database/stats", timeout=5)
            if response.status_code == 200:
                logger.info("✅ Local app is running")
                return True
            else:
                logger.error(f"❌ Local app responded with {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Local app not running: {e}")
            return False
    
    def test_local_functionality(self):
        """Test core functionality locally"""
        logger.info("🧪 Testing local functionality...")
        
        tests = [
            ("Database Stats", f"{self.local_url}/api/database/stats"),
            ("Skills API", f"{self.local_url}/api/skills/emerging"),
            ("Resources API", f"{self.local_url}/api/resources"),
            ("Skill Detail Page", f"{self.local_url}/skill/ai-enhanced-siem"),
            ("Admin Panel", f"{self.local_url}/admin"),
        ]
        
        all_passed = True
        for test_name, endpoint in tests:
            try:
                response = requests.get(endpoint, timeout=10)
                if response.status_code == 200:
                    logger.info(f"✅ {test_name} - OK")
                    self.tests_passed.append(test_name)
                else:
                    logger.error(f"❌ {test_name} - {response.status_code}")
                    self.tests_failed.append(f"{test_name}: {response.status_code}")
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ {test_name} - {e}")
                self.tests_failed.append(f"{test_name}: {e}")
                all_passed = False
        
        return all_passed
    
    def test_quiz_functionality(self):
        """Test quiz functionality specifically"""
        logger.info("🧪 Testing quiz functionality...")
        
        try:
            # Get resources
            response = requests.get(f"{self.local_url}/api/resources", timeout=10)
            if response.status_code != 200:
                logger.error("❌ Cannot get resources for quiz test")
                return False
            
            resources = response.json()
            if not resources.get('resources'):
                logger.error("❌ No resources found for quiz test")
                return False
            
            # Test quiz questions
            resource_id = resources['resources'][0]['id']
            response = requests.get(f"{self.local_url}/api/resource/{resource_id}/questions", timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Quiz questions endpoint - OK")
                
                # Test quiz grading
                questions = response.json()
                if questions:
                    sample_answers = ["Sample answer"] * len(questions)
                    grade_response = requests.post(
                        f"{self.local_url}/api/quiz/{resource_id}/grade",
                        json={"answers": sample_answers},
                        timeout=15
                    )
                    
                    if grade_response.status_code == 200:
                        logger.info("✅ Quiz grading endpoint - OK")
                        return True
                    else:
                        logger.error(f"❌ Quiz grading failed: {grade_response.status_code}")
                        return False
                else:
                    logger.warning("⚠️ No questions found but endpoint works")
                    return True
            else:
                logger.error(f"❌ Quiz questions failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Quiz test failed: {e}")
            return False
    
    def backup_current_state(self):
        """Create a backup of current working state"""
        logger.info("💾 Creating backup of current state...")
        
        try:
            # Export database
            from utils.database import DatabaseManager
            db_manager = DatabaseManager()
            
            # Get all data
            skills = db_manager.get_emerging_skills()
            resources = db_manager.get_all_resources()
            
            # Create backup data
            backup_data = {
                'skills': skills,
                'resources': resources,
                'timestamp': datetime.now().isoformat(),
                'version': '2.0'
            }
            
            # Save to file
            backup_file = f"deployment_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"✅ Backup saved to: {backup_file}")
            return backup_file
            
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
            return None
    
    def deploy_to_heroku(self):
        """Deploy to Heroku"""
        logger.info("🚀 Deploying to Heroku...")
        
        # Check git status
        success, output = self.run_command("git status --porcelain", "Checking git status")
        if success and output.strip():
            logger.info("📝 Uncommitted changes found, committing...")
            self.run_command("git add -A", "Adding all changes")
            commit_msg = f"🚀 Safe deployment - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            self.run_command(
                f'git commit -m "{commit_msg}"',
                "Committing changes"
            )
        
        # Push to Heroku
        success, output = self.run_command("git push heroku master", "Pushing to Heroku")
        if not success:
            logger.error("❌ Heroku deployment failed!")
            return False
        
        logger.info("✅ Heroku deployment completed")
        return True
    
    def test_heroku_deployment(self):
        """Test Heroku deployment"""
        logger.info("🧪 Testing Heroku deployment...")
        
        # Wait for app to start
        import time
        time.sleep(30)
        
        # Test basic endpoints
        tests = [
            ("Heroku Health", f"{self.heroku_url}/api/database/stats"),
            ("Heroku Skills", f"{self.heroku_url}/api/skills/emerging"),
            ("Heroku Resources", f"{self.heroku_url}/api/resources"),
        ]
        
        all_passed = True
        for test_name, endpoint in tests:
            try:
                response = requests.get(endpoint, timeout=30)
                if response.status_code == 200:
                    logger.info(f"✅ {test_name} - OK")
                    data = response.json()
                    if test_name == "Heroku Resources":
                        resource_count = len(data.get('resources', []))
                        logger.info(f"📊 Heroku has {resource_count} resources")
                else:
                    logger.error(f"❌ {test_name} - {response.status_code}")
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ {test_name} - {e}")
                all_passed = False
        
        return all_passed
    
    def populate_heroku_database(self):
        """Populate Heroku database if needed"""
        logger.info("📊 Checking Heroku database population...")
        
        try:
            # Check resource count
            response = requests.get(f"{self.heroku_url}/api/resources", timeout=30)
            if response.status_code == 200:
                data = response.json()
                resource_count = len(data.get('resources', []))
                
                if resource_count < 10:  # Threshold for "needs population"
                    logger.info(f"⚠️ Heroku has only {resource_count} resources, running emergency restore...")
                    
                    # Run emergency restore
                    restore_response = requests.get(f"{self.heroku_url}/emergency-restore", timeout=60)
                    if restore_response.status_code == 200:
                        logger.info("✅ Emergency restore completed")
                        
                        # Check again
                        response = requests.get(f"{self.heroku_url}/api/resources", timeout=30)
                        if response.status_code == 200:
                            data = response.json()
                            new_count = len(data.get('resources', []))
                            logger.info(f"📊 Heroku now has {new_count} resources")
                    else:
                        logger.error(f"❌ Emergency restore failed: {restore_response.status_code}")
                        return False
                else:
                    logger.info(f"✅ Heroku has {resource_count} resources - looks good")
                    
            return True
            
        except Exception as e:
            logger.error(f"❌ Database population check failed: {e}")
            return False
    
    def run_deployment(self):
        """Run the complete safe deployment process"""
        logger.info("🚀 Starting Safe Deployment Process")
        logger.info("=" * 50)
        
        # Step 1: Check local environment
        if not self.check_local_app_running():
            logger.error("❌ Local app is not running. Please start it first with: python app.py")
            return False
        
        # Step 2: Test local functionality
        if not self.test_local_functionality():
            logger.error("❌ Local functionality tests failed. Fix local issues before deployment.")
            return False
        
        # Step 3: Test quiz functionality
        if not self.test_quiz_functionality():
            logger.error("❌ Quiz functionality tests failed. Fix quiz issues before deployment.")
            return False
        
        # Step 4: Create backup
        backup_file = self.backup_current_state()
        if not backup_file:
            logger.error("❌ Failed to create backup. Deployment cancelled for safety.")
            return False
        
        # Step 5: Deploy to Heroku
        if not self.deploy_to_heroku():
            logger.error("❌ Heroku deployment failed.")
            return False
        
        # Step 6: Test Heroku deployment
        if not self.test_heroku_deployment():
            logger.error("❌ Heroku deployment tests failed.")
            return False
        
        # Step 7: Populate database if needed
        if not self.populate_heroku_database():
            logger.error("❌ Database population failed.")
            return False
        
        # Success!
        logger.info("🎉 DEPLOYMENT SUCCESSFUL!")
        logger.info("=" * 50)
        logger.info(f"✅ Local tests passed: {len(self.tests_passed)}")
        logger.info(f"✅ Heroku app: {self.heroku_url}")
        logger.info(f"✅ Custom domain: https://ed.theaihorizon.org")
        logger.info(f"💾 Backup saved: {backup_file}")
        
        return True

def main():
    """Main deployment function"""
    deployer = SafeDeployer()
    
    # Ask for confirmation
    print("\n🚀 AI-Horizon Ed Platform - Safe Deployment")
    print("=" * 50)
    print("This will:")
    print("1. Test local functionality")
    print("2. Create a backup of current state")
    print("3. Deploy to Heroku")
    print("4. Test Heroku deployment")
    print("5. Populate database if needed")
    print("")
    
    confirm = input("Continue with deployment? (y/N): ").strip().lower()
    if confirm != 'y':
        print("Deployment cancelled.")
        return False
    
    return deployer.run_deployment()

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 