import React, { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Navbar.css';

const Navbar = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
  };

  const closeMenu = () => {
    setMobileMenuOpen(false);
  };

  const isStudent = (user?.role || '').toLowerCase() === 'student';
  const isAdmin = (user?.role || '').toLowerCase() === 'admin';

  return (
    <nav className="navbar">
      <div className="navbar-container">
        {/* Brand */}
        <NavLink to="/" className="navbar-brand" onClick={closeMenu}>
          <span className="brand-icon" role="img" aria-label="graduation cap">🎓</span>
          <span className="brand-name">Campus<span className="brand-name-highlight">Complaint</span></span>
        </NavLink>

        {/* Hamburger Toggle */}
        <button
          className={`hamburger ${mobileMenuOpen ? 'active' : ''}`}
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle navigation menu"
          aria-expanded={mobileMenuOpen}
        >
          <span className="bar"></span>
          <span className="bar"></span>
          <span className="bar"></span>
        </button>

        {/* Links & Auth Actions */}
        <div className={`nav-menu ${mobileMenuOpen ? 'open' : ''}`}>
          <div className="nav-links">
            {isAuthenticated && isStudent && (
              <>
                <NavLink
                  to="/student/dashboard"
                  className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                  onClick={closeMenu}
                >
                  Dashboard
                </NavLink>
                <NavLink
                  to="/student/complaint/new"
                  className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                  onClick={closeMenu}
                >
                  + New Complaint
                </NavLink>
              </>
            )}

            {isAuthenticated && isAdmin && (
              <NavLink
                to="/admin/dashboard"
                className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                onClick={closeMenu}
              >
                Admin Console
              </NavLink>
            )}
          </div>

          <div className="nav-actions">
            {isAuthenticated ? (
              <div className="user-profile-section">
                <div className="user-info">
                  <span className="user-avatar">
                    {(user?.name || user?.email || 'U')[0].toUpperCase()}
                  </span>
                  <div className="user-details">
                    <span className="user-name">{user?.name || user?.email}</span>
                    <span className="user-role-tag">{user?.role?.toUpperCase()}</span>
                  </div>
                </div>
                <button
                  type="button"
                  className="btn-logout"
                  onClick={handleLogout}
                  title="Log out of your account"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="guest-actions">
                <NavLink
                  to="/login"
                  className={({ isActive }) => `btn btn-ghost-nav ${isActive ? 'active' : ''}`}
                  onClick={closeMenu}
                >
                  Login
                </NavLink>
                <NavLink
                  to="/register"
                  className="btn btn-nav-cta"
                  onClick={closeMenu}
                >
                  Register
                </NavLink>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
