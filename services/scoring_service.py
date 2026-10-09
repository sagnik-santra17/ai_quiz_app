import logging
import uuid

from fastapi import HTTPException, status

from repositories.attempt_repository import AttemptRepository
from repositories.session_repository import SessionRepository
from schemas.session_schema import SessionResult, WeakPoint


logger = logging.getLogger(__name__)


class ScoringService:
    def __init__(
        self, 
        attempt_repo: AttemptRepository,
        session_repo: SessionRepository
    ):
        self.attempt_repo = attempt_repo
        self.session_repo = session_repo


    # Getting the session result
    async def calculate_session_result(self, session_id: uuid.UUID) -> SessionResult:

        logger.info(f"Service: Attempting to calculate session result for session id: {session_id}")
        # Getting the session
        session = await self.session_repo.get_session_by_id(session_id=session_id)

        if not session:
            logger.warning(f"Service: Session not found for session id: {session_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session doesn't exists"
            )
        
        # Calling the query for getting the attempt with the topic
        rows = await self.attempt_repo.get_attempts_with_topic(session_id=session_id)
        logger.info(f"Service: Retrieved {len(rows)} attempts for session id: {session_id}")

        # Calculating the basline metrics
        total_questions = len(rows)
        correct_count = sum(1 for row in rows if row["is_correct"])
        accuracy = correct_count / total_questions if total_questions > 0 else 0.0

        # Getting the topic and result summary
        topic_summary = {}

        for row in rows:
            topic = row["topic"]
            is_correct = row["is_correct"]

            if topic not in topic_summary:
                topic_summary[topic] = {"missed": 0, "total": 0}

            topic_summary[topic]["total"] += 1

            if not is_correct:
                topic_summary[topic]["missed"] += 1

        # Transforming the topic summary in a list for the weak points
        weak_points = [
            WeakPoint(topic=topic, missed=stats["missed"], total=stats["total"])
            for topic, stats in topic_summary.items()
        ]

        # Returning the session result
        logger.info(
            f"Service: Calculated result for session id: {session_id} — correct: {correct_count}/{total_questions}, accuracy: {accuracy}"
        )

        # Mapping fields directly from the fetched model
        return SessionResult(
            session_id=session.session_id,  
            player_name=session.player_name,
            level=session.level,
            topic=session.topic,
            started_at=session.started_at,
            ended_at=session.ended_at,
            total_questions=total_questions,
            correct_count=correct_count,
            accuracy=accuracy,
            weak_points=weak_points
        )



    