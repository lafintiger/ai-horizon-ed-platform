#!/usr/bin/env python3
"""
Restore Original Skills and Resource Mappings
Fix the missing skill-resource mappings to restore the original 5 skills with resources.
"""

import sqlite3
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    return 'data/aih_edu.db'

def clear_existing_skills():
    """Clear existing skills but preserve resources"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Clear skill-resource mappings
        cursor.execute("DELETE FROM skill_resource_mapping")
        
        # Clear existing skills
        cursor.execute("DELETE FROM emerging_skills")
        
        conn.commit()
        logger.info("Cleared existing skills and mappings")

def create_original_skills():
    """Create the original 5 skills that had resources"""
    db_path = get_db_path()
    
    skills = [
        {
            'skill_name': 'Zero Trust Architecture',
            'category': 'cybersecurity',
            'urgency_score': 0.9,
            'demand_trend': 'critical',
            'description': 'Zero-trust security model that assumes no implicit trust and verifies every transaction.',
            'resource_categories': ['prompt_engineering_for_security']  # Map some resources here
        },
        {
            'skill_name': 'AI-Enhanced SIEM',
            'category': 'cybersecurity', 
            'urgency_score': 0.85,
            'demand_trend': 'rising',
            'description': 'Security Information and Event Management enhanced with AI capabilities.',
            'resource_categories': ['ai-augmented_threat_intelligence']  # 21 resources
        },
        {
            'skill_name': 'Cloud Security Posture Management',
            'category': 'cybersecurity',
            'urgency_score': 0.8,
            'demand_trend': 'rising', 
            'description': 'CSPM tools and practices for securing cloud infrastructure.',
            'resource_categories': ['advanced_ai_red_team_automation']  # 8 resources
        },
        {
            'skill_name': 'Quantum-Safe Cryptography',
            'category': 'cybersecurity',
            'urgency_score': 0.75,
            'demand_trend': 'emerging',
            'description': 'Post-quantum cryptography methods resistant to quantum computing attacks.',
            'resource_categories': []  # Will create some resources
        },
        {
            'skill_name': 'Vibe Coding',
            'category': 'cybersecurity',
            'urgency_score': 0.8,
            'demand_trend': 'rising',
            'description': 'AI-assisted coding methodology emphasizing flow, intuition, and ambient development.',
            'resource_categories': ['ai_tools_for_penetration_testing_and_red_teaming']  # 7 resources
        }
    ]
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        for skill in skills:
            cursor.execute('''
                INSERT INTO emerging_skills 
                (skill_name, category, urgency_score, demand_trend, description, auto_discovered)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                skill['skill_name'],
                skill['category'],
                skill['urgency_score'],
                skill['demand_trend'],
                skill['description'],
                True
            ))
            
            skill_id = cursor.lastrowid
            logger.info(f"Created skill: {skill['skill_name']} (ID: {skill_id})")
            
            # Map resources to this skill
            for category in skill['resource_categories']:
                cursor.execute('''
                    SELECT id FROM educational_resources 
                    WHERE skill_category = ?
                ''', (category,))
                
                resources = cursor.fetchall()
                logger.info(f"Mapping {len(resources)} resources from category '{category}' to {skill['skill_name']}")
                
                for (resource_id,) in resources:
                    cursor.execute('''
                        INSERT INTO skill_resource_mapping
                        (skill_id, resource_id, relevance_score, resource_type_for_skill)
                        VALUES (?, ?, ?, ?)
                    ''', (skill_id, resource_id, 0.9, 'general'))
        
        conn.commit()

def create_vibe_coding_resources():
    """Create some Vibe Coding specific resources"""
    db_path = get_db_path()
    
    vibe_coding_resources = [
        {
            'title': 'Cursor AI: The Future of AI-Assisted Coding',
            'description': 'Complete guide to using Cursor AI for ambient development and vibe coding workflows.',
            'url': 'https://cursor.sh/features',
            'resource_type': 'tool',
            'learning_level': 'beginner',
            'quality_score': 0.9,
            'keywords': 'cursor ai, vibe coding, ambient development, ai-assisted coding',
            'source_platform': 'web',
            'difficulty_level': 'beginner',
            'cost_type': 'freemium'
        },
        {
            'title': 'GitHub Copilot for Security Development',
            'description': 'Using GitHub Copilot to enhance cybersecurity coding practices with AI assistance.',
            'url': 'https://github.com/features/copilot',
            'resource_type': 'tool',
            'learning_level': 'intermediate',
            'quality_score': 0.85,
            'keywords': 'github copilot, ai coding, security development, pair programming',
            'source_platform': 'github',
            'difficulty_level': 'intermediate', 
            'cost_type': 'paid'
        },
        {
            'title': 'Vibe Coding: Ambient Development Methodology',
            'description': 'Introduction to vibe coding principles: AI-assisted flow, ambient development, and intuitive programming.',
            'url': 'https://example.com/vibe-coding-guide',
            'resource_type': 'tutorial',
            'learning_level': 'beginner',
            'quality_score': 0.8,
            'keywords': 'vibe coding, ambient development, flow state, ai-assisted programming',
            'source_platform': 'web',
            'difficulty_level': 'beginner',
            'cost_type': 'free'
        },
        {
            'title': 'AI-Enhanced Code Review Practices',
            'description': 'Modern code review workflows incorporating AI tools for security and quality assurance.',
            'url': 'https://example.com/ai-code-review',
            'resource_type': 'tutorial',
            'learning_level': 'intermediate',
            'quality_score': 0.8,
            'keywords': 'ai code review, security, quality assurance, automation',
            'source_platform': 'web',
            'difficulty_level': 'intermediate',
            'cost_type': 'free'
        },
        {
            'title': 'Building Security Tools with AI Assistance',
            'description': 'Hands-on tutorial for creating cybersecurity tools using AI-assisted development.',
            'url': 'https://example.com/ai-security-tools',
            'resource_type': 'tutorial',
            'learning_level': 'advanced',
            'quality_score': 0.85,
            'keywords': 'security tools, ai development, cybersecurity, automation',
            'source_platform': 'web',
            'difficulty_level': 'advanced',
            'cost_type': 'free'
        }
    ]
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get Vibe Coding skill ID
        cursor.execute("SELECT id FROM emerging_skills WHERE skill_name = 'Vibe Coding'")
        result = cursor.fetchone()
        if not result:
            logger.error("Vibe Coding skill not found!")
            return
        
        vibe_coding_skill_id = result[0]
        
        for resource in vibe_coding_resources:
            # Insert resource
            cursor.execute('''
                INSERT INTO educational_resources 
                (title, description, url, resource_type, skill_category, learning_level,
                 quality_score, keywords, source_platform, difficulty_level, cost_type,
                 metadata, prerequisites, learning_outcomes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resource['title'],
                resource['description'],
                resource['url'],
                resource['resource_type'],
                'vibe_coding',  # skill_category
                resource['learning_level'],
                resource['quality_score'],
                resource['keywords'],
                resource['source_platform'],
                resource['difficulty_level'],
                resource['cost_type'],
                '{}',  # metadata
                '[]',  # prerequisites
                '[]'   # learning_outcomes
            ))
            
            resource_id = cursor.lastrowid
            
            # Map to Vibe Coding skill
            cursor.execute('''
                INSERT INTO skill_resource_mapping
                (skill_id, resource_id, relevance_score, resource_type_for_skill)
                VALUES (?, ?, ?, ?)
            ''', (vibe_coding_skill_id, resource_id, 0.95, 'foundation'))
            
            logger.info(f"Created Vibe Coding resource: {resource['title']}")
        
        conn.commit()

def distribute_remaining_resources():
    """Distribute remaining resources to skills that need them"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Get skills that have few or no resources
        cursor.execute('''
            SELECT es.id, es.skill_name, COUNT(srm.resource_id) as resource_count
            FROM emerging_skills es 
            LEFT JOIN skill_resource_mapping srm ON es.id = srm.skill_id
            GROUP BY es.id, es.skill_name
            ORDER BY resource_count ASC
        ''')
        
        skills_needing_resources = cursor.fetchall()
        
        # Get unmapped resources
        cursor.execute('''
            SELECT er.id, er.title, er.skill_category
            FROM educational_resources er
            LEFT JOIN skill_resource_mapping srm ON er.id = srm.resource_id
            WHERE srm.resource_id IS NULL
            LIMIT 10
        ''')
        
        unmapped_resources = cursor.fetchall()
        
        # Distribute unmapped resources to skills with fewer resources
        for i, (resource_id, title, category) in enumerate(unmapped_resources):
            if i < len(skills_needing_resources):
                skill_id, skill_name, current_count = skills_needing_resources[i]
                
                cursor.execute('''
                    INSERT INTO skill_resource_mapping
                    (skill_id, resource_id, relevance_score, resource_type_for_skill)
                    VALUES (?, ?, ?, ?)
                ''', (skill_id, resource_id, 0.7, 'general'))
                
                logger.info(f"Mapped '{title}' to {skill_name}")
        
        conn.commit()

