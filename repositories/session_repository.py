import logging
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from core.enums import Status
from models.session import Session



logger = logging.getLogger(__name__)


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # Creating session
    async def create(self, session_obj: Session) -> Session:
        logger.info("Database: Attempting to start a new session")
        self.db.add(session_obj)
        await self.db.commit()
        await self.db.refresh(session_obj)
        logger.info(f"Database: Successfully created a session with session id: {session_obj.session_id}")
        return session_obj

    # Getting session with session ID
    async def get_session_by_id(self, session_id: uuid.UUID) -> Session | None:
        logger.info(f"Database: Attempting to find a session with session id: {session_id}")
        query = (
            select(Session)
            .where(Session.session_id == session_id)
        )
        results = await self.db.execute(query)
        session_obj = results.scalar_one_or_none()

        if not session_obj:
            logger.warning(f"Database: No session with session_id found: {session_id}")
        return session_obj

    # When the sesseion is ended by the user
    async def mark_ended_session(self, session_id: uuid.UUID) -> None:
        logger.info(f"Database: Attempting to update the session status: {session_id}")
        query = (
            update(Session)
            .where(Session.session_id == session_id)
            .values(
                status=Status.ENDED,
                ended_at=datetime.now(timezone.utc)
            )
        )
        await self.db.execute(query)
        await self.db.commit()
        logger.info(f"Database: Session status updated succesfully for session_id: {session_id}")


