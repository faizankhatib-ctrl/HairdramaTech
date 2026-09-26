'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { GoogleLoginButton } from '@/components/auth/GoogleLoginButton';
import { CheckSquare, ShieldCheck, Mail, Database } from 'lucide-react';

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'var(--bg-app)',
        padding: '24px',
        position: 'relative',
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '460px',
          backgroundColor: 'var(--bg-surface)',
          borderRadius: 'var(--radius-lg)',
          border: '1px solid var(--border-default)',
          boxShadow: 'var(--shadow-lg)',
          overflow: 'hidden',
        }}
      >
        {/* Header Banner */}
        <div
          style={{
            padding: '36px 32px 28px',
            background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            borderBottom: '1px solid var(--border-subtle)',
            textAlign: 'center',
          }}
        >
          <div
            style={{
              width: '48px',
              height: '48px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#ffffff',
              margin: '0 auto 16px',
              boxShadow: '0 4px 14px rgba(59, 130, 246, 0.4)',
            }}
          >
            <CheckSquare size={26} />
          </div>

          <div
            style={{
              fontSize: '12px',
              fontWeight: 800,
              textTransform: 'uppercase',
              letterSpacing: '1.5px',
              color: '#60a5fa',
              marginBottom: '6px',
            }}
          >
            Hairdrama Tech
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.5px' }}>
            Task Management Portal
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginTop: '8px' }}>
            Sign in with your Google Workspace or Gmail account
          </p>
        </div>

        {/* Content Body */}
        <div style={{ padding: '32px' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '24px' }}>
            <GoogleLoginButton />
          </div>

          {/* Architecture details */}
          <div
            style={{
              borderTop: '1px solid var(--border-subtle)',
              paddingTop: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '12px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
              <ShieldCheck size={16} color="#3b82f6" />
              <span>Server-side cryptographic token verification</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
              <Mail size={16} color="#10b981" />
              <span>Gmail SMTP dispatch on assignment and completion</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: 'var(--text-muted)' }}>
              <Database size={16} color="#f59e0b" />
              <span>PostgreSQL schema with automated updated_at triggers</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: '16px 32px',
            backgroundColor: 'rgba(0, 0, 0, 0.2)',
            borderTop: '1px solid var(--border-subtle)',
            textAlign: 'center',
            fontSize: '12px',
            color: 'var(--text-muted)',
          }}
        >
          Protected by OAuth 2.0 & Stateless Application JWT
        </div>
      </div>
    </div>
  );
}
