# 前端开发指南

## 概述

本指南为前端开发者提供集成 CurioCloud Backend 用户认证系统的详细说明，包括登录/注册页面和个人中心的完整实现方案。

## 技术要求

### 支持的前端框架
- **React** 16.8+ (推荐 18+)
- **Vue.js** 3.0+
- **Angular** 12+
- **原生 JavaScript** (ES6+)
- **TypeScript** 4.0+

### HTTP 客户端
- **Axios** (推荐)
- **Fetch API** (原生)
- **jQuery Ajax** (兼容性考虑)

## 项目配置

### 环境配置
```javascript
// config/api.js
const API_CONFIG = {
    development: {
        baseURL: 'http://localhost:8000',
        timeout: 10000
    },
    production: {
        baseURL: 'https://api.curiocloud.com',
        timeout: 10000
    }
};

export const apiConfig = API_CONFIG[process.env.NODE_ENV || 'development'];
```

### HTTP 客户端配置 (Axios)
```javascript
// services/api.js
import axios from 'axios';
import { apiConfig } from '../config/api';

// 创建 Axios 实例
const api = axios.create({
    baseURL: apiConfig.baseURL,
    timeout: apiConfig.timeout,
    headers: {
        'Content-Type': 'application/json'
    }
});

// 请求拦截器 - 自动添加认证头
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// 响应拦截器 - 统一错误处理
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            // 令牌过期，清除本地存储并跳转登录
            localStorage.removeItem('access_token');
            localStorage.removeItem('user_info');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

export default api;
```

## 认证服务封装

### 认证服务类
```javascript
// services/authService.js
import api from './api';

class AuthService {
    // 用户注册
    async register(userData) {
        try {
            const response = await api.post('/api/auth/register', userData);
            const { user, token } = response.data;
            
            // 保存令牌和用户信息
            this.saveAuthData(token.access_token, user);
            
            return response.data;
        } catch (error) {
            throw this.handleApiError(error);
        }
    }

    // 用户登录
    async login(credentials) {
        try {
            const response = await api.post('/api/auth/login', credentials);
            const { user, token } = response.data;
            
            // 保存令牌和用户信息
            this.saveAuthData(token.access_token, user);
            
            return response.data;
        } catch (error) {
            throw this.handleApiError(error);
        }
    }

    // 获取用户资料
    async getProfile() {
        try {
            const response = await api.get('/api/user/profile');
            return response.data;
        } catch (error) {
            throw this.handleApiError(error);
        }
    }

    // 更新用户资料
    async updateProfile(profileData) {
        try {
            const response = await api.put('/api/user/profile', profileData);
            
            // 更新本地存储的用户信息
            const currentUser = this.getCurrentUser();
            const updatedUser = { ...currentUser, ...response.data };
            localStorage.setItem('user_info', JSON.stringify(updatedUser));
            
            return response.data;
        } catch (error) {
            throw this.handleApiError(error);
        }
    }

    // 获取用户状态
    async getUserStatus() {
        try {
            const response = await api.get('/api/user/profile/status');
            return response.data;
        } catch (error) {
            throw this.handleApiError(error);
        }
    }

    // 用户登出
    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login';
    }

    // 检查是否已登录
    isAuthenticated() {
        const token = localStorage.getItem('access_token');
        return !!token;
    }

    // 获取当前用户信息
    getCurrentUser() {
        const userInfo = localStorage.getItem('user_info');
        return userInfo ? JSON.parse(userInfo) : null;
    }

    // 获取访问令牌
    getAccessToken() {
        return localStorage.getItem('access_token');
    }

    // 保存认证数据
    saveAuthData(token, user) {
        localStorage.setItem('access_token', token);
        localStorage.setItem('user_info', JSON.stringify(user));
    }

    // 处理 API 错误
    handleApiError(error) {
        if (error.response) {
            const { status, data } = error.response;
            return {
                status,
                message: data.detail || '请求失败',
                type: this.getErrorType(status)
            };
        } else if (error.request) {
            return {
                status: 0,
                message: '网络连接失败，请检查网络设置',
                type: 'network'
            };
        } else {
            return {
                status: -1,
                message: '未知错误，请稍后重试',
                type: 'unknown'
            };
        }
    }

    // 获取错误类型
    getErrorType(status) {
        const errorTypes = {
            400: 'validation',
            401: 'authentication',
            403: 'authorization',
            404: 'not_found',
            422: 'validation',
            500: 'server'
        };
        return errorTypes[status] || 'unknown';
    }
}

export default new AuthService();
```

