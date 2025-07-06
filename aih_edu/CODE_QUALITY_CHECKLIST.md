# 🔍 **AI-Horizon Ed Code Quality Checklist**

## 🚨 **CRITICAL PREVENTION GUIDELINES**

### ⚠️ **Pre-Commit Checklist** - *Prevent Runtime Errors*

Before committing any changes, **ALWAYS** verify:

#### **1. Class Method Self-References** ✅
- [ ] All class methods use `self.` prefix for instance variables
- [ ] No bare variable references like `db_manager` (should be `self.db_manager`)
- [ ] All service class dependencies properly injected and referenced

**Common Error Pattern:**
```python
# ❌ WRONG - Will cause NameError
def some_method(self):
    db_manager.get_data()  # Missing self.
    
# ✅ CORRECT  
def some_method(self):
    self.db_manager.get_data()  # Proper instance reference
```

#### **2. API Endpoint Testing** ✅
- [ ] All `/api/` endpoints return 200 status codes
- [ ] Core endpoints tested: `/api/resources`, `/api/skills/emerging`, `/api/database/stats`
- [ ] Skill detail pages load without 500 errors
- [ ] Quiz functionality works end-to-end

#### **3. Database Operations** ✅
- [ ] All database queries handle both SQLite and PostgreSQL
- [ ] JSON fields properly serialized/deserialized
- [ ] Foreign key relationships maintained
- [ ] Connection management uses context managers

#### **4. Error Handling** ✅
- [ ] Try/catch blocks around external API calls
- [ ] Graceful degradation when AI services fail
- [ ] Proper logging for debugging
- [ ] User-friendly error messages

---

## 🛠️ **TESTING PROTOCOL**

### **Local Testing Commands:**
```bash
# 1. Database Health Check
curl -s http://127.0.0.1:9000/api/database/stats | jq

# 2. Resources API Test  
curl -s http://127.0.0.1:9000/api/resources | head -20

# 3. Skill Detail Page Test
curl -s http://127.0.0.1:9000/skill/ai-enhanced-siem | grep -A 5 "Data to Defense"

# 4. Quiz System Test
curl -X POST "http://127.0.0.1:9000/api/quiz/20/grade" \
  -H "Content-Type: application/json" \
  -d '{"answers":["test answer"]}' | jq

# 5. Emergency Restore Test
curl -s http://127.0.0.1:9000/emergency-restore | jq
```

### **Automated Quality Check Script:**
```bash
# Create quality_check.py
python -c "
import requests
import sys

tests = [
    ('Database Stats', 'http://127.0.0.1:9000/api/database/stats'),
    ('Resources API', 'http://127.0.0.1:9000/api/resources'), 
    ('Skills API', 'http://127.0.0.1:9000/api/skills/emerging'),
    ('Skill Detail', 'http://127.0.0.1:9000/skill/ai-enhanced-siem')
]

all_passed = True
for name, url in tests:
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f'✅ {name}: PASSED')
        else:
            print(f'❌ {name}: FAILED ({response.status_code})')
            all_passed = False
    except Exception as e:
        print(f'❌ {name}: ERROR ({e})')
        all_passed = False

if all_passed:
    print('🎉 All tests passed! Code is ready for deployment.')
    sys.exit(0)
else:
    print('🚨 Some tests failed! Please fix before deploying.')
    sys.exit(1)
"
```

---

## 🔧 **CODE REVIEW GUIDELINES**

### **1. Class Architecture Review:**
- [ ] Services properly injected via constructor
- [ ] No global variable dependencies
- [ ] Clear separation of concerns
- [ ] Consistent error handling patterns

### **2. Database Integration Review:**
- [ ] All queries parameterized (SQL injection prevention)
- [ ] Connection pooling used appropriately 
- [ ] Transactions used for multi-step operations
- [ ] Proper indexing on frequently queried columns

