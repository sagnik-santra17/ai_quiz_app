import uuid

from typing import Self
from pydantic import BaseModel, ConfigDict, model_validator


class QuestionGenerated(BaseModel):
    question: str
    answer1: str
    answer2: str
    answer3: str
    answer4: str
    correct_answer: str
    fact: str

    @model_validator(mode='after')
    def check_answer_in_option(self) -> Self:
        options = [self.answer1, self.answer2, self.answer3, self.answer4]
        
        if self.correct_answer.strip().lower() not in options:
            raise ValueError(
                f"The correct_answer '{self.correct_answer}' must match one of the provided options."
            )
            
        return self


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    question_id: uuid.UUID
    question: str
    answer1: str
    answer2: str
    answer3: str
    answer4: str

