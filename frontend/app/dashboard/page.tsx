'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/AppShell';
import { StatCards } from '@/components/dashboard/StatCards';
import { TaskTable } from '@/components/tasks/TaskTable';
import { api } from '@/lib/api';
import { DashboardStats, Task } from '@/lib/types';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';
import { RotateCcw, ArrowRight } from 'lucide-react';

export default function DashboardPage() {
  const { user } = useAuth();
  const toast = useToast();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentTasks, setRecentTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const handleRefresh = useCallback(async () => {
    setIsLoading(true);
    try {
      const [statsData, tasksData] = await Promise.all([
        api.getDashboardStats(),
        api.getTasks(),
      ]);
      setStats(statsData);
      setRecentTasks(tasksData.tasks.slice(0, 5));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load dashboard metrics';
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    let ignore = false;
    async function loadInitial() {
      try {
        const [statsData, tasksData] = await Promise.all([
          api.getDashboardStats(),
          api.getTasks(),
        ]);
        if (!ignore) {
          setStats(statsData);
          setRecentTasks(tasksData.tasks.slice(0, 5));
        }
      } catch (err: unknown) {
        if (!ignore) {
          const msg = err instanceof Error ? err.message : 'Failed to load dashboard metrics';
          toast.error(msg);
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    loadInitial();
    return () => {
      ignore = true;
    };
  }, [toast]);

  return (
    <AppShell onTaskCreated={handleRefresh}>
      {/* Top Banner */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '28px',
        }}
      >
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.5px' }}>
            Dashboard Overview
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '4px' }}>
            Welcome back, <strong>{user?.name}</strong>. Here is your current task summary.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          className="btn btn-secondary btn-sm"
          disabled={isLoading}
          title="Refresh dashboard stats"
        >
          <RotateCcw size={15} className={isLoading ? 'spinner' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Statistics Cards */}
      <StatCards stats={stats} isLoading={isLoading} />

      {/* Recent Activity / Recent Tasks */}
      <div style={{ marginTop: '36px' }}>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '16px',
          }}
        >
          <div>
            <h2 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)' }}>
              Recent Tasks
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Most recently updated tasks across your accessible scope
            </p>
          </div>

          <Link href="/tasks" className="btn btn-ghost btn-sm" style={{ gap: '6px' }}>
            <span>View All Tasks</span>
            <ArrowRight size={15} />
          </Link>
        </div>

        <TaskTable
          tasks={recentTasks}
          isLoading={isLoading}
          onRefresh={handleRefresh}
        />
      </div>
    </AppShell>
  );
}
