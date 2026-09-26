'use client';

import React from 'react';
import { TaskStatus, TaskPriority, TaskScope, TaskFilterParams } from '@/lib/types';
import { Search, RotateCcw } from 'lucide-react';

interface TaskFiltersProps {
  filters: TaskFilterParams;
  onChange: (newFilters: TaskFilterParams) => void;
  onReset: () => void;
}

export function TaskFilters({ filters, onChange, onReset }: TaskFiltersProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
      }}
    >
      {/* Search Input */}
      <div style={{ position: 'relative', minWidth: '260px', flex: '1 1 260px' }}>
        <Search
          size={16}
          style={{
            position: 'absolute',
            left: '12px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)',
            pointerEvents: 'none',
          }}
        />
        <input
          type="text"
          placeholder="Search tasks by title or description..."
          className="form-input"
          style={{ paddingLeft: '38px', height: '40px' }}
          value={filters.search || ''}
          onChange={(e) => onChange({ ...filters, search: e.target.value })}
        />
      </div>

      {/* Dropdown Filters */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
        {/* Scope Selector */}
        <select
          className="form-select"
          style={{ width: 'auto', minWidth: '150px', height: '40px' }}
          value={filters.scope || 'all'}
          onChange={(e) => onChange({ ...filters, scope: e.target.value as TaskScope })}
        >
          <option value="all">All Tasks</option>
          <option value="assigned_to_me">Assigned to Me</option>
          <option value="created_by_me">Created by Me</option>
        </select>

        {/* Status Selector */}
        <select
          className="form-select"
          style={{ width: 'auto', minWidth: '130px', height: '40px' }}
          value={filters.status || ''}
          onChange={(e) =>
            onChange({ ...filters, status: (e.target.value || undefined) as TaskStatus | undefined })
          }
        >
          <option value="">All Statuses</option>
          <option value="TODO">To Do</option>
          <option value="IN_PROGRESS">In Progress</option>
          <option value="COMPLETED">Completed</option>
        </select>

        {/* Priority Selector */}
        <select
          className="form-select"
          style={{ width: 'auto', minWidth: '130px', height: '40px' }}
          value={filters.priority || ''}
          onChange={(e) =>
            onChange({ ...filters, priority: (e.target.value || undefined) as TaskPriority | undefined })
          }
        >
          <option value="">All Priorities</option>
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="URGENT">Urgent</option>
        </select>

        {/* Reset Filter Button */}
        {(filters.search || filters.status || filters.priority || (filters.scope && filters.scope !== 'all')) && (
          <button
            onClick={onReset}
            className="btn btn-ghost btn-sm"
            style={{ height: '40px', color: 'var(--text-muted)' }}
            title="Reset filters"
          >
            <RotateCcw size={15} />
            <span>Reset</span>
          </button>
        )}
      </div>
    </div>
  );
}
