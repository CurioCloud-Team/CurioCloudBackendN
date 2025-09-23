import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile
from app.models.analytics import AnalysisReport
from app.services.ai_service import AIService
import uuid

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    def _parse_excel(self, file: UploadFile):
        try:
            df = pd.read_excel(file.file)
            # 这里可以添加更复杂的列名验证和数据清洗逻辑
            if '姓名' not in df.columns or '分数' not in df.columns:
                raise HTTPException(status_code=400, detail="Excel文件必须包含'姓名'和'分数'列")
            return df
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无法解析Excel文件: {e}")

    def _analyze_data(self, df: pd.DataFrame):
        """使用pandas进行初步数据分析"""
        average_score = df['分数'].mean()
        failing_students = df[df['分数'] < 60]['姓名'].tolist()
        
        # 假设Excel中还有知识点得分列，例如 '知识点1', '知识点2'
        knowledge_columns = [col for col in df.columns if col.startswith('知识点')]
        error_rates = {}
        if knowledge_columns:
            for col in knowledge_columns:
                # 假设知识点列中，0表示错误，1表示正确
                error_rate = 1 - df[col].mean()
                error_rates[col] = f"{error_rate:.2%}"

        analysis_summary = {
            "average_score": f"{average_score:.2f}",
            "failing_students_count": len(failing_students),
            "failing_students_list": failing_students,
            "knowledge_point_error_rates": error_rates
        }
        return analysis_summary

    async def _get_ai_insights(self, analysis_data: dict):
        """调用AI服务获取教学建议"""
        prompt = f"""
        根据以下学生成绩数据分析，生成“预备知识掌握情况推断”和“教学建议”。
        数据摘要：
        - 平均分：{analysis_data['average_score']}
        - 不及格学生人数：{analysis_data['failing_students_count']}
        - 不及格学生名单：{', '.join(analysis_data['failing_students_list'])}
        - 主要知识点错误率：{analysis_data['knowledge_point_error_rates']}

        请提供结构化的JSON输出，包含'knowledge_gaps'和'teaching_suggestions'两个键。
        """
        try:
            response_str = await self.ai_service.generate_text(prompt, use_gemini=True)
            # 假设AI返回的是JSON字符串, 解析它
            import json
            response = json.loads(response_str)
            return response
        except Exception as e:
            # 在AI调用失败时提供一个默认的、信息丰富的建议，并符合预期的列表格式
            return {
                "knowledge_gaps": [{"gap": "AI分析失败", "suggestion": f"无法生成知识差距评估，请检查输入数据或稍后重试。错误: {e}"}],
                "teaching_suggestions": [{"suggestion": "由于AI分析失败，无法提供教学建议。", "details": "建议重点关注错误率较高的知识点，并为不及格学生提供额外辅导。"}]
            }


    async def process_grades_file(self, file: UploadFile, user_id: int):
        df = self._parse_excel(file)
        analysis_data = self._analyze_data(df)
        
        ai_insights_json = await self._get_ai_insights(analysis_data)
        
        # 创建图表所需的数据
        charts_data = [
            {"type": "bar", "title": "分数分布", "data": {str(k): v for k, v in df['分数'].value_counts().to_dict().items()}},
            {"type": "pie", "title": "知识点错误率", "data": analysis_data.get("knowledge_point_error_rates", {})}
        ]

        # 从AI结果中提取或生成摘要
        summary_text = "AI分析摘要：\n"
        if "knowledge_gaps" in ai_insights_json and isinstance(ai_insights_json["knowledge_gaps"], list) and ai_insights_json["knowledge_gaps"]:
            # 将知识点差距的第一个作为摘要
            first_gap = ai_insights_json["knowledge_gaps"][0]
            summary_text += f"- 主要问题: {first_gap.get('gap', '未明确')}\n"
            summary_text += f"- 初步建议: {first_gap.get('suggestion', '无')}"
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
