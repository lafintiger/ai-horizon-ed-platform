#!/usr/bin/env python3
"""
Add Vibe Coding skill to the AI-Horizon Ed database
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from utils.database import DatabaseManager

def add_vibe_coding_skill():
    """Add Vibe Coding as an emerging skill"""
    
    # Initialize database
    db = DatabaseManager()
    
    # Define the vibe coding skill
    vibe_coding_skill = {
        "skill_name": "Vibe Coding",
        "category": "programming_methodology", 
        "urgency_score": 0.75,
        "demand_trend": "emerging",
        "source_analysis": "trend_analysis",
        "description": "A programming approach that emphasizes mood, atmosphere, and intuitive coding practices to enhance developer productivity and creativity. Incorporates elements like ambient music, aesthetic environments, and flow-state programming techniques.",
        "job_market_data": '{"demand_growth": "25%", "skill_gap": "high", "industries": ["tech", "creative", "startups"]}',
        "related_skills": '["Creative Programming", "Developer Experience", "Flow State Programming", "Ambient Development", "UI/UX Design", "Developer Productivity"]'
    }
    
    try:
        # Add the skill to database
        skill_id = db.add_emerging_skill(vibe_coding_skill)
        
        if skill_id:
            print(f"✅ Successfully added 'Vibe Coding' skill with ID: {skill_id}")
            
            # Get all skills to verify
            skills = db.get_emerging_skills()
            print(f"\n📊 Total emerging skills in database: {len(skills)}")
            
            # Show the newly added skill
            vibe_skill = next((s for s in skills if s['skill_name'] == 'Vibe Coding'), None)
            if vibe_skill:
                print(f"\n🎨 Vibe Coding Skill Details:")
                print(f"   • ID: {vibe_skill['id']}")
                print(f"   • Category: {vibe_skill['category']}")
                print(f"   • Urgency Score: {vibe_skill['urgency_score']}")
                print(f"   • Trend: {vibe_skill['demand_trend']}")
                print(f"   • Description: {vibe_skill['description'][:100]}...")
        else:
            print("❌ Failed to add Vibe Coding skill")
            
    except Exception as e:
        print(f"❌ Error adding skill: {e}")

if __name__ == "__main__":
    add_vibe_coding_skill() 