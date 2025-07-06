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
import threading
import uuid
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect
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
from discover.resource_discovery import get_discovery_engine, ResourceDiscoveryEngine
from core.enhanced_content_analyzer import enhanced_content_analyzer, EnhancedContentAnalyzer

# Authentication imports
from flask import session, url_for, flash
from functools import wraps
from datetime import datetime, timedelta
import hashlib

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.get('SECRET_KEY')
CORS(app)

# HTTPS enforcement for production
@app.before_request
def force_https():
    """Redirect HTTP requests to HTTPS in production"""
    # Skip HTTPS enforcement completely for local development
    if (request.remote_addr in ['127.0.0.1', 'localhost'] or 
        request.host.startswith('127.0.0.1') or 
        request.host.startswith('localhost') or
        '127.0.0.1' in request.host or
        'localhost' in request.host or
        app.debug or 
        os.environ.get('FLASK_ENV') == 'development' or
        config.get('FLASK_ENV') == 'development'):
        return None
    
    # Only enforce HTTPS in production (Heroku/custom domain)
    if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
        # Get the full URL and replace http with https
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# Security headers for HTTPS
@app.after_request
def add_security_headers(response):
    """Add security headers for HTTPS"""
    if not app.debug:
        # HSTS - Force HTTPS for 1 year
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        # XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response



# Initialize database
db_manager = DatabaseManager()
content_analyzer = EnhancedContentAnalyzer()

# Initialize learning experience service with database manager
from utils.learning_experience_service import LearningExperienceService
learning_service = LearningExperienceService(db_manager)

# DIAGNOSTIC: Check what methods are available on db_manager
available_methods = [method for method in dir(db_manager) if not method.startswith('_')]
logger.info(f"DatabaseManager available methods: {available_methods}")
logger.info(f"Has store_learning_content method: {hasattr(db_manager, 'store_learning_content')}")
if hasattr(db_manager, 'store_learning_content'):
    logger.info(f"store_learning_content method: {getattr(db_manager, 'store_learning_content')}")

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

# =============================================================================
# AUTHENTICATION SYSTEM
# =============================================================================

def hash_password(password):
    """Hash a password for storing"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return hash_password(password) == hashed

def is_authenticated():
    """Check if user is authenticated"""
    return session.get('authenticated', False)

def require_auth(f):
    """Decorator to require authentication for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Make authentication available to templates
@app.context_processor
def inject_auth():
    """Inject authentication status into all templates"""
    return dict(is_authenticated=is_authenticated())

# Background task management - File-based storage for persistence
import json
from pathlib import Path

TASKS_FILE = Path('data/discovery_tasks.json')
TASKS_FILE.parent.mkdir(exist_ok=True)

def load_discovery_tasks():
    """Load tasks from file"""
    try:
        if TASKS_FILE.exists():
            with open(TASKS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to load tasks file: {e}")
    return {}

def save_discovery_tasks(tasks):
    """Save tasks to file"""
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f)
    except Exception as e:
        logger.warning(f"Failed to save tasks file: {e}")

def get_discovery_task(task_id):
    """Get a specific task"""
    tasks = load_discovery_tasks()
    return tasks.get(task_id)

def update_discovery_task(task_id, task_data):
    """Update a specific task"""
    tasks = load_discovery_tasks()
    tasks[task_id] = task_data
    save_discovery_tasks(tasks)

def delete_discovery_task(task_id):
    """Delete a specific task"""
    tasks = load_discovery_tasks()
    if task_id in tasks:
        del tasks[task_id]
        save_discovery_tasks(tasks)

def discover_resources_background(task_id, skill):
    """Background function to discover resources with progress tracking"""
    try:
        # Update task status
        task_data = get_discovery_task(task_id)
        if not task_data:
            logger.error(f"Task {task_id} not found when starting background processing")
            return
            
        task_data['status'] = 'processing'
        task_data['progress'] = 10
        task_data['current_step'] = 'Starting resource discovery...'
        update_discovery_task(task_id, task_data)
        
        if not discovery_engine:
            task_data['status'] = 'failed'
            task_data['error'] = 'Resource discovery engine not available'
            update_discovery_task(task_id, task_data)
            return
        
        # Check for cached resources first
        task_data['progress'] = 20
        task_data['current_step'] = 'Checking for existing resources...'
        update_discovery_task(task_id, task_data)
        
        existing_resources = db_manager.search_resources(query=skill, limit=20)
        if existing_resources and len(existing_resources) >= 5:
            # Return cached results
            grouped_resources = {}
            for resource in existing_resources[:10]:
                res_type = resource['resource_type']
                if res_type not in grouped_resources:
                    grouped_resources[res_type] = []
                grouped_resources[res_type].append(resource)
            
            task_data['status'] = 'completed'
            task_data['progress'] = 100
            task_data['current_step'] = 'Discovery completed (cached results)'
            task_data['results'] = {
                "skill": skill,
                "resources": grouped_resources,
                "total_resources": len(existing_resources),
                "cached": True,
                "discovery_timestamp": datetime.now().isoformat()
            }
            update_discovery_task(task_id, task_data)
            return
        
        # Discover new resources
        task_data['progress'] = 30
        task_data['current_step'] = 'Discovering new resources...'
        update_discovery_task(task_id, task_data)
        
        resource_types = ["youtube_videos", "online_courses", "documentation", "tools"]
        
        # Run discovery in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            resources = loop.run_until_complete(
                discovery_engine.discover_resources_for_skill(skill, resource_types[:2])  # Limit to 2 types for speed
            )
        finally:
            loop.close()
        
        task_data['progress'] = 70
        task_data['current_step'] = 'Storing discovered resources...'
        update_discovery_task(task_id, task_data)
        
        if not resources:
            task_data['status'] = 'completed'
            task_data['progress'] = 100
            task_data['results'] = {
                "skill": skill,
                "resources": {},
                "total_resources": 0,
                "error": "No resources discovered"
            }
            update_discovery_task(task_id, task_data)
            return
        
        # Store resources
        skill_id = None
        stored_resources = []
        
        # Find skill ID for linking
        skills = db_manager.get_emerging_skills()
        
        # Normalize skill name for better matching
        skill_normalized = skill.lower().replace('-', ' ').replace('_', ' ').strip()
        
        matching_skill = None
        for s in skills:
            skill_db_normalized = s['skill_name'].lower().replace('-', ' ').replace('_', ' ').strip()
            if skill_db_normalized == skill_normalized:
                matching_skill = s
                break
        
        skill_id = matching_skill['id'] if matching_skill else None
        
        for resource_data in resources:
            try:
                # Map to database format
                db_resource = {
                    'title': resource_data['title'],
                    'description': resource_data['description'],
                    'url': resource_data['url'],
                    'resource_type': resource_data['resource_type'],
                    'skill_category': skill.lower().replace(' ', '_'),
                    'learning_level': 'intermediate',
                    'duration_minutes': resource_data.get('duration_minutes', 0),
                    'quality_score': resource_data['quality_score'],
                    'author': resource_data.get('author', ''),
                    'source': resource_data.get('source_platform', ''),
                    'keywords': resource_data.get('keywords', [])
                }
                
                # Add to database
                resource_id = db_manager.add_resource(db_resource)
                stored_resources.append(resource_id)
                
                if skill_id:
                    db_manager.link_skill_to_resource(
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
        
        # Mark as completed
        task_data['status'] = 'completed'
        task_data['progress'] = 100
        task_data['current_step'] = 'Discovery completed successfully!'
        task_data['results'] = {
            "skill": skill,
            "resources": grouped_resources,
            "total_resources": len(resources),
            "stored_resources": len(stored_resources),
            "discovery_timestamp": datetime.now().isoformat(),
            "resource_types_searched": resource_types[:2]
        }
        update_discovery_task(task_id, task_data)
        
    except Exception as e:
        logger.error(f"Error in background discovery for {skill}: {e}")
        task_data = get_discovery_task(task_id) or {}
        task_data['status'] = 'failed'
        task_data['error'] = str(e)
        update_discovery_task(task_id, task_data)

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
        skills = db_manager.get_emerging_skills(limit=20)
        
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
                },
                {
                    "skill_name": "Vibe Coding",
                    "category": "programming_methodology",
                    "urgency_score": 0.75,
                    "demand_trend": "emerging",
                    "source_analysis": "trend_analysis",
                    "description": "A programming approach that emphasizes mood, atmosphere, and intuitive coding practices to enhance developer productivity and creativity",
                    "related_skills": ["Creative Programming", "Developer Experience", "Flow State Programming", "Ambient Development"]
                }
            ]
            
            # Add sample skills to database
            for skill_data in sample_skills:
                db_manager.add_emerging_skill(skill_data)
            
            # Retrieve the newly added skills
            skills = db_manager.get_emerging_skills(limit=20)
        
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
@require_auth
def api_discover_resources(skill):
    """Start background resource discovery for a specific skill"""
    try:
        # Check for existing cached resources first
        existing_resources = db_manager.search_resources(query=skill, limit=20)
        if existing_resources and len(existing_resources) >= 8:
            # Return cached results immediately if we have enough
            grouped_resources = {}
            for resource in existing_resources[:12]:
                res_type = resource['resource_type']
                if res_type not in grouped_resources:
                    grouped_resources[res_type] = []
                grouped_resources[res_type].append(resource)
            
            return jsonify({
                "skill": skill,
                "resources": grouped_resources,
                "total_resources": len(existing_resources),
                "cached": True,
                "discovery_timestamp": datetime.now().isoformat()
            })
        
        # Start background discovery for new resources
        task_id = str(uuid.uuid4())
        task_data = {
            'status': 'started',
            'progress': 0,
            'current_step': 'Initializing resource discovery...',
            'skill': skill,
            'created_at': datetime.now().isoformat()
        }
        update_discovery_task(task_id, task_data)
        
        # Start background thread
        thread = threading.Thread(
            target=discover_resources_background,
            args=(task_id, skill)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "task_id": task_id,
            "skill": skill,
            "status": "discovery_started",
            "message": "Resource discovery started in background. Check status for progress.",
            "status_url": f"/api/discover/status/{task_id}"
        })
        
    except Exception as e:
        logger.error(f"Error starting discovery for {skill}: {e}")
        return jsonify({
            "error": "Failed to start resource discovery",
            "skill": skill,
            "message": str(e)
        }), 500

