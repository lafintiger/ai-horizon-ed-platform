#!/usr/bin/env python3
"""
PostgreSQL Migration Script
Migrate data from local SQLite to Heroku PostgreSQL
"""

import os
import sqlite3
import psycopg2
import psycopg2.extras
import json
import logging
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_local_sqlite_data():
    """Get all data from local SQLite database"""
    logger.info("📖 Reading local SQLite database...")
    
    conn = sqlite3.connect('data/aih_edu.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get skills
    cursor.execute("SELECT * FROM emerging_skills ORDER BY id")
    skills = [dict(row) for row in cursor.fetchall()]
    
    # Get resources  
    cursor.execute("SELECT * FROM educational_resources ORDER BY id")
    resources = [dict(row) for row in cursor.fetchall()]
    
    # Get skill-resource mappings
    cursor.execute("SELECT * FROM skill_resources ORDER BY id")
    skill_resources = [dict(row) for row in cursor.fetchall()]
    
    # Get questions
    cursor.execute("SELECT * FROM resource_questions ORDER BY id")
    questions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    logger.info(f"✅ Found {len(skills)} skills, {len(resources)} resources, {len(skill_resources)} mappings, {len(questions)} questions")
    return skills, resources, skill_resources, questions

def get_postgres_connection():
    """Get PostgreSQL connection using DATABASE_URL"""
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable not set")
    
    logger.info("🔗 Connecting to Heroku PostgreSQL...")
    
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

def migrate_skills(conn, skills):
    """Migrate skills to PostgreSQL"""
    logger.info(f"📝 Migrating {len(skills)} skills...")
    
    with conn.cursor() as cursor:
        for skill in skills:
            cursor.execute("""
                INSERT INTO emerging_skills 
                (skill_name, category, urgency_score, demand_trend, source_analysis, 
                 description, related_skills, keywords, job_market_data, created_date, updated_date, discovery_status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                skill['skill_name'],
                skill.get('category', ''),
                skill.get('urgency_score', 0.0),
                skill.get('demand_trend', 'stable'),
                skill.get('source_analysis', ''),
                skill.get('description', ''),
                skill.get('related_skills', '[]'),
                skill.get('keywords', ''),
                skill.get('job_market_data', '{}'),
                skill.get('created_date', 'now()'),
                skill.get('updated_date', 'now()'),
                skill.get('discovery_status', 'pending')
            ))
    
    conn.commit()
    logger.info("✅ Skills migrated")

def migrate_resources(conn, resources):
    """Migrate resources to PostgreSQL"""
    logger.info(f"📚 Migrating {len(resources)} resources...")
    
    with conn.cursor() as cursor:
        for resource in resources:
            cursor.execute("""
                INSERT INTO educational_resources 
                (title, description, url, resource_type, cost_type, difficulty_level,
                 estimated_duration, author, tags, skill_category, quality_score,
                 discovery_method, ai_analysis_score, ai_analysis_details, ai_analysis_date,
                 learning_level, sequence_order, prerequisites, learning_objectives, created_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                resource.get('ai_analysis_date'),
                resource.get('learning_level', ''),
                resource.get('sequence_order', 0),
                resource.get('prerequisites', '[]'),
                resource.get('learning_objectives', '[]'),
                resource.get('created_date', 'now()')
            ))
    
    conn.commit()
    logger.info("✅ Resources migrated")

def migrate_skill_resources(conn, skill_resources):
    """Migrate skill-resource mappings to PostgreSQL"""
    logger.info(f"🔗 Migrating {len(skill_resources)} skill-resource mappings...")
    
    with conn.cursor() as cursor:
        for mapping in skill_resources:
            cursor.execute("""
                INSERT INTO skill_resources (skill_id, resource_id, relevance_score, created_date)
                VALUES (%s, %s, %s, %s)
            """, (
                mapping['skill_id'],
                mapping['resource_id'],
                mapping.get('relevance_score', 1.0),
                mapping.get('created_date', 'now()')
            ))
    
    conn.commit()
    logger.info("✅ Skill-resource mappings migrated")

def migrate_questions(conn, questions):
    """Migrate resource questions to PostgreSQL"""
    logger.info(f"❓ Migrating {len(questions)} resource questions...")
    
    with conn.cursor() as cursor:
        for question in questions:
            cursor.execute("""
                INSERT INTO resource_questions (resource_id, questions_data, created_date)
                VALUES (%s, %s, %s)
            """, (
                question['resource_id'],
                question['questions_data'],
                question.get('created_date', 'now()')
            ))
    
    conn.commit()
    logger.info("✅ Resource questions migrated")

def verify_migration(conn):
    """Verify the migration was successful"""
    logger.info("🔍 Verifying migration...")
    
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
    """Main migration function"""
    try:
        logger.info("🚀 Starting PostgreSQL migration...")
        
        # Get local data
        skills, resources, skill_resources, questions = get_local_sqlite_data()
        
        # Connect to Postgres
        pg_conn = get_postgres_connection()
        
        # Clear existing data
        clear_postgres_data(pg_conn)
        
        # Migrate data
        migrate_skills(pg_conn, skills)
        migrate_resources(pg_conn, resources)
        migrate_skill_resources(pg_conn, skill_resources)
        migrate_questions(pg_conn, questions)
        
        # Verify migration
        verify_migration(pg_conn)
        
        # Close connection
        pg_conn.close()
        
        logger.info("🎉 PostgreSQL migration completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    main() 