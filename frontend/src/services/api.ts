import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';
import type {
  Token,
  User,
  UserCreate,
  UserUpdate,
  ProfileUpdate,
  PasswordChange,
  RegistrationStatus,
  Project,
  ProjectListResponse,
  MarketData,
  EngineeringData,
  FinanceData,
  Attachment,
  MarketSummary,
  EngineeringSummary,
  FinanceSummary,
  ProjectReport,
  ProjectStatus,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && originalRequest && !originalRequest.headers._retry) {
      originalRequest.headers._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post<Token>('/api/auth/refresh', null, {
            headers: { Authorization: `Bearer ${refreshToken}` },
          });
          localStorage.setItem('access_token', response.data.access_token);
          localStorage.setItem('refresh_token', response.data.refresh_token);
          originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
          return api(originalRequest);
        }
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// Auth
export const authApi = {
  login: async (username: string, password: string): Promise<Token> => {
    const response = await api.post<Token>('/auth/login', { username, password });
    return response.data;
  },
  register: async (username: string, password: string, department: string): Promise<User> => {
    const response = await api.post<User>('/auth/register', { username, password, department });
    return response.data;
  },
  me: async (): Promise<User> => {
    const response = await api.get<User>('/auth/me');
    return response.data;
  },
  registrationStatus: async (): Promise<RegistrationStatus> => {
    const response = await api.get<RegistrationStatus>('/auth/registration-status');
    return response.data;
  },
  updateProfile: async (data: ProfileUpdate): Promise<User> => {
    const response = await api.put<User>('/auth/profile', data);
    return response.data;
  },
  changePassword: async (data: PasswordChange): Promise<void> => {
    await api.put('/auth/change-password', data);
  },
};

// Users (Admin only)
export const usersApi = {
  list: async (): Promise<User[]> => {
    const response = await api.get<User[]>('/users/');
    return response.data;
  },
  get: async (id: string): Promise<User> => {
    const response = await api.get<User>(`/users/${id}`);
    return response.data;
  },
  create: async (data: UserCreate): Promise<User> => {
    const response = await api.post<User>('/users/', data);
    return response.data;
  },
  update: async (id: string, data: UserUpdate): Promise<User> => {
    const response = await api.put<User>(`/users/${id}`, data);
    return response.data;
  },
  resetPassword: async (id: string, newPassword: string): Promise<void> => {
    await api.put(`/users/${id}/reset-password`, { new_password: newPassword });
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/users/${id}`);
  },
};

// Projects
export const projectsApi = {
  list: async (page = 1, pageSize = 20, search?: string): Promise<ProjectListResponse> => {
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    if (search) params.append('search', search);
    const response = await api.get<ProjectListResponse>(`/projects/?${params}`);
    return response.data;
  },
  get: async (id: string): Promise<Project> => {
    const response = await api.get<Project>(`/projects/${id}`);
    return response.data;
  },
  create: async (data: Partial<Project>): Promise<Project> => {
    const response = await api.post<Project>('/projects/', data);
    return response.data;
  },
  update: async (id: string, data: Partial<Project>): Promise<Project> => {
    const response = await api.put<Project>(`/projects/${id}`, data);
    return response.data;
  },
  delete: async (id: string): Promise<void> => {
    await api.delete(`/projects/${id}`);
  },
};

// Market Data
export const marketApi = {
  list: async (projectId: string): Promise<MarketData[]> => {
    const response = await api.get<MarketData[]>(`/market/${projectId}/data`);
    return response.data;
  },
  create: async (projectId: string, data: Partial<MarketData>): Promise<MarketData> => {
    const response = await api.post<MarketData>(`/market/${projectId}/data`, data);
    return response.data;
  },
  update: async (projectId: string, dataId: string, data: Partial<MarketData>): Promise<MarketData> => {
    const response = await api.put<MarketData>(`/market/${projectId}/data/${dataId}`, data);
    return response.data;
  },
  delete: async (projectId: string, dataId: string): Promise<void> => {
    await api.delete(`/market/${projectId}/data/${dataId}`);
  },
};

// Engineering Data
export const engineeringApi = {
  list: async (projectId: string): Promise<EngineeringData[]> => {
    const response = await api.get<EngineeringData[]>(`/engineering/${projectId}/data`);
    return response.data;
  },
  create: async (projectId: string, data: Partial<EngineeringData>): Promise<EngineeringData> => {
    const response = await api.post<EngineeringData>(`/engineering/${projectId}/data`, data);
    return response.data;
  },
  update: async (projectId: string, dataId: string, data: Partial<EngineeringData>): Promise<EngineeringData> => {
    const response = await api.put<EngineeringData>(`/engineering/${projectId}/data/${dataId}`, data);
    return response.data;
  },
  delete: async (projectId: string, dataId: string): Promise<void> => {
    await api.delete(`/engineering/${projectId}/data/${dataId}`);
  },
  updateStatus: async (projectId: string, status: ProjectStatus): Promise<Project> => {
    const response = await api.put<Project>(`/engineering/${projectId}/status`, JSON.stringify(status));
    return response.data;
  },
};

// Finance Data
export const financeApi = {
  list: async (projectId: string): Promise<FinanceData[]> => {
    const response = await api.get<FinanceData[]>(`/finance/${projectId}/data`);
    return response.data;
  },
  create: async (projectId: string, data: Partial<FinanceData>): Promise<FinanceData> => {
    const response = await api.post<FinanceData>(`/finance/${projectId}/data`, data);
    return response.data;
  },
  update: async (projectId: string, dataId: string, data: Partial<FinanceData>): Promise<FinanceData> => {
    const response = await api.put<FinanceData>(`/finance/${projectId}/data/${dataId}`, data);
    return response.data;
  },
  delete: async (projectId: string, dataId: string): Promise<void> => {
    await api.delete(`/finance/${projectId}/data/${dataId}`);
  },
};

// Attachments
export const attachmentsApi = {
  list: async (projectId: string): Promise<Attachment[]> => {
    const response = await api.get<Attachment[]>(`/attachments/${projectId}`);
    return response.data;
  },
  upload: async (projectId: string, file: File, fileType?: string): Promise<Attachment> => {
    const formData = new FormData();
    formData.append('file', file);
    if (fileType) formData.append('file_type', fileType);
    const response = await api.post<Attachment>(`/attachments/${projectId}/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  download: async (attachmentId: string): Promise<Blob> => {
    const response = await api.get(`/attachments/${attachmentId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
  delete: async (attachmentId: string): Promise<void> => {
    await api.delete(`/attachments/${attachmentId}`);
  },
};

// Statistics
export const statisticsApi = {
  marketSummary: async (projectId?: string): Promise<MarketSummary> => {
    const params = projectId ? `?project_id=${projectId}` : '';
    const response = await api.get<MarketSummary>(`/statistics/market/summary${params}`);
    return response.data;
  },
  engineeringSummary: async (projectId?: string): Promise<EngineeringSummary> => {
    const params = projectId ? `?project_id=${projectId}` : '';
    const response = await api.get<EngineeringSummary>(`/statistics/engineering/summary${params}`);
    return response.data;
  },
  financeSummary: async (projectId?: string): Promise<FinanceSummary> => {
    const params = projectId ? `?project_id=${projectId}` : '';
    const response = await api.get<FinanceSummary>(`/statistics/finance/summary${params}`);
    return response.data;
  },
  projectReport: async (projectId: string): Promise<ProjectReport> => {
    const response = await api.get<ProjectReport>(`/statistics/project/${projectId}/report`);
    return response.data;
  },
};

export default api;
