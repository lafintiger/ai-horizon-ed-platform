#!/usr/bin/env python3
"""
Fix Heroku Resource Categorization
Updates cost_type and difficulty_level for all resources to enable proper sorting
"""

import os
import psycopg2
from urllib.parse import urlparse
import requests
import json

def fix_resource_categorization():
    """Fix the cost_type and difficulty_level for resources on Heroku"""
    
    # Get database URL from environment (this will be set on Heroku)
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL not found. Run this on Heroku or set the URL.")
        return
    
    # Parse the database URL for Heroku Postgres
    url = urlparse(database_url)
    
    # Resource categorization rules
    cost_categorization = {
        'youtube_video': 'free',
        'documentation': 'free',
        'tutorial': 'free',
        'article': 'free',
        'tool': 'freemium',  # Most tools have free tiers
        'online_course': 'paid',  # Most courses are paid
        'course': 'paid'
    }
    
    difficulty_categorization = {
        # Keywords that indicate beginner level
        'beginner_keywords': ['beginner', 'introduction', 'basics', 'fundamentals', 'getting started', 'tutorial'],
        # Keywords that indicate advanced level  
        'advanced_keywords': ['advanced', 'expert', 'master', 'professional', 'enterprise', 'architecture'],
        # Default to intermediate for everything else
    }
    
    try:
        # Connect to Heroku Postgres
        conn = psycopg2.connect(
            host=url.hostname,
            database=url.path[1:],
            user=url.username,
            password=url.password,
            port=url.port
        )
        cursor = conn.cursor()
        
        print("🔗 Connected to Heroku Postgres database")
        
        # Get all resources
        cursor.execute("SELECT id, title, description, resource_type, cost_type, difficulty_level FROM educational_resources")
        resources = cursor.fetchall()
        
        print(f"📊 Found {len(resources)} resources to categorize")
        
        updated_count = 0
        
        for resource in resources:
            resource_id, title, description, resource_type, current_cost, current_difficulty = resource
            
            # Determine cost type based on resource type
            new_cost_type = cost_categorization.get(resource_type, 'unknown')
            
            # Special cases for cost type
            if 'free' in title.lower() or 'free' in description.lower():
                new_cost_type = 'free'
            elif 'paid' in title.lower() or 'premium' in title.lower():
                new_cost_type = 'paid'
            elif 'udemy.com' in description or 'coursera.org' in description:
                new_cost_type = 'paid'
            
            # Determine difficulty level based on title and description content
            content = f"{title} {description}".lower()
            new_difficulty_level = 'intermediate'  # Default
            
            # Check for beginner indicators
            if any(keyword in content for keyword in difficulty_categorization['beginner_keywords']):
                new_difficulty_level = 'beginner'
            # Check for advanced indicators
            elif any(keyword in content for keyword in difficulty_categorization['advanced_keywords']):
                new_difficulty_level = 'advanced'
            
            # Update the resource if values changed
            if new_cost_type != current_cost or new_difficulty_level != current_difficulty:
                cursor.execute("""
                    UPDATE educational_resources 
                    SET cost_type = %s, difficulty_level = %s 
                    WHERE id = %s
                """, (new_cost_type, new_difficulty_level, resource_id))
                
                updated_count += 1
                print(f"✅ Updated resource {resource_id}: {title[:50]}... -> {new_cost_type}, {new_difficulty_level}")
        
        # Commit changes
        conn.commit()
        print(f"\n🎉 Successfully updated {updated_count} resources!")
        print("💡 Resources now have proper cost_type and difficulty_level for categorization")
        
        # Test the categorization
        cursor.execute("SELECT cost_type, COUNT(*) FROM educational_resources GROUP BY cost_type")
        cost_distribution = cursor.fetchall()
        
        cursor.execute("SELECT difficulty_level, COUNT(*) FROM educational_resources GROUP BY difficulty_level")  
        difficulty_distribution = cursor.fetchall()
        
        print("\n📊 Cost Distribution:")
        for cost, count in cost_distribution:
            print(f"   {cost}: {count} resources")
            
        print("\n📊 Difficulty Distribution:")
        for difficulty, count in difficulty_distribution:
            print(f"   {difficulty}: {count} resources")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing categorization: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("🚀 Fixing Heroku Resource Categorization...")
    success = fix_resource_categorization()
    if success:
        print("✅ Categorization fix completed successfully!")
    else:
        print("❌ Categorization fix failed!") 