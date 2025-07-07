#!/usr/bin/env python3
"""
Export Local Data for Heroku Import
Export SQLite data to JSON format for PostgreSQL import
"""

import sqlite3
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def export_local_data():
    """Export all local SQLite data to JSON"""
    logger.info("📊 Exporting local SQLite data...")
    
    # Connect to local SQLite database
    conn = sqlite3.connect('data/aih_edu.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    export_data = {}
    
    # Export skills
    try:
        cursor.execute("SELECT * FROM emerging_skills ORDER BY id")
        skills = [dict(row) for row in cursor.fetchall()]
        export_data['skills'] = skills
        logger.info(f"✅ Exported {len(skills)} skills")
    except Exception as e:
        logger.warning(f"⚠️ Could not export skills: {e}")
        export_data['skills'] = []
    
    # Export resources
    try:
        cursor.execute("SELECT * FROM educational_resources ORDER BY id")
        resources = [dict(row) for row in cursor.fetchall()]
        export_data['resources'] = resources
        logger.info(f"✅ Exported {len(resources)} resources")
    except Exception as e:
        logger.warning(f"⚠️ Could not export resources: {e}")
        export_data['resources'] = []
    
    # Export skill-resource mappings
    try:
        cursor.execute("SELECT * FROM skill_resources ORDER BY id")
        skill_resources = [dict(row) for row in cursor.fetchall()]
        export_data['skill_resources'] = skill_resources
        logger.info(f"✅ Exported {len(skill_resources)} skill-resource mappings")
    except Exception as e:
        logger.warning(f"⚠️ Could not export skill_resources: {e}")
        export_data['skill_resources'] = []
    
    # Export questions
    try:
        cursor.execute("SELECT * FROM resource_questions ORDER BY id")
        questions = [dict(row) for row in cursor.fetchall()]
        export_data['questions'] = questions
        logger.info(f"✅ Exported {len(questions)} questions")
    except Exception as e:
        logger.warning(f"⚠️ Could not export questions: {e}")
        export_data['questions'] = []
    
    conn.close()
    
    # Add export metadata
    export_data['export_metadata'] = {
        'timestamp': datetime.now().isoformat(),
        'source': 'local SQLite',
        'total_skills': len(export_data['skills']),
        'total_resources': len(export_data['resources']),
        'total_mappings': len(export_data['skill_resources']),
        'total_questions': len(export_data['questions'])
    }
    
    # Write to JSON file
    with open('heroku_import_data.json', 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    logger.info("📁 Data exported to heroku_import_data.json")
    logger.info(f"📊 Summary: {export_data['export_metadata']}")
    
    return export_data

if __name__ == "__main__":
    export_local_data() 