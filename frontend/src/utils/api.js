/**
 * Safe API Utility Functions
 * Prevents "Body has already been consumed" errors
 */

/**
 * Safe JSON parsing from fetch response
 * Always parses JSON only once and handles errors gracefully
 * 
 * @param {Response} response - Fetch response object
 * @returns {Promise<{ok: boolean, data: any, error: string|null}>}
 */
export async function safeJsonParse(response) {
  let data = null;
  let error = null;
  
  try {
    data = await response.json();
  } catch (parseErr) {
    // JSON parsing failed - might be empty response or invalid JSON
    error = parseErr.message;
    data = {};
  }
  
  return {
    ok: response.ok,
    status: response.status,
    data,
    error: !response.ok ? (data?.detail || data?.message || error || 'Request failed') : null
  };
}

/**
 * Fetch with safe JSON parsing
 * Wraps fetch and automatically parses JSON response safely
 * 
 * @param {string} url - API endpoint URL
 * @param {object} options - Fetch options (method, headers, body, etc.)
 * @returns {Promise<{ok: boolean, status: number, data: any, error: string|null}>}
 */
export async function safeFetch(url, options = {}) {
  try {
    const response = await fetch(url, options);
    return await safeJsonParse(response);
  } catch (networkErr) {
    return {
      ok: false,
      status: 0,
      data: null,
      error: networkErr.message || 'Network error'
    };
  }
}

/**
 * API client with authentication
 * Automatically includes Authorization header and handles errors
 * 
 * @param {string} baseUrl - Base API URL
 * @param {string} token - JWT token for authentication
 */
export function createApiClient(baseUrl, token) {
  const defaultHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };

  return {
    async get(endpoint) {
      return safeFetch(`${baseUrl}${endpoint}`, {
        method: 'GET',
        headers: defaultHeaders
      });
    },

    async post(endpoint, body = null) {
      return safeFetch(`${baseUrl}${endpoint}`, {
        method: 'POST',
        headers: defaultHeaders,
        ...(body ? { body: JSON.stringify(body) } : {})
      });
    },

    async put(endpoint, body) {
      return safeFetch(`${baseUrl}${endpoint}`, {
        method: 'PUT',
        headers: defaultHeaders,
        body: JSON.stringify(body)
      });
    },

    async delete(endpoint) {
      return safeFetch(`${baseUrl}${endpoint}`, {
        method: 'DELETE',
        headers: defaultHeaders
      });
    }
  };
}
