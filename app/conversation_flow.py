"""
对话流程配置

定义对话式教学设计的状态机配置
"""

CONVERSATION_FLOW = {
    'start_step': 'ask_subject',
    'steps': {
        'ask_subject': {
            'question': '您好！我们来一起准备一堂新课。首先，这堂课是关于哪个学科的？',
            'key_to_save': 'subject',
            'options': ['语文', '数学', '英语', '物理', '历史', '生物'],
            'allows_free_text': True,
            'next_step': 'ask_grade'
        },
        'ask_grade': {
            'question': '好的，那么这堂课是针对哪个年级的学生？',
            'key_to_save': 'grade',
            'options': ['小学一年级', '小学二年级', '小学三年级', '小学四年级', '小学五年级', '小学六年级',
                       '初中一年级', '初中二年级', '初中三年级',
                       '高中一年级', '高中二年级', '高中三年级'],
            'allows_free_text': True,
            'next_step': 'ask_topic'
        },
        'ask_topic': {
            'question': '请告诉我这堂课的具体课题或主题是什么？',
            'key_to_save': 'topic',
            'options': [],  # 空选项列表，表示纯输入框
            'allows_free_text': True,
            'next_step': 'ask_duration'
        },
        'ask_duration': {
            'question': '这堂课预计需要多长时间？（单位：分钟）',
            'key_to_save': 'duration_minutes',
            'options': ['30', '40', '45', '50', '60', '90'],
            'allows_free_text': True,
            'next_step': 'finalize'  # 特殊标识：结束对话，开始生成
        }
    }
}


def get_step_config(step_key: str) -> dict:
    """
    获取指定步骤的配置

    Args:
        step_key: 步骤键名

    Returns:
        步骤配置字典，如果不存在返回None
    """
    return CONVERSATION_FLOW['steps'].get(step_key)


def get_next_step(current_step: str) -> str:
    """
    获取下一步的键名

    Args:
        current_step: 当前步骤键名

    Returns:
        下一步键名，如果已经是最后一步返回None
    """
    step_config = get_step_config(current_step)
    if step_config:
        return step_config.get('next_step')
    return None


def is_final_step(step_key: str) -> bool:
    """
    检查是否为最终步骤

    Args:
        step_key: 步骤键名

    Returns:
        是否为最终步骤
    """
    return get_next_step(step_key) == 'finalize'