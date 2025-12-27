# Eva v0.1 - Personal Assistant Backend

🤖 A personal assistant backend inspired by **JARVIS** from Marvel Cinematic Universe and **Baymax** from Big Hero 6.

## Overview

Eva is a scalable, cloud-based backend system that provides:

- **Google OAuth Authentication** - Secure user authentication via Google
- **Multi-User Support** - Supports up to 5 users by default (configurable and scalable)
- **Firestore Storage** - Cloud-based data persistence with Google Firestore
- **Cross-Device Sync** - Seamless experience across multiple devices
- **Function Calling Framework** - Extensible system for adding new capabilities
- **Real-Time Speech Services** - Speech-to-Text (STT) and Text-to-Speech (TTS)
- **AI-Powered Conversations** - OpenAI-powered chat with memory management
- **WebSocket Support** - Real-time bidirectional communication
- **RESTful API** - Well-documented API for all operations

## Technology Stack

- **Framework**: FastAPI (Python 3.9+)
- **Authentication**: Google OAuth 2.0
- **Database**: Google Cloud Firestore
- **Speech**: Google Cloud Speech-to-Text, Google Cloud Text-to-Speech, OpenAI Whisper
- **AI**: OpenAI GPT models for conversations and memory summarization
- **Real-Time**: WebSockets for duplex communication
- **Security**: JWT tokens, Bearer authentication
- **Deployment**: Docker, Google Cloud Run, or any Python hosting service

## Features

### 🔐 Authentication
- Google OAuth 2.0 integration
- JWT token-based authentication
- Secure user registration and login
- User limit enforcement (default: 5 users)

### 👤 User Management
- User profiles with preferences
- Multi-device support per user
- Device registration and tracking
- User preferences storage

### 🔄 Cross-Device Sync
- Session-based synchronization
- Real-time state sharing across devices
- Device-specific session data
- Automatic session management

### ⚡ Function Calling
- Dynamic function registry
- Built-in utility functions (echo, calculate, time)
- Function call history and analytics
- Easy to extend with new functions

### 🎤 Speech Services
- **Speech-to-Text (STT)**: Convert audio to text
  - OpenAI Whisper (robust in noisy environments)
  - Google Cloud Speech-to-Text
  - Modular engine switching
- **Text-to-Speech (TTS)**: Convert text to audio
  - Google Cloud TTS with neural voices
  - Custom engine support (extendable)
  - Multiple voice options

### 🧠 Memory Management
- **Short-Term Context**: Recent conversation history
- **Long-Term Memory**: Persistent user preferences, facts, and goals
- **AI Summarization**: Compress conversations to key facts
- **Context Building**: Combine short and long-term memory for AI

### 💬 AI Conversation
- OpenAI GPT-powered responses
- Context-aware conversations
- Intent detection (acknowledgments, commands, interruptions)
- Configurable AI parameters

### 🔌 WebSocket API
- Real-time bidirectional communication
- Live audio streaming
- Cross-device message sync
- Interrupt handling for TTS playback

## Project Structure

