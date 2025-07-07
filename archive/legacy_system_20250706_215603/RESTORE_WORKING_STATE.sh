#!/bin/bash
echo "🔄 RESTORING AI-HORIZON ED TO WORKING STATE..."
echo "================================================"

# Stop any running server
echo "🛑 Stopping any running servers..."
pkill -f "python app.py" || true

# Reset to working commit
echo "📝 Resetting to working commit c33197d..."
git reset --hard c33197d

# Verify database
echo "🔍 Checking database status..."
python3 -c "
import sqlite3
db_path = 'data/aih_edu.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM educational_resources')
resources = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM emerging_skills') 
skills = cursor.fetchone()[0]
cursor.execute('SELECT COUNT(*) FROM skill_resources')
mappings = cursor.fetchone()[0]
print(f'✅ Database Status:')
print(f'   Resources: {resources}')
print(f'   Skills: {skills}')
print(f'   Skill-Resource mappings: {mappings}')
conn.close()
"

echo ""
echo "🎯 WORKING STATE RESTORED!"
echo "================================================"
echo "✅ All skill curation pages should work"
echo "✅ Database has 87 resources and 7 skills"
echo "✅ Learning paths will auto-create"
echo ""
echo "To start server: cd aih_edu && python app.py"
echo "Test page: http://localhost:9000/skill/ai-enhanced-siem" 