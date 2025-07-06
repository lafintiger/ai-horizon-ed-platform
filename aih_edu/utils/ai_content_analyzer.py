"""
AI Content Analysis Service for Enhanced Learning Experience
Performs deep content analysis to extract maximum educational value from resources.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import urllib.parse
import requests
from dataclasses import dataclass

from utils.config import config

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ContentAnalysisResult:
    """Structure for content analysis results"""
    difficulty_level: str
    cost_type: str
    estimated_duration: int
    learning_objectives: List[str]
    sequence_order: int
    source_platform: str
    content_extracted: Dict[str, Any]
    comprehension_questions: List[Dict[str, Any]]
    suggested_projects: List[Dict[str, Any]]
    learning_summary: str

class AIContentAnalyzer:
    """AI-powered content analyzer for educational resources"""
    
    def __init__(self, database_manager):
        self.db_manager = database_manager
        self.anthropic_api_key = config.get('ANTHROPIC_API_KEY')
        self.openai_api_key = config.get('OPENAI_API_KEY')
        
    def analyze_resource_comprehensive(self, resource_id: int, skill_id: int) -> ContentAnalysisResult:
        """Perform comprehensive analysis of an educational resource"""
        logger.info(f"Starting comprehensive analysis for resource {resource_id}")
        
        # Get resource data
        resource = self.db_manager.get_resource_by_id(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")
        
        # Extract content based on resource type
        content_extracted = self._extract_content(resource)
        
        # Perform AI analysis
        analysis_prompt = self._build_analysis_prompt(resource, content_extracted)
        ai_analysis = self._perform_ai_analysis(analysis_prompt)
        
        # Generate learning content
        questions = self._generate_comprehension_questions(resource, content_extracted, ai_analysis)
        projects = self._generate_suggested_projects(resource, content_extracted, ai_analysis)
        summary = self._generate_learning_summary(resource, ai_analysis)
        
        # Determine sequence order within skill
        sequence_order = self._calculate_sequence_order(resource, skill_id, ai_analysis)
        
        result = ContentAnalysisResult(
            difficulty_level=ai_analysis.get('difficulty_level', 'unknown'),
            cost_type=ai_analysis.get('cost_type', 'unknown'),
            estimated_duration=ai_analysis.get('estimated_duration', 0),
            learning_objectives=ai_analysis.get('learning_objectives', []),
            sequence_order=sequence_order,
            source_platform=self._identify_platform(resource['url']),
            content_extracted=content_extracted,
            comprehension_questions=questions,
            suggested_projects=projects,
            learning_summary=summary
        )
        
        # Store results in database
        self._store_analysis_results(resource_id, skill_id, result)
        
        logger.info(f"Completed comprehensive analysis for resource {resource_id}")
        return result
    
    def _extract_content(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content from different resource types"""
        content = {
            'title': resource['title'],
            'description': resource['description'],
            'url': resource['url'],
            'resource_type': resource['resource_type'],
            'extracted_text': '',
            'metadata': {}
        }
        
        url = resource['url']
        
        try:
            if 'youtube.com' in url or 'youtu.be' in url:
                content.update(self._extract_youtube_content(url))
            elif any(domain in url for domain in ['coursera.org', 'udemy.com', 'edx.org']):
                content.update(self._extract_course_content(url))
            elif 'github.com' in url:
                content.update(self._extract_github_content(url))
            else:
                content.update(self._extract_web_content(url))
                
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
            content['extraction_error'] = str(e)
        
        return content
    
    def _extract_youtube_content(self, url: str) -> Dict[str, Any]:
        """Extract content from YouTube videos"""
        video_id = self._extract_youtube_id(url)
        if not video_id:
            return {'error': 'Could not extract video ID'}
        
        # For now, we'll use the title and description from the database
        # In a real implementation, you might use YouTube API or transcript services
        return {
            'video_id': video_id,
            'platform': 'youtube',
            'content_type': 'video',
            'transcript_available': False,  # Would check with YouTube API
            'chapters': [],  # Would extract from description
            'duration_estimate': 'varies'
        }
    
    def _extract_course_content(self, url: str) -> Dict[str, Any]:
        """Extract content from online course platforms"""
        platform = None
        if 'coursera.org' in url:
            platform = 'coursera'
        elif 'udemy.com' in url:
            platform = 'udemy'
        elif 'edx.org' in url:
            platform = 'edx'
        
        return {
            'platform': platform,
            'content_type': 'course',
            'modules': [],  # Would extract from course structure
            'prerequisites': [],  # Would parse from course description
            'certification_available': True  # Assumption for major platforms
        }
    
    def _extract_github_content(self, url: str) -> Dict[str, Any]:
        """Extract content from GitHub repositories"""
        return {
            'platform': 'github',
            'content_type': 'repository',
            'repo_structure': {},  # Would analyze repo structure
            'readme_content': '',  # Would fetch README.md
            'documentation_quality': 'unknown'
        }
    
    def _extract_web_content(self, url: str) -> Dict[str, Any]:
        """Extract content from general web pages"""
        return {
            'platform': 'web',
            'content_type': 'article',
            'word_count': 0,  # Would extract from HTML
            'reading_time': 0,  # Would calculate based on word count
            'has_code_examples': False  # Would analyze content
        }
    
    def _build_analysis_prompt(self, resource: Dict[str, Any], content: Dict[str, Any]) -> str:
        """Build comprehensive analysis prompt for AI"""
        return f"""
Analyze this educational resource for the skill "{resource['skill_category']}" and provide a comprehensive assessment:

RESOURCE DETAILS:
Title: {resource['title']}
Description: {resource['description']}
Resource Type: {resource['resource_type']}
URL: {resource['url']}
Platform: {content.get('platform', 'unknown')}

ANALYSIS REQUIRED:
1. Difficulty Level: beginner|intermediate|advanced|expert
2. Cost Type: free|freemium|paid
3. Estimated Duration: in minutes for completion
4. Learning Objectives: specific, actionable learning goals (3-5 items)
5. Prerequisites: what knowledge/skills are needed beforehand
6. Learning Outcomes: what learners will be able to do after completion

Please provide your analysis in this JSON format:
{{
    "difficulty_level": "beginner|intermediate|advanced|expert",
    "cost_type": "free|freemium|paid",
    "estimated_duration": 120,
    "learning_objectives": [
        "Understand core concepts of...",
        "Implement basic techniques for...",
        "Analyze and evaluate..."
    ],
    "prerequisites": [
        "Basic understanding of...",
        "Familiarity with..."
    ],
    "learning_outcomes": [
        "Ability to configure...",
        "Skills to troubleshoot..."
    ],
    "quality_assessment": {{
        "content_depth": "shallow|moderate|deep",
        "practical_applicability": "low|medium|high",
        "clarity_rating": 1-10,
        "up_to_date": true/false
    }},
    "educational_value": {{
        "theoretical_knowledge": 1-10,
        "practical_skills": 1-10,
        "real_world_relevance": 1-10
    }}
}}

Be specific and practical in your assessment. Focus on actionable learning objectives and realistic time estimates.
"""
    
    def _perform_ai_analysis(self, prompt: str) -> Dict[str, Any]:
        """Perform AI analysis using Claude or OpenAI"""
        try:
            # Try Claude first (Anthropic)
            if self.anthropic_api_key:
                result = self._query_claude(prompt)
                if result:
                    return result
            
            # Fallback to OpenAI
            if self.openai_api_key:
                result = self._query_openai(prompt)
                if result:
                    return result
            
            # Fallback analysis if APIs are unavailable
            return self._fallback_analysis()
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return self._fallback_analysis()
    
    def _query_claude(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query Claude AI for analysis"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.anthropic_api_key,
                'anthropic-version': '2023-06-01'
            }
            
            payload = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 2000,
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"Claude API error: {e}")
        
        return None
    
    def _query_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query OpenAI for analysis"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.openai_api_key}'
            }
            
            payload = {
                'model': 'gpt-4',
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }],
                'max_tokens': 2000,
                'temperature': 0.3
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        
        return None
    
    def _fallback_analysis(self) -> Dict[str, Any]:
        """Provide fallback analysis when AI APIs are unavailable"""
        return {
            'difficulty_level': 'intermediate',
            'cost_type': 'unknown',
            'estimated_duration': 60,
            'learning_objectives': [
                'Understand core concepts',
                'Apply practical techniques',
                'Develop foundational skills'
            ],
            'prerequisites': ['Basic technical knowledge'],
            'learning_outcomes': ['Improved understanding of the topic'],
            'quality_assessment': {
                'content_depth': 'moderate',
                'practical_applicability': 'medium',
                'clarity_rating': 7,
                'up_to_date': True
            },
            'educational_value': {
                'theoretical_knowledge': 7,
                'practical_skills': 6,
                'real_world_relevance': 7
            }
        }
    
    def _generate_comprehension_questions(self, resource: Dict[str, Any], 
                                        content: Dict[str, Any], 
                                        analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate comprehension questions for the resource"""
        questions_prompt = f"""
Based on this educational resource about {resource['skill_category']}, generate 5 comprehension questions to test understanding:

Resource: {resource['title']}
Learning Objectives: {json.dumps(analysis.get('learning_objectives', []))}
Difficulty Level: {analysis.get('difficulty_level', 'intermediate')}

Generate questions that:
1. Test conceptual understanding
2. Check practical application ability
3. Verify retention of key information
4. Assess critical thinking
5. Evaluate real-world application

Format as JSON:
{{
    "questions": [
        {{
            "id": 1,
            "question": "What is the primary purpose of...",
            "type": "multiple_choice|short_answer|essay",
            "options": ["A", "B", "C", "D"],  // for multiple choice only
            "correct_answer": "A",  // for multiple choice
            "explanation": "This tests understanding of...",
            "difficulty": "easy|medium|hard"
        }}
    ]
}}
"""
        
        try:
            if self.anthropic_api_key:
                result = self._query_claude(questions_prompt)
                if result and 'questions' in result:
                    return result['questions']
        except Exception as e:
            logger.error(f"Failed to generate questions: {e}")
        
        # Fallback questions
        return [
            {
                "id": 1,
                "question": f"What are the key concepts covered in {resource['title']}?",
                "type": "short_answer",
                "explanation": "This tests basic comprehension of main topics",
                "difficulty": "easy"
            },
            {
                "id": 2,
                "question": f"How would you apply the concepts from {resource['title']} in a real-world scenario?",
                "type": "essay",
                "explanation": "This tests practical application ability",
                "difficulty": "medium"
            }
        ]
    
    def _generate_suggested_projects(self, resource: Dict[str, Any], 
                                   content: Dict[str, Any], 
                                   analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate suggested hands-on projects"""
        projects_prompt = f"""
Based on this educational resource about {resource['skill_category']}, suggest 3 hands-on projects to reinforce learning:

Resource: {resource['title']}
Learning Objectives: {json.dumps(analysis.get('learning_objectives', []))}
Difficulty Level: {analysis.get('difficulty_level', 'intermediate')}

Generate projects that:
1. Apply the learned concepts practically
2. Build real-world skills
3. Create portfolio-worthy deliverables
4. Progressively increase in complexity

Format as JSON:
{{
    "projects": [
        {{
            "id": 1,
            "title": "Basic Implementation Project",
            "description": "Create a simple...",
            "difficulty": "beginner|intermediate|advanced",
            "estimated_hours": 2,
            "deliverables": ["Working implementation", "Documentation"],
            "learning_goals": ["Apply basic concepts", "Practice implementation"],
            "prerequisites": ["Complete the resource"],
            "tools_needed": ["Tool 1", "Tool 2"],
            "success_criteria": ["Functional implementation", "Proper documentation"]
        }}
    ]
}}
"""
        
        try:
            if self.anthropic_api_key:
                result = self._query_claude(projects_prompt)
                if result and 'projects' in result:
                    return result['projects']
        except Exception as e:
            logger.error(f"Failed to generate projects: {e}")
        
        # Fallback projects
        return [
            {
                "id": 1,
                "title": f"Basic {resource['skill_category']} Implementation",
                "description": f"Apply the concepts from {resource['title']} in a simple implementation",
                "difficulty": "beginner",
                "estimated_hours": 2,
                "deliverables": ["Working implementation", "Basic documentation"],
                "learning_goals": ["Apply learned concepts", "Practice implementation"],
                "prerequisites": ["Complete the resource"],
                "tools_needed": ["Computer", "Internet access"],
                "success_criteria": ["Functional implementation"]
            }
        ]
    
    def _generate_learning_summary(self, resource: Dict[str, Any], analysis: Dict[str, Any]) -> str:
        """Generate a learning-focused summary"""
        return f"""
Learning Summary for {resource['title']}:

This {analysis.get('difficulty_level', 'intermediate')}-level resource provides {analysis.get('estimated_duration', 60)} minutes of learning content focused on {resource['skill_category']}.

Key Learning Objectives:
{chr(10).join('• ' + obj for obj in analysis.get('learning_objectives', ['Develop understanding of core concepts']))}

Educational Value:
• Theoretical Knowledge: {analysis.get('educational_value', {}).get('theoretical_knowledge', 7)}/10
• Practical Skills: {analysis.get('educational_value', {}).get('practical_skills', 6)}/10
• Real-World Relevance: {analysis.get('educational_value', {}).get('real_world_relevance', 7)}/10

Best suited for learners who want to develop practical skills in {resource['skill_category']}.
"""
    
    def _calculate_sequence_order(self, resource: Dict[str, Any], skill_id: int, analysis: Dict[str, Any]) -> int:
        """Calculate optimal sequence order within skill learning path"""
        difficulty_order = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
        
        base_order = difficulty_order.get(analysis.get('difficulty_level', 'intermediate'), 2)
        
        # Adjust based on resource type
        type_adjustments = {
            'overview': -0.5,      # Overview content should come first
            'tutorial': 0,         # Tutorials are standard
            'documentation': 0.3,  # Documentation comes after tutorials
            'tool': 0.5,          # Tools after learning concepts
            'certification': 1     # Certifications come last
        }
        
        adjustment = type_adjustments.get(resource['resource_type'], 0)
        final_order = int((base_order + adjustment) * 100)  # Scale to allow fine-grained ordering
        
        return final_order
    
    def _identify_platform(self, url: str) -> str:
        """Identify the platform/source of the resource"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'coursera.org' in url:
            return 'coursera'
        elif 'udemy.com' in url:
            return 'udemy'
        elif 'edx.org' in url:
            return 'edx'
        elif 'github.com' in url:
            return 'github'
        elif 'microsoft.com' in url:
            return 'microsoft'
        elif 'cisco.com' in url:
            return 'cisco'
        else:
            return 'web'
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
            r'youtube\.com\/watch\?.*v=([^&\n?#]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _store_analysis_results(self, resource_id: int, skill_id: int, result: ContentAnalysisResult) -> None:
        """Store analysis results in database"""
        # Update resource with analysis data
        analysis_data = {
            'difficulty_level': result.difficulty_level,
            'cost_type': result.cost_type,
            'estimated_duration': result.estimated_duration,
            'learning_objectives': result.learning_objectives,
            'sequence_order': result.sequence_order,
            'source_platform': result.source_platform,
            'content_extracted': result.content_extracted
        }
        
        db_manager.update_resource_analysis(resource_id, analysis_data)
        
        # Store learning content
        if result.comprehension_questions:
            db_manager.add_learning_content(
                resource_id, skill_id, 'questions',
                {'questions': result.comprehension_questions}
            )
        
        if result.suggested_projects:
            db_manager.add_learning_content(
                resource_id, skill_id, 'projects',
                {'projects': result.suggested_projects}
            )
        
        if result.learning_summary:
            db_manager.add_learning_content(
                resource_id, skill_id, 'summary',
                {'summary': result.learning_summary}
            )

    def grade_quiz_answers(self, resource: Dict[str, Any], questions: List[Dict[str, Any]], 
                          answers: List[str]) -> Optional[Dict[str, Any]]:
        """Grade quiz answers using AI for intelligent evaluation"""
        if len(answers) != len(questions):
            logger.error(f"Answer count ({len(answers)}) doesn't match question count ({len(questions)})")
            return None
        
        # Build grading prompt
        grading_prompt = self._build_grading_prompt(resource, questions, answers)
        
        # Get AI evaluation
        try:
            # Try Claude first
            if self.anthropic_api_key:
                result = self._query_claude_for_grading(grading_prompt)
                if result:
                    return result
            
            # Fallback to OpenAI
            if self.openai_api_key:
                result = self._query_openai_for_grading(grading_prompt)
                if result:
                    return result
            
            # If no AI available, return None to use fallback
            return None
            
        except Exception as e:
            logger.error(f"AI grading failed: {e}")
            return None
    
    def _build_grading_prompt(self, resource: Dict[str, Any], questions: List[Dict[str, Any]], 
                             answers: List[str]) -> str:
        """Build comprehensive grading prompt for AI"""
        # Handle both dictionary and other formats
        if isinstance(resource, dict):
            skill_category = resource.get('skill_category', 'technology')
            title = resource.get('title', 'Unknown')
            description = resource.get('description', 'No description available')
        else:
            skill_category = 'technology'
            title = 'Unknown'
            description = 'No description available'
            
        prompt = f"""
You are an expert educational assessor evaluating quiz answers for a resource about {skill_category}.

RESOURCE CONTEXT:
Title: {title}
Description: {description}
Subject Area: {skill_category}

GRADING TASK:
Please evaluate each answer against the provided correct answer and explanation. For each question, provide:
1. A score from 0-100 (0 = completely wrong, 100 = perfect answer)
2. Detailed feedback explaining the scoring
3. Specific suggestions for improvement
4. Recognition of what the student got right (if anything)

EVALUATION CRITERIA:
- Accuracy of core concepts (40%)
- Completeness of answer (30%)
- Clarity and organization (20%)
- Practical understanding (10%)

QUESTIONS AND ANSWERS TO EVALUATE:
"""
        
        for i, (question, answer) in enumerate(zip(questions, answers)):
            question_text = question.get('question_text', question.get('question', ''))
            correct_answer = question.get('correct_answer', '')
            explanation = question.get('explanation', 'No explanation provided')
            
            prompt += f"""
Question {i+1}: {question_text}
Student Answer: {answer}
Correct Answer: {correct_answer}
Explanation: {explanation}

"""
        
        prompt += """
Please provide your evaluation in this JSON format:
{
    "overall_score": 85,
    "total_questions": 5,
    "questions_evaluated": [
        {
            "question_number": 1,
            "student_answer": "...",
            "correct_answer": "...",
            "score": 85,
            "max_score": 100,
            "feedback": "Your answer demonstrates good understanding of the core concepts. You correctly identified... However, you could improve by...",
            "strengths": ["Correct identification of key concepts", "Good use of examples"],
            "improvements": ["More detail needed on implementation", "Consider edge cases"],
            "partial_credit_given": true
        }
    ],
    "overall_feedback": "Overall, you show strong understanding of the material. Focus on providing more detailed explanations and practical examples.",
    "study_recommendations": ["Review the section on advanced concepts", "Practice with real-world examples"],
    "passing_grade": true,
    "grade_letter": "B+"
}

Be encouraging but honest in your feedback. Recognize effort and partial understanding while clearly indicating areas for improvement.
"""
        
        return prompt
    
    def _query_claude_for_grading(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query Claude specifically for grading with optimized parameters"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': self.anthropic_api_key,
                'anthropic-version': '2023-06-01'
            }
            
            payload = {
                'model': 'claude-3-sonnet-20240229',
                'max_tokens': 3000,  # More tokens for detailed feedback
                'temperature': 0.1,  # Lower temperature for consistent grading
                'messages': [{
                    'role': 'user',
                    'content': prompt
                }]
            }
            
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=payload,
                timeout=45  # Longer timeout for grading
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']
                
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
            else:
                logger.error(f"Claude API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.error(f"Claude grading API error: {e}")
        
        return None
    
    def _query_openai_for_grading(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Query OpenAI specifically for grading with optimized parameters"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.openai_api_key}'
            }
            
            payload = {
                'model': 'gpt-4',
                'messages': [{
                    'role': 'system',
                    'content': 'You are an expert educational assessor providing detailed, constructive feedback on quiz answers. Be thorough, fair, and encouraging while maintaining academic standards.'
                }, {
                    'role': 'user',
                    'content': prompt
                }],
                'max_tokens': 3000,
                'temperature': 0.1,  # Lower temperature for consistent grading
                'presence_penalty': 0.1
            }
            
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    return json.loads(json_str)
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.error(f"OpenAI grading API error: {e}")
        
        return None

# Global analyzer instance
# Note: Global content_analyzer instance removed - create with database_manager from app.py 