# Bulletproof Deployment Guide for AI-Horizon Ed

## Overview

This guide provides a completely fresh, bulletproof deployment approach for the AI-Horizon Ed platform. The system includes:

- **Bulletproof schema management** across SQLite and PostgreSQL
- **Safe database migration** with validation and rollback
- **Comprehensive health monitoring**
- **Automated deployment with safety checks**
- **Rollback capabilities** in case of issues

## 🚀 Quick Start

### Prerequisites

1. **Heroku CLI** installed and authenticated
2. **Git** configured
3. **Python 3.11+** installed locally
4. **PostgreSQL** addon on Heroku (will be created automatically)

### One-Command Deployment

```bash
# Deploy to Heroku app named "your-app-name"
python bulletproof_deploy.py your-app-name

# Dry run (validation only)
python bulletproof_deploy.py your-app-name --dry-run
```

## 📋 Detailed Deployment Steps

### Step 1: Prepare Local Environment

```bash
# Clone/navigate to your project
cd ai-horizon-ed

# Install dependencies
pip install -r requirements.txt

# Verify local database exists
ls -la data/aih_edu.db

# Run health checks
python aih_edu/health_checks.py --verbose
```

### Step 2: Validate Prerequisites

```bash
# Check all prerequisites
python bulletproof_deploy.py your-app-name --dry-run
```

This will verify:
- ✅ Heroku CLI installed and authenticated
- ✅ Git repository configured
- ✅ Required deployment files present
- ✅ App structure correct
- ✅ Local database accessible

### Step 3: Deploy with Safety Checks

```bash
# Full deployment with all safety checks
python bulletproof_deploy.py your-app-name
```

The deployment process includes:

1. **Prerequisites Validation** - Verify all requirements
2. **Backup Current State** - Save current Heroku configuration
3. **File Preparation** - Validate deployment files
4. **Heroku Deployment** - Push code to Heroku
5. **Database Migration** - Safe schema migration with validation
6. **Health Checks** - Comprehensive system validation

### Step 4: Verify Deployment

```bash
# Check app status
heroku ps --app your-app-name

# View logs
heroku logs --tail --app your-app-name

# Test health endpoint
curl https://your-app-name.herokuapp.com/api/health
```

## 🔧 Components Overview

### Bulletproof Schema Manager (`bulletproof_schema.py`)

Handles schema management across SQLite and PostgreSQL:

- **Unified schema definition** for both databases
- **Automatic type adaptation** (SQLite ↔ PostgreSQL)
- **Missing column detection** and addition
- **Index management**
- **Schema validation**

### Bulletproof Migration Manager (`bulletproof_migration.py`)

Provides safe database migrations:

- **Pre-migration validation**
- **Incremental data transfer** with checkpoints
- **Data integrity verification**
- **Automatic rollback** on failure
- **Progress monitoring**

### Health Check System (`health_checks.py`)

Comprehensive monitoring:

- **Database connectivity** and performance
- **Schema integrity** validation
- **Data integrity** checks
- **Environment variables** validation
- **File system** access
- **Memory and disk usage**
- **API endpoint** availability

### Deployment Manager (`bulletproof_deploy.py`)

Automated deployment:

- **Prerequisites validation**
- **Backup and rollback**
- **Heroku deployment**
- **Database setup**
- **Health monitoring**

## 🔍 Health Monitoring

### Health Check Endpoints

```bash
# Basic status
curl https://your-app-name.herokuapp.com/api/status

# Comprehensive health check
curl https://your-app-name.herokuapp.com/api/health
```

### Health Check from CLI

```bash
# Run local health checks
python aih_edu/health_checks.py

# Save report to file
python aih_edu/health_checks.py --save

# Verbose output
python aih_edu/health_checks.py --verbose
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### 1. Database Connection Issues

**Symptom**: `Failed to connect to database`

**Solution**:
```bash
# Check DATABASE_URL
heroku config:get DATABASE_URL --app your-app-name

# Verify PostgreSQL addon
heroku addons --app your-app-name

# Check database connectivity
heroku run 'cd aih_edu && python -c "from utils.database import DatabaseManager; db = DatabaseManager(); print(db.get_resource_stats())"' --app your-app-name
```

#### 2. Schema Mismatch Errors

**Symptom**: `table has no column named`

**Solution**:
```bash
# Run schema migration
python -c "
from aih_edu.bulletproof_schema import BulletproofSchemaManager
import os
schema_manager = BulletproofSchemaManager(os.environ['DATABASE_URL'])
schema_manager.migrate_schema_safely()
"
```

#### 3. Migration Failures

**Symptom**: `Migration failed with errors`

**Solution**:
```bash
# Check migration logs
heroku logs --tail --app your-app-name

# Retry migration with validation
python -c "
from aih_edu.bulletproof_migration import BulletproofMigrationManager
migration = BulletproofMigrationManager('sqlite:///data/aih_edu.db', os.environ['DATABASE_URL'])
report = migration.perform_full_migration()
print(report)
"
```

#### 4. Health Check Failures

**Symptom**: Health checks showing warnings/errors

**Solution**:
```bash
# Run detailed health check
python aih_edu/health_checks.py --verbose --save