## 登录/注册页面实现

### React 实现

#### 注册组件
```jsx
// components/auth/RegisterForm.jsx
import React, { useState } from 'react';
import authService from '../../services/authService';

const RegisterForm = ({ onSuccess, onSwitchToLogin }) => {
    const [formData, setFormData] = useState({
        username: '',
        email: '',
        password: '',
        confirm_password: '',
        full_name: ''
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);

    // 表单验证
    const validateForm = () => {
        const newErrors = {};

        // 用户名验证
        if (!formData.username) {
            newErrors.username = '用户名不能为空';
        } else if (formData.username.length < 3) {
            newErrors.username = '用户名至少3个字符';
        } else if (!/^[a-zA-Z0-9_-]+$/.test(formData.username)) {
            newErrors.username = '用户名只能包含字母、数字、下划线和连字符';
        }

        // 邮箱验证
        if (!formData.email) {
            newErrors.email = '邮箱不能为空';
        } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
            newErrors.email = '邮箱格式不正确';
        }

        // 密码验证
        if (!formData.password) {
            newErrors.password = '密码不能为空';
        } else if (formData.password.length < 8) {
            newErrors.password = '密码至少8个字符';
        } else if (!/(?=.*[A-Za-z])(?=.*\d)/.test(formData.password)) {
            newErrors.password = '密码必须包含字母和数字';
        }

        // 确认密码验证
        if (formData.password !== formData.confirm_password) {
            newErrors.confirm_password = '两次输入的密码不一致';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // 处理表单提交
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) return;

        setLoading(true);
        try {
            const result = await authService.register(formData);
            onSuccess(result);
        } catch (error) {
            setErrors({ general: error.message });
        } finally {
            setLoading(false);
        }
    };

    // 处理输入变化
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        
        // 清除对应字段的错误
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    return (
        <div className="register-form">
            <h2>用户注册</h2>
            
            {errors.general && (
                <div className="error-message">{errors.general}</div>
            )}

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="username">用户名</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        className={errors.username ? 'error' : ''}
                        placeholder="请输入用户名"
                    />
                    {errors.username && <span className="error">{errors.username}</span>}
                </div>

                <div className="form-group">
                    <label htmlFor="email">邮箱地址</label>
                    <input
                        type="email"
                        id="email"
                        name="email"
                        value={formData.email}
                        onChange={handleChange}
                        className={errors.email ? 'error' : ''}
                        placeholder="请输入邮箱地址"
                    />
                    {errors.email && <span className="error">{errors.email}</span>}
                </div>

                <div className="form-group">
                    <label htmlFor="full_name">真实姓名</label>
                    <input
                        type="text"
                        id="full_name"
                        name="full_name"
                        value={formData.full_name}
                        onChange={handleChange}
                        placeholder="请输入真实姓名（可选）"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">密码</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        className={errors.password ? 'error' : ''}
                        placeholder="请输入密码"
                    />
                    {errors.password && <span className="error">{errors.password}</span>}
                </div>

                <div className="form-group">
                    <label htmlFor="confirm_password">确认密码</label>
                    <input
                        type="password"
                        id="confirm_password"
                        name="confirm_password"
                        value={formData.confirm_password}
                        onChange={handleChange}
                        className={errors.confirm_password ? 'error' : ''}
                        placeholder="请再次输入密码"
                    />
                    {errors.confirm_password && <span className="error">{errors.confirm_password}</span>}
                </div>

                <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={loading}
                >
                    {loading ? '注册中...' : '注册'}
                </button>
            </form>

            <div className="form-footer">
                <span>已有账户？</span>
                <button 
                    type="button" 
                    className="link-btn"
                    onClick={onSwitchToLogin}
                >
                    立即登录
                </button>
            </div>
        </div>
    );
};

export default RegisterForm;
```

