import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import LoadingSpinner from '../components/LoadingSpinner';
import './ComplaintDetail.css';

const ComplaintDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [complaint, setComplaint] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchComplaintDetail = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const response = await api.get(`/api/complaints/${id}`);
      const data = response.data?.complaint || response.data?.data || response.data;
      setComplaint(data);
    } catch (err) {
      console.error('Error fetching complaint details:', err);
      setError(
        err.response?.data?.message ||
        'Unable to load complaint details. The ticket may not exist or you might lack authorization.'
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchComplaintDetail();
  }, [fetchComplaintDetail]);

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
      return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateString;
    }
  };

  const isAdmin = (user?.role || '').toLowerCase() === 'admin';
  const backDestination = isAdmin ? '/admin/dashboard' : '/student/dashboard';

  if (loading) {
    return <LoadingSpinner fullPage message="Loading complaint details..." />;
  }

  if (error || !complaint) {
    return (
      <div className="complaint-detail-page">
        <div className="error-card card">
          <span className="error-icon">⚠️</span>
          <h2>Complaint Not Found</h2>
          <p>{error || 'The requested complaint ticket could not be retrieved.'}</p>
          <div className="error-actions">
            <button onClick={() => navigate(backDestination)} className="btn btn-outline">
              ← Return to Dashboard
            </button>
            <button onClick={fetchComplaintDetail} className="btn btn-primary">
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const complaintId = complaint.id || complaint._id || id;
  const isResolved = (complaint.status || '').toLowerCase() === 'resolved';

  // Construct or parse timeline history
  const historyList = Array.isArray(complaint.history) && complaint.history.length > 0
    ? complaint.history
    : [
        {
          status: 'Submitted',
          date: complaint.createdAt || complaint.date,
          note: 'Complaint ticket created by student.',
          by: complaint.studentName || complaint.student?.name || 'Student',
        },
        ...(complaint.department
          ? [
              {
                status: 'Under Review',
                date: complaint.assignedAt || complaint.updatedAt || complaint.createdAt,
                note: `Assigned to department: ${complaint.department}${complaint.assignedTo || complaint.assignee ? ` (${complaint.assignedTo || complaint.assignee})` : ''}`,
                by: 'Administrator',
              },
            ]
          : []),
        ...(complaint.status && complaint.status.toLowerCase() === 'in progress'
          ? [
              {
                status: 'In Progress',
                date: complaint.updatedAt,
                note: complaint.progressNote || 'Investigation and active repair work underway.',
                by: complaint.assignedTo || complaint.department || 'Support Staff',
              },
            ]
          : []),
        ...(isResolved
          ? [
              {
                status: 'Resolved',
                date: complaint.resolvedAt || complaint.updatedAt,
                note: complaint.resolutionNote || 'The issue has been verified and marked as resolved.',
                by: 'Administration / Support Team',
              },
            ]
          : []),
      ];

  return (
    <div className="complaint-detail-page">
      {/* Top Bar Navigation */}
      <div className="detail-top-bar">
        <button
          type="button"
          onClick={() => navigate(backDestination)}
          className="btn-back"
        >
          ← Back to {isAdmin ? 'Admin Console' : 'Dashboard'}
        </button>
        <span className="ticket-id-tag">
          Ticket #{String(complaintId).slice(-8).toUpperCase()}
        </span>
      </div>

      <div className="detail-layout">
        {/* Main Details Column */}
        <div className="detail-main-column">
          <div className="detail-card card">
            <div className="detail-header">
              <div className="detail-badges">
                <span className={`badge ${getStatusBadgeClass(complaint.status)}`}>
                  {complaint.status || 'Submitted'}
                </span>
                <span className={`badge ${getPriorityBadgeClass(complaint.priority)}`}>
                  Priority: {complaint.priority || 'Low'}
                </span>
                <span className="category-tag">
                  📁 {complaint.category || 'General'}
                </span>
              </div>
              <h1 className="detail-title">{complaint.title}</h1>
              <div className="detail-meta-row">
                <span className="meta-item">
                  📅 Filed on: {formatDate(complaint.createdAt || complaint.date)}
                </span>
                {complaint.location && (
                  <span className="meta-item">
                    📍 Location: <strong>{complaint.location}</strong>
                  </span>
                )}
              </div>
            </div>

            <div className="detail-body">
              <h3>Description</h3>
              <div className="description-content">
                {complaint.description}
              </div>
            </div>

            {/* Resolution Box if resolved */}
            {(isResolved || complaint.resolutionNote) && (
              <div className="resolution-highlight-box">
                <div className="resolution-header">
                  <span className="resolution-icon">🎉</span>
                  <h4>Resolution Summary</h4>
                </div>
                <p className="resolution-text">
                  {complaint.resolutionNote || 'The complaint has been successfully resolved.'}
                </p>
                {complaint.resolvedAt && (
                  <div className="resolution-timestamp">
                    Resolved at: {formatDate(complaint.resolvedAt)}
                  </div>
                )}
              </div>
            )}

            {/* Department Assignment Info */}
            <div className="assignment-section">
              <h4>Department & Assignment</h4>
              <div className="assignment-grid">
                <div className="assignment-item">
                  <span className="assign-label">Assigned Department</span>
                  <span className="assign-val">
                    {complaint.department ? (
                      <span className="dept-badge">🏢 {complaint.department}</span>
                    ) : (
                      <span className="unassigned-text">Unassigned</span>
                    )}
                  </span>
                </div>
                <div className="assignment-item">
                  <span className="assign-label">Assigned Staff / Officer</span>
                  <span className="assign-val">
                    {complaint.assignedTo || complaint.assignee || 'Not yet assigned'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar: Status History Timeline & Info */}
        <div className="detail-sidebar-column">
          {/* Student Info Card (Especially helpful for admin or reference) */}
          {(complaint.student || complaint.studentName || complaint.studentId) && (
            <div className="sidebar-card card">
              <h4 className="sidebar-title">Student Information</h4>
              <div className="info-list">
                <div className="info-row">
                  <span className="info-key">Name:</span>
                  <span className="info-val">
                    {complaint.student?.name || complaint.studentName || 'Student'}
                  </span>
                </div>
                {(complaint.student?.email || complaint.studentEmail) && (
                  <div className="info-row">
                    <span className="info-key">Email:</span>
                    <span className="info-val">
                      {complaint.student?.email || complaint.studentEmail}
                    </span>
                  </div>
                )}
                {(complaint.student?.studentId || complaint.studentId) && (
                  <div className="info-row">
                    <span className="info-key">ID:</span>
                    <span className="info-val">
                      {complaint.student?.studentId || complaint.studentId}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Timeline Card */}
          <div className="sidebar-card card">
            <h4 className="sidebar-title">Status History & Timeline</h4>
            <div className="timeline-container">
              {historyList.map((item, index) => {
                const isLast = index === historyList.length - 1;
                return (
                  <div key={index} className={`timeline-step ${isLast ? 'active' : ''}`}>
                    <div className="timeline-marker">
                      <div className="marker-dot"></div>
                      {!isLast && <div className="marker-line"></div>}
                    </div>
                    <div className="timeline-details">
                      <div className="timeline-header">
                        <span className={`badge ${getStatusBadgeClass(item.status)}`}>
                          {item.status}
                        </span>
                        <span className="timeline-date">{formatDate(item.date)}</span>
                      </div>
                      {item.note && <p className="timeline-note">{item.note}</p>}
                      {item.by && (
                        <span className="timeline-author">Updated by: {item.by}</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplaintDetail;
