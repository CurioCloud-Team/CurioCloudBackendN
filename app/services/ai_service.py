"""
AI服务模块

提供与OpenRouter API的集成，用于生成教学计划
"""
import json
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings


class AIService:
    """AI服务类，负责与OpenRouter API交互"""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.default_model = settings.openrouter_default_model
        self.max_retries = settings.llm_max_retries
        self.timeout = settings.llm_timeout_seconds

    async def generate_lesson_plan(self, lesson_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        生成教学计划

        Args:
            lesson_data: 包含课程信息的字典
                {
                    "subject": "生物",
                    "grade": "初中二年级",
                    "topic": "光合作用",
                    "duration_minutes": 45
                }

        Returns:
            生成的教学计划字典，如果失败返回None
        """
        prompt = self._build_prompt(lesson_data)

        payload = {
            "model": self.default_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://curio-cloud-backend.com",
            "X-Title": "CurioCloud Teaching Assistant"
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        json=payload,
                        headers=headers
                    )

                    if response.status_code == 200:
                        result = response.json()
                        content = result["choices"][0]["message"]["content"]

                        # 尝试解析JSON响应
                        try:
                            # 清理响应内容，移除可能的markdown代码块标记
                            content = content.strip()
                            if content.startswith('```json'):
                                content = content[7:]  # 移除 ```json
                            if content.startswith('```'):
                                content = content[3:]  # 移除 ```
                            if content.endswith('```'):
                                content = content[:-3]  # 移除结尾的 ```
                            content = content.strip()  # 再次清理空白字符

                            lesson_plan = json.loads(content)
                            return self._validate_lesson_plan(lesson_plan)
                        except json.JSONDecodeError as e:
                            print(f"JSON解析失败: {e}")
                            print(f"清理后的AI响应内容: {content[:200]}...")
                            continue
                    else:
                        print(f"API请求失败 (尝试 {attempt + 1}/{self.max_retries}): {response.status_code}")
                        print(f"响应内容: {response.text}")
                        continue

            except Exception as e:
                print(f"AI服务请求异常 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                continue

        return None

    def _build_prompt(self, lesson_data: Dict[str, Any]) -> str:
        """
        构建AI提示词

        Args:
            lesson_data: 课程数据

        Returns:
            完整的提示词字符串
        """
        subject = lesson_data.get("subject", "")
        grade = lesson_data.get("grade", "")
        topic = lesson_data.get("topic", "")
        duration = lesson_data.get("duration_minutes", 45)

        prompt = f"""你是一位经验丰富的{grade}{subject}教学设计师。请根据以下要求，为一堂{duration}分钟的课程设计一个完整的教学方案。

# 课程基本信息
- 学科: {subject}
- 年级: {grade}
- 课题: {topic}

# 任务要求
请生成一个结构化的教学计划，必须严格遵循以下的 JSON 格式。不要在 JSON 之外添加任何解释性文字。

{{
  "title": "（请为这堂课生成一个生动有趣的标题）",
  "learning_objectives": [
    "（请生成3-4条具体的学习目标，例如：学生能够描述光合作用的概念和过程）",
    "（目标二）",
    "（目标三）"
  ],
  "teaching_outline": "（请在这里生成一段100-200字的教学大纲或课程简介）",
  "activities": [
    {{
      "order": 1,
      "name": "（第一个活动的名称，例如：课堂导入：植物如何"吃饭"？）",
      "description": "（对第一个活动的详细描述，包括具体做什么）",
      "duration": 5
    }},
    {{
      "order": 2,
      "name": "（第二个活动的名称）",
      "description": "（对第二个活动的详细描述）",
      "duration": 20
    }},
    {{
      "order": 3,
      "name": "（第三个活动的名称）",
      "description": "（对第三个活动的详细描述）",
      "duration": 15
    }},
    {{
      "order": 4,
      "name": "（第四个活动的名称，例如：课堂总结）",
      "description": "（对第四个活动的详细描述）",
      "duration": 5
    }}
  ]
}}"""

        return prompt

    def _validate_lesson_plan(self, lesson_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证AI生成的教学计划格式

        Args:
            lesson_plan: AI生成的教学计划

        Returns:
            验证后的教学计划，如果格式不正确会抛出异常
        """
        required_keys = ["title", "learning_objectives", "teaching_outline", "activities"]

        for key in required_keys:
            if key not in lesson_plan:
                raise ValueError(f"教学计划缺少必需字段: {key}")

        # 验证activities格式
        if not isinstance(lesson_plan["activities"], list):
            raise ValueError("activities必须是列表格式")

        for i, activity in enumerate(lesson_plan["activities"]):
            required_activity_keys = ["order", "name", "description", "duration"]
            for key in required_activity_keys:
                if key not in activity:
                    raise ValueError(f"活动 {i+1} 缺少字段: {key}")

        return lesson_plan