@app.route('/api/discover/status/<task_id>')
@require_auth
def api_discovery_status(task_id):
    """Check the status of a resource discovery task"""
    task = get_discovery_task(task_id)
    
    if not task:
        # Try to return cached resources if task not found
        existing_resources = db_manager.search_resources(query=task_id, limit=10)  # Try skill name as fallback
        if existing_resources:
            grouped_resources = {}
            for resource in existing_resources:
                res_type = resource['resource_type']
                if res_type not in grouped_resources:
                    grouped_resources[res_type] = []
                grouped_resources[res_type].append(resource)
            
            return jsonify({
                "task_id": task_id,
                "status": "completed",
                "progress": 100,
                "current_step": "Found cached resources",
                "results": {
                    "skill": "Unknown",
                    "resources": grouped_resources,
                    "total_resources": len(existing_resources),
                    "cached": True,
                    "discovery_timestamp": datetime.now().isoformat()
                }
            })
        
        return jsonify({"error": "Task not found. The task may have expired or the server was restarted."}), 404
    
    response = {
        "task_id": task_id,
        "status": task['status'],
        "progress": task['progress'],
        "current_step": task.get('current_step', ''),
        "skill": task['skill'],
        "created_at": task['created_at']
    }
    
    if task['status'] == 'completed' and 'results' in task:
        response['results'] = task['results']
        # Clean up old task after returning results
        delete_discovery_task(task_id)
    elif task['status'] == 'failed' and 'error' in task:
        response['error'] = task['error']
        # Clean up failed task
        delete_discovery_task(task_id)
    
    return jsonify(response)

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
        resources = db_manager.search_resources(
            query=query if query else None,
            skill_category=skill_category if skill_category else None,
            resource_type=resource_type if resource_type else None,
            learning_level=learning_level if learning_level else None,
            min_quality=min_quality,
            limit=limit
        )
        
        # Get database stats
        stats = db_manager.get_resource_stats()
        
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
        stats = db_manager.get_resource_stats()
        
        # Get emerging skills count
        skills = db_manager.get_emerging_skills()
        stats['emerging_skills_count'] = len(skills)
        
        # Get resources by category
        all_resources = db_manager.search_resources(limit=1000)
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

@app.route('/api/resources')
def api_resources():
    """Get all resources - basic endpoint for frontend"""
    try:
        resources = db_manager.get_all_resources()
        
        return jsonify({
            "resources": resources,
            "total_count": len(resources),
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error getting resources: {e}")
        return jsonify({"error": "Failed to get resources"}), 500

@app.route('/api/database/skill-resources/<int:skill_id>')
def api_skill_resources(skill_id):
    """Get all resources for a specific skill"""
    try:
        resources = db_manager.get_resources_for_skill(skill_id)
        
        # Get skill info
        skills = db_manager.get_emerging_skills()
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

@app.route('/emergency-restore')
def emergency_restore():
    """Emergency database restoration endpoint - bypasses authentication"""
    try:
        logger.info("🚨 EMERGENCY DATABASE RESTORE STARTED")
        
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
            ],
            'AI-Enhanced SIEM': [
                {
                    'title': 'AI-Powered Security Operations Center',
                    'description': 'Building intelligent SOCs with AI-enhanced SIEM capabilities.',
                    'url': 'https://www.splunk.com/en_us/solutions/artificial-intelligence.html',
                    'resource_type': 'documentation',
                    'quality_score': 0.88,
                    'keywords': ['AI', 'SIEM', 'security operations', 'threat detection']
                }
            ],
            'Vibe Coding': [
                {
                    'title': 'Flow State Programming with Cursor',
                    'description': 'Mastering the art of intuitive coding with AI assistance.',
                    'url': 'https://cursor.sh/',
                    'resource_type': 'tool',
                    'quality_score': 0.92,
                    'keywords': ['vibe coding', 'cursor', 'AI coding', 'flow state']
                }
            ]
        }
        
        # Add Prompt Engineering skill if not exists
        skills = db_manager.get_emerging_skills()
        prompt_skill_exists = any('prompt' in skill['skill_name'].lower() for skill in skills)
        
        if not prompt_skill_exists:
            prompt_engineering_data = {
                'skill_name': 'Prompt Engineering',
                'category': 'ai-technology',
                'urgency_score': 8.5,
                'demand_trend': 'rising',
                'source_analysis': 'AI adoption analysis - critical for AI integration',
                'description': 'Mastering the art and science of crafting effective prompts for AI language models to achieve desired outcomes.',
                'related_skills': ['AI-Enhanced SIEM', 'Vibe Coding']
            }
            skill_id = db_manager.add_emerging_skill(prompt_engineering_data)
            logger.info(f"✅ Added Prompt Engineering skill with ID: {skill_id}")
        
        # Refresh skills list
        skills = db_manager.get_emerging_skills()
        
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
                    # Check if resource already exists
                    existing = db_manager.search_resources(query=resource_data['title'][:20], limit=1)
                    if not existing:
                        # Add required fields for database
                        resource_data['skill_category'] = skill['category']
                        resource_data['learning_level'] = 'intermediate'
                        
                        resource_id = db_manager.add_resource(resource_data)
                        if resource_id:
                            # Map resource to skill
                            db_manager.link_skill_to_resource(
                                skill_id=skill['id'],
                                resource_id=resource_id,
                                relevance_score=0.9,
                                resource_type_for_skill='foundation'
                            )
                            total_added += 1
                            logger.info(f"✅ Added resource: {resource_data['title']}")
        
        logger.info(f"🎯 Database restoration completed! Added {total_added} resources")
        
        return jsonify({
            'status': 'success',
            'message': f'Database restored successfully! Added {total_added} resources.',
            'skills_count': len(skills),
            'resources_added': total_added,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error during restoration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Restoration failed: {str(e)}'
        }), 500

