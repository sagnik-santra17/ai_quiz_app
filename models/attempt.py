import uuid

from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Attempt(Base):
    __tablename__ = 'attempt'

    attempt_id: Mapped[uuid.UUID] = mapped_column(
            Uuid(as_uuid=True), 
            primary_key=True, 
            default=uuid.uuid4
        )
    session_id: Mapped[uuid.UUID] = mapped_column(
            Uuid(as_uuid=True), 
            ForeignKey('session.session_id'), 
            nullable=False
        )
    question_id: Mapped[uuid.UUID] = mapped_column(
            Uuid(as_uuid=True), 
            ForeignKey('question.question_id'), 
            nullable=False
        )

    selected_answer: Mapped[str] = mapped_column(nullable=False)
    is_correct: Mapped[bool] = mapped_column(nullable=False)

    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        UniqueConstraint(
            'session_id', 
            'question_id', 
            name='uq_session_question'
        ),
    )
