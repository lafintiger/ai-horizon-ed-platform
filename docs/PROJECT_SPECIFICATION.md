# AI-Horizon Ed: Intelligent Educational Resource Curation Platform
## Project Specification v2.0

### Project Overview

**AI-Horizon Ed** bridges workforce intelligence and education by taking insights from the main AI-Horizon cybersecurity intelligence platform and automatically curating educational resources to prepare students for emerging skill requirements.

### Core Mission
Transform workforce intelligence into actionable learning paths by identifying future-critical skills from AI-Horizon analysis and automatically discovering relevant educational content (YouTube videos, courses, tools, software) to help students prepare for the evolving cybersecurity landscape.

---

## 1. INTEGRATION ARCHITECTURE

### 1.1 Data Flow
```
Main AI-Horizon Platform → Skills Intelligence → AI-Horizon Ed → Educational Resources
     ↓                          ↓                    ↓              ↓
Job Market Analysis    →  Emerging Skills List  →  Resource Search  →  Curated Learning Paths
Trend Analysis         →  Skill Gap Identification → Content Discovery → Student Dashboard
Workforce Predictions  →  Future Requirements   →  Tool Recommendations → Progress Tracking
```

### 1.2 Technology Stack
- **Backend**: Python 3.8+ with Flask web framework
- **Database**: SQLite for development (inheriting from existing aih_edu structure)
- **Frontend**: HTML5, CSS3, JavaScript (inherit main AI-Horizon styling)
- **Integration**: Direct database/API integration with main AI-Horizon platform
- **Search APIs**: YouTube Data API, Course aggregators, GitHub API for tools
- **Deployment**: Separate Heroku app that connects to main platform

### 1.3 Existing Code Structure (Already Built)
```
aih_edu/
├── utils/
│   ├── config.py                 # ✅ Configuration with API keys, skill categories
│   └── database.py               # ✅ Educational resources database schema
├── __init__.py                   # ✅ Package initialization
└── docs/
    └── PROJECT_SPECIFICATION.md  # 📝 This specification
```

---

## 2. SKILLS INTELLIGENCE INTEGRATION

### 2.1 Data Sources from Main AI-Horizon Platform
**Pull from main platform's analysis results:**

```python
# Integration points with main AI-Horizon
MAIN_PLATFORM_SOURCES = {
    'trend_analysis': 'scripts/analysis/trend_analysis.py results',
    'ai_adoption_predictions': 'scripts/analysis/ai_adoption_predictions.py results', 
    'skills_gap_analysis': 'Custom analysis of job postings for emerging skills',
    'category_narratives': 'Comprehensive category analysis results',
    'job_market_sentiment': 'Real-time sentiment analysis of cybersecurity roles'
}
```

### 2.2 Skill Extraction Pipeline
```python
# Extract emerging skills from main platform findings
class SkillIntelligenceExtractor:
    def extract_emerging_skills(self) -> List[str]:
        """Extract list of emerging skills from main platform analysis"""
        # Pull from main AI-Horizon database analysis_results table
        # Parse trend_analysis for "emerging" skills
        # Parse ai_adoption_predictions for "future-critical" competencies
        # Return prioritized list of skills for educational resource search
        
    def identify_skill_gaps(self) -> Dict[str, float]:
        """Identify skills with highest demand vs. availability gap"""
        # Analyze job market data for supply/demand mismatches
        # Return skill gaps with urgency scores
        
    def get_skill_priorities(self) -> List[Dict]:
        """Get prioritized skills with context and urgency"""
        # Combine emerging skills + skill gaps + trend momentum
        # Return structured skill priority list for resource curation
```

---

## 3. EDUCATIONAL RESOURCE DISCOVERY

### 3.1 Automated Resource Search
**Based on emerging skills identified by main platform:**

```python
# Resource discovery for each emerging skill
class ResourceDiscoveryEngine:
    def search_youtube_content(self, skill: str) -> List[Dict]:
        """Search YouTube for educational videos on emerging skill"""
        # YouTube Data API search for tutorials, courses
        # Filter for quality content (view count, ratings, recency)
        # Extract metadata (duration, difficulty, creator credibility)
        
    def search_online_courses(self, skill: str) -> List[Dict]:
        """Find online courses and certifications"""
        # Search Coursera, edX, Udemy APIs for relevant courses
        # Prioritize industry-recognized certifications
        # Include free and paid options
        
    def discover_tools_software(self, skill: str) -> List[Dict]:
        """Find relevant tools and software for skill development"""
        # GitHub API for popular repositories and tools
        # Software discovery for hands-on practice platforms
        # Include both free and enterprise tools
        
    def curate_documentation(self, skill: str) -> List[Dict]:
        """Find official documentation and technical resources"""
        # Search for official docs, whitepapers, technical guides
        # Prioritize vendor documentation and industry standards
```

