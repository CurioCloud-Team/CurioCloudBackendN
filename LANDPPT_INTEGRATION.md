# CurioCloud Backend - LandPPT 集成说明

## 概述

CurioCloud Backend 现在支持将教案自动转换为PPT课件，通过集成 LandPPT AI驱动的PPT生成平台。

## 功能特性

- **自动转换**: 将教案数据转换为适合PPT生成的格式
- **智能场景识别**: 根据学科自动选择合适的PPT模板场景
- **实时状态查询**: 跟踪PPT生成进度
- **多格式导出**: 支持PDF和PPTX格式导出
- **内容预览**: 获取生成的幻灯片内容

## API端点

### 1. 生成PPT
```
POST /api/teaching/lesson-plans/{plan_id}/generate-ppt
```

从指定的教案生成PPT课件。

**参数:**
- `plan_id` (路径参数): 教案ID

**响应:**
```json
{
  "success": true,
  "ppt_project_id": "ppt_123_abc12345",
  "ppt_title": "语文 - 小学语文古诗教学",
  "ppt_scenario": "education",
  "message": "PPT项目创建成功，正在后台生成PPT内容"
}
```

### 2. 查询PPT状态
```
GET /api/teaching/ppt/{ppt_project_id}/status
```

查询PPT生成状态和进度。

**响应:**
```json
{
  "ppt_project_id": "ppt_123_abc12345",
  "status": {
    "project_id": "ppt_123_abc12345",
    "title": "语文 - 小学语文古诗教学",
    "status": "in_progress",
    "progress": 60.0,
    "slides_count": 8,
    "created_at": 1638360000.0,
    "updated_at": 1638360300.0
  }
}
```

### 3. 获取幻灯片内容
```
GET /api/teaching/ppt/{ppt_project_id}/slides
```

获取生成的PPT幻灯片内容。

**响应:**
```json
{
  "project_id": "ppt_123_abc12345",
  "title": "语文 - 小学语文古诗教学",
  "slides_html": "<html>...</html>",
  "slides_data": [...],
  "slides_count": 10
}
```

### 4. 导出PPT文件
```
GET /api/teaching/ppt/{ppt_project_id}/export/{format}
```

导出PPT为文件格式。

**参数:**
- `ppt_project_id`: PPT项目ID
- `format`: 导出格式 (`pdf` 或 `pptx`)

**响应:** 文件下载

## 配置说明

在 `.env` 文件中配置以下环境变量：

```env
# LandPPT集成配置
LANDPPT_BASE_URL=http://localhost:8001
LANDPPT_API_KEY=your_landppt_service_api_key_here
LANDPPT_DEFAULT_SCENARIO=education
```

## 使用流程

1. **创建教案**: 使用现有的教学对话API创建教案
2. **生成PPT**: 调用PPT生成API，将教案ID作为参数
3. **监控进度**: 定期查询PPT生成状态
4. **获取结果**: 当生成完成后，获取幻灯片内容或导出文件

## 场景映射

系统根据教案的学科自动选择合适的PPT场景：

- **语文/英语**: `education`
- **数学**: `analysis`
- **物理/化学/生物**: `technology` / `analysis`
- **历史/地理**: `history` / `tourism`
- **其他**: `education` (默认)

## 错误处理

- **401/403**: 认证失败，检查API密钥配置
- **404**: 教案不存在或PPT项目不存在
- **500**: 服务内部错误，检查LandPPT服务状态
- **503**: LandPPT服务不可用

## 测试

运行集成测试：

```bash
python test_landppt_integration.py
```

## 注意事项

1. 确保LandPPT服务正在运行且可访问
2. PPT生成是异步过程，可能需要几分钟时间
3. 生成过程中可以通过状态查询API监控进度
4. 建议在生成完成后立即导出文件，避免服务重启导致数据丢失