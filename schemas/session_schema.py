import uuid

from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime

from core.enums import Levels, Status, Topics


class SessionCreate(BaseModel):
    player_name: str = Field(..., min_length=1, max_length=50)
    level: Levels = Field(...)
    topic: Topics = Field(...)


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    session_id: uuid.UUID
    player_name: str
    level: Levels
    topic: Topics
    status: Status
    started_at: datetime


class WeakPoint(BaseModel): # -> For the wrong answers and AI suggestions for the player's weak points
    model_config = ConfigDict(from_attributes=True)
    topic: Topics
    missed: int
    total: int


class SessionResult(BaseModel): # -> For the ulitmate result that will be shown at the end of the quiz
    session_id: uuid.UUID
    player_name: str
    level: Levels
    topic: Topics
    correct_count: int
    total_questions: int
    accuracy: float
    started_at: datetime
    ended_at: datetime

    weak_points: list[WeakPoint]
