# Deployment Guide for Eva Backend

## Table of Contents
1. [Google Cloud Run](#google-cloud-run)
2. [Heroku](#heroku)
3. [AWS Elastic Beanstalk](#aws-elastic-beanstalk)
4. [Docker](#docker)
5. [Environment Configuration](#environment-configuration)

---

## Google Cloud Run

### Prerequisites
- Google Cloud SDK installed
- Docker installed
- Google Cloud project with billing enabled

### Steps

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   COPY . .
   
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
   ```

2. **Build and push to Google Container Registry**
   ```bash
   # Authenticate with Google Cloud
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   
   # Build the image
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/eva-backend
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy eva-backend \
     --image gcr.io/YOUR_PROJECT_ID/eva-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
     --set-env-vars API_SECRET_KEY=your-secret-key \
     --set-env-vars GOOGLE_CLIENT_ID=your-client-id \
     --set-env-vars GOOGLE_CLIENT_SECRET=your-client-secret \
     --set-env-vars MAX_USERS=5 \
     --set-env-vars ENVIRONMENT=production
   ```

4. **Access your application**
   - Cloud Run will provide a URL like: `https://eva-backend-xxxxx-uc.a.run.app`

---

## Heroku

### Prerequisites
- Heroku CLI installed
- Heroku account

### Steps

1. **Create Procfile**
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

2. **Create runtime.txt**
   ```
   python-3.9.16
   ```

3. **Deploy to Heroku**
   ```bash
   # Login to Heroku
   heroku login
   
   # Create a new Heroku app
   heroku create eva-backend
   
   # Set environment variables
   heroku config:set GOOGLE_CLOUD_PROJECT=your-project-id
   heroku config:set API_SECRET_KEY=your-secret-key
   heroku config:set GOOGLE_CLIENT_ID=your-client-id
   heroku config:set GOOGLE_CLIENT_SECRET=your-client-secret
   heroku config:set MAX_USERS=5
   heroku config:set ENVIRONMENT=production
   
   # For service account, you'll need to set the JSON as a single line
   heroku config:set GOOGLE_APPLICATION_CREDENTIALS_JSON='{"type":"service_account",...}'
   
   # Deploy
   git push heroku main
   ```

4. **Update code to handle credentials on Heroku**
   Add to `app/services/firestore_service.py`:
   ```python
   import json
   
   # In __init__ method:
   credentials_json = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
   if credentials_json:
       credentials_dict = json.loads(credentials_json)
       credentials = service_account.Credentials.from_service_account_info(credentials_dict)
       self.db = firestore.Client(project=settings.google_cloud_project, credentials=credentials)
   else:
       self.db = firestore.Client(project=settings.google_cloud_project)
   ```

---

## AWS Elastic Beanstalk

### Prerequisites
- AWS CLI installed
- EB CLI installed
- AWS account

### Steps

1. **Initialize EB application**
   ```bash
   eb init -p python-3.9 eva-backend --region us-east-1
   ```

2. **Create .ebextensions/python.config**
   ```yaml
   option_settings:
     aws:elasticbeanstalk:container:python:
       WSGIPath: main:app
   ```

3. **Set environment variables**
   Create `.ebextensions/environment.config`:
   ```yaml
   option_settings:
     aws:elasticbeanstalk:application:environment:
       GOOGLE_CLOUD_PROJECT: "your-project-id"
       API_SECRET_KEY: "your-secret-key"
       GOOGLE_CLIENT_ID: "your-client-id"
       GOOGLE_CLIENT_SECRET: "your-client-secret"
       MAX_USERS: "5"
       ENVIRONMENT: "production"
   ```

4. **Create and deploy**
   ```bash
   eb create eva-backend-env
   eb deploy
   ```

5. **Open application**
   ```bash
   eb open
   ```

---

## Docker

### Using Docker Compose for Local Development

1. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     eva-backend:
       build: .
       ports:
         - "8000:8000"
       environment:
         - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
         - GOOGLE_APPLICATION_CREDENTIALS=/app/service-account-key.json
         - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
         - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
         - API_SECRET_KEY=${API_SECRET_KEY}
         - MAX_USERS=5
         - ENVIRONMENT=development
       volumes:
         - ./service-account-key.json:/app/service-account-key.json:ro
         - ./.env:/app/.env:ro
       command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Create Dockerfile**
   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   
   # Install dependencies
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   
   # Copy application code
   COPY . .
   
   # Run the application
   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. **Build and run**
   ```bash
   docker-compose up --build
   ```

---

## Environment Configuration

### Required Environment Variables

For all deployment platforms, ensure these variables are set:

| Variable | Description | Example |
|----------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `eva-assistant-123` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | `service-account-key.json` |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 client ID | `xxx.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 client secret | `GOCSPX-xxx` |
| `API_SECRET_KEY` | Secret key for JWT signing | Generate with `openssl rand -hex 32` |
| `MAX_USERS` | Maximum number of users | `5` |
| `ENVIRONMENT` | Environment name | `production` or `development` |
| `CORS_ORIGINS` | Allowed CORS origins | `https://yourapp.com` |

### Generating a Secure API Secret Key

```bash
# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Using OpenSSL
openssl rand -hex 32

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### Production Best Practices

1. **Use HTTPS** - Always use HTTPS in production
2. **Secure secrets** - Use secret management services:
   - Google Cloud Secret Manager
   - AWS Secrets Manager
   - HashiCorp Vault

3. **Enable logging** - Configure proper logging:
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

4. **Add monitoring** - Integrate with:
   - Google Cloud Monitoring
   - AWS CloudWatch
   - Datadog
   - New Relic

5. **Rate limiting** - Add rate limiting middleware:
   ```bash
   pip install slowapi
   ```

6. **Database backups** - Enable Firestore backups in Google Cloud Console

7. **CDN** - Use a CDN for static assets if applicable

---

## Troubleshooting

### Common Deployment Issues

1. **Port binding issues**
   - Ensure your app listens on `0.0.0.0` not `localhost`
   - Use the PORT environment variable from the platform

2. **Credentials not found**
   - For cloud platforms, service account JSON needs special handling
   - Consider using platform-specific credential methods

3. **CORS errors**
   - Update `CORS_ORIGINS` environment variable
   - Include your frontend domain

4. **Timeout on cold starts**
   - Increase timeout settings in platform configuration
   - Cloud Run: `--timeout=300`

5. **Memory issues**
   - Increase memory allocation in platform settings
   - Cloud Run: `--memory=512Mi`

---

## Scaling Considerations

### Horizontal Scaling
- Cloud Run auto-scales based on traffic
- For other platforms, configure auto-scaling rules
- Each instance should be stateless

### Database Scaling
- Firestore automatically scales
- Add indexes for frequently queried fields
- Consider composite indexes for complex queries

### Caching
- Add Redis for session caching
- Cache frequently accessed user data
- Implement cache invalidation strategy

---

## Health Checks

Configure health checks for your platform:

**Endpoint:** `GET /health`

**Expected Response:** 200 OK
```json
{"status": "healthy"}
```

---

## Monitoring

Set up alerts for:
- Response time > 2 seconds
- Error rate > 5%
- Memory usage > 80%
- CPU usage > 80%
- Failed authentication attempts

---

For more information, refer to the specific platform's documentation.
