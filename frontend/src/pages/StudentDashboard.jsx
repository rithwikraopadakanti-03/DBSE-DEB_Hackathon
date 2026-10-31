import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import LoadingSpinner from '../components/LoadingSpinner';
import './StudentDashboard.css';

const StudentDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchComplaints = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get('/api/complaints');
      // Normalize response if nested under complaints or data
      const data = response.data?.complaints || response.data?.data || response.data || [];
      setComplaints(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error fetching complaints:', err);
      setError(
        err.response?.data?.message ||
        'Unable to load your complaints at this time. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchComplaints();
  }, [fetchComplaints]);

  // Status & Priority Helper Functions
  const getStatusBadgeClass = (status = '') => {
    const s = status.toLowerCase().replace(/[\s_]+/g, '-');
    if (s.includes('under-review') || s.includes('review')) return 'badge-status-under-review';
    if (s.includes('in-progress') || s.includes('progress')) return 'badge-status-in-progress';
    if (s.includes('resolved')) return 'badge-status-resolved';
    if (s.includes('closed')) return 'badge-status-closed';
    return 'badge-status-submitted';
  };

  const getPriorityBadgeClass = (priority = '') => {
    const p = priority.toLowerCase();
    if (p === 'critical') return 'badge-priority-critical';
    if (p === 'high') return 'badge-priority-high';
    if (p === 'medium') return 'badge-priority-medium';
    return 'badge-priority-low';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  // Stats calculation
  const totalCount = complaints.length;
  const resolvedCount = complaints.filter(
    (c) => (c.status || '').toLowerCase() === 'resolved'
  ).length;
  const pendingCount = complaints.filter((c) => {
    const s = (c.status || '').toLowerCase();
    return s !== 'resolved' && s !== 'closed';
  }).length;

  // Filter complaints
  const filteredComplaints = complaints.filter((item) => {
    const matchesStatus =
      statusFilter === 'ALL' ||
      (item.status || '').toLowerCase().replace(/[\s_]+/g, '') ===
        statusFilter.toLowerCase().replace(/[\s_]+/g, '');

    const matchesSearch =
      !searchTerm ||
      (item.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (item.category || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      String(item.id || item._id || '').toLowerCase().includes(searchTerm.toLowerCase());

    return matchesStatus && matchesSearch;
  });

  return (
    <div className="student-dashboard">
      {/* Header Banner */}
      <div className="dashboard-header card">
        <div className="welcome-section">
          <span className="welcome-badge">Student Portal</span>
          <h1>Welcome, {user?.name || 'Student'}! 👋</h1>
          <p>
            Track your submitted issues or report a new facility concern on campus.
          </p>
        </div>
        <div className="header-action">
          <Link to="/student/complaint/new" className="btn btn-secondary btn-new-complaint">
            <span className="btn-icon">➕</span>
            <span>Submit New Complaint</span>
          </Link>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="stats-grid">
        <div className="stat-card card">
          <div className="stat-icon-wrapper icon-total">
            <span>📋</span>
          </div>
          <div className="stat-info">
            <span className="stat-label">Total Complaints</span>
            <span className="stat-value">{totalCount}</span>
          </div>
        </div>

        <div className="stat-card card">
          <div className="stat-icon-wrapper icon-pending">
            <span>⏳</span>
          </div>
          <div className="stat-info">
            <span className="stat-label">Pending Action</span>
            <span className="stat-value">{pendingCount}</span>
          </div>
        </div>

        <div className="stat-card card">
          <div className="stat-icon-wrapper icon-resolved">
            <span>✅</span>
          </div>
          <div className="stat-info">
            <span className="stat-label">Resolved Issues</span>
            <span className="stat-value">{resolvedCount}</span>
          </div>
        </div>
      </div>

      {/* Main Complaints Section */}
      <div className="complaints-section card">
        <div className="section-toolbar">
          <div className="toolbar-title-group">
            <h2>Your Complaints History</h2>
            <span className="count-pill">{filteredComplaints.length} shown</span>
          </div>

          <div className="toolbar-controls">
            <div className="search-box">
              <span className="search-icon">🔍</span>
              <input
                type="text"
                placeholder="Search by title, category, ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <div className="filter-box">
              <label htmlFor="filterStatus">Status:</label>
              <select
                id="filterStatus"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="ALL">All Statuses</option>
                <option value="Submitted">Submitted</option>
                <option value="Under Review">Under Review</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Closed">Closed</option>
              </select>
            </div>
          </div>
        </div>

        {/* Content area */}
        {loading ? (
          <LoadingSpinner message="Fetching your complaints..." />
        ) : error ? (
          <div className="error-container">
            <p className="error-text">⚠️ {error}</p>
            <button onClick={fetchComplaints} className="btn btn-outline btn-sm">
              Try Again
            </button>
          </div>
        ) : filteredComplaints.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-illustration">📭</div>
            <h3>No Complaints Found</h3>
            <p>
              {complaints.length === 0
                ? "You haven't submitted any complaints yet. If you have an issue on campus, let us know!"
                : 'No complaints match your active search or status filter.'}
            </p>
            {complaints.length === 0 ? (
              <Link to="/student/complaint/new" className="btn btn-primary">
                Submit Your First Complaint
              </Link>
            ) : (
              <button
                className="btn btn-outline"
                onClick={() => {
                  setStatusFilter('ALL');
                  setSearchTerm('');
                }}
              >
                Reset Filters
              </button>
            )}
          </div>
        ) : (
          <div className="table-responsive">
            <table className="complaints-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Title</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredComplaints.map((complaint) => {
                  const complaintId = complaint.id || complaint._id || 'N/A';
                  return (
                    <tr
                      key={complaintId}
                      className="complaint-row"
                      onClick={() => navigate(`/student/complaint/${complaintId}`)}
                    >
                      <td className="complaint-id-cell">
                        #{String(complaintId).slice(-6).toUpperCase()}
                      </td>
                      <td className="complaint-title-cell">
                        <div className="cell-title">{complaint.title}</div>
                        {complaint.location && (
                          <div className="cell-location">📍 {complaint.location}</div>
                        )}
                      </td>
                      <td>
                        <span className="category-pill">{complaint.category || 'General'}</span>
                      </td>
                      <td>
                        <span className={`badge ${getPriorityBadgeClass(complaint.priority)}`}>
                          {complaint.priority || 'Low'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${getStatusBadgeClass(complaint.status)}`}>
                          {complaint.status || 'Submitted'}
                        </span>
                      </td>
                      <td className="date-cell">
                        {formatDate(complaint.createdAt || complaint.date)}
                      </td>
                      <td className="text-right" onClick={(e) => e.stopPropagation()}>
                        <Link
                          to={`/student/complaint/${complaintId}`}
                          className="btn btn-ghost btn-sm btn-view-detail"
                        >
                          View Details →
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default StudentDashboard;
