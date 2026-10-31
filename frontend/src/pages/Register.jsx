import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Register.css';

const Register = () => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    role: 'student',
    studentId: '',
  });

  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const validate = () => {
    const { name, email, password, confirmPassword, role, studentId } = formData;

    if (!name.trim()) return 'Full Name is required.';
    if (!email.trim()) return 'Email is required.';

    // Email format validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email.trim())) {
      return 'Please enter a valid email address.';
    }

    if (!password) return 'Password is required.';
    if (password.length < 6) return 'Password must be at least 6 characters long.';
    if (password !== confirmPassword) return 'Passwords do not match.';

    if (role === 'student' && !studentId.trim()) {
      return 'Student ID is required for student accounts.';
    }

    return null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        name: formData.name.trim(),
        email: formData.email.trim(),
        password: formData.password,
        role: formData.role,
      };

      if (formData.role === 'student') {
        payload.studentId = formData.studentId.trim();
      }

      await register(payload);

      // On success, redirect to login with state message
      navigate('/login', {
        state: { successMessage: 'Registration successful! You can now sign in with your credentials.' },
      });
    } catch (err) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="register-page">
      <div className="register-card">
        <div className="register-header">
          <div className="brand-pill">
            <span role="img" aria-label="student">🎓</span> Campus Portal
          </div>
          <h1>Create an Account</h1>
          <p>Join the Campus Complaint Management System</p>
        </div>

        {error && (
          <div className="alert alert-error" role="alert">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="register-form" noValidate>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input
                id="name"
                name="name"
                type="text"
                placeholder="e.g. Jane Doe"
                value={formData.name}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="email">Campus Email *</label>
              <input
                id="email"
                name="email"
                type="email"
                placeholder="e.g. jane@campus.edu"
                value={formData.email}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="role">Role *</label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleChange}
              >
                <option value="student">Student</option>
                <option value="admin">Admin</option>
              </select>
            </div>

            {formData.role === 'student' ? (
              <div className="form-group">
                <label htmlFor="studentId">Student ID *</label>
                <input
                  id="studentId"
                  name="studentId"
                  type="text"
                  placeholder="e.g. STU-2024-001"
                  value={formData.studentId}
                  onChange={handleChange}
                  required
                />
              </div>
            ) : (
              <div className="form-group">
                <label htmlFor="adminDept">Department / Affiliation</label>
                <input
                  id="adminDept"
                  type="text"
                  placeholder="e.g. Administration"
                  disabled
                  value="Campus Administration"
                />
              </div>
            )}
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="password">Password *</label>
              <input
                id="password"
                name="password"
                type="password"
                placeholder="Minimum 6 characters"
                value={formData.password}
                onChange={handleChange}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm Password *</label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="Repeat password"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />
            </div>
          </div>

          <button
            type="submit"
            className="btn btn-primary register-submit-btn"
            disabled={submitting}
          >
            {submitting ? 'Creating Account...' : 'Complete Registration'}
          </button>
        </form>

        <div className="register-footer">
          <p>
            Already registered?{' '}
            <Link to="/login" className="auth-link">
              Sign In to Your Account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Register;
