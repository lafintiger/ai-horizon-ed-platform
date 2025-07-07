#!/usr/bin/env python3
"""
🚀 PRE-FLIGHT DEPLOYMENT CHECKER
AI-Horizon Ed Platform - Heroku Deployment Verification

This script verifies all deployment requirements are met without modifying anything.
Run this BEFORE attempting deployment to catch any issues.
"""

import os
import json
import requests
import sys
from pathlib import Path

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_status(message, status="info"):
    if status == "success":
        print(f"{Colors.GREEN}✅ {message}{Colors.END}")
    elif status == "error":
        print(f"{Colors.RED}❌ {message}{Colors.END}")
    elif status == "warning":
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")
    else:
        print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def check_file_exists(filepath, description):
    """Check if required file exists"""
    if Path(filepath).exists():
        print_status(f"{description}: {filepath}", "success")
        return True
    else:
        print_status(f"{description} MISSING: {filepath}", "error")
        return False

def check_local_server():
    """Verify local server is responding"""
    try:
        response = requests.get("http://localhost:9000/api/database/stats", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_status(f"Local server responding: {data['total_resources']} resources, {data['emerging_skills_count']} skills", "success")
            return True, data
        else:
            print_status(f"Local server error: HTTP {response.status_code}", "error")
            return False, None
    except requests.exceptions.RequestException as e:
        print_status(f"Local server not accessible: {e}", "error")
        return False, None

def check_deployment_files():
    """Check all required deployment files"""
    files_ok = True
    
    # Check Procfile
    if check_file_exists("aih_edu/Procfile", "Procfile"):
        with open("aih_edu/Procfile", "r") as f:
            content = f.read().strip()
            if "gunicorn app:app" in content:
                print_status("Procfile contains correct gunicorn command", "success")
            else:
                print_status("Procfile may have incorrect command", "warning")
    else:
        files_ok = False
    
    # Check requirements.txt
    if check_file_exists("aih_edu/requirements.txt", "Requirements file"):
        with open("aih_edu/requirements.txt", "r") as f:
            content = f.read()
            required_packages = ["Flask", "anthropic", "openai", "gunicorn"]
            missing_packages = []
            for package in required_packages:
                if package.lower() not in content.lower():
                    missing_packages.append(package)
            
            if not missing_packages:
                print_status("All required packages found in requirements.txt", "success")
            else:
                print_status(f"Missing packages: {', '.join(missing_packages)}", "error")
                files_ok = False
    else:
        files_ok = False
    
    # Check runtime.txt
    if check_file_exists("aih_edu/runtime.txt", "Runtime file"):
        with open("aih_edu/runtime.txt", "r") as f:
            python_version = f.read().strip()
            if python_version.startswith("python-3."):
                print_status(f"Python version specified: {python_version}", "success")
            else:
                print_status(f"Invalid Python version: {python_version}", "warning")
    else:
        files_ok = False
    
    # Check database export
    if check_file_exists("aih_edu/heroku_export.json", "Database export"):
        try:
            with open("aih_edu/heroku_export.json", "r") as f:
                data = json.load(f)
                if "resources" in data and len(data["resources"]) > 0:
                    print_status(f"Database export contains {len(data['resources'])} resources", "success")
                else:
                    print_status("Database export appears empty", "error")
                    files_ok = False
        except json.JSONDecodeError:
            print_status("Database export is not valid JSON", "error")
            files_ok = False
    else:
        files_ok = False
    
    return files_ok

def check_git_status():
    """Check git repository status"""
    try:
        import subprocess
        result = subprocess.run(["git", "status", "--porcelain"], 
                              capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            if result.stdout.strip():
                print_status("Git has uncommitted changes - ready for commit", "success")
            else:
                print_status("Git working directory clean", "success")
            return True
        else:
            print_status("Git status check failed", "warning")
            return False
    except FileNotFoundError:
        print_status("Git not found - ensure you're in a git repository", "error")
        return False

def main():
    """Run all pre-flight checks"""
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("🚀 AI-HORIZON ED PLATFORM - PRE-FLIGHT DEPLOYMENT CHECK")
    print("=" * 60)
    print(f"{Colors.END}")
    
    all_checks_passed = True
    
    # Check 1: Local Server
    print(f"\n{Colors.BOLD}📡 CHECKING LOCAL SERVER{Colors.END}")
    server_ok, server_data = check_local_server()
    if not server_ok:
        all_checks_passed = False
        print_status("Start local server with: cd aih_edu && python app.py", "warning")
    
    # Check 2: Deployment Files
    print(f"\n{Colors.BOLD}📁 CHECKING DEPLOYMENT FILES{Colors.END}")
    files_ok = check_deployment_files()
    if not files_ok:
        all_checks_passed = False
    
    # Check 3: Git Status
    print(f"\n{Colors.BOLD}📋 CHECKING GIT REPOSITORY{Colors.END}")
    git_ok = check_git_status()
    if not git_ok:
        all_checks_passed = False
    
    # Check 4: Required Environment Variables
    print(f"\n{Colors.BOLD}🔑 CHECKING REQUIRED API KEYS{Colors.END}")
    required_keys = ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "PERPLEXITY_API_KEY"]
    
    print_status("Note: API keys should be set in Heroku, not locally", "info")
    print_status("Run: heroku config:set ANTHROPIC_API_KEY=your_key_here", "info")
    print_status("Run: heroku config:set OPENAI_API_KEY=your_key_here", "info") 
    print_status("Run: heroku config:set PERPLEXITY_API_KEY=your_key_here", "info")
    
    # Final Summary
    print(f"\n{Colors.BOLD}📊 PRE-FLIGHT SUMMARY{Colors.END}")
    print("-" * 40)
    
    if all_checks_passed:
        print_status("ALL PRE-FLIGHT CHECKS PASSED! ✈️", "success")
        print_status("Ready for deployment to Heroku", "success")
        
        if server_data:
            print(f"\n{Colors.BOLD}Current Database State:{Colors.END}")
            print(f"  • Total Resources: {server_data.get('total_resources', 'Unknown')}")
            print(f"  • Emerging Skills: {server_data.get('emerging_skills_count', 'Unknown')}")
            print(f"  • Average Quality: {server_data.get('average_quality', 'Unknown')}")
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎯 NEXT STEPS:{Colors.END}")
        print("1. Ensure you have your API keys ready")
        print("2. Run: heroku config:set [API_KEYS]")
        print("3. Execute deployment plan")
        
        return 0
    else:
        print_status("PRE-FLIGHT CHECKS FAILED!", "error")
        print_status("Fix the above issues before deployment", "error")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 