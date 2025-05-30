import React, { useContext } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, AuthContext } from './contexts/AuthContext';
import LoginPage from './pages/Auth/LoginPage';
import RegisterPage from './pages/Auth/RegisterPage';
import ACManagementPage from './pages/AC/ACManagementPage'; // Using actual component
import PolicySynthesisPage from './pages/Synthesis/PolicySynthesisPage'; // Using actual component
import PolicyListPage from './pages/Policies/PolicyListPage'; // Using actual component
import Layout from './components/Layout/Layout'; // Import Layout

// HomePage component (can be moved to pages/Home/HomePage.js later)
const HomePage = () => {
    const { currentUser } = useContext(AuthContext); // Removed logout from here, handled by Layout
    return (
        <div>
            <h1>Welcome to the Governance Framework</h1>
            {currentUser ? (
                <div>
                    <p>You are logged in as: {currentUser.profile?.username || 'User'}.</p>
                    <p>Access token (first 10 chars): {currentUser.access_token.substring(0,10)}...</p>
                    {currentUser.profile && <p>Full Name from Profile: {currentUser.profile.full_name || 'N/A'}</p>}
                    <p>Use the navigation bar to manage different aspects of the system.</p>
                </div>
            ) : (
                <p>Please login or register to use the application features.</p>
            )}
        </div>
    );
};

// ProtectedRoute component
const ProtectedRoute = ({ children }) => {
    const { currentUser, loading } = useContext(AuthContext);

    if (loading) {
        return <div>Loading authentication status...</div>; // Or a spinner
    }

    if (!currentUser) {
        return <Navigate to="/login" replace />;
    }
    return children;
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <Layout> {/* Wrap all routes within Layout */}
                    <Routes>
                        <Route path="/" element={<HomePage />} />
                        <Route path="/login" element={<LoginPage />} />
                        <Route path="/register" element={<RegisterPage />} />
                        
                        {/* Protected Routes */}
                        <Route 
                            path="/ac-management" 
                            element={<ProtectedRoute><ACManagementPage /></ProtectedRoute>} 
                        />
                        <Route 
                            path="/policy-synthesis" 
                            element={<ProtectedRoute><PolicySynthesisPage /></ProtectedRoute>} 
                        />
                        <Route 
                            path="/policies" 
                            element={<ProtectedRoute><PolicyListPage /></ProtectedRoute>} 
                        />
                        
                        {/* Add more routes as needed */}
                        <Route path="*" element={<div>404 Not Found - Page does not exist</div>} />
                    </Routes>
                </Layout>
            </Router>
        </AuthProvider>
    );
}

export default App;
