"""
Database management for AI-Horizon Educational Resources System
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging

from .config import config

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database manager for educational resources system"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager"""
        if db_path is None:
            db_path = config.get('DATABASE_URL', 'sqlite:///data/aih_edu.db')
            # Remove 'sqlite:///' prefix if present
            if db_path.startswith('sqlite:///'):
                db_path = db_path[10:]
        
        self.db_path = db_path
        self._ensure_data_directory()
        self._initialize_database()
    
    def _ensure_data_directory(self):
        """Ensure data directory exists"""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Educational Resources table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS educational_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    url TEXT UNIQUE NOT NULL,
                    resource_type TEXT NOT NULL,
                    skill_category TEXT NOT NULL,
                    learning_level TEXT NOT NULL,
                    duration_minutes INTEGER,
                    language TEXT DEFAULT 'en',
                    quality_score REAL DEFAULT 0.0,
                    popularity_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,  -- JSON metadata
                    keywords TEXT,  -- Comma-separated keywords
                    author TEXT,
                    source TEXT,
                    rating REAL DEFAULT 0.0,
                    review_count INTEGER DEFAULT 0,
                    prerequisites TEXT,  -- JSON array of prerequisites
                    learning_outcomes TEXT  -- JSON array of outcomes
                )
            ''')
            
            # User Preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    skill_interests TEXT,  -- JSON array of skills
                    learning_level TEXT DEFAULT 'intermediate',
                    preferred_resource_types TEXT,  -- JSON array
                    preferred_duration_range TEXT,  -- JSON object {min, max}
                    language_preferences TEXT,  -- JSON array
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            ''')
            
            # Learning Paths table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    skill_category TEXT NOT NULL,
                    difficulty_level TEXT NOT NULL,
                    estimated_hours INTEGER,
                    created_by TEXT,
                    resource_sequence TEXT,  -- JSON array of resource IDs in order
                    prerequisites TEXT,  -- JSON array of prerequisites
                    learning_outcomes TEXT,  -- JSON array of outcomes
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_public BOOLEAN DEFAULT 1,
                    rating REAL DEFAULT 0.0,
                    completion_count INTEGER DEFAULT 0
                )
            ''')
            
            # User Progress table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    resource_id INTEGER,
                    learning_path_id INTEGER,
                    progress_percentage REAL DEFAULT 0.0,
                    completion_status TEXT DEFAULT 'not_started',  -- not_started, in_progress, completed
                    time_spent_minutes INTEGER DEFAULT 0,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    rating REAL,
                    FOREIGN KEY (resource_id) REFERENCES educational_resources (id),
                    FOREIGN KEY (learning_path_id) REFERENCES learning_paths (id)
                )
            ''')
            
            # Resource Collections table (curated lists)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS resource_collections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    created_by TEXT NOT NULL,
                    resource_ids TEXT,  -- JSON array of resource IDs
                    tags TEXT,  -- JSON array of tags
                    is_public BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    view_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0
                )
            ''')
            
            # Search History table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    search_query TEXT NOT NULL,
                    skill_category TEXT,
                    learning_level TEXT,
                    resource_type TEXT,
                    results_count INTEGER DEFAULT 0,
                    search_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    filters_applied TEXT  -- JSON object of applied filters
                )
            ''')
            
            # Emerging Skills table (from main platform analysis)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS emerging_skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    urgency_score REAL DEFAULT 0.0,
                    demand_trend TEXT DEFAULT 'stable',  -- 'rising', 'stable', 'critical'
                    source_analysis TEXT,  -- Which analysis identified this skill
                    identified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    job_market_data TEXT,  -- JSON with supporting data
                    related_skills TEXT,  -- JSON array of related/prerequisite skills
                    description TEXT,
                    auto_discovered BOOLEAN DEFAULT 1,
                    resource_discovery_status TEXT DEFAULT 'pending'  -- 'pending', 'in_progress', 'completed'
                )
            ''')
            
            # Skill-Resource Mapping table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_resource_mapping (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id INTEGER REFERENCES emerging_skills(id),
                    resource_id INTEGER REFERENCES educational_resources(id),
                    relevance_score REAL DEFAULT 0.0,
                    resource_type_for_skill TEXT,  -- 'foundation', 'practical', 'advanced', 'certification'
                    auto_discovered BOOLEAN DEFAULT 1,
                    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (skill_id) REFERENCES emerging_skills (id),
                    FOREIGN KEY (resource_id) REFERENCES educational_resources (id)
                )
            ''')

            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_category ON educational_resources(skill_category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_level ON educational_resources(learning_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_type ON educational_resources(resource_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_quality ON educational_resources(quality_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_progress_user ON user_progress(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_search_user ON search_history(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_emerging_skills_urgency ON emerging_skills(urgency_score)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_mapping ON skill_resource_mapping(skill_id, resource_id)')
            
            conn.commit()
            logger.info("Educational resources database initialized successfully")
    
    def add_resource(self, resource_data: Dict[str, Any]) -> int:
        """Add a new educational resource"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Prepare data
            metadata = json.dumps(resource_data.get('metadata', {}))
            prerequisites = json.dumps(resource_data.get('prerequisites', []))
            learning_outcomes = json.dumps(resource_data.get('learning_outcomes', []))
            keywords = ','.join(resource_data.get('keywords', []))
            
            cursor.execute('''
                INSERT INTO educational_resources 
                (title, description, url, resource_type, skill_category, learning_level,
                 duration_minutes, language, quality_score, popularity_score, metadata,
                 keywords, author, source, rating, review_count, prerequisites, learning_outcomes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                resource_data['title'],
                resource_data.get('description', ''),
                resource_data['url'],
                resource_data['resource_type'],
                resource_data['skill_category'],
                resource_data['learning_level'],
                resource_data.get('duration_minutes', 0),
                resource_data.get('language', 'en'),
                resource_data.get('quality_score', 0.0),
                resource_data.get('popularity_score', 0.0),
                metadata,
                keywords,
                resource_data.get('author', ''),
                resource_data.get('source', ''),
                resource_data.get('rating', 0.0),
                resource_data.get('review_count', 0),
                prerequisites,
                learning_outcomes
            ))
            
            resource_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added educational resource: {resource_data['title']} (ID: {resource_id})")
            return resource_id
    
    def search_resources(self, 
                        query: Optional[str] = None,
                        skill_category: Optional[str] = None,
                        learning_level: Optional[str] = None,
                        resource_type: Optional[str] = None,
                        min_quality: float = 0.0,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Search for educational resources"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query
            where_conditions = ["quality_score >= ?"]
            params = [min_quality]
            
            if query:
                where_conditions.append("(title LIKE ? OR description LIKE ? OR keywords LIKE ?)")
                query_param = f"%{query}%"
                params.extend([query_param, query_param, query_param])
            
            if skill_category:
                where_conditions.append("skill_category = ?")
                params.append(skill_category)
            
            if learning_level:
                where_conditions.append("learning_level = ?")
                params.append(learning_level)
            
            if resource_type:
                where_conditions.append("resource_type = ?")
                params.append(resource_type)
            
            where_clause = " AND ".join(where_conditions)
            
            sql = f'''
                SELECT * FROM educational_resources 
                WHERE {where_clause}
                ORDER BY quality_score DESC, popularity_score DESC, created_at DESC
                LIMIT ?
            '''
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            resources = []
            for row in rows:
                resource = dict(row)
                # Parse JSON fields
                resource['metadata'] = json.loads(resource['metadata'] or '{}')
                resource['prerequisites'] = json.loads(resource['prerequisites'] or '[]')
                resource['learning_outcomes'] = json.loads(resource['learning_outcomes'] or '[]')
                resource['keywords'] = [k.strip() for k in resource['keywords'].split(',') if k.strip()]
                resources.append(resource)
            
            return resources
    
    def get_resource_by_id(self, resource_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific resource by ID"""
        resources = self.search_resources()
        for resource in resources:
            if resource['id'] == resource_id:
                return resource
        return None
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """Update user preferences"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert lists to JSON
            skill_interests = json.dumps(preferences.get('skill_interests', []))
            preferred_resource_types = json.dumps(preferences.get('preferred_resource_types', []))
            preferred_duration_range = json.dumps(preferences.get('preferred_duration_range', {}))
            language_preferences = json.dumps(preferences.get('language_preferences', ['en']))
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences
                (user_id, skill_interests, learning_level, preferred_resource_types,
                 preferred_duration_range, language_preferences, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                skill_interests,
                preferences.get('learning_level', 'intermediate'),
                preferred_resource_types,
                preferred_duration_range,
                language_preferences,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"Updated preferences for user: {user_id}")
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total resources
            cursor.execute("SELECT COUNT(*) FROM educational_resources")
            total_resources = cursor.fetchone()[0]
            
            # Resources by category
            cursor.execute('''
                SELECT skill_category, COUNT(*) as count 
                FROM educational_resources 
                GROUP BY skill_category
            ''')
            by_category = dict(cursor.fetchall())
            
            # Resources by type
            cursor.execute('''
                SELECT resource_type, COUNT(*) as count 
                FROM educational_resources 
                GROUP BY resource_type
            ''')
            by_type = dict(cursor.fetchall())
            
            # Average quality score
            cursor.execute("SELECT AVG(quality_score) FROM educational_resources")
            avg_quality = cursor.fetchone()[0] or 0.0
            
            return {
                'total_resources': total_resources,
                'by_category': by_category,
                'by_type': by_type,
                'average_quality': round(avg_quality, 2)
            }
    
    def log_search(self, user_id: Optional[str], search_params: Dict[str, Any], results_count: int) -> None:
        """Log search activity for analytics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            filters_applied = json.dumps({
                k: v for k, v in search_params.items() 
                if k not in ['query'] and v is not None
            })
            
            cursor.execute('''
                INSERT INTO search_history
                (user_id, search_query, skill_category, learning_level, resource_type,
                 results_count, filters_applied)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                search_params.get('query', ''),
                search_params.get('skill_category'),
                search_params.get('learning_level'),
                search_params.get('resource_type'),
                results_count,
                filters_applied
            ))
            
            conn.commit()
    
    def add_emerging_skill(self, skill_data: Dict[str, Any]) -> int:
        """Add a new emerging skill"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Prepare JSON data
            job_market_data = json.dumps(skill_data.get('job_market_data', {}))
            related_skills = json.dumps(skill_data.get('related_skills', []))
            
            cursor.execute('''
                INSERT OR REPLACE INTO emerging_skills 
                (skill_name, category, urgency_score, demand_trend, source_analysis,
                 job_market_data, related_skills, description, auto_discovered)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill_data['skill_name'],
                skill_data.get('category', 'cybersecurity'),
                skill_data.get('urgency_score', 0.0),
                skill_data.get('demand_trend', 'stable'),
                skill_data.get('source_analysis', 'manual'),
                job_market_data,
                related_skills,
                skill_data.get('description', ''),
                skill_data.get('auto_discovered', True)
            ))
            
            skill_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added emerging skill: {skill_data['skill_name']} (ID: {skill_id})")
            return skill_id
    
    def get_emerging_skills(self, limit: int = 50, urgency_threshold: float = 0.0) -> List[Dict[str, Any]]:
        """Get emerging skills ordered by urgency"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM emerging_skills 
                WHERE urgency_score >= ?
                ORDER BY urgency_score DESC, identified_date DESC
                LIMIT ?
            ''', (urgency_threshold, limit))
            
            rows = cursor.fetchall()
            skills = []
            for row in rows:
                skill = dict(row)
                skill['job_market_data'] = json.loads(skill['job_market_data'] or '{}')
                skill['related_skills'] = json.loads(skill['related_skills'] or '[]')
                skills.append(skill)
            
            return skills
    
    def update_skill_discovery_status(self, skill_id: int, status: str) -> None:
        """Update resource discovery status for a skill"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE emerging_skills 
                SET resource_discovery_status = ?, last_updated = ?
                WHERE id = ?
            ''', (status, datetime.now().isoformat(), skill_id))
            conn.commit()
    
    def link_skill_to_resource(self, skill_id: int, resource_id: int, relevance_score: float, 
                              resource_type_for_skill: str = 'general') -> None:
        """Link an emerging skill to an educational resource"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO skill_resource_mapping
                (skill_id, resource_id, relevance_score, resource_type_for_skill)
                VALUES (?, ?, ?, ?)
            ''', (skill_id, resource_id, relevance_score, resource_type_for_skill))
            conn.commit()
    
    def get_resources_for_skill(self, skill_id: int) -> List[Dict[str, Any]]:
        """Get all resources linked to a specific skill"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT er.*, srm.relevance_score, srm.resource_type_for_skill
                FROM educational_resources er
                JOIN skill_resource_mapping srm ON er.id = srm.resource_id
                WHERE srm.skill_id = ?
                ORDER BY srm.relevance_score DESC, er.quality_score DESC
            ''', (skill_id,))
            
            rows = cursor.fetchall()
            resources = []
            for row in rows:
                resource = dict(row)
                resource['metadata'] = json.loads(resource['metadata'] or '{}')
                resource['prerequisites'] = json.loads(resource['prerequisites'] or '[]')
                resource['learning_outcomes'] = json.loads(resource['learning_outcomes'] or '[]')
                resource['keywords'] = [k.strip() for k in resource['keywords'].split(',') if k.strip()]
                resources.append(resource)
            
            return resources

# Global database instance
db_manager = DatabaseManager() 