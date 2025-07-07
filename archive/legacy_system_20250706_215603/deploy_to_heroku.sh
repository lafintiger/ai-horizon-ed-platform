#!/bin/bash

# 🚀 Bulletproof Heroku Deployment Script
# Deploys AI-Horizon Ed to Heroku with PostgreSQL migration and rollback capability

set -e  # Exit on any error

# Configuration
HEROKU_APP_NAME="ai-horizon-ed-$(date +%m%d%H%M)"
BRANCH_NAME="heroku-deployment"
BACKUP_BRANCH="master-backup-$(date +%Y%m%d-%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if heroku CLI is installed
    if ! command -v heroku &> /dev/null; then
        print_error "Heroku CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if logged in to Heroku
    if ! heroku auth:whoami &> /dev/null; then
        print_error "Not logged in to Heroku. Run 'heroku login' first."
        exit 1
    fi
    
    # Check if we're on the deployment branch
    current_branch=$(git branch --show-current)
    if [ "$current_branch" != "$BRANCH_NAME" ]; then
        print_error "Must be on $BRANCH_NAME branch for deployment"
        exit 1
    fi
    
    # Check if local app is working
    print_status "Checking local app status..."
    cd aih_edu
    if ! curl -s http://localhost:9000/api/database/stats &> /dev/null; then
        print_warning "Local app doesn't seem to be running. That's OK for deployment."
    else
        print_success "Local app is running properly"
    fi
    cd ..
    
    print_success "Prerequisites check passed"
}

# Function to create backup
create_backup() {
    print_status "Creating backup branch..."
    git checkout master
    git checkout -b "$BACKUP_BRANCH"
    git checkout "$BRANCH_NAME"
    print_success "Backup branch created: $BACKUP_BRANCH"
}

# Function to prepare deployment files
prepare_deployment() {
    print_status "Preparing deployment files..."
    
    # Ensure we have fresh data export
    cd aih_edu
    python3 export_for_heroku.py
    cd ..
    
    # Add data export to git
    git add aih_edu/heroku_import_data.json
    git commit -m "Update data export for Heroku deployment" || true
    
    print_success "Deployment files prepared"
}

# Function to create or update Heroku app
setup_heroku_app() {
    print_status "Setting up Heroku app..."
    
    # Try to create app (will fail if it exists, which is fine)
    heroku create "$HEROKU_APP_NAME" || print_warning "App $HEROKU_APP_NAME already exists"
    
    # Add PostgreSQL addon
    print_status "Setting up PostgreSQL database..."
    heroku addons:create heroku-postgresql:essential-0 -a "$HEROKU_APP_NAME" || print_warning "PostgreSQL addon already exists"
    
    # Set environment variables
    print_status "Configuring environment variables..."
    heroku config:set FLASK_ENV=production -a "$HEROKU_APP_NAME"
    heroku config:set SECRET_KEY="$(openssl rand -hex 32)" -a "$HEROKU_APP_NAME"
    heroku config:set MIN_CONTENT_QUALITY=0.7 -a "$HEROKU_APP_NAME"
    heroku config:set MAX_SEARCH_RESULTS=50 -a "$HEROKU_APP_NAME"
    
    print_success "Heroku app configured"
}

# Function to deploy to Heroku
deploy_to_heroku() {
    print_status "Deploying to Heroku..."
    
    # Add Heroku remote if it doesn't exist
    git remote add heroku "https://git.heroku.com/$HEROKU_APP_NAME.git" 2>/dev/null || true
    
    # Deploy
    git push heroku "$BRANCH_NAME:master" --force
    
    print_success "Code deployed to Heroku"
}

# Function to migrate database
migrate_database() {
    print_status "Migrating database to PostgreSQL..."
    
    # Get the DATABASE_URL from Heroku
    DATABASE_URL=$(heroku config:get DATABASE_URL -a "$HEROKU_APP_NAME")
    
    # Run the migration script on Heroku (use python3 on Heroku)
    heroku run python3 aih_edu/import_to_postgres.py -a "$HEROKU_APP_NAME"
    
    print_success "Database migration completed"
}

# Function to verify deployment
verify_deployment() {
    print_status "Verifying deployment..."
    
    # Get app URL
    APP_URL=$(heroku apps:info -a "$HEROKU_APP_NAME" | grep "Web URL" | awk '{print $3}')
    
    # Test endpoints
    print_status "Testing endpoints..."
    
    # Test homepage
    if curl -s "$APP_URL" | grep -q "AI-Horizon"; then
        print_success "Homepage is working"
    else
        print_error "Homepage test failed"
        return 1
    fi
    
    # Test database stats API
    if curl -s "$APP_URL/api/database/stats" | grep -q "total_resources"; then
        print_success "Database API is working"
    else
        print_error "Database API test failed"
        return 1
    fi
    
    # Test skills API
    if curl -s "$APP_URL/api/skills/emerging" | grep -q "\["; then
        print_success "Skills API is working"
    else
        print_error "Skills API test failed"
        return 1
    fi
    
    print_success "All endpoint tests passed"
    print_success "Deployment verified successfully!"
    echo ""
    print_success "🎉 Your app is live at: $APP_URL"
    echo ""
}

# Function to handle rollback
rollback_deployment() {
    print_error "Deployment failed. Rolling back..."
    
    # Switch back to master
    git checkout master
    
    # Remove the failed deployment branch
    git branch -D "$BRANCH_NAME" || true
    
    # Recreate deployment branch from master
    git checkout -b "$BRANCH_NAME"
    
    print_success "Rollback completed. Local environment restored."
}

# Function to open app
open_app() {
    heroku open -a "$HEROKU_APP_NAME"
}

# Main deployment function
main() {
    echo ""
    echo "🚀 Starting Bulletproof Heroku Deployment"
    echo "=========================================="
    echo ""
    
    # Create trap for cleanup on error
    trap rollback_deployment ERR
    
    check_prerequisites
    create_backup
    prepare_deployment
    setup_heroku_app
    deploy_to_heroku
    migrate_database
    verify_deployment
    
    # Remove error trap on success
    trap - ERR
    
    echo ""
    print_success "🎉 Deployment completed successfully!"
    echo ""
    print_status "Next steps:"
    echo "  1. Visit your app: heroku open -a $HEROKU_APP_NAME"
    echo "  2. Monitor logs: heroku logs --tail -a $HEROKU_APP_NAME"
    echo "  3. Check app status: heroku ps -a $HEROKU_APP_NAME"
    echo ""
    print_status "To rollback if needed:"
    echo "  git checkout master"
    echo "  git branch -D $BRANCH_NAME"
    echo "  git checkout -b $BRANCH_NAME"
    echo ""
    
    read -p "Would you like to open the app now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open_app
    fi
}

# Run main function
main "$@" 