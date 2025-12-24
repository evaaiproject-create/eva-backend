"""
Example Python client for Eva Backend API.

This demonstrates how to:
1. Register/Login with Google OAuth
2. Make authenticated API calls
3. Use cross-device sync sessions
4. Call functions

Prerequisites:
    pip install requests google-auth-oauthlib
"""
import requests
from typing import Optional, Dict, Any


class EvaClient:
    """Client for interacting with Eva Backend API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize Eva client.
        
        Args:
            base_url: Base URL of the Eva backend API
        """
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.user: Optional[Dict] = None
    
    def _headers(self) -> Dict[str, str]:
        """Get headers for authenticated requests."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    def register(self, google_id_token: str, device_id: Optional[str] = None) -> Dict:
        """
        Register a new user.
        
        Args:
            google_id_token: Google ID token from OAuth flow
            device_id: Optional device identifier
            
        Returns:
            Registration response with access token and user info
        """
        response = requests.post(
            f"{self.base_url}/auth/register",
            json={"id_token": google_id_token, "device_id": device_id}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.user = data["user"]
        
        return data
    
    def login(self, google_id_token: str, device_id: Optional[str] = None) -> Dict:
        """
        Login existing user.
        
        Args:
            google_id_token: Google ID token from OAuth flow
            device_id: Optional device identifier
            
        Returns:
            Login response with access token and user info
        """
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"id_token": google_id_token, "device_id": device_id}
        )
        response.raise_for_status()
        
        data = response.json()
        self.access_token = data["access_token"]
        self.user = data["user"]
        
        return data
    
    def get_profile(self) -> Dict:
        """Get current user profile."""
        response = requests.get(
            f"{self.base_url}/users/me",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_devices(self) -> list:
        """Get list of user's registered devices."""
        response = requests.get(
            f"{self.base_url}/users/me/devices",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def add_device(self, device_id: str) -> Dict:
        """Register a new device."""
        response = requests.post(
            f"{self.base_url}/users/me/devices/{device_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_preferences(self) -> Dict:
        """Get user preferences."""
        response = requests.get(
            f"{self.base_url}/users/me/preferences",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def update_preferences(self, preferences: Dict[str, Any]) -> Dict:
        """Update user preferences."""
        response = requests.put(
            f"{self.base_url}/users/me/preferences",
            json=preferences,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    # Session Management (Cross-Device Sync)
    
    def create_session(self, device_id: str, initial_data: Dict = None) -> Dict:
        """Create a new session for cross-device sync."""
        response = requests.post(
            f"{self.base_url}/sessions",
            params={"device_id": device_id},
            json=initial_data or {},
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_sessions(self) -> list:
        """Get all user sessions."""
        response = requests.get(
            f"{self.base_url}/sessions",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_session(self, session_id: str) -> Dict:
        """Get specific session by ID."""
        response = requests.get(
            f"{self.base_url}/sessions/{session_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> Dict:
        """Update session data."""
        response = requests.put(
            f"{self.base_url}/sessions/{session_id}",
            json=data,
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def delete_session(self, session_id: str) -> Dict:
        """Delete a session."""
        response = requests.delete(
            f"{self.base_url}/sessions/{session_id}",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    # Function Calling
    
    def list_functions(self) -> Dict:
        """List all available functions."""
        response = requests.get(
            f"{self.base_url}/functions",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def call_function(self, function_name: str, parameters: Dict = None, 
                     device_id: str = None) -> Dict:
        """
        Execute a function.
        
        Args:
            function_name: Name of function to call
            parameters: Function parameters
            device_id: Optional device identifier
            
        Returns:
            Function response with result or error
        """
        response = requests.post(
            f"{self.base_url}/functions/call",
            params={
                "function_name": function_name,
                "device_id": device_id
            },
            json=parameters or {},
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()
    
    def get_function_history(self, limit: int = 50) -> list:
        """Get function call history."""
        response = requests.get(
            f"{self.base_url}/functions/history",
            params={"limit": limit},
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    # Initialize client
    client = EvaClient("http://localhost:8000")
    
    # Note: In a real application, you would get google_id_token from OAuth flow
    # For this example, we'll show the structure
    
    print("Eva Client Example")
    print("=" * 50)
    
    # Example 1: Register/Login (you need a real Google ID token)
    # try:
    #     result = client.login(google_id_token="YOUR_GOOGLE_ID_TOKEN", device_id="laptop_001")
    #     print(f"Logged in as: {result['user']['email']}")
    # except Exception as e:
    #     print(f"Login failed: {e}")
    
    # For demo purposes, let's assume we're already logged in
    # client.access_token = "YOUR_ACCESS_TOKEN_HERE"
    
    # Example 2: Get profile
    # profile = client.get_profile()
    # print(f"User profile: {profile}")
    
    # Example 3: Update preferences
    # client.update_preferences({
    #     "theme": "dark",
    #     "language": "en",
    #     "notifications": True
    # })
    
    # Example 4: List available functions
    # functions = client.list_functions()
    # print(f"Available functions: {list(functions.keys())}")
    
    # Example 5: Call a function
    # result = client.call_function("calculate", {
    #     "operation": "add",
    #     "a": 10,
    #     "b": 5
    # })
    # print(f"Calculation result: {result}")
    
    # Example 6: Create a session for cross-device sync
    # session = client.create_session("laptop_001", {
    #     "conversation_state": "active",
    #     "context": {"last_topic": "weather"}
    # })
    # print(f"Created session: {session['session_id']}")
    
    # Example 7: Update session from another device
    # client.update_session(session['session_id'], {
    #     "conversation_state": "paused",
    #     "last_action": "user_switched_device"
    # })
    
    print("\nTo use this client:")
    print("1. Set up Google OAuth and get an ID token")
    print("2. Call client.login() or client.register()")
    print("3. Use the various methods to interact with Eva")
    print("\nSee the code above for examples!")
