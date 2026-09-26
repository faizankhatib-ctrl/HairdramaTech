'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { User, AuthState } from './types';
import {
  api,
  getStoredToken,
  setStoredToken,
  removeStoredToken,
  setUnauthorizedHandler,
} from './api';

interface AuthContextType extends AuthState {
  loginWithGoogle: (credential: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const router = useRouter();

  const handleLogout = useCallback(async () => {
    try {
      if (getStoredToken()) {
        await api.logout();
      }
    } catch {
      // Ignore network errors on logout
    } finally {
      removeStoredToken();
      setToken(null);
      setUser(null);
      router.push('/login');
    }
  }, [router]);

  const refreshUser = useCallback(async () => {
    const existingToken = getStoredToken();
    if (!existingToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      setToken(existingToken);
      const currentUser = await api.getCurrentUser();
      setUser(currentUser);
    } catch {
      removeStoredToken();
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Register 401 callback
    setUnauthorizedHandler(() => {
      setUser(null);
      setToken(null);
      removeStoredToken();
      router.push('/login');
    });

    let ignore = false;
    async function initSession() {
      const existingToken = getStoredToken();
      if (!existingToken) {
        if (!ignore) setIsLoading(false);
        return;
      }

      try {
        if (!ignore) setToken(existingToken);
        const currentUser = await api.getCurrentUser();
        if (!ignore) setUser(currentUser);
      } catch {
        removeStoredToken();
        if (!ignore) {
          setUser(null);
          setToken(null);
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    initSession();
    return () => {
      ignore = true;
    };
  }, [router]);

  const loginWithGoogle = async (credential: string) => {
    setIsLoading(true);
    try {
      const data = await api.googleLogin(credential);
      setStoredToken(data.token);
      setToken(data.token);
      setUser(data.user);
      router.push('/dashboard');
    } catch (err) {
      removeStoredToken();
      setToken(null);
      setUser(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isAuthenticated: !!user && !!token,
    isLoading,
    loginWithGoogle,
    logout: handleLogout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
