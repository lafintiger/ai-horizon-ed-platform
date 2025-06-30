"""
AI-Horizon Educational Resources System

A comprehensive platform for discovering, collecting, and recommending
educational resources (videos, articles, tools) for AI skills development.

Version: 1.0.0
Author: AI-Horizon Team
"""

__version__ = "1.0.0"
__title__ = "AI-Horizon Educational Resources"
__description__ = "Educational resource discovery and recommendation platform"

# Package-level imports
from .utils.config import Config
from .utils.database import DatabaseManager

__all__ = [
    'Config',
    'DatabaseManager',
] 