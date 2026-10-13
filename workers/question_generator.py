import asyncio
import logging

from core.database import AsyncSessionLocal
from core.enums import Levels, Topics
from core.config import settings
from core.gemini import QuestionGenerationFailed, generate_structured_data
from repositories.question_repository import QuestionRepository
from schemas.question_schema import QuestionBatch
from services.question_service import QuestionService


logger = logging.getLogger("worker")


def build_prompt(topic: Topics, level: Levels, count: int) -> str: 
    logger.info(f"Worker: Generating {count} questions for topic: {topic.value} and level: {level.value}") 
    
    return f'''You are generating multiple-choice quiz questions for an adaptive learning app. 

Task: Generate exactly {count} questions on the topic of "{topic.value}" at "{level.value}" difficulty. 

Difficulty guidance: 
- Easy: well-known facts a casual player would know. 
- Medium: requires some familiarity with the topic. 
- Hard: obscure details that would challenge an enthusiast. 

Format requirements for each question: 
- One clear question sentence. 
- Exactly 4 answer options. 
- Exactly 1 option must be correct. 
- The correct_answer value must match one of the four options character for character. 
- Include one short, interesting fact related to the answer (1-2 sentences). 

Quality requirements: 
- All {count} questions must be distinct. No duplicates or near-duplicates. 
- Wrong options must be plausible, not obviously wrong. 
- Avoid phrasing that gives away the answer. 
- Vary question phrasing across the set. 
- The fact must be genuinely interesting, not restate the answer. 

Topic scope: Stay strictly within "{topic.value}". Do not drift into related topics.'''


async def run_worker():
    combos = [(t, l) for t in Topics for l in Levels]

    try:
        while True:
            async with AsyncSessionLocal() as db:
                repo = QuestionRepository(db)
                service = QuestionService(repo)
                
                for t, l in combos:
                    count = await service.count_by_topic_level(topic=t, level=l)

                    if count < settings.POOL_THRESHOLD:
                        needed = settings.POOL_TARGET - count
                        logger.info(f"Worker: Generating {needed} questions for topic: {t} and level: {l}")
                        await asyncio.sleep(20.0)

                        try:
                            prompt = build_prompt(t, l, needed)
                            batch = await generate_structured_data(prompt=prompt, response_schema=QuestionBatch)
                            questionss = await service.create_questions(data=batch.questions, topic=t, level=l)
                            logger.info(f"Worker: Generated {len(batch.questions)} questions {len(questionss)} for topic: {t} and level: {l}")

                        except QuestionGenerationFailed as e:
                            logger.error(f"Worker: Failed to generate questions for topic: {t} and level: {l}. Error: {e}")

                logger.info(f"Worker: Loop finishied. Waiting for next iteration in {settings.POOL_INTERVAL_SECONDS} seconds...")

            await asyncio.sleep(settings.POOL_INTERVAL_SECONDS)

    except asyncio.CancelledError:
        logger.info("Worker: Worker loop cancelled. Exiting...")