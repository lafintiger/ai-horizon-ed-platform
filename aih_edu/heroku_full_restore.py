#!/usr/bin/env python3
"""
COMPLETE DATABASE RESTORATION for Heroku
Transfers ALL local skills and resources to Heroku
"""

import json
import requests
from utils.database import DatabaseManager
from datetime import datetime

def full_heroku_restore():
    """Transfer complete local database to Heroku"""
    
    print("🚨 COMPLETE DATABASE RESTORATION STARTING")
    print("=" * 60)
    
    # Get local database
    db = DatabaseManager()
    
    # Get all local skills
    local_skills = db.get_emerging_skills()
    print(f"📊 Local database has {len(local_skills)} skills")
    
    total_resources = 0
    
    # Get all resources for each skill
    for skill in local_skills:
        skill_resources = db.get_resources_for_skill(skill['id'])
        total_resources += len(skill_resources)
        print(f"  📚 {skill['skill_name']}: {len(skill_resources)} resources")
    
    print(f"📊 Total local resources: {total_resources}")
    print()
    
    # Prepare data for Heroku restoration
    restoration_data = {
        'skills': [],
        'resources': [],
        'mappings': []
    }
    
    # Collect all skills
    for skill in local_skills:
        skill_data = {
            'skill_name': skill['skill_name'],
            'category': skill['category'],
            'urgency_score': skill['urgency_score'],
            'demand_trend': skill['demand_trend'],
            'source_analysis': skill['source_analysis'],
            'description': skill['description'],
            'related_skills': skill.get('related_skills', [])
        }
        restoration_data['skills'].append(skill_data)
        
        # Get resources for this skill
        skill_resources = db.get_resources_for_skill(skill['id'])
        
        for resource in skill_resources:
            resource_data = {
                'title': resource['title'],
                'description': resource['description'],
                'url': resource['url'],
                'resource_type': resource['resource_type'],
                'skill_category': skill['category'],
                'learning_level': 'intermediate',
                'quality_score': resource.get('quality_score', 0.8),
                'keywords': resource.get('keywords', [])
            }
            restoration_data['resources'].append(resource_data)
            
            # Create mapping
            mapping = {
                'skill_name': skill['skill_name'],
                'resource_title': resource['title'],
                'relevance_score': 0.9,
                'resource_type_for_skill': 'foundation'
            }
            restoration_data['mappings'].append(mapping)
    
    # Save restoration data
    with open('complete_restoration_data.json', 'w') as f:
        json.dump(restoration_data, f, indent=2)
    
    print(f"✅ Prepared restoration data:")
    print(f"   - {len(restoration_data['skills'])} skills")
    print(f"   - {len(restoration_data['resources'])} resources") 
    print(f"   - {len(restoration_data['mappings'])} mappings")
    print(f"   - Saved to: complete_restoration_data.json")
    
    # Now upload to Heroku via API
    heroku_url = "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com"
    
    print(f"\n🚀 Uploading to Heroku: {heroku_url}")
    
    try:
        # Call emergency restore with full data
        response = requests.post(f"{heroku_url}/emergency-restore-full", 
                               json=restoration_data,
                               timeout=300)  # 5 minute timeout
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS! Restored {result.get('resources_added', 0)} resources")
            print(f"   Skills: {result.get('skills_count', 0)}")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
            # Fallback: use existing emergency-restore multiple times
            print("\n🔄 Trying fallback method...")
            for i in range(3):  # Try 3 times to get more resources
                response = requests.get(f"{heroku_url}/emergency-restore")
                if response.status_code == 200:
                    result = response.json()
                    print(f"   Attempt {i+1}: {result.get('resources_added', 0)} resources added")
                else:
                    print(f"   Attempt {i+1} failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error uploading to Heroku: {e}")
        print("💡 You can manually trigger bulk discovery in the admin panel")
    
    print(f"\n🎯 RESTORATION COMPLETE")
    print(f"📊 Your local database remains intact with all {total_resources} resources")

if __name__ == "__main__":
    full_heroku_restore() 