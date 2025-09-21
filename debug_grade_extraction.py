#!/usr/bin/env python3
"""
调试grade字段提取功能的脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.ai_service import AIService
from app.services.teaching_service import TeachingService

def test_grade_extraction():
    """测试年级提取功能"""
    
    # 创建AI服务实例
    ai_service = AIService()
    
    # 测试数据 - 模拟动态模式收集的数据
    test_data_1 = {
        "question_1_answer": "我想准备一堂数学课，主要讲解二次方程的解法",
        "question_2_answer": "这是针对初中二年级的学生，他们已经学过一次方程",
        "question_3_answer": "课程时长是45分钟，希望能够让学生掌握基本的解题方法"
    }
    
    test_data_2 = {
        "question_1_answer": "准备一节物理课",
        "question_2_answer": "高一学生，刚接触物理",
        "question_3_answer": "40分钟课程"
    }
    
    test_data_3 = {
        "question_1_answer": "语文课程设计",
        "question_2_answer": "小学三年级的孩子们",
        "question_3_answer": "需要35分钟"
    }
    
    test_data_4 = {
        "grade": "初中一年级",  # 直接设置grade字段
        "subject": "数学"
    }
    
    print("=== Grade提取功能测试 ===\n")
    
    # 测试用例1
    print("测试用例1 - 包含'初中二年级':")
    print(f"输入数据: {test_data_1}")
    extracted_grade_1 = ai_service._extract_grade_from_data(test_data_1)
    print(f"提取的年级: '{extracted_grade_1}'\n")
    
    # 测试用例2
    print("测试用例2 - 包含'高一':")
    print(f"输入数据: {test_data_2}")
    extracted_grade_2 = ai_service._extract_grade_from_data(test_data_2)
    print(f"提取的年级: '{extracted_grade_2}'\n")
    
    # 测试用例3
    print("测试用例3 - 包含'小学三年级':")
    print(f"输入数据: {test_data_3}")
    extracted_grade_3 = ai_service._extract_grade_from_data(test_data_3)
    print(f"提取的年级: '{extracted_grade_3}'\n")
    
    # 测试用例4
    print("测试用例4 - 直接grade字段:")
    print(f"输入数据: {test_data_4}")
    extracted_grade_4 = ai_service._extract_grade_from_data(test_data_4)
    print(f"提取的年级: '{extracted_grade_4}'\n")
    
    # 测试TeachingService的提取方法
    print("=== TeachingService Grade提取测试 ===\n")
    
    # 模拟TeachingService的方法（不需要数据库连接）
    class MockTeachingService:
        def _extract_grade_from_collected_data(self, collected_data):
            # 首先检查直接的grade字段
            if collected_data.get("grade"):
                return collected_data["grade"]
            
            # 从动态问题答案中提取年级信息
            for key, value in collected_data.items():
                if key.startswith("question_") and key.endswith("_answer") and value:
                    # 检查答案中是否包含年级关键词
                    grade_patterns = [
                        # 小学
                        ("一年级", "小学一年级"), ("二年级", "小学二年级"), ("三年级", "小学三年级"),
                        ("四年级", "小学四年级"), ("五年级", "小学五年级"), ("六年级", "小学六年级"),
                        ("小学", "小学"),
                        # 初中
                        ("初一", "初中一年级"), ("初二", "初中二年级"), ("初三", "初中三年级"),
                        ("七年级", "初中一年级"), ("八年级", "初中二年级"), ("九年级", "初中三年级"),
                        ("初中", "初中"),
                        # 高中
                        ("高一", "高中一年级"), ("高二", "高中二年级"), ("高三", "高中三年级"),
                        ("高中", "高中"),
                        # 大学
                        ("大一", "大学一年级"), ("大二", "大学二年级"), ("大三", "大学三年级"), ("大四", "大学四年级"),
                        ("大学", "大学"),
                        # 幼儿园
                        ("幼儿园", "幼儿园"), ("学前班", "学前班")
                    ]
                    
                    value_lower = value.lower()
                    for pattern, grade in grade_patterns:
                        if pattern in value_lower:
                            return grade
            
            return ""
    
    mock_service = MockTeachingService()
    
    print("TeachingService测试用例1:")
    ts_grade_1 = mock_service._extract_grade_from_collected_data(test_data_1)
    print(f"提取的年级: '{ts_grade_1}'\n")
    
    print("TeachingService测试用例2:")
    ts_grade_2 = mock_service._extract_grade_from_collected_data(test_data_2)
    print(f"提取的年级: '{ts_grade_2}'\n")
    
    print("TeachingService测试用例3:")
    ts_grade_3 = mock_service._extract_grade_from_collected_data(test_data_3)
    print(f"提取的年级: '{ts_grade_3}'\n")

if __name__ == "__main__":
    test_grade_extraction()