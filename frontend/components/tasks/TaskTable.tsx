'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Task } from '@/lib/types';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PriorityBadge } from '@/components/ui/PriorityBadge';
import { EditTaskModal } from './EditTaskModal';
import { api, APIError } from '@/lib/api';
import { useToast } from '@/components/ui/Toast';
import { CheckCircle2, Circle, Eye, Edit2, Trash2, Calendar, Inbox } from 'lucide-react';

interface TaskTableProps {
  tasks: Task[];
  isLoading: boolean;
  onRefresh: () => void;
}

export function TaskTable({ tasks, isLoading, onRefresh }: TaskTableProps) {
  const toast = useToast();
  const [selectedTaskForEdit, setSelectedTaskForEdit] = useState<Task | null>(null);
  const [actionInProgressId, setActionInProgressId] = useState<string | null>(null);

  const handleToggleComplete = async (task: Task) => {
    setActionInProgressId(task.id);
    try {
      await api.completeTask(task.id);
      const newStatus = task.status === 'COMPLETED' ? 'reopened' : 'marked as completed';
      toast.success(`Task ${newStatus}.`);
      onRefresh();
    } catch (err: unknown) {
      if (err instanceof APIError && err.statusCode === 403) {
        toast.error('You are not authorized to complete this task.');
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to update task status';
        toast.error(msg);
      }
    } finally {
      setActionInProgressId(null);
    }
  };

  const handleDelete = async (task: Task) => {
    if (!window.confirm(`Are you sure you want to delete task "${task.title}"?`)) {
      return;
    }

    setActionInProgressId(task.id);
    try {
      await api.deleteTask(task.id);
      toast.success('Task deleted successfully.');
      onRefresh();
    } catch (err: unknown) {
      if (err instanceof APIError && err.statusCode === 403) {
        toast.error('You are not authorized to delete this task. Only the creator can delete it.');
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to delete task';
        toast.error(msg);
      }
    } finally {
      setActionInProgressId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '40px' }}></th>
              <th>Task</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Assignee</th>
              <th>Due Date</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {[1, 2, 3, 4, 5].map((idx) => (
              <tr key={idx}>
                <td><div className="skeleton" style={{ width: '20px', height: '20px', borderRadius: '50%' }} /></td>
                <td><div className="skeleton" style={{ width: '180px', height: '16px' }} /></td>
                <td><div className="skeleton" style={{ width: '70px', height: '20px' }} /></td>
                <td><div className="skeleton" style={{ width: '80px', height: '20px' }} /></td>
                <td><div className="skeleton" style={{ width: '110px', height: '16px' }} /></td>
                <td><div className="skeleton" style={{ width: '90px', height: '16px' }} /></td>
                <td style={{ textAlign: 'right' }}><div className="skeleton" style={{ width: '60px', height: '24px', marginLeft: 'auto' }} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div
        className="card"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '60px 20px',
          textAlign: 'center',
          backgroundColor: 'var(--bg-surface)',
        }}
      >
        <div
          style={{
            width: '56px',
            height: '56px',
            borderRadius: '50%',
            backgroundColor: 'var(--bg-surface-elevated)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)',
            marginBottom: '16px',
          }}
        >
          <Inbox size={28} />
        </div>
        <h3 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '6px' }}>No Tasks Found</h3>
        <p style={{ fontSize: '14px', color: 'var(--text-secondary)', maxWidth: '400px' }}>
          No tasks match your selected filter criteria. Try adjusting your search or create a new task to get started.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: '48px', textAlign: 'center' }}>Done</th>
              <th>Task Details</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Assignee</th>
              <th>Due Date</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => {
              const isCompleted = task.status === 'COMPLETED';
              const isBusy = actionInProgressId === task.id;

              return (
                <tr key={task.id} style={{ opacity: isBusy ? 0.6 : 1 }}>
                  {/* Quick Toggle Status */}
                  <td style={{ textAlign: 'center' }}>
                    <button
                      onClick={() => handleToggleComplete(task)}
                      disabled={isBusy}
                      style={{
                        background: 'transparent',
                        border: 'none',
                        cursor: 'pointer',
                        color: isCompleted ? '#10b981' : 'var(--text-muted)',
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        transition: 'transform 0.1s ease',
                      }}
                      title={isCompleted ? 'Mark as incomplete' : 'Mark as completed'}
                    >
                      {isCompleted ? <CheckCircle2 size={20} /> : <Circle size={20} />}
                    </button>
                  </td>

                  {/* Title & Description */}
                  <td>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
                      <Link
                        href={`/tasks/${task.id}`}
                        style={{
                          fontWeight: 700,
                          color: isCompleted ? 'var(--text-muted)' : 'var(--text-primary)',
                          textDecoration: isCompleted ? 'line-through' : 'none',
                          fontSize: '14px',
                        }}
                      >
                        {task.title}
                      </Link>
                      {task.description && (
                        <span
                          style={{
                            fontSize: '12px',
                            color: 'var(--text-muted)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            maxWidth: '380px',
                          }}
                        >
                          {task.description}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Priority */}
                  <td>
                    <PriorityBadge priority={task.priority} />
                  </td>

                  {/* Status */}
                  <td>
                    <StatusBadge status={task.status} />
                  </td>

                  {/* Assignee */}
                  <td>
                    {task.assignee ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        {task.assignee.profile_image ? (
                          // eslint-disable-next-line @next/next/no-img-element
                          <img
                            src={task.assignee.profile_image}
                            alt={task.assignee.name}
                            style={{ width: '24px', height: '24px', borderRadius: '50%' }}
                          />
                        ) : (
                          <div
                            style={{
                              width: '24px',
                              height: '24px',
                              borderRadius: '50%',
                              backgroundColor: 'var(--bg-surface-hover)',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '11px',
                              fontWeight: 700,
                            }}
                          >
                            {task.assignee.name.charAt(0).toUpperCase()}
                          </div>
                        )}
                        <span style={{ fontSize: '13px', color: 'var(--text-primary)' }}>
                          {task.assignee.name}
                        </span>
                      </div>
                    ) : (
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                        Unassigned
                      </span>
                    )}
                  </td>

                  {/* Due Date */}
                  <td>
                    {task.due_date ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <Calendar size={14} opacity={0.7} />
                        <span>{new Date(task.due_date).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}</span>
                      </div>
                    ) : (
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>—</span>
                    )}
                  </td>

                  {/* Actions */}
                  <td style={{ textAlign: 'right' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '4px' }}>
                      <Link
                        href={`/tasks/${task.id}`}
                        className="btn btn-ghost btn-sm btn-icon"
                        title="View details"
                      >
                        <Eye size={15} />
                      </Link>

                      <button
                        onClick={() => setSelectedTaskForEdit(task)}
                        className="btn btn-ghost btn-sm btn-icon"
                        title="Edit task"
                        disabled={isBusy}
                      >
                        <Edit2 size={15} />
                      </button>

                      <button
                        onClick={() => handleDelete(task)}
                        className="btn btn-ghost btn-sm btn-icon"
                        style={{ color: '#f87171' }}
                        title="Delete task"
                        disabled={isBusy}
                      >
                        <Trash2 size={15} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <EditTaskModal
        task={selectedTaskForEdit}
        isOpen={!!selectedTaskForEdit}
        onClose={() => setSelectedTaskForEdit(null)}
        onUpdated={() => {
          setSelectedTaskForEdit(null);
          onRefresh();
        }}
      />
    </>
  );
}
