import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../../contexts/AuthContext';
import './Layout.css'; // Create this CSS file for basic styling

const Layout = ({ children }) => {
    const { currentUser, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login'); // Redirect to login after logout
    };

    return (
        <>
            <header className="app-header">
                <nav className="app-nav">
                    <Link to="/" className="nav-logo">GovFrame</Link>
                    <ul className="nav-links">
                        <li><Link to="/">Home</Link></li>
                        <li><Link to="/public-consultation">Public Consultation</Link></li>
                        {currentUser ? (
                            <>
                                <li><Link to="/ac-management">AC Mgmt</Link></li>
                                <li><Link to="/policy-synthesis">Synthesize</Link></li>
                                <li><Link to="/policies">View Policies</Link></li>
                                <li><button onClick={handleLogout} className="logout-button">Logout ({currentUser.profile?.username || 'User'})</button></li>
                            </>
                        ) : (
                            <>
                                <li><Link to="/login">Login</Link></li>
                                <li><Link to="/register">Register</Link></li>
                            </>
                        )}
                    </ul>
                </nav>
            </header>
            <main className="app-main">
                {children}
            </main>
            <footer className="app-footer">
                <p>&copy; 2024 Governance Framework Project</p>
            </footer>
        </>
    );
};

export default Layout;
