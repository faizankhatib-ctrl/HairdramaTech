'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { LogOut, User as UserIcon, CheckSquare, Plus } from 'lucide-react';

interface NavbarProps {
  onOpenCreateModal?: () => void;
}

export function Navbar({ onOpenCreateModal }: NavbarProps) {
  const { user, logout } = useAuth();

  return (
    <header
      style={{
        height: '64px',
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 24px',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Brand */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            boxShadow: '0 2px 8px rgba(59, 130, 246, 0.4)',
          }}
        >
          <CheckSquare size={20} />
        </div>
        <Link href="/dashboard" style={{ display: 'flex', flexDirection: 'column' }}>
          <span style={{ fontSize: '15px', fontWeight: 800, letterSpacing: '-0.3px', color: 'var(--text-primary)' }}>
            HAIRDRAMA TECH
          </span>
          <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.8px' }}>
            Task Portal
          </span>
        </Link>
      </div>

      {/* Actions & User Profile */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {onOpenCreateModal && (
          <button
            onClick={onOpenCreateModal}
            className="btn btn-primary btn-sm"
            id="nav-create-task-btn"
          >
            <Plus size={16} />
            <span>Create Task</span>
          </button>
        )}

        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', borderLeft: '1px solid var(--border-subtle)', paddingLeft: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              {user.profile_image ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={user.profile_image}
                  alt={user.name}
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    border: '2px solid var(--border-default)',
                    objectFit: 'cover',
                  }}
                />
              ) : (
                <div
                  style={{
                    width: '34px',
                    height: '34px',
                    borderRadius: '50%',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--text-secondary)',
                    border: '1px solid var(--border-default)',
                  }}
                >
                  <UserIcon size={18} />
                </div>
              )}
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.2 }}>
                  {user.name}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', lineHeight: 1.2 }}>
                  {user.email}
                </span>
              </div>
            </div>

            <button
              onClick={logout}
              className="btn btn-ghost btn-sm"
              title="Sign Out"
              id="logout-btn"
              style={{ color: 'var(--text-muted)', marginLeft: '4px' }}
            >
              <LogOut size={16} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
