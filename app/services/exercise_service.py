"""
练习题业务逻辑服务
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services.ai_service import AIService
from app.models.lesson_plan import LessonPlan
from app.models.exercise import Question, Choice, QuestionType, DifficultyLevel
from app.schemas.exercise import QuestionCreate

class ExerciseService:
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    async def generate_and_save_mcq(
        self, lesson_plan_id: int, num_questions: int, difficulty: str
    ) -> list[Question]:
        """
        为指定的教案生成并保存选择题
        """
        lesson_plan = self.db.query(LessonPlan).filter(LessonPlan.id == lesson_plan_id).first()
        if not lesson_plan:
            raise HTTPException(status_code=404, detail="未找到指定的教案")

        # 组合教案内容
        content = f"标题: {lesson_plan.title}\n教学目标: {lesson_plan.teaching_objective}\n教学大纲: {lesson_plan.teaching_outline}"

        # 调用AI服务生成题目
        generated_questions = await self.ai_service.generate_multiple_choice_questions(
            content=content,
            num_questions=num_questions,
            difficulty=difficulty
        )

        if not generated_questions:
            raise HTTPException(status_code=500, detail="AI服务未能生成题目")

        saved_questions = []
        try:
            for q_data in generated_questions:
                question_create = QuestionCreate(
                    lesson_plan_id=lesson_plan_id,
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    difficulty=DifficultyLevel(difficulty),
                    content=q_data["content"],
                    answer=q_data.get("answer"),
                    choices=[choice for choice in q_data["choices"]]
                )

                db_question = Question(
                    lesson_plan_id=question_create.lesson_plan_id,
                    question_type=question_create.question_type,
                    difficulty=question_create.difficulty,
                    content=question_create.content,
                    answer=question_create.answer
                )

                self.db.add(db_question)
                self.db.flush()  # Flush to get the question ID

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
            raise HTTPException(status_code=500, detail=f"保存题目时出错: {e}")

    async def generate_and_save_fitb(
        self, lesson_plan_id: int, num_questions: int, difficulty: str
    ) -> list[Question]:
        """
        为指定的教案生成并保存填空题
        """
        lesson_plan = self.db.query(LessonPlan).filter(LessonPlan.id == lesson_plan_id).first()
        if not lesson_plan:
            raise HTTPException(status_code=404, detail="未找到指定的教案")

        content = f"标题: {lesson_plan.title}\n教学目标: {lesson_plan.teaching_objective}\n教学大纲: {lesson_plan.teaching_outline}"

        generated_questions = await self.ai_service.generate_fill_in_the_blank_questions(
            content=content,
            num_questions=num_questions,
            difficulty=difficulty
        )

        if not generated_questions:
            raise HTTPException(status_code=500, detail="AI服务未能生成题目")

        saved_questions = []
        try:
            for q_data in generated_questions:
                # 注意：填空题没有选项
                question_create = QuestionCreate(
                    lesson_plan_id=lesson_plan_id,
                    question_type=QuestionType.FILL_IN_THE_BLANK,
                    difficulty=DifficultyLevel(difficulty),
                    content=q_data["content"],
                    answer=q_data.get("answer"),
                    choices=[] # 填空题没有选项
                )

                db_question = Question(
                    lesson_plan_id=question_create.lesson_plan_id,
                    question_type=question_create.question_type,
                    difficulty=question_create.difficulty,
                    content=question_create.content,
                    answer=question_create.answer
                )
                self.db.add(db_question)
                saved_questions.append(db_question)

            self.db.commit()
            for q in saved_questions:
                self.db.refresh(q)
            return saved_questions
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"保存题目时出错: {e}")
