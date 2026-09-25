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
        logger.info(f"Service: Generated quesitons: {len(generated_questions)}")
        return generated_questions
