import uuid

from pydantic import BaseModel, Field


class AttemptCreate(BaseModel):
    question_id: uuid.UUID
    selected_answer: str


class AttemptResponse(BaseModel):
    selected_answer: str
    is_correct: bool
    correct_answer: str
    fact: str
