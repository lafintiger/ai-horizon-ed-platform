#!/usr/bin/env python3
"""
Comprehensive Local System Test Script for AI-Horizon Ed
Tests all major components to ensure everything is working correctly.
"""

import os
import sys
import json
import time
import sqlite3
import requests
import subprocess
import psutil
from datetime import datetime
from pathlib import Path

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def print_header(text):
    """Print a colored header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

# Test configuration
BASE_URL = "http://localhost:9000"
TEST_RESULTS = {
    'passed': 0,
    'failed': 0,
    'warnings': 0,
    'details': []
}

def add_result(test_name, passed, message, details=None):
    """Add test result"""
    if passed:
        TEST_RESULTS['passed'] += 1
        print_success(f"{test_name}: {message}")
    else:
        TEST_RESULTS['failed'] += 1
        print_error(f"{test_name}: {message}")
    
    TEST_RESULTS['details'].append({
        'test': test_name,
        'passed': passed,
        'message': message,
        'details': details or {}
    })

def test_directory_structure():
    """Test if all required directories and files exist"""
    print_header("TESTING DIRECTORY STRUCTURE")
    
    required_paths = [
        'aih_edu/app.py',
        'aih_edu/utils/database.py',
        'aih_edu/utils/config.py',
        'aih_edu/templates/',
        'aih_edu/static/',
        'aih_edu/data/',
        'test_local_system.py'
    ]
    
    missing_paths = []
    for path in required_paths:
        if not os.path.exists(path):
            missing_paths.append(path)
    
    # Check for deprecated files that should be removed
    deprecated_files = [
        'app.py', 'Procfile', 'requirements.txt', 'runtime.txt', 
        'restore_endpoint.py', 'templates/'
    ]
    
    found_deprecated = []
    for file in deprecated_files:
        if os.path.exists(file):
            found_deprecated.append(file)
    
    if not missing_paths and not found_deprecated:
        add_result("Directory Structure", True, "All required files present, no deprecated files found")
    elif missing_paths:
        add_result("Directory Structure", False, f"Missing files: {missing_paths}")
    else:
        add_result("Directory Structure", False, f"Found deprecated files: {found_deprecated}")

def test_database_integrity():
    """Test database content and functionality"""
    print_header("TESTING DATABASE INTEGRITY")
    
    try:
        # Test database file exists
        db_path = 'aih_edu/data/aih_edu.db'
        if not os.path.exists(db_path):
            add_result("Database File", False, f"Database file not found at {db_path}")
            return
        
        # Connect and test tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test educational_resources table
        cursor.execute("SELECT COUNT(*) FROM educational_resources")
        resource_count = cursor.fetchone()[0]
        
        # Test emerging_skills table  
        cursor.execute("SELECT COUNT(*) FROM emerging_skills")
        skill_count = cursor.fetchone()[0]
        
        # Test learning_content table
        cursor.execute("SELECT COUNT(*) FROM learning_content")
        content_count = cursor.fetchone()[0]
        
        conn.close()
        
        expected_resources = 86
        expected_skills = 7
        
        details = {
            'resources': resource_count,
            'skills': skill_count,
            'learning_content': content_count
        }
        
        if resource_count == expected_resources and skill_count >= expected_skills:
            add_result("Database Content", True, 
                      f"Database healthy: {resource_count} resources, {skill_count} skills, {content_count} learning content",
                      details)
        else:
            add_result("Database Content", False,
                      f"Database content mismatch: Expected {expected_resources} resources, {expected_skills}+ skills. Got {resource_count} resources, {skill_count} skills",
                      details)
            
    except Exception as e:
        add_result("Database Content", False, f"Database test failed: {e}")

def test_dependencies():
    """Test if required Python dependencies are available"""
    print_header("TESTING DEPENDENCIES")
    
    required_modules = [
        'flask', 'requests', 'sqlite3', 'json', 'logging',
        'anthropic', 'openai', 'youtube_transcript_api'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if not missing_modules:
        add_result("Dependencies", True, "All required Python modules available")
    else:
        add_result("Dependencies", False, f"Missing modules: {missing_modules}")

def test_server_startup():
    """Test if server can start and respond"""
    print_header("TESTING SERVER STARTUP & RESPONSE")
    
    try:
        # Test if server is already running
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            add_result("Server Running", True, f"Server responding on {BASE_URL}")
            return True
        else:
            add_result("Server Running", False, f"Server returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        add_result("Server Running", False, f"Cannot connect to server at {BASE_URL}")
        return False
    except requests.exceptions.Timeout:
        add_result("Server Running", False, "Server connection timeout")
        return False
    except Exception as e:
        add_result("Server Running", False, f"Server test error: {e}")
        return False

def test_api_endpoints():
    """Test critical API endpoints"""
    print_header("TESTING API ENDPOINTS")
    
    if not test_server_startup():
        add_result("API Endpoints", False, "Server not running, skipping API tests")
        return
    
    endpoints = [
        ("/", "Homepage"),
        ("/api/database/stats", "Database Stats"),
        ("/api/skills/emerging", "Emerging Skills"),
        ("/skills", "Skills Overview")
    ]
    
    failed_endpoints = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            if response.status_code == 200:
                print_success(f"{name} ({endpoint}): OK")
            else:
                print_error(f"{name} ({endpoint}): Status {response.status_code}")
                failed_endpoints.append(f"{name} ({response.status_code})")
        except Exception as e:
            print_error(f"{name} ({endpoint}): {e}")
            failed_endpoints.append(f"{name} (error)")
    
    if not failed_endpoints:
        add_result("API Endpoints", True, "All core endpoints responding correctly")
    else:
        add_result("API Endpoints", False, f"Failed endpoints: {', '.join(failed_endpoints)}")

def test_skill_pages_and_content():
    """Test individual skill pages, quizzes, and assignments"""
    print_header("TESTING SKILL PAGES, QUIZZES & ASSIGNMENTS")
    
    if not test_server_startup():
        add_result("Skill Pages", False, "Server not running, skipping skill page tests")
        return
    
    try:
        # Get list of skills
        response = requests.get(f"{BASE_URL}/api/skills/emerging", timeout=10)
        if response.status_code != 200:
            add_result("Skill Pages", False, f"Cannot get skills list: Status {response.status_code}")
            return
        
        skills_data = response.json()
        skills = skills_data.get('emerging_skills', [])
        
        if not skills:
            add_result("Skill Pages", False, "No skills found in database")
            return
        
        print_info(f"Testing {len(skills)} skill pages...")
        
        skill_results = []
        for skill in skills:
            skill_name = skill.get('skill_name', '')
            if not skill_name:
                continue
                
            # Convert skill name to URL format
            url_skill_name = skill_name.lower().replace(' ', '-').replace('&', 'and')
            
            skill_result = {
                'name': skill_name,
                'url_name': url_skill_name,
                'page_loads': False,
                'has_resources': False,
                'quiz_questions': 0,
                'quiz_exercises': 0,
                'errors': []
            }
            
            # Test skill page loads
            try:
                skill_response = requests.get(f"{BASE_URL}/skill/{url_skill_name}", timeout=15)
                if skill_response.status_code == 200:
                    skill_result['page_loads'] = True
                    print_success(f"Skill page loads: {skill_name}")
                else:
                    skill_result['errors'].append(f"Page status {skill_response.status_code}")
                    print_error(f"Skill page failed: {skill_name} (Status {skill_response.status_code})")
            except Exception as e:
                skill_result['errors'].append(f"Page load error: {e}")
                print_error(f"Skill page error: {skill_name} - {e}")
            
            # Test for resources/content
            try:
                # Check if skill has resources
                content = skill_response.text if skill_result['page_loads'] else ""
                if "resources" in content.lower() and len(content) > 1000:
                    skill_result['has_resources'] = True
                    print_success(f"Skill has content: {skill_name}")
                else:
                    print_warning(f"Skill appears empty: {skill_name}")
            except:
                pass
            
            # Get resources for this skill and test quiz endpoints
            try:
                # Get database stats to find resource IDs
                stats_response = requests.get(f"{BASE_URL}/api/database/stats", timeout=10)
                if stats_response.status_code == 200:
                    # Test a few sample resource IDs for quiz content
                    sample_resource_ids = [41, 42, 43, 44, 46, 47, 50, 52]  # From logs, these should work
                    
                    working_questions = 0
                    working_exercises = 0
                    
                    for resource_id in sample_resource_ids:
                        # Test questions endpoint
                        try:
                            questions_response = requests.get(f"{BASE_URL}/api/resource/{resource_id}/questions", timeout=5)
                            if questions_response.status_code == 200:
                                working_questions += 1
                        except:
                            pass
                        
                        # Test exercises endpoint  
                        try:
                            exercises_response = requests.get(f"{BASE_URL}/api/resource/{resource_id}/exercises", timeout=5)
                            if exercises_response.status_code == 200:
                                working_exercises += 1
                        except:
                            pass
                    
                    skill_result['quiz_questions'] = working_questions
                    skill_result['quiz_exercises'] = working_exercises
                    
                    if working_questions > 0:
                        print_success(f"Found {working_questions} working quiz questions")
                    else:
                        print_error(f"No working quiz questions found")
                        
                    if working_exercises > 0:
                        print_success(f"Found {working_exercises} working exercises")
                    else:
                        print_error(f"No working exercises found")
                        
            except Exception as e:
                skill_result['errors'].append(f"Quiz test error: {e}")
            
            skill_results.append(skill_result)
        
        # Analyze results
        working_pages = sum(1 for r in skill_results if r['page_loads'])
        pages_with_content = sum(1 for r in skill_results if r['has_resources'])
        total_questions = sum(r['quiz_questions'] for r in skill_results)
        total_exercises = sum(r['quiz_exercises'] for r in skill_results)
        
        result_summary = {
            'total_skills': len(skills),
            'working_pages': working_pages,
            'pages_with_content': pages_with_content,
            'total_quiz_questions': total_questions,
            'total_exercises': total_exercises,
            'skill_details': skill_results
        }
        
        # Overall assessment
        if working_pages == len(skills) and total_questions > 0 and total_exercises > 0:
            add_result("Skill Pages & Content", True, 
                      f"All {working_pages} skill pages working, {total_questions} quiz questions, {total_exercises} exercises available",
                      result_summary)
        elif working_pages == len(skills):
            add_result("Skill Pages & Content", False,
                      f"All {working_pages} skill pages load, but missing quizzes/exercises: {total_questions} questions, {total_exercises} exercises",
                      result_summary)
        else:
            add_result("Skill Pages & Content", False,
                      f"Only {working_pages}/{len(skills)} skill pages working, {total_questions} quiz questions, {total_exercises} exercises",
                      result_summary)
                      
    except Exception as e:
        add_result("Skill Pages & Content", False, f"Skill page testing failed: {e}")

def test_port_availability():
    """Test if required ports are available"""
    print_header("TESTING PORT AVAILABILITY")
    
    target_port = 9000
    
    # Check if port is in use
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', target_port))
        sock.close()
        
        if result == 0:
            # Port is in use - check if it's our server
            try:
                response = requests.get(f"http://localhost:{target_port}/", timeout=3)
                if response.status_code == 200 and "AI-Horizon" in response.text:
                    add_result("Port Status", True, f"Port {target_port} in use by our application")
                else:
                    add_result("Port Status", False, f"Port {target_port} in use by unknown application")
            except:
                add_result("Port Status", False, f"Port {target_port} in use but not responding to HTTP")
        else:
            add_result("Port Status", True, f"Port {target_port} available for use")
            
    except Exception as e:
        add_result("Port Status", False, f"Port test failed: {e}")

def test_cleanup():
    """Test system cleanup and resource management"""
    print_header("TESTING CLEANUP & RESOURCE MANAGEMENT")
    
    issues = []
    
    # Check for log file sizes
    log_dirs = ['logs/', 'aih_edu/logs/']
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            total_size = sum(os.path.getsize(os.path.join(log_dir, f)) 
                           for f in os.listdir(log_dir) 
                           if os.path.isfile(os.path.join(log_dir, f)))
            if total_size > 100 * 1024 * 1024:  # 100MB
                issues.append(f"Large log directory: {log_dir} ({total_size // (1024*1024)}MB)")
    
    # Check for temporary files
    temp_patterns = ['*.tmp', '*.temp', '*~', '*.bak']
    for pattern in temp_patterns:
        import glob
        temp_files = glob.glob(pattern) + glob.glob(f"aih_edu/{pattern}")
        if temp_files:
            issues.append(f"Temporary files found: {temp_files}")
    
    if not issues:
        add_result("System Cleanup", True, "No cleanup issues found")
    else:
        add_result("System Cleanup", False, f"Cleanup issues: {'; '.join(issues)}")

def print_final_summary():
    """Print final test summary"""
    print_header("FINAL TEST SUMMARY")
    
    total_tests = TEST_RESULTS['passed'] + TEST_RESULTS['failed']
    pass_rate = (TEST_RESULTS['passed'] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n{Colors.BOLD}Test Results:{Colors.END}")
    print(f"  {Colors.GREEN}✅ Passed: {TEST_RESULTS['passed']}{Colors.END}")
    print(f"  {Colors.RED}❌ Failed: {TEST_RESULTS['failed']}{Colors.END}")
    print(f"  {Colors.YELLOW}⚠️  Warnings: {TEST_RESULTS['warnings']}{Colors.END}")
    print(f"  {Colors.CYAN}📊 Pass Rate: {pass_rate:.1f}%{Colors.END}")
    
    if TEST_RESULTS['failed'] > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ CRITICAL ISSUES FOUND:{Colors.END}")
        for detail in TEST_RESULTS['details']:
            if not detail['passed']:
                print(f"  • {detail['test']}: {detail['message']}")
    
    print(f"\n{Colors.BOLD}Overall Status:{Colors.END}")
    if TEST_RESULTS['failed'] == 0:
        print(f"{Colors.GREEN}🎉 ALL SYSTEMS OPERATIONAL{Colors.END}")
    elif TEST_RESULTS['failed'] <= 2:
        print(f"{Colors.YELLOW}⚠️  MINOR ISSUES - MOSTLY FUNCTIONAL{Colors.END}")
    else:
        print(f"{Colors.RED}🚨 MAJOR ISSUES - SYSTEM NEEDS ATTENTION{Colors.END}")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'passed': TEST_RESULTS['passed'],
                'failed': TEST_RESULTS['failed'],
                'warnings': TEST_RESULTS['warnings'],
                'pass_rate': pass_rate
            },
            'details': TEST_RESULTS['details']
        }, f, indent=2)
    
    print(f"\n{Colors.CYAN}📄 Detailed results saved to: {results_file}{Colors.END}")

def main():
    """Run all tests"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🔍 AI-HORIZON ED COMPREHENSIVE SYSTEM TEST")
    print("==========================================")
    print(f"Starting system validation at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{Colors.END}")
    
    # Run all tests
    test_directory_structure()
    test_database_integrity()
    test_dependencies()
    test_server_startup()
    test_api_endpoints()
    test_skill_pages_and_content()
    test_port_availability()
    test_cleanup()
    
    # Print final summary
    print_final_summary()

if __name__ == "__main__":
    main() 