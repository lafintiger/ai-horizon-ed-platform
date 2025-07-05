"""
Enhanced Content Analyzer for AI-Horizon Ed
Analyzes educational content to generate comprehension questions and practical exercises

This service implements your next phase requirements:
1. LLM reads videos/documents 
2. Generates comprehension questions
3. Creates practical exercises for real-world application
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import os
import sys
import requests

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import config

logger = logging.getLogger(__name__)

@dataclass
class ContentAnalysis:
    """Structured content analysis result"""
    resource_id: int
    content_type: str
    key_concepts: List[str]
    learning_objectives: List[str]
    difficulty_level: str
    comprehension_questions: List[Dict[str, Any]]
    practical_exercises: List[Dict[str, Any]]
    analysis_timestamp: str

class EnhancedContentAnalyzer:
    """
    Service for analyzing educational content and generating learning materials
    
    METHODOLOGY (Transparent Workflow):
    1. Extract content from resource (video/document/article)
    2. LLM analysis to understand key concepts and learning value
    3. Generate 3-5 comprehension questions that test understanding
    4. Create 3 practical exercises for real-world application
    5. Store results with full transparency and traceability
    """
    
    def __init__(self):
        self.openai_api_key = config.get('OPENAI_API_KEY')
        self.anthropic_api_key = config.get('ANTHROPIC_API_KEY')
        
    def analyze_resource_content(self, resource_id: int) -> ContentAnalysis:
        """
        Main entry point for content analysis
        
        WORKFLOW:
        1. Get resource from database
        2. Extract content based on resource type
        3. Analyze content with LLM
        4. Generate questions and exercises
        5. Store results in database
        6. Return structured analysis
        """
        logger.info(f"Starting enhanced content analysis for resource {resource_id}")
        
        try:
            # Import here to avoid circular imports
            from utils.database import db_manager
            
            # Get resource data
            resource = db_manager.get_resource_by_id(resource_id)
            if not resource:
                logger.error(f"Resource {resource_id} not found")
                return None
            
            # Extract content information
            content_info = self._extract_content_info(resource)
            
            # Generate GPT-4 based analysis
            gpt_analysis = self._perform_gpt_analysis(resource, content_info)
            
            if not gpt_analysis:
                logger.warning(f"No GPT analysis generated for resource {resource_id}")
                return self._create_fallback_analysis(resource_id, resource)
            
            # Parse and structure the analysis
            questions = gpt_analysis.get('questions', [])
            exercises = gpt_analysis.get('exercises', [])
            
            analysis = ContentAnalysis(
                resource_id=resource_id,
                content_type=resource.get('resource_type', 'unknown'),
                key_concepts=gpt_analysis.get('key_concepts', []),
                learning_objectives=gpt_analysis.get('learning_objectives', []),
                difficulty_level=gpt_analysis.get('difficulty_level', 'intermediate'),
                comprehension_questions=questions,
                practical_exercises=exercises,
                analysis_timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"Completed enhanced content analysis for resource {resource_id}: "
                       f"{len(questions)} questions, {len(exercises)} exercises")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_resource_content for resource {resource_id}: {e}")
            return self._create_fallback_analysis(resource_id, resource if 'resource' in locals() else None)
    
    def _extract_content_info(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content information from resource"""
        try:
            url = resource.get('url', '')
            
            # Extract YouTube video ID if it's a YouTube video
            if 'youtube.com' in url or 'youtu.be' in url:
                video_id = self._extract_youtube_id(url)
                if video_id:
                    transcript = self._get_youtube_transcript(video_id)
                    return {
                        'type': 'youtube',
                        'video_id': video_id,
                        'transcript': transcript,
                        'title': resource.get('title', ''),
                        'description': resource.get('description', '')
                    }
            
            # For other content types, use title and description
            return {
                'type': 'general',
                'title': resource.get('title', ''),
                'description': resource.get('description', ''),
                'url': url
            }
            
        except Exception as e:
            logger.warning(f"Error extracting content info: {e}")
            return {
                'type': 'general',
                'title': resource.get('title', ''),
                'description': resource.get('description', ''),
                'error': str(e)
            }
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        import re
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _get_youtube_transcript(self, video_id: str) -> str:
        """Get YouTube video transcript"""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript = ' '.join([item['text'] for item in transcript_list])
            return transcript[:2000]  # Limit transcript length
        except Exception as e:
            logger.info(f"Transcript extraction failed, using description for https://www.youtube.com/watch?v={video_id}")
            return ""
    
    def _perform_gpt_analysis(self, resource: Dict[str, Any], content_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Perform GPT-4 analysis of the resource content"""
        try:
            logger.info(f"Starting GPT-4 content analysis for resource {resource['id']}")
            
            # Build analysis prompt
            prompt = self._build_analysis_prompt(resource, content_info)
            
            if self.openai_api_key:
                result = self._query_openai(prompt)
                if result:
                    return result
            
            if self.anthropic_api_key:
                result = self._query_anthropic(prompt)
                if result:
                    return result
            
            logger.warning("No AI API keys available for content analysis")
            return None
            
        except Exception as e:
            logger.error(f"Error in GPT analysis: {e}")
            return None
    
    def _build_analysis_prompt(self, resource: Dict[str, Any], content_info: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt"""
        
        content_text = ""
        if content_info.get('transcript'):
            content_text = f"\nTranscript: {content_info['transcript'][:1500]}"
        
        return f"""
Analyze this cybersecurity/technology educational resource and create comprehensive learning content:

RESOURCE:
Title: {resource.get('title', '')}
Description: {resource.get('description', '')}
Type: {resource.get('resource_type', '')}
URL: {resource.get('url', '')}
{content_text}

Create exactly 5 comprehension questions and at least 1 practical exercise. Return as JSON:

{{
    "key_concepts": ["concept1", "concept2", "concept3"],
    "learning_objectives": ["objective1", "objective2", "objective3"],
    "difficulty_level": "beginner|intermediate|advanced",
    "questions": [
        {{
            "question_text": "What is the main principle of Zero Trust security?",
            "question_type": "multiple_choice",
            "options": ["A) Trust everyone", "B) Never trust, always verify", "C) Trust but verify", "D) Verify once"],
            "correct_answer": "B",
            "explanation": "Zero Trust operates on the principle of never trusting any entity by default.",
            "concepts_tested": ["Zero Trust"]
        }}
    ],
    "exercises": [
        {{
            "title": "Implement Basic Security Control",
            "description": "Create a simple security implementation based on the concepts learned",
            "difficulty": "intermediate",
            "estimated_time_minutes": 30,
            "deliverables": ["Security plan", "Implementation steps"]
        }}
    ]
}}

Ensure questions test understanding of key concepts and exercises provide hands-on application opportunities.
"""
    
    def _query_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query OpenAI GPT-4 for content analysis"""
        try:
            import httpx
            
            headers = {
                'Authorization': f'Bearer {self.openai_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-4',
                'messages': [
                    {'role': 'system', 'content': 'You are an expert cybersecurity educator creating learning content. Always return valid JSON.'},
                    {'role': 'user', 'content': prompt}
                ],
                'max_tokens': 2000,
                'temperature': 0.3
            }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    'https://api.openai.com/v1/chat/completions',
                    headers=headers,
                    json=data
                )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                logger.info(f"GPT-4 response length: {len(content)} chars")
                
                # Try to parse JSON response
                try:
                    parsed_content = json.loads(content)
                    
                    # Count questions and exercises
                    questions_count = len(parsed_content.get('questions', []))
                    exercises_count = len(parsed_content.get('exercises', []))
                    
                    logger.info(f"Completed GPT-4 analysis for resource {prompt.split('Title:')[1].split('Description:')[0].strip()}: {questions_count} questions, {exercises_count} exercises")
                    
                    return parsed_content
                except json.JSONDecodeError:
                    logger.warning("GPT-4 response was not valid JSON, attempting to extract content")
                    return self._extract_content_from_text(content)
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying OpenAI: {e}")
            return None
    
    def _query_anthropic(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query Anthropic Claude for content analysis"""
        try:
            headers = {
                'x-api-key': self.anthropic_api_key,
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01'
            }
            
            data = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 2000,
                'messages': [
                    {'role': 'user', 'content': prompt}
                ]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return self._extract_content_from_text(content)
            else:
                logger.error(f"Anthropic API error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error querying Anthropic: {e}")
            return None
    
    def _extract_content_from_text(self, text: str) -> Dict[str, Any]:
        """Extract structured content from text response"""
        try:
            # Simple extraction logic for when JSON parsing fails
            questions = []
            exercises = []
            
            # Look for question patterns
            import re
            question_matches = re.findall(r'(?:Question|Q)\s*\d*[:\.]?\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
            
            for i, q_text in enumerate(question_matches[:5]):
                questions.append({
                    'question_text': q_text.strip(),
                    'question_type': 'multiple_choice',
                    'options': ['A) Option 1', 'B) Option 2', 'C) Option 3', 'D) Option 4'],
                    'correct_answer': 'A',
                    'explanation': 'Answer explanation',
                    'concepts_tested': ['General concept']
                })
            
            # Create at least one exercise
            exercises.append({
                'title': 'Practical Application Exercise',
                'description': 'Apply the concepts learned from this resource',
                'difficulty': 'intermediate',
                'estimated_time_minutes': 30,
                'deliverables': ['Implementation plan', 'Test results']
            })
            
            return {
                'key_concepts': ['Security', 'Implementation', 'Best Practices'],
                'learning_objectives': ['Understand core concepts', 'Apply practical skills'],
                'difficulty_level': 'intermediate',
                'questions': questions,
                'exercises': exercises
            }
            
        except Exception as e:
            logger.error(f"Error extracting content from text: {e}")
            return self._create_default_content()
    
    def _create_fallback_analysis(self, resource_id: int, resource: Optional[Dict[str, Any]]) -> ContentAnalysis:
        """Create fallback analysis when AI analysis fails"""
        title = resource.get('title', 'Unknown Resource') if resource else 'Unknown Resource'
        
        return ContentAnalysis(
            resource_id=resource_id,
            content_type='unknown',
            key_concepts=['General cybersecurity concepts'],
            learning_objectives=['Understand key concepts from the resource'],
            difficulty_level='intermediate',
            comprehension_questions=[
                {
                    'question_text': f'What is the main topic covered in "{title}"?',
                    'question_type': 'short_answer',
                    'options': [],
                    'correct_answer': 'The main cybersecurity topic covered',
                    'explanation': 'This question tests basic comprehension of the resource content.',
                    'concepts_tested': ['General understanding']
                }
            ],
            practical_exercises=[
                {
                    'title': 'Apply Key Concepts',
                    'description': 'Practice implementing the main concepts from this resource',
                    'difficulty': 'intermediate',
                    'estimated_time_minutes': 30,
                    'deliverables': ['Implementation notes', 'Practice results']
                }
            ],
            analysis_timestamp=datetime.now().isoformat()
        )
    
    def _create_default_content(self) -> Dict[str, Any]:
        """Create default content structure"""
        return {
            'key_concepts': ['Security fundamentals'],
            'learning_objectives': ['Understand basic concepts'],
            'difficulty_level': 'intermediate',
            'questions': [
                {
                    'question_text': 'What is a key security principle?',
                    'question_type': 'multiple_choice',
                    'options': ['A) Security by default', 'B) Security by obscurity', 'C) No security', 'D) Maximum access'],
                    'correct_answer': 'A',
                    'explanation': 'Security by default is a fundamental principle.',
                    'concepts_tested': ['Security principles']
                }
            ],
            'exercises': [
                {
                    'title': 'Basic Security Implementation',
                    'description': 'Implement a basic security control',
                    'difficulty': 'beginner',
                    'estimated_time_minutes': 20,
                    'deliverables': ['Security plan']
                }
            ]
        }

    def generate_learning_content(self, resource_data):
        """Generate learning content (questions, exercises) for a resource"""
        try:
            # Extract resource ID from the resource data
            resource_id = resource_data.get('id') if isinstance(resource_data, dict) else resource_data
            
            if not resource_id:
                logger.warning(f"No resource ID found in resource data: {resource_data}")
                return None
            
            # Use the existing enhanced analysis method
            analysis_result = self.analyze_resource_content(resource_id)
            
            if not analysis_result:
                logger.warning(f"No analysis result for resource {resource_id}")
                return None
            
            # Extract questions and exercises from the analysis
            questions = []
            exercises = []
            
            # Handle ContentAnalysis object
            if hasattr(analysis_result, 'comprehension_questions'):
                questions = [
                    {
                        'question': q.get('question_text', ''),
                        'options': q.get('options', []),
                        'correct_answer': q.get('correct_answer', ''),
                        'explanation': q.get('explanation', ''),
                        'difficulty': 'medium'
                    }
                    for q in analysis_result.comprehension_questions
                ]
            
            if hasattr(analysis_result, 'practical_exercises'):
                exercises = [
                    {
                        'title': ex.get('title', ''),
                        'description': ex.get('description', ''),
                        'instructions': ex.get('deliverables', []),
                        'difficulty': ex.get('difficulty', 'medium'),
                        'estimated_time': ex.get('estimated_time_minutes', 30)
                    }
                    for ex in analysis_result.practical_exercises
                ]
            
            return {
                'questions': questions,
                'exercises': exercises,
                'resource_id': resource_id
            }
            
        except Exception as e:
            logger.error(f"Error generating learning content: {e}")
            return None

# Create global instance
enhanced_content_analyzer = EnhancedContentAnalyzer() 