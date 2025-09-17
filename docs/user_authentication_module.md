# 用户认证模块文档

## 概述

CurioCloud Backend 用户认证模块提供完整的用户注册、登录和资料管理功能，基于 FastAPI 框架构建，采用 JWT 令牌认证机制，确保系统安全性和用户体验。

## 功能特性

### 核心功能
- ✅ **用户注册**: 支持用户名、邮箱、密码注册
- ✅ **用户登录**: 支持用户名/邮箱登录，JWT 令牌认证
- ✅ **用户资料管理**: 获取和更新用户个人信息
- ✅ **密码安全**: bcrypt 哈希加密，强密码策略
- ✅ **数据验证**: 严格的输入验证和错误处理
- ✅ **权限控制**: 基于令牌的访问控制

### 安全特性
- JWT 令牌认证机制
- 密码强度验证（字母+数字+特殊字符）
- 用户名和邮箱唯一性验证
- 防 SQL 注入（SQLAlchemy ORM）
- CORS 跨域保护

## 系统架构

### 技术栈
- **框架**: FastAPI 0.110.0
- **数据库**: MySQL + SQLAlchemy ORM
- **认证**: JWT + python-jose
- **密码加密**: bcrypt + passlib
- **数据验证**: Pydantic
- **测试框架**: pytest

### 模块结构
```
app/
├── models/user.py          # 用户数据模型
├── schemas/user.py         # 数据验证模式
├── services/auth_service.py # 认证业务逻辑
├── routers/
│   ├── auth.py            # 认证路由
│   └── user.py            # 用户管理路由
├── dependencies/auth.py    # 认证依赖
└── utils/
    ├── security.py        # 密码工具
    └── jwt.py             # JWT 工具
```

## 数据库设计

### users 表结构

| 字段名 | 数据类型 | 约束条件 | 描述 |
|--------|----------|----------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 用户唯一标识 |
| username | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL, INDEX | 邮箱地址 |
| full_name | VARCHAR(100) | NULL | 用户全名 |
| hashed_password | VARCHAR(255) | NOT NULL | 哈希加密密码 |
| is_active | BOOLEAN | DEFAULT TRUE | 账户是否激活 |
| is_verified | BOOLEAN | DEFAULT FALSE | 邮箱是否验证 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE NOW() | 更新时间 |

### 索引设计
- **主键索引**: `id`
- **唯一索引**: `username`, `email`
- **普通索引**: `username`, `email` (用于快速查询)

## API 接口文档

### 基础信息
- **基础URL**: `http://localhost:8000`
- **API 前缀**: `/api`
- **认证方式**: Bearer Token
- **响应格式**: JSON

### 1. 用户注册

#### 接口信息
- **URL**: `POST /api/auth/register`
- **功能**: 注册新用户账户
- **认证**: 无需认证

#### 请求参数
```json
{
    "username": "string",      // 用户名，3-50字符，字母数字下划线
    "email": "string",         // 邮箱地址，有效邮箱格式
    "password": "string",      // 密码，最少8字符，包含字母数字特殊字符
    "confirm_password": "string", // 确认密码，必须与密码一致
    "full_name": "string"      // 可选，用户全名，最大100字符
}
```

#### 响应示例
**成功响应 (201 Created)**:
```json
{
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "测试用户",
        "is_active": true,
        "is_verified": false,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
    },
    "token": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 1800
    },
    "message": "注册成功"
}
```

**错误响应 (400 Bad Request)**:
```json
{
    "detail": "用户名已存在"
}
```

### 2. 用户登录

#### 接口信息
- **URL**: `POST /api/auth/login`
- **功能**: 用户身份验证
- **认证**: 无需认证

#### 请求参数
```json
{
    "username": "string",    // 用户名或邮箱地址
    "password": "string"     // 密码
}
```

#### 响应示例
**成功响应 (200 OK)**:
```json
{
    "user": {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "测试用户",
        "is_active": true,
        "is_verified": false,
        "created_at": "2024-01-01T12:00:00Z",
        "updated_at": "2024-01-01T12:00:00Z"
    },
    "token": {
        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "token_type": "bearer",
        "expires_in": 1800
    },
    "message": "登录成功"
}
```

**错误响应 (401 Unauthorized)**:
```json
{
    "detail": "用户名、邮箱或密码错误"
}
```

### 3. 获取用户资料

