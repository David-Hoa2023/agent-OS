/**
 * API client for Codex Prime backend
 */

import axios, { AxiosInstance } from 'axios';

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  user_id?: string;
}

export interface ChatResponse {
  response: string;
  session_id: string;
  metadata?: Record<string, any>;
}

export interface Memory {
  text: string;
  tier: 'ember' | 'rune' | 'glyph';
  timestamp: string;
  tags: string[];
  references?: number;
}

export interface Session {
  session_id: string;
  name: string;
  owner_id: string;
  status: string;
  participants: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface UserPresence {
  user_id: string;
  username: string;
  status: 'online' | 'away' | 'busy' | 'offline';
  last_seen: string;
  current_session?: string;
}

export interface MetricsData {
  counters: Record<string, number>;
  gauges: Record<string, number>;
  histograms: Record<string, any>;
}

export interface AnalyticsData {
  total_events: number;
  events_last_24h: number;
  top_events: Array<[string, number]>;
  active_users: number;
  active_projects: number;
}

class CodexPrimeAPI {
  private client: AxiosInstance;
  private wsUrl: string;

  constructor(baseURL: string = 'http://localhost:8000', wsURL: string = 'ws://localhost:8765') {
    this.client = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.wsUrl = wsURL;
  }

  // Set authentication token
  setAuthToken(token: string) {
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  // Chat API
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await this.client.post('/chat', request);
    return response.data;
  }

  // Streaming chat via WebSocket
  connectStreaming(
    onMessage: (chunk: string) => void,
    onComplete: () => void,
    onError: (error: Error) => void
  ): WebSocket {
    const ws = new WebSocket(this.wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'stream_chunk') {
          onMessage(data.content);
        } else if (data.type === 'stream_complete') {
          onComplete();
        } else if (data.type === 'error') {
          onError(new Error(data.message));
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    ws.onerror = (error) => {
      onError(new Error('WebSocket error'));
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return ws;
  }

  // Memory API
  async getMemories(tier?: string, limit: number = 50): Promise<Memory[]> {
    const params = tier ? { tier, limit } : { limit };
    const response = await this.client.get('/memories', { params });
    return response.data.memories || [];
  }

  async addMemory(text: string, tier: string, tags: string[] = []): Promise<void> {
    await this.client.post('/memories', { text, tier, tags });
  }

  async searchMemories(query: string, k: number = 10): Promise<Memory[]> {
    const response = await this.client.post('/memories/search', { query, k });
    return response.data.results || [];
  }

  // Session API
  async getSessions(): Promise<Session[]> {
    const response = await this.client.get('/sessions');
    return response.data.sessions || [];
  }

  async createSession(name: string, owner_id: string): Promise<Session> {
    const response = await this.client.post('/sessions', { name, owner_id });
    return response.data;
  }

  async joinSession(session_id: string, user_id: string, username: string): Promise<void> {
    await this.client.post(`/sessions/${session_id}/join`, { user_id, username });
  }

  async leaveSession(session_id: string, user_id: string): Promise<void> {
    await this.client.post(`/sessions/${session_id}/leave`, { user_id });
  }

  // Presence API
  async getUserPresence(user_id: string): Promise<UserPresence> {
    const response = await this.client.get(`/presence/${user_id}`);
    return response.data;
  }

  async getOnlineUsers(): Promise<UserPresence[]> {
    const response = await this.client.get('/presence/online');
    return response.data.users || [];
  }

  async updatePresence(user_id: string, status: string): Promise<void> {
    await this.client.post(`/presence/${user_id}`, { status });
  }

  // Metrics & Analytics API
  async getMetrics(): Promise<MetricsData> {
    const response = await this.client.get('/metrics');
    return response.data;
  }

  async getAnalytics(): Promise<AnalyticsData> {
    const response = await this.client.get('/analytics');
    return response.data;
  }

  // Agent API
  async listAgents(): Promise<any[]> {
    const response = await this.client.get('/agents');
    return response.data.agents || [];
  }

  async executeAgent(agent_name: string, task: string): Promise<any> {
    const response = await this.client.post(`/agents/${agent_name}/execute`, { task });
    return response.data;
  }

  // Admin API
  async getUsers(): Promise<any[]> {
    const response = await this.client.get('/admin/users');
    return response.data.users || [];
  }

  async createUser(username: string, email: string, roles: string[]): Promise<any> {
    const response = await this.client.post('/admin/users', { username, email, roles });
    return response.data;
  }

  async updateUserRoles(user_id: string, roles: string[]): Promise<void> {
    await this.client.put(`/admin/users/${user_id}/roles`, { roles });
  }

  async getAuditLogs(limit: number = 100, user_id?: string): Promise<any[]> {
    const params = user_id ? { limit, user_id } : { limit };
    const response = await this.client.get('/admin/audit', { params });
    return response.data.events || [];
  }
}

export const apiClient = new CodexPrimeAPI();
export default apiClient;
