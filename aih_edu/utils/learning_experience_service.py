"""
Learning Experience Service
Orchestrates enhanced learning experiences for skills, creating guided learning paths
and managing progress for anonymous users.
"""

import json
import uuid
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from utils.config import config
from utils.database import db_manager
from utils.ai_content_analyzer import content_analyzer

logger = logging.getLogger(__name__)

class LearningExperienceService:
    """Service to manage enhanced learning experiences"""
    
    def __init__(self):
        self.session_timeout_hours = 24  # Session expires after 24 hours
        
    def get_skill_learning_experience(self, skill_name: str, session_id: Optional[str] = None,
                                     difficulty_filter: Optional[str] = None,
                                     cost_filter: Optional[str] = None) -> Dict[str, Any]:
        """Get complete learning experience for a skill"""
        logger.info(f"Generating learning experience for skill: {skill_name}")
        
        # Get skill data
        skills = db_manager.get_emerging_skills()
        logger.info(f"Found {len(skills)} skills in database")
        logger.info(f"Looking for skill: '{skill_name}' (normalized)")
        
        skill = next((s for s in skills if s['skill_name'].lower() == skill_name.lower()), None)
        
        if not skill:
            available_skills = [s['skill_name'] for s in skills]
            logger.warning(f"Skill '{skill_name}' not found. Available skills: {available_skills}")
            raise ValueError(f"Skill '{skill_name}' not found")
        
        skill_id = skill['id']
        
        # Get or create session
        if not session_id:
            session_id = self.create_learning_session(skill_id)
        
        session_data = db_manager.get_learning_session(session_id)
        
        # Get enhanced resources with filtering
        resources = db_manager.get_enhanced_resources_for_skill(
            skill_id, difficulty_filter, cost_filter
        )
        
        # Analyze and enhance resources if needed
        resources = self._ensure_resources_analyzed(resources, skill_id)
        
        # Get or create learning paths
        learning_paths = self._get_or_create_learning_paths(skill_id, resources)
        
        # Get learning statistics
        learning_stats = self._calculate_learning_stats(resources, session_data)
        
        # Prepare resource categories
        resource_categories = self._categorize_resources(resources)
        
        # Prepare progress data
        progress_data = self._calculate_progress(session_data, resources, learning_paths)
        
        return {
            'skill': skill,
            'session_id': session_id,
            'learning_paths': learning_paths,
            'resources': resources,
            'resource_categories': resource_categories,
            'learning_stats': learning_stats,
            'progress': progress_data,
            'filters': {
                'difficulty': difficulty_filter,
                'cost': cost_filter,
                'available_difficulties': self._get_available_difficulties(resources),
                'available_costs': self._get_available_costs(resources)
            },
            'recommendations': self._get_learning_recommendations(skill_id, session_data, resources)
        }
    
    def create_learning_session(self, skill_id: int, learning_path_id: Optional[int] = None) -> str:
        """Create a new anonymous learning session"""
        session_id = str(uuid.uuid4())
        db_manager.create_learning_session(session_id, skill_id, learning_path_id)
        logger.info(f"Created learning session {session_id} for skill {skill_id}")
        return session_id
    
    def update_learning_progress(self, session_id: str, progress_update: Dict[str, Any]) -> Dict[str, Any]:
        """Update learning progress for a session"""
        session_data = db_manager.get_learning_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        
        # Merge progress data
        updated_progress = {
            'current_resource_id': progress_update.get('current_resource_id', session_data.get('current_resource_id')),
            'resources_completed': list(set(
                session_data.get('resources_completed', []) + 
                progress_update.get('new_completed_resources', [])
            )),
            'questions_answered': {
                **session_data.get('questions_answered', {}),
                **progress_update.get('questions_answered', {})
            },
            'projects_completed': list(set(
                session_data.get('projects_completed', []) + 
                progress_update.get('new_completed_projects', [])
            )),
            'time_spent_minutes': session_data.get('time_spent_minutes', 0) + progress_update.get('additional_time', 0),
            'learning_preferences': {
                **session_data.get('learning_preferences', {}),
                **progress_update.get('learning_preferences', {})
            }
        }
        
        # Calculate progress percentage
        skill_id = session_data['skill_id']
        total_resources = len(db_manager.get_enhanced_resources_for_skill(skill_id))
        completed_resources = len(updated_progress['resources_completed'])
        updated_progress['progress_percentage'] = (completed_resources / max(total_resources, 1)) * 100
        
        # Update database
        db_manager.update_learning_progress(session_id, updated_progress)
        
        logger.info(f"Updated progress for session {session_id}: {updated_progress['progress_percentage']:.1f}% complete")
        
        return updated_progress
    
    def get_resource_learning_content(self, resource_id: int, content_type: Optional[str] = None) -> Dict[str, Any]:
        """Get enhanced learning content for a specific resource"""
        resource = db_manager.get_resource_by_id(resource_id)
        if not resource:
            raise ValueError(f"Resource {resource_id} not found")
        
        learning_content = db_manager.get_learning_content(resource_id, content_type)
        
        # Organize content by type
        content_by_type = defaultdict(list)
        for content in learning_content:
            content_by_type[content['content_type']].append(content)
        
        return {
            'resource': resource,
            'questions': content_by_type.get('questions', []),
            'projects': content_by_type.get('projects', []),
            'summary': content_by_type.get('summary', []),
            'objectives': content_by_type.get('objectives', [])
        }
    
    def answer_comprehension_question(self, session_id: str, resource_id: int, 
                                    question_id: int, answer: str) -> Dict[str, Any]:
        """Process a comprehension question answer"""
        session_data = db_manager.get_learning_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        
        # Get the question
        learning_content = db_manager.get_learning_content(resource_id, 'questions')
        question = None
        for content in learning_content:
            for q in content['content_data'].get('questions', []):
                if q['id'] == question_id:
                    question = q
                    break
        
        if not question:
            raise ValueError(f"Question {question_id} not found for resource {resource_id}")
        
        # Evaluate answer
        is_correct = False
        feedback = "Answer recorded."
        
        if question['type'] == 'multiple_choice':
            is_correct = answer.upper() == question.get('correct_answer', '').upper()
            feedback = question.get('explanation', 'Answer evaluated.') if is_correct else f"Incorrect. {question.get('explanation', '')}"
        
        # Update session with answer
        questions_answered = session_data.get('questions_answered', {})
        question_key = f"{resource_id}_{question_id}"
        questions_answered[question_key] = {
            'answer': answer,
            'is_correct': is_correct,
            'answered_at': datetime.now().isoformat(),
            'feedback': feedback
        }
        
        self.update_learning_progress(session_id, {
            'questions_answered': questions_answered
        })
        
        return {
            'is_correct': is_correct,
            'feedback': feedback,
            'question': question
        }
    
    def complete_project(self, session_id: str, resource_id: int, project_id: int, 
                        completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mark a project as completed"""
        session_data = db_manager.get_learning_session(session_id)
        if not session_data:
            raise ValueError(f"Session {session_id} not found")
        
        project_key = f"{resource_id}_{project_id}"
        completion_record = {
            'project_id': project_id,
            'resource_id': resource_id,
            'completed_at': datetime.now().isoformat(),
            'deliverables': completion_data.get('deliverables', []),
            'notes': completion_data.get('notes', ''),
            'self_assessment': completion_data.get('self_assessment', {})
        }
        
        self.update_learning_progress(session_id, {
            'new_completed_projects': [project_key]
        })
        
        logger.info(f"Project {project_id} completed for session {session_id}")
        
        return {
            'status': 'completed',
            'completion_record': completion_record
        }
    
    def queue_skill_for_analysis(self, skill_name: str, priority: int = 1) -> Dict[str, Any]:
        """Queue all resources for a skill for AI analysis"""
        skills = db_manager.get_emerging_skills()
        skill = next((s for s in skills if s['skill_name'].lower() == skill_name.lower()), None)
        
        if not skill:
            raise ValueError(f"Skill '{skill_name}' not found")
        
        resources = db_manager.get_resources_for_skill(skill['id'])
        queued_count = 0
        
        for resource in resources:
            if not resource.get('ai_analysis_date'):  # Only queue if not already analyzed
                db_manager.queue_content_analysis(resource['id'], 'full', priority)
                queued_count += 1
        
        logger.info(f"Queued {queued_count} resources for analysis for skill: {skill_name}")
        
        return {
            'skill': skill['skill_name'],
            'total_resources': len(resources),
            'queued_for_analysis': queued_count,
            'already_analyzed': len(resources) - queued_count
        }
    
    def process_analysis_queue(self, batch_size: int = 5) -> Dict[str, Any]:
        """Process queued resources for analysis"""
        queue_items = db_manager.get_analysis_queue('pending', batch_size)
        
        processed = 0
        errors = []
        
        for item in queue_items:
            try:
                # Update status to processing
                db_manager.update_analysis_queue_status(item['id'], 'processing')
                
                # Perform analysis
                result = content_analyzer.analyze_resource_comprehensive(
                    item['resource_id'], 
                    1  # Default skill_id, would need to determine actual skill
                )
                
                # Mark as completed
                db_manager.update_analysis_queue_status(item['id'], 'completed')
                processed += 1
                
                logger.info(f"Analyzed resource {item['resource_id']}: {item['title']}")
                
            except Exception as e:
                logger.error(f"Failed to analyze resource {item['resource_id']}: {e}")
                db_manager.update_analysis_queue_status(item['id'], 'failed', str(e))
                errors.append({
                    'resource_id': item['resource_id'],
                    'title': item['title'],
                    'error': str(e)
                })
        
        return {
            'processed': processed,
            'errors': errors,
            'remaining_in_queue': len(db_manager.get_analysis_queue('pending'))
        }
    
    def _ensure_resources_analyzed(self, resources: List[Dict[str, Any]], skill_id: int) -> List[Dict[str, Any]]:
        """Ensure all resources have been analyzed, queue if needed"""
        analyzed_resources = []
        
        for resource in resources:
            if not resource.get('ai_analysis_date'):
                # Queue for analysis
                db_manager.queue_content_analysis(resource['id'], 'full', 1)
                logger.info(f"Queued resource {resource['id']} for analysis")
            
            # Add learning content to resource
            resource['learning_content'] = db_manager.get_learning_content(resource['id'])
            analyzed_resources.append(resource)
        
        return analyzed_resources
    
    def _get_or_create_learning_paths(self, skill_id: int, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get existing learning paths or create them if they don't exist"""
        existing_paths = db_manager.get_learning_paths_for_skill(skill_id)
        
        if existing_paths:
            return existing_paths
        
        # Create learning paths based on difficulty levels
        paths_to_create = []
        
        # Group resources by difficulty
        difficulty_groups = defaultdict(list)
        for resource in resources:
            difficulty = resource.get('difficulty_level', 'intermediate')
            difficulty_groups[difficulty].append(resource['id'])
        
        # Create paths for each difficulty level
        difficulty_order = ['beginner', 'intermediate', 'advanced', 'expert']
        
        for difficulty in difficulty_order:
            if difficulty in difficulty_groups:
                resource_sequence = sorted(
                    difficulty_groups[difficulty],
                    key=lambda rid: next(
                        (r.get('sequence_order', 0) for r in resources if r['id'] == rid), 0
                    )
                )
                
                if resource_sequence:
                    path_data = {
                        'path_description': f"{difficulty.title()} level learning path",
                        'estimated_duration': sum(
                            next((r.get('estimated_duration', 60) for r in resources if r['id'] == rid), 60)
                            for rid in resource_sequence
                        ),
                        'prerequisites': [f"Basic understanding of cybersecurity concepts"] if difficulty != 'beginner' else [],
                        'learning_milestones': [
                            f"Complete {len(resource_sequence)} resources",
                            f"Master {difficulty} level concepts"
                        ],
                        'completion_projects': [
                            f"Capstone project applying {difficulty} level skills"
                        ]
                    }
                    
                    path_id = db_manager.create_learning_path(
                        skill_id, difficulty, resource_sequence, path_data
                    )
                    
                    paths_to_create.append({
                        'id': path_id,
                        'path_name': difficulty,
                        'resource_sequence': resource_sequence,
                        **path_data
                    })
        
        return paths_to_create if paths_to_create else existing_paths
    
    def _calculate_learning_stats(self, resources: List[Dict[str, Any]], 
                                session_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate learning statistics"""
        total_resources = len(resources)
        total_duration = sum(r.get('estimated_duration', 60) for r in resources)
        
        # Count by difficulty
        difficulty_counts = defaultdict(int)
        for resource in resources:
            difficulty = resource.get('difficulty_level', 'unknown')
            difficulty_counts[difficulty] += 1
        
        # Count by cost
        cost_counts = defaultdict(int)
        for resource in resources:
            cost = resource.get('cost_type', 'unknown')
            cost_counts[cost] += 1
        
        # Progress stats
        completed_resources = len(session_data.get('resources_completed', [])) if session_data else 0
        time_spent = session_data.get('time_spent_minutes', 0) if session_data else 0
        
        return {
            'total_resources': total_resources,
            'completed_resources': completed_resources,
            'total_duration_minutes': total_duration,
            'time_spent_minutes': time_spent,
            'estimated_time_remaining': max(0, total_duration - time_spent),
            'completion_percentage': (completed_resources / max(total_resources, 1)) * 100,
            'difficulty_distribution': dict(difficulty_counts),
            'cost_distribution': dict(cost_counts),
            'average_quality': sum(r.get('quality_score', 0) for r in resources) / max(total_resources, 1)
        }
    
    def _categorize_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize resources for better organization"""
        categories = {
            'free': [],
            'paid': [],
            'beginner': [],
            'intermediate': [],
            'advanced': [],
            'videos': [],
            'courses': [],
            'tools': [],
            'documentation': []
        }
        
        for resource in resources:
            # By cost
            cost_type = resource.get('cost_type', 'unknown')
            if cost_type == 'free':
                categories['free'].append(resource)
            elif cost_type in ['paid', 'freemium']:
                categories['paid'].append(resource)
            
            # By difficulty
            difficulty = resource.get('difficulty_level', 'intermediate')
            if difficulty in categories:
                categories[difficulty].append(resource)
            
            # By type
            resource_type = resource.get('resource_type', '').lower()
            if 'video' in resource_type or resource.get('source_platform') == 'youtube':
                categories['videos'].append(resource)
            elif 'course' in resource_type:
                categories['courses'].append(resource)
            elif 'tool' in resource_type:
                categories['tools'].append(resource)
            elif 'documentation' in resource_type:
                categories['documentation'].append(resource)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def _calculate_progress(self, session_data: Optional[Dict[str, Any]], 
                          resources: List[Dict[str, Any]], 
                          learning_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate detailed progress information"""
        if not session_data:
            return {
                'overall_progress': 0,
                'current_resource': None,
                'completed_resources': [],
                'next_recommended': None,
                'learning_streak': 0,
                'achievements': []
            }
        
        completed_resource_ids = session_data.get('resources_completed', [])
        current_resource_id = session_data.get('current_resource_id')
        
        # Find current and next resources
        current_resource = None
        next_recommended = None
        
        if current_resource_id:
            current_resource = next((r for r in resources if r['id'] == current_resource_id), None)
        
        # Find next resource based on sequence order
        incomplete_resources = [r for r in resources if r['id'] not in completed_resource_ids]
        if incomplete_resources:
            next_recommended = min(incomplete_resources, key=lambda r: r.get('sequence_order', 999))
        
        # Calculate achievements
        achievements = []
        if len(completed_resource_ids) >= 1:
            achievements.append("🎯 First Resource Complete")
        if len(completed_resource_ids) >= 5:
            achievements.append("📚 Learning Momentum")
        if len(completed_resource_ids) >= 10:
            achievements.append("🏆 Dedicated Learner")
        
        return {
            'overall_progress': session_data.get('progress_percentage', 0),
            'current_resource': current_resource,
            'completed_resources': [r for r in resources if r['id'] in completed_resource_ids],
            'next_recommended': next_recommended,
            'learning_streak': self._calculate_learning_streak(session_data),
            'achievements': achievements,
            'time_spent_today': self._calculate_time_spent_today(session_data),
            'questions_answered': len(session_data.get('questions_answered', {})),
            'projects_completed': len(session_data.get('projects_completed', []))
        }
    
    def _get_available_difficulties(self, resources: List[Dict[str, Any]]) -> List[str]:
        """Get available difficulty levels from resources"""
        difficulties = set()
        for resource in resources:
            difficulty = resource.get('difficulty_level')
            if difficulty and difficulty != 'unknown':
                difficulties.add(difficulty)
        return sorted(list(difficulties), key=lambda x: ['beginner', 'intermediate', 'advanced', 'expert'].index(x))
    
    def _get_available_costs(self, resources: List[Dict[str, Any]]) -> List[str]:
        """Get available cost types from resources"""
        costs = set()
        for resource in resources:
            cost = resource.get('cost_type')
            if cost and cost != 'unknown':
                costs.add(cost)
        return sorted(list(costs))
    
    def _get_learning_recommendations(self, skill_id: int, session_data: Optional[Dict[str, Any]], 
                                   resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate personalized learning recommendations"""
        recommendations = {
            'next_resource': None,
            'suggested_path': None,
            'focus_areas': [],
            'tips': []
        }
        
        if not session_data:
            # New learner recommendations
            beginner_resources = [r for r in resources if r.get('difficulty_level') == 'beginner']
            if beginner_resources:
                recommendations['next_resource'] = min(beginner_resources, key=lambda r: r.get('sequence_order', 999))
            recommendations['suggested_path'] = 'Start with beginner-level resources'
            recommendations['tips'] = [
                "Begin with foundational concepts",
                "Take your time with each resource",
                "Practice hands-on when possible"
            ]
        else:
            # Personalized recommendations based on progress
            completed_count = len(session_data.get('resources_completed', []))
            if completed_count == 0:
                recommendations['tips'].append("Complete your first resource to build momentum")
            elif completed_count < 3:
                recommendations['tips'].append("Great start! Keep the learning momentum going")
            else:
                recommendations['tips'].append("Excellent progress! Consider tackling more advanced topics")
        
        return recommendations
    
    def _calculate_learning_streak(self, session_data: Dict[str, Any]) -> int:
        """Calculate current learning streak in days"""
        # This would require tracking daily activity
        # For now, return a simple calculation based on recent activity
        last_activity = session_data.get('last_activity')
        if last_activity:
            try:
                last_active = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                days_since = (datetime.now() - last_active).days
                return max(0, 7 - days_since)  # Simple streak calculation
            except:
                return 0
        return 0
    
    def _calculate_time_spent_today(self, session_data: Dict[str, Any]) -> int:
        """Calculate time spent learning today"""
        # This would require more sophisticated session tracking
        # For now, return a portion of total time if last activity was today
        last_activity = session_data.get('last_activity')
        if last_activity:
            try:
                last_active = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                if last_active.date() == datetime.now().date():
                    return min(session_data.get('time_spent_minutes', 0), 480)  # Max 8 hours per day
            except:
                pass
        return 0

# Global service instance
learning_service = LearningExperienceService() 