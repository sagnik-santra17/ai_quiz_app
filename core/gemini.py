from google import genai
from google.genai import types
from pydantic import BaseModel

from core.config import settings


# Clean Domain Exceptions for the Infrastructure Layer
class GeminiClientError(Exception):
    """Base exception for Gemini client wrapper issues."""
    pass

class QuestionGenerationFailed(GeminiClientError):
    """Raised when Gemini fails to return or parse valid structured data."""
    pass


try:
    # Initialize the client synchronously at startup
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Gemini Client: {e}")


async def generate_structured_data(prompt: str, response_schema: type[BaseModel]) -> BaseModel:
    try:
        # Use client.aio to yield control back to the FastAPI / Worker event loop
        response = await client.aio.models.generate_content(
            model='gemini-3.8-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
    except Exception as e:
        # Propagate domain errors so the background worker or API router can handle them
        raise QuestionGenerationFailed(f"Gemini API invocation failed: {str(e)}") from e

    # Guard against missing, empty, or blocked responses
    if not response.text:
         raise QuestionGenerationFailed("Gemini returned an empty response or content was blocked.")

    # Access the clean parsed Pydantic object directly provided by the google-genai SDK
    parsed_object = response.parsed
    
    if parsed_object is None:
        raise QuestionGenerationFailed(
            "Gemini returned text, but the SDK failed to unpack it into the requested Pydantic schema."
        )

    return parsed_object
