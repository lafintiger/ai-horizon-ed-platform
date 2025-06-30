"""
Configuration management for AI-Horizon Educational Resources System
"""

import os
from typing import Dict, Any, Optional

class Config:
    """Configuration manager for educational resources system"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables and defaults"""
        return {
            # Database Configuration
            'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///data/aih_edu.db'),
            'DATABASE_POOL_SIZE': int(os.getenv('DATABASE_POOL_SIZE', '10')),
            
            # API Keys
            'PERPLEXITY_API_KEY': os.getenv('PERPLEXITY_API_KEY'),
            'YOUTUBE_API_KEY': os.getenv('YOUTUBE_API_KEY'),
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            
            # Search Configuration
            'MAX_SEARCH_RESULTS': int(os.getenv('MAX_SEARCH_RESULTS', '50')),
            'SEARCH_TIMEOUT': int(os.getenv('SEARCH_TIMEOUT', '30')),
            'MIN_CONTENT_QUALITY': float(os.getenv('MIN_CONTENT_QUALITY', '0.7')),
            
            # Resource Types
            'SUPPORTED_RESOURCE_TYPES': [
                'youtube_video',
                'online_course',
                'tutorial',
                'documentation',
                'book',
                'article',
                'tool',
                'dataset',
                'coding_example'
            ],
            
            # Learning Levels
            'LEARNING_LEVELS': [
                'beginner',
                'intermediate', 
                'advanced',
                'expert'
            ],
            
            # AI Skill Categories
            'AI_SKILL_CATEGORIES': [
                'machine_learning',
                'deep_learning',
                'natural_language_processing',
                'computer_vision',
                'data_science',
                'cybersecurity_ai',
                'robotics',
                'ai_ethics',
                'cloud_ai',
                'ai_tools'
            ],
            
            # Rate Limiting
            'RATE_LIMIT_REQUESTS': int(os.getenv('RATE_LIMIT_REQUESTS', '100')),
            'RATE_LIMIT_WINDOW': int(os.getenv('RATE_LIMIT_WINDOW', '3600')),
            
            # Logging
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'LOG_FILE': os.getenv('LOG_FILE', 'logs/aih_edu.log'),
            
            # Flask Configuration
            'SECRET_KEY': os.getenv('SECRET_KEY', 'edu-dev-key-change-in-production'),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
            'PORT': int(os.getenv('PORT', '9000')),
            
            # Content Filtering
            'CONTENT_FILTERS': {
                'min_duration_seconds': 300,  # 5 minutes minimum for videos
                'max_duration_seconds': 7200,  # 2 hours maximum for videos
                'required_languages': ['en'],
                'exclude_keywords': ['spam', 'clickbait', 'scam']
            },
            
            # Recommendation Engine
            'RECOMMENDATION_CONFIG': {
                'similarity_threshold': 0.8,
                'max_recommendations': 20,
                'diversity_factor': 0.3,
                'freshness_weight': 0.2
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.config[key] = value
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for specific service"""
        key_map = {
            'perplexity': 'PERPLEXITY_API_KEY',
            'youtube': 'YOUTUBE_API_KEY', 
            'openai': 'OPENAI_API_KEY',
            'anthropic': 'ANTHROPIC_API_KEY'
        }
        
        if service.lower() in key_map:
            return self.get(key_map[service.lower()])
        return None
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.get('FLASK_ENV') == 'development'
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'url': self.get('DATABASE_URL'),
            'pool_size': self.get('DATABASE_POOL_SIZE')
        }

# Global configuration instance
config = Config() 