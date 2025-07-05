#!/usr/bin/env python3
"""
Link Resources to Skills in PostgreSQL
Create skill-resource mappings based on resource categories
"""

import os
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

def create_skill_resource_links(conn):
    """Create links between skills and resources based on categories"""
    logger.info("🔗 Creating skill-resource links...")
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        # Get all skills
        cursor.execute("SELECT id, skill_name, category FROM emerging_skills")
        skills = cursor.fetchall()
        
        # Get all resources
        cursor.execute("SELECT id, title, skill_category FROM educational_resources")
        resources = cursor.fetchall()
        
        logger.info(f"Found {len(skills)} skills and {len(resources)} resources")
        
        # Category mappings (flexible matching)
        links_created = 0
        
        for resource in resources:
            resource_category = (resource['skill_category'] or '').lower()
            
            # Find matching skills for this resource
            matched_skills = []
            
            # Direct category matches
            if 'vibe' in resource_category or 'coding' in resource_category:
                matched_skills.extend([s for s in skills if 'vibe' in s['skill_name'].lower()])
            
            if 'ai' in resource_category or 'siem' in resource_category:
                matched_skills.extend([s for s in skills if 'ai-enhanced siem' in s['skill_name'].lower()])
            
            if 'ethical' in resource_category or 'hacking' in resource_category or 'penetration' in resource_category:
                matched_skills.extend([s for s in skills if 'ethical hacking' in s['skill_name'].lower()])
            
            if 'prompt' in resource_category or 'engineering' in resource_category:
                matched_skills.extend([s for s in skills if 'prompt engineering' in s['skill_name'].lower()])
            
            if 'zero' in resource_category or 'trust' in resource_category:
                matched_skills.extend([s for s in skills if 'zero trust' in s['skill_name'].lower()])
            
            if 'quantum' in resource_category or 'cryptography' in resource_category:
                matched_skills.extend([s for s in skills if 'quantum' in s['skill_name'].lower()])
            
            if 'cloud' in resource_category or 'security' in resource_category or 'posture' in resource_category:
                matched_skills.extend([s for s in skills if 'cloud security' in s['skill_name'].lower()])
            
            # If no specific match, try broader cybersecurity categories
            if not matched_skills:
                if any(term in resource_category for term in ['security', 'cyber', 'network', 'malware', 'incident']):
                    # Distribute across cyber security skills
                    cyber_skills = [s for s in skills if any(term in s['skill_name'].lower() 
                                  for term in ['siem', 'ethical', 'zero trust', 'cloud security'])]
                    if cyber_skills:
                        matched_skills.append(cyber_skills[hash(resource['title']) % len(cyber_skills)])
            
            # If still no match, assign to a general skill
            if not matched_skills:
                # Default to AI-Enhanced SIEM for general cybersecurity content
                ai_siem_skills = [s for s in skills if 'ai-enhanced siem' in s['skill_name'].lower()]
                if ai_siem_skills:
                    matched_skills.append(ai_siem_skills[0])
            
            # Create links for matched skills
            for skill in matched_skills:
                try:
                    cursor.execute("""
                        INSERT INTO skill_resources (skill_id, resource_id, relevance_score)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (skill_id, resource_id) DO NOTHING
                    """, (skill['id'], resource['id'], 1.0))
                    links_created += 1
                except Exception as e:
                    logger.warning(f"Could not link resource {resource['id']} to skill {skill['id']}: {e}")
        
        conn.commit()
        logger.info(f"✅ Created {links_created} skill-resource links")

def verify_links(conn):
    """Verify the links were created successfully"""
    logger.info("🔍 Verifying skill-resource links...")
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
        cursor.execute("""
            SELECT s.skill_name, COUNT(sr.resource_id) as resource_count
            FROM emerging_skills s
            LEFT JOIN skill_resources sr ON s.id = sr.skill_id
            GROUP BY s.id, s.skill_name
            ORDER BY resource_count DESC
        """)
        
        results = cursor.fetchall()
        total_links = sum(r['resource_count'] for r in results)
        
        logger.info(f"📊 Total skill-resource links: {total_links}")
        logger.info("🎯 Skills with resource counts:")
        for result in results:
            logger.info(f"  - {result['skill_name']}: {result['resource_count']} resources")

def main():
    """Main function"""
    try:
        logger.info("🚀 Starting skill-resource linking...")
        
        # Connect to Postgres
        pg_conn = get_postgres_connection()
        
        # Create links
        create_skill_resource_links(pg_conn)
        
        # Verify links
        verify_links(pg_conn)
        
        # Close connection
        pg_conn.close()
        
        logger.info("🎉 Skill-resource linking completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Linking failed: {e}")
        raise

if __name__ == "__main__":
    main() 