import React, { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';

interface User {
  id: string;
  email: string;
  plan: string;
  files_processed_this_month: number;
  created_at: string;
}

interface UsageInfo {
  user_type: 'anonymous' | 'registered';
  files_used: number;
  files_remaining?: number;
  needs_signup?: boolean;
  file_size_limit_mb: number;
  plan?: string;
  files_limit?: number;
}

interface AuthContextType {
  user: User | null;
  usageInfo: UsageInfo | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUsage: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [usageInfo, setUsageInfo] = useState<UsageInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const getToken = () => localStorage.getItem('token');

  const setToken = (token: string) => localStorage.setItem('token', token);

  const removeToken = () => localStorage.removeItem('token');

  const fetchUsageInfo = useCallback(async () => {
    try {
      const response = await fetch('/usage-info', {
        headers: user ? { 'Authorization': `Bearer ${getToken()}` } : {}
      });
      if (response.ok) {
        const data = await response.json();
        setUsageInfo(data);
      }
    } catch (error) {
      console.error('Failed to fetch usage info:', error);
    }
  }, [user]);

  const login = async (email: string, password: string) => {
    const response = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    setToken(data.access_token);
    setUser(data.user);
    await fetchUsageInfo();
  };

  const register = async (email: string, password: string) => {
    const response = await fetch('/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    setToken(data.access_token);
    setUser(data.user);
    await fetchUsageInfo();
  };

  const logout = () => {
    removeToken();
    setUser(null);
    setUsageInfo(null);
  };

  const refreshUsage = async () => {
    await fetchUsageInfo();
  };

  useEffect(() => {
    const checkAuth = async () => {
      const token = getToken();
      if (token) {
        try {
          const response = await fetch('/auth/me', {
            headers: { 'Authorization': `Bearer ${token}` }
          });
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          } else {
            removeToken();
          }
        } catch (error) {
          removeToken();
        }
      }
      await fetchUsageInfo();
      setIsLoading(false);
    };

    checkAuth();
  }, [fetchUsageInfo]);

  const value = {
    user,
    usageInfo,
    isLoading,
    login,
    register,
    logout,
    refreshUsage
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}; 