import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.models.analytics import AnalysisReport
from app.services.ai_service import AIService
import uuid
import json

import dirtyjson

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    async def _extract_structured_data_with_ai(self, file: UploadFile):
        """
        使用轻量级AI模型将Excel文件内容转换为结构化的JSON数据。
        """
        try:
            # 将Excel文件读为文本（CSV格式），以便AI处理
            df = pd.read_excel(file.file)
            file_content_text = df.to_csv(index=False)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无法读取或转换Excel文件: {e}")

        prompt = f"""
        你是一个数据转换助手。请从以下CSV格式的文本中提取学生成绩信息。
        无论原始列名是什么，请识别出学生的姓名、总分以及每个知识点的得分情况。
        以JSON格式返回一个包含所有学生信息的列表。每个学生是一个对象，必须包含 'name', 'total_score' 和 'knowledge_points' 三个键。
        'knowledge_points' 应该是一个字典，键是知识点名称，值是该知识点的得分。如果无法识别知识点，可以返回空字典。

        文本数据如下:
        ---
        {file_content_text}
        ---

        请严格按照指定的JSON格式输出，不要包含任何额外的解释或标记。
        示例输出:
        [
          {{"name": "张三", "total_score": 85, "knowledge_points": {{"知识点1": 1, "知识点2": 0, "知识点3": 1}}}},
          {{"name": "李四", "total_score": 55, "knowledge_points": {{"知识点1": 0, "知识点2": 1, "知识点3": 0}}}}
        ]
        """
        try:
            # 使用快速、轻量的模型进行结构化提取
            response_str = await self.ai_service.generate_text(prompt, use_gemini=True, model="google/gemini-2.5-flash")
            if not response_str:
                raise HTTPException(status_code=500, detail="AI未能返回任何内容")

            # 使用dirtyjson来解析可能不规范的JSON
            structured_data = dirtyjson.loads(response_str)
            
            # 验证返回的数据结构
            if not isinstance(structured_data, list) or not all('name' in item and 'total_score' in item for item in structured_data):
                raise ValueError("AI返回的数据格式不符合预期")

            return structured_data
        except (dirtyjson.error.Error, ValueError) as e:
            raise HTTPException(status_code=500, detail=f"AI结构化数据失败: {e}. AI原始返回: {response_str}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"调用AI进行数据提取时发生未知错误: {e}")


    def _analyze_data_from_structured_json(self, structured_data: list):
        """从AI提取的结构化JSON数据进行初步数据分析"""
        if not structured_data:
            raise ValueError("输入的结构化数据为空")
            
        df = pd.DataFrame(structured_data)
        
        # 确保分数列是数字类型
        df['total_score'] = pd.to_numeric(df['total_score'], errors='coerce').fillna(0)

        average_score = df['total_score'].mean()
        failing_students = df[df['total_score'] < 60]['name'].tolist()
        
        # 分析知识点错误率
        all_knowledge_points = {}
        for item in structured_data:
            kps = item.get('knowledge_points', {})
            if isinstance(kps, dict):
                for kp, score in kps.items():
                    if kp not in all_knowledge_points:
                        all_knowledge_points[kp] = []
                    # 假设1为正确，0或其它为错误
                    all_knowledge_points[kp].append(1 if score == 1 else 0)
        
        error_rates = {}
        for kp, scores in all_knowledge_points.items():
            if scores:
                error_rate = 1 - (sum(scores) / len(scores))
                error_rates[kp] = f"{error_rate:.2%}"

        analysis_summary = {
            "average_score": f"{average_score:.2f}",
            "failing_students_count": len(failing_students),
            "failing_students_list": failing_students,
            "knowledge_point_error_rates": error_rates,
            "dataframe": df # 将DataFrame传递下去用于图表生成
        }
        return analysis_summary

    async def _get_ai_insights(self, analysis_data: dict):
        """调用AI服务获取教学建议"""
        prompt = f"""
        作为一名资深教学分析专家，请根据以下学生成绩数据分析，生成“预备知识掌握情况推断”和“教学建议”。
        分析应深入、具体，并提供可操作的建议。

        数据摘要：
        - 班级平均分：{analysis_data['average_score']}
        - 不及格学生人数：{analysis_data['failing_students_count']}
        - 不及格学生名单：{', '.join(analysis_data['failing_students_list']) if analysis_data['failing_students_list'] else '无'}
        - 主要知识点错误率：{json.dumps(analysis_data['knowledge_point_error_rates'], ensure_ascii=False)}

        请提供结构化的JSON输出，包含'knowledge_gaps'和'teaching_suggestions'两个键。
        'knowledge_gaps' 是一个列表，每个元素是一个对象，包含 'gap' (具体知识点问题) 和 'students' (涉及的学生名单，可选)。
        'teaching_suggestions' 也是一个列表，每个元素是一个对象，包含 'suggestion' (具体教学建议) 和 'priority' (优先级，如 '高', '中', '低')。
        """
        try:
            response_str = await self.ai_service.generate_text(prompt, use_gemini=True)
            if not response_str:
                raise ValueError("AI未能返回任何内容")
            
            # 使用dirtyjson来解析可能不规范的JSON
            response = dirtyjson.loads(response_str)
            return response
        except (dirtyjson.error.Error, ValueError, Exception) as e:
            return {
                "knowledge_gaps": [{"gap": "AI深度分析失败", "suggestion": f"无法生成教学建议。错误: {e}"}],
                "teaching_suggestions": [{"suggestion": "由于AI分析失败，无法提供教学建议。", "priority": "高"}]
            }


    async def process_grades_file(self, file: UploadFile, user_id: int):
        # 步骤1: 使用小模型将Excel转换为结构化数据
        structured_data = await self._extract_structured_data_with_ai(file)
        
        # 步骤2: 基于结构化数据进行统计分析
        analysis_data = self._analyze_data_from_structured_json(structured_data)
        
        # 步骤3: 使用大模型进行学情分析和建议生成
        ai_insights_json = await self._get_ai_insights(analysis_data)
        
        df = analysis_data["dataframe"]
        # 创建图表所需的数据
        charts_data = [
            {"type": "bar", "title": "分数分布", "data": {str(k): int(v) for k, v in df['total_score'].value_counts().to_dict().items()}},
            {"type": "pie", "title": "知识点错误率", "data": analysis_data.get("knowledge_point_error_rates", {})}
        ]

        # 从AI结果中提取或生成摘要
        summary_text = "AI分析摘要：\n"
        if "knowledge_gaps" in ai_insights_json and isinstance(ai_insights_json["knowledge_gaps"], list) and ai_insights_json["knowledge_gaps"]:
            first_gap = ai_insights_json["knowledge_gaps"][0]
            summary_text += f"- 主要问题: {first_gap.get('gap', '未明确')}\n"
        else:
            summary_text = "AI分析失败或未返回有效数据，无法生成摘要。"


        new_report = AnalysisReport(
            analysis_id=str(uuid.uuid4()),
            user_id=user_id,
            summary=summary_text,
            charts_data=charts_data,
            knowledge_gaps=ai_insights_json.get("knowledge_gaps", [])
        )
        
        self.db.add(new_report)
        self.db.commit()
        self.db.refresh(new_report)
        
        return new_report

    def get_analysis_report(self, analysis_id: str, user_id: int):
        report = self.db.query(AnalysisReport).filter(
            AnalysisReport.analysis_id == analysis_id,
            AnalysisReport.user_id == user_id
        ).first()
        
        if not report:
            raise HTTPException(status_code=404, detail="报告未找到或无权访问")
            
        return report