# Check specific issues
heroku run 'cd aih_edu && python health_checks.py' --app your-app-name
```

### Emergency Rollback

If deployment fails:

```bash
# Automatic rollback (during deployment)
# The system will ask if you want to rollback on failure

# Manual rollback
heroku rollback --app your-app-name

# Or rollback to specific version
heroku rollback v123 --app your-app-name
```

## 📊 Monitoring and Maintenance

### Regular Health Checks

Set up monitoring:

```bash
# Add to cron job for regular health checks
0 */6 * * * curl -s https://your-app-name.herokuapp.com/api/health | jq .overall_status
```

### Database Maintenance

```bash
# Check database stats
heroku run 'cd aih_edu && python -c "from utils.database import DatabaseManager; db = DatabaseManager(); print(db.get_resource_stats())"' --app your-app-name

# Backup database
heroku pg:backups:capture --app your-app-name

# View backup status
heroku pg:backups --app your-app-name
```

### Performance Monitoring

```bash
# View app metrics
heroku logs --tail --app your-app-name

# Check dyno status
heroku ps --app your-app-name

# Monitor database performance
heroku pg:diagnose --app your-app-name
```

## 🔒 Security Considerations

### Environment Variables

Ensure these are set in Heroku:

```bash
# Required
heroku config:set DATABASE_URL=postgresql://... --app your-app-name
heroku config:set SECRET_KEY=your-secret-key --app your-app-name

# Optional (for full functionality)
heroku config:set OPENAI_API_KEY=your-key --app your-app-name
heroku config:set ANTHROPIC_API_KEY=your-key --app your-app-name
```

### HTTPS Configuration

The app automatically:
- Redirects HTTP to HTTPS in production
- Sets security headers
- Enforces HSTS (HTTP Strict Transport Security)

## 🎯 Best Practices

### 1. Pre-Deployment Checklist

- [ ] Run health checks locally
- [ ] Verify database integrity
- [ ] Test all API endpoints
- [ ] Validate environment variables
- [ ] Backup current state

### 2. Deployment Checklist

- [ ] Run dry-run deployment
- [ ] Deploy during low-traffic periods
- [ ] Monitor logs during deployment
- [ ] Run post-deployment health checks
- [ ] Verify all functionality

### 3. Post-Deployment Monitoring

- [ ] Check health endpoint every 6 hours
- [ ] Monitor error rates
- [ ] Review performance metrics
- [ ] Update dependencies regularly
- [ ] Backup database weekly

## 📈 Performance Optimization

### Database Optimization

```bash
# Create indexes for better performance
heroku run 'cd aih_edu && python -c "
from bulletproof_schema import BulletproofSchemaManager
import os
schema_manager = BulletproofSchemaManager(os.environ[\"DATABASE_URL\"])
schema_manager.create_indexes()
"' --app your-app-name
```

### Application Optimization

The deployment uses:
- **Gunicorn** with optimized worker configuration
- **Connection pooling** for database
- **Caching** for frequently accessed data
- **Efficient querying** with proper indexes

## 🆘 Support and Recovery

### Emergency Recovery

If the app is completely broken:

```bash
# Emergency restore endpoint
curl -X POST https://your-app-name.herokuapp.com/emergency-restore-full

# Manual database restore
heroku pg:backups:restore --app your-app-name
```

### Getting Help

1. Check the health endpoint: `/api/health`
2. Review deployment logs: `heroku logs --tail --app your-app-name`
3. Run local health checks: `python aih_edu/health_checks.py --verbose`
4. Check database connectivity: Use database browser endpoint

## 📝 Deployment Logs

All deployments create detailed logs:

- `deployment_YYYYMMDD_HHMMSS.json` - Complete deployment report
- `migration_checkpoint_*.json` - Migration progress (auto-cleaned)
- `health_report_*.json` - Health check results (optional)

## 🎉 Success Indicators

Your deployment is successful when:

- ✅ Health endpoint returns `"overall_status": "healthy"`
- ✅ App responds to HTTP requests
- ✅ Database connectivity works
- ✅ No critical errors in logs
- ✅ All API endpoints functional

## 📚 Additional Resources

- [Heroku PostgreSQL Documentation](https://devcenter.heroku.com/articles/heroku-postgresql)
- [Flask Deployment Guide](https://flask.palletsprojects.com/en/2.0.x/deploying/)
- [PostgreSQL Best Practices](https://wiki.postgresql.org/wiki/Performance_Optimization)

---

## 🚀 Ready to Deploy?

```bash
# Quick deployment
python bulletproof_deploy.py your-app-name

# That's it! The system handles everything else automatically.
```

The bulletproof deployment system ensures your AI-Horizon Ed platform deploys safely, with comprehensive monitoring and automatic rollback capabilities. Your deployment will be robust, monitored, and maintainable. 