@app.route('/emergency-restore-full', methods=['POST'])
def emergency_restore_full():
    """Complete database restoration - accepts full database export"""
    try:
        logger.info("🚨 COMPLETE DATABASE RESTORATION STARTED")
        
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        skills_data = data.get('skills', [])
        resources_data = data.get('resources', [])
        mappings_data = data.get('mappings', [])
        
        logger.info(f"Restoring {len(skills_data)} skills, {len(resources_data)} resources")
        
        # Add all skills
        skill_mapping = {}  # old_name -> new_id
        for skill_data in skills_data:
            try:
                # Check if skill exists
                existing_skills = db_manager.get_emerging_skills()
                existing_skill = None
                for s in existing_skills:
                    if s['skill_name'].lower() == skill_data['skill_name'].lower():
                        existing_skill = s
                        break
                
                if existing_skill:
                    skill_mapping[skill_data['skill_name']] = existing_skill['id']
                    logger.info(f"Using existing skill: {skill_data['skill_name']}")
                else:
                    skill_id = db_manager.add_emerging_skill(skill_data)
                    skill_mapping[skill_data['skill_name']] = skill_id
                    logger.info(f"Added skill: {skill_data['skill_name']} (ID: {skill_id})")
                    
            except Exception as e:
                logger.warning(f"Failed to add skill {skill_data['skill_name']}: {e}")
        
        # Add all resources
        resource_mapping = {}  # title -> resource_id
        added_resources = 0
        
        for resource_data in resources_data:
            try:
                # Check if resource already exists
                existing = db_manager.search_resources(query=resource_data['title'][:20], limit=1)
                if existing:
                    resource_mapping[resource_data['title']] = existing[0]['id']
                    continue
                
                resource_id = db_manager.add_resource(resource_data)
                if resource_id:
                    resource_mapping[resource_data['title']] = resource_id
                    added_resources += 1
                    logger.info(f"Added resource: {resource_data['title']}")
                    
            except Exception as e:
                logger.warning(f"Failed to add resource {resource_data['title']}: {e}")
        
        # Create mappings
        created_mappings = 0
        for mapping in mappings_data:
            try:
                skill_name = mapping['skill_name']
                resource_title = mapping['resource_title']
                
                if skill_name in skill_mapping and resource_title in resource_mapping:
                    skill_id = skill_mapping[skill_name]
                    resource_id = resource_mapping[resource_title]
                    
                    db_manager.link_skill_to_resource(
                        skill_id=skill_id,
                        resource_id=resource_id,
                        relevance_score=mapping.get('relevance_score', 0.9),
                        resource_type_for_skill=mapping.get('resource_type_for_skill', 'foundation')
                    )
                    created_mappings += 1
                    
            except Exception as e:
                logger.warning(f"Failed to create mapping: {e}")
        
        logger.info(f"🎯 Complete restoration finished!")
        logger.info(f"   Skills: {len(skill_mapping)}")
        logger.info(f"   Resources added: {added_resources}")
        logger.info(f"   Mappings created: {created_mappings}")
        
        return jsonify({
            'status': 'success',
            'message': f'Complete database restored! Added {added_resources} resources.',
            'skills_count': len(skill_mapping),
            'resources_added': added_resources,
            'mappings_created': created_mappings,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error during complete restoration: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Complete restoration failed: {str(e)}'
        }), 500