### 3.2 Content Quality Assessment
**Inherit quality ranking from main platform:**

```python
# Reuse main platform's quality assessment approach
from scripts.analysis.implement_quality_ranking import DocumentQualityRanker

class EducationalContentRanker(DocumentQualityRanker):
    def rank_educational_content(self, content: Dict) -> float:
        """Rank educational content with learning-specific criteria"""
        # Adapt main platform's quality scoring for educational context
        # Consider: recency, credibility, comprehensiveness, engagement
        # Return 0.0-1.0 quality score for educational resources
```

---

## 4. CORE FEATURES

### 4.1 Skills-Based Dashboard
**Visual Design**: Inherit from main AI-Horizon dashboard styling

**Components**:
- **Emerging Skills Feed**: Real-time list from main platform analysis
- **Skill Priority Matrix**: Visual grid of urgency vs. availability
- **Learning Path Generator**: Auto-generated paths for priority skills
- **Resource Discovery**: Curated content for each emerging skill
- **Progress Tracking**: Individual learning advancement

### 4.2 Automated Learning Path Creation
```python
# Auto-generate learning paths from workforce intelligence
class LearningPathGenerator:
    def create_skill_pathway(self, skill: str, user_level: str) -> Dict:
        """Generate comprehensive learning path for emerging skill"""
        # 1. Foundation resources (beginner concepts)
        # 2. Practical tutorials (hands-on practice)  
        # 3. Advanced applications (real-world scenarios)
        # 4. Tools and software (practical implementation)
        # 5. Certification paths (credential achievement)
        
    def prioritize_learning_sequence(self, skills_list: List[str]) -> List[Dict]:
        """Order skills by learning sequence and urgency"""
        # Consider prerequisite relationships
        # Factor in main platform's urgency scoring
        # Create optimal learning sequence for career preparation
```

### 4.3 Resource Curation Interface
- **Skill-Specific Collections**: Organized by emerging skills
- **Multi-Format Resources**: Videos, courses, tools, documentation
- **Quality Indicators**: Inherited scoring from main platform
- **Freshness Tracking**: Recently updated content prioritization
- **Community Curation**: User ratings and feedback

---

## 5. DATABASE SCHEMA INTEGRATION

### 5.1 Skills Intelligence Tables (New)
```sql
-- Skills identified from main AI-Horizon platform
CREATE TABLE emerging_skills (
    id INTEGER PRIMARY KEY,
    skill_name TEXT NOT NULL,
    category TEXT NOT NULL,  -- From main platform categories
    urgency_score REAL DEFAULT 0.0,  -- From main platform analysis
    demand_trend TEXT,  -- 'rising', 'stable', 'critical'
    source_analysis TEXT,  -- Which main platform analysis identified this
    identified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    job_market_data TEXT,  -- JSON with supporting data from main platform
    related_skills TEXT  -- JSON array of related/prerequisite skills
);

-- Link between main platform findings and educational resources
CREATE TABLE skill_resource_mapping (
    id INTEGER PRIMARY KEY,
    skill_id INTEGER REFERENCES emerging_skills(id),
    resource_id INTEGER REFERENCES educational_resources(id),
    relevance_score REAL DEFAULT 0.0,
    resource_type_for_skill TEXT,  -- 'foundation', 'practical', 'advanced', 'certification'
    auto_discovered BOOLEAN DEFAULT 1,  -- Whether automatically found or manually curated
    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Existing Educational Resources Schema (Already Built)
**Reuse existing schema from `aih_edu/utils/database.py`:**
- `educational_resources` table ✅
- `user_preferences` table ✅  
- `learning_paths` table ✅
- `user_progress` table ✅
- `resource_collections` table ✅

---

## 6. API INTEGRATION

### 6.1 Main Platform Integration APIs
```python
# Connect to main AI-Horizon platform
class MainPlatformConnector:
    def get_latest_trend_analysis(self) -> Dict:
        """Fetch latest trend analysis from main platform"""
        # Connect to main platform database
        # Query analysis_results for trend_analysis type
        # Return latest findings with emerging skills data
        
    def get_skills_predictions(self) -> Dict:
        """Get AI adoption predictions affecting skills"""
        # Fetch ai_adoption_predictions results
        # Extract skills impact data
        # Return skills transformation predictions
        
    def monitor_analysis_updates(self) -> None:
        """Monitor main platform for new analysis results"""
        # Set up periodic checks for new analysis results
        # Trigger educational resource discovery when new skills emerge
        # Update emerging_skills table with latest intelligence
