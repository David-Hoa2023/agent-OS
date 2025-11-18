/**
 * Analytics dashboard for metrics and insights
 */

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import apiClient, { MetricsData, AnalyticsData } from '../api/client';
import './AnalyticsDashboard.css';

const AnalyticsDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
    // Refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [metricsData, analyticsData] = await Promise.all([
        apiClient.getMetrics(),
        apiClient.getAnalytics(),
      ]);

      setMetrics(metricsData);
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Error loading analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="analytics-loading">Loading analytics...</div>;
  }

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

  // Prepare chart data
  const topEventsData =
    analytics?.top_events.map(([event, count]) => ({
      name: event,
      count,
    })) || [];

  const counterData = metrics
    ? Object.entries(metrics.counters).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  const gaugeData = metrics
    ? Object.entries(metrics.gauges).map(([name, value]) => ({
        name,
        value,
      }))
    : [];

  return (
    <div className="analytics-dashboard">
      <div className="analytics-header">
        <h2>Analytics Dashboard</h2>
        <button className="refresh-button" onClick={loadData}>
          ↻ Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-value">{analytics?.total_events.toLocaleString() || 0}</div>
            <div className="card-label">Total Events</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🔥</div>
          <div className="card-content">
            <div className="card-value">{analytics?.events_last_24h.toLocaleString() || 0}</div>
            <div className="card-label">Last 24 Hours</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">👥</div>
          <div className="card-content">
            <div className="card-value">{analytics?.active_users || 0}</div>
            <div className="card-label">Active Users</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📁</div>
          <div className="card-content">
            <div className="card-value">{analytics?.active_projects || 0}</div>
            <div className="card-label">Active Projects</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Top Events Bar Chart */}
        <div className="chart-container">
          <h3>Top Events</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={topEventsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Counters Pie Chart */}
        <div className="chart-container">
          <h3>Counters Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={counterData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => entry.name}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {counterData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Gauges Bar Chart */}
        <div className="chart-container">
          <h3>Current Gauges</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={gaugeData} layout="horizontal">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={150} />
              <Tooltip />
              <Bar dataKey="value" fill="#82ca9d" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Performance Metrics */}
        <div className="chart-container">
          <h3>Performance Metrics</h3>
          <div className="metrics-list">
            {metrics?.histograms &&
              Object.entries(metrics.histograms).map(([name, stats]) => (
                <div key={name} className="metric-item">
                  <div className="metric-name">{name}</div>
                  <div className="metric-stats">
                    {typeof stats === 'object' && stats !== null ? (
                      <>
                        <span>Min: {stats.min?.toFixed(2) || 'N/A'}</span>
                        <span>Avg: {stats.mean?.toFixed(2) || 'N/A'}</span>
                        <span>Max: {stats.max?.toFixed(2) || 'N/A'}</span>
                        <span>P95: {stats.p95?.toFixed(2) || 'N/A'}</span>
                      </>
                    ) : (
                      <span>Count: {stats}</span>
                    )}
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
