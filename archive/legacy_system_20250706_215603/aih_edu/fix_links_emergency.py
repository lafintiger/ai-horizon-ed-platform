#!/usr/bin/env python3
"""Emergency fix for skill-resource links"""

from utils.database import DatabaseManager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def emergency_fix_links():
    """Emergency repair of skill-resource links"""
    
    logger.info("🚨 EMERGENCY SKILL-RESOURCE LINK REPAIR")
    
    db = DatabaseManager()
    
    # Get all skills and resources
    skills = db.get_all_skills()
    resources = db.get_all_resources()
    
    logger.info(f"Found {len(skills)} skills and {len(resources)} resources")
    
    # Quick mapping based on categories found in database
    category_mappings = {
        'vibe_coding': 'Vibe Coding',
        'ai-technology': 'Prompt Engineering', 
        'cybersecurity': 'AI-Enhanced SIEM',
        'Network Security': 'Zero Trust Architecture',
        'ai-augmented_threat_intelligence': 'AI-Enhanced SIEM',
        'ethical_hacking_and_penetration_testing': 'Ethical Hacking and Penetration Testing',
        'prompt_engineering_for_security': 'Prompt Engineering',
        'quantum-cryptography': 'Quantum-Safe Cryptography',
        'advanced_ai_red_team_automation': 'Advanced AI Red Team Automation'
    }
    
    # Create skill name to ID mapping
    skill_name_to_id = {skill['skill_name']: skill['id'] for skill in skills}
    
    total_links = 0
    
    for resource in resources:
        category = resource.get('skill_category', '')
        
        # Find matching skill
        target_skill = category_mappings.get(category)
        if not target_skill:
            # Fallback: try to match any skill name containing the category
            for skill_name in skill_name_to_id.keys():
                if category.lower() in skill_name.lower() or skill_name.lower() in category.lower():
                    target_skill = skill_name
                    break
        
        if target_skill and target_skill in skill_name_to_id:
            skill_id = skill_name_to_id[target_skill]
            try:
                db.link_skill_to_resource(
                    skill_id=skill_id,
                    resource_id=resource['id'],
                    relevance_score=0.9,
                    resource_type_for_skill=resource.get('resource_type', 'general')
                )
                total_links += 1
                logger.info(f"✅ Linked '{resource['title'][:40]}...' to {target_skill}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to link resource {resource['id']}: {e}")
        else:
            logger.warning(f"⚠️ No skill found for category: {category}")
    
    logger.info(f"\n🎉 REPAIR COMPLETE!")
    logger.info(f"   Total links created: {total_links}")
    
    # Verify results
    logger.info("\n🔍 Verification:")
    for skill in skills:
        linked_resources = db.get_resources_for_skill(skill['id'])
        logger.info(f"  {skill['skill_name']}: {len(linked_resources)} resources")
    
    return total_links

if __name__ == '__main__':
    emergency_fix_links() 