'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { CheckSquare, ShieldCheck, Mail, Users, ArrowRight } from 'lucide-react';

export default function HomePage() {
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
        flexDirection: 'column',
        backgroundColor: 'var(--bg-app)',
      }}
    >
      {/* Top Header */}
      <header
        style={{
          height: '70px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 40px',
          borderBottom: '1px solid var(--border-subtle)',
          backgroundColor: 'rgba(17, 24, 39, 0.7)',
          backdropFilter: 'blur(8px)',
        }}
      >
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
            }}
          >
            <CheckSquare size={20} />
          </div>
          <span style={{ fontSize: '16px', fontWeight: 800, letterSpacing: '-0.3px' }}>
            HAIRDRAMA TECH
          </span>
        </div>

        <Link href="/login" className="btn btn-primary btn-sm">
          <span>Sign In</span>
          <ArrowRight size={16} />
        </Link>
      </header>

      {/* Hero Section */}
      <main
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '80px 24px',
          textAlign: 'center',
          maxWidth: '900px',
          margin: '0 auto',
        }}
      >
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            border: '1px solid rgba(59, 130, 246, 0.3)',
            color: '#60a5fa',
            fontSize: '13px',
            fontWeight: 700,
            marginBottom: '24px',
          }}
        >
          <span>INTERNSHIP ASSIGNMENT PROJECT</span>
        </div>

        <h1
          style={{
            fontSize: '48px',
            fontWeight: 800,
            letterSpacing: '-1.5px',
            lineHeight: 1.15,
            marginBottom: '20px',
            color: '#ffffff',
          }}
        >
          High-Performance Task Management with Live Gmail Notifications
        </h1>

        <p
          style={{
            fontSize: '18px',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            maxWidth: '680px',
            marginBottom: '36px',
          }}
        >
          Architected with a secured Flask REST API, Supabase PostgreSQL with automated triggers,
          server-side Google OAuth 2.0 verification, and a responsive Next.js App Router frontend.
        </p>

        <div style={{ display: 'flex', gap: '16px', marginBottom: '64px' }}>
          <Link href="/login" className="btn btn-primary" style={{ padding: '12px 28px', fontSize: '15px' }}>
            Access Task Portal
            <ArrowRight size={18} />
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noreferrer"
            className="btn btn-secondary"
            style={{ padding: '12px 24px', fontSize: '15px' }}
          >
            Architecture Docs
          </a>
        </div>

        {/* Feature Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '20px',
            width: '100%',
            textAlign: 'left',
          }}
        >
          <div className="card">
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '8px',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#3b82f6',
                marginBottom: '14px',
              }}
            >
              <ShieldCheck size={22} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>
              Google OAuth 2.0 & JWT
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Strict server-side Google ID token cryptographic verification with signed 7-day Bearer JWT sessions.
            </p>
          </div>

          <div className="card">
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '8px',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#10b981',
                marginBottom: '14px',
              }}
            >
              <Mail size={22} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>
              Gmail SMTP Dispatch
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Asynchronous non-blocking background emails upon task assignments and completions with Jinja templates.
            </p>
          </div>

          <div className="card">
            <div
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '8px',
                backgroundColor: 'rgba(249, 115, 22, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#f97316',
                marginBottom: '14px',
              }}
            >
              <Users size={22} />
            </div>
            <h3 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '6px' }}>
              Role-Based Authorization
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
              Granular permissions ensuring creators retain modification rights and assignees can update execution status.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer
        style={{
          padding: '24px',
          textAlign: 'center',
          fontSize: '13px',
          color: 'var(--text-muted)',
          borderTop: '1px solid var(--border-subtle)',
        }}
      >
        Hairdrama Tech Full-Stack Internship Engineering Assignment
      </footer>
    </div>
  );
}
