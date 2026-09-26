'use client';

import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { api, APIError } from '@/lib/api';
import { Task, User, TaskPriority, TaskStatus, UpdateTaskInput } from '@/lib/types';
import { useToast } from '@/components/ui/Toast';

interface EditTaskModalProps {
  task: Task | null;
  isOpen: boolean;
  onClose: () => void;
  onUpdated: () => void;
}

interface EditFormProps {
  task: Task;
  onClose: () => void;
  onUpdated: () => void;
}

function EditTaskForm({ task, onClose, onUpdated }: EditFormProps) {
  const toast = useToast();
  const [title, setTitle] = useState(task.title || '');
  const [description, setDescription] = useState(task.description || '');
  const [priority, setPriority] = useState<TaskPriority>(task.priority);
  const [status, setStatus] = useState<TaskStatus>(task.status);
  const [dueDate, setDueDate] = useState(task.due_date ? task.due_date.substring(0, 10) : '');
  const [assignedTo, setAssignedTo] = useState(task.assigned_to || '');
  const [users, setUsers] = useState<User[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let ignore = false;
    api.getUsers()
      .then((data) => {
        if (!ignore) setUsers(data);
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Task title is required.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const input: UpdateTaskInput = {
        title: title.trim(),
        description: description.trim() || null,
        priority,
        status,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        assigned_to: assignedTo || null,
      };

      await api.updateTask(task.id, input);

      // If assignee changed, call assign endpoint explicitly to trigger backend assignment email
      if (assignedTo !== (task.assigned_to || '')) {
        await api.assignTask(task.id, assignedTo || null);
      }

      toast.success('Task updated successfully.');
      onUpdated();
    } catch (err: unknown) {
      if (err instanceof APIError && err.statusCode === 403) {
        setError('You are not authorized to perform this action.');
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to update task.';
        setError(msg);
      }
      const toastMsg = err instanceof Error ? err.message : 'Update failed';
      toast.error(toastMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div className="modal-body">
        {error && (
          <div
            style={{
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid #ef4444',
              color: '#f87171',
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '13px',
              marginBottom: '16px',
            }}
          >
            {error}
          </div>
        )}

        <div className="form-group">
          <label className="form-label" htmlFor="edit-task-title">
            Title <span style={{ color: '#ef4444' }}>*</span>
          </label>
          <input
            id="edit-task-title"
            type="text"
            className="form-input"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="edit-task-description">
            Description
          </label>
          <textarea
            id="edit-task-description"
            className="form-textarea"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
          />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-task-priority">
              Priority
            </label>
            <select
              id="edit-task-priority"
              className="form-select"
              value={priority}
              onChange={(e) => setPriority(e.target.value as TaskPriority)}
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="URGENT">Urgent</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="edit-task-status">
              Status
            </label>
            <select
              id="edit-task-status"
              className="form-select"
              value={status}
              onChange={(e) => setStatus(e.target.value as TaskStatus)}
            >
              <option value="TODO">To Do</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="COMPLETED">Completed</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <div className="form-group">
            <label className="form-label" htmlFor="edit-task-due-date">
              Due Date
            </label>
            <input
              id="edit-task-due-date"
              type="date"
              className="form-input"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="edit-task-assignee">
              Assignee
            </label>
            <select
              id="edit-task-assignee"
              className="form-select"
              value={assignedTo}
              onChange={(e) => setAssignedTo(e.target.value)}
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
      </div>

      <div className="modal-footer">
        <button type="button" onClick={onClose} className="btn btn-secondary" disabled={isSubmitting}>
          Cancel
        </button>
        <button type="submit" className="btn btn-primary" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <span className="spinner" />
              <span>Saving...</span>
            </>
          ) : (
            'Save Changes'
          )}
        </button>
      </div>
    </form>
  );
}

export function EditTaskModal({ task, isOpen, onClose, onUpdated }: EditTaskModalProps) {
  if (!isOpen || !task) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Edit Task Details">
      <EditTaskForm key={task.id} task={task} onClose={onClose} onUpdated={onUpdated} />
    </Modal>
  );
}
