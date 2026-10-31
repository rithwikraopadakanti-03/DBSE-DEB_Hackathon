import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Login.css';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!email.trim() || !password) {
      setError('Please provide both email and password.');
      return;
    }

    setSubmitting(true);
    try {
      const result = await login(email.trim(), password);
      const user = result.user;
      
      const role = (user?.role || '').toLowerCase();
      const redirectPath = role === 'admin' ? '/admin/dashboard' : '/student/dashboard';
      
      // If user came from a protected page matching their role, use that; otherwise go to role dashboard
      const fromPath = location.state?.from?.pathname;
      if (fromPath && !fromPath.includes('/login') && !fromPath.includes('/register')) {
        if (role === 'admin' && fromPath.startsWith('/admin')) {
          navigate(fromPath, { replace: true });
          return;
        }
        if (role === 'student' && fromPath.startsWith('/student')) {
          navigate(fromPath, { replace: true });
          return;
        }
      }

      navigate(redirectPath, { replace: true });
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <div className="auth-card">
        {/* Left Hero (Desktop) */}
        <div className="auth-hero">
          <div className="hero-content">
            <div className="hero-badge">Campus Support</div>
            <h2>Smart Campus Complaint Resolution</h2>
            <p>
              Report issues quickly, track progress in real-time, and experience
              AI-assisted triage for faster resolutions.
            </p>
            <div className="hero-highlights">
              <div className="highlight-item">
                <span className="highlight-icon">⚡</span>
                <div>
                  <strong>AI Smart Triage</strong>
                  <span>Instant category & priority suggestion</span>
                </div>
              </div>
              <div className="highlight-item">
                <span className="highlight-icon">📍</span>
                <div>
                  <strong>Live Tracking</strong>
                  <span>Step-by-step resolution status updates</span>
                </div>
              </div>
              <div className="highlight-item">
                <span className="highlight-icon">🛡️</span>
                <div>
                  <strong>Administrative Oversight</strong>
                  <span>Direct routing to responsible campus departments</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Form */}
        <div className="auth-form-wrapper">
          <div className="auth-header">
            <h1 className="auth-title">Welcome Back</h1>
            <p className="auth-desc">Sign in with your campus credentials to continue</p>
          </div>

          {location.state?.successMessage && (
            <div className="alert alert-success" role="status">
              <span>✅</span>
              <span>{location.state.successMessage}</span>
            </div>
          )}

          {error && (
            <div className="alert alert-error" role="alert">
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            <div className="form-group">
              <label htmlFor="login-email">Campus Email</label>
              <input
                id="login-email"
                type="email"
                placeholder="e.g. student@campus.edu or admin@campus.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary auth-submit-btn"
              disabled={submitting}
            >
              {submitting ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="auth-footer">
            <p>
              Don't have an account?{' '}
              <Link to="/register" className="auth-link">
                Register here
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
