from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from google.genai import errors

from core.llm import generate_structured_data, QuestionGenerationFailed, gemini_client, groq_client
from schemas.question_schema import QuestionBatch


@pytest.mark.asyncio
@patch.object(gemini_client.aio.models, "generate_content")
async def test_happy_path_gemini_succeeds(mock_gemini_generate):
    """Test the Happy Path. Gemini succeeds, Groq is never invoked."""
    # Instantiate a fake QuestionBatch to serve as our expected return value
    fake_question_batch = QuestionBatch(questions=[])

    # Setup the Gemini mock response following the google-genai response object structure
    mock_response = MagicMock()
    mock_response.text = '{"questions": []}'
    mock_response.parsed = fake_question_batch

    mock_gemini_generate.return_value = mock_response

    with patch.object(groq_client.beta.chat.completions, "parse") as mock_groq_parse:
        # Act
        result = await generate_structured_data("Prompt", QuestionBatch)

        # Assert
        assert result == fake_question_batch
        mock_gemini_generate.assert_called_once()
        mock_groq_parse.assert_not_called()


@pytest.mark.asyncio
@patch.object(gemini_client.aio.models, "generate_content")
async def test_fallback_gemini_fails_groq_succeeds(mock_gemini_generate):
    """Test Fallback. Gemini throws 503, Groq succeeds."""
    fake_question_batch = QuestionBatch(questions=[])

    # Create a REAL APIError instance with code 503
    fake_error = errors.APIError(503, "Service Unavailable")
    mock_gemini_generate.side_effect = fake_error

    # Replicate Groq's nested response path
    mock_groq_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.parsed = fake_question_batch
    mock_choice.message.refusal = None  # Explicitly set refusal to None so it doesn't trigger a false positive
    mock_groq_response.choices = [mock_choice]

    with patch.object(groq_client.beta.chat.completions, "parse", new_callable=AsyncMock) as mock_groq_parse:
        mock_groq_parse.return_value = mock_groq_response

        # Act
        result = await generate_structured_data("Prompt", QuestionBatch)

        # Assert
        assert result == fake_question_batch
        mock_gemini_generate.assert_called_once()
        mock_groq_parse.assert_called_once()


@pytest.mark.asyncio
@patch.object(gemini_client.aio.models, "generate_content")
async def test_catastrophic_failure_both_fail(mock_gemini_generate):
    """Test Catastrophic Failure. Both LLMs fail, raises QuestionGenerationFailed."""
    # Setup Gemini 503 Exception
    fake_error = errors.APIError(503, "Service Unavailable")
    mock_gemini_generate.side_effect = fake_error

    with patch.object(groq_client.beta.chat.completions, "parse", new_callable=AsyncMock) as mock_groq_parse:
        # Setup Groq generic fallback failure
        mock_groq_parse.side_effect = Exception("Groq is down too")

        # Act & Assert
        with pytest.raises(QuestionGenerationFailed):
            await generate_structured_data("Prompt", QuestionBatch)