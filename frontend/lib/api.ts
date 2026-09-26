/**
 * Centralized API Client
 * Interacts with the Flask REST API backend, manages Bearer tokens,
 * and normalizes error messages for the UI.
 */

import {
  APIErrorDetail,
  User,
  Task,
  CreateTaskInput,
  UpdateTaskInput,
  TaskFilterParams,
  DashboardStats,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

export class APIError extends Error {
  code: string;
  statusCode: number;

  constructor(message: string, code: string = 'UNKNOWN_ERROR', statusCode: number = 500) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.statusCode = statusCode;
  }
}

// Token storage key in localStorage
const TOKEN_KEY = 'hairdrama_auth_token';

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeStoredToken(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(TOKEN_KEY);
}

// Global listener for 401 unauthorized to trigger logout
type UnauthorizedCallback = () => void;
let unauthorizedHandler: UnauthorizedCallback | null = null;

export function setUnauthorizedHandler(handler: UnauthorizedCallback): void {
  unauthorizedHandler = handler;
}

/**
 * Low-level HTTP fetch wrapper
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = new Headers(options.headers || {});

  headers.set('Accept', 'application/json');
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const token = getStoredToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch {
    throw new APIError(
      'Unable to connect to server. Please verify the backend is running.',
      'NETWORK_ERROR',
      0
    );
  }

  // Handle 401 Unauthorized globally
  if (response.status === 401) {
    removeStoredToken();
    if (unauthorizedHandler) {
      unauthorizedHandler();
    }
  }

  interface ErrorEnvelope {
    error?: APIErrorDetail;
    message?: string;
    data?: unknown;
  }

  let data: ErrorEnvelope | null = null;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    try {
      data = (await response.json()) as ErrorEnvelope;
    } catch {
      data = null;
    }
  }

  if (!response.ok) {
    const errorDetail: APIErrorDetail = data?.error || {
      code: response.status === 403 ? 'FORBIDDEN' : response.status === 404 ? 'NOT_FOUND' : 'ERROR',
      message: data?.message || data?.error?.message || `Request failed with status ${response.status}`,
    };

    throw new APIError(errorDetail.message, errorDetail.code, response.status);
  }

  return data?.data as T;
}

// =============================================================================
// API Service Methods
// =============================================================================

export const api = {
  // Authentication
  async googleLogin(credential: string): Promise<{ token: string; user: User }> {
    return request<{ token: string; user: User }>('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify({ credential }),
    });
  },

  async getCurrentUser(): Promise<User> {
    const res = await request<{ user: User }>('/api/auth/me', {
      method: 'GET',
    });
    return res.user;
  },

  async logout(): Promise<void> {
    try {
      await request<null>('/api/auth/logout', {
        method: 'POST',
      });
    } finally {
      removeStoredToken();
    }
  },

  // Users
  async getUsers(search?: string): Promise<User[]> {
    const query = search ? `?search=${encodeURIComponent(search)}` : '';
    const res = await request<{ users: User[]; total: number }>(`/api/users${query}`, {
      method: 'GET',
    });
    return res.users || [];
  },

  // Dashboard Stats
  async getDashboardStats(): Promise<DashboardStats> {
    return request<DashboardStats>('/api/dashboard/stats', {
      method: 'GET',
    });
  },

  // Tasks
  async getTasks(filters?: TaskFilterParams): Promise<{ tasks: Task[]; total: number }> {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.priority) params.set('priority', filters.priority);
    if (filters?.search) params.set('search', filters.search);
    if (filters?.scope && filters.scope !== 'all') params.set('scope', filters.scope);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    return request<{ tasks: Task[]; total: number }>(`/api/tasks${queryString}`, {
      method: 'GET',
    });
  },

  async getTask(id: string): Promise<Task> {
    const res = await request<{ task: Task }>(`/api/tasks/${id}`, {
      method: 'GET',
    });
    return res.task;
  },

  async createTask(input: CreateTaskInput): Promise<Task> {
    const res = await request<{ task: Task }>('/api/tasks', {
      method: 'POST',
      body: JSON.stringify(input),
    });
    return res.task;
  },

  async updateTask(id: string, input: UpdateTaskInput): Promise<Task> {
    const res = await request<{ task: Task }>(`/api/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(input),
    });
    return res.task;
  },

  async assignTask(id: string, assigneeId: string | null): Promise<Task> {
    const res = await request<{ task: Task }>(`/api/tasks/${id}/assign`, {
      method: 'PATCH',
      body: JSON.stringify({ assigned_to: assigneeId }),
    });
    return res.task;
  },

  async completeTask(id: string): Promise<Task> {
    const res = await request<{ task: Task }>(`/api/tasks/${id}/complete`, {
      method: 'PATCH',
    });
    return res.task;
  },

  async deleteTask(id: string): Promise<void> {
    await request<null>(`/api/tasks/${id}`, {
      method: 'DELETE',
    });
  },
};
