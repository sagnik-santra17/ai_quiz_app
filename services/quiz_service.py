import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError  # Added to handle database unique constraints

from core.enums import Status
from models.attempt import Attempt
from models.question import Question
from models.session import Session
from repositories.attempt_repository import AttemptRepository
from repositories.session_repository import SessionRepository
from schemas.attempt_schema import AttemptCreate, AttemptResponse
from schemas.session_schema import SessionCreate, SessionResult
from services.question_service import QuestionService


logger = logging.getLogger(__name__)


class QuizService:
    def __init__(
        self,
        attempt_repo: AttemptRepository,
        session_repo: SessionRepository,
        question_service: QuestionService
    ):
        self.attempt_repo = attempt_repo
        self.session_repo = session_repo
        self.question_service = question_service

    # Private helper to fetch and validate an active session
    async def _get_active_session(self, session_id: uuid.UUID) -> Session:
        session = await self.session_repo.get_session_by_id(session_id=session_id)

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Session not found"
            )

        if session.status != Status.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session is not currently active"
            )
            
        return session


    # Creating a new quiz session
    async def start_session(self, session_data: SessionCreate) -> Session:
        logger.info("Service: Attempting to create the quiz session")
        session = Session(**session_data.model_dump())
        new_session = await self.session_repo.create(session_obj=session)
        logger.info(f"Service: Quiz session created successfully: Session ID: {new_session.session_id}")
        return new_session


    # Getting the next question
    async def get_next_question(self, session_id: uuid.UUID) -> Question:
        logger.info(f"Service: Attempting to get the next question for session id: {session_id}")

        # Use helper to get a verified active session
        session = await self._get_active_session(session_id)

        # Getting the excluded question ids
        excluded_ids = await self.attempt_repo.get_attempted_question_ids(session_id=session_id)

        # Getting a random question excluding the already attempted ones
        next_question = await self.question_service.get_random_excluding(
            topic=session.topic,
            level=session.level,
            exclude_ids=excluded_ids
        )

        if next_question is None:
            logger.warning(f"Service: Question pool exhausted for session id: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No more questions available for this topic and level"
            )

        logger.info(f"Service: Successfully got the next question for session id: {session_id}")
        return next_question


    # Recording a user's answer attempt
    async def record_attempt(self, session_id: uuid.UUID, attempt_data: AttemptCreate) -> AttemptResponse:
        logger.info(f"Service: Attempting to record answer for session id: {session_id}, question id: {attempt_data.question_id}")

        # 1. Fetch and verify the session using the private helper
        session = await self._get_active_session(session_id)

        # 2. Fetch the question and verify it exists
        question = await self.question_service.get_question_by_id(question_id=attempt_data.question_id)

        if not question:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found"
            )

        # Safety Check: Verify the question belongs to this session's topic and level
        if question.topic != session.topic or question.level != session.level:
            logger.warning(f"Service: Mismatched question {attempt_data.question_id} submitted for session {session_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The provided question does not match this session's topic or difficulty level"
            )

        # 3. Grade the answer
        is_correct = (attempt_data.selected_answer == question.correct_answer)

        # 4. Build the Attempt ORM object
        attempt_obj = Attempt(
            session_id=session_id,
            question_id=attempt_data.question_id,
            selected_answer=attempt_data.selected_answer,
            is_correct=is_correct
        )

        # Try inserting the attempt and catch unique constraint violations (double-submits)
        try:
            new_attempt = await self.attempt_repo.create(attempt_obj=attempt_obj)
        except IntegrityError:
            logger.warning(f"Service: Double-submit detected for session {session_id}, question {attempt_data.question_id}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted an answer for this question in this session."
            )

        # 5. Log and return symmetric final response
        logger.info(f"Service: Successfully recorded attempt for session id: {session_id}. Result: correct={is_correct}")
        
        return AttemptResponse(
            selected_answer=new_attempt.selected_answer,
            is_correct=new_attempt.is_correct,
            correct_answer=question.correct_answer,
            fact=question.fact
        )


    # Ending the session
    async def end_session(self, session_id: uuid.UUID) -> SessionResult:
        logger.info(f"QuizService: Attempting to end session: {session_id}")

        # Fetch session by ID directly (avoiding helper methods that block ended sessions)
        session = await self.session_repo.get_session_by_id(session_id=session_id)
        if not session:
            logger.warning(f"QuizService: End session failed. Session {session_id} not found.")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session doesn't exist"
            )

        # Check current state to handle retries and post-failure recoveries idempotently
        if session.ended_at is not None:
            logger.info(
                f"QuizService: Session {session_id} is already ended (ended_at: {session.ended_at}). "
                f"Proceeding directly to re-score."
            )
        else:
            # First-time ending: Transition state to ended in the database
            logger.info(f"QuizService: Marking session {session_id} as ended.")
            await self.session_repo.mark_ended_session(session_id=session_id)

        # Calculate metrics and build the final result profile
        try:
            result = await self.scoring_service.calculate_session_result(session_id=session_id)
            return result
            
        except HTTPException:
            raise
            
        except Exception as e:
            logger.error(f"QuizService: Unexpected failure while calculating score profile for session {session_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session closed successfully, but analytics calculation failed. Please retry."
            )