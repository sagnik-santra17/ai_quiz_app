import logging

from sqlalchemy.ext.asyncio import AsyncSession




logger = logging.getLogger(__name__)


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db


    # Creating session
    """async def create(self, session: )"""