```
Eva-v0.1/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── models/
│   │   └── __init__.py        # Data models (User, Session, etc.)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Authentication logic
│   │   ├── firestore_service.py  # Firestore operations
│   │   ├── function_service.py   # Function calling framework
│   │   ├── stt_service.py     # Speech-to-Text service
│   │   ├── tts_service.py     # Text-to-Speech service
│   │   ├── memory_service.py  # Memory management
│   │   └── conversation_service.py  # AI conversation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py            # Auth endpoints
│   │   ├── users.py           # User management endpoints
│   │   ├── sessions.py        # Session sync endpoints
│   │   ├── functions.py       # Function calling endpoints
│   │   ├── speech.py          # STT/TTS endpoints
│   │   ├── conversation.py    # AI chat endpoints
│   │   ├── memory.py          # Memory CRUD endpoints
│   │   └── websocket.py       # Real-time WebSocket
│   └── utils/
│       ├── __init__.py
│       └── dependencies.py    # FastAPI dependencies
├── tests/                     # Unit and integration tests
│   ├── conftest.py
│   ├── test_function_service.py
│   ├── test_conversation_service.py
│   ├── test_speech_services.py
│   └── test_api_endpoints.py
├── examples/                  # Client examples
│   ├── python_client.py
│   └── javascript_client.js
├── main.py                    # Application entry point
├── requirements.txt           # Python dependencies
├── pytest.ini                 # Test configuration
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Docker Compose setup
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

## Setup Instructions

### Prerequisites

1. Python 3.8 or higher
2. Google Cloud Project with Firestore enabled
3. Google OAuth 2.0 credentials

### Google Cloud Setup

1. **Create a Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Firestore**
   - Navigate to Firestore in the console
   - Create a database in Native mode
   - Choose a location for your data

3. **Create Service Account**
   - Go to IAM & Admin > Service Accounts
   - Create a new service account
   - Grant "Cloud Datastore User" role
   - Create and download a JSON key
   - Save it as `service-account-key.json` in the project root

4. **Setup OAuth 2.0**
   - Go to APIs & Services > Credentials
   - Create OAuth 2.0 Client ID
   - Configure consent screen
   - Add authorized redirect URIs
   - Note down the Client ID and Client Secret

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/evaaiproject-create/Eva-v0.1.git
   cd Eva-v0.1
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

   Required variables:
   ```env
   GOOGLE_CLOUD_PROJECT=your-project-id
   GOOGLE_APPLICATION_CREDENTIALS=service-account-key.json
   GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret
   API_SECRET_KEY=your-super-secret-key
   ```

   Optional variables (for speech and AI features):
   ```env
   TTS_ENGINE=google      # Options: google, custom
   STT_ENGINE=whisper     # Options: whisper, google
   OPENAI_API_KEY=your-openai-api-key  # Required for AI chat and Whisper STT
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Run tests**
   ```bash
   pytest tests/ -v
   ```

## API Documentation

Once running, access the interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /auth/register` - Register new user with Google OAuth
- `POST /auth/login` - Login existing user
- `GET /auth/verify` - Verify JWT token

#### Users
- `GET /users/me` - Get current user profile
- `GET /users/me/devices` - List user's devices
- `POST /users/me/devices/{device_id}` - Register a device
- `GET /users/me/preferences` - Get user preferences
- `PUT /users/me/preferences` - Update user preferences

#### Sessions (Cross-Device Sync)
- `POST /sessions` - Create new session
- `GET /sessions` - List user's sessions
- `GET /sessions/{session_id}` - Get specific session
- `PUT /sessions/{session_id}` - Update session data
- `DELETE /sessions/{session_id}` - Delete session

#### Functions
- `GET /functions` - List available functions
- `POST /functions/call` - Execute a function
- `GET /functions/history` - Get function call history

#### Speech (STT/TTS)
- `POST /speech/transcribe` - Transcribe audio file to text
- `POST /speech/transcribe/base64` - Transcribe base64 audio to text
- `GET /speech/stt/engines` - List available STT engines
- `POST /speech/synthesize` - Convert text to speech audio
- `GET /speech/tts/engines` - List available TTS engines
- `GET /speech/tts/voices` - List available TTS voices

#### Conversation (AI Chat)
- `POST /conversation/chat` - Send message and get AI response
- `GET /conversation/history` - Get conversation history
- `DELETE /conversation/history` - Clear conversation history
- `POST /conversation/intent` - Analyze message intent
- `POST /conversation/compress-memory` - Compress short-term to long-term memory

#### Memory
- `POST /memory` - Save information to long-term memory
- `GET /memory` - Get long-term memories
- `GET /memory/search` - Search memories by keyword
- `GET /memory/{memory_id}` - Get specific memory
- `PUT /memory/{memory_id}` - Update a memory
- `DELETE /memory/{memory_id}` - Delete a memory
- `GET /memory/context/recent` - Get recent short-term context
- `DELETE /memory/context` - Clear short-term context
- `POST /memory/summarize` - Summarize conversations with AI
- `POST /memory/compress` - Compress to long-term memory

#### WebSocket
- `WS /ws/speech/{device_id}` - Real-time speech communication

## Usage Examples

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "GOOGLE_ID_TOKEN_HERE",
    "device_id": "device_001"
  }'
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1...",
  "token_type": "bearer",
  "user": {
    "uid": "google_123",
    "email": "user@example.com",
    "display_name": "John Doe",
    "role": "user",
    "devices": ["device_001"]
  }
}
```

### 2. Call a Function

```bash
curl -X POST "http://localhost:8000/functions/call" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "function_name": "calculate",
    "parameters": {
      "operation": "add",
      "a": 5,
      "b": 3
    }
  }'
```

