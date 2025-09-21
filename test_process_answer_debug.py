import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.teaching_service import TeachingService
import asyncio
import traceback

async def test_process_answer():
    try:
        db = next(get_db())
        teaching_service = TeachingService(db)
        
        # 使用最新的会话ID
        session_id = 'e9999f95-3c0a-437e-8836-eefeb1459683'
        answer = '数学'
        
        print(f'测试 process_answer: session_id={session_id}, answer={answer}')
        result = await teaching_service.process_answer(session_id, answer)
        print(f'结果: {result}')
        
    except Exception as e:
        print(f'错误类型: {type(e).__name__}')
        print(f'错误消息: {str(e)}')
        print(f'详细堆栈跟踪:')
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_process_answer())
