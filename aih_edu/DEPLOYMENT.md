# 🚀 Deployment Guide: AI-Horizon Ed

This guide will walk you through deploying AI-Horizon Ed to GitHub and Heroku for public access.

## 📋 Prerequisites

- Git installed on your system
- GitHub account
- Heroku account (free tier available)
- Heroku CLI installed

## 🐙 GitHub Repository Setup

### 1. Create GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Repository name: `ai-horizon-ed` (or your preferred name)
3. Description: `Transform AI workforce intelligence into educational resources`
4. Make it **Public** (recommended for educational use)
5. **Don't** initialize with README (we already have one)

### 2. Connect Local Repository to GitHub

```bash
# Navigate to your project directory
cd /path/to/ai-horizon-ed/aih_edu

# Initialize git repository (if not already done)
git init

# Add all files to git
git add .

# Create initial commit
git commit -m "Initial commit: AI-Horizon Ed platform with resource discovery engine"

# Add GitHub remote (replace with your GitHub username/repo)
git remote add origin https://github.com/YOUR_USERNAME/ai-horizon-ed.git

# Push to GitHub
git push -u origin main
```

### 3. Verify Repository

- Check that all files are uploaded to GitHub
- Verify the README.md displays properly
- Ensure `.env` file is **NOT** uploaded (protected by .gitignore)

## 🚀 Heroku Deployment

### 1. Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Windows
# Download from https://devcenter.heroku.com/articles/heroku-cli

# Ubuntu/Debian
sudo snap install --classic heroku
```

### 2. Login to Heroku

```bash
heroku login
```

### 3. Create Heroku Application

```bash
# Create new Heroku app (replace with your preferred name)
heroku create ai-horizon-ed-demo

# Alternative: Let Heroku generate a name
heroku create
```

### 4. Configure Environment Variables

Set up your API keys and configuration on Heroku:

```bash
# Required API Keys
heroku config:set PERPLEXITY_API_KEY="your_perplexity_key_here"
heroku config:set ANTHROPIC_API_KEY="your_anthropic_key_here"
heroku config:set OPENAI_API_KEY="your_openai_key_here"

# Application Configuration
heroku config:set SECRET_KEY="your-secret-key-for-production"
heroku config:set FLASK_ENV="production"
heroku config:set MIN_CONTENT_QUALITY="0.7"
heroku config:set MAX_SEARCH_RESULTS="20"

# Database (will be auto-configured by Heroku)
# heroku config:set DATABASE_URL="..." # Not needed for SQLite
```

### 5. Deploy to Heroku

```bash
# Deploy the application
git push heroku main

# Open the deployed application
heroku open
```

### 6. Monitor Deployment

```bash
# View application logs
heroku logs --tail

# Check application status
heroku ps

# Restart if needed
heroku restart
```

## 🗄️ Database Configuration

### For Development (SQLite - Current Setup)
- Uses local SQLite database
- Automatically creates `data/aih_edu.db`
- Perfect for development and small deployments

### For Production (PostgreSQL - Recommended)

```bash
# Add PostgreSQL addon
heroku addons:create heroku-postgresql:mini

# Update database configuration
heroku config:set DATABASE_URL="postgres://..."
```

## 🔧 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `PERPLEXITY_API_KEY` | ✅ | Resource discovery search | `pplx-...` |
| `ANTHROPIC_API_KEY` | ✅ | Content quality scoring | `sk-ant-...` |
| `OPENAI_API_KEY` | ⚠️ | Alternative quality scoring | `sk-...` |
| `SECRET_KEY` | ✅ | Flask session security | `your-secret-key` |
| `FLASK_ENV` | ✅ | Environment mode | `production` |
| `DATABASE_URL` | ⚠️ | Database connection | Auto-set by Heroku |
| `MIN_CONTENT_QUALITY` | ❌ | Quality threshold | `0.7` |
| `MAX_SEARCH_RESULTS` | ❌ | Search result limit | `20` |

## 🔍 Verification Checklist

### After GitHub Push:
- [ ] Repository is public and accessible
- [ ] README.md displays correctly with emojis
- [ ] No sensitive files (`.env`, `*.db`) in repository
- [ ] All source code is present

### After Heroku Deployment:
- [ ] Application starts without errors (`heroku logs`)
- [ ] Environment variables are set (`heroku config`)
- [ ] Homepage loads at your Heroku URL
- [ ] Database browser accessible at `/database`
- [ ] Resource discovery works (test with a skill)
- [ ] API endpoints respond correctly

## 🧪 Testing the Deployment

1. **Homepage Test**: Visit `https://your-app.herokuapp.com/`
2. **Database Browser**: Visit `https://your-app.herokuapp.com/database`
3. **API Test**: Visit `https://your-app.herokuapp.com/api/status`
4. **Skills API**: Visit `https://your-app.herokuapp.com/api/skills/emerging`
5. **Resource Discovery**: Click "Discover Resources" on a skill

## 🛠️ Troubleshooting

### Common Issues:

**App won't start:**
```bash
# Check logs for errors
heroku logs --tail

# Common fixes:
heroku restart
heroku ps:scale web=1
```

**Missing environment variables:**
```bash
# Check current config
heroku config

# Add missing variables
heroku config:set VARIABLE_NAME="value"
```

**Database issues:**
```bash
# For SQLite (development)
# Database will be created automatically

# For PostgreSQL (production)
heroku addons:create heroku-postgresql:mini
```

**Build failures:**
```bash
# Check Python version
cat runtime.txt

# Verify requirements.txt
cat requirements.txt
```

## 🔄 Updates and Maintenance

### Deploying Updates:

```bash
# Make your changes
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin main

# Deploy to Heroku
git push heroku main
```

### Monitoring:

```bash
# View logs
heroku logs --tail

# Check metrics
heroku metrics

# Scale if needed
heroku ps:scale web=2
```

## 🎯 Custom Domain (Optional)

```bash
# Add custom domain
heroku domains:add www.your-domain.com

# Configure DNS with your domain provider
# Point CNAME to your-app.herokuapp.com
```

## 📞 Support

- **Heroku Issues**: Check [Heroku Dev Center](https://devcenter.heroku.com/)
- **GitHub Issues**: Use repository's Issues tab
- **Application Logs**: `heroku logs --tail`

---

🎉 **Congratulations!** Your AI-Horizon Ed platform is now live and helping students worldwide discover resources for emerging cybersecurity skills!

**Share your deployment:** Once live, share the URL with students, faculty, and the cybersecurity education community. 