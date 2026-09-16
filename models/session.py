import uuid

from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, Uuid 
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.enums import Levels, Status, Topics



class Session(Base):
    __tablename__ = 'session'

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    player_name: Mapped[str] = mapped_column(nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    topic: Mapped[Topics] = mapped_column(Enum(Topics, native_enum=False), nullable=False)
    level: Mapped[Levels] = mapped_column(Enum(Levels, native_enum=False), nullable=False)
    status: Mapped[Status] = mapped_column(Enum(Status, native_enum=False), default=Status.ACTIVE)



