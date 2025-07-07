#!/usr/bin/env python3
"""
Fix Skill-Resource Links
Emergency script to link existing resources to their appropriate skills
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'aih_edu'))

from utils.database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_skill_resource_links():
    """Fix the missing links between skills and resources"""
    
    logger.info("🔧 Starting skill-resource link repair...")
    
    db_manager = DatabaseManager()
    
    # Get all skills and resources
    skills = db_manager.get_all_skills()
    resources = db_manager.get_all_resources()
    
    logger.info(f"Found {len(skills)} skills and {len(resources)} resources")
    
    # Mapping between skill names and resource categories
    skill_mappings = {
        'Vibe Coding': ['vibe_coding', 'ai-assisted', 'ambient development'],
        'AI-Enhanced SIEM': ['ai-augmented_threat_intelligence', 'siem', 'cybersecurity'],
        'Zero Trust Architecture': ['Network Security', 'zero trust', 'cybersecurity'],
        'Prompt Engineering': ['ai-technology', 'prompt_engineering_for_security', 'ai'],
        'Ethical Hacking and Penetration Testing': ['ethical_hacking_and_penetration_testing', 'cybersecurity', 'pentest'],
        'Cloud Security Posture Management': ['cloud security', 'cybersecurity'],
        'Quantum-Safe Cryptography': ['quantum-cryptography', 'cybersecurity'],
        'Advanced AI Red Team Automation': ['advanced_ai_red_team_automation', 'cybersecurity']
    }
    
    total_links = 0
    
    for skill in skills:
        skill_name = skill['skill_name']
        skill_id = skill['id']
        
        # Get matching categories for this skill
        matching_categories = skill_mappings.get(skill_name, [skill_name.lower().replace(' ', '_')])
        
        logger.info(f"Linking resources for skill: {skill_name} (ID: {skill_id})")
        logger.info(f"  Looking for categories: {matching_categories}")
        
        linked_count = 0
        for resource in resources:
            resource_category = resource.get('skill_category', '').lower()
            
            # Check if resource category matches any of the skill's categories
            for category in matching_categories:
                if category.lower() in resource_category or resource_category in category.lower():
                    try:
                        # Link the resource to the skill
                        db_manager.link_skill_to_resource(
                            skill_id=skill_id,
                            resource_id=resource['id'],
                            relevance_score=0.9,
                            resource_type_for_skill=resource.get('resource_type', 'general')
                        )
                        linked_count += 1
                        logger.info(f"  ✅ Linked: {resource['title'][:50]}...")
                        break
                    except Exception as e:
                        logger.warning(f"  ⚠️  Failed to link resource {resource['id']}: {e}")
        
        logger.info(f"  📊 Total linked for {skill_name}: {linked_count}")
        total_links += linked_count
    
    logger.info(f"🎉 Skill-resource link repair completed!")
    logger.info(f"   Total links created: {total_links}")
    
    # Verify the fix
    logger.info("\n🔍 Verification:")
    for skill in skills:
        skill_resources = db_manager.get_resources_for_skill(skill['id'])
        logger.info(f"  {skill['skill_name']}: {len(skill_resources)} resources")

if __name__ == '__main__':
    fix_skill_resource_links() 