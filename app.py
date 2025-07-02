#!/usr/bin/env python3

import os
import sys
import json
import logging
from datetime import datetime

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, abort
from flask_cors import CORS
import sqlite3

# Import our modules
from utils.database import DatabaseManager
from utils.config import config
from utils.learning_experience_service import LearningExperienceService

# Auto-restore database if empty (for Heroku deployments)
def auto_restore_database_if_empty():
    """Auto-restore database if it's empty (for Heroku ephemeral filesystem)"""
    try:
        db_manager = DatabaseManager()
        skills = db_manager.get_emerging_skills()
        
        if len(skills) == 0:
            print("🚨 EMPTY DATABASE DETECTED - Auto-restoring...")
            
            # Import the restore function
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from heroku_database_restore import main as restore_main
            
            # Run the restoration
            restore_main()
            print("✅ Auto-restore completed!")
            
    except Exception as e:
        print(f"❌ Auto-restore failed: {e}")

# ... existing code ... 