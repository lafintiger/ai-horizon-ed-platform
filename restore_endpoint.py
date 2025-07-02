#!/usr/bin/env python3
"""
Simple database restoration endpoint for Heroku
Can be called to restore all skills and resources
"""

import requests
import json

def restore_heroku_database():
    """Restore database by calling individual skill discovery endpoints"""
    
    base_url = "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com"
    
    # Skills to restore with their exact names
    skills_to_restore = [
        "Zero Trust Architecture",
        "AI-Enhanced SIEM", 
        "Cloud Security Posture Management",
        "Quantum-Safe Cryptography",
        "Vibe Coding",
        "Ethical Hacking and Penetration Testing",
        "Prompt Engineering"
    ]
    
    print("🚨 RESTORING HEROKU DATABASE")
    print("=" * 50)
    
    for skill in skills_to_restore:
        skill_url = skill.lower().replace(" ", "-").replace("&", "and")
        
        print(f"\n🔍 Discovering resources for: {skill}")
        
        try:
            # Try to trigger discovery for this skill
            response = requests.post(f"{base_url}/api/discover/{skill_url}", 
                                   json={"skill_name": skill},
                                   timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {skill}: {len(result.get('resources', []))} resources discovered")
            else:
                print(f"❌ {skill}: Failed to discover resources (Status: {response.status_code})")
                
        except Exception as e:
            print(f"❌ {skill}: Error - {str(e)}")
    
    print(f"\n🎯 Database restoration completed!")
    print(f"Check: {base_url}/api/database/stats")

if __name__ == "__main__":
    restore_heroku_database() 