```

### 6.2 Educational Resource Discovery APIs
```python
# External APIs for content discovery
@app.route('/api/discover/youtube/<skill>')
def discover_youtube_content(skill):
    """API to discover YouTube content for a specific skill"""
    # Use YouTube Data API to search for educational content
    # Return curated list of videos with quality assessment
    
@app.route('/api/discover/courses/<skill>')
def discover_courses(skill):
    """API to discover online courses for emerging skill"""
    # Search course platforms for relevant educational content
    # Return structured course data with enrollment links

@app.route('/api/discover/tools/<skill>')  
def discover_tools(skill):
    """API to discover tools and software for skill development"""
    # Search GitHub, tool directories for relevant software
    # Return curated list of development tools and platforms
```

---

## 7. USER INTERFACE DESIGN

### 7.1 Visual Theme (Inherit from Main AI-Horizon)
- **Color Scheme**: Same blues and purples as main platform
- **Typography**: 'Segoe UI' font family consistency
- **Layout**: Card-based responsive design
- **Navigation**: Simplified for educational focus

### 7.2 Key Pages
1. **Skills Intelligence Dashboard** (`/`) - Emerging skills from main platform
2. **Resource Discovery** (`/discover/<skill>`) - Curated content for specific skills
3. **Learning Paths** (`/paths`) - Auto-generated learning sequences  
4. **My Progress** (`/progress`) - Personal learning tracking
5. **Skills Explorer** (`/skills`) - Interactive skill browsing
6. **Resource Collections** (`/collections`) - Curated content libraries

### 7.3 Dashboard Components
```html
<!-- Skills Intelligence Dashboard -->
<div class="skills-dashboard">
    <div class="emerging-skills-feed">
        <!-- Real-time feed from main platform analysis -->
        <h2>🔥 Emerging Skills (Live from AI-Horizon Intelligence)</h2>
        <div class="skill-card" data-urgency="critical">
            <h3>Zero Trust Architecture</h3>
            <p>Identified in latest trend analysis • 89% demand increase</p>
            <a href="/discover/zero-trust">Find Learning Resources →</a>
        </div>
    </div>
    
    <div class="learning-paths">
        <!-- Auto-generated learning paths -->
        <h2>📚 Recommended Learning Paths</h2>
        <div class="path-card">
            <h3>AI-Enhanced Security Operations</h3>
            <p>5 resources • 12 hours • Based on job market analysis</p>
            <div class="progress-bar">40% complete</div>
        </div>
    </div>
</div>
```

---

## 8. IMPLEMENTATION ROADMAP

### Phase 1: Integration Foundation (Week 1)
- ✅ **Already Built**: Database schema, configuration, project structure
- 🔄 **Setup**: Main platform database connection and API integration
- 🔄 **Build**: Skills intelligence extraction from main platform results

### Phase 2: Resource Discovery Engine (Week 2)
- 🔄 **Build**: YouTube, course, and tool discovery APIs
- 🔄 **Build**: Content quality assessment and ranking system
- 🔄 **Build**: Automated resource curation pipeline

### Phase 3: Web Interface (Week 3)
- 🔄 **Build**: Skills dashboard with main platform integration
- 🔄 **Build**: Resource discovery and browsing interface  
- 🔄 **Build**: Learning path generation and tracking

### Phase 4: Polish & Automation (Week 4)
- 🔄 **Build**: Automated skill monitoring and resource updates
- 🔄 **Build**: User progress tracking and recommendations
- 🔄 **Test**: End-to-end integration with main platform

---

## 9. SUCCESS METRICS

### 9.1 Intelligence Integration
- Skills extraction accuracy from main platform (>90%)
- Resource discovery relevance for emerging skills (>85%)
- Learning path completion rates (>60%)

### 9.2 Educational Effectiveness  
- Students finding relevant resources for priority skills
- Career preparation alignment with industry demand
- Time from skill identification to resource availability (<24 hours)

---

## 10. TECHNICAL ARCHITECTURE

### 10.1 Deployment
- **Separate Heroku App**: Independent deployment connected to main platform
- **Database Sync**: Periodic sync with main AI-Horizon database for latest intelligence
- **API Keys**: YouTube, course platforms, GitHub for resource discovery
- **Port**: 9000 (from existing config.py)

### 10.2 Environment Variables
```bash
# Educational platform configuration
FLASK_ENV=development
DATABASE_URL=sqlite:///data/aih_edu.db
PORT=9000

# Main platform integration
MAIN_PLATFORM_DB_URL=connection_to_main_ai_horizon_db
SYNC_INTERVAL_HOURS=6

# Resource discovery APIs
YOUTUBE_API_KEY=your_youtube_key
GITHUB_API_KEY=your_github_key
```

---

*This specification describes how AI-Horizon Ed transforms workforce intelligence from the main platform into curated educational resources, creating a bridge between "what skills are emerging" and "how to learn those skills."* 