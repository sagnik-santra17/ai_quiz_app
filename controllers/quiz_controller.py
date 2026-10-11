import uuid

from fastapi.routing import APIRouter
from fastapi import status

from schemas.attempt_schema import AttemptCreate, AttemptResponse
from schemas.question_schema import QuestionResponse
from schemas.session_schema import SessionCreate, SessionResponse, SessionResult
from core.dependencies import quiz_service_dependency

# FastAPI router
router = APIRouter(prefix="/quiz", tags=["quiz"])


# ------- Start session -------- #
@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SessionResponse)
async def start_session(
    session_data: SessionCreate, 
    service: quiz_service_dependency,
) -> SessionResponse:
    return await service.start_session(session_data=session_data)


# ------ Get next question ------- #
@router.get("/{session_id}/next", status_code=status.HTTP_200_OK, response_model=QuestionResponse)
async def get_next_question(
    session_id: uuid.UUID, 
    service: quiz_service_dependency
) -> QuestionResponse:
    return await service.get_next_question(session_id=session_id)


# ------- Record attempt -------- #
@router.post("/{session_id}/attempts", status_code=status.HTTP_200_OK, response_model=AttemptResponse)
async def record_attempt(
    session_id: uuid.UUID, 
    attempt_data: AttemptCreate, 
    service: quiz_service_dependency
) -> AttemptResponse:
    return await service.record_attempt(session_id=session_id, attempt_data=attempt_data)


# --------- End session -------- #
@router.post("/{session_id}/end", status_code=status.HTTP_200_OK, response_model=SessionResult)
async def end_session(
    session_id: uuid.UUID, 
    service: quiz_service_dependency
) -> SessionResult:
    return await service.end_session(session_id=session_id)
