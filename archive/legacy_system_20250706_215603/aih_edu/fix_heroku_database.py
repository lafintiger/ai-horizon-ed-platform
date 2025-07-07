#!/usr/bin/env python3
"""
Fix Heroku Database Population
Properly populate Heroku with all resources and learning content
"""

import os
import psycopg2
import json
from urllib.parse import urlparse
from utils.database import DatabaseManager

def get_heroku_db_connection():
    """Get Heroku database connection"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    # Parse the database URL
    parsed = urlparse(database_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password,
        port=parsed.port
    )
    return conn

def populate_heroku_database():
    """Populate Heroku database with all resources"""
    print("🔄 Starting Heroku database population...")
    
    # Get local database data
    local_db = DatabaseManager()
    all_resources = local_db.get_all_resources()
    all_skills = local_db.get_all_skills()
    
    print(f"📊 Found {len(all_resources)} resources and {len(all_skills)} skills locally")
    
    # Connect to Heroku
    heroku_conn = get_heroku_db_connection()
    heroku_cursor = heroku_conn.cursor()
    
    try:
        # Clear existing data
        print("🧹 Clearing existing Heroku data...")
        heroku_cursor.execute("DELETE FROM resource_questions")
        heroku_cursor.execute("DELETE FROM resource_exercises") 
        heroku_cursor.execute("DELETE FROM skill_resources")
        heroku_cursor.execute("DELETE FROM resources")
        heroku_cursor.execute("DELETE FROM skills")
        
        # Insert skills
        print("📝 Inserting skills...")
        for skill in all_skills:
            heroku_cursor.execute("""
                INSERT INTO skills (id, skill_name, description, category, keywords, emerging_trend)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                skill['id'],
                skill['skill_name'],
                skill.get('description', ''),
                skill.get('category', ''),
                skill.get('keywords', ''),
                skill.get('emerging_trend', False)
            ))
        
        # Insert resources
        print("📚 Inserting resources...")
        for resource in all_resources:
            heroku_cursor.execute("""
                INSERT INTO resources (id, title, url, description, resource_type, 
                                     difficulty_level, estimated_time, cost, keywords, 
                                     source_platform, rating, publication_date, 
                                     last_updated, content_format, author, 
                                     prerequisites, learning_objectives, tags, 
                                     engagement_metrics, quality_score, 
                                     verification_status, ai_analysis_complete)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                resource['id'],
                resource['title'],
                resource['url'],
                resource.get('description', ''),
                resource.get('resource_type', ''),
                resource.get('difficulty_level', ''),
                resource.get('estimated_time', 0),
                resource.get('cost', 0),
                resource.get('keywords', ''),
                resource.get('source_platform', ''),
                resource.get('rating', 0),
                resource.get('publication_date'),
                resource.get('last_updated'),
                resource.get('content_format', ''),
                resource.get('author', ''),
                resource.get('prerequisites', ''),
                resource.get('learning_objectives', ''),
                resource.get('tags', ''),
                resource.get('engagement_metrics', ''),
                resource.get('quality_score', 0),
                resource.get('verification_status', ''),
                resource.get('ai_analysis_complete', False)
            ))
        
        # Insert skill-resource relationships
        print("🔗 Inserting skill-resource relationships...")
        for skill in all_skills:
            skill_resources = local_db.get_resources_for_skill(skill['id'])
            for resource in skill_resources:
                heroku_cursor.execute("""
                    INSERT INTO skill_resources (skill_id, resource_id, relevance_score)
                    VALUES (%s, %s, %s)
                """, (skill['id'], resource['id'], resource.get('relevance_score', 0.5)))
        
        # Commit all changes
        heroku_conn.commit()
        print("✅ Successfully populated Heroku database!")
        
        # Check final counts
        heroku_cursor.execute("SELECT COUNT(*) FROM resources")
        resource_count = heroku_cursor.fetchone()[0]
        
        heroku_cursor.execute("SELECT COUNT(*) FROM skills")
        skill_count = heroku_cursor.fetchone()[0]
        
        print(f"📊 Final Heroku database stats:")
        print(f"   Resources: {resource_count}")
        print(f"   Skills: {skill_count}")
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        heroku_conn.rollback()
        raise
    finally:
        heroku_cursor.close()
        heroku_conn.close()

if __name__ == "__main__":
    populate_heroku_database() 