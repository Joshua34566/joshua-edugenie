const pageInfo = {
  ask: {
    label: "Ask anything", kicker: "LET’S GET CURIOUS", heading: "What’s on your mind?",
    title: "Make learning<br><span>feel a little simpler.</span>",
    subtitle: "Curious about something? Start with a question and we’ll figure it out together."
  },
  quiz: {
    label: "Generate a quiz", kicker: "A QUICK KNOWLEDGE CHECK", heading: "See what’s clicking.",
    title: "Make learning<br><span>feel a little simpler.</span>",
    subtitle: "Turn a topic into a few questions and find out what you already know."
  },
  path: {
    label: "Learning path", kicker: "A PLAN THAT FITS YOU", heading: "Take it one step at a time.",
    title: "Make learning<br><span>feel a little simpler.</span>",
    subtitle: "Pick a subject and we’ll map a clear route from first steps to confident practice."
  },
  summary: {
    label: "Summarize text", kicker: "THE IMPORTANT PARTS, CLEARLY", heading: "Make a long read lighter.",
    title: "Make learning<br><span>feel a little simpler.</span>",
    subtitle: "Bring a passage and pull out the main idea and details worth remembering."
  },
  recommend: {
    label: "Study suggestions", kicker: "YOUR NEXT SMALL WIN", heading: "Find a good next step.",
    title: "Make learning<br><span>feel a little simpler.</span>",
    subtitle: "Share what you’re working toward and get practical ideas for your next study session."
  }
};

const exampleCards = [
  { icon: "↗", title: "Which is the largest ocean?", mode: "ask", value: "Which is the largest ocean?" },
  { icon: "▤", title: "Quiz me on Pythagoras", mode: "quiz", value: "The Pythagorean theorem" },
  { icon: "⌘", title: "Plan my SQL learning", mode: "path", value: "SQL" }
];

const appState = { mode: "ask", quiz: null };
const toolForm = document.querySelector("#tool-form");
const resultArea = document.querySelector("#result-area");

