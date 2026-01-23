import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Voice API
export const voiceApi = {
  createSession: async (data: { text?: string; audio_base64?: string }) => {
    const response = await apiClient.post('/api/v1/voice/session', data);
    return response.data;
  },

  confirmAction: async (actionId: string, confirmed: boolean) => {
    const response = await apiClient.post('/api/v1/voice/confirm-action', {
      action_id: actionId,
      confirmed,
    });
    return response.data;
  },
};

// Memory API
export const memoryApi = {
  getPreferences: async (category?: string) => {
    const params = category ? { category } : {};
    const response = await apiClient.get('/api/v1/memory/preferences', { params });
    return response.data;
  },

  updatePreference: async (entry: {
    category: string;
    key: string;
    value: Record<string, any>;
  }) => {
    const response = await apiClient.put('/api/v1/memory/preferences', entry);
    return response.data;
  },

  getBehaviors: async (behaviorType?: string) => {
    const params = behaviorType ? { behavior_type: behaviorType } : {};
    const response = await apiClient.get('/api/v1/memory/behaviors', { params });
    return response.data;
  },

  deleteBehavior: async (behaviorId: number) => {
    const response = await apiClient.delete(`/api/v1/memory/behaviors/${behaviorId}`);
    return response.data;
  },

  exportMemory: async () => {
    const response = await apiClient.get('/api/v1/memory/export');
    return response.data;
  },

  clearAll: async () => {
    const response = await apiClient.delete('/api/v1/memory/clear-all');
    return response.data;
  },
};

// Settings API
export const settingsApi = {
  getSettings: async () => {
    const response = await apiClient.get('/api/v1/settings');
    return response.data;
  },

  updateSettings: async (settings: Record<string, any>) => {
    const response = await apiClient.put('/api/v1/settings', settings);
    return response.data;
  },
};

// Health API
export const healthApi = {
  checkHealth: async () => {
    const response = await apiClient.get('/api/v1/health');
    return response.data;
  },
};

export default apiClient;
