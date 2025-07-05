#!/usr/bin/env python3
"""
Fix PostgreSQL Schema Issues
Update field lengths to accommodate real data
"""

import os
import psycopg2
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

def fix_schema(conn):
    """Fix PostgreSQL schema field lengths"""
    logger.info("🔧 Fixing PostgreSQL schema...")
    
    with conn.cursor() as cursor:
        # Update URL field to handle very long URLs
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN url TYPE TEXT")
        
        # Update other fields that might be too small
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN title TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN description TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN author TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN tags TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN estimated_duration TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN discovery_method TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN ai_analysis_details TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN learning_level TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN skill_category TYPE TEXT")
        cursor.execute("ALTER TABLE educational_resources ALTER COLUMN resource_type TYPE TEXT")
        
        # Update skill fields
        cursor.execute("ALTER TABLE emerging_skills ALTER COLUMN skill_name TYPE TEXT")
        cursor.execute("ALTER TABLE emerging_skills ALTER COLUMN description TYPE TEXT")
        cursor.execute("ALTER TABLE emerging_skills ALTER COLUMN category TYPE TEXT")
        cursor.execute("ALTER TABLE emerging_skills ALTER COLUMN source_analysis TYPE TEXT")
        cursor.execute("ALTER TABLE emerging_skills ALTER COLUMN demand_trend TYPE TEXT")
        cursor.execute("ALTER TABLE emerging_skills ALTER COLUMN keywords TYPE TEXT")
        
    conn.commit()
    logger.info("✅ Schema updated successfully")

def main():
    """Main function"""
    try:
        logger.info("🚀 Starting PostgreSQL schema fix...")
        
        # Connect to Postgres
        pg_conn = get_postgres_connection()
        
        # Fix schema
        fix_schema(pg_conn)
        
        # Close connection
        pg_conn.close()
        
        logger.info("🎉 PostgreSQL schema fix completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Schema fix failed: {e}")
        raise

if __name__ == "__main__":
    main() 