async function refreshModeStatus() {
  const pill = document.querySelector("#mode-pill");
  const label = document.querySelector("#mode-label");
  try {
    const response = await fetch("/api/health");
    if (!response.ok) throw new Error("Status unavailable");
    const status = await response.json();
    const cloudEnabled = status.mode === "cloud";
    label.textContent = cloudEnabled ? "AI enabled" : "Local mode";
    pill.title = cloudEnabled ? `AI enabled · ${status.model}` : "Using built-in learning guides";
    pill.dataset.mode = cloudEnabled ? "cloud" : "local";
  } catch {
    label.textContent = "Local guide";
    pill.title = "Using built-in learning guides";
    pill.dataset.mode = "local";
  }
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function escapeLabel(value) {
  return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}

function levelSelect(id, selected = "High school") {
  return `<select class="form-control" id="${id}" name="${id}">
    <option${selected === "Beginner" ? " selected" : ""}>Beginner</option>
    <option${selected === "Middle school" ? " selected" : ""}>Middle school</option>
    <option${selected === "High school" ? " selected" : ""}>High school</option>
    <option${selected === "College" ? " selected" : ""}>College</option>
    <option${selected === "Advanced" ? " selected" : ""}>Advanced</option>
  </select>`;
}

function formField(label, id, control, hint = "") {
  return `<div class="form-field"><label class="field-label" for="${id}">${label}</label>${control}${hint ? `<p class="form-help">${hint}</p>` : ""}</div>`;
}

function formTemplate(mode) {
  const input = (id, placeholder, max = 300) => `<input class="form-control" id="${id}" name="${id}" maxlength="${max}" placeholder="${placeholder}" required>`;
  const select = (id, selected) => `<select class="form-control" id="${id}" name="${id}">${levelSelect(id, selected).replace(/^.*?<select[^>]*>/s, "").replace(/<\/select>.*$/s, "")}</select>`;
  const footer = `<div class="submit-row"><span class="submit-note">✨ &nbsp;Just a good place to start</span><button class="primary-button" type="submit"><span class="submit-label">Get a clear answer</span><span class="button-arrow">↗</span></button></div>`;
  if (mode === "ask") return `<form data-form="ask">
    ${formField("YOUR QUESTION", "question", input("question", "e.g. Why does the Moon change shape?", 2000))}
    <div class="form-row">${formField("EXPLAIN IT FOR", "level", select("level", "High school"))}<div></div></div>${footer}
    <div class="chip-row"><button type="button" class="idea-chip" data-prefill="question" data-value="Which is the largest ocean?">Oceans & rivers</button><button type="button" class="idea-chip" data-prefill="question" data-value="Can you explain the Pythagorean theorem with an example?">Pythagoras</button></div>
  </form>`;
  if (mode === "quiz") return `<form data-form="quiz">
    ${formField("TOPIC TO PRACTICE", "topic", input("topic", "e.g. The Pythagorean theorem"))}
    <div class="form-row">${formField("LEARNER LEVEL", "level", select("level", "High school"))}<div></div></div>${footer}
  </form>`;
  if (mode === "path") return `<form data-form="path">
    ${formField("WHAT WOULD YOU LIKE TO LEARN?", "subject", input("subject", "e.g. SQL, biology, creative writing"))}
    <div class="form-row">${formField("STARTING POINT", "level", select("level", "Beginner"))}${formField("HOURS EACH WEEK", "hours", `<input class="form-control" id="hours" name="hours" type="number" min="1" max="40" value="4" required>`)}</div>${footer}
  </form>`;
  if (mode === "summary") return `<form data-form="summary">
    ${formField("PASTE A PASSAGE", "text", `<textarea class="form-control" id="text" name="text" minlength="30" maxlength="16000" placeholder="Paste your notes, textbook passage, or article excerpt here…" required></textarea>`, "30–16,000 characters")}${footer}
  </form>`;
  return `<form data-form="recommend">
    ${formField("SUBJECT", "subject", input("subject", "e.g. SQL, world history, algebra"))}
    <div class="form-row">${formField("YOUR LEVEL", "level", select("level", "Beginner"))}${formField("YOUR GOAL", "goal", input("goal", "e.g. Build a portfolio project", 500))}</div>${footer}
  </form>`;
}

function renderSuggestions() {
  const host = document.querySelector("#suggestions");
  host.replaceChildren();
  exampleCards.forEach((card) => {
    const button = el("button", "suggestion");
    button.type = "button";
    button.dataset.mode = card.mode;
    button.dataset.value = card.value;
    button.innerHTML = `<span class="suggestion-icon" aria-hidden="true">${card.icon}</span><span class="suggestion-text">${escapeLabel(card.title)}</span><span class="suggestion-arrow">›</span>`;
    button.addEventListener("click", () => {
      setMode(card.mode);
      const target = document.querySelector(`#${card.mode === "ask" ? "question" : card.mode === "quiz" ? "topic" : "subject"}`);
      if (target) { target.value = card.value; target.focus(); }
    });
    host.append(button);
  });
}

function setMode(mode) {
  appState.mode = mode;
  appState.quiz = null;
  const info = pageInfo[mode];
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
  document.querySelector("#breadcrumb-current").textContent = info.label;
  document.querySelector("#page-title").innerHTML = info.title;
  document.querySelector("#page-subtitle").textContent = info.subtitle;
  document.querySelector("#tool-kicker").textContent = info.kicker;
  document.querySelector("#tool-heading").textContent = info.heading;
  toolForm.innerHTML = formTemplate(mode);
  resultArea.replaceChildren();
  toolForm.querySelector("form").addEventListener("submit", submitForm);
  toolForm.querySelectorAll("[data-prefill]").forEach((button) => button.addEventListener("click", () => {
    const input = document.querySelector(`#${button.dataset.prefill}`);
    input.value = button.dataset.value;
    input.focus();
  }));
  renderSuggestions();
}

function addMeta(host, label, mode) {
  const meta = el("div", "result-meta", label);
  const modeTag = el("span", "", mode === "cloud" ? "AI assisted" : "Local guide");
  meta.append(modeTag);
  host.append(meta);
}

async function submitForm(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const mode = form.dataset.form;
  const data = new FormData(form);
  const button = form.querySelector("button[type=submit]");
  const oldLabel = button.querySelector(".submit-label").textContent;
  button.disabled = true;
  button.querySelector(".submit-label").textContent = "Putting it together…";
  resultArea.replaceChildren();
  const loading = el("div", "loading");
  loading.append(el("span", "spinner"), document.createTextNode("A little thinking…"));
  resultArea.append(loading);
  let endpoint;
  let payload;
  if (mode === "ask") { endpoint = "/api/ask"; payload = { question: data.get("question"), level: data.get("level") }; }
  else if (mode === "quiz") { endpoint = "/api/quiz"; payload = { topic: data.get("topic"), level: data.get("level") }; }
  else if (mode === "path") { endpoint = "/api/learning-path"; payload = { subject: data.get("subject"), level: data.get("level"), hours_per_week: Number(data.get("hours")) }; }
  else if (mode === "summary") { endpoint = "/api/summarize"; payload = { text: data.get("text") }; }
  else { endpoint = "/api/recommendations"; payload = { subject: data.get("subject"), level: data.get("level"), goal: data.get("goal") }; }
  try {
    const response = await fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail?.[0]?.msg || "That didn’t work. Please check the form and try again.");
    resultArea.replaceChildren();
    if (mode === "ask") renderAnswer(result);
    if (mode === "quiz") renderQuiz(result);
    if (mode === "path") renderPath(result);
    if (mode === "summary") renderSummary(result);
    if (mode === "recommend") renderRecommendations(result);
  } catch (error) {
    resultArea.replaceChildren(el("div", "error-box", error.message || "Couldn’t reach EduGenie. Please try again."));
  } finally {
    button.disabled = false;
    button.querySelector(".submit-label").textContent = oldLabel;
  }
}

