#!/usr/bin/env python3
"""
Direct Heroku Database Population
Export from local SQLite and populate Heroku PostgreSQL
"""

import os
import sqlite3
import psycopg2
from urllib.parse import urlparse

def export_and_populate():
    """Export from local SQLite and populate Heroku PostgreSQL"""
    print("🔄 Starting direct database population...")
    
    # Connect to local SQLite
    local_conn = sqlite3.connect('data/aih_edu.db')
    local_conn.row_factory = sqlite3.Row
    local_cursor = local_conn.cursor()
    
    # Connect to Heroku PostgreSQL
    database_url = "postgres://uf5qefmntlip35:pe63f542ab611c5eff9d740e528aeed2b82f8626d2e680b56eb6dff1942a8ddea@c2hbg00ac72j9d.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d7fb1t5acffq6j"
    parsed = urlparse(database_url)
    
    heroku_conn = psycopg2.connect(
        host=parsed.hostname,
        database=parsed.path[1:],
        user=parsed.username,
        password=parsed.password,
        port=parsed.port
    )
    heroku_cursor = heroku_conn.cursor()
    
    try:
        # Drop and recreate tables with proper field sizes
        print("🏗️ Recreating Heroku tables...")
        
        heroku_cursor.execute("DROP TABLE IF EXISTS resource_questions CASCADE")
        heroku_cursor.execute("DROP TABLE IF EXISTS resource_exercises CASCADE") 
        heroku_cursor.execute("DROP TABLE IF EXISTS skill_resources CASCADE")
        heroku_cursor.execute("DROP TABLE IF EXISTS resources CASCADE")
        heroku_cursor.execute("DROP TABLE IF EXISTS skills CASCADE")
        
        heroku_cursor.execute("""
            CREATE TABLE skills (
                id SERIAL PRIMARY KEY,
                skill_name TEXT UNIQUE NOT NULL,
                description TEXT,
                category TEXT,
                keywords TEXT,
                emerging_trend BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        heroku_cursor.execute("""
            CREATE TABLE resources (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT UNIQUE,
                description TEXT,
                resource_type TEXT,
                difficulty_level TEXT,
                estimated_time INTEGER,
                cost DECIMAL(10,2),
                keywords TEXT,
                source_platform TEXT,
                rating DECIMAL(3,2),
                publication_date DATE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_format TEXT,
                author TEXT,
                prerequisites TEXT,
                learning_objectives TEXT,
                tags TEXT,
                engagement_metrics TEXT,
                quality_score DECIMAL(3,2),
                verification_status TEXT,
                ai_analysis_complete BOOLEAN DEFAULT FALSE
            )
        """)
        
        heroku_cursor.execute("""
            CREATE TABLE skill_resources (
                skill_id INTEGER,
                resource_id INTEGER,
                relevance_score DECIMAL(3,2) DEFAULT 0.5,
                PRIMARY KEY (skill_id, resource_id)
            )
        """)
        
        heroku_cursor.execute("""
            CREATE TABLE resource_questions (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER,
                question_text TEXT,
                correct_answer TEXT,
                wrong_answers TEXT,
                explanation TEXT,
                difficulty TEXT
            )
        """)
        
        heroku_cursor.execute("""
            CREATE TABLE resource_exercises (
                id SERIAL PRIMARY KEY,
                resource_id INTEGER,
                exercise_text TEXT,
                exercise_type TEXT,
                expected_outcome TEXT,
                difficulty TEXT
            )
        """)
        
        # Export and insert skills
        print("📝 Exporting skills...")
        local_cursor.execute("SELECT * FROM emerging_skills")
        skills = local_cursor.fetchall()
        
        for skill in skills:
            heroku_cursor.execute("""
                INSERT INTO skills (skill_name, description, category, keywords, emerging_trend)
                VALUES (%s, %s, %s, %s, %s) RETURNING id
            """, (
                skill['skill_name'],
                skill['description'] if 'description' in skill.keys() else '',
                skill['category'] if 'category' in skill.keys() else '',
                skill['keywords'] if 'keywords' in skill.keys() else '',
                skill['emerging_trend'] if 'emerging_trend' in skill.keys() else False
            ))
            skill_id = heroku_cursor.fetchone()[0]
            print(f"   ✅ {skill['skill_name']} (ID: {skill_id})")
        
        # Export and insert resources
        print("📚 Exporting resources...")
        local_cursor.execute("SELECT * FROM educational_resources")
        resources = local_cursor.fetchall()
        
        resource_mapping = {}
        for resource in resources:
            heroku_cursor.execute("""
                INSERT INTO resources (title, url, description, resource_type, difficulty_level,
                                     estimated_time, cost, keywords, source_platform, rating,
                                     content_format, author, ai_analysis_complete)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                resource['title'],
                resource['url'],
                resource['description'] if 'description' in resource.keys() else '',
                resource['resource_type'] if 'resource_type' in resource.keys() else '',
                resource['difficulty_level'] if 'difficulty_level' in resource.keys() else '',
                resource['estimated_time'] if 'estimated_time' in resource.keys() else 0,
                resource['cost'] if 'cost' in resource.keys() else 0,
                resource['keywords'] if 'keywords' in resource.keys() else '',
                resource['source_platform'] if 'source_platform' in resource.keys() else '',
                resource['rating'] if 'rating' in resource.keys() else 0,
                resource['content_format'] if 'content_format' in resource.keys() else '',
                resource['author'] if 'author' in resource.keys() else '',
                resource['ai_analysis_complete'] if 'ai_analysis_complete' in resource.keys() else False
            ))
            new_id = heroku_cursor.fetchone()[0]
            resource_mapping[resource['id']] = new_id
            print(f"   ✅ {resource['title'][:50]}... (ID: {new_id})")
        
        # Export skill-resource relationships
        print("🔗 Exporting skill-resource relationships...")
        local_cursor.execute("SELECT * FROM skill_resource_mapping")
        mappings = local_cursor.fetchall()
        
        for mapping in mappings:
            if mapping['resource_id'] in resource_mapping:
                heroku_cursor.execute("""
                    INSERT INTO skill_resources (skill_id, resource_id, relevance_score)
                    VALUES (%s, %s, %s)
                """, (
                    mapping['skill_id'],
                    resource_mapping[mapping['resource_id']],
                    mapping['relevance_score'] if 'relevance_score' in mapping.keys() else 0.5
                ))
        
        # Export learning content (questions and exercises)
        print("💡 Exporting learning content...")
        local_cursor.execute("SELECT * FROM learning_content")
        content = local_cursor.fetchall()
        
        for item in content:
            if item['resource_id'] in resource_mapping:
                new_resource_id = resource_mapping[item['resource_id']]
                
                # Insert questions
                questions_text = item['questions'] if 'questions' in item.keys() else '[]'
                try:
                    questions = eval(questions_text) if questions_text else []
                    for q in questions:
                        heroku_cursor.execute("""
                            INSERT INTO resource_questions (resource_id, question_text, correct_answer, 
                                                           wrong_answers, explanation, difficulty)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            new_resource_id,
                            q.get('question', '') if hasattr(q, 'get') else str(q),
                            q.get('correct_answer', '') if hasattr(q, 'get') else '',
                            str(q.get('wrong_answers', [])) if hasattr(q, 'get') else '[]',
                            q.get('explanation', '') if hasattr(q, 'get') else '',
                            q.get('difficulty', 'medium') if hasattr(q, 'get') else 'medium'
                        ))
                except:
                    pass  # Skip invalid question data
                
                # Insert exercises
                exercises_text = item['exercises'] if 'exercises' in item.keys() else '[]'
                try:
                    exercises = eval(exercises_text) if exercises_text else []
                    for e in exercises:
                        heroku_cursor.execute("""
                            INSERT INTO resource_exercises (resource_id, exercise_text, exercise_type,
                                                           expected_outcome, difficulty)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            new_resource_id,
                            e.get('text', '') if hasattr(e, 'get') else str(e),
                            e.get('type', 'practical') if hasattr(e, 'get') else 'practical',
                            e.get('expected_outcome', '') if hasattr(e, 'get') else '',
                            e.get('difficulty', 'medium') if hasattr(e, 'get') else 'medium'
                        ))
                except:
                    pass  # Skip invalid exercise data
        
        # Commit all changes
        heroku_conn.commit()
        
        # Final verification
        heroku_cursor.execute("SELECT COUNT(*) FROM resources")
        resource_count = heroku_cursor.fetchone()[0]
        
        heroku_cursor.execute("SELECT COUNT(*) FROM skills")
        skill_count = heroku_cursor.fetchone()[0]
        
        heroku_cursor.execute("SELECT COUNT(*) FROM resource_questions")
        question_count = heroku_cursor.fetchone()[0]
        
        heroku_cursor.execute("SELECT COUNT(*) FROM resource_exercises")
        exercise_count = heroku_cursor.fetchone()[0]
        
        print(f"\n✅ HEROKU DATABASE POPULATION COMPLETE!")
        print(f"📊 Final counts:")
        print(f"   Skills: {skill_count}")
        print(f"   Resources: {resource_count}")
        print(f"   Questions: {question_count}")
        print(f"   Exercises: {exercise_count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        heroku_conn.rollback()
        raise
    finally:
        local_cursor.close()
        local_conn.close()
        heroku_cursor.close()
        heroku_conn.close()

if __name__ == "__main__":
    export_and_populate() 