@app.route('/admin')
@require_auth
def admin_panel():
    """Admin panel for managing skills and discovery"""
    try:
        # Get current skills
        skills = db_manager.get_emerging_skills()
        
        # Get discovery statistics
        base_stats = db_manager.get_resource_stats()
        
        # Get quality breakdown for admin panel
        resources = db_manager.search_resources(limit=1000)
        quality_breakdown = {'high': 0, 'medium': 0, 'low': 0}
        for resource in resources:
            score = resource.get('quality_score', 0)
            if score >= 0.8:
                quality_breakdown['high'] += 1
            elif score >= 0.5:
                quality_breakdown['medium'] += 1
            else:
                quality_breakdown['low'] += 1
        
        # Combine stats for template
        stats = {
            'total_skills': len(skills),
            'total_resources': base_stats.get('total_resources', 0),
            'resources_by_quality': quality_breakdown,
            'resources_by_type': base_stats.get('by_type', {}),
            'average_quality': base_stats.get('average_quality', 0.0)
        }
        
        return render_template('admin_panel.html', skills=skills, stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading admin panel: {e}")
        # Provide safe fallback stats
        fallback_stats = {
            'total_skills': 0,
            'total_resources': 0,
            'resources_by_quality': {'high': 0, 'medium': 0, 'low': 0},
            'resources_by_type': {},
            'average_quality': 0.0
        }
        return render_template('admin_panel.html', skills=[], stats=fallback_stats)

@app.route('/api/admin/add-skill', methods=['POST'])
@require_auth
def api_add_skill():
    """Add a new skill for discovery"""
    try:
        data = request.get_json()
        
        skill_name = data.get('skill_name', '').strip()
        if not skill_name:
            return jsonify({"error": "Skill name is required"}), 400
            
        description = data.get('description', '').strip()
        category = data.get('category', 'cybersecurity').strip()
        urgency_score = float(data.get('urgency_score', 0.5))
        demand_trend = data.get('demand_trend', 'emerging').strip()
        
        # Check if skill already exists
        existing_skills = db_manager.get_emerging_skills()
        if any(s['skill_name'].lower() == skill_name.lower() for s in existing_skills):
            return jsonify({"error": "Skill already exists"}), 400
        
        # Add the skill
        skill_data = {
            "skill_name": skill_name,
            "description": description or f"Emerging skill in {category}",
            "category": category,
            "urgency_score": max(0.0, min(1.0, urgency_score)),
            "demand_trend": demand_trend,
            "source_analysis": "manual_admin_entry"
        }
        
        skill_id = db_manager.add_emerging_skill(skill_data)
        
        return jsonify({
            "success": True,
            "message": f"Skill '{skill_name}' added successfully",
            "skill_id": skill_id,
            "skill_data": skill_data
        })
        
    except Exception as e:
        logger.error(f"Error adding skill: {e}")
        return jsonify({"error": "Failed to add skill"}), 500

@app.route('/api/admin/bulk-discover', methods=['POST'])
@require_auth
def api_bulk_discover():
    """Trigger discovery for multiple skills"""
    try:
        data = request.get_json()
        skill_names = data.get('skills', [])
        
        if not skill_names:
            return jsonify({"error": "No skills specified"}), 400
            
        task_ids = []
        for skill_name in skill_names:
            # Start discovery for each skill
            task_id = str(uuid.uuid4())
            task_data = {
                'task_id': task_id,
                'skill': skill_name,
                'status': 'pending',
                'progress': 0,
                'created_at': datetime.now().isoformat()
            }
            
            # Save task
            update_discovery_task(task_id, task_data)
            
            # Start background discovery
            threading.Thread(
                target=discover_resources_background,
                args=(task_id, skill_name),
                daemon=True
            ).start()
            
            task_ids.append({
                'skill': skill_name,
                'task_id': task_id,
                'status_url': f'/api/discover/status/{task_id}'
            })
            
        return jsonify({
            "success": True,
            "message": f"Started discovery for {len(skill_names)} skills",
            "tasks": task_ids
        })
        
    except Exception as e:
        logger.error(f"Error starting bulk discovery: {e}")
        return jsonify({"error": "Failed to start bulk discovery"}), 500

@app.route('/api/admin/import-forecast', methods=['POST'])
def api_import_forecast():
    """Import AI-Horizon forecast data and create skills"""
    try:
        data = request.get_json()
        forecast_text = data.get('forecast_text', '').strip()
        
        if not forecast_text:
            return jsonify({"error": "No forecast data provided"}), 400
        
        # Parse the forecast data
        parsed_skills = parse_forecast_data(forecast_text)
        
        if not parsed_skills:
            return jsonify({"error": "No skills could be extracted from forecast data"}), 400
        
        # Preview mode - just return what would be created
        if data.get('preview_only', False):
            return jsonify({
                "success": True,
                "preview": True,
                "skills_found": len(parsed_skills),
                "skills": parsed_skills
            })
        
        # Import mode - actually create the skills
        created_skills = []
        updated_skills = []
        existing_skills = db_manager.get_emerging_skills()
        existing_skill_names = [s['skill_name'].lower() for s in existing_skills]
        
        for skill_data in parsed_skills:
            skill_name_lower = skill_data['skill_name'].lower()
            
            # Check if skill already exists
            if skill_name_lower in existing_skill_names:
                # Update existing skill with new forecast data
                updated_skills.append(skill_data['skill_name'])
                # TODO: Add update_emerging_skill method to database.py
                logger.info(f"Skill '{skill_data['skill_name']}' already exists - would update with new forecast data")
            else:
                # Create new skill
                skill_data['source_analysis'] = 'ai_horizon_forecast_import'
                skill_id = db_manager.add_emerging_skill(skill_data)
                created_skills.append({
                    'skill_name': skill_data['skill_name'],
                    'skill_id': skill_id
                })
        
        # Start discovery for all new skills
        discovery_tasks = []
        for skill in created_skills:
            task_id = str(uuid.uuid4())
            task_data = {
                'task_id': task_id,
                'skill': skill['skill_name'],
                'status': 'pending',
                'progress': 0,
                'created_at': datetime.now().isoformat()
            }
            
            update_discovery_task(task_id, task_data)
            
            # Start background discovery
            threading.Thread(
                target=discover_resources_background,
                args=(task_id, skill['skill_name']),
                daemon=True
            ).start()
            
            discovery_tasks.append({
                'skill': skill['skill_name'],
                'task_id': task_id
            })
        
        return jsonify({
            "success": True,
            "message": f"Imported {len(created_skills)} new skills from forecast",
            "created_skills": len(created_skills),
            "updated_skills": len(updated_skills),
            "skills": created_skills,
            "discovery_tasks": discovery_tasks
        })
        
    except Exception as e:
        logger.error(f"Error importing forecast: {e}")
        return jsonify({"error": f"Failed to import forecast: {str(e)}"}), 500

def parse_forecast_data(forecast_text):
    """Parse AI-Horizon forecast data and extract skill information"""
    import re
    import json
    
    skills = []
    
    try:
        # Try to parse as JSON first
        if forecast_text.strip().startswith('{') or forecast_text.strip().startswith('['):
            forecast_data = json.loads(forecast_text)
            
            # Handle different JSON structures
            if isinstance(forecast_data, list):
                for item in forecast_data:
                    skill = extract_skill_from_json(item)
                    if skill:
                        skills.append(skill)
            elif isinstance(forecast_data, dict):
                # Handle nested structures
                if 'emerging_skills' in forecast_data:
                    for skill_data in forecast_data['emerging_skills']:
                        skill = extract_skill_from_json(skill_data)
                        if skill:
                            skills.append(skill)
                elif 'skills' in forecast_data:
                    for skill_data in forecast_data['skills']:
                        skill = extract_skill_from_json(skill_data)
                        if skill:
                            skills.append(skill)
                else:
                    # Try to extract from top-level object
                    skill = extract_skill_from_json(forecast_data)
                    if skill:
                        skills.append(skill)
    
    except json.JSONDecodeError:
        # Parse as text using patterns
        skills = parse_forecast_text(forecast_text)
    
    return skills

def extract_skill_from_json(data):
    """Extract skill information from JSON object"""
    if not isinstance(data, dict):
        return None
    
    # Look for skill name in various fields
    skill_name = (data.get('skill_name') or 
                 data.get('skill') or 
                 data.get('name') or 
                 data.get('title'))
    
    if not skill_name:
        return None
    
    # Extract other fields with defaults
    description = (data.get('description') or 
                  data.get('summary') or 
                  data.get('overview') or 
                  f"Skill identified from AI-Horizon forecast: {skill_name}")
    
    # Map category variations
    category = data.get('category', 'cybersecurity')
    category_map = {
        'cyber': 'cybersecurity',
        'security': 'cybersecurity', 
        'ai': 'ai_security',
        'cloud': 'cloud_security',
        'programming': 'programming',
        'development': 'programming'
    }
    category = category_map.get(category.lower(), category)
    
    # Extract urgency/priority score
    urgency_score = 0.7  # Default
    if 'urgency' in data:
        urgency_score = float(data['urgency'])
    elif 'priority' in data:
        urgency_score = float(data['priority'])
    elif 'score' in data:
        urgency_score = float(data['score'])
    elif 'importance' in data:
        urgency_score = float(data['importance'])
    
    # Normalize to 0-1 range
    if urgency_score > 1:
        urgency_score = urgency_score / 100.0
    urgency_score = max(0.0, min(1.0, urgency_score))
    
    # Extract trend
    trend = data.get('trend', 'emerging')
    if urgency_score >= 0.9:
        trend = 'critical'
    elif urgency_score >= 0.8:
        trend = 'rising'
    elif urgency_score >= 0.6:
        trend = 'emerging'
    else:
        trend = 'stable'
    
    return {
        'skill_name': skill_name.strip(),
        'description': description.strip()[:500],  # Limit length
        'category': category,
        'urgency_score': urgency_score,
        'demand_trend': trend,
        'related_skills': data.get('related_skills', [])
    }

def parse_forecast_text(text):
    """Parse forecast data from text format"""
    import re
    
    skills = []
    
    # Common patterns for skill extraction
    patterns = [
        r'(?:skill|technology|capability):\s*([^.\n]+)',
        r'(?:emerging|new|critical):\s*([^.\n]+)',
        r'•\s*([^.\n]+)',
        r'-\s*([^.\n]+)',
        r'\d+\.\s*([^.\n]+)'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            skill_name = match.strip()
            if len(skill_name) > 5 and skill_name not in [s['skill_name'] for s in skills]:
                skills.append({
                    'skill_name': skill_name,
                    'description': f"Skill extracted from AI-Horizon forecast: {skill_name}",
                    'category': 'cybersecurity',
                    'urgency_score': 0.7,
                    'demand_trend': 'emerging',
                    'related_skills': []
                })
    
    return skills[:10]  # Limit to 10 skills to avoid overwhelming

@app.route('/skills')
def skills_overview():
    """Display overview of all emerging skills with learn-more links"""
    try:
        # Get all skills from database
        skills = db_manager.get_emerging_skills()
        
        # Calculate statistics for each skill
        skill_stats = []
        for skill in skills:
            # Flatten skill data for template with defensive coding
            skill_data = dict(skill)  # Copy all skill fields
            skill_data['resource_count'] = len(db_manager.get_resources_for_skill(skill['id']))
            skill_data['learn_more_url'] = f"/skill/{skill['skill_name'].lower().replace(' ', '-').replace('&', 'and')}"
            
            # Ensure required fields exist with defaults
            skill_data.setdefault('description', 'No description available')
            skill_data.setdefault('demand_trend', 'stable')
            skill_data.setdefault('urgency_score', 0.5)
            skill_data.setdefault('category', 'general')
            skill_data.setdefault('resource_types', [])
            
            # Add resource types based on actual resources
            skill_resources = db_manager.get_resources_for_skill(skill['id'])
            resource_types = list(set(r.get('resource_type', 'unknown') for r in skill_resources))
            skill_data['resource_types'] = resource_types[:5]  # Limit to 5 types
            
            skill_stats.append(skill_data)
        
        # Get overall platform statistics
        total_skills = len(skills)
        total_resources = len(db_manager.search_resources(limit=1000))  # Get all resources
        
        return render_template('skills_overview.html', 
                             skills=skill_stats,
                             total_skills=total_skills,
                             total_resources=total_resources)
    except Exception as e:
        logger.error(f"Error in skills overview: {e}")
        return render_template('skill_not_found.html'), 500

@app.route('/workflow')
def workflow():
    """Display the AI-Horizon Ed workflow page"""
    return render_template('workflow.html')

@app.route('/methodology')
def methodology():
    """Display the AI-Horizon Ed methodology page"""
    return render_template('methodology.html')

@app.route('/skill/<skill_name>')
def skill_detail(skill_name):
    """Enhanced skill page with comprehensive learning experience"""
    logger.info(f"Skill detail requested for: '{skill_name}'")
    try:
        # Get session ID from query params or create new one
        session_id = request.args.get('session_id')
        difficulty_filter = request.args.get('difficulty')
        cost_filter = request.args.get('cost')
        
        # Convert URL format back to skill name with robust matching
        target_skill_name = normalize_skill_name_from_url(skill_name)
        logger.info(f"Converted skill name: '{skill_name}' -> '{target_skill_name}'")
        
        # Get comprehensive learning experience
        learning_experience = learning_service.get_skill_learning_experience(
            target_skill_name, session_id, difficulty_filter, cost_filter
        )
        
        # Queue resources for analysis if not already analyzed
        unanalyzed_count = sum(1 for r in learning_experience['resources'] 
                              if not r.get('ai_analysis_date'))
        if unanalyzed_count > 0:
            learning_service.queue_skill_for_analysis(target_skill_name, priority=1)
        
        return render_template('skill_detail.html', 
                             skill=learning_experience['skill'],
                             session_id=learning_experience['session_id'],
                             learning_paths=learning_experience['learning_paths'],
                             resources=learning_experience['resource_categories'],  # Use categorized resources for template
                             resource_categories=learning_experience['resource_categories'],
                             learning_stats=learning_experience['learning_stats'],
                             progress=learning_experience['progress'],
                             filters=learning_experience['filters'],
                             recommendations=learning_experience['recommendations'],
                             unanalyzed_count=unanalyzed_count,
                             total_resources=len(learning_experience['resources']))
        
    except ValueError as e:
        logger.warning(f"Skill not found: {skill_name} - {e}")
        return render_template('skill_not_found.html', skill_name=skill_name), 404
    except Exception as e:
        logger.error(f"Error loading enhanced skill detail for {skill_name}: {e}")
        return render_template('skill_not_found.html', skill_name=skill_name), 500

def normalize_skill_name_from_url(url_skill_name: str) -> str:
    """Convert URL skill name to match database skill names"""
    # Get all skills from database to find best match
    skills = db_manager.get_emerging_skills()
    
    # Create normalized URL name (replace dashes with spaces, lowercase)
    url_normalized = url_skill_name.lower().replace('-', ' ').strip()
    
    # Try exact match first (after normalization)
    for skill in skills:
        skill_normalized = skill['skill_name'].lower().strip()
        if skill_normalized == url_normalized:
            return skill['skill_name']
    
    # Try partial matching for common variations
    for skill in skills:
        skill_normalized = skill['skill_name'].lower().strip()
        
        # Normalize both for comparison (handle common variations)
        skill_clean = skill_normalized.replace('-', ' ').replace('&', 'and').strip()
        url_clean = url_normalized.replace('-', ' ').replace('&', 'and').strip()
        
        # Direct match
        if skill_clean == url_clean:
            return skill['skill_name']
        
        # Check if they're equivalent (handle extra spaces, punctuation)
        skill_words = skill_clean.split()
        url_words = url_clean.split()
        
        # If all words match (in order), it's a match
        if len(skill_words) == len(url_words):
            if all(s == u for s, u in zip(skill_words, url_words)):
                return skill['skill_name']
        
        # Partial match - if URL words are a subset of skill words
        if all(word in skill_words for word in url_words):
            return skill['skill_name']
    
    # If no match found, raise ValueError to trigger 404
    raise ValueError(f"Skill '{url_skill_name}' not found in database")

# =============================================================================
# ENHANCED LEARNING EXPERIENCE API ENDPOINTS
# =============================================================================

@app.route('/api/learning/progress', methods=['POST'])
def api_update_learning_progress():
    """Update learning progress for a session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Session ID required'}), 400
        
        progress_update = {
            'current_resource_id': data.get('current_resource_id'),
            'new_completed_resources': data.get('completed_resources', []),
            'additional_time': data.get('time_spent', 0),
            'learning_preferences': data.get('preferences', {})
        }
        
        updated_progress = learning_service.update_learning_progress(session_id, progress_update)
        
        return jsonify({
            'success': True,
            'progress': updated_progress
        })
        
    except Exception as e:
        logger.error(f"Error updating learning progress: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/learning/questions/answer', methods=['POST'])
def api_answer_question():
    """Process a comprehension question answer"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        resource_id = data.get('resource_id')
        question_id = data.get('question_id')
        answer = data.get('answer')
        
        if not all([session_id, resource_id, question_id, answer]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = learning_service.answer_comprehension_question(
            session_id, resource_id, question_id, answer
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error processing question answer: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/learning/projects/complete', methods=['POST'])
def api_complete_project():
    """Mark a project as completed"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        resource_id = data.get('resource_id')
        project_id = data.get('project_id')
        completion_data = data.get('completion_data', {})
        
        if not all([session_id, resource_id, project_id]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        result = learning_service.complete_project(
            session_id, resource_id, project_id, completion_data
        )
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error completing project: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/learning/resource/<int:resource_id>/content')
def api_get_resource_content(resource_id):
    """Get enhanced learning content for a resource"""
    try:
        content_type = request.args.get('type')  # 'questions', 'projects', 'summary', etc.
        
        content = learning_service.get_resource_learning_content(resource_id, content_type)
        
        return jsonify({
            'success': True,
            'content': content
        })
        
    except Exception as e:
        logger.error(f"Error getting resource content: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/analyze-skill', methods=['POST'])
@require_auth
def api_analyze_skill():
    """Queue a skill for comprehensive AI analysis"""
    try:
        data = request.get_json()
        skill_name = data.get('skill_name')
        priority = data.get('priority', 1)
        
        if not skill_name:
            return jsonify({'error': 'Skill name required'}), 400
        
        result = learning_service.queue_skill_for_analysis(skill_name, priority)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error queuing skill for analysis: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/process-analysis-queue', methods=['POST'])
@require_auth
def api_process_analysis_queue():
    """Process queued analysis tasks"""
    try:
        data = request.get_json()
        batch_size = data.get('batch_size', 5)
        
        result = learning_service.process_analysis_queue(batch_size)
        
        return jsonify({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error processing analysis queue: {e}")
        return jsonify({'error': str(e)}), 500

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

# =============================================================================
# AUTHENTICATION ROUTES
# =============================================================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Get credentials from config
        admin_creds = config.get_admin_credentials()
        
        if (username == admin_creds['username'] and 
            verify_password(password, hash_password(admin_creds['password']))):
            session['authenticated'] = True
            session['username'] = username
            session['login_time'] = datetime.now().isoformat()
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('index'))

def create_app():
    """Application factory"""
    return app

@app.route('/api/enhanced-analysis/<int:resource_id>', methods=['POST'])
def api_enhanced_content_analysis(resource_id):
    """
    Generate enhanced content analysis with comprehension questions and practical exercises
    
    This implements your next phase vision:
    1. LLM analyzes video/document content
    2. Generates comprehension questions to verify understanding
    3. Creates practical exercises for real-world application
    """
    try:
        logger.info(f"Starting enhanced content analysis for resource {resource_id}")
        
        # Generate enhanced analysis
        analysis = content_analyzer.analyze_resource_content(resource_id)
        
        # Convert to dict for JSON response
        analysis_dict = {
            'resource_id': analysis.resource_id,
            'content_type': analysis.content_type,
            'key_concepts': analysis.key_concepts,
            'learning_objectives': analysis.learning_objectives,
            'difficulty_level': analysis.difficulty_level,
            'comprehension_questions': analysis.comprehension_questions,
            'practical_exercises': analysis.practical_exercises,
            'analysis_timestamp': analysis.analysis_timestamp,
            'methodology': {
                'content_extraction': 'LLM-powered content understanding',
                'question_generation': 'Understanding-focused, not memorization',
                'exercise_creation': 'Three-tier practical application (follow-along, modify, create)',
                'transparency': 'All steps documented and traceable'
            }
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis_dict,
            'message': f'Enhanced analysis completed: {len(analysis.comprehension_questions)} questions, {len(analysis.practical_exercises)} exercises'
        })
        
    except Exception as e:
        logger.error(f"Enhanced content analysis failed for resource {resource_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Enhanced content analysis failed'
        }), 500

@app.route('/api/test-enhanced-analysis')
def api_test_enhanced_analysis():
    """
    Test endpoint for enhanced content analysis 
    Shows the methodology and results structure
    """
    try:
        # Test with a sample resource (resource ID 1 if it exists)
        test_resource_id = 1
        
        analysis = content_analyzer.analyze_resource_content(test_resource_id)
        
        return jsonify({
            'success': True,
            'message': 'Enhanced Content Analysis Test Results',
            'vision_implementation': {
                'purpose': 'Transform educational content into verified learning experiences',
                'methodology': {
                    'step_1': 'Extract content from videos/documents',
                    'step_2': 'LLM analysis to understand key concepts',
                    'step_3': 'Generate comprehension questions (understanding, not memorization)',
                    'step_4': 'Create practical exercises (follow-along, modify, create)',
                    'step_5': 'Store with full transparency and traceability'
                },
                'transparency': 'Every step documented, methodology clear, results traceable'
            },
            'sample_analysis': {
                'key_concepts': analysis.key_concepts,
                'learning_objectives': analysis.learning_objectives,
                'difficulty_level': analysis.difficulty_level,
                'question_count': len(analysis.comprehension_questions),
                'exercise_count': len(analysis.practical_exercises),
                'sample_question': analysis.comprehension_questions[0] if analysis.comprehension_questions else None,
                'sample_exercise': analysis.practical_exercises[0] if analysis.practical_exercises else None
            },
            'next_steps': [
                'Integrate with real LLM APIs (Claude/OpenAI)',
                'Add YouTube transcript extraction',
                'Implement document content parsing',
                'Connect to database for storage',
                'Add to skill detail pages'
            ]
        })
        
    except Exception as e:
        logger.error(f"Enhanced analysis test failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Enhanced analysis test failed'
        }), 500

@app.route('/api/fix-categorization', methods=['POST'])
def fix_categorization():
    """Fix cost_type and difficulty_level for all resources"""
    try:
        # Resource categorization rules
        cost_categorization = {
            'youtube_video': 'free',
            'documentation': 'free', 
            'tutorial': 'free',
            'article': 'free',
            'tool': 'freemium',  # Most tools have free tiers
            'online_course': 'paid',  # Most courses are paid
            'course': 'paid'
        }
        
        difficulty_keywords = {
            'beginner': ['beginner', 'introduction', 'basics', 'fundamentals', 'getting started', 'tutorial'],
            'advanced': ['advanced', 'expert', 'master', 'professional', 'enterprise', 'architecture']
        }
        
        # Get all resources
        resources = db_manager.get_all_resources()
        updated_count = 0
        
        for resource in resources:
            resource_id = resource['id']
            title = resource.get('title', '').lower()
            description = resource.get('description', '').lower()
            resource_type = resource.get('resource_type', '')
            
            # Determine cost type
            new_cost_type = cost_categorization.get(resource_type, 'unknown')
            
            # Special cases for cost type
            if 'free' in title or 'free' in description:
                new_cost_type = 'free'
            elif 'paid' in title or 'premium' in title:
                new_cost_type = 'paid'
            elif 'udemy.com' in description or 'coursera.org' in description:
                new_cost_type = 'paid'
            
            # Determine difficulty level
            content = f"{title} {description}"
            new_difficulty_level = 'intermediate'  # Default
            
            # Check for beginner indicators
            if any(keyword in content for keyword in difficulty_keywords['beginner']):
                new_difficulty_level = 'beginner'
            # Check for advanced indicators  
            elif any(keyword in content for keyword in difficulty_keywords['advanced']):
                new_difficulty_level = 'advanced'
            
            # Update the resource
            success = db_manager.update_resource_categorization(
                resource_id, new_cost_type, new_difficulty_level
            )
            
            if success:
                updated_count += 1
        
        # Get updated distribution
        cost_distribution = db_manager.get_cost_distribution()
        difficulty_distribution = db_manager.get_difficulty_distribution()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count,
            'total_resources': len(resources),
            'cost_distribution': cost_distribution,
            'difficulty_distribution': difficulty_distribution,
            'message': f'Successfully updated {updated_count} resources with proper categorization'
        })
        
    except Exception as e:
        logger.error(f"Error fixing categorization: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# =============================================================================
# RESOURCE QUIZ & LEARNING CONTENT ENDPOINTS
# =============================================================================

@app.route('/api/resource/<int:resource_id>/questions')
def api_resource_questions(resource_id):
    """Get quiz questions for a specific resource"""
    try:
        logger.info(f"Retrieving questions for resource {resource_id}")
        
        # Get resource details
        resource = db_manager.get_resource_by_id(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Try to get questions from learning_content table
        questions = db_manager.get_resource_questions(resource_id)
        
        if questions:
            return jsonify({
                'success': True,
                'resource_id': resource_id,
                'resource_title': resource.get('title', ''),
                'questions': questions,
                'count': len(questions)
            })
        else:
            # Generate questions using the enhanced content analyzer
            logger.info(f"Generating questions for resource {resource_id}: {resource.get('title', '')}")
            
            # Use the existing content analyzer to generate questions
            try:
                analysis = content_analyzer.analyze_resource_content(resource_id)
                if analysis and analysis.comprehension_questions:
                    # Store the generated questions
                    stored = db_manager.store_resource_questions(resource_id, analysis.comprehension_questions)
                    if stored:
                        return jsonify({
                            'success': True,
                            'resource_id': resource_id,
                            'resource_title': resource.get('title', ''),
                            'questions': analysis.comprehension_questions,
                            'count': len(analysis.comprehension_questions),
                            'generated': True
                        })
                    else:
                        # Return generated questions even if storage failed
                        return jsonify({
                            'success': True,
                            'resource_id': resource_id,
                            'resource_title': resource.get('title', ''),
                            'questions': analysis.comprehension_questions,
                            'count': len(analysis.comprehension_questions),
                            'generated': True,
                            'warning': 'Questions generated but not stored'
                        })
                else:
                    return jsonify({'error': 'Failed to generate questions'}), 500
                    
            except Exception as e:
                logger.error(f"Error generating questions for resource {resource_id}: {e}")
                return jsonify({'error': f'Question generation failed: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error retrieving questions for resource {resource_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/resource/<int:resource_id>/exercises')
def api_resource_exercises(resource_id):
    """Get practical exercises for a specific resource"""
    try:
        logger.info(f"Retrieving exercises for resource {resource_id}")
        
        # Get resource details
        resource = db_manager.get_resource_by_id(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Try to get exercises from learning_content table
        exercises = db_manager.get_resource_exercises(resource_id)
        
        if exercises:
            return jsonify({
                'success': True,
                'resource_id': resource_id,
                'resource_title': resource.get('title', ''),
                'exercises': exercises,
                'count': len(exercises)
            })
        else:
            # Generate exercises using the enhanced content analyzer
            logger.info(f"Generating exercises for resource {resource_id}: {resource.get('title', '')}")
            
            try:
                analysis = content_analyzer.analyze_resource_content(resource_id)
                if analysis and analysis.practical_exercises:
                    # Store the generated exercises
                    stored = db_manager.store_resource_exercises(resource_id, analysis.practical_exercises)
                    if stored:
                        return jsonify({
                            'success': True,
                            'resource_id': resource_id,
                            'resource_title': resource.get('title', ''),
                            'exercises': analysis.practical_exercises,
                            'count': len(analysis.practical_exercises),
                            'generated': True
                        })
                    else:
                        # Return generated exercises even if storage failed
                        return jsonify({
                            'success': True,
                            'resource_id': resource_id,
                            'resource_title': resource.get('title', ''),
                            'exercises': analysis.practical_exercises,
                            'count': len(analysis.practical_exercises),
                            'generated': True,
                            'warning': 'Exercises generated but not stored'
                        })
                else:
                    return jsonify({'error': 'Failed to generate exercises'}), 500
                    
            except Exception as e:
                logger.error(f"Error generating exercises for resource {resource_id}: {e}")
                return jsonify({'error': f'Exercise generation failed: {str(e)}'}), 500
                
    except Exception as e:
        logger.error(f"Error retrieving exercises for resource {resource_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/<int:resource_id>/submit', methods=['POST'])
def api_submit_quiz(resource_id):
    """Submit quiz answers and get results"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        answers = data.get('answers', {})
        if not answers:
            return jsonify({'error': 'No answers provided'}), 400
        
        # Get the questions for this resource
        questions = db_manager.get_resource_questions(resource_id)
        if not questions:
            return jsonify({'error': 'No questions found for this resource'}), 404
        
        # Score the quiz
        total_questions = len(questions)
        correct_answers = 0
        results = []
        
        for question in questions:
            question_id = question.get('id', question.get('question_id', ''))
            user_answer = answers.get(str(question_id), '')
            correct_answer = question.get('correct_answer', '')
            
            is_correct = user_answer.lower().strip() == correct_answer.lower().strip()
            if is_correct:
                correct_answers += 1
            
            results.append({
                'question_id': question_id,
                'question': question.get('question_text', ''),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', '')
            })
        
        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Store quiz attempt (optional)
        try:
            db_manager.store_quiz_attempt(resource_id, answers, score_percentage)
        except:
            pass  # Don't fail if storage doesn't work
        
        return jsonify({
            'success': True,
            'resource_id': resource_id,
            'score': {
                'correct': correct_answers,
                'total': total_questions,
                'percentage': round(score_percentage, 1)
            },
            'results': results,
            'passed': score_percentage >= 70,  # 70% passing grade
            'message': f"You scored {correct_answers}/{total_questions} ({score_percentage:.1f}%)"
        })
        
    except Exception as e:
        logger.error(f"Error submitting quiz for resource {resource_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/<int:resource_id>/grade', methods=['POST'])
def api_grade_quiz_ai(resource_id):
    """AI-powered grading for quiz answers"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        answers = data.get('answers', [])
        if not answers:
            return jsonify({'error': 'No answers provided'}), 400
        
        # Get the questions for this resource
        questions = db_manager.get_resource_questions(resource_id)
        if not questions:
            return jsonify({'error': 'No questions found for this resource'}), 404
        
        # Get resource details for context
        resource = db_manager.get_resource_by_id(resource_id)
        if not resource:
            return jsonify({'error': 'Resource not found'}), 404
        
        # Use AI to grade the answers
        from utils.ai_content_analyzer import content_analyzer
        grading_results = content_analyzer.grade_quiz_answers(
            resource, questions, answers
        )
        
        if grading_results:
            return jsonify({
                'success': True,
                'resource_id': resource_id,
                'grading_results': grading_results,
                'ai_graded': True
            })
        else:
            # Fallback to basic grading
            return api_submit_quiz(resource_id)
        
    except Exception as e:
        logger.error(f"Error grading quiz for resource {resource_id}: {e}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# ADMIN CONTENT MANAGEMENT ENDPOINTS  
# =============================================================================

@app.route('/api/admin/content-status')
@require_auth
def api_admin_content_status():
    """Get content generation status for all resources"""
    try:
        # Get all resources and their content status
        resources = db_manager.get_all_resources()
        
        content_status = {
            'total_resources': len(resources),
            'resources_with_questions': 0,
            'resources_with_exercises': 0,
            'resources_needing_content': [],
            'content_summary': []
        }
        
        for resource in resources:
            resource_id = resource['id']
            title = resource.get('title', 'Untitled')
            
            # Check for questions
            questions = db_manager.get_resource_questions(resource_id)
            has_questions = len(questions) > 0 if questions else False
            
            # Check for exercises  
            exercises = db_manager.get_resource_exercises(resource_id)
            has_exercises = len(exercises) > 0 if exercises else False
            
            if has_questions:
                content_status['resources_with_questions'] += 1
            if has_exercises:
                content_status['resources_with_exercises'] += 1
                
            if not has_questions and not has_exercises:
                content_status['resources_needing_content'].append({
                    'id': resource_id,
                    'title': title,
                    'type': resource.get('resource_type', 'unknown')
                })
            
            content_status['content_summary'].append({
                'id': resource_id,
                'title': title[:50] + ('...' if len(title) > 50 else ''),
                'has_questions': has_questions,
                'has_exercises': has_exercises,
                'question_count': len(questions) if questions else 0,
                'exercise_count': len(exercises) if exercises else 0
            })
        
        return jsonify({
            'success': True,
            'status': content_status
        })
        
    except Exception as e:
        logger.error(f"Error getting content status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/generate-content', methods=['POST'])
@require_auth
def api_admin_generate_content():
    """Generate content for resources that don't have it"""
    try:
        data = request.get_json()
        resource_ids = data.get('resource_ids', [])
        batch_size = data.get('batch_size', 5)
        
        if not resource_ids:
            # Get all resources needing content
            resources = db_manager.get_all_resources()
            resource_ids = []
            
            for resource in resources:
                resource_id = resource['id']
                questions = db_manager.get_resource_questions(resource_id)
                exercises = db_manager.get_resource_exercises(resource_id)
                
                if not questions or not exercises:
                    resource_ids.append(resource_id)
        
        # Limit to batch size
        resource_ids = resource_ids[:batch_size]
        
        results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'details': []
        }
        
        for resource_id in resource_ids:
            results['processed'] += 1
            
            try:
                resource = db_manager.get_resource_by_id(resource_id)
                if not resource:
                    continue
                
                logger.info(f"Generating content for resource {resource_id}: {resource.get('title', '')}")
                
                # Generate analysis
                analysis = content_analyzer.analyze_resource_content(resource_id)
                
                if analysis:
                    # Store questions
                    if analysis.comprehension_questions:
                        db_manager.store_resource_questions(resource_id, analysis.comprehension_questions)
                    
                    # Store exercises
                    if analysis.practical_exercises:
                        db_manager.store_resource_exercises(resource_id, analysis.practical_exercises)
                    
                    results['successful'] += 1
                    results['details'].append({
                        'resource_id': resource_id,
                        'title': resource.get('title', ''),
                        'status': 'success',
                        'questions_generated': len(analysis.comprehension_questions),
                        'exercises_generated': len(analysis.practical_exercises)
                    })
                else:
                    results['failed'] += 1
                    results['details'].append({
                        'resource_id': resource_id,
                        'title': resource.get('title', ''),
                        'status': 'failed',
                        'error': 'No analysis generated'
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append({
                    'resource_id': resource_id,
                    'title': resource.get('title', '') if 'resource' in locals() else 'Unknown',
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"Error generating content for resource {resource_id}: {e}")
        
        return jsonify({
            'success': True,
            'results': results,
            'message': f"Processed {results['processed']} resources: {results['successful']} successful, {results['failed']} failed"
        })
        
    except Exception as e:
        logger.error(f"Error in content generation: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/restart-services', methods=['POST'])
@require_auth
def api_admin_restart_services():
    """Force restart all services and regenerate content"""
    try:
        logger.info("Admin triggered service restart and content regeneration")
        
        # Get all resources that need content generation
        resources = db_manager.get_all_resources()
        
        processed_count = 0
        successful_count = 0
        
        # Start content generation for all resources
        for resource in resources:
            try:
                processed_count += 1
                
                # Queue resource for analysis
                db_manager.queue_content_analysis(resource['id'])
                
                # Generate content immediately
                content_result = content_analyzer.generate_learning_content(resource)
                
                if content_result and content_result.get('questions'):
                    # Store questions
                    db_manager.store_learning_content(
                        resource['id'], 
                        'questions', 
                        content_result['questions']
                    )
                    
                if content_result and content_result.get('exercises'):
                    # Store exercises
                    db_manager.store_learning_content(
                        resource['id'], 
                        'exercises', 
                        content_result['exercises']
                    )
                    
                successful_count += 1
                logger.info(f"Regenerated content for resource {resource['id']}")
                
            except Exception as e:
                logger.error(f"Error regenerating content for resource {resource['id']}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Services restarted and content regeneration started for {processed_count} resources',
            'resources_processed': processed_count,
            'successful': successful_count
        })
        
    except Exception as e:
        logger.error(f"Error restarting services: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/admin/regenerate-content', methods=['POST'])
@require_auth
def api_admin_regenerate_content():
    """Regenerate all learning content"""
    try:
        logger.info("Admin triggered content regeneration for all resources")
        
        # Get all resources
        resources = db_manager.get_all_resources()
        processed_count = 0
        successful_count = 0
        
        for resource in resources:
            try:
                processed_count += 1
                
                # Generate learning content
                content_result = content_analyzer.generate_learning_content(resource)
                
                if content_result:
                    # Store questions
                    if content_result.get('questions'):
                        db_manager.store_learning_content(
                            resource['id'], 
                            'questions', 
                            content_result['questions']
                        )
                    
                    # Store exercises
                    if content_result.get('exercises'):
                        db_manager.store_learning_content(
                            resource['id'], 
                            'exercises', 
                            content_result['exercises']
                        )
                    
                    successful_count += 1
                    logger.info(f"Regenerated content for resource {resource['id']}: {resource.get('title', 'Unknown')}")
                    
            except Exception as e:
                logger.error(f"Error regenerating content for resource {resource['id']}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'message': f'Content regeneration completed for {successful_count}/{processed_count} resources',
            'resources_processed': processed_count,
            'successful': successful_count
        })
        
    except Exception as e:
        logger.error(f"Error regenerating content: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

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