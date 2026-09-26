'use client';

import React, { useState, useEffect, useCallback, use } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { EditTaskModal } from '@/components/tasks/EditTaskModal';
import { api, APIError } from '@/lib/api';
import { Task, User } from '@/lib/types';
import { useToast } from '@/components/ui/Toast';
import {
  ArrowLeft,
  Calendar,
  Clock,
  User as UserIcon,
  CheckCircle2,
  Circle,
  Edit2,
  Trash2,
  AlertCircle,
} from 'lucide-react';

interface TaskDetailsPageProps {
  params: Promise<{ id: string }>;
}

export default function TaskDetailsPage({ params }: TaskDetailsPageProps) {
  const resolvedParams = use(params);
  const taskId = resolvedParams.id;

  const router = useRouter();
  const toast = useToast();

  const [task, setTask] = useState<Task | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isActionBusy, setIsActionBusy] = useState(false);

  const handleReload = useCallback(async () => {
    setIsLoading(true);
    try {
      const taskData = await api.getTask(taskId);
      setTask(taskData);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to reload task';
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  }, [taskId, toast]);

  useEffect(() => {
    let ignore = false;
    async function load() {
      try {
        const [taskData, usersData] = await Promise.all([
          api.getTask(taskId),
          api.getUsers().catch(() => []),
        ]);
        if (!ignore) {
          setTask(taskData);
          setUsers(usersData);
        }
      } catch (err: unknown) {
        if (!ignore) {
          if (err instanceof APIError && err.statusCode === 403) {
            setError('You are not authorized to view this task.');
          } else if (err instanceof APIError && err.statusCode === 404) {
            setError('The requested task does not exist or has been deleted.');
          } else {
            const msg = err instanceof Error ? err.message : 'Failed to load task details';
            setError(msg);
          }
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    load();
    return () => {
      ignore = true;
    };
  }, [taskId]);

  const handleToggleComplete = async () => {
    if (!task) return;
    setIsActionBusy(true);
    try {
      const updated = await api.completeTask(task.id);
      setTask(updated);
      toast.success(
        updated.status === 'COMPLETED'
          ? 'Task marked as completed! Notification sent.'
          : 'Task reopened.'
      );
    } catch (err: unknown) {
      if (err instanceof APIError && err.statusCode === 403) {
        toast.error('You are not authorized to complete this task.');
      } else {
        const msg = err instanceof Error ? err.message : 'Action failed';
        toast.error(msg);
      }
    } finally {
      setIsActionBusy(false);
    }
  };

  const handleAssigneeChange = async (newAssigneeId: string) => {
    if (!task) return;
    setIsActionBusy(true);
    try {
      const updated = await api.assignTask(task.id, newAssigneeId || null);
      setTask(updated);
      toast.success('Task assignee updated successfully.');
    } catch (err: unknown) {
      if (err instanceof APIError && err.statusCode === 403) {
        toast.error('You are not authorized to reassign this task.');
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to reassign task';
        toast.error(msg);
      }
    } finally {
      setIsActionBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!task) return;
    if (!window.confirm(`Are you sure you want to delete "${task.title}"?`)) return;

    setIsActionBusy(true);
    try {
      await api.deleteTask(task.id);
      toast.success('Task deleted successfully.');
      router.push('/tasks');
    } catch (err: unknown) {
      if (err instanceof APIError && err.statusCode === 403) {
        toast.error('You are not authorized to delete this task. Only the creator can delete it.');
      } else {
        const msg = err instanceof Error ? err.message : 'Deletion failed';
        toast.error(msg);
      }
      setIsActionBusy(false);
    }
  };

  if (isLoading) {
    return (
      <AppShell>
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
          <div className="skeleton" style={{ width: '120px', height: '24px', marginBottom: '24px' }} />
          <div className="card">
            <div className="skeleton" style={{ width: '60%', height: '32px', marginBottom: '16px' }} />
            <div className="skeleton" style={{ width: '100%', height: '80px', marginBottom: '24px' }} />
            <div className="skeleton" style={{ width: '40%', height: '24px' }} />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error || !task) {
    return (
      <AppShell>
        <div style={{ maxWidth: '600px', margin: '60px auto', textAlign: 'center' }}>
          <div
            style={{
              width: '64px',
              height: '64px',
              borderRadius: '50%',
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ef4444',
              margin: '0 auto 20px',
            }}
          >
            <AlertCircle size={32} />
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '8px' }}>
            {error || 'Task Not Found'}
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '14px' }}>
            Please return to your task dashboard or verify your permissions.
          </p>
          <Link href="/tasks" className="btn btn-secondary">
            <ArrowLeft size={16} />
            <span>Back to Tasks</span>
          </Link>
        </div>
      </AppShell>
    );
  }

  const isCompleted = task.status === 'COMPLETED';

  return (
    <AppShell onTaskCreated={handleReload}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        {/* Navigation Breadcrumb */}
        <div style={{ marginBottom: '24px' }}>
          <Link
            href="/tasks"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '13px',
              color: 'var(--text-muted)',
              fontWeight: 600,
            }}
          >
            <ArrowLeft size={16} />
            <span>Back to All Tasks</span>
          </Link>
        </div>

        {/* Task Details Card */}
        <div className="card" style={{ padding: '32px' }}>
          {/* Header Row */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '20px', marginBottom: '24px' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                <StatusBadge status={task.status} />
                <PriorityBadge priority={task.priority} />
              </div>
              <h1
                style={{
                  fontSize: '26px',
                  fontWeight: 800,
                  color: isCompleted ? 'var(--text-muted)' : 'var(--text-primary)',
                  textDecoration: isCompleted ? 'line-through' : 'none',
                  lineHeight: 1.3,
                }}
              >
                {task.title}
              </h1>
            </div>

            {/* Quick Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
              <button
                onClick={handleToggleComplete}
                className={`btn ${isCompleted ? 'btn-secondary' : 'btn-primary'} btn-sm`}
                disabled={isActionBusy}
                title={isCompleted ? 'Reopen task' : 'Mark completed'}
              >
                {isCompleted ? <Circle size={15} /> : <CheckCircle2 size={15} />}
                <span>{isCompleted ? 'Reopen' : 'Complete'}</span>
              </button>

              <button
                onClick={() => setIsEditModalOpen(true)}
                className="btn btn-secondary btn-sm"
                disabled={isActionBusy}
                title="Edit task"
              >
                <Edit2 size={15} />
                <span>Edit</span>
              </button>

              <button
                onClick={handleDelete}
                className="btn btn-danger btn-sm"
                disabled={isActionBusy}
                title="Delete task"
              >
                <Trash2 size={15} />
                <span>Delete</span>
              </button>
            </div>
          </div>

          {/* Description */}
          <div style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.8px', marginBottom: '8px' }}>
              Description
            </h3>
            <div
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                padding: '16px 20px',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border-subtle)',
                fontSize: '14px',
                lineHeight: 1.6,
                color: task.description ? 'var(--text-primary)' : 'var(--text-muted)',
                fontStyle: task.description ? 'normal' : 'italic',
              }}
            >
              {task.description || 'No description provided for this task.'}
            </div>
          </div>

          {/* Metadata Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '20px',
              paddingTop: '24px',
              borderTop: '1px solid var(--border-subtle)',
            }}
          >
            {/* Assignee Box */}
            <div>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.6px' }}>
                Assignee
              </span>
              <div style={{ marginTop: '8px' }}>
                <select
                  className="form-select"
                  style={{ fontSize: '13px', padding: '6px 10px' }}
                  value={task.assigned_to || ''}
                  onChange={(e) => handleAssigneeChange(e.target.value)}
                  disabled={isActionBusy}
                >
                  <option value="">Unassigned</option>
                  {users.map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.email})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Creator Box */}
            <div>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.6px' }}>
                Created By
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px' }}>
                <div
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--text-secondary)',
                  }}
                >
                  <UserIcon size={14} />
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    {task.creator?.name || 'Unknown Author'}
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                    {task.creator?.email}
                  </div>
                </div>
              </div>
            </div>

            {/* Due Date */}
            <div>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.6px' }}>
                Due Date
              </span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '10px', fontSize: '13px', color: 'var(--text-secondary)' }}>
                <Calendar size={16} opacity={0.7} />
                <span>
                  {task.due_date
                    ? new Date(task.due_date).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })
                    : 'No due date'}
                </span>
              </div>
            </div>

            {/* Timestamps */}
            <div>
              <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-muted)', letterSpacing: '0.6px' }}>
                Timeline
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <Clock size={12} />
                  <span>Created: {new Date(task.created_at).toLocaleDateString()}</span>
                </div>
                {task.completed_at && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981' }}>
                    <CheckCircle2 size={12} />
                    <span>Completed: {new Date(task.completed_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <EditTaskModal
        task={task}
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onUpdated={() => {
          setIsEditModalOpen(false);
          handleReload();
        }}
      />
    </AppShell>
  );
}
