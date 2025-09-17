# 测试文档

## 测试组织结构

本项目采用 pytest 测试框架，遵循标准的 Python 测试最佳实践：

### 目录结构

```
tests/
├── __init__.py          # 测试包标识
├── conftest.py          # pytest配置和共享fixtures
├── test_auth.py         # API接口集成测试
├── test_models.py       # 数据模型和Schema验证测试
└── test_services.py     # 业务逻辑单元测试
```

### 测试分类

#### 1. API集成测试 (`test_auth.py`)
- **健康检查测试**: 验证应用和认证路由的基本可用性
- **用户注册测试**: 
  - 成功注册场景
  - 重复用户名/邮箱处理
  - 弱密码验证
  - 密码不匹配验证
  - 无效邮箱格式验证
- **用户登录测试**:
  - 用户名登录成功
  - 邮箱登录成功
  - 错误密码处理
  - 不存在用户处理
- **根端点测试**: 验证API根路径响应

#### 2. 数据模型测试 (`test_models.py`)
- **用户Schema验证测试**:
  - 有效用户创建数据验证
  - 无效用户名长度验证
  - 无效邮箱格式验证
  - 弱密码强度验证
  - 密码确认匹配验证
  - 登录数据验证
  - 用户响应数据验证
- **用户模型测试**:
  - 用户实例创建
  - 字符串表示方法

#### 3. 业务逻辑单元测试 (`test_services.py`)
- **认证服务测试**:
  - 用户注册成功场景
  - 重复用户名处理
  - 重复邮箱处理
- **密码安全测试**:
  - 密码哈希和验证
- **JWT令牌测试**:
  - 令牌创建和验证
  - 无效令牌处理

### 测试配置 (`conftest.py`)

#### Fixtures
- `test_client`: FastAPI测试客户端，用于API接口测试
- `test_db`: 测试数据库会话，替换生产数据库
- `sample_user_data`: 测试用户数据
- `user_create_data`: 用户创建数据
- `auth_service`: 认证服务实例
- `mock_db`: 模拟数据库会话

#### 数据库配置
- 使用内存SQLite数据库进行测试
- 每个测试运行前创建表，运行后清理
- 依赖注入覆盖，确保测试隔离

### 运行测试

#### 运行所有测试
```bash
python -m pytest tests/ -v
```

#### 运行特定测试文件
```bash
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_models.py -v
python -m pytest tests/test_services.py -v
```

#### 运行特定测试类或方法
```bash
python -m pytest tests/test_auth.py::TestUserRegistration -v
python -m pytest tests/test_auth.py::TestUserRegistration::test_successful_registration -v
```

#### 生成覆盖率报告
```bash
python -m pytest tests/ --cov=app --cov-report=html
```

### 测试最佳实践

1. **测试隔离**: 每个测试独立运行，不依赖其他测试结果
2. **Mock使用**: 对外部依赖（数据库、第三方服务）进行模拟
3. **数据准备**: 使用fixtures提供测试数据
4. **断言清晰**: 每个测试验证明确的预期结果
5. **错误场景**: 覆盖成功和失败两种场景
6. **文档化**: 每个测试方法都有清晰的文档说明

### 测试覆盖范围

- ✅ API端点功能测试
- ✅ 数据验证测试
- ✅ 业务逻辑测试
- ✅ 错误处理测试
- ✅ 安全功能测试（密码哈希、JWT）
- ✅ 数据库操作测试（通过Mock）

### 已知警告处理

测试过程中会出现一些弃用警告，这些都是依赖库的兼容性问题：
- Pydantic V2迁移警告
- SQLAlchemy 2.0兼容性警告
- datetime.utcnow()弃用警告

这些警告不影响测试功能，可以通过升级依赖版本或调整代码来解决。

### 持续改进

随着项目发展，可以考虑添加：
- 性能测试
- 端到端测试
- 负载测试
- 安全性测试
- 数据库迁移测试