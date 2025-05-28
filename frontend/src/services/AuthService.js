import axios from 'axios';
import Cookies from 'js-cookie'; // For reading CSRF token

const API_URL = process.env.REACT_APP_AUTH_API_URL || 'http://localhost:8002/auth';

// Create an Axios instance for auth requests
const authAxios = axios.create({
    baseURL: API_URL,
    withCredentials: true, // Send cookies with requests
});

// Interceptor to add CSRF token to mutating requests
authAxios.interceptors.request.use(config => {
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method.toUpperCase())) {
        const csrfToken = Cookies.get('csrf_access_token');
        if (csrfToken) {
            config.headers['X-CSRF-Token'] = csrfToken;
        }
    }
    return config;
}, error => {
    return Promise.reject(error);
});


const login = async (username, password) => {
    try {
        // The backend now sets HttpOnly cookies.
        // The response body might contain user info or just a success message.
        const response = await authAxios.post(`/token`, 
            new URLSearchParams({
                username: username,
                password: password
            }),
            {
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded'
                }
            }
        );
        // The CSRF token needed for subsequent requests is also set as a cookie.
        // The body of the response might also contain it for the initial grab if needed.
        // Example: const initialCsrfToken = response.data.csrf_token_in_body_for_initial_grab;
        // Cookies.set('csrf_access_token', initialCsrfToken); // If backend doesn't set it directly as cookie
        return response.data; // e.g., { message: "Login successful", username: "...", csrf_token_in_body_for_initial_grab: "..." }
    } catch (error) {
        console.error('Login failed:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Login failed');
    }
};

const register = async (username, email, password) => {
    try {
        // Register endpoint might not set auth cookies immediately, depends on app flow
        // (e.g., if it requires email verification before login)
        const response = await authAxios.post(`/users/`, {
            username,
            email,
            password
        });
        return response.data;
    } catch (error) {
        console.error('Registration failed:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Registration failed');
    }
};

const logout = async () => {
    try {
        // Call backend logout which clears HttpOnly cookies and revokes tokens
        await authAxios.post(`/logout`);
    } catch (error) {
        console.error('Logout failed:', error.response ? error.response.data : error.message);
        // Even if backend call fails, frontend should clear its perception of auth state
    }
    // Frontend state (e.g., in AuthContext) will be cleared by the caller of this service method.
    // Cookies are cleared by the backend.
};

const getCurrentUser = () => {
    // With HttpOnly cookies, JS can't directly check if the access_token cookie exists.
    // The presence of a csrf_access_token might be an indicator, or a specific non-HttpOnly "session_active" cookie.
    // For now, we rely on API calls to /users/me to confirm auth status.
    // This function might become less useful, or just return a placeholder if csrf_access_token exists.
    if (Cookies.get('csrf_access_token')) { // Check if CSRF token exists as a proxy for session
        return { isAuthenticated: true }; // This is a simplified representation
    }
    return null;
};

const getUserProfile = async () => {
    // This call will succeed if HttpOnly access_token cookie is present and valid.
    try {
        const response = await authAxios.get(`/users/me`);
        return response.data; // User profile from backend
    } catch (error) {
        console.error('Failed to fetch user profile:', error.response ? error.response.data : error.message);
        // If 401, AuthContext or caller should handle logout/redirect
        throw error.response ? error.response.data : new Error('Failed to fetch profile');
    }
};

const refreshToken = async () => {
    try {
        // The refresh token is in an HttpOnly cookie, backend reads it.
        // No need to send refresh_token in body.
        const response = await authAxios.post(`/token/refresh`);
        // Backend sets new access_token and csrf_access_token cookies.
        // Response body might include new CSRF token for immediate use if needed.
        return response.data;
    } catch (error) {
        console.error('Token refresh failed:', error.response ? error.response.data : error.message);
        throw error.response ? error.response.data : new Error('Token refresh failed');
    }
};


const AuthService = {
    login,
    register,
    logout,
    getCurrentUser, // Use with caution, see comments
    getUserProfile,
    refreshToken
};

export default AuthService;
