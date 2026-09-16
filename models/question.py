import uuid

from sqlalchemy import Uuid, Enum
from core.database import Base
from sqlalchemy.orm import Mapped, mapped_column

from core.enums import Levels, Topics


class Question(Base):
    __tablename__ = 'question'

    question_id: Mapped[uuid.UUID] = mapped_column(
            Uuid(as_uuid=True), 
            primary_key=True, 
            default=uuid.uuid4
        )
    question: Mapped[str] = mapped_column(nullable=False)

    answer1: Mapped[str] = mapped_column(nullable=False)
    answer2: Mapped[str] = mapped_column(nullable=False)
    answer3: Mapped[str] = mapped_column(nullable=False)
    answer4: Mapped[str] = mapped_column(nullable=False)

    correct_answer: Mapped[str] = mapped_column(nullable=False) 

    topic: Mapped[Topics] = mapped_column(Enum(Topics, native_enum=False), nullable=False)
    level: Mapped[Levels] = mapped_column(Enum(Levels, native_enum=False), nullable=False)
    fact: Mapped[str] = mapped_column(nullable=False)




