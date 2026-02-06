"""
================================================================================
API PACKAGE INITIALIZATION
================================================================================

PURPOSE:
    This file makes the app/api/ directory a Python package and exports
    all API router modules.

ROUTERS:
    auth      - Authentication (login, register, token verification)
    users     - User profile management
    sessions  - Cross-device session synchronization
    functions - Dynamic function calling framework
    chat      - Chat with EVA using Gemini AI (NEW!)

================================================================================
"""

from app.api import auth, users, sessions, functions, chat

__all__ = ["auth", "users", "sessions", "functions", "chat"]
