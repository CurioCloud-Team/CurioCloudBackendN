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

    async def _extract_generic_json_from_excel(self, file: UploadFile) -> list:
        """
        使用AI将任何Excel文件内容转换为通用的JSON数据结构（字典列表）。
        """
        try:
            df = pd.read_excel(file.file)
            # 处理潜在的空文件或只有表头的文件
            if df.empty:
                raise HTTPException(status_code=400, detail="Excel文件为空或无法解析。")
            # 仅使用前5行数据让AI分析结构
            file_content_text = df.head(5).to_csv(index=False)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无法读取或转换Excel文件: {e}")

        prompt = f"""
        你是一个高效的数据转换工具。请将以下CSV格式的表格数据，转换为一个JSON数组。
        数组中的每个对象代表原始表格的一行。对象的键应该是表格的列名。
        请确保所有行都被转换。不要修改任何数据，只需进行格式转换。

        CSV数据如下:
        ---
        {file_content_text}
        ---

        请严格按照JSON数组的格式输出，不要包含任何额外的解释、代码块标记或文本。
        """
        try:
            response_str = await self.ai_service.generate_text(
                prompt, 
                use_gemini=True, 
                model="google/gemini-2.5-flash",
                is_json_output=True # 请求JSON输出
            )
            if not response_str:
                raise HTTPException(status_code=500, detail="AI未能从文件中提取任何数据。")

            structured_data = dirtyjson.loads(response_str)
            
            if not isinstance(structured_data, list):
                raise ValueError("AI返回的数据不是一个列表。")

            return structured_data
        except (dirtyjson.error.Error, ValueError) as e:
            raise HTTPException(status_code=500, detail=f"AI结构化数据失败: {e}. AI原始返回: {response_str[:500]}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"调用AI进行数据提取时发生未知错误: {e}")

    async def _generate_narrative_report(self, extracted_data: list) -> str:
        """
        根据提取的JSON数据，调用AI生成一篇完整的叙事性分析报告。
        """
        # 将列表转换为更易于AI阅读的JSON字符串
        data_json_str = json.dumps(extracted_data, indent=2, ensure_ascii=False)

        prompt = f"""
        你是一位顶级的教育数据分析师和资深教师。你的任务是根据提供的学生表现数据（JSON格式），撰写一篇专业、深入、且充满人文关怀的学情分析报告。

        **核心要求:**
        1.  **文章形式**: 最终输出必须是一篇流畅、连贯的Markdown格式文章，而不是一个简单的JSON对象或数据点列表。
        2.  **自适应分析**: 你的分析深度必须与数据丰富度相匹配。
            *   **如果数据简单** (例如，只有姓名和总分), 请进行总体表现分析，如计算平均分、最高分、最低分，识别优等生和需要关注的学生，并给出普遍性的学习建议。
            *   **如果数据复杂** (例如，包含各科成绩、知识点得分、出勤率等), 请进行多维度、深层次的分析。找出学生间的关联性（如某几位同学在数学和物理上都偏弱），分析特定知识点的普遍性问题，并提出极具针对性的教学策略。
        3.  **数据驱动**: 你的所有结论都必须基于提供的数据。在文章中，请巧妙地引用关键数据来支撑你的观点（例如，“本次考试平均分为78.5，说明班级整体掌握情况良好，但仍有约15%的学生（如王五、赵六）未能及格，需要重点关注…”）。
        4.  **结构清晰**: 报告应包含但不限于以下部分，请用Markdown标题组织：
            *   `### 一、总体表现概览` (总结整体情况)
            *   `### 二、亮点与优势分析` (表扬表现优异的学生和普遍掌握较好的方面)
            *   `### 三"、潜在问题与挑战` (指出需要关注的学生群体和普遍性知识短板)
            *   `### 四、具体教学建议` (提供可操作的、针对性的建议)
        5.  **人文关怀**: 语言应专业且富有同理心，避免使用冰冷或指责性的词汇。

        **学生数据如下:**
        ```json
        {data_json_str}
        ```

        请立即开始撰写你的分析报告。
        """
        try:
            report_text = await self.ai_service.generate_text(
                prompt, 
                use_gemini=True, 
                model="google/gemini-pro-1.5",
                is_json_output=False # 我们需要的是Markdown文本
            )
            if not report_text:
                return "AI未能生成分析报告。请检查输入数据是否有效。"
            
            return report_text
        except Exception as e:
            # 在生产环境中，这里应该有更完善的日志记录
            # 将底层异常包装成HTTPException，以便将清晰的错误信息传递给上层调用者
            raise HTTPException(status_code=502, detail=f"AI报告生成失败: {e}")


    async def process_grades_file(self, file: UploadFile, user_id: int):
        # 步骤1: 从Excel中提取通用的JSON数据
        extracted_data = await self._extract_generic_json_from_excel(file)
        
        # 步骤2: 基于提取的数据生成叙事性报告
        narrative_report = await self._generate_narrative_report(extracted_data)
        
        # 注意：图表和结构化知识点现在由AI在报告中生成，我们只存储核心报告
        new_report = AnalysisReport(
            analysis_id=str(uuid.uuid4()),
            user_id=user_id,
            summary=narrative_report, # 存储完整的Markdown报告
            # 以下字段将被废弃或由前端根据报告内容解析
            charts_data=[], 
            knowledge_gaps=[],
            average_score=None,
            failing_students_count=None,
            failing_students_list=None,
            knowledge_point_error_rates=None
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
            
        # 返回一个简化的、以完整报告为核心的结构
        return {
            "analysis_id": report.analysis_id,
            "summary": report.summary, # summary现在是完整的报告
            "report": {
                "charts_data": [], # 前端可根据报告内容自行生成
                "knowledge_gaps": [], # 信息已在报告中
                "statistics": {} # 信息已在报告中
            }
        }

    def get_all_analysis_reports_for_user(self, user_id: int):
        """获取指定用户的所有分析报告条目"""
        reports = self.db.query(AnalysisReport).filter(
            AnalysisReport.user_id == user_id
        ).order_by(AnalysisReport.created_at.desc()).all()

        if not reports:
            return []

        report_entries = []
        for report in reports:
            summary_preview = report.summary
            if len(summary_preview) > 50:
                summary_preview = summary_preview[:50] + "..."

            report_entries.append({
                "analysis_id": report.analysis_id,
                "summary_preview": summary_preview,
                "created_at": report.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })
            
        return report_entries
