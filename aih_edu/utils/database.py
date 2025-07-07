"""
Database management for AI-Horizon Educational Resources System
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import os
from urllib.parse import urlparse

from .config import config

logger = logging.getLogger(__name__)

# Try to import PostgreSQL adapter
try:
    import psycopg2
    import psycopg2.extras
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

class DatabaseManager:
    """Database manager for educational resources system"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager"""
        if db_path is None:
            db_path = config.get('DATABASE_URL', 'sqlite:///data/aih_edu.db')
        
        self.db_url = db_path
        self.is_postgres = self._is_postgres_url(db_path)
        
        if self.is_postgres:
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL connections. Install with: pip install psycopg2-binary")
            self.db_config = self._parse_postgres_url(db_path)
        else:
            # SQLite setup
            if db_path.startswith('sqlite:///'):
                db_path = db_path[10:]
            self.db_path = db_path
            self._ensure_data_directory()
        
        self._initialize_database()
    
    def _is_postgres_url(self, url: str) -> bool:
        """Check if URL is for PostgreSQL"""
        return url.startswith(('postgres://', 'postgresql://'))
    
    def _parse_postgres_url(self, url: str) -> Dict[str, Any]:
        """Parse PostgreSQL URL into connection parameters"""
        parsed = urlparse(url)
        return {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'database': parsed.path[1:],  # Remove leading slash
            'user': parsed.username,
            'password': parsed.password
        }
    
    def _ensure_data_directory(self):
        """Ensure data directory exists (SQLite only)"""
        if not self.is_postgres:
            data_dir = Path(self.db_path).parent
            data_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_connection(self):
        """Get database connection"""
        if self.is_postgres:
            return psycopg2.connect(**self.db_config)
        else:
            return sqlite3.connect(self.db_path)
    
    def _initialize_database(self):
        """Initialize database with required tables and indexes"""
        
        # SQL for table creation - compatible with both SQLite and PostgreSQL
        create_tables_sql = """
            CREATE TABLE IF NOT EXISTS emerging_skills (
                id SERIAL PRIMARY KEY,
                skill_name VARCHAR(255) NOT NULL UNIQUE,
                category VARCHAR(100),
                urgency_score FLOAT,
                demand_trend VARCHAR(50),
                source_analysis TEXT,
                description TEXT,
                related_skills TEXT,
                keywords TEXT,
                job_market_data TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                discovery_status VARCHAR(50) DEFAULT 'pending'
            );
            
            CREATE TABLE IF NOT EXISTS educational_resources (
                id SERIAL PRIMARY KEY,
                title VARCHAR(500) NOT NULL,
                description TEXT,
                url VARCHAR(1000) NOT NULL,
                resource_type VARCHAR(100),
                cost_type VARCHAR(50),
                difficulty_level VARCHAR(50),
                estimated_duration VARCHAR(100),
                author VARCHAR(255),
                publication_date DATE,
                last_updated DATE,
                tags TEXT,
                skill_category VARCHAR(100),
                quality_score FLOAT,
                discovery_method VARCHAR(100),
                ai_analysis_score FLOAT,
                ai_analysis_details TEXT,
                ai_analysis_date TIMESTAMP,
                learning_level VARCHAR(50),
                sequence_order INTEGER,
                prerequisites TEXT,
                learning_objectives TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS skill_resources (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                relevance_score FLOAT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(skill_id, resource_id)
            );
        """
        
        # Additional tables for enhanced learning experience
        additional_tables_sql = """
            CREATE TABLE IF NOT EXISTS learning_content (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                content_type VARCHAR(50),
                content_data TEXT,
                difficulty_level VARCHAR(50),
                estimated_time_minutes INTEGER,
                sequence_order INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS skill_learning_paths (
                id SERIAL PRIMARY KEY,
                skill_id INTEGER REFERENCES emerging_skills(id) ON DELETE CASCADE,
                path_name VARCHAR(100),
                description TEXT,
                difficulty_level VARCHAR(50),
                estimated_total_hours INTEGER,
                sequence_order INTEGER,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS learning_sessions (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) UNIQUE,
                skill_id INTEGER REFERENCES emerging_skills(id),
                user_data TEXT,
                progress_data TEXT,
                started_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS content_analysis_queue (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                analysis_type VARCHAR(50),
                priority INTEGER DEFAULT 3,
                status VARCHAR(50) DEFAULT 'pending',
                queued_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_date TIMESTAMP,
                completed_date TIMESTAMP,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS resource_questions (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                questions_data TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS resource_exercises (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER REFERENCES educational_resources(id) ON DELETE CASCADE,
                exercises_data TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """
        
        if self.is_postgres:
            # PostgreSQL-specific initialization
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # Replace SERIAL with appropriate PostgreSQL syntax
                    postgres_sql = create_tables_sql.replace('SERIAL', 'SERIAL')
                    postgres_additional = additional_tables_sql.replace('SERIAL', 'SERIAL')
                    
                    cursor.execute(postgres_sql)
                    cursor.execute(postgres_additional)
                    
                    # Create indexes
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_resources_skill ON skill_resources(skill_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_resources_resource ON skill_resources(resource_id)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_quality ON educational_resources(quality_score)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_category ON educational_resources(skill_category)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_type ON educational_resources(resource_type)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_difficulty ON educational_resources(difficulty_level)')
                    cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_cost ON educational_resources(cost_type)')
                    
                conn.commit()
        else:
            # SQLite initialization
            sqlite_sql = create_tables_sql.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
            sqlite_sql = sqlite_sql.replace('TIMESTAMP', 'TEXT')
            sqlite_sql = sqlite_sql.replace('VARCHAR(255)', 'TEXT')
            sqlite_sql = sqlite_sql.replace('VARCHAR(100)', 'TEXT')
            sqlite_sql = sqlite_sql.replace('VARCHAR(500)', 'TEXT')
            sqlite_sql = sqlite_sql.replace('VARCHAR(1000)', 'TEXT')
            sqlite_sql = sqlite_sql.replace('VARCHAR(50)', 'TEXT')
            sqlite_sql = sqlite_sql.replace('FLOAT', 'REAL')
            sqlite_sql = sqlite_sql.replace('REFERENCES', 'REFERENCES')
            sqlite_sql = sqlite_sql.replace('ON DELETE CASCADE', '')
            
            sqlite_additional = additional_tables_sql.replace('SERIAL PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT')
            sqlite_additional = sqlite_additional.replace('TIMESTAMP', 'TEXT')
            sqlite_additional = sqlite_additional.replace('VARCHAR(255)', 'TEXT')
            sqlite_additional = sqlite_additional.replace('VARCHAR(100)', 'TEXT')
            sqlite_additional = sqlite_additional.replace('VARCHAR(50)', 'TEXT')
            sqlite_additional = sqlite_additional.replace('REFERENCES', 'REFERENCES')
            sqlite_additional = sqlite_additional.replace('ON DELETE CASCADE', '')
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executescript(sqlite_sql)
                cursor.executescript(sqlite_additional)
                
                # Create indexes for SQLite
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_resources_skill ON skill_resources(skill_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_skill_resources_resource ON skill_resources(resource_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_quality ON educational_resources(quality_score)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_category ON educational_resources(skill_category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_type ON educational_resources(resource_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_difficulty ON educational_resources(difficulty_level)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_resources_cost ON educational_resources(cost_type)')
                
                conn.commit()
        
        logger.info("Educational resources database initialized successfully")
    
    def add_resource(self, resource_data: Dict[str, Any]) -> Optional[int]:
        """Add a new educational resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO educational_resources 
                            (title, description, url, resource_type, cost_type, difficulty_level,
                             estimated_duration, author, tags, skill_category, quality_score,
                             discovery_method, learning_level, prerequisites, learning_objectives)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            resource_data['title'],
                            resource_data.get('description', ''),
                            resource_data['url'],
                            resource_data.get('resource_type', ''),
                            resource_data.get('cost_type', 'unknown'),
                            resource_data.get('difficulty_level', 'unknown'),
                            resource_data.get('estimated_duration', ''),
                            resource_data.get('author', ''),
                            resource_data.get('tags', ''),
                            resource_data.get('skill_category', ''),
                            resource_data.get('quality_score', 0.0),
                            resource_data.get('discovery_method', ''),
                            resource_data.get('learning_level', ''),
                            json.dumps(resource_data.get('prerequisites', [])),
                            json.dumps(resource_data.get('learning_objectives', []))
                        ))
                        resource_id = cursor.fetchone()[0]
                        conn.commit()
                        return resource_id
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO educational_resources 
                        (title, description, url, resource_type, cost_type, difficulty_level,
                         estimated_duration, author, tags, skill_category, quality_score,
                         discovery_method, learning_level, prerequisites, learning_objectives)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        resource_data['title'],
                        resource_data.get('description', ''),
                        resource_data['url'],
                        resource_data.get('resource_type', ''),
                        resource_data.get('cost_type', 'unknown'),
                        resource_data.get('difficulty_level', 'unknown'),
                        resource_data.get('estimated_duration', ''),
                        resource_data.get('author', ''),
                        resource_data.get('tags', ''),
                        resource_data.get('skill_category', ''),
                        resource_data.get('quality_score', 0.0),
                        resource_data.get('discovery_method', ''),
                        resource_data.get('learning_level', ''),
                        json.dumps(resource_data.get('prerequisites', [])),
                        json.dumps(resource_data.get('learning_objectives', []))
                    ))
                    resource_id = cursor.lastrowid
                    conn.commit()
                    return resource_id
                    
        except Exception as e:
            logger.error(f"Error adding resource: {e}")
            return None
    
    def search_resources(self, 
                        query: Optional[str] = None,
                        skill_category: Optional[str] = None,
                        learning_level: Optional[str] = None,
                        resource_type: Optional[str] = None,
                        min_quality: float = 0.0,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Search for educational resources"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        # Build query
                        where_conditions = ["quality_score >= %s"]
                        params = [min_quality]
                        
                        if query:
                            where_conditions.append("(title ILIKE %s OR description ILIKE %s OR keywords ILIKE %s)")
                            query_param = f"%{query}%"
                            params.extend([query_param, query_param, query_param])
                        
                        if skill_category:
                            where_conditions.append("skill_category = %s")
                            params.append(skill_category)
                        
                        if learning_level:
                            where_conditions.append("learning_level = %s")
                            params.append(learning_level)
                        
                        if resource_type:
                            where_conditions.append("resource_type = %s")
                            params.append(resource_type)
                        
                        where_clause = " AND ".join(where_conditions)
                        
                        sql = f'''
                            SELECT * FROM educational_resources 
                            WHERE {where_clause}
                            ORDER BY quality_score DESC, created_date DESC
                            LIMIT %s
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
                            resource['keywords'] = [k.strip() for k in (resource['keywords'] or '').split(',') if k.strip()]
                            resources.append(resource)
                        
                        return resources
                else:
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
                        ORDER BY quality_score DESC, created_date DESC
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
                        resource['keywords'] = [k.strip() for k in (resource['keywords'] or '').split(',') if k.strip()]
                        resources.append(resource)
                    
                    return resources
        except Exception as e:
            logger.error(f"Error searching resources: {e}")
            return []
    
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
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
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
                else:
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
        except Exception as e:
            logger.error(f"Error getting resource stats: {e}")
            return {
                'total_resources': 0,
                'by_category': {},
                'by_type': {},
                'average_quality': 0.0
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
        """Add a new emerging skill to the database"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO emerging_skills 
                            (skill_name, category, urgency_score, demand_trend, source_analysis, 
                             description, related_skills, keywords, job_market_data)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            RETURNING id
                        """, (
                            skill_data['skill_name'],
                            skill_data.get('category', ''),
                            skill_data.get('urgency_score', 0.0),
                            skill_data.get('demand_trend', 'stable'),
                            skill_data.get('source_analysis', ''),
                            skill_data.get('description', ''),
                            json.dumps(skill_data.get('related_skills', [])),
                            skill_data.get('keywords', ''),
                            json.dumps(skill_data.get('job_market_data', {}))
                        ))
                        skill_id = cursor.fetchone()[0]
                        conn.commit()
                        return skill_id
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO emerging_skills 
                        (skill_name, category, urgency_score, demand_trend, source_analysis, 
                         description, related_skills, keywords, job_market_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        skill_data['skill_name'],
                        skill_data.get('category', ''),
                        skill_data.get('urgency_score', 0.0),
                        skill_data.get('demand_trend', 'stable'),
                        skill_data.get('source_analysis', ''),
                        skill_data.get('description', ''),
                        json.dumps(skill_data.get('related_skills', [])),
                        skill_data.get('keywords', ''),
                        json.dumps(skill_data.get('job_market_data', {}))
                    ))
                    skill_id = cursor.lastrowid
                    conn.commit()
                    return skill_id
                    
        except Exception as e:
            logger.error(f"Error adding emerging skill: {e}")
            return None

    def get_emerging_skills(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get all emerging skills or limit to specific number"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        query = "SELECT * FROM emerging_skills ORDER BY urgency_score DESC"
                        if limit:
                            query += f" LIMIT {limit}"
                        cursor.execute(query)
                        rows = cursor.fetchall()
                        skills = []
                        for row in rows:
                            skill = dict(row)
                            skill['job_market_data'] = json.loads(skill['job_market_data'] or '{}')
                            skill['related_skills'] = json.loads(skill['related_skills'] or '[]')
                            skills.append(skill)
                        return skills
                else:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    query = "SELECT * FROM emerging_skills ORDER BY urgency_score DESC"
                    if limit:
                        query += f" LIMIT {limit}"
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    skills = []
                    for row in rows:
                        skill = dict(row)
                        skill['job_market_data'] = json.loads(skill['job_market_data'] or '{}')
                        skill['related_skills'] = json.loads(skill['related_skills'] or '[]')
                        skills.append(skill)
                    return skills
                    
        except Exception as e:
            logger.error(f"Error getting emerging skills: {e}")
            return []

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
    
    def link_skill_to_resource(self, skill_id: int, resource_id: int, relevance_score: float = 1.0) -> bool:
        """Link a skill to a resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO skill_resources (skill_id, resource_id, relevance_score)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (skill_id, resource_id) DO UPDATE SET
                            relevance_score = EXCLUDED.relevance_score
                        """, (skill_id, resource_id, relevance_score))
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO skill_resources (skill_id, resource_id, relevance_score)
                        VALUES (?, ?, ?)
                    """, (skill_id, resource_id, relevance_score))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error linking skill {skill_id} to resource {resource_id}: {e}")
            return False
    
    def get_resources_for_skill(self, skill_id: int) -> List[Dict[str, Any]]:
        """Get all resources linked to a specific skill"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT er.*, sr.relevance_score
                            FROM educational_resources er
                            JOIN skill_resources sr ON er.id = sr.resource_id
                            WHERE sr.skill_id = %s
                            ORDER BY sr.relevance_score DESC, er.quality_score DESC
                        """, (skill_id,))
                        return [dict(row) for row in cursor.fetchall()]
                else:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT er.*, sr.relevance_score
                        FROM educational_resources er
                        JOIN skill_resources sr ON er.id = sr.resource_id
                        WHERE sr.skill_id = ?
                        ORDER BY sr.relevance_score DESC, er.quality_score DESC
                    """, (skill_id,))
                    return [dict(row) for row in cursor.fetchall()]
                    
        except Exception as e:
            logger.error(f"Error getting resources for skill {skill_id}: {e}")
            return []

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
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        if content_type:
                            cursor.execute('''
                                SELECT * FROM learning_content 
                                WHERE resource_id = %s AND content_type = %s
                                ORDER BY created_date DESC
                            ''', (resource_id, content_type))
                        else:
                            cursor.execute('''
                                SELECT * FROM learning_content 
                                WHERE resource_id = %s
                                ORDER BY content_type, created_date DESC
                            ''', (resource_id,))
                        
                        rows = cursor.fetchall()
                else:
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
                    if 'admin_modified' in content:
                        content['admin_modified'] = json.loads(content['admin_modified'] or '{}')
                    content_list.append(content)
                
                return content_list
        except Exception as e:
            logger.error(f"Error getting learning content for resource {resource_id}: {e}")
            return []
    
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
                (skill_id, path_name, description, resource_sequence, estimated_duration,
                 difficulty_progression, prerequisites, learning_milestones, completion_projects)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill_id,
                path_name,
                path_data.get('description', ''),
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
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute('''
                            SELECT * FROM skill_learning_paths 
                            WHERE skill_id = %s
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
                else:
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
        except Exception as e:
            logger.error(f"Error getting learning paths for skill {skill_id}: {e}")
            return []
    
    def get_enhanced_resources_for_skill(self, skill_id: int, difficulty_filter: Optional[str] = None,
                                        cost_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get enhanced resources for a skill with filtering options"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        # Build dynamic query with filters
                        where_conditions = ["sr.skill_id = %s"]
                        params = [skill_id]
                        
                        if difficulty_filter:
                            where_conditions.append("er.difficulty_level = %s")
                            params.append(difficulty_filter)
                        
                        if cost_filter:
                            where_conditions.append("er.cost_type = %s")
                            params.append(cost_filter)
                        
                        where_clause = " AND ".join(where_conditions)
                        
                        cursor.execute(f'''
                            SELECT er.*, sr.relevance_score
                            FROM educational_resources er
                            JOIN skill_resources sr ON er.id = sr.resource_id
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
                else:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Build dynamic query with filters
                    where_conditions = ["sr.skill_id = ?"]
                    params = [skill_id]
                    
                    if difficulty_filter:
                        where_conditions.append("er.difficulty_level = ?")
                        params.append(difficulty_filter)
                    
                    if cost_filter:
                        where_conditions.append("er.cost_type = ?")
                        params.append(cost_filter)
                    
                    where_clause = " AND ".join(where_conditions)
                    
                    cursor.execute(f'''
                        SELECT er.*, sr.relevance_score
                        FROM educational_resources er
                        JOIN skill_resources sr ON er.id = sr.resource_id
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
                    resource['keywords'] = [k.strip() for k in (resource['keywords'] or '').split(',') if k.strip()]
                    
                    # Get associated learning content
                    resource['learning_content'] = self.get_learning_content(resource['id'])
                    
                    resources.append(resource)
                
                return resources
        except Exception as e:
            logger.error(f"Error getting enhanced resources for skill {skill_id}: {e}")
            return []
    
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
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute('''
                            SELECT * FROM learning_sessions WHERE session_id = %s
                        ''', (session_id,))
                        
                        row = cursor.fetchone()
                        if row:
                            session = dict(row)
                            session['resources_completed'] = json.loads(session['resources_completed'] or '[]')
                            session['questions_answered'] = json.loads(session['questions_answered'] or '{}')
                            session['projects_completed'] = json.loads(session['projects_completed'] or '[]')
                            session['learning_preferences'] = json.loads(session['learning_preferences'] or '{}')
                            return session
                else:
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
        except Exception as e:
            logger.error(f"Error getting learning session {session_id}: {e}")
            return None

    def update_resource_categorization(self, resource_id, cost_type, difficulty_level):
        """Update cost_type and difficulty_level for a resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            UPDATE educational_resources 
                            SET cost_type = %s, difficulty_level = %s
                            WHERE id = %s
                        """, (cost_type, difficulty_level, resource_id))
                        conn.commit()
                        return cursor.rowcount > 0
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE educational_resources 
                        SET cost_type = ?, difficulty_level = ?
                        WHERE id = ?
                    """, (cost_type, difficulty_level, resource_id))
                    conn.commit()
                    return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating resource categorization: {e}")
            return False
    
    def get_cost_distribution(self):
        """Get distribution of resources by cost type"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT cost_type, COUNT(*) 
                            FROM educational_resources 
                            GROUP BY cost_type
                        """)
                        return dict(cursor.fetchall())
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT cost_type, COUNT(*) 
                        FROM educational_resources 
                        GROUP BY cost_type
                    """)
                    return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error getting cost distribution: {e}")
            return {}
    
    def get_difficulty_distribution(self):
        """Get distribution of resources by difficulty level"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT difficulty_level, COUNT(*) 
                            FROM educational_resources 
                            GROUP BY difficulty_level
                        """)
                        return dict(cursor.fetchall())
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT difficulty_level, COUNT(*) 
                        FROM educational_resources 
                        GROUP BY difficulty_level
                    """)
                    return dict(cursor.fetchall())
        except Exception as e:
            logger.error(f"Error getting difficulty distribution: {e}")
            return {}

    def get_all_resources(self):
        """Get all educational resources"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT id, title, description, resource_type, cost_type, difficulty_level,
                                   url, quality_score, learning_level, author, estimated_duration, skill_category
                            FROM educational_resources
                            ORDER BY quality_score DESC
                        """)
                        return [dict(row) for row in cursor.fetchall()]
                else:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT id, title, description, resource_type, cost_type, difficulty_level,
                               url, quality_score, learning_level, author, estimated_duration, skill_category
                        FROM educational_resources
                        ORDER BY quality_score DESC
                    """)
                    columns = [desc[0] for desc in cursor.description]
                    resources = []
                    for row in cursor.fetchall():
                        resource = dict(zip(columns, row))
                        resources.append(resource)
                    return resources
        except Exception as e:
            logger.error(f"Error getting all resources: {e}")
            return []

    def get_all_skills(self):
        """Get all emerging skills from the database"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT * FROM emerging_skills 
                            ORDER BY skill_name ASC
                        """)
                        rows = cursor.fetchall()
                        skills = []
                        for row in rows:
                            skill = dict(row)
                            skill['job_market_data'] = json.loads(skill['job_market_data'] or '{}')
                            skill['related_skills'] = json.loads(skill['related_skills'] or '[]')
                            skills.append(skill)
                        return skills
                else:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT * FROM emerging_skills 
                        ORDER BY skill_name ASC
                    """)
                    rows = cursor.fetchall()
                    skills = []
                    for row in rows:
                        skill = dict(row)
                        skill['job_market_data'] = json.loads(skill['job_market_data'] or '{}')
                        skill['related_skills'] = json.loads(skill['related_skills'] or '[]')
                        skills.append(skill)
                    return skills
        except Exception as e:
            logger.error(f"Error getting all skills: {e}")
            return []

    def store_learning_content(self, resource_id, content_type, content_data):
        """Store learning content (questions, exercises) for a resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            INSERT INTO learning_content 
                            (resource_id, content_type, content_data, created_date)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (resource_id, content_type) DO UPDATE SET
                            content_data = EXCLUDED.content_data,
                            created_date = EXCLUDED.created_date
                        """, (resource_id, content_type, json.dumps(content_data), datetime.now()))
                        
                        conn.commit()
                        logger.info(f"Successfully stored {content_type} content for resource {resource_id}")
                        return True
                else:
                    cursor = conn.cursor()
                    
                    # Store in learning_content table - use correct column names
                    cursor.execute("""
                        INSERT OR REPLACE INTO learning_content 
                        (resource_id, content_type, content_data, ai_generated_date)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (resource_id, content_type, json.dumps(content_data)))
                    
                    conn.commit()
                    logger.info(f"Successfully stored {content_type} content for resource {resource_id}")
                    return True
                
        except Exception as e:
            logger.error(f"Error storing learning content for resource {resource_id}: {e}")
            raise

    def get_resource_questions(self, resource_id):
        """Get quiz questions for a specific resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT content_data 
                            FROM learning_content 
                            WHERE resource_id = %s AND content_type = %s
                        """, (resource_id, 'questions'))
                        
                        result = cursor.fetchone()
                        if result:
                            content_data = json.loads(result['content_data'])
                            
                            # Handle both formats: direct list or dict with 'questions' key
                            if isinstance(content_data, list):
                                questions = content_data
                            elif isinstance(content_data, dict):
                                questions = content_data.get('questions', [])
                            else:
                                return []
                        else:
                            return []
                else:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Get questions from learning_content table
                    cursor.execute("""
                        SELECT content_data 
                        FROM learning_content 
                        WHERE resource_id = ? AND content_type = 'questions'
                    """, (resource_id,))
                    
                    result = cursor.fetchone()
                    if result:
                        content_data = json.loads(result['content_data'])
                        
                        # Handle both formats: direct list or dict with 'questions' key
                        if isinstance(content_data, list):
                            questions = content_data
                        elif isinstance(content_data, dict):
                            questions = content_data.get('questions', [])
                        else:
                            return []
                    else:
                        return []
                
                # Normalize questions to ensure they're all dictionaries
                normalized_questions = []
                for i, question in enumerate(questions):
                    if isinstance(question, dict):
                        # Ensure required fields exist
                        normalized_question = {
                            'id': question.get('id', i + 1),
                            'question_text': question.get('question_text', question.get('question', '')),
                            'question_type': question.get('question_type', question.get('type', 'open_ended')),
                            'options': question.get('options', []),
                            'correct_answer': question.get('correct_answer', ''),
                            'explanation': question.get('explanation', 'No explanation provided'),
                            'difficulty': question.get('difficulty', 'medium')
                        }
                        normalized_questions.append(normalized_question)
                    elif isinstance(question, str):
                        # Convert string question to dictionary format
                        normalized_question = {
                            'id': i + 1,
                            'question_text': question,
                            'question_type': 'open_ended',
                            'options': [],
                            'correct_answer': '',
                            'explanation': 'No explanation provided',
                            'difficulty': 'medium'
                        }
                        normalized_questions.append(normalized_question)
                    else:
                        # Skip invalid question formats
                        logger.warning(f"Invalid question format for resource {resource_id}: {type(question)}")
                        continue
                
                return normalized_questions
                        
        except Exception as e:
            logger.error(f"Error getting questions for resource {resource_id}: {e}")
            return []

    def get_resource_exercises(self, resource_id):
        """Get practical exercises for a specific resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    conn.cursor_factory = psycopg2.extras.RealDictCursor
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT content_data 
                            FROM learning_content 
                            WHERE resource_id = %s AND content_type = %s
                        """, (resource_id, 'exercises'))
                        
                        result = cursor.fetchone()
                        if result:
                            content_data = json.loads(result['content_data'])
                            
                            # Handle both formats: direct list or dict with 'exercises' key
                            if isinstance(content_data, list):
                                return content_data
                            elif isinstance(content_data, dict):
                                return content_data.get('exercises', [])
                            else:
                                return []
                        else:
                            return []
                else:
                    conn.row_factory = sqlite3.Row
                    cursor = conn.cursor()
                    
                    # Get exercises from learning_content table
                    cursor.execute("""
                        SELECT content_data 
                        FROM learning_content 
                        WHERE resource_id = ? AND content_type = 'exercises'
                    """, (resource_id,))
                    
                    result = cursor.fetchone()
                    if result:
                        content_data = json.loads(result['content_data'])
                        
                        # Handle both formats: direct list or dict with 'exercises' key
                        if isinstance(content_data, list):
                            return content_data
                        elif isinstance(content_data, dict):
                            return content_data.get('exercises', [])
                        else:
                            return []
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting exercises for resource {resource_id}: {e}")
            return []

    def store_resource_questions(self, resource_id, questions):
        """Store quiz questions for a resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        # Store questions in learning_content table
                        content_data = {
                            'questions': questions,
                            'generated_at': datetime.now().isoformat()
                        }
                        
                        cursor.execute("""
                            INSERT INTO learning_content 
                            (resource_id, content_type, content_data, created_date)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (resource_id, content_type) DO UPDATE SET
                            content_data = EXCLUDED.content_data,
                            created_date = EXCLUDED.created_date
                        """, (
                            resource_id,
                            'questions',
                            json.dumps(content_data),
                            datetime.now()
                        ))
                        
                        conn.commit()
                        return True
                else:
                    cursor = conn.cursor()
                    
                    # Store questions in learning_content table
                    content_data = {
                        'questions': questions,
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO learning_content 
                        (resource_id, content_type, content_data, ai_generated_date)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        resource_id,
                        'questions',
                        json.dumps(content_data)
                    ))
                    
                    conn.commit()
                    return True
                
        except Exception as e:
            logger.error(f"Error storing questions for resource {resource_id}: {e}")
            return False

    def store_resource_exercises(self, resource_id, exercises):
        """Store practical exercises for a resource"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        # Store exercises in learning_content table
                        content_data = {
                            'exercises': exercises,
                            'generated_at': datetime.now().isoformat()
                        }
                        
                        cursor.execute("""
                            INSERT INTO learning_content 
                            (resource_id, content_type, content_data, created_date)
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (resource_id, content_type) DO UPDATE SET
                            content_data = EXCLUDED.content_data,
                            created_date = EXCLUDED.created_date
                        """, (
                            resource_id,
                            'exercises',
                            json.dumps(content_data),
                            datetime.now()
                        ))
                        
                        conn.commit()
                        return True
                else:
                    cursor = conn.cursor()
                    
                    # Store exercises in learning_content table
                    content_data = {
                        'exercises': exercises,
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO learning_content 
                        (resource_id, content_type, content_data, ai_generated_date)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        resource_id,
                        'exercises',
                        json.dumps(content_data)
                    ))
                    
                    conn.commit()
                    return True
                
        except Exception as e:
            logger.error(f"Error storing exercises for resource {resource_id}: {e}")
            return False

    def store_quiz_attempt(self, resource_id, answers, score_percentage):
        """Store a quiz attempt"""
        try:
            with self._get_connection() as conn:
                if self.is_postgres:
                    with conn.cursor() as cursor:
                        # Store the attempt
                        cursor.execute("""
                            INSERT INTO quiz_attempts (resource_id, answers, score_percentage, created_at)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            resource_id,
                            json.dumps(answers),
                            score_percentage,
                            datetime.now()
                        ))
                        
                        conn.commit()
                        return True
                else:
                    cursor = conn.cursor()
                    
                    # Create quiz_attempts table if it doesn't exist
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS quiz_attempts (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            resource_id INTEGER,
                            answers TEXT,
                            score_percentage REAL,
                            created_at TEXT,
                            FOREIGN KEY (resource_id) REFERENCES educational_resources (id)
                        )
                    """)
                    
                    # Store the attempt
                    cursor.execute("""
                        INSERT INTO quiz_attempts (resource_id, answers, score_percentage, created_at)
                        VALUES (?, ?, ?, ?)
                    """, (
                        resource_id,
                        json.dumps(answers),
                        score_percentage,
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    return True
                
        except Exception as e:
            logger.error(f"Error storing quiz attempt for resource {resource_id}: {e}")
            return False

# Note: Global database instance removed - use the instance from app.py instead 