"""
本模块包含用于生成练习题的提示模板。
"""

def get_multiple_choice_prompt(content: str, num_questions: int, difficulty: str) -> str:
    """
    返回生成选择题的提示。
    """
    return f"""
    请根据以下教案内容，生成 {num_questions} 道难度为 '{difficulty}' 的选择题。
    输出必须是一个有效的JSON数组，其中每个对象代表一个问题，并具有以下结构:
    {{
        "content": "题目文本",
        "choices": [
            {{
                "content": "选项A",
                "is_correct": false
            }},
            {{
                "content": "选项B",
                "is_correct": true
            }},
            {{
                "content": "选项C",
                "is_correct": false
            }},
            {{
                "content": "选项D",
                "is_correct": false
            }}
        ],
        "answer": "对正确答案的详细解释。"
    }}

    教案内容:
    ---
    {content}
    ---

    请仅提供JSON数组作为输出。
    """

def get_fill_in_the_blank_prompt(content: str, num_questions: int, difficulty: str) -> str:
    """
    返回生成填空题的提示。
    """
    return f"""
    请根据以下教案内容，生成 {num_questions} 道难度为 '{difficulty}' 的填空题。
    题目内容应使用“___”代表空格。
    输出必须是一个有效的JSON数组，其中每个对象代表一个问题，并具有以下结构:
    {{
        "content": "带有“___”空格的题目文本。",
        "answer": "空格的正确答案。"
    }}

    教案内容:
    ---
    {content}
    ---

    请仅提供JSON数组作为输出。
    """

def get_short_answer_prompt(content: str, num_questions: int, difficulty: str) -> str:
    """
    返回生成简答题的提示。
    """
    return f"""
    请根据以下教案内容，生成 {num_questions} 道难度为 '{difficulty}' 的简答题。
    输出必须是一个有效的JSON数组，其中每个对象代表一个问题，并具有以下结构:
    {{
        "content": "题目文本。",
        "answer": "简答题的参考答案或要点。"
    }}

    教案内容:
    ---
    {content}
    ---

    请仅提供JSON数组作为输出。
    """
