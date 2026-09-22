import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.attempt import Attempt


logger = logging.getLogger(__name__)


class AttemptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    # Creating an attempt
    async def create(self, attempt_obj: Attempt) -> Attempt:
        logger.info("Database: Attempting to create an attempt to answer a question")
        self.db.add(attempt_obj)
        await self.db.commit()
        logger.info(f"Database: Successfully created an attempt with attempt id: {attempt_obj.attempt_id}")
        return attempt_obj

    # Getting the question ids that were answered
    async def get_attempted_question_ids(self, session_id: uuid.UUID) -> list[uuid.UUID]:
        logger.info(f"Database: Attempting get the answered question ids for the session: {session_id}")
        query = (
            select(Attempt.question_id)
            .where(Attempt.session_id == session_id)
        )
        result = await self.db.execute(query)
        question_ids = result.scalars().all()
        logger.info(f"Database: {len(question_ids)} questions have been answered")
        return question_ids

    # Getting all the attempt rows for scoring
    async def get_attempts_by_session(self, session_id: uuid.UUID) -> list[Attempt]:
        logger.info(f"Database: Attempting get the attempt details for the session: {session_id}")
        query = (
            select(Attempt)
            .where(Attempt.session_id == session_id)
        )
        result = await self.db.execute(query)
        logger.info(f"Database: Successfully return the attempt rows for session id: {session_id}")
        return result.scalars().all()