import axios from 'axios';
import Cookies from 'js-cookie';

const api = axios.create({
    // No baseURL here, as each service might have a different one,
    // or it can be set if all microservices are behind a single gateway.
    // For this project, each service sets its own baseURL.
    withCredentials: true, // Send cookies with all requests from this instance
});

// Request interceptor to add CSRF token
api.interceptors.request.use(
    config => {
        if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(config.method.toUpperCase())) {
            const csrfToken = Cookies.get('csrf_access_token'); // Name must match cookie set by backend
            if (csrfToken) {
                config.headers['X-CSRF-Token'] = csrfToken;
            } else {
                // Optionally handle missing CSRF token, e.g., by warning or preventing request
                console.warn('CSRF token not found for mutating request to', config.url);
            }
        }
        return config;
    },
    error => {
        return Promise.reject(error);
    }
);

// Response interceptor for handling 401 errors (e.g., token expired)
// This is a basic example; more sophisticated logic might be needed for token refresh.
api.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config;
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true; // Mark to prevent infinite retry loops
            console.log("Received 401, attempting token refresh...");
            try {
                // Assume AuthService is correctly set up and refreshToken handles cookie-based refresh
                // This import creates a potential circular dependency if AuthService also imports this 'api' instance.
                // It's better if refreshToken logic is self-contained or AuthService uses a raw axios instance for refresh.
                // For now, let's assume it's handled carefully, or AuthService.refreshToken uses a different axios instance.
                
                // Dynamically import AuthService to try and break circular dependency if AuthService imports this 'api'
                const AuthService = (await import('./AuthService')).default; 
                await AuthService.refreshToken(); // Backend sets new cookies
                console.log("Token refresh successful, retrying original request.");
                // Update headers if needed (CSRF token might change after refresh)
                // Then retry the original request with the new token (which is now in cookie)
                return api(originalRequest);
            } catch (refreshError) {
                console.error("Token refresh failed:", refreshError);
                // If refresh fails, redirect to login or trigger logout
                // This should ideally be handled by AuthContext or a global error handler
                // For now, just re-throw the error from refresh attempt.
                // AuthService.logout(); // Trigger logout
                // window.location.href = '/login'; // Force redirect
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export default api;
