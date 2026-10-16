const startScreen = document.getElementById("start-screen");
const quizScreen = document.getElementById("quiz-screen");
const endScreen = document.getElementById("end-screen");
const startForm = document.getElementById("start-form");
const playerNameInput = document.getElementById("player-name");
const topicSelect = document.getElementById("topic");
const levelSelect = document.getElementById("level");
const questionTopicElement = document.getElementById("question-topic");
const questionElement = document.getElementById("question");
const answersElement = document.getElementById("answers");
const nextQuestionButton = document.getElementById("next-question");
const quitButton = document.getElementById("quit");
const resultElement = document.getElementById("result");
const playAgainButton = document.getElementById("play-again");

let sessionId = null;
let currentQuestion = null;
let topic = null;
let level = null;
const answerButtons = [];

function showScreen(name) {
  startScreen.style.display = "none";
  quizScreen.style.display = "none";
  endScreen.style.display = "none";

  switch (name) {
    case "start":
      startScreen.style.display = "block";
      break;
    case "quiz":
      quizScreen.style.display = "block";
      break;
    case "end":
      endScreen.style.display = "block";
      break;
  }
}

function showFeedback(isCorrect, correctAnswer, fact) {
  const feedbackDiv = document.createElement("div");
  feedbackDiv.id = "feedback-box";
  // EDIT 1: Inject class based on accuracy for styling
  feedbackDiv.className = isCorrect ? "feedback-correct" : "feedback-wrong";

  if (isCorrect) {
    feedbackDiv.textContent = "Correct!";
  } else {
    feedbackDiv.textContent = `Wrong. The answer was: ${correctAnswer}`;
  }

  feedbackDiv.textContent += `\n${fact}`;
  answersElement.appendChild(feedbackDiv);
}

function clearFeedback() {
  const feedbackDiv = document.getElementById("feedback-box");
  if (feedbackDiv) {
    feedbackDiv.remove();
  }
}

async function getQuestion() {
  if (!sessionId) {
    console.error("No session ID");
    return;
  }

  try {
    const response = await fetch(`/quiz/${sessionId}/next`);
    if (!response.ok) {
      if (response.status === 503) {
        alert("No questions available for this topic yet. Try another.");
        showScreen("start");
        return;
      }
      alert("Something went wrong.");
      return;
    }

    const data = await response.json();
    currentQuestion = data;

    questionTopicElement.textContent = topic;
    questionElement.textContent = currentQuestion.question;

    answersElement.innerHTML = "";
    // FIX 1: Clear the answerButtons array so it doesn't grow indefinitely
    answerButtons.length = 0;

    for (let i = 1; i <= 4; i++) {
      const answer = currentQuestion[`answer${i}`];
      const button = document.createElement("button");
      button.textContent = answer;
      button.addEventListener("click", () => submitAnswer(answer));
      answersElement.appendChild(button);
      answerButtons.push(button);
    }

    nextQuestionButton.style.display = "none";
  } catch (error) {
    console.error(error);
  }
}

async function submitAnswer(selectedAnswer) {
  if (!sessionId) {
    console.error("No session ID");
    return;
  }

  try {
    const response = await fetch(`/quiz/${sessionId}/attempts`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question_id: currentQuestion.question_id,
        selected_answer: selectedAnswer, // Fixed typo from selected_answer to selectedAnswer
      }),
    });

    if (!response.ok) {
      alert("Failed to submit answer.");
      return;
    }

    const data = await response.json();
    showFeedback(data.is_correct, data.correct_answer, data.fact);

    answerButtons.forEach((button) => {
      button.disabled = true;
    });

    nextQuestionButton.style.display = "block";
  } catch (error) {
    console.error(error);
  }
}

startForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  topic = topicSelect.value;
  level = levelSelect.value;

  try {
    const response = await fetch("/quiz/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        player_name: playerNameInput.value,
        topic,
        level,
      }),
    });

    if (!response.ok) {
      alert("Failed to start quiz.");
      return;
    }

    const data = await response.json();
    sessionId = data.session_id;
    showScreen("quiz");
    await getQuestion();
  } catch (error) {
    console.error(error);
  }
});

nextQuestionButton.addEventListener("click", async () => {
  clearFeedback();
  await getQuestion();
});

quitButton.addEventListener("click", async () => {
  try {
    const response = await fetch(`/quiz/${sessionId}/end`, {
      method: "POST",
    });

    if (!response.ok) {
      alert("Failed to end quiz session.");
      return;
    }

    const data = await response.json();

    // FIX 2: Format accuracy as a percentage
    const formattedAccuracy = Math.round(data.accuracy * 100) + "%";

    // EDIT 2: Wrap each weak point object into a styled <span> pill structure instead of joining with <br>
    const weakPointsText =
      data.weak_points && data.weak_points.length > 0
        ? data.weak_points
            .map(
              (wp) =>
                `<span>${wp.topic}: missed ${wp.missed} of ${wp.total}</span>`,
            )
            .join(" ")
        : "<span>None!</span>";

    resultElement.innerHTML = `
      <p>Score: ${data.correct_count} / ${data.total_questions}</p>
      <p>Accuracy: ${formattedAccuracy}</p>
      <p>Weak Points:</p>
      ${weakPointsText}
    `;

    showScreen("end");
  } catch (error) {
    console.error(error);
  }
});

// FIX 4 & 5: Added missing play-again handler and verified full code completion
playAgainButton.addEventListener("click", () => {
  sessionId = null;
  currentQuestion = null;
  topic = null;
  level = null;

  startForm.reset();
  answersElement.innerHTML = "";
  questionElement.textContent = "";
  questionTopicElement.textContent = "";

  showScreen("start");
});
