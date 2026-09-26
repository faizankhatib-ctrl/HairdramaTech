'use client';

import React, { useState, useEffect } from 'react';
import { Modal } from '@/components/ui/Modal';
import { api } from '@/lib/api';
import { User, TaskPriority, TaskStatus, CreateTaskInput } from '@/lib/types';
import { useToast } from '@/components/ui/Toast';

interface CreateTaskModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateTaskModal({ isOpen, onClose, onCreated }: CreateTaskModalProps) {
  const toast = useToast();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState<TaskPriority>('MEDIUM');
  const [status, setStatus] = useState<TaskStatus>('TODO');
  const [dueDate, setDueDate] = useState('');
  const [assignedTo, setAssignedTo] = useState('');
  const [users, setUsers] = useState<User[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const resetForm = () => {
    setTitle('');
    setDescription('');
    setPriority('MEDIUM');
    setStatus('TODO');
    setDueDate('');
    setAssignedTo('');
    setErrors({});
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  useEffect(() => {
    if (!isOpen) return;
    let ignore = false;
    api.getUsers()
      .then((data) => {
        if (!ignore) setUsers(data);
      })
      .catch(() => {});
    return () => {
      ignore = true;
    };
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: { [key: string]: string } = {};

    if (!title.trim()) {
      newErrors.title = 'Task title is required.';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const input: CreateTaskInput = {
        title: title.trim(),
        description: description.trim() || null,
        priority,
        status,
        due_date: dueDate ? new Date(dueDate).toISOString() : null,
        assigned_to: assignedTo || null,
      };

      await api.createTask(input);
      toast.success('Task created successfully! Notification sent if assigned.');
      resetForm();
      onCreated();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create task';
      toast.error(msg);
      setErrors({ form: msg });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create New Task">
      <form onSubmit={handleSubmit}>
        <div className="modal-body">
          {errors.form && (
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
              {errors.form}
            </div>
          )}

          <div className="form-group">
            <label className="form-label" htmlFor="task-title">
              Title <span style={{ color: '#ef4444' }}>*</span>
            </label>
            <input
              id="task-title"
              type="text"
              className="form-input"
              placeholder="e.g. Implement authentication flow audit"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
            {errors.title && <span className="form-error">{errors.title}</span>}
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="task-description">
              Description
            </label>
            <textarea
              id="task-description"
              className="form-textarea"
              placeholder="Add key deliverables, technical context, or notes..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div className="form-group">
              <label className="form-label" htmlFor="task-priority">
                Priority
              </label>
              <select
                id="task-priority"
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
              <label className="form-label" htmlFor="task-status">
                Initial Status
              </label>
              <select
                id="task-status"
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
              <label className="form-label" htmlFor="task-due-date">
                Due Date
              </label>
              <input
                id="task-due-date"
                type="date"
                className="form-input"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="task-assignee">
                Assignee
              </label>
              <select
                id="task-assignee"
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
          <button type="button" onClick={handleClose} className="btn btn-secondary" disabled={isSubmitting}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting} id="submit-create-task-btn">
            {isSubmitting ? (
              <>
                <span className="spinner" />
                <span>Creating...</span>
              </>
            ) : (
              'Create Task'
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
}
