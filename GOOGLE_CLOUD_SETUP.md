# Google Cloud Setup Guide for Eva

This guide walks you through setting up Google Cloud services for Eva backend.

## Prerequisites

- Google account
- Credit card (for Google Cloud billing, free tier available)

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top
3. Click "NEW PROJECT"
4. Enter project details:
   - **Project name**: `eva-assistant` (or your preferred name)
   - **Organization**: (optional)
   - **Location**: (optional)
5. Click "CREATE"
6. Wait for project creation and select it

### 2. Enable Required APIs

1. In the Cloud Console, go to **APIs & Services > Library**
2. Search for and enable the following APIs:
   - **Cloud Firestore API**
   - **Identity Toolkit API** (for authentication)
   - **Cloud Resource Manager API**

### 3. Set Up Firestore Database

1. In the Cloud Console, go to **Firestore**
2. Click "CREATE DATABASE"
3. Choose your mode:
   - **Native mode** (recommended for new apps)
   - Location: Choose closest to your users (e.g., `us-central1`)
4. Click "CREATE DATABASE"
5. Wait for database creation

#### Firestore Security Rules (Optional but Recommended)

Go to **Firestore > Rules** and set:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users collection - users can only read/write their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Sessions collection - users can only access their own sessions
    match /sessions/{sessionId} {
      allow read, write: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
    }
    
    // Function calls - users can only access their own history
    match /function_calls/{callId} {
      allow read: if request.auth != null && 
        resource.data.user_id == request.auth.uid;
      allow write: if request.auth != null;
    }
  }
}
```

### 4. Create Service Account

Service accounts allow your backend to authenticate with Google Cloud services.

1. Go to **IAM & Admin > Service Accounts**
2. Click "CREATE SERVICE ACCOUNT"
3. Enter service account details:
   - **Service account name**: `eva-backend`
   - **Description**: "Service account for Eva backend application"
4. Click "CREATE AND CONTINUE"
5. Grant roles:
   - **Cloud Datastore User** (for Firestore access)
   - Click "CONTINUE"
6. Click "DONE"

#### Download Service Account Key

1. In the service accounts list, find your `eva-backend` account
2. Click the three dots menu on the right
3. Select "Manage keys"
4. Click "ADD KEY" > "Create new key"
5. Choose **JSON** format
6. Click "CREATE"
7. Save the downloaded JSON file as `service-account-key.json`
8. **⚠️ IMPORTANT**: Keep this file secure! Never commit it to version control

### 5. Set Up OAuth 2.0

OAuth 2.0 allows users to authenticate with their Google accounts.

#### Configure OAuth Consent Screen

1. Go to **APIs & Services > OAuth consent screen**
2. Choose user type:
   - **Internal** (if using Google Workspace)
   - **External** (for public use)
3. Click "CREATE"
4. Fill in the OAuth consent screen:
   - **App name**: `Eva Personal Assistant`
   - **User support email**: Your email
   - **Developer contact email**: Your email
   - **Authorized domains**: (add your domain if you have one)
5. Click "SAVE AND CONTINUE"
6. **Scopes**: Click "ADD OR REMOVE SCOPES"
   - Add: `openid`, `email`, `profile`
   - Click "UPDATE" then "SAVE AND CONTINUE"
7. **Test users** (if External): Add test user emails
8. Click "SAVE AND CONTINUE" then "BACK TO DASHBOARD"

#### Create OAuth Client ID

1. Go to **APIs & Services > Credentials**
2. Click "CREATE CREDENTIALS" > "OAuth client ID"
3. Choose application type:
   - **Web application** (for web apps)
   - **iOS** or **Android** (for mobile apps)
   - **Desktop app** (for desktop apps)
4. Configure the application:
   - **Name**: `Eva Web Client`
   - **Authorized JavaScript origins** (for web):
     - `http://localhost:3000` (development)
     - `https://yourdomain.com` (production)
   - **Authorized redirect URIs**:
     - `http://localhost:3000/auth/callback` (development)
     - `https://yourdomain.com/auth/callback` (production)
5. Click "CREATE"
6. **Save the Client ID and Client Secret** - you'll need these!

### 6. Configure Eva Backend

Create a `.env` file in your Eva project:

```env
# Google Cloud Project
GOOGLE_CLOUD_PROJECT=eva-assistant

# Service Account (path to the JSON file)
GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json

# OAuth 2.0 Credentials
GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-AbCdEfGhIjKlMnOpQrStUvWx

# API Configuration
API_SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32
API_HOST=0.0.0.0
API_PORT=8000

# User Management
MAX_USERS=5

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Environment
ENVIRONMENT=development
```

