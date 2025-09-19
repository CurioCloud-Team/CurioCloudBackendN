"""
This module contains the prompt templates for generating exercises.
"""

def get_multiple_choice_prompt(content: str, num_questions: int, difficulty: str) -> str:
    """
    Returns the prompt for generating multiple-choice questions.
    """
    return f"""
    Based on the following lesson plan content, please generate {num_questions} multiple-choice questions with a difficulty level of '{difficulty}'.
    The output must be a valid JSON array, where each object represents a question and has the following structure:
    {{
        "content": "The question text",
        "choices": [
            {{
                "content": "Choice A",
                "is_correct": false
            }},
            {{
                "content": "Choice B",
                "is_correct": true
            }},
            {{
                "content": "Choice C",
                "is_correct": false
            }},
            {{
                "content": "Choice D",
                "is_correct": false
            }}
        ],
        "answer": "A detailed explanation of the correct answer."
    }}

    Lesson Plan Content:
    ---
    {content}
    ---

    Please provide only the JSON array as the output.
    """

def get_fill_in_the_blank_prompt(content: str, num_questions: int, difficulty: str) -> str:
    """
    Returns the prompt for generating fill-in-the-blank questions.
    """
    return f"""
    Based on the following lesson plan content, please generate {num_questions} fill-in-the-blank questions with a difficulty level of '{difficulty}'.
    The question content should use '___' to represent the blank.
    The output must be a valid JSON array, where each object represents a question and has the following structure:
    {{
        "content": "The question text with '___' for the blank.",
        "answer": "The correct answer for the blank."
    }}

    Lesson Plan Content:
    ---
    {content}
    ---

    Please provide only the JSON array as the output.
    """

def get_short_answer_prompt(content: str, num_questions: int, difficulty: str) -> str:
    """
    Returns the prompt for generating short-answer questions.
    """
    return f"""
    Based on the following lesson plan content, please generate {num_questions} short-answer questions with a difficulty level of '{difficulty}'.
    The output must be a valid JSON array, where each object represents a question and has the following structure:
    {{
        "content": "The question text.",
        "answer": "A model answer or key points for the short-answer question."
    }}

    Lesson Plan Content:
    ---
    {content}
    ---

    Please provide only the JSON array as the output.
    """
