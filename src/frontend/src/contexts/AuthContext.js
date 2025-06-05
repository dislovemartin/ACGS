import React, { createContext, useState, useEffect, useCallback } from 'react';
import AuthService from '../services/AuthService';
import Cookies from 'js-cookie'; // To check for CSRF token as proxy for session

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [currentUser, setCurrentUser] = useState(null); // Will store user profile data
    const [isAuthenticated, setIsAuthenticated] = useState(false); // Separate flag
    const [loading, setLoading] = useState(true);

    const verifyAuthStatus = useCallback(async () => {
        setLoading(true);
        // Check for CSRF token as a hint of an active session.
        // The definitive check is fetching user profile.
        const csrfToken = Cookies.get('csrf_access_token');
        if (!csrfToken) {
            // If no CSRF token, likely no session or cookies were cleared.
            setCurrentUser(null);
            setIsAuthenticated(false);
            setLoading(false);
            return;
        }

        try {
            // Attempt to fetch user profile. This will succeed if HttpOnly access_token is valid.
            const profile = await AuthService.getUserProfile();
            setCurrentUser(profile); // Store profile data
            setIsAuthenticated(true);
        } catch (error) {
            console.warn("Auth verification failed (e.g., token expired or invalid):", error.message);
            setCurrentUser(null);
            setIsAuthenticated(false);
            // AuthService.logout() might be called by the api interceptor on 401
            // if not, or if error is different, ensure cookies are cleared if possible
            // (though JS can't clear HttpOnly ones directly)
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        verifyAuthStatus();
    }, [verifyAuthStatus]);

    const login = async (username, password) => {
        // AuthService.login now handles setting cookies via backend.
        // It returns { message: "...", username: "...", csrf_token_in_body_for_initial_grab: "..." }
        const loginResponse = await AuthService.login(username, password);
        // After successful login, cookies are set. Verify status and fetch profile.
        await verifyAuthStatus(); 
        return loginResponse; // Return original login response
    };

    const register = async (username, email, password) => {
        // Register doesn't automatically log in or set auth cookies in current backend setup
        return await AuthService.register(username, email, password);
    };

    const logout = async () => {
        try {
            await AuthService.logout(); // Calls backend to clear HttpOnly cookies & revoke tokens
        } catch (error) {
            console.error("Error during backend logout:", error);
        } finally {
            // Clear frontend state regardless of backend call success
            setCurrentUser(null);
            setIsAuthenticated(false);
            // Cookies (like csrf_access_token) should be cleared by backend.
            // If any non-HttpOnly frontend cookies related to auth, clear them here.
            // Cookies.remove('csrf_access_token'); // Backend should handle this.
        }
    };

    const value = {
        currentUser, // This is now the user's profile data
        isAuthenticated,
        loading,
        login,
        register,
        logout,
        checkCurrentUser // Expose if manual re-check needed
    };

    return (
        <AuthContext.Provider value={value}>
            {!loading && children} {/* Don't render children until initial auth check is done */}
        </AuthContext.Provider>
    );
};
