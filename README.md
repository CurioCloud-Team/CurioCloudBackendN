# CurioCloud Backend

基于FastAPI的用户认证系统，支持用户注册和登录功能。

## 项目概述
课研云 CurioCloud 旨在打造一款AI驱动的教师备课辅助系统，通过集成先进的人工智能技术，解决传统备课方式效率低、创新性不足的痛点。项目旨在实现教学设计的自动化、教学资源的智能化生成与个性化推荐、以及深度的学情分析，从而革命性地提升教师的备课效率与教学质量。

## 功能特性

- ✅ 用户注册与登录
- ✅ 用户资料管理（获取/更新）
- ✅ JWT令牌认证
- ✅ 密码安全加密
- ✅ 数据验证和错误处理
- ✅ MySQL数据库集成
- ✅ RESTful API设计
- ✅ 完整的文档和注释
- ✅ 完善的测试套件

## 技术栈

- **框架**: FastAPI 0.104.1
- **数据库**: MySQL + SQLAlchemy
- **认证**: JWT + Passlib (bcrypt)
- **数据验证**: Pydantic
- **服务器**: Uvicorn

## 项目结构

```
CurioCloudBackendN/
├── app/                    # 应用程序包
│   ├── core/              # 核心配置
│   │   ├── config.py      # 应用配置
│   │   └── database.py    # 数据库连接
│   ├── dependencies/      # 依赖注入
│   │   └── auth.py        # 认证依赖
│   ├── models/            # 数据库模型
│   │   └── user.py        # 用户模型
│   ├── schemas/           # 数据验证模式
│   │   └── user.py        # 用户相关schema
│   ├── services/          # 业务逻辑
│   │   └── auth_service.py # 认证服务
│   ├── routers/           # API路由
│   │   ├── auth.py        # 认证路由
│   │   └── user.py        # 用户管理路由
│   └── utils/             # 工具函数
│       ├── security.py    # 密码工具
│       └── jwt.py         # JWT工具
├── tests/                 # 测试套件
│   ├── conftest.py        # 测试配置
│   ├── test_auth.py       # 认证API测试
│   ├── test_models.py     # 数据模型测试
│   ├── test_services.py   # 业务逻辑测试
│   └── test_user_profile.py # 用户资料测试
├── main.py                # 应用入口
├── requirements.txt       # 依赖包
└── .env                   # 环境变量
```

## 快速开始

### 1. 环境配置

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 文件，设置数据库连接信息
```

### 2. 数据库设置

确保MySQL服务正在运行，并创建数据库：

```sql
CREATE DATABASE curio_cloud;
```

### 3. 配置 .env 文件

```env
# 数据库配置
DATABASE_HOST=localhost
DATABASE_PORT=3306
DATABASE_USER=your_username
DATABASE_PASSWORD=your_password
DATABASE_NAME=curio_cloud

# JWT配置
JWT_SECRET_KEY=your_super_secret_jwt_key_here_change_this_in_production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 4. 启动应用

```bash
# 开发模式
python main.py

# 或使用uvicorn
uvicorn main:app --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. 访问文档

启动后访问：
- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc

## API接口

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

**响应示例:**
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

### 用户登录

```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "testuser",  // 支持用户名或邮箱
    "password": "Test123!@#"
}
```

**响应示例:**
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

### 获取用户资料

```http
GET /api/user/profile
Authorization: Bearer {access_token}
```

**响应示例:**
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
    "full_name": "更新后的用户名",  // 可选
    "email": "new@example.com"     // 可选
}
```

**响应示例:**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "new@example.com",
    "full_name": "更新后的用户名",
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

**响应示例:**
```json
{
    "message": "用户 testuser: 账户已激活, 邮箱未验证",
    "success": true
}
```

## 密码要求

- 最少8个字符
- 至少包含一个字母
- 至少包含一个数字
- 至少包含一个特殊字符

## 安全特性

1. **密码加密**: 使用bcrypt进行密码哈希
2. **JWT认证**: 安全的令牌认证机制
3. **数据验证**: 严格的输入数据验证
4. **SQL注入防护**: 使用SQLAlchemy ORM
5. **CORS保护**: 配置跨域资源共享策略

## 数据库表结构

### users 表

| 字段 | 类型 | 约束 | 描述 |
|------|------|------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | 用户ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| email | VARCHAR(100) | UNIQUE, NOT NULL | 邮箱 |
| full_name | VARCHAR(100) | NULL | 全名 |
| hashed_password | VARCHAR(255) | NOT NULL | 加密密码 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |
| is_verified | BOOLEAN | DEFAULT FALSE | 是否验证 |
| created_at | DATETIME | DEFAULT NOW() | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW() ON UPDATE NOW() | 更新时间 |

## 开发指南

### 添加新的API路由

1. 在 `app/routers/` 中创建新的路由文件
2. 在 `main.py` 中注册路由
3. 创建对应的service和schema

### 数据库迁移

```bash
# 生成迁移文件
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

### 运行测试

```bash
pytest
```

## 部署建议

1. 使用强密码和安全的JWT密钥
2. 启用HTTPS
3. 配置防火墙
4. 使用环境变量管理敏感信息
5. 定期备份数据库
6. 监控日志和性能

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否运行
   - 验证.env文件中的数据库配置
   - 确保数据库存在

2. **JWT令牌错误**
   - 检查JWT_SECRET_KEY配置
   - 验证令牌是否过期

3. **依赖安装失败**
   - 使用虚拟环境
   - 更新pip版本