#### 接口信息
- **URL**: `GET /api/user/profile`
- **功能**: 获取当前登录用户的资料信息
- **认证**: 需要 Bearer Token

#### 请求头
```
Authorization: Bearer {access_token}
```

#### 响应示例
**成功响应 (200 OK)**:
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "测试用户",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:00:00Z"
}
```

**错误响应 (401 Unauthorized)**:
```json
{
    "detail": "无法验证用户凭据"
}
```

### 4. 更新用户资料

#### 接口信息
- **URL**: `PUT /api/user/profile`
- **功能**: 更新当前登录用户的资料信息
- **认证**: 需要 Bearer Token

#### 请求头
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

#### 请求参数
```json
{
    "full_name": "string",   // 可选，用户全名
    "email": "string"        // 可选，邮箱地址
}
```

#### 响应示例
**成功响应 (200 OK)**:
```json
{
    "id": 1,
    "username": "testuser",
    "email": "newemail@example.com",
    "full_name": "更新后的用户名",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:05:00Z"
}
```

**错误响应 (400 Bad Request)**:
```json
{
    "detail": "邮箱已被其他用户使用"
}
```

### 5. 获取用户状态

#### 接口信息
- **URL**: `GET /api/user/profile/status`
- **功能**: 获取当前用户的账户状态信息
- **认证**: 需要 Bearer Token

#### 请求头
```
Authorization: Bearer {access_token}
```

#### 响应示例
**成功响应 (200 OK)**:
```json
{
    "message": "用户 testuser: 账户已激活, 邮箱未验证",
    "success": true
}
```

## 前端集成指南

### 登录/注册页面

#### 注册流程
1. **用户输入验证**
   - 用户名: 3-50字符，仅字母数字下划线
   - 邮箱: 有效邮箱格式验证
   - 密码: 至少8字符，包含字母+数字+特殊字符
   - 确认密码: 与密码一致

2. **API调用示例**
```javascript
// 注册用户
async function registerUser(userData) {
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });
        
        if (response.ok) {
            const data = await response.json();
            // 保存令牌
            localStorage.setItem('access_token', data.token.access_token);
            return data;
        } else {
            const error = await response.json();
            throw new Error(error.detail);
        }
    } catch (error) {
        console.error('注册失败:', error.message);
        throw error;
    }
}
```

#### 登录流程
```javascript
// 用户登录
async function loginUser(credentials) {
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(credentials)
        });
        
        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.token.access_token);
            return data;
        } else {
            const error = await response.json();
            throw new Error(error.detail);
        }
    } catch (error) {
        console.error('登录失败:', error.message);
        throw error;
    }
}
```

### 个人中心页面

#### 获取用户资料
```javascript
// 获取用户资料
async function getUserProfile() {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            throw new Error('获取用户资料失败');
        }
    } catch (error) {
        console.error('获取资料失败:', error.message);
        throw error;
    }
}
```

#### 更新用户资料
```javascript
// 更新用户资料
async function updateUserProfile(profileData) {
    const token = localStorage.getItem('access_token');
    
    try {
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(profileData)
        });
        
        if (response.ok) {
            return await response.json();
        } else {
            const error = await response.json();
            throw new Error(error.detail);
        }
    } catch (error) {
        console.error('更新资料失败:', error.message);
        throw error;
    }
}
```

#### 令牌管理
```javascript
// 检查令牌是否存在
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

// 登出
function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
}

