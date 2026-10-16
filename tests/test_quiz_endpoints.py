import pytest_asyncio
import uuid
    
from models.question import Question
from tests.conftest import db_session

# ------ Utils --------- #
#Player data
player_data = {
    "player_name": "Alex",
    "level": "easy",
    "topic": "history"
}

# Session id
@pytest_asyncio.fixture(scope="function")
async def quiz_setup(client, db_session):
    """
    Fixture that prepares a clean question and a fresh quiz session.
    """
    # Insert a mock question using your exact columns
    test_question = Question(
        topic="history",
        level="easy",
        question="Who was the first president of the United States?",
        answer1="George Washington",
        answer2="Thomas Jefferson",
        answer3="John Adams",
        answer4="Benjamin Franklin",
        correct_answer="George Washington",
        fact="George Washington was the only president unanimously elected."
    )
    db_session.add(test_question)
    await db_session.commit()
    await db_session.refresh(test_question)

    # Start the quiz session
    player_data = {
        "player_name": "Alex",
        "level": "easy",
        "topic": "history"
    }
    response = await client.post("/quiz/", json=player_data)
    assert response.status_code == 201
    session_id = response.json()["session_id"]

    # Return both items cleanly as a package
    return {
        "question_id": test_question.question_id,
        "session_id": session_id
    }


# ----- Happy paths --------- #

# Valid input → 201, session created with correct fields
async def test_start_session_success(client):
    response = await client.post("/quiz/", json=player_data)
    assert response.status_code == 201

    data = response.json()
    assert data["session_id"]
    assert data["player_name"] == player_data["player_name"]
    assert data["level"] == player_data["level"]
    assert data["topic"] == player_data["topic"]
    

# Valid session with stocked pool → 200, question returned
async def test_get_next_question_success(client, db_session, quiz_setup):
    # Insert a mock question using the exact model columns
    test_question = Question(
        topic="history",
        level="easy",
        question="Who was the first president of the United States?",
        answer1="George Washington",
        answer2="Thomas Jefferson",
        answer3="John Adams",
        answer4="Benjamin Franklin",
        correct_answer="George Washington",
        fact="George Washington was the only president unanimously elected."
    )
    
    db_session.add(test_question)
    await db_session.commit()  # Save it into the clean test database context
    
    # Fetch the next question using GET
    sid = quiz_setup["session_id"]
    response = await client.get(f"/quiz/{str(sid)}/next")
    assert response.status_code == 200
    
    data = response.json()
    assert data["question_id"]
    assert data["question"] == test_question.question


# Valid answer → 200, graded correctly, fact returned
async def test_record_attempt_success(client, quiz_setup):
    # Extract the data cleanly from our setup fixture package
    question_id = quiz_setup["question_id"]
    session_id = quiz_setup["session_id"]

    # Package the payload
    attempt_data = {
        "question_id": str(question_id),  # Convertng the UUID object to a text string
        "selected_answer": "George Washington"
    }
    
    # Submit the attempt via POST
    response = await client.post(f"/quiz/{session_id}/attempts", json=attempt_data)
    
    # Verify everything graded correctly and returned the fact
    assert response.status_code == 200
    
    response_data = response.json()
    assert response_data["is_correct"] is True
    assert response_data["fact"] == "George Washington was the only president unanimously elected."

    
# Valid session with attempts → 200, result with weak points
async def test_end_session_success(client, db_session):
    # Insert an explicit "history" question that the user will fail
    wrong_question = Question(
        topic="history",
        level="easy",
        question="In which year did World War II end?",
        answer1="1941",
        answer2="1943",
        answer3="1945",
        answer4="1950",
        correct_answer="1945",
        fact="World War II officially concluded on September 2, 1945."
    )
    db_session.add(wrong_question)
    await db_session.commit()
    await db_session.refresh(wrong_question)

    # Start a fresh quiz session
    player_data = {
        "player_name": "Alex",
        "level": "easy",
        "topic": "history"
    }
    session_response = await client.post("/quiz/", json=player_data)
    assert session_response.status_code == 201
    session_id = session_response.json()["session_id"]

    # Deliberately submit a wrong answer ("1941" instead of "1945") to create a weak point
    attempt_data = {
        "question_id": str(wrong_question.question_id),
        "selected_answer": "1941" 
    }
    attempt_response = await client.post(f"/quiz/{session_id}/attempts", json=attempt_data)
    assert attempt_response.status_code == 200

    # Request to wrap up the session and calculate final results
    response = await client.post(f"/quiz/{session_id}/end")
    
    # Verify the grading and weak point calculations
    assert response.status_code == 200
    
    result_data = response.json()
    assert "total_questions" in result_data
    
    # Verify using 'correct_count' to avoid the KeyError
    assert "correct_count" in result_data
    
    # Scan the array of weak point dictionaries to find the missed history topic
    assert "weak_points" in result_data
    assert any(wp["topic"] == "history" for wp in result_data["weak_points"])


