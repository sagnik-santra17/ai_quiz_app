import logging
import uuid

from core.enums import Levels, Topics
from models.question import Question
from repositories.question_repository import QuestionRepository
from schemas.question_schema import QuestionGenerated



logger = logging.getLogger(__name__)


class QuestionService:
    def __init__(self, repo: QuestionRepository):
        self.repo = repo


    # Creating a question
    async def create_questions(self, data: list[QuestionGenerated], topic: Topics, level: Levels) -> list[Question]:
        logger.info("Service: Attempting to create a question")
        new_questions = [Question(**item.model_dump(), topic=topic, level=level) for item in data]
        generated_questions = await self.repo.create_many(new_questions)
        logger.info(f"Service: Generated questions: {len(generated_questions)}")
        return generated_questions


    # Getting a question by its id
    async def get_question_by_id(self, question_id: uuid.UUID) -> Question | None:
        logger.info(f"Service: Attempting to find a question with question id: {question_id}")
        question = await self.repo.get_question_by_id(question_id=question_id)

        if question:
            return question
        logger.warning(f"Service: No question was found for the question id: {question_id}")
        return None


    # Returning how many questions are available with a topic and level combo
    async def count_by_topic_level(self, topic: Topics, level: Levels) -> int:
        logger.info(
            f"Service: Counting how many questions are available with this topic and level combo: {topic} + {level}"
        )
        return await self.repo.count_by_topic_level(topic=topic, level=level)

        
    # Excluding the already asked questions and returns a unique question
    async def get_random_excluding(self, topic: Topics, level: Levels, exclude_ids: list[uuid.UUID]) -> Question | None:
        logger.info(f"Service: Excluding questions that are already asked based on this combo: {topic} + {level}")

        unique_question = await self.repo.get_random_excluding(
            topic=topic, 
            level=level, 
            exclude_ids=exclude_ids
        )
        if unique_question:
            logger.info(f"Service: Found a question for combo {topic} + {level}: {unique_question.question_id}")
            return unique_question
        logger.warning(f"Service: No more questions available for combo {topic} + {level}")
        return None
        

