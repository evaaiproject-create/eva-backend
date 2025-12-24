/**
 * Example JavaScript/TypeScript client for Eva Backend API.
 * 
 * This demonstrates how to interact with Eva from a web application.
 * Works in both browser and Node.js environments.
 * 
 * Prerequisites:
 *   npm install axios
 *   For Google OAuth: npm install @react-oauth/google (for React apps)
 */

class EvaClient {
  /**
   * Initialize Eva client
   * @param {string} baseUrl - Base URL of Eva backend API
   */
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.accessToken = null;
    this.user = null;
  }

  /**
   * Get headers for authenticated requests
   * @private
   */
  _getHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }
    
    return headers;
  }

  /**
   * Register a new user
   * @param {string} googleIdToken - Google ID token from OAuth flow
   * @param {string} deviceId - Optional device identifier
   */
  async register(googleIdToken, deviceId = null) {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_token: googleIdToken,
        device_id: deviceId
      })
    });

    if (!response.ok) {
      throw new Error(`Registration failed: ${response.statusText}`);
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    this.user = data.user;

    return data;
  }

  /**
   * Login existing user
   * @param {string} googleIdToken - Google ID token from OAuth flow
   * @param {string} deviceId - Optional device identifier
   */
  async login(googleIdToken, deviceId = null) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id_token: googleIdToken,
        device_id: deviceId
      })
    });

    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    this.user = data.user;

    return data;
  }

  /**
   * Get current user profile
   */
  async getProfile() {
    const response = await fetch(`${this.baseUrl}/users/me`, {
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get profile: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get user's registered devices
   */
  async getDevices() {
    const response = await fetch(`${this.baseUrl}/users/me/devices`, {
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get devices: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Register a new device
   * @param {string} deviceId - Device identifier
   */
  async addDevice(deviceId) {
    const response = await fetch(`${this.baseUrl}/users/me/devices/${deviceId}`, {
      method: 'POST',
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to add device: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get user preferences
   */
  async getPreferences() {
    const response = await fetch(`${this.baseUrl}/users/me/preferences`, {
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get preferences: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Update user preferences
   * @param {Object} preferences - Preferences object
   */
  async updatePreferences(preferences) {
    const response = await fetch(`${this.baseUrl}/users/me/preferences`, {
      method: 'PUT',
      headers: this._getHeaders(),
      body: JSON.stringify(preferences)
    });

    if (!response.ok) {
      throw new Error(`Failed to update preferences: ${response.statusText}`);
    }

    return await response.json();
  }

  // Session Management (Cross-Device Sync)

  /**
   * Create a new session for cross-device sync
   * @param {string} deviceId - Device identifier
   * @param {Object} initialData - Optional initial session data
   */
  async createSession(deviceId, initialData = {}) {
    const response = await fetch(`${this.baseUrl}/sessions?device_id=${deviceId}`, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(initialData)
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get all user sessions
   */
  async getSessions() {
    const response = await fetch(`${this.baseUrl}/sessions`, {
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get sessions: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get specific session by ID
   * @param {string} sessionId - Session identifier
   */
  async getSession(sessionId) {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`, {
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get session: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Update session data
   * @param {string} sessionId - Session identifier
   * @param {Object} data - Data to update
   */
  async updateSession(sessionId, data) {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`, {
      method: 'PUT',
      headers: this._getHeaders(),
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`Failed to update session: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Delete a session
   * @param {string} sessionId - Session identifier
   */
  async deleteSession(sessionId) {
    const response = await fetch(`${this.baseUrl}/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to delete session: ${response.statusText}`);
    }

    return await response.json();
  }

  // Function Calling

  /**
   * List all available functions
   */
  async listFunctions() {
    const response = await fetch(`${this.baseUrl}/functions`, {
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to list functions: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Execute a function
   * @param {string} functionName - Name of function to call
   * @param {Object} parameters - Function parameters
   * @param {string} deviceId - Optional device identifier
   */
  async callFunction(functionName, parameters = {}, deviceId = null) {
    const url = new URL(`${this.baseUrl}/functions/call`);
    url.searchParams.append('function_name', functionName);
    if (deviceId) {
      url.searchParams.append('device_id', deviceId);
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: this._getHeaders(),
      body: JSON.stringify(parameters)
    });

    if (!response.ok) {
      throw new Error(`Failed to call function: ${response.statusText}`);
    }

    return await response.json();
  }

  /**
   * Get function call history
   * @param {number} limit - Maximum number of records
   */
  async getFunctionHistory(limit = 50) {
    const response = await fetch(`${this.baseUrl}/functions/history?limit=${limit}`, {
      headers: this._getHeaders()
    });

    if (!response.ok) {
      throw new Error(`Failed to get function history: ${response.statusText}`);
    }

    return await response.json();
  }
}

// Export for Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = EvaClient;
}

// Example usage in browser
/*
// Initialize client
const eva = new EvaClient('http://localhost:8000');

// After getting Google ID token from OAuth flow
async function handleGoogleLogin(idToken) {
  try {
    const result = await eva.login(idToken, 'browser_001');
    console.log('Logged in as:', result.user.email);
    
    // Get user preferences
    const preferences = await eva.getPreferences();
    console.log('Preferences:', preferences);
    
    // Call a function
    const calcResult = await eva.callFunction('calculate', {
      operation: 'add',
      a: 10,
      b: 5
    });
    console.log('Result:', calcResult.result);
    
    // Create session for cross-device sync
    const session = await eva.createSession('browser_001', {
      page: 'home',
      scroll_position: 0
    });
    console.log('Session created:', session.session_id);
    
  } catch (error) {
    console.error('Error:', error);
  }
}
*/

// Example usage in Node.js
/*
const EvaClient = require('./javascript_client');

async function main() {
  const eva = new EvaClient('http://localhost:8000');
  
  // Your implementation here
  // Note: You'll need to implement Google OAuth flow separately
}

main().catch(console.error);
*/
