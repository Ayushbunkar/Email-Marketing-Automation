import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { toast } from 'sonner';

// Create axios instance with base configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  }
);

// Response interceptor for handling errors and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 unauthorized and token refresh
    if (error.response?.status === 401 && !originalRequest._retry && originalRequest.url !== '/auth/refresh') {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const refreshResponse = await axios.post(
            '/api/auth/refresh',
            { refresh_token: refreshToken }
          );

          const { access_token, refresh_token: newRefreshToken } = refreshResponse.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken || refreshToken);

          // Update the original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        }
      } catch (_refreshError) {
        // Refresh token failed, logout user
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(_refreshError);
      }
    }

    // Handle other errors
    if (error.response) {
      const { status } = error.response;

      switch (status) {
        case 400:
          toast.error('Bad Request: Please check your input');
          break;
        case 403:
          toast.error('Forbidden: You do not have permission');
          break;
        case 404:
          toast.error('Not Found: Resource not found');
          break;
        case 500:
          toast.error('Internal Server Error: Please try again later');
          break;
        default:
          toast.error(`Error: ${status}`);
      }
    } else if (error.request) {
      toast.error('Network Error: Unable to connect to server');
    } else {
      toast.error('Request Error: Something went wrong');
    }

    return Promise.reject(error);
  }
);

// API service methods
export const apiService = {
  // Auth endpoints
  login: (credentials: { email: string; password: string }) => {
    const params = new URLSearchParams();
    params.append('username', credentials.email);
    params.append('password', credentials.password);
    return apiClient.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  register: (credentials: { email: string; password: string; full_name?: string }) =>
    apiClient.post('/auth/register', { 
      email: credentials.email, 
      password: credentials.password, 
      name: credentials.full_name || credentials.email.split('@')[0] 
    }),
  logout: () => apiClient.post('/auth/logout'),
  refreshToken: (refreshToken: string) =>
    apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
  getMe: () => apiClient.get('/auth/me'),

  // Campaign endpoints
  getCampaigns: (params?: { page?: number; limit?: number; status?: string }) =>
    apiClient.get('/campaigns/', { params }),
  createCampaign: (campaignData: unknown) =>
    apiClient.post('/campaigns/', campaignData),
  getCampaign: (id: string) => apiClient.get(`/campaigns/${id}`),
  updateCampaign: (id: string, campaignData: unknown) =>
    apiClient.put(`/campaigns/${id}`, campaignData),
  deleteCampaign: (id: string) => apiClient.delete(`/campaigns/${id}`),
  getCampaignAnalytics: (id: string) => apiClient.get(`/campaigns/${id}/analytics`),

  // Contact endpoints
  getContacts: (params?: { page?: number; limit?: number; search?: string; status?: string }) =>
    apiClient.get('/contacts/', { params }),
  createContact: (contactData: unknown) =>
    apiClient.post('/contacts/', contactData),
  updateContact: (id: string, contactData: unknown) =>
    apiClient.put(`/contacts/${id}`, contactData),
  deleteContact: (id: string) => apiClient.delete(`/contacts/${id}`),
  importContacts: (formData: FormData) =>
    apiClient.post('/contacts/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  exportContacts: () => apiClient.get('/contacts/export', { responseType: 'blob' }),

  // Template endpoints
  getTemplates: (params?: { page?: number; limit?: number }) =>
    apiClient.get('/templates/', { params }),
  createTemplate: (templateData: unknown) =>
    apiClient.post('/templates/', templateData),
  updateTemplate: (id: string, templateData: unknown) =>
    apiClient.put(`/templates/${id}`, templateData),
  deleteTemplate: (id: string) => apiClient.delete(`/templates/${id}`),

  // Inbox endpoints
  getInbox: (params?: { page?: number; limit?: number; status?: string }) =>
    apiClient.get('/inbox/', { params }),
  getInboxItem: (id: string) => apiClient.get(`/inbox/${id}`),
  updateInboxItem: (id: string, data: unknown) =>
    apiClient.put(`/inbox/${id}`, data),

  // Replies endpoints
  getReplies: (params?: { page?: number; limit?: number; status?: string }) =>
    apiClient.get('/replies/', { params }),
  getReply: (id: string) => apiClient.get(`/replies/${id}`),
  updateReply: (id: string, data: unknown) =>
    apiClient.put(`/replies/${id}`, data),
  approveReply: (id: string) => apiClient.post(`/replies/${id}/approve`),
  rejectReply: (id: string) => apiClient.post(`/replies/${id}/reject`),

  // Analytics endpoints
  getDashboardStats: () => apiClient.get('/analytics/summary'),
  getCampaignPerformance: (params?: { days?: number }) =>
    apiClient.get('/analytics/campaign-performance', { params }),
  getDeliveryStats: (params?: { days?: number }) =>
    apiClient.get('/analytics/delivery', { params }),
  getEngagementStats: (params?: { days?: number }) =>
    apiClient.get('/analytics/engagement', { params }),

  // Settings endpoints
  getSettings: () => apiClient.get('/settings'),
  updateSettings: (settingsData: unknown) =>
    apiClient.put('/settings', settingsData),
  getSystemStatus: () => apiClient.get('/settings/status'),
};

export default apiService;