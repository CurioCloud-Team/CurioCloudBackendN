"""
PPT生成服务

负责与讯飞PPT API交互，创建和管理PPT生成任务。
"""
import time
import hashlib
import hmac
import base64
import json
import asyncio
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.ppt import PPTGenerationTask
from app.schemas.ppt import PPTTaskCreate

class PPTService:
    def __init__(self, db: Session):
        self.db = db
        self.app_id = settings.xunfei_app_id
        self.api_secret = settings.xunfei_api_secret
        self.base_url = "https://zwapi.xfyun.cn/api/ppt/v2"

    def _get_signature(self, ts: str) -> str:
        """生成讯飞API签名"""
        auth = hashlib.md5((self.app_id + ts).encode('utf-8')).hexdigest()
        signature = hmac.new(self.api_secret.encode('utf-8'), auth.encode('utf-8'), hashlib.sha1).digest()
        return base64.b64encode(signature).decode('utf-8')

    def _get_headers(self, content_type: str = "application/json; charset=utf-8"):
        """构建请求头"""
        timestamp = str(int(time.time()))
        signature = self._get_signature(timestamp)
        return {
            "appId": self.app_id,
            "timestamp": timestamp,
            "signature": signature,
            "Content-Type": content_type
        }

    async def create_ppt_task(self, user_id: int, ppt_data: PPTTaskCreate, background_tasks: BackgroundTasks) -> PPTGenerationTask:
        """创建PPT生成任务并启动后台轮询"""
        db_task = PPTGenerationTask(
            user_id=user_id,
            query=ppt_data.query,
            status="pending"
        )
        self.db.add(db_task)
        self.db.commit()
        self.db.refresh(db_task)

        background_tasks.add_task(self._run_ppt_generation, db_task.id, ppt_data)
        return db_task

    async def _run_ppt_generation(self, db_task_id: int, ppt_data: PPTTaskCreate):
        """后台执行PPT生成和状态更新"""
        db_task = self.db.query(PPTGenerationTask).filter(PPTGenerationTask.id == db_task_id).first()
        if not db_task:
            return

        try:
            # 1. 创建任务
            db_task.status = "processing"
            self.db.commit()

            form_data = MultipartEncoder(
                fields={
                    "query": ppt_data.query,
                    "templateId": ppt_data.template_id,
                    "author": ppt_data.author,
                    "isCardNote": str(ppt_data.is_card_note),
                    "search": str(ppt_data.search),
                    "isFigure": str(ppt_data.is_figure),
                    "aiImage": ppt_data.ai_image,
                }
            )
            headers = self._get_headers(form_data.content_type)
            
            create_url = f"{self.base_url}/create"
            response = requests.post(create_url, data=form_data, headers=headers, timeout=30)
            response.raise_for_status()
            resp_data = response.json()

            if resp_data.get("code") != 0:
                raise HTTPException(status_code=400, detail=f"创建PPT任务失败: {resp_data.get('message')}")

            task_id = resp_data["data"]["sid"]
            db_task.task_id = task_id
            self.db.commit()

            # 2. 轮询任务进度
            progress_url = f"{self.base_url}/progress?sid={task_id}"
            progress_headers = self._get_headers() # Default JSON content type for GET

            while True:
                await asyncio.sleep(5) # 轮询间隔
                progress_response = requests.get(progress_url, headers=progress_headers, timeout=30)
                progress_response.raise_for_status()
                progress_data = progress_response.json()
                
                if progress_data.get("code") != 0:
                    raise HTTPException(status_code=400, detail=f"查询任务进度失败: {progress_data.get('message')}")

                ppt_status = progress_data["data"].get("pptStatus")
                if ppt_status == "done":
                    db_task.status = "done"
                    db_task.ppt_url = progress_data["data"]["pptUrl"]
                    self.db.commit()
                    break
                elif ppt_status == "failed":
                    raise HTTPException(status_code=500, detail=f"PPT生成失败: {progress_data['data'].get('failReason')}")

        except Exception as e:
            db_task.status = "failed"
            db_task.error_message = str(e)
            self.db.commit()
        finally:
            self.db.close()

    def get_task_status(self, task_id: int, user_id: int) -> PPTGenerationTask:
        """获取指定任务的状态"""
        db_task = self.db.query(PPTGenerationTask).filter(PPTGenerationTask.id == task_id, PPTGenerationTask.user_id == user_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="任务未找到")
        return db_task
