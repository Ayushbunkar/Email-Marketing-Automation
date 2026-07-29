import apiService from '@/api/client';
import { jwtDecode } from 'jwt-decode';

interface JwtPayload {
  sub: string;
  email: string;
  role: string;
  exp: number;
}

export interface User {
  id: string;
  email: string;
  role: string;
}

export class AuthService {
  private static instance: AuthService;

  private constructor() {}

  public static getInstance(): AuthService {
    if (!AuthService.instance) {
      AuthService.instance = new AuthService();
    }
    return AuthService.instance;
  }

  async login(email: string, password: string): Promise<{ user: User; accessToken: string; refreshToken: string }> {
    const response = await apiService.login({ email, password });
    const { access_token, refresh_token } = response.data;

    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);

    const user = this.decodeToken(access_token);
    return { user, accessToken: access_token, refreshToken: refresh_token };
  }

  async register(email: string, password: string): Promise<User> {
    const response = await apiService.register({ email, password });
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      await apiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  async refreshToken(): Promise<string> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await apiService.refreshToken(refreshToken);
    const { access_token, refresh_token: newRefreshToken } = response.data;

    localStorage.setItem('access_token', access_token);
    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken);
    }

    return access_token;
  }

  async getCurrentUser(): Promise<User | null> {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return null;
    }

    try {
      const user = this.decodeToken(token);
      return user;
    } catch (error) {
      console.error('Failed to decode token:', error);
      return null;
    }
  }

  async checkAuth(): Promise<boolean> {
    const token = localStorage.getItem('access_token');
    if (!token) {
      return false;
    }

    try {
      const decoded = jwtDecode<JwtPayload>(token);
      const now = Date.now() / 1000;

      if (decoded.exp < now) {
        return false;
      }

      return true;
    } catch (error) {
      return false;
    }
  }

  private decodeToken(token: string): User {
    const decoded = jwtDecode<JwtPayload>(token);
    return {
      id: decoded.sub,
      email: decoded.email,
      role: decoded.role,
    };
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }
}

// Singleton instance
export const authService = AuthService.getInstance();