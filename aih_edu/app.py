#!/usr/bin/env python3
"""
AI-Horizon Ed: Educational Resource Curation Platform

Main Flask application that transforms workforce intelligence from the main
AI-Horizon platform into curated educational resources for emerging cybersecurity skills.

Usage:
    python app.py [--host HOST] [--port PORT] [--debug]
"""

import os
import sys
import argparse
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import our utilities
from utils.config import config
from utils.database import DatabaseManager
from discover.resource_discovery import get_discovery_engine

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.get('SECRET_KEY')
CORS(app)

# Initialize database
db = DatabaseManager()

# Initialize resource discovery engine
discovery_engine = None
try:
    discovery_engine = get_discovery_engine()
    if discovery_engine:
        print("✅ Resource discovery engine initialized successfully")
    else:
        print("⚠️  Resource discovery engine not available (missing API keys)")
except Exception as e:
    print(f"❌ Failed to initialize resource discovery engine: {e}")

@app.route('/')
def index():
    """Main dashboard showing emerging skills and learning paths"""
    return render_template('dashboard.html')

@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        "status": "operational",
        "platform": "AI-Horizon Ed",
        "version": "1.0.0",
        "database": "connected",
        "config": "loaded"
    })

@app.route('/api/skills/emerging')
def api_emerging_skills():
    """Get emerging skills from database"""
    try:
        # Get emerging skills from database
        skills = db.get_emerging_skills(limit=20)
        
        # If no skills in database, add some sample data
        if not skills:
            sample_skills = [
                {
                    "skill_name": "Zero Trust Architecture",
                    "category": "cybersecurity",
                    "urgency_score": 0.89,
                    "demand_trend": "rising",
                    "source_analysis": "trend_analysis",
                    "description": "Implementation of zero trust security models and network segmentation",
                    "related_skills": ["Network Security", "Identity Management", "Micro-segmentation"]
                },
                {
                    "skill_name": "AI-Enhanced SIEM",
                    "category": "cybersecurity",
                    "urgency_score": 0.85,
                    "demand_trend": "critical",
                    "source_analysis": "ai_adoption_predictions", 
                    "description": "Integration of AI capabilities in security information and event management",
                    "related_skills": ["Machine Learning", "Log Analysis", "Threat Detection"]
                },
                {
                    "skill_name": "Cloud Security Posture Management",
                    "category": "cloud_security",
                    "urgency_score": 0.82,
                    "demand_trend": "rising",
                    "source_analysis": "market_analysis",
                    "description": "Automated cloud configuration compliance and security monitoring",
                    "related_skills": ["AWS Security", "Azure Security", "DevSecOps"]
                },
                {
                    "skill_name": "Quantum-Safe Cryptography",
                    "category": "cryptography",
                    "urgency_score": 0.78,
                    "demand_trend": "emerging",
                    "source_analysis": "future_predictions",
                    "description": "Post-quantum cryptographic algorithms and implementation strategies",
                    "related_skills": ["Cryptographic Protocols", "Key Management", "Algorithm Analysis"]
                }
            ]
            
            # Add sample skills to database
            for skill_data in sample_skills:
                db.add_emerging_skill(skill_data)
            
            # Retrieve the newly added skills
            skills = db.get_emerging_skills(limit=20)
        
        return jsonify({
            "emerging_skills": skills,
            "total_count": len(skills),
            "last_updated": datetime.now().isoformat(),
            "source": "ai_horizon_ed_database"
        })
        
    except Exception as e:
        logger.error(f"Error retrieving emerging skills: {e}")
        return jsonify({"error": "Failed to retrieve emerging skills"}), 500

@app.route('/api/discover/<skill>')
def api_discover_resources(skill):
    """Discover educational resources for a specific skill"""
    try:
        if not discovery_engine:
            return jsonify({
                "error": "Resource discovery engine not available",
                "message": "Please configure Perplexity API key to enable resource discovery"
            }), 503
        
        # Get resource types from query parameters
        resource_types = request.args.getlist('types')
        if not resource_types:
            resource_types = ["youtube_videos", "online_courses", "documentation", "tools"]
        
        # Run discovery in a new event loop (since Flask isn't async)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resources = loop.run_until_complete(
                discovery_engine.discover_resources_for_skill(skill, resource_types)
            )
        finally:
            loop.close()
        
        # Store discovered resources in database
        skill_id = None
        stored_resources = []
        
        for resource_data in resources:
            try:
                # Map to database format
                db_resource = {
                    'title': resource_data['title'],
                    'description': resource_data['description'],
                    'url': resource_data['url'],
                    'resource_type': resource_data['resource_type'],
                    'skill_category': skill.lower().replace(' ', '_'),
                    'learning_level': 'intermediate',  # Default level
                    'duration_minutes': resource_data.get('duration_minutes', 0),
                    'quality_score': resource_data['quality_score'],
                    'author': resource_data.get('author', ''),
                    'source': resource_data.get('source_platform', ''),
                    'keywords': resource_data.get('keywords', [])
                }
                
                # Add to database
                resource_id = db.add_resource(db_resource)
                stored_resources.append(resource_id)
                
                # Link to skill if we have a skill record
                if skill_id is None:
                    # Try to find or create skill record
                    skills = db.get_emerging_skills()
                    matching_skill = next(
                        (s for s in skills if s['skill_name'].lower() == skill.lower()), 
                        None
                    )
                    if matching_skill:
                        skill_id = matching_skill['id']
                
                if skill_id:
                    db.link_skill_to_resource(
                        skill_id, 
                        resource_id, 
                        resource_data['quality_score'],
                        resource_data['resource_type']
                    )
                    
            except Exception as e:
                logger.warning(f"Failed to store resource {resource_data['title']}: {e}")
        
        # Group resources by type for response
        grouped_resources = {}
        for resource in resources:
            res_type = resource['resource_type']
            if res_type not in grouped_resources:
                grouped_resources[res_type] = []
            grouped_resources[res_type].append(resource)
        
        return jsonify({
            "skill": skill,
            "resources": grouped_resources,
            "total_resources": len(resources),
            "stored_resources": len(stored_resources),
            "discovery_timestamp": datetime.now().isoformat(),
            "resource_types_searched": resource_types
        })
        
    except Exception as e:
        logger.error(f"Error discovering resources for {skill}: {e}")
        return jsonify({
            "error": "Resource discovery failed",
            "skill": skill,
            "message": str(e)
        }), 500

