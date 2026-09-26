'use client';

import React, { useState } from 'react';
import { GoogleOAuthProvider, GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { useAuth } from '@/lib/auth';
import { useToast } from '@/components/ui/Toast';

export function GoogleLoginButton() {
  const { loginWithGoogle } = useAuth();
  const toast = useToast();
  const [isProcessing, setIsProcessing] = useState(false);

  const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || '';

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      toast.error('No credential received from Google Identity Services.');
      return;
    }

    setIsProcessing(true);
    try {
      await loginWithGoogle(credentialResponse.credential);
      toast.success('Successfully authenticated with Google.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Authentication with Flask API failed.';
      toast.error(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleError = () => {
    toast.error('Google Sign-In failed or was cancelled.');
  };

  if (!clientId || clientId.includes('dummy-client-id') || clientId.includes('your-google-client-id')) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '14px',
          alignItems: 'center',
          width: '100%',
        }}
      >
        <div
          style={{
            backgroundColor: 'rgba(234, 179, 8, 0.1)',
            border: '1px solid rgba(234, 179, 8, 0.3)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px 16px',
            fontSize: '12px',
            color: '#facc15',
            lineHeight: 1.5,
            textAlign: 'left',
            width: '100%',
          }}
        >
          <strong>Google OAuth Client ID Required:</strong>
          <p style={{ marginTop: '4px', opacity: 0.9 }}>
            Set <code>NEXT_PUBLIC_GOOGLE_CLIENT_ID</code> in <code>frontend/.env.local</code> to enable live Google Sign-In.
          </p>
        </div>

        {/* Development credential input option for testing server verification */}
        <div style={{ width: '100%', marginTop: '6px' }}>
          <form
            onSubmit={async (e) => {
              e.preventDefault();
              const form = e.target as HTMLFormElement;
              const token = (form.elements.namedItem('testToken') as HTMLInputElement).value;
              if (token) {
                setIsProcessing(true);
                try {
                  await loginWithGoogle(token);
                  toast.success('Logged in successfully.');
                } catch (err: unknown) {
                  const msg = err instanceof Error ? err.message : 'Token verification failed';
                  toast.error(msg);
                } finally {
                  setIsProcessing(false);
                }
              }
            }}
            style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}
          >
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Developer Test: Submit Google ID Token directly
            </span>
            <div style={{ display: 'flex', gap: '8px' }}>
              <input
                name="testToken"
                type="text"
                placeholder="Paste Google ID Token..."
                className="form-input"
                style={{ fontSize: '12px', height: '36px' }}
                disabled={isProcessing}
              />
              <button
                type="submit"
                className="btn btn-secondary btn-sm"
                disabled={isProcessing}
                style={{ whiteSpace: 'nowrap' }}
              >
                {isProcessing ? <span className="spinner" /> : 'Verify'}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', width: '100%' }}>
        {isProcessing ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '10px' }}>
            <span className="spinner" />
            <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Verifying Google Token with Flask...</span>
          </div>
        ) : (
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            useOneTap={false}
            theme="filled_black"
            shape="rectangular"
            size="large"
            text="signin_with"
            width="320"
          />
        )}
      </div>
    </GoogleOAuthProvider>
  );
}
