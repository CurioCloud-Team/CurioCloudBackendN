"""
LandPPT集成服务

负责与LandPPT API进行通信，将教案转换为PPT
"""
import httpx
import json
from typing import Dict, Any, Optional, List
from fastapi import HTTPException
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class LandPPTService:
    """LandPPT服务类"""

    def __init__(self):
        self.base_url = settings.landppt_base_url.rstrip('/')
        self.api_key = settings.landppt_api_key
        self.default_scenario = settings.landppt_default_scenario
        self.timeout = 300  # 5分钟超时，PPT生成可能需要较长时间

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发起HTTP请求到LandPPT API

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据

        Returns:
            API响应数据

        Raises:
            HTTPException: 请求失败时抛出
        """
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Content-Type": "application/json",
        }

        # 如果配置了API密钥，添加到请求头
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=headers, json=data)
                else:
                    raise HTTPException(status_code=400, detail=f"不支持的HTTP方法: {method}")

                if response.status_code >= 400:
                    logger.error(f"LandPPT API请求失败: {response.status_code} - {response.text}")
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"LandPPT API请求失败: {response.text}"
                    )

                return response.json()

        except httpx.RequestError as e:
            logger.error(f"LandPPT API请求异常: {e}")
            raise HTTPException(status_code=500, detail=f"无法连接到LandPPT服务: {str(e)}")

    def _convert_lesson_plan_to_ppt_request(self, lesson_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        将教案数据转换为LandPPT API请求格式

        Args:
            lesson_plan: 教案数据

        Returns:
            LandPPT API请求数据
        """
        # 构建PPT主题
        topic = f"{lesson_plan['subject']} - {lesson_plan['title']}"

        # 构建需求描述
        requirements = f"""
教案主题：{lesson_plan['title']}
学科：{lesson_plan['subject']}
年级：{lesson_plan['grade']}
教学目标：{lesson_plan['teaching_objective']}
教学大纲：{lesson_plan['teaching_outline']}
"""

        # 添加活动信息
        if lesson_plan.get('activities'):
            requirements += "\n教学活动：\n"
            for activity in lesson_plan['activities']:
                requirements += f"- {activity['activity_name']} ({activity['duration']}分钟): {activity['description']}\n"

        # 确定场景
        scenario = self._determine_scenario(lesson_plan.get('subject', ''))

        return {
            "scenario": scenario,
            "topic": topic,
            "requirements": requirements.strip(),
            "language": "zh",
            "ppt_style": "general",
            "target_audience": lesson_plan.get('grade', ''),
            "description": f"为{lesson_plan.get('grade', '')}学生设计的{lesson_plan.get('subject', '')}课件"
        }

    def _determine_scenario(self, subject: str) -> str:
        """
        根据学科确定PPT场景

        Args:
            subject: 学科名称

        Returns:
            PPT场景标识
        """
        scenario_mapping = {
            "语文": "education",
            "数学": "analysis",
            "英语": "education",
            "物理": "technology",
            "化学": "analysis",
            "生物": "education",
            "历史": "history",
            "地理": "tourism",
            "政治": "business",
            "音乐": "education",
            "美术": "education",
            "体育": "education",
            "信息技术": "technology"
        }

        return scenario_mapping.get(subject, self.default_scenario)

    async def create_ppt_from_lesson_plan(self, lesson_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        从教案创建PPT

        Args:
            lesson_plan: 教案数据

        Returns:
            PPT项目信息

        Raises:
            HTTPException: 创建失败时抛出
        """
        try:
            # 转换教案数据为PPT请求
            ppt_request = self._convert_lesson_plan_to_ppt_request(lesson_plan)

            logger.info(f"正在为教案 '{lesson_plan['title']}' 创建PPT项目")

            # 调用LandPPT API创建项目
            response = await self._make_request("POST", "/api/projects", ppt_request)

            logger.info(f"PPT项目创建成功: {response.get('project_id', 'unknown')}")

            return {
                "success": True,
                "ppt_project_id": response.get("project_id"),
                "ppt_title": response.get("title", lesson_plan['title']),
                "ppt_scenario": response.get("scenario", ppt_request["scenario"]),
                "message": "PPT项目创建成功，正在后台生成PPT内容"
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"创建PPT项目失败: {e}")
            raise HTTPException(status_code=500, detail=f"创建PPT项目失败: {str(e)}")

    async def get_ppt_status(self, ppt_project_id: str) -> Dict[str, Any]:
        """
        获取PPT生成状态

        Args:
            ppt_project_id: PPT项目ID

        Returns:
            PPT状态信息
        """
        try:
            response = await self._make_request("GET", f"/api/projects/{ppt_project_id}")

            return {
                "project_id": response.get("project_id"),
                "title": response.get("title"),
                "status": response.get("status"),
                "progress": self._calculate_progress(response.get("todo_board", {})),
                "slides_count": len(response.get("slides_data", [])) if response.get("slides_data") else 0,
                "created_at": response.get("created_at"),
                "updated_at": response.get("updated_at")
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取PPT状态失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取PPT状态失败: {str(e)}")

    def _calculate_progress(self, todo_board: Dict[str, Any]) -> float:
        """
        计算PPT生成进度

        Args:
            todo_board: TODO板数据

        Returns:
            进度百分比
        """
        if not todo_board or not todo_board.get("stages"):
            return 0.0

        stages = todo_board["stages"]
        completed_stages = sum(1 for stage in stages if stage.get("status") == "completed")

        return round((completed_stages / len(stages)) * 100, 1) if stages else 0.0

    async def export_ppt(self, ppt_project_id: str, export_format: str = "pdf") -> bytes:
        """
        导出PPT文件

        Args:
            ppt_project_id: PPT项目ID
            export_format: 导出格式 (pdf 或 pptx)

        Returns:
            文件二进制数据

        Raises:
            HTTPException: 导出失败时抛出
        """
        try:
            if export_format not in ["pdf", "pptx"]:
                raise HTTPException(status_code=400, detail="不支持的导出格式，仅支持 pdf 和 pptx")

            endpoint = f"/api/projects/{ppt_project_id}/export/{export_format}"

            # 注意：这里需要特殊处理，因为返回的是文件而不是JSON
            url = f"{self.base_url}{endpoint}"
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)

                if response.status_code >= 400:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"PPT导出失败: {response.text}"
                    )

                return response.content

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"PPT导出失败: {e}")
            raise HTTPException(status_code=500, detail=f"PPT导出失败: {str(e)}")

    async def get_ppt_slides(self, ppt_project_id: str) -> Dict[str, Any]:
        """
        获取PPT幻灯片内容

        Args:
            ppt_project_id: PPT项目ID

        Returns:
            幻灯片数据
        """
        try:
            response = await self._make_request("GET", f"/api/projects/{ppt_project_id}")

            return {
                "project_id": response.get("project_id"),
                "title": response.get("title"),
                "slides_html": response.get("slides_html"),
                "slides_data": response.get("slides_data", []),
                "slides_count": len(response.get("slides_data", []))
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取PPT幻灯片失败: {e}")
            raise HTTPException(status_code=500, detail=f"获取PPT幻灯片失败: {str(e)}")