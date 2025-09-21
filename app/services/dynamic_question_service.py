"""
动态问题生成服务

基于AI的智能问题生成系统，支持动态问题序列和多选项生成
"""
import json
from typing import Dict, Any, Optional, List
from app.services.ai_service import AIService


class DynamicQuestionService:
    """动态问题生成服务类"""

    def __init__(self):
        self.ai_service = AIService()
        
    async def generate_next_question(self, 
                                   collected_data: Dict[str, Any], 
                                   question_count: int,
                                   max_questions: int = 5) -> Optional[Dict[str, Any]]:
        """
        基于已收集的数据生成下一个问题
        
        Args:
            collected_data: 已收集的用户数据
            question_count: 当前问题数量
            max_questions: 最大问题数量
            
        Returns:
            生成的问题卡片，如果应该结束则返回None
        """
        if question_count >= max_questions:
            return None
            
        prompt = self._build_question_generation_prompt(collected_data, question_count, max_questions)
        
        payload = {
            "model": self.ai_service.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": 1000
        }
        
        result = await self.ai_service.generate_json_response(payload)
        if result:
            content = result["choices"][0]["message"]["content"]
            question_data = self.ai_service.clean_and_parse_json(content)
            if question_data and self._validate_question_format(question_data):
                # 添加step_key字段
                question_data["step_key"] = f"dynamic_question_{question_count + 1}"
                return question_data
        
        return None
    
    def _build_question_generation_prompt(self, 
                                        collected_data: Dict[str, Any], 
                                        question_count: int,
                                        max_questions: int) -> str:
        """
        构建问题生成的AI提示词
        
        Args:
            collected_data: 已收集的数据
            question_count: 当前问题数量
            max_questions: 最大问题数量
            
        Returns:
            完整的提示词字符串
        """
        # 分析已有数据
        data_summary = self._analyze_collected_data(collected_data)
        remaining_questions = max_questions - question_count
        
        return f"""你是一位专业的教学设计顾问。基于用户已提供的信息，请生成下一个最合适的问题来收集教案设计所需的关键信息。

# 已收集的信息
{data_summary}

# 当前状态
- 这是第 {question_count + 1} 个问题
- 还剩 {remaining_questions} 个问题可以询问
- 需要确保收集到足够的信息来生成高质量的教案

# 任务要求
请生成一个问题，必须严格遵循以下JSON格式，不要添加任何解释性文字：

{{
  "question": "（生成一个具体、有针对性的问题，帮助深入了解教学需求）",
  "question_type": "（问题类型：basic_info/teaching_method/student_analysis/content_depth/assessment_method）",
  "key_to_save": "（用于保存答案的键名，使用英文下划线格式）",
  "options": [
    "（选项1 - 提供4-6个具体的选择项）",
    "（选项2）",
    "（选项3）",
    "（选项4）",
    "（选项5）",
    "（选项6）"
  ],
  "allows_free_text": true,
  "priority": "（问题优先级：high/medium/low）",
  "reasoning": "（为什么在当前阶段问这个问题的简短说明）"
}}

# 问题生成策略
1. 如果是前1-2个问题，重点收集基础信息（学科、年级、主题等）
2. 如果是中间问题，深入了解教学方法、学生特点、内容深度
3. 如果是最后1-2个问题，关注评估方式、特殊需求等
4. 选项应该涵盖常见情况，但允许用户自定义输入
5. 问题应该循序渐进，基于已有信息提出更精准的询问
"""

    def _analyze_collected_data(self, collected_data: Dict[str, Any]) -> str:
        """
        分析已收集的数据，生成摘要
        
        Args:
            collected_data: 已收集的数据
            
        Returns:
            数据摘要字符串
        """
        if not collected_data:
            return "暂无已收集的信息"
        
        summary_parts = []
        for key, value in collected_data.items():
            if value:
                summary_parts.append(f"- {key}: {value}")
        
        return "\n".join(summary_parts) if summary_parts else "暂无已收集的信息"
    
    def _validate_question_format(self, question_data: Dict[str, Any]) -> bool:
        """
        验证问题格式是否正确
        
        Args:
            question_data: 问题数据
            
        Returns:
            是否格式正确
        """
        required_keys = ["question", "question_type", "key_to_save", "options", "allows_free_text"]
        
        for key in required_keys:
            if key not in question_data:
                return False
        
        # 验证选项数量
        options = question_data.get("options", [])
        if not isinstance(options, list) or len(options) < 4 or len(options) > 6:
            return False
        
        return True
    
    def should_continue_questioning(self, 
                                        collected_data: Dict[str, Any], 
                                        question_count: int,
                                        min_questions: int = 3,
                                        max_questions: int = 5) -> Dict[str, Any]:
        """
        判断是否应该继续提问
        
        Args:
            collected_data: 已收集的数据
            question_count: 当前问题数量
            min_questions: 最少问题数量
            max_questions: 最多问题数量
            
        Returns:
            包含决策信息的字典
        """
        # 强制最小问题数
        if question_count < min_questions:
            return {
                "should_continue": True,
                "reason": "未达到最少问题数量",
                "confidence": 1.0
            }
        
        # 强制最大问题数
        if question_count >= max_questions:
            return {
                "should_continue": False,
                "reason": "已达到最大问题数量",
                "confidence": 1.0
            }
        
        # 基于数据完整性判断
        completeness_score = self._calculate_data_completeness(collected_data)
        
        if completeness_score >= 0.8:
            return {
                "should_continue": False,
                "reason": "数据收集已较为完整",
                "confidence": completeness_score
            }
        elif completeness_score >= 0.6:
            return {
                "should_continue": True,
                "reason": "数据收集基本完整，可再询问1-2个问题",
                "confidence": completeness_score
            }
        else:
            return {
                "should_continue": True,
                "reason": "数据收集不够完整，需要继续询问",
                "confidence": completeness_score
            }
    
    def _calculate_data_completeness(self, collected_data: Dict[str, Any]) -> float:
        """
        计算数据完整性得分
        
        Args:
            collected_data: 已收集的数据
            
        Returns:
            完整性得分 (0.0-1.0)
        """
        # 定义关键信息权重
        key_weights = {
            "subject": 0.2,      # 学科
            "grade": 0.2,        # 年级
            "topic": 0.2,        # 主题
            "duration_minutes": 0.1,  # 时长
            "teaching_method": 0.1,   # 教学方法
            "student_level": 0.1,     # 学生水平
            "learning_objectives": 0.1  # 学习目标
        }
        
        total_score = 0.0
        for key, weight in key_weights.items():
            if key in collected_data and collected_data[key]:
                total_score += weight
        
        return min(total_score, 1.0)