def verify_restoration():
    """Verify the skill restoration was successful"""
    db_path = get_db_path()
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT es.skill_name, COUNT(srm.resource_id) as resource_count
            FROM emerging_skills es 
            LEFT JOIN skill_resource_mapping srm ON es.id = srm.skill_id
            GROUP BY es.id, es.skill_name
            ORDER BY resource_count DESC
        ''')
        
        results = cursor.fetchall()
        
        logger.info("✅ Skill restoration verification:")
        total_resources = 0
        for skill_name, count in results:
            logger.info(f"  📚 {skill_name}: {count} resources")
            total_resources += count
        
        logger.info(f"  🎯 Total mapped resources: {total_resources}")
        
        # Check specifically for Vibe Coding
        vibe_coding_count = next((count for name, count in results if 'Vibe Coding' in name), 0)
        if vibe_coding_count > 0:
            logger.info(f"🚀 Vibe Coding successfully restored with {vibe_coding_count} resources!")
        else:
            logger.warning("⚠️  Vibe Coding still has no resources")

def main():
    """Run the complete skill restoration"""
    logger.info("Starting skill restoration for enhanced learning experience...")
    
    try:
        # Step 1: Clear existing skills
        clear_existing_skills()
        
        # Step 2: Create original 5 skills
        create_original_skills()
        
        # Step 3: Create Vibe Coding specific resources
        create_vibe_coding_resources()
        
        # Step 4: Distribute remaining resources
        distribute_remaining_resources()
        
        # Step 5: Verify restoration
        verify_restoration()
        
        logger.info("✅ Skill restoration completed successfully!")
        logger.info("🎯 Original 5 skills restored with resources")
        logger.info("🚀 Vibe Coding ready for enhanced learning experience!")
        
    except Exception as e:
        logger.error(f"Skill restoration failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 