#### 登录组件
```jsx
// components/auth/LoginForm.jsx
import React, { useState } from 'react';
import authService from '../../services/authService';

const LoginForm = ({ onSuccess, onSwitchToRegister }) => {
    const [formData, setFormData] = useState({
        username: '',
        password: ''
    });
    const [errors, setErrors] = useState({});
    const [loading, setLoading] = useState(false);

    // 处理表单提交
    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.username || !formData.password) {
            setErrors({ general: '用户名和密码不能为空' });
            return;
        }

        setLoading(true);
        try {
            const result = await authService.login(formData);
            onSuccess(result);
        } catch (error) {
            setErrors({ general: error.message });
        } finally {
            setLoading(false);
        }
    };

    // 处理输入变化
    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
        
        // 清除错误信息
        if (errors.general) {
            setErrors({});
        }
    };

    return (
        <div className="login-form">
            <h2>用户登录</h2>
            
            {errors.general && (
                <div className="error-message">{errors.general}</div>
            )}

            <form onSubmit={handleSubmit}>
                <div className="form-group">
                    <label htmlFor="username">用户名/邮箱</label>
                    <input
                        type="text"
                        id="username"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        placeholder="请输入用户名或邮箱"
                    />
                </div>

                <div className="form-group">
                    <label htmlFor="password">密码</label>
                    <input
                        type="password"
                        id="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="请输入密码"
                    />
                </div>

                <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={loading}
                >
                    {loading ? '登录中...' : '登录'}
                </button>
            </form>

            <div className="form-footer">
                <span>没有账户？</span>
                <button 
                    type="button" 
                    className="link-btn"
                    onClick={onSwitchToRegister}
                >
                    立即注册
                </button>
            </div>
        </div>
    );
};

export default LoginForm;
```

#### 认证页面容器
```jsx
// pages/AuthPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import RegisterForm from '../components/auth/RegisterForm';
import authService from '../services/authService';

const AuthPage = () => {
    const [isLogin, setIsLogin] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        // 如果已登录，重定向到首页
        if (authService.isAuthenticated()) {
            navigate('/dashboard');
        }
    }, [navigate]);

    const handleAuthSuccess = (result) => {
        // 登录/注册成功后的处理
        console.log('认证成功:', result);
        navigate('/dashboard');
    };

    const switchForm = () => {
        setIsLogin(!isLogin);
    };

    return (
        <div className="auth-page">
            <div className="auth-container">
                {isLogin ? (
                    <LoginForm 
                        onSuccess={handleAuthSuccess}
                        onSwitchToRegister={switchForm}
                    />
                ) : (
                    <RegisterForm 
                        onSuccess={handleAuthSuccess}
                        onSwitchToLogin={switchForm}
                    />
                )}
            </div>
        </div>
    );
};

export default AuthPage;
```

## 个人中心实现

