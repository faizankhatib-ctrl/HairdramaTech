'use client';

import React, { useState, useEffect, useCallback, useMemo, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { AppShell } from '@/components/layout/AppShell';
import { TaskTable } from '@/components/tasks/TaskTable';
import { TaskFilters } from '@/components/tasks/TaskFilters';
import { api } from '@/lib/api';
import { Task, TaskFilterParams, TaskScope } from '@/lib/types';
import { useToast } from '@/components/ui/Toast';
import { RotateCcw } from 'lucide-react';

function TasksContent() {
  const searchParams = useSearchParams();
  const scopeFromUrl = searchParams.get('scope') as TaskScope | null;

  const toast = useToast();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);

  const [customFilters, setCustomFilters] = useState<TaskFilterParams>({
    search: '',
    status: undefined,
    priority: undefined,
    scope: undefined,
  });

  const activeFilters: TaskFilterParams = useMemo(() => ({
    ...customFilters,
    scope: scopeFromUrl || customFilters.scope || 'all',
  }), [customFilters, scopeFromUrl]);

  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await api.getTasks(activeFilters);
      setTasks(data.tasks);
      setTotal(data.total);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch tasks';
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  }, [activeFilters, toast]);

  useEffect(() => {
    let ignore = false;
    async function loadTasks() {
      try {
        const data = await api.getTasks(activeFilters);
        if (!ignore) {
          setTasks(data.tasks);
          setTotal(data.total);
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : 'Failed to fetch tasks';
          toast.error(msg);
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    loadTasks();
    return () => {
      ignore = true;
    };
  }, [activeFilters, toast]);

  const handleResetFilters = () => {
    setCustomFilters({
      search: '',
      status: undefined,
      priority: undefined,
      scope: 'all',
    });
  };

  return (
    <div>
      {/* Page Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.5px' }}>
              Tasks
            </h1>
            <span
              style={{
                backgroundColor: 'var(--bg-surface-elevated)',
                color: 'var(--text-secondary)',
                fontSize: '13px',
                fontWeight: 700,
                padding: '2px 10px',
                borderRadius: 'var(--radius-full)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              {total} total
            </span>
          </div>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Manage, filter, reassign, and track execution status
          </p>
        </div>

        <button
          onClick={handleRefresh}
          className="btn btn-secondary btn-sm"
          disabled={isLoading}
          title="Refresh task list"
        >
          <RotateCcw size={15} className={isLoading ? 'spinner' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <TaskFilters
        filters={activeFilters}
        onChange={setCustomFilters}
        onReset={handleResetFilters}
      />

      {/* Task Table */}
      <TaskTable
        tasks={tasks}
        isLoading={isLoading}
        onRefresh={handleRefresh}
      />
    </div>
  );
}

export default function TasksPage() {
  return (
    <AppShell>
      <Suspense fallback={<div className="spinner" style={{ margin: '40px auto' }} />}>
        <TasksContent />
      </Suspense>
    </AppShell>
  );
}
