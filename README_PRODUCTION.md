# 🚀 CleanMyCSV.online - Production Deployment Guide

## 📋 Overview

CleanMyCSV.online is a production-ready, AI-powered CSV cleaning SaaS with:
- **Anonymous Usage**: 3 free cleanings for new users
- **User Authentication**: Secure registration, login, and email verification
- **Razorpay Integration**: Subscription management and payments
- **AI-Powered Cleaning**: Groq LLM integration for smart data analysis
- **Production Security**: JWT tokens, rate limiting, and secure headers

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Nginx         │    │   FastAPI       │
│   (React)       │◄──►│   (Reverse      │◄──►│   (Backend)     │
│                 │    │    Proxy)       │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │   Redis         │
                       │   (Database)    │    │   (Cache)       │
                       └─────────────────┘    └─────────────────┘
```

## 🛠️ Prerequisites

- **Server**: Ubuntu 20.04+ or CentOS 8+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Domain**: cleancsv.online (or your domain)
- **SSL Certificate**: Let's Encrypt or your provider

## 📦 Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/clean-my-csv.git
cd clean-my-csv
```

### 2. Environment Setup
```bash
# Copy environment template
cp env.example .env

# Edit environment variables
nano .env
```

### 3. Configure Environment Variables

#### Required Variables:
```bash
# Database
DATABASE_URL=postgresql://cleancsv:your_secure_password@localhost:5432/cleancsv
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://:your_redis_password@localhost:6379/0
REDIS_PASSWORD=your_redis_password

# AI/LLM
GROQ_API_KEY=gsk_your_groq_api_key

# Razorpay
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret
RAZORPAY_WEBHOOK_SECRET=your_webhook_secret

# Security
JWT_SECRET_KEY=your_super_secure_jwt_key
SECRET_KEY=your_super_secure_secret_key

# Email (for verification)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
FROM_EMAIL=noreply@cleancsv.online

# Production Settings
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=cleancsv.online,www.cleancsv.online
CORS_ORIGINS=https://cleancsv.online,https://www.cleancsv.online
```

### 4. Razorpay Setup

1. **Create Razorpay Account**:
   - Sign up at [razorpay.com](https://razorpay.com)
   - Complete KYC verification

2. **Create Plans**:
   ```bash
   # Pro Monthly Plan
   curl -u "rzp_test_YOUR_KEY:YOUR_SECRET" \
     -X POST https://api.razorpay.com/v1/plans \
     -H "Content-Type: application/json" \
     -d '{
       "period": "monthly",
       "interval": 1,
       "item": {
         "name": "Pro Plan Monthly",
         "amount": 99900,
         "currency": "INR",
         "description": "Pro plan for CleanMyCSV.online"
       }
     }'
   
   # Pro Yearly Plan
   curl -u "rzp_test_YOUR_KEY:YOUR_SECRET" \
     -X POST https://api.razorpay.com/v1/plans \
     -H "Content-Type: application/json" \
     -d '{
       "period": "yearly",
       "interval": 1,
       "item": {
         "name": "Pro Plan Yearly",
         "amount": 999900,
         "currency": "INR",
         "description": "Pro plan yearly for CleanMyCSV.online"
       }
     }'
   ```

3. **Update Plan IDs**:
   ```bash
   # Add the returned plan IDs to your .env file
   RAZORPAY_PRO_MONTHLY_PLAN_ID=plan_xxxxxxxxxxxxx
   RAZORPAY_PRO_YEARLY_PLAN_ID=plan_xxxxxxxxxxxxx
   ```

### 5. Database Setup
```bash
# Run production setup script
python scripts/setup_production.py

# Or manually create tables
python -c "from app.database import create_tables; create_tables()"
```

### 6. SSL Certificate Setup
```bash
# Install Certbot
sudo apt update
sudo apt install certbot

# Get SSL certificate
sudo certbot certonly --standalone -d cleancsv.online -d www.cleancsv.online

# Copy certificates to nginx directory
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/cleancsv.online/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/cleancsv.online/privkey.pem nginx/ssl/
```

### 7. Nginx Configuration
```bash
# Create nginx configuration
mkdir -p nginx
```

Create `nginx/nginx.conf`:
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name cleancsv.online www.cleancsv.online;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name cleancsv.online www.cleancsv.online;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # API
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Rate limiting
            limit_req zone=api burst=10 nodelay;
            limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
        }

        # Health check
        location /health {
            proxy_pass http://backend/health;
            access_log off;
        }
    }
}
```

### 8. Deploy with Docker
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 🔧 Configuration

### Frontend Configuration
Update `frontend/src/config.ts`:
```typescript
export const config = {
  API_BASE_URL: 'https://cleancsv.online/api',
  RAZORPAY_KEY_ID: 'rzp_test_your_key_id', // Your Razorpay key
  ENVIRONMENT: 'production'
};
```

### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new feature"

# Apply migrations
alembic upgrade head
```

## 📊 Monitoring

### Health Checks
```bash
# Check API health
curl https://cleancsv.online/api/health

# Check database
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Check Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

### Logs
```bash
# View all logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Performance Monitoring
```bash
# Check resource usage
docker stats

# Monitor disk usage
df -h

# Monitor memory usage
free -h
```

## 🔒 Security

### SSL Certificate Renewal
```bash
# Set up automatic renewal
sudo crontab -e

# Add this line for daily renewal check
0 12 * * * /usr/bin/certbot renew --quiet
```

### Database Backups
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U cleancsv cleancsv > backup_$DATE.sql
gzip backup_$DATE.sql
aws s3 cp backup_$DATE.sql.gz s3://your-backup-bucket/
rm backup_$DATE.sql.gz
EOF

chmod +x backup.sh

# Add to crontab for daily backups
0 2 * * * /path/to/backup.sh
```

### Rate Limiting
The nginx configuration includes rate limiting:
- API endpoints: 10 requests/second with burst of 10
- Adjust limits in `nginx/nginx.conf` as needed

## 🚀 Scaling

### Horizontal Scaling
```bash
# Scale backend services
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

### Load Balancer
For high traffic, consider using a load balancer like AWS ALB or CloudFlare.

## 🔄 Updates

### Application Updates
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d
```

### Database Updates
```bash
# Apply migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## 📈 Analytics

### User Analytics
- Track user registrations and conversions
- Monitor subscription metrics
- Analyze CSV cleaning patterns

### Performance Metrics
- Response times
- Error rates
- Resource utilization

## 🆘 Troubleshooting

### Common Issues

1. **SSL Certificate Issues**:
   ```bash
   # Check certificate validity
   openssl x509 -in nginx/ssl/fullchain.pem -text -noout
   
   # Renew certificate
   sudo certbot renew
   ```

2. **Database Connection Issues**:
   ```bash
   # Check database status
   docker-compose -f docker-compose.prod.yml exec postgres pg_isready
   
   # Check logs
   docker-compose -f docker-compose.prod.yml logs postgres
   ```

3. **Payment Issues**:
   - Verify Razorpay webhook configuration
   - Check payment logs in Razorpay dashboard
   - Verify webhook signature verification

### Support
For production support:
- Email: support@cleancsv.online
- Documentation: https://docs.cleancsv.online
- Status page: https://status.cleancsv.online

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**🎉 Congratulations!** Your CleanMyCSV.online instance is now production-ready and deployed! 