### 个人资料组件
```jsx
// components/profile/ProfileForm.jsx
import React, { useState, useEffect } from 'react';
import authService from '../../services/authService';

const ProfileForm = () => {
    const [profile, setProfile] = useState({
        username: '',
        email: '',
        full_name: '',
        is_active: false,
        is_verified: false,
        created_at: '',
        updated_at: ''
    });
    const [editData, setEditData] = useState({
        full_name: '',
        email: ''
    });
    const [isEditing, setIsEditing] = useState(false);
    const [loading, setLoading] = useState(false);
    const [errors, setErrors] = useState({});
    const [success, setSuccess] = useState('');

    // 加载用户资料
    useEffect(() => {
        loadProfile();
    }, []);

    const loadProfile = async () => {
        setLoading(true);
        try {
            const data = await authService.getProfile();
            setProfile(data);
            setEditData({
                full_name: data.full_name || '',
                email: data.email
            });
        } catch (error) {
            setErrors({ general: error.message });
        } finally {
            setLoading(false);
        }
    };

    // 验证邮箱格式
    const validateEmail = (email) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    };

    // 处理保存
    const handleSave = async () => {
        setErrors({});
        setSuccess('');

        // 验证邮箱
        if (editData.email && !validateEmail(editData.email)) {
            setErrors({ email: '邮箱格式不正确' });
            return;
        }

        // 检查是否有变化
        const hasChanges = 
            editData.full_name !== (profile.full_name || '') ||
            editData.email !== profile.email;

        if (!hasChanges) {
            setIsEditing(false);
            return;
        }

        setLoading(true);
        try {
            const updatedProfile = await authService.updateProfile(editData);
            setProfile(updatedProfile);
            setIsEditing(false);
            setSuccess('资料更新成功');
        } catch (error) {
            setErrors({ general: error.message });
        } finally {
            setLoading(false);
        }
    };

    // 处理取消编辑
    const handleCancel = () => {
        setEditData({
            full_name: profile.full_name || '',
            email: profile.email
        });
        setIsEditing(false);
        setErrors({});
    };

    // 处理输入变化
    const handleChange = (e) => {
        const { name, value } = e.target;
        setEditData(prev => ({ ...prev, [name]: value }));
        
        // 清除对应字段的错误
        if (errors[name]) {
            setErrors(prev => ({ ...prev, [name]: '' }));
        }
    };

    if (loading && !profile.username) {
        return <div className="loading">加载中...</div>;
    }

    return (
        <div className="profile-form">
            <h2>个人资料</h2>

            {errors.general && (
                <div className="error-message">{errors.general}</div>
            )}

            {success && (
                <div className="success-message">{success}</div>
            )}

            <div className="profile-info">
                <div className="info-group">
                    <label>用户名</label>
                    <div className="info-value">{profile.username}</div>
                    <small className="info-note">用户名不可修改</small>
                </div>

                <div className="info-group">
                    <label htmlFor="email">邮箱地址</label>
                    {isEditing ? (
                        <>
                            <input
                                type="email"
                                id="email"
                                name="email"
                                value={editData.email}
                                onChange={handleChange}
                                className={errors.email ? 'error' : ''}
                            />
                            {errors.email && <span className="error">{errors.email}</span>}
                        </>
                    ) : (
                        <div className="info-value">
                            {profile.email}
                            {profile.is_verified ? (
                                <span className="verified">已验证</span>
                            ) : (
                                <span className="unverified">未验证</span>
                            )}
                        </div>
                    )}
                </div>

                <div className="info-group">
                    <label htmlFor="full_name">真实姓名</label>
                    {isEditing ? (
                        <input
                            type="text"
                            id="full_name"
                            name="full_name"
                            value={editData.full_name}
                            onChange={handleChange}
                            placeholder="请输入真实姓名"
                        />
                    ) : (
                        <div className="info-value">
                            {profile.full_name || '未设置'}
                        </div>
                    )}
                </div>

                <div className="info-group">
                    <label>账户状态</label>
                    <div className="info-value">
                        {profile.is_active ? (
                            <span className="status active">正常</span>
                        ) : (
                            <span className="status inactive">已禁用</span>
                        )}
                    </div>
                </div>

                <div className="info-group">
                    <label>注册时间</label>
                    <div className="info-value">
                        {new Date(profile.created_at).toLocaleString()}
                    </div>
                </div>

                <div className="info-group">
                    <label>最后更新</label>
                    <div className="info-value">
                        {new Date(profile.updated_at).toLocaleString()}
                    </div>
                </div>
            </div>

            <div className="profile-actions">
                {isEditing ? (
                    <>
                        <button 
                            className="save-btn"
                            onClick={handleSave}
                            disabled={loading}
                        >
                            {loading ? '保存中...' : '保存'}
                        </button>
                        <button 
                            className="cancel-btn"
                            onClick={handleCancel}
                            disabled={loading}
                        >
                            取消
                        </button>
                    </>
                ) : (
                    <button 
                        className="edit-btn"
                        onClick={() => setIsEditing(true)}
                    >
                        编辑资料
                    </button>
                )}
            </div>
        </div>
    );
};

export default ProfileForm;
```

### 个人中心页面
```jsx
// pages/ProfilePage.jsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProfileForm from '../components/profile/ProfileForm';
import authService from '../services/authService';

const ProfilePage = () => {
    const navigate = useNavigate();
    const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);

    const handleLogout = () => {
        authService.logout();
        navigate('/login');
    };

    return (
        <div className="profile-page">
            <div className="profile-header">
                <h1>个人中心</h1>
                <button 
                    className="logout-btn"
                    onClick={() => setShowLogoutConfirm(true)}
                >
                    退出登录
                </button>
            </div>

            <div className="profile-content">
                <ProfileForm />
            </div>

            {/* 退出确认对话框 */}
            {showLogoutConfirm && (
                <div className="modal-overlay">
                    <div className="modal">
                        <h3>确认退出</h3>
                        <p>确定要退出登录吗？</p>
                        <div className="modal-actions">
                            <button 
                                className="confirm-btn"
                                onClick={handleLogout}
                            >
                                确定
                            </button>
                            <button 
                                className="cancel-btn"
                                onClick={() => setShowLogoutConfirm(false)}
                            >
                                取消
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ProfilePage;
```

