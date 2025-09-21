"""
练习题业务逻辑服务
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.services.ai_service import AIService
from app.models.lesson_plan import LessonPlan
from app.models.exercise import Question, Choice, QuestionType, DifficultyLevel
from app.schemas.exercise import QuestionCreate, ChoiceCreate

class ExerciseService:
    """
    处理与练习题相关的业务逻辑，包括生成和存储。
    """
    def __init__(self, db: Session):
        """
        初始化练习题服务。

        Args:
            db (Session): 数据库会话实例。
        """
        self.db = db
        self.ai_service = AIService()

    def _get_lesson_plan_content(self, lesson_plan_id: int) -> str:
        """
        根据教案ID获取并格式化教案内容。

        Args:
            lesson_plan_id (int): 教案的ID。

        Returns:
            str: 格式化后的教案内容字符串。

        Raises:
            HTTPException: 如果找不到教案，则抛出404错误。
        """
        lesson_plan = self.db.query(LessonPlan).filter(LessonPlan.id == lesson_plan_id).first()
        if not lesson_plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到指定的教案")
        
        return f"标题: {lesson_plan.title}\n教学目标: {lesson_plan.teaching_objective}\n教学大纲: {lesson_plan.teaching_outline}"

    async def _generate_questions_from_ai(self, question_type: QuestionType, content: str, num_questions: int, difficulty: str):
        """
        根据题目类型调用相应的AI服务生成题目。

        Args:
            question_type (QuestionType): 题目类型。
            content (str): 教案内容。
            num_questions (int): 题目数量。
            difficulty (str): 题目难度。

        Returns:
            list: AI生成的题目数据列表。

        Raises:
            HTTPException: 如果AI服务未能生成题目，则抛出500错误。
        """
        generation_map = {
            QuestionType.MULTIPLE_CHOICE: self.ai_service.generate_multiple_choice_questions,
            QuestionType.FILL_IN_THE_BLANK: self.ai_service.generate_fill_in_the_blank_questions,
            QuestionType.SHORT_ANSWER: self.ai_service.generate_short_answer_questions,
        }
        
        generate_func = generation_map.get(question_type)
        if not generate_func:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"不支持的题目类型: {question_type}")

        generated_questions = await generate_func(
            content=content,
            num_questions=num_questions,
            difficulty=difficulty
        )

        if not generated_questions:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="AI服务未能生成题目")
        
        return generated_questions

    def _save_questions_to_db(self, lesson_plan_id: int, difficulty: str, question_type: QuestionType, questions_data: list) -> list[Question]:
        """
        将生成的题目数据保存到数据库。

        Args:
            lesson_plan_id (int): 教案ID。
            difficulty (str): 题目难度。
            question_type (QuestionType): 题目类型。
            questions_data (list): 包含题目信息的字典列表。

        Returns:
            list[Question]: 保存到数据库的Question对象列表。
        
        Raises:
            HTTPException: 如果保存过程中发生错误，则抛出500错误。
        """
        saved_questions = []
        try:
            for q_data in questions_data:
                question_create = QuestionCreate(
                    lesson_plan_id=lesson_plan_id,
                    question_type=question_type,
                    difficulty=DifficultyLevel(difficulty),
                    content=q_data.get("content"),
                    answer=q_data.get("answer"),
                    choices=[ChoiceCreate(**choice) for choice in q_data.get("choices", [])]
                )

                db_question = Question(
                    lesson_plan_id=question_create.lesson_plan_id,
                    question_type=question_create.question_type,
                    difficulty=question_create.difficulty,
                    content=question_create.content,
                    answer=question_create.answer
                )
                self.db.add(db_question)
                self.db.flush()

                for choice_data in question_create.choices:
                    db_choice = Choice(
                        question_id=db_question.id,
                        content=choice_data.content,
                        is_correct=choice_data.is_correct
                    )
                    self.db.add(db_choice)
                
                saved_questions.append(db_question)

            self.db.commit()
            for q in saved_questions:
                self.db.refresh(q)
            return saved_questions
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"保存题目时出错: {e}")

    async def generate_and_save_mcq(
        self, lesson_plan_id: int, num_questions: int, difficulty: str
    ) -> list[Question]:
        """
        为指定的教案生成并保存选择题。
        """
        content = self._get_lesson_plan_content(lesson_plan_id)
        generated_questions = await self._generate_questions_from_ai(
            QuestionType.MULTIPLE_CHOICE, content, num_questions, difficulty
        )
        return self._save_questions_to_db(lesson_plan_id, difficulty, QuestionType.MULTIPLE_CHOICE, generated_questions)

    async def generate_and_save_fitb(
        self, lesson_plan_id: int, num_questions: int, difficulty: str
    ) -> list[Question]:
        """
        为指定的教案生成并保存填空题。
        """
        content = self._get_lesson_plan_content(lesson_plan_id)
        generated_questions = await self._generate_questions_from_ai(
            QuestionType.FILL_IN_THE_BLANK, content, num_questions, difficulty
        )
        return self._save_questions_to_db(lesson_plan_id, difficulty, QuestionType.FILL_IN_THE_BLANK, generated_questions)

    async def generate_and_save_saq(
        self, lesson_plan_id: int, num_questions: int, difficulty: str
    ) -> list[Question]:
        """
        为指定的教案生成并保存简答题。
        """
        content = self._get_lesson_plan_content(lesson_plan_id)
        generated_questions = await self._generate_questions_from_ai(
            QuestionType.SHORT_ANSWER, content, num_questions, difficulty
        )
        return self._save_questions_to_db(lesson_plan_id, difficulty, QuestionType.SHORT_ANSWER, generated_questions)
