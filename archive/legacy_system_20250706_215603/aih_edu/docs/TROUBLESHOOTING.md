# AI-Horizon Ed Troubleshooting Guide

## Critical Development Workflow Issues

### ⚠️ Server Restart Required After Code Changes

**Issue**: Methods/functions exist in code files but server reports "object has no attribute" errors.

**Root Cause**: Flask development server caches imported modules. When you add new methods to existing classes, the running server continues using the old cached version.

**Solution**: 
```bash
# Kill any running processes on port 9000
pkill -f "python app.py" 2>/dev/null || true

# Wait for processes to terminate
sleep 2

# Start fresh server instance
cd aih_edu && python app.py --debug --port 9000
```

**Prevention**: Always restart the development server after:
- Adding new methods to existing classes
- Modifying class structure
- Changing import statements
- Adding new files to the project

---

## Common Issues and Solutions

### Database-Related Issues

#### Learning Content Generation Failing
**Symptoms**: 
- GPT-4 successfully analyzes content
- Server logs show `'DatabaseManager' object has no attribute 'store_learning_content'`
- Content generation appears to work but doesn't save

**Diagnosis**:
1. Check if methods exist in files: `grep -n "def store_learning_content" utils/database.py`
2. Check server startup logs for any import errors
3. Verify server is using updated code by checking modification timestamps

**Solution**: Restart the server to load updated code.

#### Resource Questions/Exercises Return 404
**Symptoms**: API endpoints return 404 for `/api/resource/{id}/questions`

**Common Causes**:
1. Learning content not generated yet
2. Database missing learning_content entries
3. Incorrect resource ID

**Diagnosis**:
```bash
# Check database for learning content
sqlite3 data/aih_edu.db "SELECT COUNT(*) FROM learning_content;"

# Check specific resource
curl -s "http://localhost:9000/api/resource/41/questions"
```

### Content Generation Issues

#### GPT-4 Analysis Working But Storage Failing
**Symptoms**: Server logs show successful GPT-4 responses but errors during storage

**Solution**: 
1. Verify `store_learning_content` method exists in DatabaseManager
2. Restart server to load updated code
3. Check database permissions and file paths

#### Transcript Extraction Failures
**Symptoms**: YouTube transcript API rate limiting errors

**Workaround**: Content analyzer falls back to video descriptions when transcripts fail.

### Server Management

#### Port Already in Use
**Error**: `Address already in use` when starting server

**Solution**:
```bash
# Find and kill processes using port 9000
lsof -ti:9000 | xargs kill -9

# Or use pkill
pkill -f "python app.py"
```

#### Module Not Found Errors
**Error**: `ModuleNotFoundError: No module named 'utils'`

**Cause**: Running server from wrong directory

**Solution**: Always run from `aih_edu` directory:
```bash
cd aih_edu && python app.py --debug --port 9000
```

---

## Development Best Practices

### Code Changes Workflow
1. **Make code changes**
2. **Always restart server** - Don't assume changes are automatically loaded
3. **Test the specific functionality** that was changed
4. **Check server logs** for any errors during startup

### Testing After Changes
```bash
# Quick health check
curl -s "http://localhost:9000/api/status"

# Test specific functionality
curl -s "http://localhost:9000/api/resource/41/questions"

# Check database stats
curl -s "http://localhost:9000/api/database/stats"
```

### Debugging Steps
1. **Check if methods exist in files**: Use grep to verify code is actually saved
2. **Restart server**: Most "missing method" errors are solved by this
3. **Check imports**: Verify all required modules are properly imported
4. **Test endpoints**: Use curl or browser to test specific functionality
5. **Review logs**: Check both server startup and runtime logs

---

## Emergency Recovery

### Complete System Reset
If issues persist, try a complete reset:

```bash
# Kill all Python processes
pkill -f python

# Clear any cached Python files
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete

# Restart fresh
cd aih_edu && python app.py --debug --port 9000
```

### Backup and Restore Database
```bash
# Backup current database
cp data/aih_edu.db data/aih_edu_backup_$(date +%Y%m%d_%H%M%S).db

# If needed, restore from backup
# cp data/aih_edu_backup_TIMESTAMP.db data/aih_edu.db
```

---

## Monitoring and Maintenance

### Regular Health Checks
- Verify all API endpoints respond correctly
- Check database integrity
- Monitor server performance and memory usage
- Ensure learning content generation is working

### Log Analysis
Key log patterns to monitor:
- `ERROR` - Any error messages
- `'object has no attribute'` - Indicates code caching issues
- `Address already in use` - Port conflicts
- GPT-4 API responses and content generation success rates

---

*Last Updated: July 4, 2025*
*Key Lesson: Server restart is essential after code changes to avoid cached module issues* 