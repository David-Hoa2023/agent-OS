/**
 * Admin panel for user management and system administration
 */

import React, { useState, useEffect } from 'react';
import apiClient from '../api/client';
import './AdminPanel.css';

interface User {
  user_id: string;
  username: string;
  email: string;
  roles: string[];
  created_at: string;
  is_active: boolean;
}

interface AuditLog {
  event_id: string;
  event_type: string;
  timestamp: string;
  user_id: string;
  action: string;
  result: string;
  severity: string;
}

const AdminPanel: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [activeTab, setActiveTab] = useState<'users' | 'audit'>('users');
  const [loading, setLoading] = useState(false);

  const [newUser, setNewUser] = useState({
    username: '',
    email: '',
    roles: ['viewer'],
  });

  const [editingUser, setEditingUser] = useState<User | null>(null);

  useEffect(() => {
    if (activeTab === 'users') {
      loadUsers();
    } else {
      loadAuditLogs();
    }
  }, [activeTab]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getUsers();
      setUsers(data);
    } catch (error) {
      console.error('Error loading users:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadAuditLogs = async () => {
    setLoading(true);
    try {
      const data = await apiClient.getAuditLogs(100);
      setAuditLogs(data);
    } catch (error) {
      console.error('Error loading audit logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUser.username || !newUser.email) {
      alert('Please fill in all fields');
      return;
    }

    try {
      await apiClient.createUser(newUser.username, newUser.email, newUser.roles);
      setNewUser({ username: '', email: '', roles: ['viewer'] });
      loadUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      alert('Failed to create user');
    }
  };

  const handleUpdateRoles = async (user_id: string, roles: string[]) => {
    try {
      await apiClient.updateUserRoles(user_id, roles);
      setEditingUser(null);
      loadUsers();
    } catch (error) {
      console.error('Error updating roles:', error);
      alert('Failed to update roles');
    }
  };

  const toggleRole = (role: string) => {
    const current = newUser.roles;
    if (current.includes(role)) {
      setNewUser({ ...newUser, roles: current.filter((r) => r !== role) });
    } else {
      setNewUser({ ...newUser, roles: [...current, role] });
    }
  };

  const getRoleBadgeClass = (role: string) => {
    switch (role) {
      case 'admin':
        return 'role-badge-admin';
      case 'developer':
        return 'role-badge-developer';
      case 'operator':
        return 'role-badge-operator';
      default:
        return 'role-badge-viewer';
    }
  };

  const getSeverityClass = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return 'severity-critical';
      case 'error':
        return 'severity-error';
      case 'warning':
        return 'severity-warning';
      default:
        return 'severity-info';
    }
  };

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h2>Admin Panel</h2>
      </div>

      {/* Tabs */}
      <div className="admin-tabs">
        <button
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          👥 User Management
        </button>
        <button
          className={`tab ${activeTab === 'audit' ? 'active' : ''}`}
          onClick={() => setActiveTab('audit')}
        >
          📋 Audit Logs
        </button>
      </div>

      {/* User Management */}
      {activeTab === 'users' && (
        <div className="users-section">
          {/* Create User */}
          <div className="create-user-form">
            <h3>Create New User</h3>
            <div className="form-row">
              <input
                type="text"
                className="form-input"
                placeholder="Username"
                value={newUser.username}
                onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
              />
              <input
                type="email"
                className="form-input"
                placeholder="Email"
                value={newUser.email}
                onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
              />
            </div>

            <div className="roles-selector">
              <label>Roles:</label>
              {['admin', 'developer', 'operator', 'viewer'].map((role) => (
                <label key={role} className="role-checkbox">
                  <input
                    type="checkbox"
                    checked={newUser.roles.includes(role)}
                    onChange={() => toggleRole(role)}
                  />
                  <span className={`role-label ${getRoleBadgeClass(role)}`}>{role}</span>
                </label>
              ))}
            </div>

            <button className="create-button" onClick={handleCreateUser}>
              Create User
            </button>
          </div>

          {/* Users List */}
          <div className="users-list">
            {loading && <div className="loading">Loading users...</div>}

            {!loading && users.length === 0 && (
              <div className="empty-state">No users found</div>
            )}

            {!loading &&
              users.map((user) => (
                <div key={user.user_id} className="user-card">
                  <div className="user-info">
                    <div className="user-name">{user.username}</div>
                    <div className="user-email">{user.email}</div>
                    <div className="user-meta">
                      <span>ID: {user.user_id}</span>
                      <span>•</span>
                      <span>Created: {new Date(user.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="user-roles">
                    {user.roles.map((role) => (
                      <span key={role} className={`role-badge ${getRoleBadgeClass(role)}`}>
                        {role}
                      </span>
                    ))}
                  </div>

                  <button
                    className="edit-button"
                    onClick={() => setEditingUser(user)}
                  >
                    Edit Roles
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Audit Logs */}
      {activeTab === 'audit' && (
        <div className="audit-section">
          <div className="audit-header">
            <h3>Audit Logs</h3>
            <button className="refresh-button" onClick={loadAuditLogs}>
              ↻ Refresh
            </button>
          </div>

          <div className="audit-logs">
            {loading && <div className="loading">Loading audit logs...</div>}

            {!loading && auditLogs.length === 0 && (
              <div className="empty-state">No audit logs found</div>
            )}

            {!loading &&
              auditLogs.map((log) => (
                <div key={log.event_id} className="audit-log-item">
                  <div className={`severity-indicator ${getSeverityClass(log.severity)}`} />
                  <div className="log-content">
                    <div className="log-header">
                      <span className="log-type">{log.event_type}</span>
                      <span className={`log-result result-${log.result}`}>{log.result}</span>
                    </div>
                    <div className="log-details">
                      <span className="log-user">User: {log.user_id || 'system'}</span>
                      <span>•</span>
                      <span className="log-action">{log.action || 'N/A'}</span>
                      <span>•</span>
                      <span className="log-time">
                        {new Date(log.timestamp).toLocaleString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Edit User Modal */}
      {editingUser && (
        <div className="modal-overlay" onClick={() => setEditingUser(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3>Edit Roles for {editingUser.username}</h3>
            <div className="roles-selector">
              {['admin', 'developer', 'operator', 'viewer'].map((role) => (
                <label key={role} className="role-checkbox">
                  <input
                    type="checkbox"
                    checked={editingUser.roles.includes(role)}
                    onChange={() => {
                      const newRoles = editingUser.roles.includes(role)
                        ? editingUser.roles.filter((r) => r !== role)
                        : [...editingUser.roles, role];
                      setEditingUser({ ...editingUser, roles: newRoles });
                    }}
                  />
                  <span className={`role-label ${getRoleBadgeClass(role)}`}>{role}</span>
                </label>
              ))}
            </div>

            <div className="modal-actions">
              <button
                className="save-button"
                onClick={() => handleUpdateRoles(editingUser.user_id, editingUser.roles)}
              >
                Save Changes
              </button>
              <button className="cancel-button" onClick={() => setEditingUser(null)}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