### **3. API Design Review:**
- [ ] RESTful endpoint naming conventions
- [ ] Consistent JSON response formats
- [ ] Proper HTTP status codes
- [ ] Input validation and sanitization

### **4. Frontend Integration Review:**
- [ ] Graceful loading states
- [ ] Error message handling
- [ ] Responsive design maintained
- [ ] Accessibility considerations

---

## 🚀 **DEPLOYMENT SAFETY PROTOCOL**

### **Pre-Deployment Checklist:**
1. [ ] Run full quality check script
2. [ ] Test all skill detail pages
3. [ ] Verify quiz generation and grading
4. [ ] Check database migration compatibility
5. [ ] Confirm AI API integration working
6. [ ] Test emergency restore functionality

### **Post-Deployment Monitoring:**
1. [ ] Monitor application logs for errors
2. [ ] Check response times for all endpoints
3. [ ] Verify database performance metrics
4. [ ] Test core user workflows
5. [ ] Monitor AI API usage and costs

---

## 📝 **COMMON ISSUE PATTERNS & SOLUTIONS**

### **Issue 1: "NameError: name 'db_manager' is not defined"**
**Root Cause:** Bare variable reference in class method
**Solution:** Use `self.db_manager` instead
**Prevention:** Search for `(?<!self\.)db_manager\.` before commits

### **Issue 2: "AttributeError: 'list' object has no attribute 'get'"**
**Root Cause:** Type mismatch in data structures
**Solution:** Add type checking and normalization
**Prevention:** Validate data formats at API boundaries

### **Issue 3: Database connection errors**
**Root Cause:** Connection not properly closed or managed
**Solution:** Use context managers (`with` statements)
**Prevention:** Standardize database access patterns

### **Issue 4: Quiz grading failures**
**Root Cause:** AI API timeouts or format mismatches
**Solution:** Implement fallback grading with timeout handling
**Prevention:** Test with various answer formats and scenarios

---

## 🎯 **AUTOMATED PREVENTION TOOLS**

### **Pre-commit Hook (Git):**
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Running code quality checks..."

# Check for bare db_manager references
if grep -r "(?<!self\.)db_manager\." aih_edu/ --include="*.py"; then
    echo "❌ Found bare db_manager references. Use self.db_manager instead."
    exit 1
fi

# Check for missing self in class methods
if grep -r "def.*self.*:" aih_edu/ --include="*.py" -A 10 | grep -v "self\." | grep "db_manager\|analyzer\|config"; then
    echo "⚠️  Potential missing self reference detected."
fi

echo "✅ Pre-commit checks passed!"
```

### **Linting Configuration (pylint/flake8):**
```ini
# .pylintrc
[MESSAGES CONTROL]
enable=unused-variable,undefined-variable,attribute-defined-outside-init

[VARIABLES]
callbacks=self
```

---

## 📚 **LEARNING FROM THIS INCIDENT**

### **What Went Wrong:**
1. **Incomplete Refactoring**: Service classes weren't properly updated
2. **Missing Tests**: No integration tests caught the issues
3. **Deployment Without Verification**: Code went live without testing

### **What We Learned:**
1. **Always test skill detail pages** before deployment
2. **Use automated quality checks** in CI/CD pipeline
3. **Implement comprehensive error logging** for faster debugging
4. **Create fallback mechanisms** for critical functionality

### **Process Improvements:**
1. ✅ **Mandatory Testing**: Never deploy without running quality checks
2. ✅ **Code Review**: Focus on class method patterns and dependencies
3. ✅ **Staged Deployment**: Test locally → staging → production
4. ✅ **Monitoring**: Real-time alerts for application errors

---

## 🎉 **SUCCESS METRICS**

We know the platform is healthy when:
- ✅ All skill detail pages load in <2 seconds
- ✅ Quiz grading success rate >90%  
- ✅ API response times <500ms average
- ✅ Database operations complete without errors
- ✅ AI content generation succeeds >85% of the time

**Remember: Quality is not an accident - it's the result of intelligent effort!** 🚀 