import React, { useState, useEffect, useCallback, useMemo } from 'react';
import api from '../api/axios';
import LoadingSpinner from '../components/LoadingSpinner';
import './AdminDashboard.css';

const DEPARTMENTS = [
  'Electrical Department',
  'Civil & Maintenance',
  'IT Infrastructure & Support',
  'Hostel Administration',
  'Canteen & Catering',
  'Campus Transport Services',
  'Academic Affairs Office',
  'Campus Security',
];

const STATUSES = ['Submitted', 'Under Review', 'In Progress', 'Resolved', 'Closed'];
const PRIORITIES = ['Low', 'Medium', 'High', 'Critical'];
const CATEGORIES = [
  'Electrical',
  'Maintenance',
  'IT Support',
  'Hostel Administration',
  'Canteen',
  'Transport',
  'Academic',
  'Security',
];

const AdminDashboard = () => {
  // Main Data States
  const [complaints, setComplaints] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionSuccess, setActionSuccess] = useState('');

  // Filtering & Pagination States
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [categoryFilter, setCategoryFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  // Modals State
  const [activeModal, setActiveModal] = useState(null); // 'assign' | 'status' | 'resolve' | 'detail' | null
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');

  // Form states for modals
  const [assignForm, setAssignForm] = useState({ department: '', assignee: '' });
  const [statusForm, setStatusForm] = useState({ status: 'Under Review', note: '' });
  const [resolveForm, setResolveForm] = useState({ resolutionNote: '' });

  // Open Actions menu dropdown on a row
  const [openDropdownId, setOpenDropdownId] = useState(null);

  // Close open action dropdown if clicked outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (!e.target.closest('.action-menu-container')) {
        setOpenDropdownId(null);
      }
    };
    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, []);

  // Fetch complaints & stats
  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      // Fetch complaints
      let complaintsData = [];
      try {
        const resComplaints = await api.get('/api/admin/complaints');
        complaintsData =
          resComplaints.data?.complaints ||
          resComplaints.data?.data ||
          resComplaints.data ||
          [];
      } catch (err) {
        // Fallback to standard endpoint if admin endpoint varies
        const resFallback = await api.get('/api/complaints');
        complaintsData =
          resFallback.data?.complaints ||
          resFallback.data?.data ||
          resFallback.data ||
          [];
      }

      setComplaints(Array.isArray(complaintsData) ? complaintsData : []);

      // Fetch stats
      try {
        const resStats = await api.get('/api/admin/stats');
        setStats(resStats.data?.stats || resStats.data?.data || resStats.data);
      } catch {
        // Stats can be computed locally from complaints list
        setStats(null);
      }
    } catch (err) {
      console.error('Error fetching admin data:', err);
      setError(
        err.response?.data?.message ||
        'Failed to load administrative records. Please verify server connection.'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Status & Priority CSS Helper
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
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  // Compute stats if not returned by server
  const computedStats = useMemo(() => {
    const total = stats?.total ?? complaints.length;
    const resolved =
      stats?.resolved ??
      complaints.filter((c) => (c.status || '').toLowerCase() === 'resolved').length;
    const open =
      stats?.open ??
      complaints.filter((c) => {
        const s = (c.status || '').toLowerCase();
        return s !== 'resolved' && s !== 'closed';
      }).length;
    const critical =
      stats?.critical ??
      complaints.filter((c) => (c.priority || '').toLowerCase() === 'critical').length;

    // Category breakdown
    const categoryCounts = {};
    complaints.forEach((c) => {
      const cat = c.category || 'Other';
      categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
    });

    // Status breakdown
    const statusCounts = {};
    complaints.forEach((c) => {
      const st = c.status || 'Submitted';
      statusCounts[st] = (statusCounts[st] || 0) + 1;
    });

    return { total, open, resolved, critical, categoryCounts, statusCounts };
  }, [stats, complaints]);

  // Filter complaints
  const filteredComplaints = useMemo(() => {
    return complaints.filter((c) => {
      // Status
      if (statusFilter !== 'ALL') {
        const itemStatus = (c.status || '').toLowerCase().replace(/[\s_]+/g, '');
        const targetStatus = statusFilter.toLowerCase().replace(/[\s_]+/g, '');
        if (itemStatus !== targetStatus) return false;
      }
      // Category
      if (categoryFilter !== 'ALL' && c.category !== categoryFilter) {
        return false;
      }
      // Priority
      if (priorityFilter !== 'ALL' && c.priority?.toLowerCase() !== priorityFilter.toLowerCase()) {
        return false;
      }
      // Search
      if (searchTerm.trim()) {
        const term = searchTerm.toLowerCase();
        const id = String(c.id || c._id || '').toLowerCase();
        const title = (c.title || '').toLowerCase();
        const student = (c.studentName || c.student?.name || c.studentEmail || '').toLowerCase();
        const dept = (c.department || '').toLowerCase();
        const cat = (c.category || '').toLowerCase();

        return (
          id.includes(term) ||
          title.includes(term) ||
          student.includes(term) ||
          dept.includes(term) ||
          cat.includes(term)
        );
      }
      return true;
    });
  }, [complaints, statusFilter, categoryFilter, priorityFilter, searchTerm]);

  // Reset page when filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [statusFilter, categoryFilter, priorityFilter, searchTerm]);

  // Paginated Complaints
  const totalPages = Math.ceil(filteredComplaints.length / pageSize) || 1;
  const paginatedComplaints = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredComplaints.slice(start, start + pageSize);
  }, [filteredComplaints, currentPage, pageSize]);

  // Modal Triggers
  const openAssignModal = (complaint) => {
    setSelectedComplaint(complaint);
    setAssignForm({
      department: complaint.department || DEPARTMENTS[0],
      assignee: complaint.assignedTo || complaint.assignee || '',
    });
    setModalError('');
    setActiveModal('assign');
    setOpenDropdownId(null);
  };

  const openStatusModal = (complaint) => {
    setSelectedComplaint(complaint);
    setStatusForm({
      status: complaint.status || 'Under Review',
      note: '',
    });
    setModalError('');
    setActiveModal('status');
    setOpenDropdownId(null);
  };

  const openResolveModal = (complaint) => {
    setSelectedComplaint(complaint);
    setResolveForm({
      resolutionNote: complaint.resolutionNote || '',
    });
    setModalError('');
    setActiveModal('resolve');
    setOpenDropdownId(null);
  };

  const openDetailModal = (complaint) => {
    setSelectedComplaint(complaint);
    setActiveModal('detail');
    setOpenDropdownId(null);
  };

  const closeModal = () => {
    setActiveModal(null);
    setSelectedComplaint(null);
    setModalError('');
    setModalLoading(false);
  };

  // Handlers for Submitting Modal Forms
  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;
    const complaintId = selectedComplaint.id || selectedComplaint._id;

    if (!assignForm.department) {
      setModalError('Please select a department.');
      return;
    }

    setModalLoading(true);
    setModalError('');
    try {
      await api.put(`/api/admin/complaints/${complaintId}/assign`, {
        department: assignForm.department,
        assignedTo: assignForm.assignee.trim(),
        assignee: assignForm.assignee.trim(),
      });

      // Update state locally
      setComplaints((prev) =>
        prev.map((c) =>
          (c.id || c._id) === complaintId
            ? {
                ...c,
                department: assignForm.department,
                assignedTo: assignForm.assignee.trim(),
                assignee: assignForm.assignee.trim(),
                status: c.status === 'Submitted' ? 'Under Review' : c.status,
              }
            : c
        )
      );

      setActionSuccess(`Department successfully assigned to Complaint #${String(complaintId).slice(-6).toUpperCase()}`);
      setTimeout(() => setActionSuccess(''), 4000);
      closeModal();
    } catch (err) {
      console.error('Assign error:', err);
      setModalError(err.response?.data?.message || 'Failed to assign department.');
    } finally {
      setModalLoading(false);
    }
  };

  const handleStatusSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;
    const complaintId = selectedComplaint.id || selectedComplaint._id;

    setModalLoading(true);
    setModalError('');
    try {
      await api.put(`/api/admin/complaints/${complaintId}/status`, {
        status: statusForm.status,
        note: statusForm.note.trim(),
      });

      // Update state locally
      setComplaints((prev) =>
        prev.map((c) =>
          (c.id || c._id) === complaintId
            ? { ...c, status: statusForm.status, updatedAt: new Date().toISOString() }
            : c
        )
      );

      setActionSuccess(`Status updated to "${statusForm.status}" for Complaint #${String(complaintId).slice(-6).toUpperCase()}`);
      setTimeout(() => setActionSuccess(''), 4000);
      closeModal();
    } catch (err) {
      console.error('Status update error:', err);
      setModalError(err.response?.data?.message || 'Failed to update complaint status.');
    } finally {
      setModalLoading(false);
    }
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;
    const complaintId = selectedComplaint.id || selectedComplaint._id;

    if (!resolveForm.resolutionNote.trim()) {
      setModalError('Please enter a resolution summary or explanation.');
      return;
    }

    setModalLoading(true);
    setModalError('');
    try {
      await api.put(`/api/admin/complaints/${complaintId}/resolve`, {
        resolutionNote: resolveForm.resolutionNote.trim(),
        note: resolveForm.resolutionNote.trim(),
        status: 'Resolved',
      });

      // Update state locally
      setComplaints((prev) =>
        prev.map((c) =>
          (c.id || c._id) === complaintId
            ? {
                ...c,
                status: 'Resolved',
                resolutionNote: resolveForm.resolutionNote.trim(),
                resolvedAt: new Date().toISOString(),
              }
            : c
        )
      );

      setActionSuccess(`Complaint #${String(complaintId).slice(-6).toUpperCase()} has been marked as Resolved!`);
      setTimeout(() => setActionSuccess(''), 4000);
      closeModal();
    } catch (err) {
      console.error('Resolve error:', err);
      setModalError(err.response?.data?.message || 'Failed to mark complaint as resolved.');
    } finally {
      setModalLoading(false);
    }
  };

  return (
    <div className="admin-dashboard">
      {/* Header */}
      <div className="admin-header card">
        <div className="admin-header-title">
          <span className="admin-badge">Admin Workspace</span>
          <h1>Campus Complaints Management Console</h1>
          <p>
            Monitor, assign departments, triage priority complaints, and supervise campus-wide resolution pipelines.
          </p>
        </div>
        <div className="admin-header-right">
          <button onClick={fetchData} className="btn btn-outline btn-refresh" title="Refresh complaints and stats">
            🔄 Refresh Data
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="alert alert-success" role="status">
          <span>✅</span>
          <span>{actionSuccess}</span>
        </div>
      )}

      {error && (
        <div className="alert alert-error" role="alert">
          <span>⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {/* 4 Stat Cards Overview */}
      <div className="admin-stats-grid">
        <div className="admin-stat-card card">
          <div className="stat-icon-box total-box">📋</div>
          <div className="stat-content">
            <span className="stat-label">Total Logged</span>
            <span className="stat-number">{computedStats.total}</span>
            <span className="stat-sub">Across all campus categories</span>
          </div>
        </div>

        <div className="admin-stat-card card">
          <div className="stat-icon-box open-box">⚡</div>
          <div className="stat-content">
            <span className="stat-label">Active / Open</span>
            <span className="stat-number">{computedStats.open}</span>
            <span className="stat-sub">Requiring action or in progress</span>
          </div>
        </div>

        <div className="admin-stat-card card">
          <div className="stat-icon-box resolved-box">✅</div>
          <div className="stat-content">
            <span className="stat-label">Resolved Issues</span>
            <span className="stat-number">{computedStats.resolved}</span>
            <span className="stat-sub">Verified & concluded tickets</span>
          </div>
        </div>

        <div className="admin-stat-card card">
          <div className="stat-icon-box critical-box">🔥</div>
          <div className="stat-content">
            <span className="stat-label">Critical Priority</span>
            <span className="stat-number">{computedStats.critical}</span>
            <span className="stat-sub">Immediate attention flagged</span>
          </div>
        </div>
      </div>

      {/* Pure CSS Charts Overview Section */}
      <div className="charts-overview-grid">
        {/* Category Breakdown Chart */}
        <div className="chart-card card">
          <div className="chart-header">
            <h3>Complaints by Category</h3>
            <span className="chart-meta">Distribution</span>
          </div>
          <div className="css-chart-body">
            {CATEGORIES.map((cat) => {
              const count = computedStats.categoryCounts[cat] || 0;
              const percent = computedStats.total > 0 ? Math.round((count / computedStats.total) * 100) : 0;
              return (
                <div key={cat} className="bar-row">
                  <div className="bar-label-group">
                    <span className="bar-label">{cat}</span>
                    <span className="bar-count">{count} ({percent}%)</span>
                  </div>
                  <div className="bar-track">
                    <div
                      className="bar-fill category-fill"
                      style={{ width: `${percent}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Status Distribution Chart */}
        <div className="chart-card card">
          <div className="chart-header">
            <h3>Status Breakdown</h3>
            <span className="chart-meta">Lifecycle</span>
          </div>
          <div className="css-chart-body">
            {STATUSES.map((st) => {
              const count = computedStats.statusCounts[st] || 0;
              const percent = computedStats.total > 0 ? Math.round((count / computedStats.total) * 100) : 0;
              
              let fillClass = 'status-fill-submitted';
              if (st === 'Under Review') fillClass = 'status-fill-review';
              if (st === 'In Progress') fillClass = 'status-fill-progress';
              if (st === 'Resolved') fillClass = 'status-fill-resolved';
              if (st === 'Closed') fillClass = 'status-fill-closed';

              return (
                <div key={st} className="bar-row">
                  <div className="bar-label-group">
                    <span className="bar-label">{st}</span>
                    <span className="bar-count">{count} ({percent}%)</span>
                  </div>
                  <div className="bar-track">
                    <div
                      className={`bar-fill ${fillClass}`}
                      style={{ width: `${percent}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Complaints Management Table */}
      <div className="admin-table-section card">
        <div className="table-controls-bar">
          <div className="table-title-area">
            <h2>Complaints Directory</h2>
            <span className="records-badge">{filteredComplaints.length} Records</span>
          </div>

          <div className="filters-row">
            {/* Search Input */}
            <div className="search-input-wrapper">
              <span className="search-symbol">🔍</span>
              <input
                type="text"
                placeholder="Search student, title, ID, dept..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter by Status"
            >
              <option value="ALL">All Statuses</option>
              {STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>

            {/* Category Filter */}
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              aria-label="Filter by Category"
            >
              <option value="ALL">All Categories</option>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>

            {/* Priority Filter */}
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              aria-label="Filter by Priority"
            >
              <option value="ALL">All Priorities</option>
              {PRIORITIES.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Table Content */}
        {loading ? (
          <LoadingSpinner message="Fetching campus complaints..." />
        ) : filteredComplaints.length === 0 ? (
          <div className="empty-table-state">
            <span className="empty-icon">📂</span>
            <h3>No Complaints Found</h3>
            <p>No complaints match your active filters or query parameters.</p>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => {
                setSearchTerm('');
                setStatusFilter('ALL');
                setCategoryFilter('ALL');
                setPriorityFilter('ALL');
              }}
            >
              Reset All Filters
            </button>
          </div>
        ) : (
          <>
            <div className="table-responsive">
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Student</th>
                    <th>Title</th>
                    <th>Category</th>
                    <th>Priority</th>
                    <th>Department</th>
                    <th>Status</th>
                    <th>Date</th>
                    <th className="text-center">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedComplaints.map((complaint) => {
                    const complaintId = complaint.id || complaint._id || 'N/A';
                    const studentName =
                      complaint.studentName ||
                      complaint.student?.name ||
                      complaint.studentEmail ||
                      'Student';

                    return (
                      <tr key={complaintId} className="admin-row">
                        <td className="id-col">
                          #{String(complaintId).slice(-6).toUpperCase()}
                        </td>
                        <td className="student-col">
                          <span className="student-name">{studentName}</span>
                          {(complaint.student?.studentId || complaint.studentId) && (
                            <span className="student-sub-id">
                              {complaint.student?.studentId || complaint.studentId}
                            </span>
                          )}
                        </td>
                        <td className="title-col">
                          <span className="complaint-title" title={complaint.title}>
                            {complaint.title}
                          </span>
                          {complaint.location && (
                            <span className="location-badge">📍 {complaint.location}</span>
                          )}
                        </td>
                        <td>
                          <span className="table-category-tag">{complaint.category || 'General'}</span>
                        </td>
                        <td>
                          <span className={`badge ${getPriorityBadgeClass(complaint.priority)}`}>
                            {complaint.priority || 'Low'}
                          </span>
                        </td>
                        <td className="department-col">
                          {complaint.department ? (
                            <span className="dept-tag">
                              🏢 {complaint.department}
                              {complaint.assignedTo && (
                                <span className="assignee-text">({complaint.assignedTo})</span>
                              )}
                            </span>
                          ) : (
                            <span className="unassigned-badge">Unassigned</span>
                          )}
                        </td>
                        <td>
                          <span className={`badge ${getStatusBadgeClass(complaint.status)}`}>
                            {complaint.status || 'Submitted'}
                          </span>
                        </td>
                        <td className="date-col">
                          {formatDate(complaint.createdAt || complaint.date)}
                        </td>
                        <td className="text-center action-col">
                          <div className="action-menu-container">
                            <button
                              type="button"
                              className="btn-action-trigger"
                              onClick={(e) => {
                                e.stopPropagation();
                                setOpenDropdownId(
                                  openDropdownId === complaintId ? null : complaintId
                                );
                              }}
                              aria-label="Actions"
                            >
                              ⚙️ Actions ▾
                            </button>

                            {openDropdownId === complaintId && (
                              <div className="action-dropdown-menu">
                                <button
                                  type="button"
                                  className="dropdown-item"
                                  onClick={() => openDetailModal(complaint)}
                                >
                                  👁️ View Details
                                </button>
                                <button
                                  type="button"
                                  className="dropdown-item"
                                  onClick={() => openAssignModal(complaint)}
                                >
                                  🏢 Assign Department
                                </button>
                                <button
                                  type="button"
                                  className="dropdown-item"
                                  onClick={() => openStatusModal(complaint)}
                                >
                                  🔄 Update Status
                                </button>
                                <button
                                  type="button"
                                  className="dropdown-item resolve-item"
                                  onClick={() => openResolveModal(complaint)}
                                >
                                  ✅ Resolve Issue
                                </button>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            <div className="pagination-bar">
              <div className="pagination-info">
                Showing{' '}
                <strong>
                  {Math.min(
                    (currentPage - 1) * pageSize + 1,
                    filteredComplaints.length
                  )}
                </strong>{' '}
                to{' '}
                <strong>
                  {Math.min(currentPage * pageSize, filteredComplaints.length)}
                </strong>{' '}
                of <strong>{filteredComplaints.length}</strong> entries
              </div>

              <div className="pagination-controls">
                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  disabled={currentPage === 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                >
                  ‹ Prev
                </button>

                <div className="page-numbers">
                  {Array.from({ length: totalPages }, (_, i) => i + 1)
                    .filter((p) => {
                      return (
                        p === 1 ||
                        p === totalPages ||
                        Math.abs(p - currentPage) <= 1
                      );
                    })
                    .map((p, idx, arr) => {
                      const showEllipsis = idx > 0 && p - arr[idx - 1] > 1;
                      return (
                        <React.Fragment key={p}>
                          {showEllipsis && <span className="ellipsis">...</span>}
                          <button
                            type="button"
                            className={`page-btn ${currentPage === p ? 'active' : ''}`}
                            onClick={() => setCurrentPage(p)}
                          >
                            {p}
                          </button>
                        </React.Fragment>
                      );
                    })}
                </div>

                <button
                  type="button"
                  className="btn btn-outline btn-sm"
                  disabled={currentPage === totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                >
                  Next ›
                </button>
              </div>
            </div>
          </>
        )}
      </div>

      {/* ================= MODALS ================= */}

      {/* 1. ASSIGN DEPARTMENT MODAL */}
      {activeModal === 'assign' && selectedComplaint && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Assign Department</h3>
              <button className="modal-close-btn" onClick={closeModal}>
                ×
              </button>
            </div>
            <form onSubmit={handleAssignSubmit}>
              <div className="modal-body">
                <p className="modal-instruction">
                  Assign this complaint to a dedicated university department and assign a specific staff member.
                </p>

                {modalError && (
                  <div className="alert alert-error">
                    <span>⚠️</span>
                    <span>{modalError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="dept-select">Responsible Department *</label>
                  <select
                    id="dept-select"
                    value={assignForm.department}
                    onChange={(e) =>
                      setAssignForm({ ...assignForm, department: e.target.value })
                    }
                    required
                  >
                    <option value="">Select Department</option>
                    {DEPARTMENTS.map((d) => (
                      <option key={d} value={d}>
                        {d}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ marginTop: '16px' }}>
                  <label htmlFor="assignee-input">Assignee / Staff Officer (Optional)</label>
                  <input
                    id="assignee-input"
                    type="text"
                    placeholder="e.g. Officer John / Maintenance Team Lead"
                    value={assignForm.assignee}
                    onChange={(e) =>
                      setAssignForm({ ...assignForm, assignee: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={closeModal}
                  disabled={modalLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={modalLoading}
                >
                  {modalLoading ? 'Saving...' : 'Assign Department'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 2. UPDATE STATUS MODAL */}
      {activeModal === 'status' && selectedComplaint && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Update Complaint Status</h3>
              <button className="modal-close-btn" onClick={closeModal}>
                ×
              </button>
            </div>
            <form onSubmit={handleStatusSubmit}>
              <div className="modal-body">
                <p className="modal-instruction">
                  Select a new workflow status and add an administrative note for the student.
                </p>

                {modalError && (
                  <div className="alert alert-error">
                    <span>⚠️</span>
                    <span>{modalError}</span>
                  </div>
                )}

                <div className="form-group">
                  <label htmlFor="status-select">Status *</label>
                  <select
                    id="status-select"
                    value={statusForm.status}
                    onChange={(e) =>
                      setStatusForm({ ...statusForm, status: e.target.value })
                    }
                    required
                  >
                    {STATUSES.map((st) => (
                      <option key={st} value={st}>
                        {st}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group" style={{ marginTop: '16px' }}>
                  <label htmlFor="status-note">Status Note / Progress Log</label>
                  <textarea
                    id="status-note"
                    rows="3"
                    placeholder="Provide additional details regarding this status update..."
                    value={statusForm.note}
                    onChange={(e) =>
                      setStatusForm({ ...statusForm, note: e.target.value })
                    }
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={closeModal}
                  disabled={modalLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={modalLoading}
                >
                  {modalLoading ? 'Updating...' : 'Update Status'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 3. RESOLVE MODAL */}
      {activeModal === 'resolve' && selectedComplaint && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Resolve Complaint</h3>
              <button className="modal-close-btn" onClick={closeModal}>
                ×
              </button>
            </div>
            <form onSubmit={handleResolveSubmit}>
              <div className="modal-body">
                <div className="resolve-info-banner">
                  <span className="banner-icon">ℹ️</span>
                  <span>
                    Marking this ticket as Resolved will notify the student that the issue has been repaired or addressed.
                  </span>
                </div>

                {modalError && (
                  <div className="alert alert-error">
                    <span>⚠️</span>
                    <span>{modalError}</span>
                  </div>
                )}

                <div className="form-group" style={{ marginTop: '16px' }}>
                  <label htmlFor="resolution-note">Resolution Summary / Note *</label>
                  <textarea
                    id="resolution-note"
                    rows="4"
                    placeholder="Explain what steps were taken to resolve this problem (e.g. replaced AC capacitor, restored WiFi access point)..."
                    value={resolveForm.resolutionNote}
                    onChange={(e) =>
                      setResolveForm({ ...resolveForm, resolutionNote: e.target.value })
                    }
                    required
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-ghost"
                  onClick={closeModal}
                  disabled={modalLoading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-accent"
                  disabled={modalLoading}
                >
                  {modalLoading ? 'Resolving...' : 'Confirm Resolution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 4. COMPLAINT DETAIL MODAL */}
      {activeModal === 'detail' && selectedComplaint && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content modal-detail-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Complaint Details</h3>
              <button className="modal-close-btn" onClick={closeModal}>
                ×
              </button>
            </div>

            <div className="modal-body">
              <div className="detail-modal-badges">
                <span className={`badge ${getStatusBadgeClass(selectedComplaint.status)}`}>
                  {selectedComplaint.status || 'Submitted'}
                </span>
                <span className={`badge ${getPriorityBadgeClass(selectedComplaint.priority)}`}>
                  Priority: {selectedComplaint.priority || 'Low'}
                </span>
                <span className="category-tag">📁 {selectedComplaint.category || 'General'}</span>
              </div>

              <h2 className="modal-complaint-title">{selectedComplaint.title}</h2>

              <div className="modal-info-grid">
                <div className="modal-info-cell">
                  <span className="cell-lbl">Ticket ID</span>
                  <span className="cell-val">#{String(selectedComplaint.id || selectedComplaint._id).slice(-8).toUpperCase()}</span>
                </div>
                <div className="modal-info-cell">
                  <span className="cell-lbl">Submitted By</span>
                  <span className="cell-val">
                    {selectedComplaint.studentName || selectedComplaint.student?.name || selectedComplaint.studentEmail || 'Student'}
                  </span>
                </div>
                <div className="modal-info-cell">
                  <span className="cell-lbl">Date Filed</span>
                  <span className="cell-val">{formatDate(selectedComplaint.createdAt || selectedComplaint.date)}</span>
                </div>
                <div className="modal-info-cell">
                  <span className="cell-lbl">Campus Location</span>
                  <span className="cell-val">📍 {selectedComplaint.location || 'N/A'}</span>
                </div>
                <div className="modal-info-cell">
                  <span className="cell-lbl">Assigned Department</span>
                  <span className="cell-val">🏢 {selectedComplaint.department || 'Unassigned'}</span>
                </div>
                <div className="modal-info-cell">
                  <span className="cell-lbl">Assigned Staff</span>
                  <span className="cell-val">{selectedComplaint.assignedTo || selectedComplaint.assignee || 'None'}</span>
                </div>
              </div>

              <div className="modal-desc-box">
                <h4>Description:</h4>
                <p>{selectedComplaint.description}</p>
              </div>

              {selectedComplaint.resolutionNote && (
                <div className="modal-resolution-box">
                  <h4>Resolution Summary:</h4>
                  <p>{selectedComplaint.resolutionNote}</p>
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => {
                  const comp = selectedComplaint;
                  closeModal();
                  openResolveModal(comp);
                }}
              >
                Resolve
              </button>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => {
                  const comp = selectedComplaint;
                  closeModal();
                  openAssignModal(comp);
                }}
              >
                Assign Department
              </button>
              <button type="button" className="btn btn-outline" onClick={closeModal}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
