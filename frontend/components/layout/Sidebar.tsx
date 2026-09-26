'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname, useSearchParams } from 'next/navigation';
import { LayoutDashboard, CheckSquare, UserCheck, FolderPlus } from 'lucide-react';

export function Sidebar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const currentScope = searchParams.get('scope');

  const navItems = [
    {
      label: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      isActive: pathname === '/dashboard',
    },
    {
      label: 'All Tasks',
      href: '/tasks',
      icon: CheckSquare,
      isActive: pathname === '/tasks' && !currentScope,
    },
    {
      label: 'Assigned to Me',
      href: '/tasks?scope=assigned_to_me',
      icon: UserCheck,
      isActive: pathname === '/tasks' && currentScope === 'assigned_to_me',
    },
    {
      label: 'Created by Me',
      href: '/tasks?scope=created_by_me',
      icon: FolderPlus,
      isActive: pathname === '/tasks' && currentScope === 'created_by_me',
    },
  ];

  return (
    <aside
      style={{
        width: '240px',
        backgroundColor: 'var(--bg-surface)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 16px',
        gap: '6px',
        flexShrink: 0,
      }}
    >
      <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)', padding: '0 12px 10px' }}>
        Workspace
      </div>

      {navItems.map((item) => {
        const Icon = item.icon;
        return (
          <Link
            key={item.label}
            href={item.href}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 14px',
              borderRadius: 'var(--radius-sm)',
              fontSize: '14px',
              fontWeight: item.isActive ? 700 : 500,
              color: item.isActive ? '#ffffff' : 'var(--text-secondary)',
              backgroundColor: item.isActive ? 'var(--primary)' : 'transparent',
              transition: 'all 0.15s ease',
            }}
          >
            <Icon size={18} opacity={item.isActive ? 1 : 0.8} />
            <span>{item.label}</span>
          </Link>
        );
      })}

      <div style={{ marginTop: 'auto', padding: '16px 12px', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '4px' }}>
          Internship Portal
        </div>
        <p style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.4 }}>
          Flask REST API + PostgreSQL backend connected with live Gmail notifications.
        </p>
      </div>
    </aside>
  );
}
