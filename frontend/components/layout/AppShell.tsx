'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';
import { CreateTaskModal } from '@/components/tasks/CreateTaskModal';

interface AppShellProps {
  children: React.ReactNode;
  onTaskCreated?: () => void;
}

export function AppShell({ children, onTaskCreated }: AppShellProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '16px',
          backgroundColor: 'var(--bg-app)',
        }}
      >
        <div className="spinner" style={{ width: '32px', height: '32px', borderWidth: '3px' }} />
        <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>
          Loading Hairdrama Task Portal...
        </span>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Navbar onOpenCreateModal={() => setIsCreateModalOpen(true)} />
      <div style={{ display: 'flex', flex: 1, minHeight: 'calc(100vh - 64px)' }}>
        <Sidebar />
        <main
          style={{
            flex: 1,
            padding: '32px 40px',
            backgroundColor: 'var(--bg-app)',
            overflowY: 'auto',
          }}
        >
          {children}
        </main>
      </div>

      <CreateTaskModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={() => {
          setIsCreateModalOpen(false);
          if (onTaskCreated) onTaskCreated();
        }}
      />
    </div>
  );
}
