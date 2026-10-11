from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from core.database import get_db
from repositories.attempt_repository import AttemptRepository
from repositories.question_repository import QuestionRepository
from repositories.session_repository import SessionRepository
from services.question_service import QuestionService
from services.quiz_service import QuizService
from services.scoring_service import ScoringService


# ----- Main dependency ------ #
db_dependency = Annotated[AsyncSession, Depends(get_db)]


# ------ Question service dependency ------- #
def get_question_service(db: db_dependency) -> QuestionService:
    repo = QuestionRepository(db=db)
    return QuestionService(repo=repo)

question_service_dependency = Annotated[QuestionService, Depends(get_question_service)]


# ----- Quiz service dependency ------ #
def get_quiz_service(
    db: db_dependency,
) -> QuizService:
    
    attempt_repo = AttemptRepository(db=db)
    session_repo = SessionRepository(db=db)
    question_service = QuestionService(repo=QuestionRepository(db=db))
    scoring_service = ScoringService(attempt_repo=attempt_repo, session_repo=session_repo)
    return QuizService(
        attempt_repo=attempt_repo, 
        session_repo=session_repo, 
        question_service=question_service, 
        scoring_service=scoring_service
    )

quiz_service_dependency = Annotated[QuizService, Depends(get_quiz_service)]