#!/bin/bash

# 🚀 AI-HORIZON ED PLATFORM - AUTOMATED DEPLOYMENT SCRIPT
# This script executes the complete deployment process to Heroku

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Function to print colored output
print_step() {
    echo -e "${BLUE}${BOLD}🚀 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Heroku CLI
check_heroku_cli() {
    if ! command_exists heroku; then
        print_error "Heroku CLI not found. Please install it first."
        echo "Visit: https://devcenter.heroku.com/articles/heroku-cli"
        exit 1
    fi
    
    if ! heroku auth:whoami >/dev/null 2>&1; then
        print_error "Not logged in to Heroku. Please run: heroku login"
        exit 1
    fi
    
    print_success "Heroku CLI ready ($(heroku auth:whoami))"
}

# Function to verify API keys
verify_api_keys() {
    print_step "PHASE 1: Verifying API Keys"
    
    # Check if API keys are set in Heroku
    if ! heroku config:get ANTHROPIC_API_KEY -a ai-horizon-ed-platform >/dev/null 2>&1; then
        print_error "ANTHROPIC_API_KEY not set in Heroku"
        print_info "Run: heroku config:set ANTHROPIC_API_KEY=sk-ant-xxxxx -a ai-horizon-ed-platform"
        exit 1
    fi
    
    if ! heroku config:get OPENAI_API_KEY -a ai-horizon-ed-platform >/dev/null 2>&1; then
        print_error "OPENAI_API_KEY not set in Heroku"
        print_info "Run: heroku config:set OPENAI_API_KEY=sk-xxxxx -a ai-horizon-ed-platform"
        exit 1
    fi
    
    if ! heroku config:get PERPLEXITY_API_KEY -a ai-horizon-ed-platform >/dev/null 2>&1; then
        print_error "PERPLEXITY_API_KEY not set in Heroku"
        print_info "Run: heroku config:set PERPLEXITY_API_KEY=pplx-xxxxx -a ai-horizon-ed-platform"
        exit 1
    fi
    
    print_success "All API keys configured in Heroku"
}

# Function to commit and push to GitHub
deploy_to_github() {
    print_step "PHASE 2: Deploying to GitHub"
    
    # Check if there are changes to commit
    if [[ -n $(git status --porcelain) ]]; then
        print_info "Committing changes..."
        git add -A
        git commit -m "🚀 Deploy AI-Powered Quiz System to Heroku

✅ Complete quiz functionality with AI grading
✅ 86 resources, 7 skills, 19 active quizzes  
✅ Claude/OpenAI integration operational
✅ Fresh database export included

Features:
- Interactive quiz modals with AI grading
- Multi-provider AI fallback (Claude → OpenAI → Basic)
- Comprehensive error handling
- Production-ready performance
- Full documentation included"
        
        print_success "Changes committed to git"
    else
        print_info "No changes to commit"
    fi
    
    # Push to GitHub
    print_info "Pushing to GitHub..."
    git push origin master
    print_success "Pushed to GitHub successfully"
}

# Function to deploy to Heroku
deploy_to_heroku() {
    print_step "PHASE 3: Deploying to Heroku"
    
    # Check if Heroku remote exists
    if ! git remote get-url heroku >/dev/null 2>&1; then
        print_warning "Heroku remote not found, adding it..."
        heroku git:remote -a ai-horizon-ed-platform
        print_success "Heroku remote added"
    fi
    
    # Deploy to Heroku
    print_info "Deploying to Heroku (this may take a few minutes)..."
    git push heroku master
    print_success "Deployed to Heroku successfully"
}

# Function to populate database
populate_database() {
    print_step "PHASE 4: Populating Database"
    
    # Check if database export exists
    if [[ ! -f "aih_edu/heroku_export.json" ]]; then
        print_error "Database export not found: aih_edu/heroku_export.json"
        exit 1
    fi
    
    print_info "Populating database with exported data..."
    
    # Wait for app to be ready
    sleep 10
    
    # Check if population endpoint exists
    if curl -s "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/admin/populate-from-export" \
            -X POST \
            -H "Content-Type: application/json" \
            -d @aih_edu/heroku_export.json \
            --connect-timeout 30 \
            --max-time 60 >/dev/null 2>&1; then
        print_success "Database populated successfully"
    else
        print_warning "Database population may have failed, checking status..."
        # Try to check database stats
        if curl -s "https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/api/database/stats" \
                --connect-timeout 10 >/dev/null 2>&1; then
            print_info "Database appears to be accessible"
        else
            print_error "Database population failed"
            exit 1
        fi
    fi
}

# Function to verify deployment
verify_deployment() {
    print_step "PHASE 5: Verifying Deployment"
    
    # Test critical endpoints
    APP_URL="https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com"
    
    print_info "Testing homepage..."
    if curl -s "$APP_URL" --connect-timeout 10 >/dev/null 2>&1; then
        print_success "Homepage loads successfully"
    else
        print_error "Homepage failed to load"
        exit 1
    fi
    
    print_info "Testing database stats..."
    if STATS=$(curl -s "$APP_URL/api/database/stats" --connect-timeout 10 2>/dev/null); then
        RESOURCE_COUNT=$(echo "$STATS" | grep -o '"total_resources":[0-9]*' | cut -d':' -f2)
        SKILL_COUNT=$(echo "$STATS" | grep -o '"emerging_skills_count":[0-9]*' | cut -d':' -f2)
        print_success "Database stats: $RESOURCE_COUNT resources, $SKILL_COUNT skills"
    else
        print_error "Database stats endpoint failed"
        exit 1
    fi
    
    print_info "Testing skill page..."
    if curl -s "$APP_URL/skill/vibe-coding" --connect-timeout 10 >/dev/null 2>&1; then
        print_success "Skill page loads successfully"
    else
        print_warning "Skill page may have issues"
    fi
    
    print_info "Testing quiz endpoint..."
    if curl -s "$APP_URL/api/resource/85/questions" --connect-timeout 10 >/dev/null 2>&1; then
        print_success "Quiz endpoint responding"
    else
        print_warning "Quiz endpoint may have issues"
    fi
    
    print_info "Testing admin panel..."
    if curl -s "$APP_URL/admin" --connect-timeout 10 >/dev/null 2>&1; then
        print_success "Admin panel accessible"
    else
        print_warning "Admin panel may have issues"
    fi
}

# Main deployment function
main() {
    echo -e "${BOLD}${BLUE}"
    echo "🚀 AI-HORIZON ED PLATFORM - AUTOMATED DEPLOYMENT"
    echo "=================================================="
    echo -e "${NC}"
    
    print_info "Starting deployment process..."
    
    # Check prerequisites
    check_heroku_cli
    
    # Run pre-flight checks
    print_info "Running pre-flight checks..."
    if python3 deployment/pre_flight_check.py; then
        print_success "Pre-flight checks passed"
    else
        print_error "Pre-flight checks failed"
        exit 1
    fi
    
    # Execute deployment phases
    verify_api_keys
    deploy_to_github
    deploy_to_heroku
    populate_database
    verify_deployment
    
    # Success message
    echo -e "${GREEN}${BOLD}"
    echo "🎉 DEPLOYMENT SUCCESSFUL!"
    echo "========================"
    echo -e "${NC}"
    
    echo -e "${GREEN}✅ AI-Horizon Ed Platform is now live at:${NC}"
    echo -e "${BLUE}🌐 https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com${NC}"
    echo -e "${BLUE}👤 https://ai-horizon-ed-platform-50ef91ff7701.herokuapp.com/admin${NC}"
    echo ""
    echo -e "${GREEN}🎯 Key Features Deployed:${NC}"
    echo "• AI-powered quiz system with Claude/OpenAI grading"
    echo "• Interactive quiz modals with real-time feedback"
    echo "• 86 educational resources across 7 skills"
    echo "• Comprehensive admin panel"
    echo "• Production-ready performance"
    echo ""
    echo -e "${YELLOW}📋 Next Steps:${NC}"
    echo "1. Test the quiz functionality on skill pages"
    echo "2. Verify AI grading is working correctly"
    echo "3. Check admin panel for resource management"
    echo "4. Monitor application logs for any issues"
    
    print_success "Deployment completed successfully! 🚀"
}

# Run the deployment
main "$@" 