Response:
```json
{
  "success": true,
  "result": {
    "result": 8
  },
  "execution_time": 0.001
}
```

### 3. Chat with Eva (AI Conversation)

```bash
curl -X POST "http://localhost:8000/conversation/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can you help me with today?",
    "include_memory": true
  }'
```

Response:
```json
{
  "success": true,
  "message": "Hello! I'm Eva, your personal assistant. I can help you with...",
  "model": "gpt-3.5-turbo",
  "usage": {
    "prompt_tokens": 150,
    "completion_tokens": 80,
    "total_tokens": 230
  }
}
```

### 4. Text-to-Speech (Synthesize)

```bash
curl -X POST "http://localhost:8000/speech/synthesize?text=Hello%20World&language=en-US" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response:
```json
{
  "audio_base64": "//uQxAAAAAANIAAAAAE...",
  "content_type": "audio/mp3",
  "duration_seconds": 0.8,
  "engine": "google"
}
```

### 5. Save Memory

```bash
curl -X POST "http://localhost:8000/memory" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "category": "preference",
    "content": "User prefers dark mode",
    "importance": 7
  }'
```

### 6. Create a Session for Cross-Device Sync

```bash
curl -X POST "http://localhost:8000/sessions" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_001",
    "initial_data": {
      "conversation_state": "active",
      "last_message": "Hello Eva"
    }
  }'
```

### 7. WebSocket Connection

```javascript
// Connect to WebSocket with authentication
const ws = new WebSocket('ws://localhost:8000/ws/speech/device_001?token=YOUR_JWT_TOKEN');

ws.onopen = () => {
  console.log('Connected to Eva');
  
  // Send a chat message
  ws.send(JSON.stringify({
    type: 'chat',
    message: 'Hello Eva!',
    include_audio: true
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Response:', data);
};
```

## Extending Eva

### Adding New Functions

To add new capabilities to Eva, register functions in the `FunctionRegistry`:

```python
# In app/services/function_service.py

def my_custom_function(param1: str, param2: int) -> dict:
    """Your custom function logic."""
    result = f"Processed {param1} with {param2}"
    return {"result": result}

# Register the function
function_registry.register(
    name="my_custom_function",
    func=my_custom_function,
    description="Description of what it does",
    parameters_schema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "integer"}
        },
        "required": ["param1", "param2"]
    }
)
```

### Scaling Beyond 5 Users

To support more users, update the `MAX_USERS` environment variable:

```env
MAX_USERS=100
```

For production scale, consider:
- Implementing proper database indexing
- Adding caching (Redis)
- Load balancing
- Rate limiting per user
- Monitoring and logging

## Security Considerations

1. **Never commit credentials** - Keep `.env` and service account keys out of version control
2. **Use strong secret keys** - Generate secure random strings for `API_SECRET_KEY`
3. **Enable HTTPS** - Always use HTTPS in production
4. **Validate inputs** - All inputs are validated using Pydantic models
5. **Rate limiting** - Consider adding rate limiting for production
6. **Token expiration** - JWT tokens expire after 7 days by default

## Deployment

### Deploy to Google Cloud Run

1. **Build container**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/eva-backend
   ```

2. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy eva-backend \
     --image gcr.io/YOUR_PROJECT_ID/eva-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

### Deploy to Other Platforms

Eva can be deployed to:
- Heroku
- AWS Elastic Beanstalk
- Azure App Service
- DigitalOcean App Platform
- Any platform supporting Python/FastAPI

## Troubleshooting

### Common Issues

1. **"Could not automatically determine credentials"**
   - Ensure `GOOGLE_APPLICATION_CREDENTIALS` points to valid service account JSON
   - Check that the service account has Firestore permissions

2. **"User limit reached"**
   - Increase `MAX_USERS` in environment variables
   - Or remove users from Firestore to make space

3. **"Invalid Google ID token"**
   - Ensure `GOOGLE_CLIENT_ID` matches your OAuth client
   - Token may have expired - request a new one from client

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

This project is for educational and personal use.

## Acknowledgments

Inspired by:
- **JARVIS** - Marvel Cinematic Universe
- **Baymax** - Big Hero 6

Built with modern Python tools and Google Cloud Platform.

---

**Questions or Issues?** Open an issue on GitHub or contact the development team.
