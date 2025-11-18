/**
 * Main App component with routing and navigation
 */

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import ChatInterface from './components/ChatInterface';
import MemoryBrowser from './components/MemoryBrowser';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import AdminPanel from './components/AdminPanel';
import './App.css';

const App: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [currentUser] = useState({
    user_id: 'demo-user',
    username: 'Demo User',
    role: 'admin',
  });

  return (
    <Router>
      <div className="app">
        {/* Sidebar */}
        <aside className={`sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
          <div className="sidebar-header">
            <h1 className="app-title">
              {sidebarOpen && (
                <>
                  <span className="logo">⚡</span>
                  Codex Prime
                </>
              )}
              {!sidebarOpen && <span className="logo">⚡</span>}
            </h1>
            <button className="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? '◀' : '▶'}
            </button>
          </div>

          <nav className="sidebar-nav">
            <Link to="/chat" className="nav-item">
              <span className="nav-icon">💬</span>
              {sidebarOpen && <span className="nav-label">Chat</span>}
            </Link>

            <Link to="/memory" className="nav-item">
              <span className="nav-icon">🧠</span>
              {sidebarOpen && <span className="nav-label">Memory</span>}
            </Link>

            <Link to="/analytics" className="nav-item">
              <span className="nav-icon">📊</span>
              {sidebarOpen && <span className="nav-label">Analytics</span>}
            </Link>

            <Link to="/admin" className="nav-item">
              <span className="nav-icon">⚙️</span>
              {sidebarOpen && <span className="nav-label">Admin</span>}
            </Link>
          </nav>

          <div className="sidebar-footer">
            <div className="user-info">
              <span className="user-avatar">👤</span>
              {sidebarOpen && (
                <div className="user-details">
                  <div className="user-name">{currentUser.username}</div>
                  <div className="user-role">{currentUser.role}</div>
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Navigate to="/chat" />} />
            <Route
              path="/chat"
              element={<ChatInterface userId={currentUser.user_id} />}
            />
            <Route path="/memory" element={<MemoryBrowser />} />
            <Route path="/analytics" element={<AnalyticsDashboard />} />
            <Route path="/admin" element={<AdminPanel />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;
