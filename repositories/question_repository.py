import logging
import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.enums import Levels, Topics
from models.question import Question


logger = logging.getLogger(__name__)


class QuestionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    # Getting a question with its question ID
    async def get_question_by_id(self, question_id: uuid.UUID) -> Question | None:
        logger.info(f"Database: Attempting to find a question with question id: {question_id}")
        query = (
            select(Question)
            .where(Question.question_id == question_id)
        )
        results = await self.db.execute(query)
        question_obj = results.scalar_one_or_none()

        if not question_obj:
            logger.warning(f"Database: No question with question_id found: {question_id}")
        return question_obj
    

    # Return how many questions are available with a topic and level combo
    async def count_by_topic_level(self, topic: Topics, level: Levels) -> int:
        logger.info(
            f"Database: Counting how many questions are available with this topic and level combo: {topic} + {level}"
        )
        query = (
            select(func.count(Question.question_id))
            .where(
                and_(
                    Question.topic == topic,
                    Question.level == level
                )
            )
        )
        results = await self.db.execute(query)
        total_questions = results.scalar_one()
        logger.info(
            f"Database: {total_questions} questions are available with this topic and level combo: {topic} + {level}"
        )
        return total_questions
    

    # Excludes the already asked questions and returns a unique question
    async def get_random_excluding(self, topic: Topics, level: Levels, exclude_ids: list[uuid.UUID]) -> Question | None:
        logger.info(
            f"Database: Excluding questions that are already asked based on this combo: {topic} + {level}"
        )

        # Filter the topic + level questions
        query = (
            select(Question).
            where(
                Question.topic == topic,
                Question.level == level
            )
        )

        # Checking if the question exists in the excluded (exclude_ids) questions
        if exclude_ids:
            query = query.where(Question.question_id.not_in(exclude_ids))

        # Randomizing the quetions
        query = query.order_by(func.random()).limit(1)

        # Executing the query
        results = await self.db.execute(query)
        question_obj = results.scalar_one_or_none()

        if question_obj:
            logger.info(f"Database: Found a question for combo {topic} + {level}: {question_obj.question_id}")
            return question_obj
        logger.warning(f"Database: No more questions available for combo {topic} + {level}")
        return None


    # Inserting bulk list of the "Question" object for the worker to call
    async def create_many(self, bulk_questions: list[Question]) -> list[Question]:
        logger.info("Database: Creating bulk questions for the worker")
        self.db.add_all(bulk_questions)
        await self.db.commit()
        logger.info(f"Database: Succesfully created {len(bulk_questions)} questions for the worker")
        return bulk_questions


