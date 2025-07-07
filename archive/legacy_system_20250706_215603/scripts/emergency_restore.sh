#!/bin/bash

# 🚨 EMERGENCY DATABASE RESTORE SCRIPT
# Use this before any demo to ensure database is populated

echo "🚨 EMERGENCY: Restoring AI-Horizon Ed Database..."

# Check current status
echo "📊 Current database status:"
curl -s https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/database/stats

echo -e "\n🔄 Triggering bulk discovery for all skills..."

# Trigger immediate discovery for all skills
curl -X POST -H "Content-Type: application/json" \
  -d '{"skills": ["Zero Trust Architecture", "AI-Enhanced SIEM", "Cloud Security Posture Management", "Quantum-Safe Cryptography", "Vibe Coding"]}' \
  https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/admin/bulk-discover

echo -e "\n⏱️  Waiting 60 seconds for discovery to complete..."
sleep 60

echo -e "\n📊 Final database status:"
curl -s https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/database/stats

echo -e "\n✅ Database restoration complete!"
echo "🚀 Demo URLs ready:"
echo "   Main: https://ed.theaihorizon.org/"
echo "   Admin: https://ed.theaihorizon.org/admin"
echo "   Skills: https://ed.theaihorizon.org/skills"
echo "   Vibe Coding: https://ed.theaihorizon.org/skill/vibe-coding" 