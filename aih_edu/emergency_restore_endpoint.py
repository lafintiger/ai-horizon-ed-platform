#!/usr/bin/env python3
"""
Emergency database restoration endpoint for Heroku
Access via browser: /emergency-restore
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify
from utils.database import DatabaseManager

app = Flask(__name__)

@app.route('/emergency-restore')
def emergency_restore():
    """Emergency database restoration endpoint"""
    
    try:
        print("🚨 EMERGENCY DATABASE RESTORE STARTED")
        
        # Get database manager
        db_manager = DatabaseManager()
        
        # Add Prompt Engineering skill if not exists
        prompt_engineering_data = {
            'skill_name': 'Prompt Engineering',
            'category': 'ai-technology',
            'urgency_score': 8.5,
            'demand_trend': 'rising',
            'source_analysis': 'AI adoption analysis - critical for AI integration',
            'description': 'Mastering the art and science of crafting effective prompts for AI language models to achieve desired outcomes in cybersecurity and beyond.',
            'related_skills': ['AI-Enhanced SIEM', 'Vibe Coding']
        }
        
        # Check if Prompt Engineering exists
        skills = db_manager.get_emerging_skills()
        prompt_skill_exists = any('prompt' in skill['skill_name'].lower() for skill in skills)
        
        if not prompt_skill_exists:
            skill_id = db_manager.add_emerging_skill(prompt_engineering_data)
            print(f"✅ Added Prompt Engineering skill with ID: {skill_id}")
        else:
            print("✅ Prompt Engineering skill already exists")
        
        # Sample resources for each skill
        sample_resources = {
            'Zero Trust Architecture': [
                {
                    'title': 'NIST Zero Trust Architecture Guide',
                    'description': 'Comprehensive guide to implementing Zero Trust Architecture following NIST standards.',
                    'url': 'https://www.nist.gov/publications/zero-trust-architecture',
                    'resource_type': 'documentation',
                    'quality_score': 0.95,
                    'keywords': ['zero trust', 'NIST', 'architecture', 'security']
                }
            ],
            'Prompt Engineering': [
                {
                    'title': 'Complete Guide to Prompt Engineering',
                    'description': 'Comprehensive tutorial on crafting effective prompts for AI language models.',
                    'url': 'https://www.promptingguide.ai/',
                    'resource_type': 'course',
                    'quality_score': 0.9,
                    'keywords': ['prompt engineering', 'AI', 'language models', 'ChatGPT']
                },
                {
                    'title': 'ChatGPT Prompt Engineering Course',
                    'description': 'Learn advanced prompting techniques for better AI interactions.',
                    'url': 'https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/',
                    'resource_type': 'course',
                    'quality_score': 0.95,
                    'keywords': ['ChatGPT', 'prompt engineering', 'developers', 'AI']
                }
            ],
            'Quantum-Safe Cryptography': [
                {
                    'title': 'NIST Post-Quantum Cryptography Standards',
                    'description': 'Official NIST standards for quantum-resistant cryptographic algorithms.',
                    'url': 'https://www.nist.gov/news-events/news/2024/08/nist-releases-first-3-finalized-post-quantum-encryption-standards',
                    'resource_type': 'documentation',
                    'quality_score': 0.95,
                    'keywords': ['quantum safe', 'cryptography', 'NIST', 'post-quantum']
                }
            ]
        }
        
        # Add sample resources
        total_added = 0
        for skill_name, resources in sample_resources.items():
            # Find skill
            skill = None
            for s in skills:
                if skill_name.lower() in s['skill_name'].lower() or s['skill_name'].lower() in skill_name.lower():
                    skill = s
                    break
            
            if skill:
                for resource_data in resources:
                    resource_id = db_manager.add_educational_resource(resource_data)
                    if resource_id:
                        # Map resource to skill
                        mapping_data = {
                            'skill_id': skill['id'],
                            'resource_id': resource_id,
                            'relevance_score': 0.9,
                            'resource_type_for_skill': 'foundation'
                        }
                        db_manager.add_skill_resource_mapping(mapping_data)
                        total_added += 1
                        print(f"✅ Added resource: {resource_data['title']}")
        
        print(f"🎯 Database restoration completed! Added {total_added} resources")
        
        return jsonify({
            'status': 'success',
            'message': f'Database restored successfully! Added {total_added} resources.',
            'skills_count': len(skills),
            'resources_added': total_added
        })
        
    except Exception as e:
        print(f"❌ Error during restoration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Restoration failed: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 