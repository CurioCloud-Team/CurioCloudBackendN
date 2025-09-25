"""
AI服务模块

提供与OpenRouter API的集成，用于生成教学计划和练习题
"""
import json
import httpx
from typing import Dict, Any, Optional

from app.core.config import settings
from app.prompts.exercise_prompts import get_multiple_choice_prompt, get_fill_in_the_blank_prompt, get_short_answer_prompt


class AIService:
    """AI服务类，负责与OpenRouter API交互"""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.default_model = settings.openrouter_default_model
        self.max_retries = settings.llm_max_retries
        self.timeout = settings.llm_timeout_seconds
        
        # Tavily搜索配置
        self.tavily_api_key = settings.tavily_api_key
        self.tavily_base_url = settings.tavily_base_url
        self.tavily_search_max_results = settings.tavily_search_max_results

    async def _make_api_call(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        向OpenRouter API发出请求并处理通用逻辑
        """
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
                        return response.json()
                    else:
                        print(f"API请求失败 (尝试 {attempt + 1}/{self.max_retries}): {response.status_code}")
                        print(f"响应内容: {response.text}")
                        continue
            except Exception as e:
                print(f"AI服务请求异常 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                continue
        return None

    def _clean_and_parse_json(self, content: str) -> Optional[Any]:
        """
        清理并解析AI返回的JSON字符串
        """
        try:
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            print(f"清理后的AI响应内容: {content[:200]}...")
            return None

    async def search_web(self, query: str, max_results: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        使用Tavily API进行网页搜索

        Args:
            query: 搜索查询
            max_results: 最大结果数量，默认使用配置的值

        Returns:
            搜索结果字典，包含结果列表和元数据
        """
        if max_results is None:
            max_results = self.tavily_search_max_results

        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "include_images": False,
            "include_answer": False,
            "include_raw_content": False,
            "max_results": max_results,
            "include_domains": [],
            "exclude_domains": []
        }

        headers = {
            "Content-Type": "application/json"
        }

        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.tavily_base_url}/search",
                        json=payload,
                        headers=headers
                    )

                    if response.status_code == 200:
                        result = response.json()
                        # 添加搜索结果的元数据
                        if "results" in result:
                            result["search_metadata"] = {
                                "query": query,
                                "total_results": len(result["results"]),
                                "sources": [r.get("url", "") for r in result["results"]]
                            }
                        return result
                    else:
                        print(f"Tavily搜索请求失败 (尝试 {attempt + 1}/{self.max_retries}): {response.status_code}")
                        print(f"响应内容: {response.text}")
                        continue
            except Exception as e:
                print(f"Tavily搜索请求异常 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                continue
        return None

    async def generate_lesson_plan(self, lesson_data: Dict[str, Any], enable_web_search: bool = False) -> Optional[Dict[str, Any]]:
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
            enable_web_search: 是否启用联网搜索

        Returns:
            生成的教学计划字典，如果失败返回None
        """
        # 如果启用联网搜索，先搜索相关信息
        search_results = None
        if enable_web_search:
            search_query = self._build_search_query(lesson_data)
            search_results = await self.search_web(search_query)
        
        prompt = self._build_prompt(lesson_data, search_results)
        payload = {
            "model": self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        result = await self._make_api_call(payload)
        if result:
            content = result["choices"][0]["message"]["content"]
            lesson_plan = self._clean_and_parse_json(content)
            if lesson_plan:
                validated_plan = self._validate_lesson_plan(lesson_plan)
                # 如果有搜索结果，添加到返回的数据中
                if search_results and "search_metadata" in search_results:
                    validated_plan["web_search_info"] = {
                        "used_web_search": True,
                        "search_query": search_results["search_metadata"]["query"],
                        "total_sources": search_results["search_metadata"]["total_results"],
                        "sources": search_results["search_metadata"]["sources"]
                    }
                else:
                    validated_plan["web_search_info"] = {
                        "used_web_search": False,
                        "total_sources": 0,
                        "sources": []
                    }
                return validated_plan
        return None

    async def generate_multiple_choice_questions(self, content: str, num_questions: int, difficulty: str) -> Optional[list[Dict[str, Any]]]:
        """
        生成选择题

        Args:
            content: 教案内容
            num_questions: 题目数量
            difficulty: 题目难度

        Returns:
            生成的选择题列表，如果失败返回None
        """
        prompt = get_multiple_choice_prompt(content, num_questions, difficulty)
        payload = {
            "model": self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        result = await self._make_api_call(payload)
        if result:
            content_str = result["choices"][0]["message"]["content"]
            questions = self._clean_and_parse_json(content_str)
            if isinstance(questions, list):
                return questions
        return None

    async def generate_fill_in_the_blank_questions(self, content: str, num_questions: int, difficulty: str) -> Optional[list[Dict[str, Any]]]:
        """
        生成填空题

        Args:
            content: 教案内容
            num_questions: 题目数量
            difficulty: 题目难度

        Returns:
            生成的填空题列表，如果失败返回None
        """
        prompt = get_fill_in_the_blank_prompt(content, num_questions, difficulty)
        payload = {
            "model": self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        result = await self._make_api_call(payload)
        if result:
            content_str = result["choices"][0]["message"]["content"]
            questions = self._clean_and_parse_json(content_str)
            if isinstance(questions, list):
                return questions
        return None

    async def generate_short_answer_questions(self, content: str, num_questions: int, difficulty: str) -> Optional[list[Dict[str, Any]]]:
        """
        生成简答题

        Args:
            content: 教案内容
            num_questions: 题目数量
            difficulty: 题目难度

        Returns:
            生成的简答题列表，如果失败返回None
        """
        prompt = get_short_answer_prompt(content, num_questions, difficulty)
        payload = {
            "model": self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 2000
        }

        result = await self._make_api_call(payload)
        if result:
            content_str = result["choices"][0]["message"]["content"]
            questions = self._clean_and_parse_json(content_str)
            if isinstance(questions, list):
                return questions
        return None

    def _build_search_query(self, lesson_data: Dict[str, Any]) -> str:
        """
        构建搜索查询

        Args:
            lesson_data: 课程数据

        Returns:
            搜索查询字符串
        """
        subject = self._extract_subject_from_data(lesson_data)
        grade = self._extract_grade_from_data(lesson_data)
        topic = lesson_data.get("topic", "")
        
        # 构建基础搜索查询
        query_parts = []
        if subject:
            query_parts.append(subject)
        if grade:
            query_parts.append(grade)
        if topic:
            query_parts.append(topic)
        
        # 添加教学相关的关键词
        query_parts.extend(["教学设计", "教学方法", "教学活动", "教学资源"])
        
        return " ".join(query_parts)

    def _build_prompt(self, lesson_data: Dict[str, Any], search_results: Optional[Dict[str, Any]] = None) -> str:
        """
        构建AI提示词

        Args:
            lesson_data: 课程数据
            search_results: 联网搜索结果

        Returns:
            完整的提示词字符串
        """
        # 提取基础信息，支持从动态数据中智能提取
        subject = self._extract_subject_from_data(lesson_data)
        grade = self._extract_grade_from_data(lesson_data)
        topic = lesson_data.get("topic", "")
        duration = lesson_data.get("duration_minutes", 45)
        
        # 分析动态收集的数据
        dynamic_info = self._extract_dynamic_info(lesson_data)
        
        # 处理搜索结果
        search_info = ""
        if search_results and "results" in search_results:
            search_info = "\n\n# 联网搜索结果参考\n"
            search_info += f"基于以下 {len(search_results['results'])} 个网页的搜索结果来优化教学设计：\n"
            for i, result in enumerate(search_results["results"][:3], 1):  # 只显示前3个结果
                title = result.get("title", "无标题")
                url = result.get("url", "")
                content = result.get("content", "")[:200] + "..." if len(result.get("content", "")) > 200 else result.get("content", "")
                search_info += f"{i}. {title}\n   链接: {url}\n   内容摘要: {content}\n\n"
        
        # 构建增强的提示词
        base_prompt = f"""你是一位经验丰富的{grade}{subject}教学设计师。请根据以下要求，为一堂{duration}分钟的课程设计一个完整的教学方案。

# 课程基本信息
- 学科: {subject}
- 年级: {grade}
- 课题: {topic}
- 课程时长: {duration}分钟

# 收集到的详细信息
{dynamic_info}{search_info}

# 任务要求
请生成一个结构化的教学计划，必须严格遵循以下的 JSON 格式。不要在 JSON 之外添加任何解释性文字。

{{
  "title": "（请为这堂课生成一个生动有趣的标题）",
  "learning_objectives": [
    "（请生成3-4条具体的学习目标，结合收集到的信息制定）",
    "（目标二）",
    "（目标三）"
  ],
  "teaching_outline": "（请在这里生成一段150-250字的教学大纲或课程简介，体现个性化需求）",
  "activities": [
    {{
      "order": 1,
      "name": "（第一个活动的名称，例如：课堂导入）",
      "description": "（对第一个活动的详细描述，包括具体做什么，考虑学生特点和教学方法）",
      "duration": 5
    }},
    {{
      "order": 2,
      "name": "（第二个活动的名称）",
      "description": "（对第二个活动的详细描述，体现教学重点）",
      "duration": 20
    }},
    {{
      "order": 3,
      "name": "（第三个活动的名称）",
      "description": "（对第三个活动的详细描述，注重互动和实践）",
      "duration": 15
    }},
    {{
      "order": 4,
      "name": "（第四个活动的名称，例如：课堂总结与评估）",
      "description": "（对第四个活动的详细描述，包含评估方式）",
      "duration": 5
    }}
  ]
}}

# 设计原则
1. 确保活动时间总和等于课程总时长
2. 根据收集到的学生特点和教学需求调整活动设计
3. 体现教学方法的多样性和针对性
4. 确保学习目标与活动内容高度匹配
5. 考虑学生的认知水平和兴趣特点
6. 如有联网搜索结果，请参考这些信息来丰富教学内容和方法"""

        return base_prompt
    
    def _extract_dynamic_info(self, lesson_data: Dict[str, Any]) -> str:
        """
        从动态收集的数据中提取有用信息
        
        Args:
            lesson_data: 课程数据
            
        Returns:
            格式化的信息字符串
        """
        info_parts = []
        
        # 处理动态问题的答案
        for key, value in lesson_data.items():
            if key.startswith("question_") and key.endswith("_answer") and value:
                question_num = key.split("_")[1]
                info_parts.append(f"- 问题{question_num}回答: {value}")
        
        # 处理传统字段
        traditional_fields = {
            "teaching_method": "教学方法偏好",
            "student_level": "学生水平",
            "learning_objectives": "学习目标要求",
            "assessment_method": "评估方式",
            "special_requirements": "特殊要求",
            "classroom_environment": "课堂环境",
            "available_resources": "可用资源"
        }
        
        for key, label in traditional_fields.items():
            if key in lesson_data and lesson_data[key]:
                info_parts.append(f"- {label}: {lesson_data[key]}")
        
        return "\n".join(info_parts) if info_parts else "暂无额外信息"

    def _extract_subject_from_data(self, lesson_data: Dict[str, Any]) -> str:
        """
        从课程数据中智能提取学科信息
        
        Args:
            lesson_data: 课程数据
            
        Returns:
            学科名称
        """
        # 首先检查直接的subject字段
        if lesson_data.get("subject"):
            return lesson_data["subject"]
        
        # 从动态问题答案中提取学科信息
        for key, value in lesson_data.items():
            if key.startswith("question_") and key.endswith("_answer") and value:
                # 检查答案中是否包含常见学科关键词
                subject_keywords = {
                    "数学": ["数学", "算术", "代数", "几何", "微积分", "统计"],
                    "语文": ["语文", "中文", "文学", "作文", "阅读", "古诗"],
                    "英语": ["英语", "English", "英文", "单词", "语法", "听力"],
                    "物理": ["物理", "力学", "电学", "光学", "热学", "声学"],
                    "化学": ["化学", "元素", "分子", "化合物", "反应", "实验"],
                    "生物": ["生物", "细胞", "遗传", "进化", "生态", "植物", "动物"],
                    "历史": ["历史", "古代", "近代", "现代", "朝代", "战争", "文明"],
                    "地理": ["地理", "地图", "气候", "地形", "国家", "城市", "河流"],
                    "政治": ["政治", "法律", "宪法", "政府", "公民", "权利"],
                    "音乐": ["音乐", "歌曲", "乐器", "节拍", "音符", "合唱"],
                    "美术": ["美术", "绘画", "素描", "色彩", "艺术", "创作"],
                    "体育": ["体育", "运动", "健身", "球类", "跑步", "游泳"],
                    "信息技术": ["计算机", "编程", "软件", "网络", "信息技术", "IT"]
                }
                
                value_lower = value.lower()
                for subject, keywords in subject_keywords.items():
                    if any(keyword in value_lower for keyword in keywords):
                        return subject
        
        return ""

    def _extract_grade_from_data(self, lesson_data: Dict[str, Any]) -> str:
        """
        从课程数据中智能提取年级信息
        
        Args:
            lesson_data: 课程数据
            
        Returns:
            年级信息
        """
        # 首先检查直接的grade字段
        if lesson_data.get("grade"):
            return lesson_data["grade"]
        
        # 从动态问题答案中提取年级信息
        for key, value in lesson_data.items():
            if key.startswith("question_") and key.endswith("_answer") and value:
                # 检查答案中是否包含年级关键词 - 按照优先级排序，更具体的匹配在前
                grade_patterns = [
                    # 初中 - 具体年级
                    ("初中一年级", "初中一年级"), ("初中二年级", "初中二年级"), ("初中三年级", "初中三年级"),
                    ("初一", "初中一年级"), ("初二", "初中二年级"), ("初三", "初中三年级"),
                    ("七年级", "初中一年级"), ("八年级", "初中二年级"), ("九年级", "初中三年级"),
                    # 高中 - 具体年级
                    ("高中一年级", "高中一年级"), ("高中二年级", "高中二年级"), ("高中三年级", "高中三年级"),
                    ("高一", "高中一年级"), ("高二", "高中二年级"), ("高三", "高中三年级"),
                    # 小学 - 具体年级
                    ("小学一年级", "小学一年级"), ("小学二年级", "小学二年级"), ("小学三年级", "小学三年级"),
                    ("小学四年级", "小学四年级"), ("小学五年级", "小学五年级"), ("小学六年级", "小学六年级"),
                    # 大学 - 具体年级
                    ("大学一年级", "大学一年级"), ("大学二年级", "大学二年级"), ("大学三年级", "大学三年级"), ("大学四年级", "大学四年级"),
                    ("大一", "大学一年级"), ("大二", "大学二年级"), ("大三", "大学三年级"), ("大四", "大学四年级"),
                    # 通用年级（只有在没有学段前缀时才匹配）
                    ("一年级", "小学一年级"), ("二年级", "小学二年级"), ("三年级", "小学三年级"),
                    ("四年级", "小学四年级"), ("五年级", "小学五年级"), ("六年级", "小学六年级"),
                    # 学段（最后匹配）
                    ("初中", "初中"), ("高中", "高中"), ("小学", "小学"), ("大学", "大学"),
                    # 幼儿园
                    ("幼儿园", "幼儿园"), ("学前班", "学前班")
                ]
                
                value_lower = value.lower()
                for pattern, grade in grade_patterns:
                    if pattern in value_lower:
                        return grade
        
        return ""

    async def generate_text(
        self,
        prompt: str,
        use_gemini: bool = False,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        is_json_output: bool = True
    ) -> Optional[str]:
        """
        通用的文本生成方法

        Args:
            prompt: 发送给AI的提示
            use_gemini: 是否强制使用Gemini模型
            model: 指定要使用的模型，如果为None则使用默认模型
            temperature: 控制生成文本的随机性
            max_tokens: 生成文本的最大长度
            is_json_output: AI是否应该返回JSON格式的字符串

        Returns:
            AI生成的文本内容字符串，如果失败则返回None
        """
        if model is None:
            model = "google/gemini-pro-1.5" if use_gemini else self.default_model

        messages = [{"role": "user", "content": prompt}]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if is_json_output:
            payload["response_format"] = {"type": "json_object"}

        response_data = await self._make_api_call(payload)

        if response_data and response_data.get("choices"):
            content = response_data["choices"][0]["message"]["content"]
            return content
        
        return None

    async def generate_lesson_plan_from_scratch(
        self,
        subject: str,
        grade: str,
        topic: str,
        duration_minutes: int,
        teaching_method: str = "传统教学",
        student_level: str = "中等",
        special_requirements: str = "",
        enable_web_search: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        从零开始生成教学计划

        Args:
            subject: 学科
            grade: 年级
            topic: 课题
            duration_minutes: 课程时长（分钟）
            teaching_method: 教学方法偏好
            student_level: 学生水平
            special_requirements: 特殊要求
            enable_web_search: 是否启用联网搜索

        Returns:
            生成的教学计划字典，如果失败返回None
        """
        lesson_data = {
            "subject": subject,
            "grade": grade,
            "topic": topic,
            "duration_minutes": duration_minutes,
            "teaching_method": teaching_method,
            "student_level": student_level,
            "special_requirements": special_requirements
        }

        return await self.generate_lesson_plan(lesson_data, enable_web_search)


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

        if not isinstance(lesson_plan["activities"], list):
            raise ValueError("activities必须是列表格式")

        for i, activity in enumerate(lesson_plan["activities"]):
            required_activity_keys = ["order", "name", "description", "duration"]
            for key in required_activity_keys:
                if key not in activity:
                    raise ValueError(f"活动 {i+1} 缺少字段: {key}")

        return lesson_plan

    async def identify_subject(self, user_input: str) -> str:
        """
        使用AI智能识别用户输入的学科
        
        Args:
            user_input: 用户输入的文本
            
        Returns:
            识别出的学科名称
        """
        prompt = f"""
请分析用户输入的内容，智能识别其中的学科信息。

用户输入："{user_input}"

请根据以下规则进行识别：
1. 如果是编程语言（如Go、Rust、Python、Java、C++等），直接返回该编程语言名称
2. 如果是传统学科（如数学、语文、英语、物理、化学等），返回对应的学科名称
3. 如果是复合描述（如"Rust程序设计语言"、"Go语言编程"），提取核心的编程语言名称
4. 如果是专业课程（如"数据结构与算法"、"计算机网络"、"操作系统"等），返回具体的课程名称
5. 如果无法明确识别，返回最接近的学科分类

请直接返回学科名称，不要包含任何解释或额外文字。

示例：
- 输入"go语言" → 输出"Go"
- 输入"Rust程序设计语言" → 输出"Rust"
- 输入"Python编程基础" → 输出"Python"
- 输入"数据结构与算法" → 输出"数据结构与算法"
- 输入"高等数学" → 输出"数学"
- 输入"英语口语" → 输出"英语"
"""

        payload = {
            "model": self.default_model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,  # 使用较低的温度以获得更一致的结果
            "max_tokens": 50
        }

        try:
            response = await self._make_api_call(payload)
            if response and 'choices' in response and len(response['choices']) > 0:
                subject = response['choices'][0]['message']['content'].strip()
                # 清理可能的引号和多余字符
                subject = subject.strip('"\'').strip()
                return subject if subject else user_input
            else:
                print(f"AI学科识别失败，使用原始输入: {user_input}")
                return user_input
        except Exception as e:
            print(f"AI学科识别出错: {e}")
            return user_input