## 路由保护

### 路由保护组件
```jsx
// components/common/ProtectedRoute.jsx
import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import authService from '../../services/authService';

const ProtectedRoute = ({ children }) => {
    const location = useLocation();
    const isAuthenticated = authService.isAuthenticated();

    if (!isAuthenticated) {
        // 保存当前路径，登录后重定向
        return <Navigate to="/login" state={{ from: location }} replace />;
    }

    return children;
};

export default ProtectedRoute;
```

### 路由配置示例
```jsx
// App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import AuthPage from './pages/AuthPage';
import ProfilePage from './pages/ProfilePage';
import DashboardPage from './pages/DashboardPage';
import ProtectedRoute from './components/common/ProtectedRoute';

function App() {
    return (
        <Router>
            <div className="App">
                <Routes>
                    <Route path="/login" element={<AuthPage />} />
                    <Route 
                        path="/profile" 
                        element={
                            <ProtectedRoute>
                                <ProfilePage />
                            </ProtectedRoute>
                        } 
                    />
                    <Route 
                        path="/dashboard" 
                        element={
                            <ProtectedRoute>
                                <DashboardPage />
                            </ProtectedRoute>
                        } 
                    />
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />
                </Routes>
            </div>
        </Router>
    );
}

export default App;
```

## 状态管理 (Redux/Context)

### React Context 实现
```jsx
// contexts/AuthContext.jsx
import React, { createContext, useContext, useReducer, useEffect } from 'react';
import authService from '../services/authService';

const AuthContext = createContext();

// 状态类型
const authReducer = (state, action) => {
    switch (action.type) {
        case 'LOGIN_SUCCESS':
            return {
                ...state,
                isAuthenticated: true,
                user: action.payload.user,
                token: action.payload.token,
                loading: false,
                error: null
            };
        case 'LOGOUT':
            return {
                ...state,
                isAuthenticated: false,
                user: null,
                token: null,
                loading: false,
                error: null
            };
        case 'UPDATE_PROFILE':
            return {
                ...state,
                user: { ...state.user, ...action.payload }
            };
        case 'SET_LOADING':
            return {
                ...state,
                loading: action.payload
            };
        case 'SET_ERROR':
            return {
                ...state,
                error: action.payload,
                loading: false
            };
        default:
            return state;
    }
};

// 初始状态
const initialState = {
    isAuthenticated: false,
    user: null,
    token: null,
    loading: true,
    error: null
};

export const AuthProvider = ({ children }) => {
    const [state, dispatch] = useReducer(authReducer, initialState);

    // 初始化认证状态
    useEffect(() => {
        const token = authService.getAccessToken();
        const user = authService.getCurrentUser();
        
        if (token && user) {
            dispatch({
                type: 'LOGIN_SUCCESS',
                payload: { user, token }
            });
        } else {
            dispatch({ type: 'SET_LOADING', payload: false });
        }
    }, []);

    // 登录
    const login = async (credentials) => {
        dispatch({ type: 'SET_LOADING', payload: true });
        try {
            const result = await authService.login(credentials);
            dispatch({
                type: 'LOGIN_SUCCESS',
                payload: result
            });
            return result;
        } catch (error) {
            dispatch({ type: 'SET_ERROR', payload: error.message });
            throw error;
        }
    };

    // 注册
    const register = async (userData) => {
        dispatch({ type: 'SET_LOADING', payload: true });
        try {
            const result = await authService.register(userData);
            dispatch({
                type: 'LOGIN_SUCCESS',
                payload: result
            });
            return result;
        } catch (error) {
            dispatch({ type: 'SET_ERROR', payload: error.message });
            throw error;
        }
    };

    // 更新资料
    const updateProfile = async (profileData) => {
        try {
            const updatedUser = await authService.updateProfile(profileData);
            dispatch({
                type: 'UPDATE_PROFILE',
                payload: updatedUser
            });
            return updatedUser;
        } catch (error) {
            dispatch({ type: 'SET_ERROR', payload: error.message });
            throw error;
        }
    };

    // 登出
    const logout = () => {
        authService.logout();
        dispatch({ type: 'LOGOUT' });
    };

    const value = {
        ...state,
        login,
        register,
        updateProfile,
        logout
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
```

## 样式设计参考

