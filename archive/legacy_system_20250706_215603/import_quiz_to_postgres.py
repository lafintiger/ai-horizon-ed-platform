#!/usr/bin/env python3
"""
Import quiz data from JSON export into PostgreSQL database on Heroku
"""

import psycopg2
import json
import os
from datetime import datetime

def import_quiz_data():
    """Import quiz data from JSON export into PostgreSQL"""
    
    # Load the exported quiz data
    export_filename = 'quiz_data_export.json'
    if not os.path.exists(export_filename):
        print(f"❌ Export file not found: {export_filename}")
        print("Run export_quiz_data.py first!")
        return False
    
    print(f"📖 Loading quiz data from {export_filename}")
    
    with open(export_filename, 'r') as f:
        data = json.load(f)
    
    # Get PostgreSQL connection string
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("Set it with: export DATABASE_URL='postgres://...'")
        return False
    
    print(f"🗄️  Connecting to PostgreSQL...")
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check the actual schema of learning_content table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = %s
            ORDER BY ordinal_position
        """, ('learning_content',))
        
        columns = cursor.fetchall()
        print(f"📋 PostgreSQL learning_content table schema:")
        for col in columns:
            print(f"   • {col[0]} ({col[1]})")
        
        if not columns:
            print("❌ learning_content table does not exist in PostgreSQL database")
            return False
        
        print(f"📊 Import statistics:")
        print(f"   • Quiz questions to import: {len(data['learning_content_questions'])}")
        print(f"   • Other learning content: {len(data['learning_content_other'])}")
        print(f"   • Quiz attempts: {len(data['quiz_attempts'])}")
        
        # Import quiz questions using only the columns that exist in PostgreSQL
        imported_questions = 0
        skipped_questions = 0
        
        for item in data['learning_content_questions']:
            try:
                # Check if this resource already has quiz questions
                cursor.execute("""
                    SELECT COUNT(*) FROM learning_content 
                    WHERE resource_id = %s AND content_type = %s
                """, (item['resource_id'], 'questions'))
                
                existing_count = cursor.fetchone()[0]
                
                if existing_count > 0:
                    print(f"⚠️  Resource {item['resource_id']} already has {existing_count} quiz questions, skipping")
                    skipped_questions += 1
                    continue
                
                # Insert quiz data using only the columns that exist in PostgreSQL
                cursor.execute("""
                    INSERT INTO learning_content 
                    (resource_id, skill_id, content_type, content_data, 
                     difficulty_level, estimated_time_minutes, sequence_order, created_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item['resource_id'],
                    item['skill_id'],
                    item['content_type'],
                    item['content_data'],
                    'medium',  # Default difficulty level
                    10,        # Default estimated time
                    1,         # Default sequence order
                    datetime.now()  # Current timestamp
                ))
                
                imported_questions += 1
                
                if imported_questions % 10 == 0:
                    print(f"   📝 Imported {imported_questions} quiz questions...")
                
            except Exception as e:
                print(f"❌ Error importing quiz for resource {item['resource_id']}: {e}")
        
        # Import other learning content
        imported_other = 0
        for item in data['learning_content_other']:
            try:
                cursor.execute("""
                    INSERT INTO learning_content 
                    (resource_id, skill_id, content_type, content_data,
                     difficulty_level, estimated_time_minutes, sequence_order, created_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    item['resource_id'],
                    item['skill_id'],
                    item['content_type'],
                    item['content_data'],
                    'medium',  # Default difficulty level
                    15,        # Default estimated time for other content
                    2,         # Default sequence order
                    datetime.now()  # Current timestamp
                ))
                
                imported_other += 1
                
            except Exception as e:
                print(f"❌ Error importing other content for resource {item['resource_id']}: {e}")
        
        # Import quiz attempts if there are any
        imported_attempts = 0
        if data['quiz_attempts']:
            # Check if quiz_attempts table exists
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = %s
            """, ('quiz_attempts',))
            
            if cursor.fetchone()[0] == 0:
                # Create quiz_attempts table
                cursor.execute("""
                    CREATE TABLE quiz_attempts (
                        id SERIAL PRIMARY KEY,
                        resource_id INTEGER,
                        answers TEXT,
                        score_percentage REAL,
                        created_at TIMESTAMP
                    )
                """)
                print("✅ Created quiz_attempts table")
            
            for attempt in data['quiz_attempts']:
                try:
                    cursor.execute("""
                        INSERT INTO quiz_attempts 
                        (resource_id, answers, score_percentage, created_at)
                        VALUES (%s, %s, %s, %s)
                    """, (
                        attempt['resource_id'],
                        attempt['answers'],
                        attempt['score_percentage'],
                        attempt['created_at']
                    ))
                    
                    imported_attempts += 1
                    
                except Exception as e:
                    print(f"❌ Error importing quiz attempt: {e}")
        
        # Commit all changes
        conn.commit()
        
        print(f"✅ Quiz data import completed!")
        print(f"📊 Final results:")
        print(f"   • Quiz questions imported: {imported_questions}")
        print(f"   • Quiz questions skipped: {skipped_questions}")
        print(f"   • Other learning content imported: {imported_other}")
        print(f"   • Quiz attempts imported: {imported_attempts}")
        
        # Verify the import
        cursor.execute("SELECT COUNT(*) FROM learning_content WHERE content_type = %s", ('questions',))
        total_questions = cursor.fetchone()[0]
        print(f"   • Total quiz questions in database: {total_questions}")
        
        # Show sample quiz resources
        cursor.execute("""
            SELECT DISTINCT resource_id FROM learning_content 
            WHERE content_type = %s
            ORDER BY resource_id 
            LIMIT 10
        """, ('questions',))
        sample_resources = [row[0] for row in cursor.fetchall()]
        print(f"   • Sample resources with quizzes: {sample_resources}")
        
        # Show a sample quiz question
        if sample_resources:
            cursor.execute("""
                SELECT content_data FROM learning_content 
                WHERE resource_id = %s AND content_type = %s
                LIMIT 1
            """, (sample_resources[0], 'questions'))
            
            sample_data = cursor.fetchone()
            if sample_data:
                try:
                    quiz_data = json.loads(sample_data[0])
                    if isinstance(quiz_data, dict) and 'questions' in quiz_data:
                        questions = quiz_data['questions']
                        print(f"   • Sample quiz has {len(questions)} questions")
                        if questions:
                            first_q = questions[0]
                            question_text = first_q.get('question_text', first_q.get('question', 'Unknown'))
                            print(f"     First question: {question_text[:80]}...")
                except:
                    print(f"   • Sample quiz data: {sample_data[0][:100]}...")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error importing quiz data: {e}")
        return False

if __name__ == "__main__":
    import_quiz_data() 