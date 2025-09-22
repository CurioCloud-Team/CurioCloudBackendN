import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.schemas.teaching import ProcessAnswerResponse
from pydantic import ValidationError
import traceback

def test_schema_validation():
    # 模拟从teaching_service返回的数据
    test_data = {
        'session_id': 'e9999f95-3c0a-437e-8836-eefeb1459683', 
        'status': 'in_progress', 
        'is_dynamic_mode': True, 
        'question_card': {
            'question': '您希望本次课程主要达到哪种教学目标？', 
            'question_type': 'teaching_method', 
            'key_to_save': 'teaching_goals', 
            'options': ['知识传授：让学生掌握核心概念和公式', '能力培养：提升学生解决实际问题的能力和思维能力'], 
            'allows_free_text': True, 
            'priority': 'high', 
            'reasoning': '在明确学科（数学）后，下一步需要了解教学的根本目的'
        }, 
        'question_count': 3, 
        'max_questions': 5
    }
    
    try:
        print('测试 ProcessAnswerResponse schema 验证...')
        response = ProcessAnswerResponse(**test_data)
        print(f'验证成功: {response}')
        
    except ValidationError as e:
        print(f'验证错误: {e}')
        print('详细错误信息:')
        for error in e.errors():
            print(f'  字段: {error["loc"]}, 错误: {error["msg"]}, 输入: {error["input"]}')
            
    except Exception as e:
        print(f'其他错误: {type(e).__name__}: {str(e)}')
        traceback.print_exc()

if __name__ == '__main__':
    test_schema_validation()
