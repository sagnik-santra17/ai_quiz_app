import logging
from google import genai
from google.genai import types
from google.genai import errors  
from openai import AsyncOpenAI
from pydantic import BaseModel

from core.config import settings

logger = logging.getLogger("app.llm")

class GeminiClientError(Exception):
    """Base exception for LLM infrastructure wrapper issues."""
    pass

class QuestionGenerationFailed(GeminiClientError):
    """Raised when BOTH Gemini and the Groq fallback fail to generate data."""
    pass

# Timeout settings
TIMEOUT_SECONDS = 30.0
TIMEOUT_MILLISECONDS = int(TIMEOUT_SECONDS * 1000)

try:
    gemini_client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=TIMEOUT_MILLISECONDS)
    )
    logger.info("Primary LLM Client initialized: Gemini.")
except Exception as e:
    raise RuntimeError(f"Failed to initialize primary Gemini Client: {e}")

groq_client = None

if hasattr(settings, "GROQ_API_KEY") and settings.GROQ_API_KEY:
    try:
        # Base URL to point directly to Groq's official OpenAI endpoint path
        groq_client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.GROQ_API_KEY,
            timeout=TIMEOUT_SECONDS
        )
        logger.info("Fallback LLM Client initialized: Groq.")
    except Exception as e:
        logger.error(f"Failed to initialize secondary Groq fallback client: {e}")
else:
    logger.warning("Groq configuration variables are completely absent. Degraded mode active: Fallback disabled.")


async def _generate_with_groq(prompt: str, response_schema: type[BaseModel]) -> BaseModel:
    """Helper method to invoke the secondary Groq fallback pipeline."""
    if not groq_client:
        raise QuestionGenerationFailed("Fallback option triggered, but Groq client was never successfully initialized.")

    logger.warning("Entering Fallback Pipeline: Route switching to Groq/OpenAI client...")
    
    # Try block order to prevent custom domain exceptions from being swallowed
    try:
        response = await groq_client.beta.chat.completions.parse(
            model=settings.LLM_MODEL,  
            messages=[
                {"role": "system", "content": "You are a precise technical interviewer that outputs structured JSON responses."},
                {"role": "user", "content": prompt}
            ],
            response_format=response_schema,
        )
    except Exception as groq_network_err:
        raise QuestionGenerationFailed(f"Failure: Both systems dropped connection. Groq error: {str(groq_network_err)}")

    # Outside the try block to avoid re-wrapping custom raised exceptions
    message = response.choices[0].message
    
    if hasattr(message, "refusal") and message.refusal:
         raise QuestionGenerationFailed(f"Groq safety filter system refused request: {message.refusal}")

    parsed_object = message.parsed
    if parsed_object is None:
        raise QuestionGenerationFailed("Groq completed successfully, but failed to unpack properties into the requested schema.")
    
    logger.info("Fallback execution completed successfully via Groq engine resource profiles.")
    return parsed_object


async def generate_structured_data(prompt: str, response_schema: type[BaseModel]) -> BaseModel:
    """
    Asynchronously sends a prompt to Gemini. 
    If Gemini throws an HTTP 429 or 503 error, it switches to Groq dynamically.
    """
    try:
        response = await gemini_client.aio.models.generate_content(
            model=settings.MODEL_NAME, 
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        
        if not response.text:
            raise QuestionGenerationFailed("Gemini returned an empty response or content was blocked.")

        parsed_object = response.parsed
        if parsed_object is None:
            raise QuestionGenerationFailed("Gemini SDK failed to unpack data into Pydantic schema.")

        return parsed_object

    except errors.APIError as gemini_error:
        # Targetting both 429 quota exhaustion and 503 overloads
        if gemini_error.code in (429, 503, 504):
            logger.warning(f"Gemini API interdiction hit (HTTP {gemini_error.code}). Activating Groq fallback mechanism...")
            return await _generate_with_groq(prompt, response_schema)
        
        raise QuestionGenerationFailed(f"Gemini API error ({gemini_error.code}): {str(gemini_error)}") from gemini_error

    except Exception as e:
        raise QuestionGenerationFailed(f"Gemini unexpected invocation crash: {str(e)}") from e
