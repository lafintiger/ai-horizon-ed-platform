#!/usr/bin/env python3
"""
Import JSON Data to PostgreSQL
Import exported JSON data to Heroku PostgreSQL
"""

import os
import json
import psycopg2
import psycopg2.extras
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_postgres_connection():
    """Get PostgreSQL connection using DATABASE_URL"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    logger.info("🔗 Connecting to PostgreSQL...")
    
    # Parse URL
    parsed = urlparse(database_url)
    
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        database=parsed.path[1:],  # Remove leading slash
        user=parsed.username,
        password=parsed.password
    )
    
    return conn

def clear_postgres_data(conn):
    """Clear all existing data from PostgreSQL"""
    logger.info("🧹 Clearing existing PostgreSQL data...")
    
    with conn.cursor() as cursor:
        # Clear in correct order due to foreign keys
        cursor.execute("TRUNCATE TABLE resource_questions RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE resource_exercises RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE skill_resources RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE educational_resources RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE emerging_skills RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE content_analysis_queue RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE learning_content RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE skill_learning_paths RESTART IDENTITY CASCADE")
        cursor.execute("TRUNCATE TABLE learning_sessions RESTART IDENTITY CASCADE")
    
    conn.commit()
    logger.info("✅ PostgreSQL data cleared")

def import_skills(conn, skills):
    """Import skills to PostgreSQL"""
    logger.info(f"📝 Importing {len(skills)} skills...")
    
    with conn.cursor() as cursor:
        for skill in skills:
            cursor.execute("""
                INSERT INTO emerging_skills 
                (skill_name, category, urgency_score, demand_trend, source_analysis, 
                 description, related_skills, keywords, job_market_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                skill['skill_name'],
                skill.get('category', ''),
                skill.get('urgency_score', 0.0),
                skill.get('demand_trend', 'stable'),
                skill.get('source_analysis', ''),
                skill.get('description', ''),
                skill.get('related_skills', '[]'),
                skill.get('keywords', ''),
                skill.get('job_market_data', '{}')
            ))
    
    conn.commit()
    logger.info("✅ Skills imported")

def import_resources(conn, resources):
    """Import resources to PostgreSQL"""
    logger.info(f"📚 Importing {len(resources)} resources...")
    
    with conn.cursor() as cursor:
        for resource in resources:
            cursor.execute("""
                INSERT INTO educational_resources 
                (title, description, url, resource_type, cost_type, difficulty_level,
                 estimated_duration, author, tags, skill_category, quality_score,
                 discovery_method, ai_analysis_score, ai_analysis_details, 
                 learning_level, sequence_order, prerequisites, learning_objectives)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                resource['title'],
                resource.get('description', ''),
                resource['url'],
                resource.get('resource_type', ''),
                resource.get('cost_type', 'unknown'),
                resource.get('difficulty_level', 'unknown'),
                resource.get('estimated_duration', ''),
                resource.get('author', ''),
                resource.get('tags', ''),
                resource.get('skill_category', ''),
                resource.get('quality_score', 0.0),
                resource.get('discovery_method', ''),
                resource.get('ai_analysis_score', 0.0),
                resource.get('ai_analysis_details', ''),
                resource.get('learning_level', ''),
                resource.get('sequence_order', 0),
                resource.get('prerequisites', '[]'),
                resource.get('learning_objectives', '[]')
            ))
    
    conn.commit()
    logger.info("✅ Resources imported")

def import_skill_resources(conn, skill_resources):
    """Import skill-resource mappings to PostgreSQL"""
    logger.info(f"🔗 Importing {len(skill_resources)} skill-resource mappings...")
    
    with conn.cursor() as cursor:
        for mapping in skill_resources:
            cursor.execute("""
                INSERT INTO skill_resources (skill_id, resource_id, relevance_score)
                VALUES (%s, %s, %s)
            """, (
                mapping['skill_id'],
                mapping['resource_id'],
                mapping.get('relevance_score', 1.0)
            ))
    
    conn.commit()
    logger.info("✅ Skill-resource mappings imported")

def import_questions(conn, questions):
    """Import resource questions to PostgreSQL"""
    logger.info(f"❓ Importing {len(questions)} resource questions...")
    
    with conn.cursor() as cursor:
        for question in questions:
            cursor.execute("""
                INSERT INTO resource_questions (resource_id, questions_data)
                VALUES (%s, %s)
            """, (
                question['resource_id'],
                question['questions_data']
            ))
    
    conn.commit()
    logger.info("✅ Resource questions imported")

def verify_import(conn):
    """Verify the import was successful"""
    logger.info("🔍 Verifying import...")
    
    with conn.cursor() as cursor:
        # Count records
        cursor.execute("SELECT COUNT(*) FROM emerging_skills")
        skills_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM educational_resources")
        resources_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM skill_resources")
        mappings_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM resource_questions")
        questions_count = cursor.fetchone()[0]
        
        logger.info(f"📊 Final counts: {skills_count} skills, {resources_count} resources, {mappings_count} mappings, {questions_count} questions")
        
        # Test a sample query
        cursor.execute("""
            SELECT s.skill_name, COUNT(sr.resource_id) as resource_count
            FROM emerging_skills s
            LEFT JOIN skill_resources sr ON s.id = sr.skill_id
            GROUP BY s.id, s.skill_name
            ORDER BY resource_count DESC
        """)
        
        logger.info("🎯 Skills with resource counts:")
        for skill_name, count in cursor.fetchall():
            logger.info(f"  - {skill_name}: {count} resources")

def main():
    """Main import function"""
    try:
        logger.info("🚀 Starting PostgreSQL import...")
        
        # Load JSON data
        with open('heroku_import_data.json', 'r') as f:
            data = json.load(f)
        
        logger.info(f"📊 Loaded data: {data['export_metadata']}")
        
        # Connect to Postgres
        pg_conn = get_postgres_connection()
        
        # Clear existing data
        clear_postgres_data(pg_conn)
        
        # Import data
        import_skills(pg_conn, data['skills'])
        import_resources(pg_conn, data['resources'])
        import_skill_resources(pg_conn, data['skill_resources'])
        import_questions(pg_conn, data['questions'])
        
        # Verify import
        verify_import(pg_conn)
        
        # Close connection
        pg_conn.close()
        
        logger.info("🎉 PostgreSQL import completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        raise

if __name__ == "__main__":
    main() 