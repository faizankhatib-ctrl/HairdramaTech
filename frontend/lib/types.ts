/**
 * Application Type Definitions
 * Strictly aligned with the Flask backend API schema and database contracts.
 */

export type TaskStatus = 'TODO' | 'IN_PROGRESS' | 'COMPLETED';

export type TaskPriority = 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';

export type TaskScope = 'all' | 'assigned_to_me' | 'created_by_me';

export interface User {
  id: string;
  name: string;
  email: string;
  profile_image: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  created_by: string;
  assigned_to: string | null;
  creator?: User;
  assignee?: User | null;
}

export interface TaskFilterParams {
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
  scope?: TaskScope;
}

export interface CreateTaskInput {
  title: string;
  description?: string | null;
  priority: TaskPriority;
  status?: TaskStatus;
  due_date?: string | null;
  assigned_to?: string | null;
}

export interface UpdateTaskInput {
  title?: string;
  description?: string | null;
  priority?: TaskPriority;
  status?: TaskStatus;
  due_date?: string | null;
  assigned_to?: string | null;
}

export interface DashboardStats {
  total_tasks: number;
  todo: number;
  in_progress: number;
  completed: number;
  assigned_to_me: number;
  created_by_me: number;
}

export interface APIResponse<T> {
  success: boolean;
  data: T;
  message?: string;
}

export interface APIErrorDetail {
  code: string;
  message: string;
}

export interface APIErrorResponse {
  success: false;
  error: APIErrorDetail;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}