### 7. Test the Setup

Run a simple test to verify everything is configured correctly:

```python
# test_setup.py
from google.cloud import firestore
import os

# Set credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"

# Test Firestore connection
try:
    db = firestore.Client(project="eva-assistant")
    print("✅ Firestore connection successful!")
    
    # Try to write a test document
    doc_ref = db.collection("test").document("setup_test")
    doc_ref.set({"test": "success", "timestamp": firestore.SERVER_TIMESTAMP})
    print("✅ Write test successful!")
    
    # Try to read it back
    doc = doc_ref.get()
    if doc.exists:
        print("✅ Read test successful!")
        print(f"   Data: {doc.to_dict()}")
    
    # Clean up
    doc_ref.delete()
    print("✅ Setup verification complete!")
    
except Exception as e:
    print(f"❌ Setup failed: {e}")
```

Run the test:
```bash
pip install google-cloud-firestore
python test_setup.py
```

## Security Best Practices

### 1. Protect Service Account Keys

- Never commit `service-account-key.json` to version control
- Add it to `.gitignore`
- Store securely in production (use secret managers)

### 2. Use Environment Variables

- Never hardcode credentials in code
- Use `.env` file for local development
- Use platform secret managers in production:
  - Google Secret Manager
  - AWS Secrets Manager
  - HashiCorp Vault

### 3. Restrict API Keys

1. Go to **APIs & Services > Credentials**
2. Find your OAuth Client ID
3. Restrict usage:
   - Set application restrictions
   - Set API restrictions
   - Add allowed domains/IPs

### 4. Enable Firestore Security Rules

Always use security rules in production to prevent unauthorized access.

### 5. Monitor Usage

1. Go to **IAM & Admin > Quotas**
2. Set up alerts for:
   - API usage
   - Firestore operations
   - Authentication attempts

### 6. Regular Audits

- Review IAM permissions regularly
- Rotate service account keys periodically
- Check audit logs for suspicious activity

## Cost Management

### Free Tier Limits

Google Cloud offers generous free tiers:

**Firestore**:
- 1 GB storage
- 50,000 document reads/day
- 20,000 document writes/day
- 20,000 document deletes/day

**Authentication**:
- Free for most use cases
- Pay-as-you-go for advanced features

### Monitor Costs

1. Go to **Billing > Budgets & alerts**
2. Create a budget:
   - Set amount (e.g., $5/month)
   - Set alert thresholds (50%, 75%, 100%)
3. Receive email alerts when approaching limits

### Cost Optimization Tips

1. Use Firestore efficiently:
   - Batch operations where possible
   - Cache frequently accessed data
   - Use composite indexes wisely

2. Clean up unused resources:
   - Delete old sessions
   - Archive old function call logs
   - Remove unused service accounts

## Troubleshooting

### "Could not automatically determine credentials"

**Cause**: Service account key not found or GOOGLE_APPLICATION_CREDENTIALS not set

**Solution**:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Or in Python:
```python
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"
```

### "Permission denied" errors

**Cause**: Service account doesn't have required permissions

**Solution**:
1. Go to **IAM & Admin > IAM**
2. Find your service account
3. Click "Edit" and add "Cloud Datastore User" role

### "Invalid OAuth token"

**Cause**: Client ID doesn't match or token expired

**Solution**:
- Verify GOOGLE_CLIENT_ID matches your OAuth client
- Request a new token from the client side

### Firestore quota exceeded

**Cause**: Exceeded free tier limits

**Solution**:
- Check **Firestore > Usage** for details
- Optimize queries and caching
- Consider upgrading to paid tier if needed

## Production Checklist

Before deploying to production:

- [ ] Service account key stored securely (not in code)
- [ ] Firestore security rules enabled
- [ ] OAuth redirect URIs configured for production domain
- [ ] CORS origins set to production domain
- [ ] Budget alerts configured
- [ ] Monitoring/logging enabled
- [ ] Backup strategy in place
- [ ] API restrictions configured
- [ ] Environment set to "production"
- [ ] HTTPS enabled on all endpoints

## Additional Resources

- [Firestore Documentation](https://firebase.google.com/docs/firestore)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [Service Account Best Practices](https://cloud.google.com/iam/docs/best-practices-service-accounts)
- [Cloud Console](https://console.cloud.google.com/)

## Support

If you encounter issues:
1. Check the [troubleshooting section](#troubleshooting)
2. Review Google Cloud documentation
3. Check Eva backend logs
4. Open an issue on GitHub

---

**Next Steps**: After completing this setup, return to the main README.md to continue with Eva backend installation.
