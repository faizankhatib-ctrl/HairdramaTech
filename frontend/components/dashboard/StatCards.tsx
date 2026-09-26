'use client';

import React from 'react';
import { DashboardStats } from '@/lib/types';
import { CheckSquare, Circle, Clock, CheckCircle2, UserCheck, FolderPlus } from 'lucide-react';

interface StatCardsProps {
  stats?: DashboardStats | null;
  isLoading: boolean;
}

export function StatCards({ stats, isLoading }: StatCardsProps) {
  if (isLoading) {
    return (
      <div className="stat-grid">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="stat-card">
            <div className="skeleton" style={{ width: '80px', height: '14px', marginBottom: '12px' }} />
            <div className="skeleton" style={{ width: '40px', height: '36px' }} />
          </div>
        ))}
      </div>
    );
  }

  const statItems = [
    {
      label: 'Total Tasks',
      value: stats?.total_tasks ?? 0,
      icon: CheckSquare,
      colorClass: '',
      accentColor: '#3b82f6',
    },
    {
      label: 'To Do',
      value: stats?.todo ?? 0,
      icon: Circle,
      colorClass: '',
      accentColor: '#38bdf8',
    },
    {
      label: 'In Progress',
      value: stats?.in_progress ?? 0,
      icon: Clock,
      colorClass: 'stat-in_progress',
      accentColor: '#f59e0b',
    },
    {
      label: 'Completed',
      value: stats?.completed ?? 0,
      icon: CheckCircle2,
      colorClass: 'stat-completed',
      accentColor: '#10b981',
    },
    {
      label: 'Assigned to Me',
      value: stats?.assigned_to_me ?? 0,
      icon: UserCheck,
      colorClass: '',
      accentColor: '#a855f7',
    },
    {
      label: 'Created by Me',
      value: stats?.created_by_me ?? 0,
      icon: FolderPlus,
      colorClass: '',
      accentColor: '#06b6d4',
    },
  ];

  return (
    <div className="stat-grid">
      {statItems.map((st) => {
        const Icon = st.icon;
        return (
          <div key={st.label} className={`stat-card ${st.colorClass}`}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span className="stat-label">{st.label}</span>
              <Icon size={18} color={st.accentColor} opacity={0.85} />
            </div>
            <div className="stat-value">{st.value}</div>
          </div>
        );
      })}
    </div>
  );
}
