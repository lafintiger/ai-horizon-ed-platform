#!/usr/bin/env python3
"""
Export quiz data from local SQLite database for PostgreSQL migration
"""

import sqlite3
import json
from datetime import datetime
import os

def export_quiz_data():
    """Export all learning content (quiz data) from SQLite database"""
    
    # Try different possible database paths - prioritize the one with actual data
    possible_paths = [
        "aih_edu/data/aih_edu.db",  # This one has the quiz data
        "./aih_edu/data/aih_edu.db",
        "../aih_edu/data/aih_edu.db",
        "data/aih_edu.db"  # This one is empty, check last
    ]
    
    db_path = None
    for path in possible_paths:
        if os.path.exists(path):
            # Test if this database has quiz data
            try:
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM learning_content WHERE content_type = "questions"')
                count = cursor.fetchone()[0]
                conn.close()
                
                print(f"🔍 Checking {path}: {count} quiz entries")
                
                if count > 0:
                    db_path = path
                    break
                elif db_path is None:  # Keep as fallback if no better option
                    db_path = path
            except:
                continue
    
    if not db_path:
        print(f"❌ Database not found in any of these locations:")
        for path in possible_paths:
            print(f"   {path}")
        return None
    
    print(f"📚 Using database: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Export learning_content table (where quiz questions are stored)
        cursor.execute("""
            SELECT id, resource_id, skill_id, content_type, content_data, 
                   ai_model_used, ai_generated_date, admin_approved, admin_modified,
                   quality_score, usage_count, feedback_rating
            FROM learning_content
            WHERE content_type = 'questions'
            ORDER BY resource_id
        """)
        
        learning_content = []
        rows = cursor.fetchall()
        
        print(f"📊 Found {len(rows)} quiz entries")
        
        for row in rows:
            learning_content.append({
                'id': row['id'],
                'resource_id': row['resource_id'],
                'skill_id': row['skill_id'],
                'content_type': row['content_type'],
                'content_data': row['content_data'],
                'ai_model_used': row['ai_model_used'],
                'ai_generated_date': row['ai_generated_date'],
                'admin_approved': row['admin_approved'],
                'admin_modified': row['admin_modified'],
                'quality_score': row['quality_score'],
                'usage_count': row['usage_count'],
                'feedback_rating': row['feedback_rating']
            })
        
        # Also export other learning content types if they exist
        cursor.execute("""
            SELECT id, resource_id, skill_id, content_type, content_data,
                   ai_model_used, ai_generated_date, admin_approved, admin_modified,
                   quality_score, usage_count, feedback_rating
            FROM learning_content
            WHERE content_type != 'questions'
            ORDER BY resource_id, content_type
        """)
        
        other_content = []
        other_rows = cursor.fetchall()
        
        for row in other_rows:
            other_content.append({
                'id': row['id'],
                'resource_id': row['resource_id'],
                'skill_id': row['skill_id'],
                'content_type': row['content_type'],
                'content_data': row['content_data'],
                'ai_model_used': row['ai_model_used'],
                'ai_generated_date': row['ai_generated_date'],
                'admin_approved': row['admin_approved'],
                'admin_modified': row['admin_modified'],
                'quality_score': row['quality_score'],
                'usage_count': row['usage_count'],
                'feedback_rating': row['feedback_rating']
            })
        
        # Export quiz attempts if they exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='quiz_attempts'
        """)
        
        quiz_attempts = []
        if cursor.fetchone():
            cursor.execute("""
                SELECT id, resource_id, answers, score_percentage, created_at
                FROM quiz_attempts
                ORDER BY created_at
            """)
            
            attempt_rows = cursor.fetchall()
            for row in attempt_rows:
                quiz_attempts.append({
                    'id': row['id'],
                    'resource_id': row['resource_id'],
                    'answers': row['answers'],
                    'score_percentage': row['score_percentage'],
                    'created_at': row['created_at']
                })
        
        conn.close()
        
        # Create export data structure
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'export_type': 'quiz_data_migration',
            'source_database': 'sqlite',
            'source_path': db_path,
            'target_database': 'postgresql',
            'learning_content_questions': learning_content,
            'learning_content_other': other_content,
            'quiz_attempts': quiz_attempts,
            'statistics': {
                'total_quiz_questions': len(learning_content),
                'total_other_content': len(other_content),
                'total_quiz_attempts': len(quiz_attempts),
                'unique_resources_with_quizzes': len(set(item['resource_id'] for item in learning_content))
            }
        }
        
        # Save to JSON file
        export_filename = 'quiz_data_export.json'
        with open(export_filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"✅ Quiz data exported to {export_filename}")
        print(f"📊 Statistics:")
        print(f"   • Quiz questions: {export_data['statistics']['total_quiz_questions']}")
        print(f"   • Other learning content: {export_data['statistics']['total_other_content']}")
        print(f"   • Quiz attempts: {export_data['statistics']['total_quiz_attempts']}")
        print(f"   • Resources with quizzes: {export_data['statistics']['unique_resources_with_quizzes']}")
        
        # Show sample quiz data
        if learning_content:
            sample = learning_content[0]
            try:
                sample_questions = json.loads(sample['content_data'])
                if isinstance(sample_questions, dict) and 'questions' in sample_questions:
                    sample_questions = sample_questions['questions']
                print(f"   • Sample quiz (Resource {sample['resource_id']}): {len(sample_questions) if isinstance(sample_questions, list) else 0} questions")
                if isinstance(sample_questions, list) and len(sample_questions) > 0:
                    first_q = sample_questions[0]
                    question_text = first_q.get('question_text', first_q.get('question', 'Unknown'))
                    print(f"     First question: {question_text[:80]}...")
            except:
                print(f"     Raw data preview: {sample['content_data'][:100]}...")
        
        return export_data
        
    except Exception as e:
        print(f"❌ Error exporting quiz data: {e}")
        return None

if __name__ == "__main__":
    export_quiz_data() 