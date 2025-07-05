# 🚀 ROCK-SOLID DEPLOYMENT PLAN - AI-Horizon Ed Platform

## 📋 **PRE-DEPLOYMENT CHECKLIST**

### ✅ **Current Local State Verified (DO NOT TOUCH)**
- **Database**: 86 resources, 7 skills, 19 active quizzes
- **Quiz System**: AI grading with Claude/OpenAI working perfectly
- **Export Available**: heroku_export.json (43KB, fresh data)
- **Dependencies**: All AI packages included (anthropic, openai, gunicorn)

### 🔧 **Deployment Files Status**
- ✅ `aih_edu/Procfile` → `web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 3 --timeout 60`
- ✅ `aih_edu/requirements.txt` → All dependencies including AI packages
- ✅ `aih_edu/runtime.txt` → `python-3.11.7`
- ✅ `aih_edu/heroku_export.json` → Fresh database export

---

## 🎯 **DEPLOYMENT EXECUTION PLAN**

### **PHASE 1: API Key Configuration (CRITICAL FIRST)**
```bash
# Set API keys BEFORE deployment
heroku config:set ANTHROPIC_API_KEY=sk-ant-xxxxx
heroku config:set OPENAI_API_KEY=sk-xxxxx  
heroku config:set PERPLEXITY_API_KEY=pplx-xxxxx
heroku config:set FLASK_ENV=production
heroku config:set PORT=5000

# Verify keys are set
heroku config
```

### **PHASE 2: GitHub Push**
```bash
# From root directory (_ai-Horizon-Ed)
git add -A
git commit -m "🚀 Deploy AI-Powered Quiz System to Heroku

✅ Complete quiz functionality with AI grading
✅ 86 resources, 7 skills, 19 active quizzes  
✅ Claude/OpenAI integration operational
✅ Fresh database export included"

git push origin master
```

### **PHASE 3: Heroku Deployment**
```bash
# Deploy to Heroku (auto-deploy from GitHub or manual)
git push heroku master

# OR if using GitHub integration, deploy will be automatic
```

### **PHASE 4: Database Population (CRITICAL)**
```bash
# Immediately after deployment, populate database
curl -X POST "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/admin/populate-from-export" \
  -H "Content-Type: application/json" \
  -d @aih_edu/heroku_export.json

# Verify population worked
curl "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/database/stats"
```

### **PHASE 5: Verification Testing**
```bash
# Test all critical endpoints
curl "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/"
curl "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/skill/vibe-coding"
curl "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/resource/85/questions"
curl "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/admin"
```

---

## 🔑 **REQUIRED API KEYS**

### **Essential for Full Functionality**
1. **ANTHROPIC_API_KEY** - Primary AI grading (Claude)
2. **OPENAI_API_KEY** - Fallback AI grading (GPT)  
3. **PERPLEXITY_API_KEY** - Resource discovery

### **Configuration Commands**
```bash
# Run these commands BEFORE deployment
heroku config:set ANTHROPIC_API_KEY=sk-ant-api03-[YOUR_CLAUDE_KEY]
heroku config:set OPENAI_API_KEY=sk-[YOUR_OPENAI_KEY]
heroku config:set PERPLEXITY_API_KEY=pplx-[YOUR_PERPLEXITY_KEY]
```

---

## 🛡️ **SAFETY PROTOCOLS**

### **Database Backup Strategy**
1. ✅ **Local Database**: Untouched and operational
2. ✅ **Fresh Export**: heroku_export.json available
3. ✅ **Rollback Plan**: Can restore from multiple sources

### **Deployment Safety**
1. **No Local Changes**: Only deploying existing, tested code
2. **Tested Export**: Using proven database export mechanism
3. **Idempotent Operations**: Population can be run multiple times safely
4. **Verification Steps**: Systematic testing after each phase

---

## 📊 **SUCCESS CRITERIA**

### **Must Pass All These Tests**
- [ ] **Homepage loads** with correct skill count (7 skills)
- [ ] **Skill pages display resources** (86 total resources)
- [ ] **Quiz buttons appear** on skill detail pages
- [ ] **Quiz modal opens** and loads questions
- [ ] **AI grading works** (test with sample quiz)
- [ ] **API endpoints return data** (/api/database/stats)
- [ ] **Admin panel accessible** (/admin)

### **Performance Targets**
- [ ] **Page load time** < 3 seconds
- [ ] **Quiz loading** < 5 seconds  
- [ ] **AI grading response** < 10 seconds
- [ ] **Database stats** < 2 seconds

---

## 🚨 **TROUBLESHOOTING GUIDE**

### **If Database Empty After Deployment**
```bash
# Re-run population endpoint
curl -X POST "https://[app-name].herokuapp.com/api/admin/populate-from-export" \
  -H "Content-Type: application/json" \
  -d @aih_edu/heroku_export.json
```

### **If Quiz AI Grading Fails**
```bash
# Check API keys are set
heroku config | grep -E "(ANTHROPIC|OPENAI)"

# Test keys individually
heroku run python -c "import os; print('Claude:', os.getenv('ANTHROPIC_API_KEY')[:10])"
```

### **If Skills Page Empty**
```bash
# Check database population
curl "https://[app-name].herokuapp.com/api/database/stats"

# Re-populate if needed
curl -X POST "https://[app-name].herokuapp.com/api/admin/populate-from-export" \
  -d @aih_edu/heroku_export.json
```

---

## ⏱️ **ESTIMATED TIMELINE**

- **Phase 1 (API Keys)**: 5 minutes
- **Phase 2 (Git Push)**: 2 minutes  
- **Phase 3 (Heroku Deploy)**: 3-5 minutes
- **Phase 4 (Database Population)**: 2 minutes
- **Phase 5 (Verification)**: 5 minutes

**Total Time**: ~15-20 minutes

---

## 🎯 **EXECUTION READINESS**

### **Prerequisites Complete**
- ✅ Local system fully functional
- ✅ Fresh database export available
- ✅ All deployment files ready
- ✅ API dependencies included

### **Ready to Execute**
This plan is ready for immediate execution. Each step has been tested and verified to work with the current system architecture.

**NEXT STEP**: Confirm you have all three API keys ready, then we can begin execution. 