# 🚀 AI-Horizon Ed: Educational Resource Curation Platform

**🚀 Live Production Platform**: https://ed.theaihorizon.org/

---

## 🚨 **CRITICAL: PRE-DEMO PROTOCOL**

**⚠️ ALWAYS CHECK DATABASE FIRST** - *Learned the Hard Way*

Before ANY demo or presentation:
```bash
# 1. Check database status (should show ~37+ resources)
curl https://ed.theaihorizon.org/api/database/stats

# 2. If empty, run emergency restore
./scripts/emergency_restore.sh

# 3. Verify skill pages have content
# Visit: https://ed.theaihorizon.org/skill/vibe-coding
```

**The educational resources ARE the money shot - without them, you have empty pages!**

---

> **Transform AI workforce intelligence into actionable learning paths for cybersecurity professionals**

AI-Horizon Ed bridges the gap between workforce intelligence and education by automatically discovering and curating educational resources for emerging cybersecurity skills, powered by AI-driven analysis and real-time resource discovery.

## 🌟 Key Features

### 🧠 **AI Workforce Intelligence Integration**
- **Real-time emerging skills detection** from AI impact analysis  
- **Evidence-based urgency scoring** with confidence metrics
- **10+ emerging cybersecurity skills** including AI Security Engineering, MLSecOps, and Prompt Engineering for Security
- **Dual categorization**: NEW AI roles vs. AI-AUGMENTED traditional roles

### 🔍 **Intelligent Resource Discovery**
- **Enhanced Perplexity API integration** with AI-specific search patterns
- **Quality assessment** using Claude/OpenAI APIs (0.0-1.0 scoring)
- **Multi-platform resource discovery**: YouTube, Coursera, GitHub, documentation
- **Smart content filtering** and duplicate prevention

### 📊 **Advanced Database & Analytics**
- **40+ curated resources** with quality scores and metadata
- **Advanced filtering** by category, type, quality, and keywords
- **Real-time statistics** and resource analytics
- **Skill-resource mapping** with relevance scoring

### 💎 **Modern Web Interface**
- **Responsive dashboard** with real-time skill feeds
- **Interactive resource discovery** with loading states
- **Database browser** with advanced search and filtering
- **Professional UI/UX** designed for student engagement

## 🎯 Problem Statement

**The Challenge**: Students are graduating with skills that may become obsolete as AI transforms the cybersecurity workforce. Traditional curricula can't keep pace with emerging AI-driven roles and augmented skill requirements.

**Our Solution**: AI-Horizon Ed transforms workforce intelligence into educational resources, helping students focus their learning on skills that will remain valuable in an AI-enhanced cybersecurity landscape.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- API keys for resource discovery (see Configuration)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-horizon-ed.git
cd ai-horizon-ed/aih_edu

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys

# Run the application
python app.py
```

### Access the Platform
- **Main Dashboard**: `http://localhost:9000/`
- **Database Browser**: `http://localhost:9000/database`
- **API Documentation**: `http://localhost:9000/api/status`

## ⚙️ Configuration

### Required Environment Variables

```bash
# API Keys for Resource Discovery
PERPLEXITY_API_KEY=your_perplexity_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here  # For quality scoring
OPENAI_API_KEY=your_openai_key_here        # Alternative for quality scoring

# Database Configuration
DATABASE_URL=sqlite:///data/aih_edu.db

# Application Settings
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
PORT=9000
MIN_CONTENT_QUALITY=0.7
MAX_SEARCH_RESULTS=20
```

### API Key Setup
1. **Perplexity API**: Get key from [perplexity.ai](https://perplexity.ai)
2. **Anthropic Claude**: Get key from [console.anthropic.com](https://console.anthropic.com)  
3. **OpenAI**: Get key from [platform.openai.com](https://platform.openai.com)

## 📡 API Endpoints

### Skills & Discovery
- `GET /api/skills/emerging` - Get emerging skills with urgency scores
- `GET /api/discover/<skill>` - Discover resources for specific skill
- `GET /api/database/browse` - Browse all stored resources
- `GET /api/database/stats` - Get database statistics

### Filtering & Search
- `GET /api/database/browse?search=<query>&category=<cat>&type=<type>&min_quality=<score>`
- `GET /api/database/skill-resources/<skill_id>` - Get resources for specific skill

## 🏗️ Architecture

### Core Components

```
aih_edu/
├── app.py                     # Main Flask application
├── utils/
│   ├── config.py              # Configuration management
│   └── database.py            # Database operations & schema
├── discover/
│   └── resource_discovery.py  # AI-powered resource discovery engine
├── templates/
│   ├── dashboard.html         # Main interface
│   └── database_browser.html  # Resource browsing interface
└── data/
    └── aih_edu.db            # SQLite database (auto-created)
```

### Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLite with advanced indexing
- **APIs**: Perplexity (search), Anthropic Claude (quality scoring), OpenAI (alternative scoring)
- **Frontend**: Bootstrap 5, modern JavaScript
- **Deployment**: Heroku-ready with Gunicorn

## 🎓 Educational Impact

### Target Audience
- **Cybersecurity students** preparing for AI-enhanced careers
- **Faculty** updating curricula with emerging skills
- **Professionals** transitioning to AI-augmented roles
- **Career counselors** guiding students toward future-proof skills

### Learning Pathways
1. **AI NEW TASKS**: Entirely new roles created by AI adoption
   - Prompt Engineering for Security (67.5% urgency)
   - AI Security Engineering (50.7% urgency)
   - MLSecOps (49.6% urgency)

2. **AI AUGMENTED**: Traditional roles enhanced by AI
   - AI-Enhanced Security Research (59.1% augmentation)
   - AI-Augmented Threat Intelligence (56.4% augmentation)
   - AI-Enhanced Penetration Testing (54.5% augmentation)

## 🔬 Research Foundation

Based on comprehensive analysis of:
- **256 articles** on AI augmentation in cybersecurity
- **112 articles** on AI-driven job creation
- **Evidence-based confidence scoring** from real job market data
- **Industry trend analysis** and workforce predictions

## 🚀 Deployment

### Heroku Deployment

```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set PERPLEXITY_API_KEY=your_key
heroku config:set ANTHROPIC_API_KEY=your_key
heroku config:set SECRET_KEY=your_secret

# Deploy
git push heroku main
```

### Production Considerations
- Use PostgreSQL for production database
- Implement rate limiting for API calls
- Set up monitoring and logging
- Configure CDN for static assets

## 📊 Database Schema

### Core Tables
- **emerging_skills**: AI-identified skills with urgency scores
- **educational_resources**: Curated content with quality ratings
- **skill_resource_mapping**: Links between skills and resources
- **user_preferences**: Personalization settings
- **search_history**: Analytics and usage tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **AI Workforce Intelligence**: Based on comprehensive cybersecurity job market analysis
- **Educational Focus**: Designed to prevent career devastation from skill obsolescence
- **Open Source Community**: Built with modern web technologies and APIs

## 📞 Support

- **Documentation**: See `/docs` directory for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Feature Requests**: Open a GitHub Discussion

---

**🎯 Mission**: Transform workforce intelligence into educational resources that prepare students for the AI-enhanced cybersecurity future.

**🚀 Vision**: Every cybersecurity student graduates with skills that remain valuable as AI transforms the industry.

---

*Built with ❤️ for the cybersecurity education community* 