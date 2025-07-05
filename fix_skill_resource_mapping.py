#!/usr/bin/env python3
"""
Fix skill-to-resource mapping by connecting skills to their appropriate resources
based on category matching.
"""

import sqlite3
from datetime import datetime
import sys

def get_skill_mappings():
    """Define mappings between skill names and resource categories."""
    return {
        "AI-Enhanced SIEM": ["ai-augmented_threat_intelligence", "cybersecurity"],
        "Prompt Engineering": ["prompt_engineering_for_security", "ai-technology"],
        "Quantum-Safe Cryptography": ["quantum-cryptography"],
        "Zero Trust Architecture": ["cybersecurity", "Network Security"],
        "Cloud Security Posture Management": ["cybersecurity", "Network Security"],
        # Note: "Ethical Hacking and Penetration Testing" and "Vibe Coding" already have mappings
    }

def fix_skill_resource_mapping():
    """Fix the skill-to-resource mapping in the database."""
    conn = sqlite3.connect('data/aih_edu.db')
    cursor = conn.cursor()
    
    try:
        # Get skill mappings
        skill_mappings = get_skill_mappings()
        
        # Get all skills
        cursor.execute("SELECT id, skill_name FROM emerging_skills")
        skills = cursor.fetchall()
        
        total_mappings = 0
        
        for skill_id, skill_name in skills:
            if skill_name in skill_mappings:
                categories = skill_mappings[skill_name]
                print(f"\nProcessing skill: {skill_name} (ID: {skill_id})")
                
                # Get resources for these categories
                placeholders = ','.join(['?' for _ in categories])
                cursor.execute(f"""
                    SELECT id, title, skill_category 
                    FROM educational_resources 
                    WHERE skill_category IN ({placeholders})
                """, categories)
                
                resources = cursor.fetchall()
                print(f"Found {len(resources)} resources for categories: {', '.join(categories)}")
                
                # Insert mappings
                for resource_id, title, category in resources:
                    # Check if mapping already exists
                    cursor.execute("""
                        SELECT id FROM skill_resource_mapping 
                        WHERE skill_id = ? AND resource_id = ?
                    """, (skill_id, resource_id))
                    
                    if not cursor.fetchone():
                        # Calculate relevance score based on category match
                        relevance_score = 0.9 if category in categories else 0.7
                        
                        # Determine resource type
                        resource_type = "foundation" if "basic" in title.lower() else "practical"
                        
                        cursor.execute("""
                            INSERT INTO skill_resource_mapping 
                            (skill_id, resource_id, relevance_score, resource_type_for_skill, auto_discovered, discovery_date)
                            VALUES (?, ?, ?, ?, 1, ?)
                        """, (skill_id, resource_id, relevance_score, resource_type, datetime.now()))
                        
                        total_mappings += 1
                        print(f"  ✓ Mapped: {title[:50]}{'...' if len(title) > 50 else ''}")
        
        # Commit changes
        conn.commit()
        print(f"\n🎉 Successfully created {total_mappings} new skill-resource mappings!")
        
        # Show final counts
        cursor.execute("""
            SELECT 
                es.skill_name,
                COUNT(srm.resource_id) as resource_count
            FROM emerging_skills es
            LEFT JOIN skill_resource_mapping srm ON es.id = srm.skill_id
            GROUP BY es.id, es.skill_name
            ORDER BY resource_count DESC
        """)
        
        print("\n📊 Final skill-resource mapping counts:")
        for skill_name, count in cursor.fetchall():
            print(f"  {skill_name}: {count} resources")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    fix_skill_resource_mapping() 