// 添加请求拦截器自动添加认证头
function setupAuthInterceptor() {
    // 原生 fetch 包装
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        const token = localStorage.getItem('access_token');
        if (token && args[1]) {
            args[1].headers = {
                ...args[1].headers,
                'Authorization': `Bearer ${token}`
            };
        }
        return originalFetch.apply(this, args);
    };
}
```

## 数据验证规则

### 用户名验证
- **长度**: 3-50 个字符
- **格式**: 只能包含字母、数字、下划线和连字符
- **唯一性**: 系统内唯一

### 邮箱验证
- **格式**: 符合标准邮箱格式
- **唯一性**: 系统内唯一
- **更新限制**: 不能使用其他用户已占用的邮箱

### 密码验证
- **长度**: 最少 8 个字符
- **复杂度要求**:
  - 至少包含一个字母 (a-z, A-Z)
  - 至少包含一个数字 (0-9)
  - 至少包含一个特殊字符 (!@#$%^&*(),.?":{}|<>)
- **确认**: 注册时需要确认密码一致

### 全名验证
- **长度**: 最大 100 个字符
- **可选性**: 可以为空或不提供
- **更新**: 支持更新，不能为空字符串

## 错误处理

### 常见错误码

| HTTP状态码 | 错误类型 | 描述 |
|------------|----------|------|
| 400 | Bad Request | 请求数据无效或业务逻辑错误 |
| 401 | Unauthorized | 认证失败或令牌无效 |
| 403 | Forbidden | 权限不足，缺少认证信息 |
| 404 | Not Found | 资源不存在 |
| 422 | Unprocessable Entity | 数据验证失败 |
| 500 | Internal Server Error | 服务器内部错误 |

### 错误响应格式
```json
{
    "detail": "具体错误描述信息"
}
```

### 前端错误处理建议
```javascript
// 统一错误处理函数
function handleApiError(error, response) {
    switch (response.status) {
        case 400:
            showErrorMessage(error.detail);
            break;
        case 401:
            showErrorMessage('登录已过期，请重新登录');
            logout();
            break;
        case 403:
            showErrorMessage('权限不足，请先登录');
            break;
        case 422:
            showValidationErrors(error.detail);
            break;
        case 500:
            showErrorMessage('服务器错误，请稍后重试');
            break;
        default:
            showErrorMessage('未知错误，请联系管理员');
    }
}
```

## 安全考虑

### JWT 令牌安全
- **过期时间**: 默认 30 分钟
- **存储**: 建议存储在 localStorage 或 sessionStorage
- **传输**: 使用 HTTPS 传输
- **刷新**: 令牌过期需要重新登录

### 密码安全
- **哈希算法**: bcrypt
- **强度要求**: 字母+数字+特殊字符
- **存储**: 只存储哈希值，不存储明文

### 防护机制
- **SQL注入**: 使用 SQLAlchemy ORM 参数化查询
- **CORS**: 配置允许的源域名
- **输入验证**: Pydantic 严格验证所有输入
- **错误信息**: 避免泄露敏感信息

## 测试覆盖

### 测试类型
- **单元测试**: 业务逻辑和工具函数
- **集成测试**: API 接口端到端测试
- **数据模型测试**: 数据验证和模型创建
- **安全测试**: 认证和权限控制

### 测试覆盖范围
- ✅ 用户注册成功/失败场景
- ✅ 用户登录成功/失败场景
- ✅ 用户资料获取/更新
- ✅ JWT 令牌验证
- ✅ 密码哈希和验证
- ✅ 数据验证规则
- ✅ 错误处理机制

### 运行测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_auth.py -v

# 生成覆盖率报告
pytest tests/ --cov=app --cov-report=html
```

## 部署配置

### 环境变量
```env
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
DATABASE_NAME=curio_cloud

# JWT配置
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
APP_NAME=CurioCloudBackend
APP_VERSION=1.0.0
DEBUG=False
```

### 生产环境建议
1. **使用强密码和安全的 JWT 密钥**
2. **启用 HTTPS**
3. **配置防火墙规则**
4. **使用环境变量管理敏感信息**
5. **定期备份数据库**
6. **监控日志和性能指标**
7. **隐藏 API 文档** (设置 `DEBUG=False`)

## 故障排除

### 常见问题

#### 1. 数据库连接失败
- 检查 MySQL 服务是否运行
- 验证 `.env` 文件中的数据库配置
- 确保数据库存在且用户有权限

#### 2. JWT 令牌错误
- 检查 `JWT_SECRET_KEY` 配置
- 验证令牌是否过期
- 确认令牌格式正确

#### 3. 依赖安装失败
- 使用虚拟环境
- 更新 pip 版本
- 检查 Python 版本兼容性

#### 4. 密码验证失败
- 确认密码符合强度要求
- 检查字符编码问题
- 验证 bcrypt 库正常工作

### 调试工具
- **API 文档**: http://localhost:8000/docs
- **数据库日志**: 开启 SQLAlchemy 日志
- **应用日志**: 查看 uvicorn 输出
- **测试工具**: 使用 pytest 进行测试

## 总结

CurioCloud Backend 用户认证模块提供了完整、安全、易用的用户管理功能。通过清晰的 API 设计、严格的数据验证、完善的错误处理和全面的测试覆盖，确保系统的稳定性和安全性。

前端开发者可以轻松集成这些 API 来构建登录注册页面和个人中心功能，同时享受到 JWT 令牌认证带来的安全保障。