# ----- Sad paths --------- #

# Bad topic value → 422
async def test_start_session_invalid_topic(client):
    invalid_data = {
        "player_name": "Alex",
        "level": "easy",
        "topic": "invalid_topic_name_here"  # Invalid topic to trigger validation error
    }
    
    response = await client.post("/quiz/", json=invalid_data)
    assert response.status_code == 422


# Bad level value → 422
async def test_start_session_invalid_level(client):
    invalid_data = {
        "player_name": "Alex",
        "level": "random_level", # Invalid Level to trigger validation error
        "topic": "geography"  
    }
    
    response = await client.post("/quiz/", json=invalid_data)
    assert response.status_code == 422


# Random session_id → 404
async def test_get_next_question_session_not_found(client):

    # Generate a random UUID to guarantee the session won't be found
    random_sid = str(uuid.uuid4())
    
    response = await client.get(f"/quiz/{random_sid}/next")
    assert response.status_code == 404


# Empty pool for combo → 503
async def test_get_next_question_pool_exhausted(client):
    # Start a fresh session with a unique combo that has no questions in the database
    empty_pool_player = {
        "player_name": "Alex",
        "level": "easy",
        "topic": "movies"
    }
    
    session_response = await client.post("/quiz/", json=empty_pool_player)
    assert session_response.status_code == 201
    session_id = session_response.json()["session_id"]
    
    response = await client.get(f"/quiz/{session_id}/next")
    assert response.status_code == 503


# Random session_id → 404
async def test_record_attempt_session_not_found(client):
    # Generate a random UUID to simulate a missing session context
    random_sid = str(uuid.uuid4())
    
    # Package a dummy attempt payload
    attempt_data = {
        "question_id": str(uuid.uuid4()),
        "selected_answer": "Any Answer"
    }
    
    response = await client.post(f"/quiz/{random_sid}/attempts", json=attempt_data)
    assert response.status_code == 404


# Random question_id → 404
async def test_record_attempt_question_not_found(client, quiz_setup):
    # Extract a real session ID from our setup package
    session_id = quiz_setup["session_id"]
    
    # Generate a random UUID for the question to simulate a missing question item
    random_qid = str(uuid.uuid4())
    
    attempt_data = {
        "question_id": random_qid,
        "selected_answer": "George Washington"
    }
    
    response = await client.post(f"/quiz/{session_id}/attempts", json=attempt_data)
    assert response.status_code == 404

# Same question twice in session → 409
async def test_record_attempt_duplicate(client, quiz_setup):
    question_id = quiz_setup["question_id"]
    session_id = quiz_setup["session_id"]
    
    attempt_data = {
        "question_id": str(question_id),
        "selected_answer": "George Washington"
    }
    
    # First attempt: Successfully recorded (200 OK)
    first_response = await client.post(f"/quiz/{session_id}/attempts", json=attempt_data)
    assert first_response.status_code == 200
    
    # Second attempt: Duplicate submission for the same question triggers conflict rule
    second_response = await client.post(f"/quiz/{session_id}/attempts", json=attempt_data)
    assert second_response.status_code == 409

# Random session_id → 404
async def test_end_session_not_found(client):
    # Generate a random UUID to ensure the session context does not exist
    random_sid = str(uuid.uuid4())
    
    response = await client.post(f"/quiz/{random_sid}/end")
    assert response.status_code == 404

# 31 requests in a minute → 429
async def test_rate_limit_exceeded(client):
    player_payload = {
        "player_name": "Alex",
        "level": "easy",
        "topic": "history"
    }
    
    # Fire off 30 successful or allowed requests to hit the threshold limit
    for _ in range(30):
        response = await client.post("/quiz/", json=player_payload)
        assert response.status_code in (201, 422)
        
    # The 31st request triggers the rate limiter rule
    throttled_response = await client.post("/quiz/", json=player_payload)
    assert throttled_response.status_code == 429