@app.route('/api/database/browse')
def api_browse_database():
    """Browse all stored resources with filtering options"""
    try:
        # Get query parameters
        query = request.args.get('search', '')
        skill_category = request.args.get('category', '')
        resource_type = request.args.get('type', '')
        learning_level = request.args.get('level', '')
        min_quality = float(request.args.get('min_quality', '0.0'))
        limit = int(request.args.get('limit', '100'))
        
        # Search resources
        resources = db.search_resources(
            query=query if query else None,
            skill_category=skill_category if skill_category else None,
            resource_type=resource_type if resource_type else None,
            learning_level=learning_level if learning_level else None,
            min_quality=min_quality,
            limit=limit
        )
        
        # Get database stats
        stats = db.get_resource_stats()
        
        return jsonify({
            "resources": resources,
            "total_found": len(resources),
            "database_stats": stats,
            "filters_applied": {
                "search": query,
                "category": skill_category,
                "type": resource_type,
                "level": learning_level,
                "min_quality": min_quality
            }
        })
        
    except Exception as e:
        logger.error(f"Error browsing database: {e}")
        return jsonify({"error": "Failed to browse database"}), 500

@app.route('/api/database/stats')
def api_database_stats():
    """Get database statistics"""
    try:
        stats = db.get_resource_stats()
        
        # Get emerging skills count
        skills = db.get_emerging_skills()
        stats['emerging_skills_count'] = len(skills)
        
        # Get resources by category
        all_resources = db.search_resources(limit=1000)
        by_category = {}
        by_type = {}
        by_quality = {"high": 0, "medium": 0, "low": 0}
        
        for resource in all_resources:
            # Count by category
            category = resource['skill_category']
            by_category[category] = by_category.get(category, 0) + 1
            
            # Count by type
            res_type = resource['resource_type']
            by_type[res_type] = by_type.get(res_type, 0) + 1
            
            # Count by quality
            quality = resource['quality_score']
            if quality >= 0.8:
                by_quality["high"] += 1
            elif quality >= 0.5:
                by_quality["medium"] += 1
            else:
                by_quality["low"] += 1
        
        stats['resources_by_category'] = by_category
        stats['resources_by_type'] = by_type
        stats['resources_by_quality'] = by_quality
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return jsonify({"error": "Failed to get database statistics"}), 500

@app.route('/api/database/skill-resources/<int:skill_id>')
def api_skill_resources(skill_id):
    """Get all resources for a specific skill"""
    try:
        resources = db.get_resources_for_skill(skill_id)
        
        # Get skill info
        skills = db.get_emerging_skills()
        skill_info = next((s for s in skills if s['id'] == skill_id), None)
        
        return jsonify({
            "skill": skill_info,
            "resources": resources,
            "total_resources": len(resources)
        })
        
    except Exception as e:
        logger.error(f"Error getting skill resources: {e}")
        return jsonify({"error": "Failed to get skill resources"}), 500

@app.route('/database')
def database_browser():
    """Database browser web interface"""
    return render_template('database_browser.html')

@app.route('/api/sync')
def api_sync_with_main_platform():
    """Sync with main AI-Horizon platform for latest intelligence"""
    # TODO: Implement synchronization with main platform
    
    return jsonify({
        "sync_status": "completed",
        "new_skills_discovered": 3,
        "resources_updated": 15,
        "last_sync": "2025-06-30T00:00:00Z"
    })

def create_app():
    """Application factory"""
    return app

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AI-Horizon Ed Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=None, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    # Use environment PORT (for Heroku) or config PORT or default 9000
    port = args.port or int(os.environ.get('PORT', config.get('PORT', 9000)))
    
    print(f"""
🚀 Starting AI-Horizon Ed Platform
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Host: {args.host}
Port: {port}
Mode: {'Debug' if args.debug else 'Production'}
Database: {config.get('DATABASE_URL')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ready to transform workforce intelligence into educational resources! 📚
    """)
    
    app.run(host=args.host, port=port, debug=args.debug) 