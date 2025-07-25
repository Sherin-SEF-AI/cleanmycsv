# CleanMyCSV.online - AI-Powered CSV Cleaning SaaS

A production-ready CSV cleaning service with anonymous usage, AI-powered features, and freemium monetization. Users can clean CSVs immediately without signup, then get prompted to register for unlimited access.

## 🚀 Features

### Core Functionality
- **Anonymous Usage**: 3 free cleanings per month, no signup required
- **AI-Powered Cleaning**: GPT-3.5 integration for smart column detection and natural language instructions
- **Basic Cleaning**: Remove duplicates, empty rows, type conversion
- **Advanced Features**: Email/phone/date/currency standardization
- **Real-time Processing**: Clean files in seconds, not hours
- **Secure**: Files automatically deleted after processing

### User Experience
- **Zero-friction Onboarding**: Start cleaning immediately
- **Progressive Signup**: Gentle conversion from anonymous to registered users
- **Modern UI**: Beautiful, responsive interface with drag-and-drop uploads
- **Usage Tracking**: Clear indicators of remaining free cleanings
- **Download Results**: One-click download of cleaned CSV files

### Technical Stack
- **Backend**: FastAPI + Python, PostgreSQL, Redis
- **Frontend**: React + TypeScript, Tailwind CSS
- **AI**: OpenAI GPT-3.5-turbo for smart features
- **Deployment**: Docker containers, ready for Railway/AWS

## 🏗️ Architecture

```
├── app/                    # FastAPI backend
│   ├── main.py            # Main API endpoints
│   ├── cleaner.py         # CSV cleaning engine with LLM
│   ├── auth.py            # JWT authentication
│   ├── usage.py           # Anonymous usage tracking
│   ├── models.py          # Database models
│   └── config.py          # Configuration settings
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # Auth context
│   │   └── App.tsx        # Main app component
│   └── package.json
├── docker-compose.yml     # Local development setup
├── Dockerfile            # Production container
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 16+ (for frontend development)

### 1. Clone and Setup
```bash
git clone <repository-url>
cd clean-my-csv
```

### 2. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env with your API keys
nano .env
```

Required environment variables:
```bash
DATABASE_URL=postgresql://cleancsv:password123@localhost:5432/cleancsv
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-openai-key-here
STRIPE_SECRET_KEY=sk_test_your-stripe-key
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
ENVIRONMENT=development
```

### 3. Start with Docker (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f web
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 4. Manual Setup (Alternative)

#### Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis (or use Docker)
docker-compose up db redis -d

# Run migrations
python -c "from app.models import create_tables; create_tables()"

# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📊 Usage

### Anonymous Users
1. Visit the website
2. Drag & drop a CSV file (up to 10MB)
3. Add cleaning instructions (optional)
4. Click "Clean My CSV"
5. Download the cleaned file
6. After 3 uses, prompted to sign up

### Registered Users
1. Sign up for a free account
2. Get 50 free cleanings per month
3. Access AI-powered features
4. Upload larger files (up to 100MB)
5. Use natural language instructions

### API Usage
```bash
# Upload and clean a CSV file
curl -X POST "http://localhost:8000/upload-csv" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@data.csv" \
  -F "user_instructions=Remove duplicates and fix phone formats"

# Check usage info
curl "http://localhost:8000/usage-info"
```

## 🎯 Business Model

### Freemium Structure
- **Free Tier**: 3 cleanings/month, 10MB files, basic features
- **Pro Plan**: $9/month, 500 cleanings, 500MB files, AI features
- **Enterprise**: $29/month, unlimited, 2GB files, API access

### Conversion Strategy
1. **Anonymous Usage**: Let users try the service immediately
2. **Value Demonstration**: Show quality improvements and time savings
3. **Gentle Nudges**: Usage indicators and signup prompts
4. **Feature Differentiation**: AI features only for registered users

## 🔧 Development

### Adding New Features
1. **Backend**: Add endpoints in `app/main.py`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Database**: Update models in `app/models.py`
4. **Testing**: Add tests in `tests/` directory

### Code Structure
- **Clean Architecture**: Separation of concerns
- **Type Safety**: TypeScript frontend, type hints in Python
- **Error Handling**: Comprehensive error responses
- **Security**: JWT tokens, input validation, rate limiting

### Testing
```bash
# Backend tests
pytest tests/

# Frontend tests
cd frontend && npm test

# Integration tests
docker-compose -f docker-compose.test.yml up
```

## 🚀 Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to Railway/AWS/DigitalOcean
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables for Production
```bash
ENVIRONMENT=production
DATABASE_URL=your-production-db-url
REDIS_URL=your-production-redis-url
OPENAI_API_KEY=your-openai-key
STRIPE_SECRET_KEY=your-stripe-key
JWT_SECRET_KEY=your-secure-jwt-key
```

### Monitoring
- **Health Check**: `GET /health`
- **Metrics**: Prometheus endpoints
- **Logging**: Structured JSON logs
- **Error Tracking**: Sentry integration

## 📈 Performance

### Benchmarks
- **Processing Speed**: < 30 seconds for files under 50MB
- **Concurrent Users**: 100+ simultaneous cleanings
- **Uptime**: 99.9% availability target
- **Error Rate**: < 1% failed processing attempts

### Optimization
- **Caching**: Redis for session data
- **Async Processing**: Background tasks for large files
- **CDN**: Static asset delivery
- **Database**: Connection pooling, indexes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: [docs.cleanmycsv.online](https://docs.cleanmycsv.online)
- **API Reference**: [api.cleanmycsv.online/docs](https://api.cleanmycsv.online/docs)
- **Issues**: GitHub Issues
- **Email**: support@cleanmycsv.online

---

**Built with ❤️ for data scientists, analysts, and anyone who works with CSV files.** 