function renderAnswer(result) {
  addMeta(resultArea, "A CLEAR ANSWER", result.mode);
  const card = el("div", "answer-card");
  card.append(el("p", "result-copy", result.answer));
  resultArea.append(card);
}

function renderQuiz(result) {
  appState.quiz = result;
  addMeta(resultArea, `${result.topic} · QUICK QUIZ`, result.mode);
  result.questions.forEach((item, index) => {
    const card = el("section", "quiz-question");
    card.append(el("p", "question-title", `${index + 1}. ${item.question}`));
    if (item.choices?.length) {
      const options = el("div", "quiz-options");
      item.choices.forEach((choice, choiceIndex) => {
        const label = el("label", "quiz-option");
        const radio = document.createElement("input");
        radio.type = "radio"; radio.name = `answer-${index}`; radio.value = String(choiceIndex);
        label.append(radio, document.createTextNode(choice));
        options.append(label);
      });
      card.append(options);
    } else {
      const answer = document.createElement("textarea");
      answer.className = "form-control"; answer.rows = 2; answer.placeholder = "Write a few thoughts…";
      card.append(answer);
    }
    card.append(el("p", "quiz-feedback", ""));
    resultArea.append(card);
  });
  const objective = result.questions.some((item) => Number.isInteger(item.answer));
  if (objective) {
    const check = el("button", "primary-button", "Check my answers");
    check.type = "button";
    check.addEventListener("click", () => checkQuiz(result));
    const row = el("div", "submit-row"); row.append(el("span", "submit-note", "No rush — take your time."), check);
    resultArea.append(row);
  } else {
    resultArea.append(el("div", "result-note", "These are reflection prompts. There’s no fixed answer key in local mode, so use them to explain the topic in your own words."));
  }
}

