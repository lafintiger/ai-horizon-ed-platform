import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from datetime import datetime
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://vincentnestler@localhost/aih_edu_local')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models
class EmergingSkill(db.Model):
    __tablename__ = 'emerging_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    skill_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    urgency_score = db.Column(db.Float, default=0.0)
    market_demand_evidence = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(50), default='active')
    source = db.Column(db.String(100))
    
    # Relationships
    learning_paths = db.relationship('SkillLearningPath', backref='skill', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'skill_name': self.skill_name,
            'description': self.description,
            'category': self.category,
            'urgency_score': self.urgency_score,
            'market_demand_evidence': self.market_demand_evidence,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'status': self.status,
            'source': self.source
        }

class EducationalResource(db.Model):
    __tablename__ = 'educational_resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    url = db.Column(db.String(1000), nullable=False)
    resource_type = db.Column(db.String(100))  # 'video', 'course', 'documentation', 'tool'
    difficulty_level = db.Column(db.String(50))  # 'beginner', 'intermediate', 'advanced'
    estimated_duration_minutes = db.Column(db.Integer)
    quality_score = db.Column(db.Float, default=0.0)
    ai_analysis_summary = db.Column(db.Text)
    transcript = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_analyzed = db.Column(db.DateTime)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'approved', 'rejected'
    
    # Relationships
    learning_paths = db.relationship('SkillLearningPath', backref='resource', lazy=True)
    quiz_questions = db.relationship('QuizQuestion', backref='resource', lazy=True)
    assignments = db.relationship('PracticalAssignment', backref='resource', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'resource_type': self.resource_type,
            'difficulty_level': self.difficulty_level,
            'estimated_duration_minutes': self.estimated_duration_minutes,
            'quality_score': self.quality_score,
            'ai_analysis_summary': self.ai_analysis_summary,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_analyzed': self.last_analyzed.isoformat() if self.last_analyzed else None,
            'status': self.status
        }

class SkillLearningPath(db.Model):
    __tablename__ = 'skill_learning_paths'
    
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('emerging_skills.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    sequence_order = db.Column(db.Integer)
    path_type = db.Column(db.String(50))  # 'foundation', 'intermediate', 'advanced', 'practical'
    is_required = db.Column(db.Boolean, default=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class PracticalAssignment(db.Model):
    __tablename__ = 'practical_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    assignment_title = db.Column(db.String(255), nullable=False)
    assignment_description = db.Column(db.Text, nullable=False)
    assignment_type = db.Column(db.String(50))  # 'coding', 'configuration', 'analysis', 'research'
    estimated_time_minutes = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class LearningSession(db.Model):
    __tablename__ = 'learning_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_token = db.Column(db.String(255), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('emerging_skills.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('educational_resources.id'), nullable=False)
    started_date = db.Column(db.DateTime, default=datetime.utcnow)
    completed_date = db.Column(db.DateTime)
    progress_percentage = db.Column(db.Float, default=0.0)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)

# Helper functions
def is_admin_logged_in():
    return 'admin_logged_in' in session

def require_admin():
    if not is_admin_logged_in():
        flash('Admin access required', 'error')
        return redirect(url_for('admin_login'))
    return None

# Routes
@app.route('/')
def index():
    """Home page showing skills overview"""
    skills = EmergingSkill.query.filter_by(status='active').order_by(EmergingSkill.urgency_score.desc()).all()
    return render_template('index.html', skills=skills)

@app.route('/skills/<int:skill_id>')
def skill_detail(skill_id):
    """Detailed view of a specific skill"""
    skill = EmergingSkill.query.get_or_404(skill_id)
    # Get learning paths for this skill
    learning_paths = db.session.query(SkillLearningPath, EducationalResource)\
        .join(EducationalResource)\
        .filter(SkillLearningPath.skill_id == skill_id)\
        .filter(EducationalResource.status == 'approved')\
        .order_by(SkillLearningPath.sequence_order)\
        .all()
    
    return render_template('skill_detail.html', skill=skill, learning_paths=learning_paths)

@app.route('/resources/<int:resource_id>')
def resource_detail(resource_id):
    """Detailed view of a specific resource"""
    resource = EducationalResource.query.get_or_404(resource_id)
    quiz_questions = QuizQuestion.query.filter_by(resource_id=resource_id).all()
    assignments = PracticalAssignment.query.filter_by(resource_id=resource_id).all()
    
    return render_template('resource_detail.html', resource=resource, 
                         quiz_questions=quiz_questions, assignments=assignments)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == os.getenv('ADMIN_USERNAME') and password == os.getenv('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            flash('Admin login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    """Admin dashboard"""
    redirect_response = require_admin()
    if redirect_response:
        return redirect_response
    
    # Get summary statistics
    total_skills = EmergingSkill.query.count()
    total_resources = EducationalResource.query.count()
    pending_resources = EducationalResource.query.filter_by(status='pending').count()
    
    return render_template('admin_dashboard.html', 
                         total_skills=total_skills,
                         total_resources=total_resources,
                         pending_resources=pending_resources)

# API Routes
@app.route('/api/skills')
def api_skills():
    """API endpoint to get all active skills"""
    skills = EmergingSkill.query.filter_by(status='active').all()
    return jsonify([skill.to_dict() for skill in skills])

@app.route('/api/skills/<int:skill_id>/resources')
def api_skill_resources(skill_id):
    """API endpoint to get resources for a specific skill"""
    learning_paths = db.session.query(SkillLearningPath, EducationalResource)\
        .join(EducationalResource)\
        .filter(SkillLearningPath.skill_id == skill_id)\
        .filter(EducationalResource.status == 'approved')\
        .order_by(SkillLearningPath.sequence_order)\
        .all()
    
    resources = []
    for path, resource in learning_paths:
        resource_dict = resource.to_dict()
        resource_dict['path_type'] = path.path_type
        resource_dict['sequence_order'] = path.sequence_order
        resource_dict['is_required'] = path.is_required
        resources.append(resource_dict)
    
    return jsonify(resources)

@app.route('/api/resources/<int:resource_id>')
def api_resource_detail(resource_id):
    """API endpoint to get detailed resource information"""
    resource = EducationalResource.query.get_or_404(resource_id)
    return jsonify(resource.to_dict())

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

# Database initialization
def init_db():
    """Initialize database with tables"""
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=9000) 