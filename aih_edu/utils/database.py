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
                    learning_outcomes TEXT,  -- JSON array of outcomes
                    
                    -- Enhanced Learning Experience Fields
                    difficulty_level TEXT DEFAULT 'unknown',  -- beginner|intermediate|advanced|expert
                    cost_type TEXT DEFAULT 'unknown',         -- free|freemium|paid
                    estimated_duration INTEGER DEFAULT 0,    -- minutes (more precise than duration_minutes)
                    learning_objectives TEXT DEFAULT '[]',   -- AI-extracted learning goals (JSON)
                    sequence_order INTEGER DEFAULT 0,        -- optimal learning order within skill
                    ai_analysis_date TIMESTAMP,              -- when AI analysis was performed
                    admin_reviewed BOOLEAN DEFAULT 0,        -- human-reviewed flag
                    content_extracted TEXT,                  -- extracted content for AI analysis (JSON)
                    source_platform TEXT                     -- youtube|coursera|udemy|github|etc
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

            # AI-Generated Learning Content table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_id INTEGER REFERENCES educational_resources(id),
                    skill_id INTEGER REFERENCES emerging_skills(id),
                    content_type TEXT NOT NULL,  -- 'questions'|'projects'|'summary'|'objectives'
                    content_data TEXT NOT NULL,  -- JSON with questions/projects/etc
                    ai_model_used TEXT,          -- 'claude-3'|'gpt-4'|'combined'
                    ai_generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    admin_approved BOOLEAN DEFAULT 0,
                    admin_modified TEXT DEFAULT NULL,  -- admin edits/additions (JSON)
                    quality_score REAL DEFAULT 0.0,    -- quality of generated content
                    usage_count INTEGER DEFAULT 0,     -- how often content is accessed
                    feedback_rating REAL DEFAULT 0.0,  -- user feedback on content quality
                    FOREIGN KEY (resource_id) REFERENCES educational_resources (id),
                    FOREIGN KEY (skill_id) REFERENCES emerging_skills (id)
                )
            ''')
            
            # Enhanced Learning Paths for Skills
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS skill_learning_paths (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    skill_id INTEGER REFERENCES emerging_skills(id),
                    path_name TEXT NOT NULL,  -- 'beginner'|'intermediate'|'advanced'|'expert'
                    path_description TEXT,
                    resource_sequence TEXT NOT NULL,  -- JSON array of resource IDs in optimal order
                    estimated_duration INTEGER,       -- total minutes for path
                    difficulty_progression TEXT,      -- JSON showing difficulty curve
                    prerequisites TEXT DEFAULT '[]',  -- JSON array of required skills/knowledge
                    learning_milestones TEXT DEFAULT '[]',  -- JSON array of checkpoints
                    completion_projects TEXT DEFAULT '[]',  -- JSON array of final projects
                    ai_generated BOOLEAN DEFAULT 1,
                    admin_curated BOOLEAN DEFAULT 0,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0,
                    completion_rate REAL DEFAULT 0.0,  -- percentage of users who complete
                    FOREIGN KEY (skill_id) REFERENCES emerging_skills (id)
                )
            ''')
            
            # Learning Progress Tracking (Session-based for anonymous users)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,  -- browser session or generated ID
                    skill_id INTEGER REFERENCES emerging_skills(id),
                    learning_path_id INTEGER REFERENCES skill_learning_paths(id),
                    current_resource_id INTEGER REFERENCES educational_resources(id),
                    resources_completed TEXT DEFAULT '[]',  -- JSON array of completed resource IDs
                    questions_answered TEXT DEFAULT '{}',   -- JSON object of question responses
                    projects_completed TEXT DEFAULT '[]',   -- JSON array of completed projects
                    progress_percentage REAL DEFAULT 0.0,
                    time_spent_minutes INTEGER DEFAULT 0,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    learning_preferences TEXT DEFAULT '{}', -- JSON object of user preferences
                    FOREIGN KEY (skill_id) REFERENCES emerging_skills (id),
                    FOREIGN KEY (learning_path_id) REFERENCES skill_learning_paths (id),
                    FOREIGN KEY (current_resource_id) REFERENCES educational_resources (id)
                )
            ''')
            
            # Content Analysis Queue
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS content_analysis_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_id INTEGER REFERENCES educational_resources(id),
                    analysis_type TEXT DEFAULT 'full',  -- 'full'|'update'|'questions_only'|'projects_only'
                    priority INTEGER DEFAULT 1,         -- 1=high, 2=medium, 3=low
                    status TEXT DEFAULT 'pending',      -- 'pending'|'processing'|'completed'|'failed'
                    retry_count INTEGER DEFAULT 0,
                    error_message TEXT,
                    queued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_date TIMESTAMP,
                    completed_date TIMESTAMP,
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
            
            # Enhanced Learning Experience Indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_difficulty ON educational_resources(difficulty_level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_cost ON educational_resources(cost_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_sequence ON educational_resources(sequence_order)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_ai_analyzed ON educational_resources(ai_analysis_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_content_resource ON learning_content(resource_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_content_skill ON learning_content(skill_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_content_type ON learning_content(content_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_paths_skill ON skill_learning_paths(skill_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_sessions_session ON learning_sessions(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_learning_sessions_skill ON learning_sessions(skill_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_queue_status ON content_analysis_queue(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_analysis_queue_priority ON content_analysis_queue(priority)')
            
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

    # =============================================================================
    # ENHANCED LEARNING EXPERIENCE METHODS
    # =============================================================================
    
    def update_resource_analysis(self, resource_id: int, analysis_data: Dict[str, Any]) -> None:
        """Update resource with AI analysis results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert complex data to JSON
            learning_objectives = json.dumps(analysis_data.get('learning_objectives', []))
            content_extracted = json.dumps(analysis_data.get('content_extracted', {}))
            
            cursor.execute('''
                UPDATE educational_resources 
                SET difficulty_level = ?, cost_type = ?, estimated_duration = ?,
                    learning_objectives = ?, sequence_order = ?, ai_analysis_date = ?,
                    content_extracted = ?, source_platform = ?
                WHERE id = ?
            ''', (
                analysis_data.get('difficulty_level', 'unknown'),
                analysis_data.get('cost_type', 'unknown'),
                analysis_data.get('estimated_duration', 0),
                learning_objectives,
                analysis_data.get('sequence_order', 0),
                datetime.now().isoformat(),
                content_extracted,
                analysis_data.get('source_platform', ''),
                resource_id
            ))
            
            conn.commit()
            logger.info(f"Updated analysis for resource ID: {resource_id}")
    
    def add_learning_content(self, resource_id: int, skill_id: int, content_type: str, 
                            content_data: Dict[str, Any], ai_model: str = 'claude-3') -> int:
        """Add AI-generated learning content for a resource"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            content_json = json.dumps(content_data)
            
            cursor.execute('''
                INSERT INTO learning_content
                (resource_id, skill_id, content_type, content_data, ai_model_used)
                VALUES (?, ?, ?, ?, ?)
            ''', (resource_id, skill_id, content_type, content_json, ai_model))
            
            content_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Added {content_type} content for resource {resource_id}")
            return content_id
    
    def get_learning_content(self, resource_id: int, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get learning content for a resource"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if content_type:
                cursor.execute('''
                    SELECT * FROM learning_content 
                    WHERE resource_id = ? AND content_type = ?
                    ORDER BY ai_generated_date DESC
                ''', (resource_id, content_type))
            else:
                cursor.execute('''
                    SELECT * FROM learning_content 
                    WHERE resource_id = ?
                    ORDER BY content_type, ai_generated_date DESC
                ''', (resource_id,))
            
            rows = cursor.fetchall()
            content_list = []
            for row in rows:
                content = dict(row)
                content['content_data'] = json.loads(content['content_data'])
                content['admin_modified'] = json.loads(content['admin_modified'] or '{}')
                content_list.append(content)
            
            return content_list
    
    def create_learning_path(self, skill_id: int, path_name: str, resource_sequence: List[int],
                            path_data: Dict[str, Any]) -> int:
        """Create a learning path for a skill"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert complex data to JSON
            sequence_json = json.dumps(resource_sequence)
            prerequisites = json.dumps(path_data.get('prerequisites', []))
            milestones = json.dumps(path_data.get('learning_milestones', []))
            projects = json.dumps(path_data.get('completion_projects', []))
            difficulty_progression = json.dumps(path_data.get('difficulty_progression', {}))
            
            cursor.execute('''
                INSERT INTO skill_learning_paths
                (skill_id, path_name, path_description, resource_sequence, estimated_duration,
                 difficulty_progression, prerequisites, learning_milestones, completion_projects)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill_id,
                path_name,
                path_data.get('path_description', ''),
                sequence_json,
                path_data.get('estimated_duration', 0),
                difficulty_progression,
                prerequisites,
                milestones,
                projects
            ))
            
            path_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Created learning path '{path_name}' for skill {skill_id}")
            return path_id
    
    def get_learning_paths_for_skill(self, skill_id: int) -> List[Dict[str, Any]]:
        """Get all learning paths for a skill"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM skill_learning_paths 
                WHERE skill_id = ?
                ORDER BY 
                    CASE path_name 
                        WHEN 'beginner' THEN 1
                        WHEN 'intermediate' THEN 2
                        WHEN 'advanced' THEN 3
                        WHEN 'expert' THEN 4
                        ELSE 5
                    END
            ''', (skill_id,))
            
            rows = cursor.fetchall()
            paths = []
            for row in rows:
                path = dict(row)
                path['resource_sequence'] = json.loads(path['resource_sequence'])
                path['prerequisites'] = json.loads(path['prerequisites'] or '[]')
                path['learning_milestones'] = json.loads(path['learning_milestones'] or '[]')
                path['completion_projects'] = json.loads(path['completion_projects'] or '[]')
                path['difficulty_progression'] = json.loads(path['difficulty_progression'] or '{}')
                paths.append(path)
            
            return paths
    
    def get_enhanced_resources_for_skill(self, skill_id: int, difficulty_filter: Optional[str] = None,
                                        cost_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get enhanced resources for a skill with filtering options"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build dynamic query with filters
            where_conditions = ["srm.skill_id = ?"]
            params = [skill_id]
            
            if difficulty_filter:
                where_conditions.append("er.difficulty_level = ?")
                params.append(difficulty_filter)
            
            if cost_filter:
                where_conditions.append("er.cost_type = ?")
                params.append(cost_filter)
            
            where_clause = " AND ".join(where_conditions)
            
            cursor.execute(f'''
                SELECT er.*, srm.relevance_score, srm.resource_type_for_skill
                FROM educational_resources er
                JOIN skill_resource_mapping srm ON er.id = srm.resource_id
                WHERE {where_clause}
                ORDER BY 
                    er.sequence_order ASC,
                    CASE er.difficulty_level 
                        WHEN 'beginner' THEN 1
                        WHEN 'intermediate' THEN 2
                        WHEN 'advanced' THEN 3
                        WHEN 'expert' THEN 4
                        ELSE 5
                    END,
                    er.quality_score DESC
            ''', params)
            
            rows = cursor.fetchall()
            resources = []
            for row in rows:
                resource = dict(row)
                # Parse JSON fields
                resource['metadata'] = json.loads(resource['metadata'] or '{}')
                resource['prerequisites'] = json.loads(resource['prerequisites'] or '[]')
                resource['learning_outcomes'] = json.loads(resource['learning_outcomes'] or '[]')
                resource['learning_objectives'] = json.loads(resource['learning_objectives'] or '[]')
                resource['content_extracted'] = json.loads(resource['content_extracted'] or '{}')
                resource['keywords'] = [k.strip() for k in resource['keywords'].split(',') if k.strip()]
                
                # Get associated learning content
                resource['learning_content'] = self.get_learning_content(resource['id'])
                
                resources.append(resource)
            
            return resources
    
    def queue_content_analysis(self, resource_id: int, analysis_type: str = 'full', priority: int = 1) -> None:
        """Queue a resource for AI content analysis"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO content_analysis_queue
                (resource_id, analysis_type, priority, status)
                VALUES (?, ?, ?, 'pending')
            ''', (resource_id, analysis_type, priority))
            
            conn.commit()
            logger.info(f"Queued resource {resource_id} for {analysis_type} analysis")
    
    def get_analysis_queue(self, status: str = 'pending', limit: int = 10) -> List[Dict[str, Any]]:
        """Get resources queued for analysis"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT caq.*, er.title, er.url, er.resource_type
                FROM content_analysis_queue caq
                JOIN educational_resources er ON caq.resource_id = er.id
                WHERE caq.status = ?
                ORDER BY caq.priority ASC, caq.queued_date ASC
                LIMIT ?
            ''', (status, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def update_analysis_queue_status(self, queue_id: int, status: str, error_message: Optional[str] = None) -> None:
        """Update analysis queue item status"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if status == 'processing':
                cursor.execute('''
                    UPDATE content_analysis_queue 
                    SET status = ?, started_date = ?
                    WHERE id = ?
                ''', (status, datetime.now().isoformat(), queue_id))
            elif status == 'completed':
                cursor.execute('''
                    UPDATE content_analysis_queue 
                    SET status = ?, completed_date = ?
                    WHERE id = ?
                ''', (status, datetime.now().isoformat(), queue_id))
            elif status == 'failed':
                cursor.execute('''
                    UPDATE content_analysis_queue 
                    SET status = ?, error_message = ?, retry_count = retry_count + 1
                    WHERE id = ?
                ''', (status, error_message, queue_id))
            
            conn.commit()
    
    def create_learning_session(self, session_id: str, skill_id: int, learning_path_id: Optional[int] = None) -> int:
        """Create a new learning session for anonymous progress tracking"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO learning_sessions
                (session_id, skill_id, learning_path_id)
                VALUES (?, ?, ?)
            ''', (session_id, skill_id, learning_path_id))
            
            session_db_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Created learning session {session_id} for skill {skill_id}")
            return session_db_id
    
    def update_learning_progress(self, session_id: str, progress_data: Dict[str, Any]) -> None:
        """Update learning progress for a session"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Convert lists/dicts to JSON
            resources_completed = json.dumps(progress_data.get('resources_completed', []))
            questions_answered = json.dumps(progress_data.get('questions_answered', {}))
            projects_completed = json.dumps(progress_data.get('projects_completed', []))
            learning_preferences = json.dumps(progress_data.get('learning_preferences', {}))
            
            cursor.execute('''
                UPDATE learning_sessions 
                SET current_resource_id = ?, resources_completed = ?, questions_answered = ?,
                    projects_completed = ?, progress_percentage = ?, time_spent_minutes = ?,
                    last_activity = ?, learning_preferences = ?
                WHERE session_id = ?
            ''', (
                progress_data.get('current_resource_id'),
                resources_completed,
                questions_answered,
                projects_completed,
                progress_data.get('progress_percentage', 0.0),
                progress_data.get('time_spent_minutes', 0),
                datetime.now().isoformat(),
                learning_preferences,
                session_id
            ))
            
            conn.commit()
    
    def get_learning_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get learning session data"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM learning_sessions WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            if row:
                session = dict(row)
                session['resources_completed'] = json.loads(session['resources_completed'] or '[]')
                session['questions_answered'] = json.loads(session['questions_answered'] or '{}')
                session['projects_completed'] = json.loads(session['projects_completed'] or '[]')
                session['learning_preferences'] = json.loads(session['learning_preferences'] or '{}')
                return session
            
            return None

# Global database instance
db_manager = DatabaseManager() 