function checkQuiz(result) {
  let correct = 0;
  let answered = 0;
  let gradable = 0;
  result.questions.forEach((item, index) => {
    if (!Number.isInteger(item.answer)) return;
    gradable += 1;
    const selected = document.querySelector(`input[name="answer-${index}"]:checked`);
    const question = document.querySelectorAll(".quiz-question")[index];
    const feedback = question.querySelector(".quiz-feedback");
    if (!selected) {
      feedback.className = "quiz-feedback incorrect";
      feedback.textContent = "Choose an answer to check this one.";
      return;
    }
    answered += 1;
    const isCorrect = Number(selected.value) === item.answer;
    if (isCorrect) correct += 1;
    feedback.className = `quiz-feedback ${isCorrect ? "correct" : "incorrect"}`;
    feedback.textContent = `${isCorrect ? "That’s right." : `The answer is ${item.choices[item.answer]}.`} ${item.explanation}`;
  });
  let score = document.querySelector(".quiz-score");
  if (!score) { score = el("div", "quiz-score"); resultArea.append(score); }
  score.textContent = answered < gradable
    ? `You’ve answered ${answered} of ${gradable}. Keep going when you’re ready.`
    : `You got ${correct} out of ${gradable}. Read the notes above, then give it another try if you like.`;
}

function renderPath(result) {
  addMeta(resultArea, result.title || "YOUR LEARNING PATH", result.mode);
  if (result.timeframe) resultArea.append(el("p", "result-copy", result.timeframe));
  (result.stages || []).forEach((stage, index) => {
    const card = el("article", "path-stage");
    const top = el("div", "path-stage-top");
    top.append(el("span", "stage-number", String(index + 1)), el("h3", "", stage.title || `Step ${index + 1}`));
    if (stage.duration) top.append(el("span", "stage-duration", stage.duration));
    card.append(top);
    const topics = el("div", "stage-topics");
    (stage.topics || []).forEach((topic) => topics.append(el("span", "topic-tag", topic)));
    card.append(topics);
    if (stage.project) {
      const project = el("p", "stage-project");
      project.append(el("strong", "", "Try this: "), document.createTextNode(stage.project));
      card.append(project);
    }
    resultArea.append(card);
  });
  if (result.note) resultArea.append(el("div", "result-note", result.note));
}

function renderSummary(result) {
  addMeta(resultArea, "YOUR STUDY NOTES", result.mode);
  const card = el("div", "answer-card");
  card.append(el("p", "result-copy", result.summary));
  resultArea.append(card);
  if (result.key_points?.length) {
    resultArea.append(el("p", "field-label", "KEY POINTS TO REMEMBER"));
    const list = el("ul", "keypoint-list");
    result.key_points.forEach((point) => list.append(el("li", "", point)));
    resultArea.append(list);
  }
  if (result.mode === "local") resultArea.append(el("div", "result-note", "Local mode selects the most relevant sentences from your passage. Connect an AI model for a rewritten summary."));
}

function renderRecommendations(result) {
  addMeta(resultArea, `IDEAS FOR ${result.subject}`, result.mode);
  result.items.forEach((item) => {
    const card = el("article", "recommendation");
    const top = el("div", "path-stage-top"); top.append(el("h3", "", item.title || "A next step"));
    if (item.time) top.append(el("span", "rec-time", item.time));
    card.append(top);
    if (item.why) card.append(el("p", "", item.why));
    if (item.action) card.append(el("p", "action-line", item.action));
    resultArea.append(card);
  });
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => setMode(button.dataset.mode)));
document.querySelector(".help-button").addEventListener("click", () => {
  const existing = document.querySelector(".about-popover");
  if (existing) { existing.remove(); return; }
  const popover = el("div", "about-popover", "EduGenie helps you ask questions, practice a topic, organize a learning path, and turn long passages into study notes. Add an OpenAI-compatible API key to enable cloud AI; submitted content then goes to that configured provider. Local guides work without one.");
  document.querySelector(".topbar").append(popover);
});

refreshModeStatus();

setMode("ask");
fetch("/api/health").then((response) => response.json()).then((health) => {
  const label = document.querySelector("#mode-label");
  label.textContent = health.mode === "cloud" ? "Cloud configured" : "Local mode";
  document.querySelector(".mode-dot").style.background = health.mode === "cloud" ? "#579268" : "#c79965";
}).catch(() => {});

