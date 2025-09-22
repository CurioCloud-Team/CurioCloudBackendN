# API 接口快速参考

## 基础信息
- **基础URL**: `http://localhost:8000`
- **API版本**: v1.0
- **认证方式**: Bearer Token (JWT)
- **内容类型**: `application/json`

## 认证接口

### 用户注册
```http
POST /api/auth/register
Content-Type: application/json

{
    "username": "testuser",
    "email": "test@example.com", 
    "password": "Test123!@#",
    "confirm_password": "Test123!@#",
    "full_name": "测试用户"
}
```

**响应**: 201 Created
```json
{
    "user": { /* 用户信息 */ },
    "token": {
        "access_token": "eyJ...",
        "token_type": "bearer",
        "expires_in": 1800
    },
    "message": "注册成功"
}
```

### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "testuser",  // 支持用户名或邮箱
    "password": "Test123!@#"
}
```

**响应**: 200 OK
```json
{
    "user": { /* 用户信息 */ },
    "token": {
        "access_token": "eyJ...",
        "token_type": "bearer", 
        "expires_in": 1800
    },
    "message": "登录成功"
}
```

### 认证服务健康检查
```http
GET /api/auth/health
```

**响应**: 200 OK
```json
{
    "message": "认证服务运行正常",
    "success": true
}
```

## 用户管理接口

### 获取用户资料
```http
GET /api/user/profile
Authorization: Bearer {access_token}
```

**响应**: 200 OK
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

### 更新用户资料
```http
PUT /api/user/profile
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "full_name": "新的用户名",  // 可选
    "email": "new@example.com"  // 可选
}
```

**响应**: 200 OK
```json
{
    "id": 1,
    "username": "testuser",
    "email": "new@example.com",
    "full_name": "新的用户名",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:05:00Z"
}
```

### 获取用户状态
```http
GET /api/user/profile/status
Authorization: Bearer {access_token}
```

**响应**: 200 OK
```json
{
    "message": "用户 testuser: 账户已激活, 邮箱未验证",
    "success": true
}
```

## 系统接口

### 应用健康检查
```http
GET /health
```

**响应**: 200 OK
```json
{
    "status": "healthy",
    "message": "服务运行正常",
    "version": "1.0.0"
}
```

### 根路径
```http
GET /
```

**响应**: 200 OK
```json
{
    "message": "欢迎使用 CurioCloudBackend",
    "version": "1.0.0",
    "docs": "/docs",
    "status": "运行中"
}
```

## 错误响应格式

所有错误响应都遵循统一格式：

```json
{
    "detail": "具体错误描述信息"
}
```

### 常见错误状态码

| 状态码 | 描述 | 示例 |
|--------|------|------|
| 400 | 请求数据错误 | `{"detail": "用户名已存在"}` |
| 401 | 认证失败 | `{"detail": "无法验证用户凭据"}` |
| 403 | 权限不足 | `{"detail": "需要认证"}` |
| 422 | 数据验证失败 | `{"detail": "密码必须包含至少一个字母"}` |
| 500 | 服务器错误 | `{"detail": "服务器内部错误"}` |

## 前端集成示例

### JavaScript/TypeScript

```javascript
// API 基础配置
const API_BASE_URL = 'http://localhost:8000';

// 注册用户
async function register(userData) {
    const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(userData)
    });
    return response.json();
}

// 用户登录
async function login(credentials) {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials)
    });
    return response.json();
}

// 获取用户资料
async function getProfile(token) {
    const response = await fetch(`${API_BASE_URL}/api/user/profile`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    return response.json();
}

// 更新用户资料
async function updateProfile(token, profileData) {
    const response = await fetch(`${API_BASE_URL}/api/user/profile`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
    });
    return response.json();
}
```

### cURL 示例

```bash
# 用户注册
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "Test123!@#",
       "confirm_password": "Test123!@#",
       "full_name": "测试用户"
     }'

# 用户登录
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "password": "Test123!@#"
     }'

# 获取用户资料 (需要替换 {token} 为实际令牌)
curl -X GET "http://localhost:8000/api/user/profile" \
     -H "Authorization: Bearer {token}"

# 更新用户资料
curl -X PUT "http://localhost:8000/api/user/profile" \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer {token}" \
     -d '{
       "full_name": "新的用户名",
       "email": "new@example.com"
     }'
```

## 数据验证规则

### 用户名
- 长度: 3-50 字符
- 格式: 字母、数字、下划线、连字符
- 唯一性: 必须唯一

### 邮箱
- 格式: 标准邮箱格式
- 唯一性: 必须唯一

### 密码
- 长度: 最少 8 字符
- 必须包含: 字母 + 数字

### 全名
- 长度: 最大 100 字符
- 可选字段
- 不能为空字符串

## 令牌管理

### 令牌格式
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 令牌包含信息
- `sub`: 用户名
- `user_id`: 用户ID
- `exp`: 过期时间

### 令牌有效期
- 默认: 30 分钟
- 可配置: 通过环境变量调整

## 开发工具

### API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 测试工具
- HTTP 文件: `test_main.http`
- 用户资料测试: `test_user_profile_api.http`

### 数据库工具
- 查看表结构: 通过 MySQL 客户端
- 测试数据: 通过测试套件创建