### CSS 样式示例
```css
/* styles/auth.css */
.auth-page {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.auth-container {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    width: 100%;
    max-width: 400px;
}

.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    color: #333;
    font-weight: 500;
}

.form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 1rem;
}

.form-group input:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.form-group input.error {
    border-color: #e53e3e;
}

.error {
    color: #e53e3e;
    font-size: 0.875rem;
    margin-top: 0.25rem;
    display: block;
}

.error-message {
    background: #fed7d7;
    color: #c53030;
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    border: 1px solid #feb2b2;
}

.success-message {
    background: #c6f6d5;
    color: #22543d;
    padding: 0.75rem;
    border-radius: 4px;
    margin-bottom: 1rem;
    border: 1px solid #9ae6b4;
}

.submit-btn {
    width: 100%;
    padding: 0.75rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
    transition: background-color 0.2s;
}

.submit-btn:hover:not(:disabled) {
    background: #5a67d8;
}

.submit-btn:disabled {
    background: #a0aec0;
    cursor: not-allowed;
}

.form-footer {
    text-align: center;
    margin-top: 1rem;
    color: #666;
}

.link-btn {
    background: none;
    border: none;
    color: #667eea;
    cursor: pointer;
    text-decoration: underline;
    margin-left: 0.5rem;
}

.link-btn:hover {
    color: #5a67d8;
}

/* styles/profile.css */
.profile-page {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
}

.profile-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #e2e8f0;
}

.profile-header h1 {
    color: #2d3748;
    margin: 0;
}

.logout-btn {
    padding: 0.5rem 1rem;
    background: #e53e3e;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.logout-btn:hover {
    background: #c53030;
}

.profile-form {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.info-group {
    margin-bottom: 1.5rem;
}

.info-group label {
    display: block;
    margin-bottom: 0.5rem;
    color: #4a5568;
    font-weight: 500;
}

.info-value {
    padding: 0.75rem;
    background: #f7fafc;
    border-radius: 4px;
    color: #2d3748;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.info-note {
    color: #718096;
    font-size: 0.875rem;
    margin-top: 0.25rem;
    display: block;
}

.verified {
    background: #c6f6d5;
    color: #22543d;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.unverified {
    background: #fed7d7;
    color: #c53030;
    padding: 0.25rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
}

.status.active {
    color: #22543d;
    font-weight: 500;
}

.status.inactive {
    color: #c53030;
    font-weight: 500;
}

.profile-actions {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
}

.edit-btn, .save-btn {
    padding: 0.75rem 1.5rem;
    background: #667eea;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.edit-btn:hover, .save-btn:hover:not(:disabled) {
    background: #5a67d8;
}

.cancel-btn {
    padding: 0.75rem 1.5rem;
    background: #e2e8f0;
    color: #4a5568;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.cancel-btn:hover {
    background: #cbd5e0;
}

.save-btn:disabled, .cancel-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.modal {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    max-width: 400px;
    width: 90%;
}

.modal h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    color: #2d3748;
}

.modal p {
    margin-bottom: 1.5rem;
    color: #4a5568;
}

.modal-actions {
    display: flex;
    gap: 1rem;
    justify-content: flex-end;
}

.confirm-btn {
    padding: 0.5rem 1rem;
    background: #e53e3e;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.2s;
}

.confirm-btn:hover {
    background: #c53030;
}

.loading {
    text-align: center;
    padding: 2rem;
    color: #4a5568;
}
```

## 最佳实践

### 1. 错误处理
- 统一的错误处理机制
- 用户友好的错误提示
- 网络错误重试机制
- 表单验证错误高亮

### 2. 用户体验
- 加载状态提示
- 操作成功反馈
- 防重复提交
- 响应式设计

### 3. 安全性
- 令牌自动过期处理
- 敏感操作确认
- 输入数据验证
- XSS 防护

### 4. 性能优化
- 组件懒加载
- 图片优化
- 缓存策略
- 代码分割

### 5. 可维护性
- 组件模块化
- 代码复用
- 文档注释
- 统一的编码规范

## 总结

本指南提供了完整的前端集成方案，包括：
- 完整的认证服务封装
- React 组件实现示例
- 路由保护机制
- 状态管理方案
- 样式设计参考
- 最佳实践建议

开发者可以根据实际项目需求调整和扩展这些示例代码，确保与后端 API 的完美集成。