from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import logging
import datetime

# Structured logging — visible in CloudWatch Log Groups
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SSNC Hello World")


class EchoRequest(BaseModel):
    message: str


HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hello World - SS&C</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      min-height: 100vh;
      background-color: #0d1117;
      font-family: Arial, sans-serif;
      color: #f0f6fc;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem;
    }
    h1 { font-size: 2.5rem; margin-bottom: 0.3rem; }
    .subtitle { color: #8b949e; margin-bottom: 2rem; font-size: 1rem; }
    .badge {
      display: inline-block;
      padding: 0.3rem 0.9rem;
      background: #238636;
      border-radius: 20px;
      font-size: 0.85rem;
      margin-bottom: 2rem;
    }
    .card {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 10px;
      padding: 1.5rem;
      width: 100%;
      max-width: 600px;
      margin-bottom: 1.5rem;
    }
    .card h2 { font-size: 1.1rem; margin-bottom: 1rem; color: #58a6ff; }
    .input-row { display: flex; gap: 0.5rem; }
    input[type="text"] {
      flex: 1;
      padding: 0.6rem 1rem;
      background: #0d1117;
      border: 1px solid #30363d;
      border-radius: 6px;
      color: #f0f6fc;
      font-size: 1rem;
    }
    input[type="text"]:focus { outline: none; border-color: #58a6ff; }
    button {
      padding: 0.6rem 1.2rem;
      background: #238636;
      color: white;
      border: none;
      border-radius: 6px;
      font-size: 1rem;
      cursor: pointer;
    }
    button:hover { background: #2ea043; }
    .response-box {
      margin-top: 1rem;
      padding: 0.8rem 1rem;
      background: #0d1117;
      border: 1px solid #238636;
      border-radius: 6px;
      color: #3fb950;
      font-size: 0.95rem;
      display: none;
    }
    .history-list { list-style: none; }
    .history-list li {
      padding: 0.6rem 0;
      border-bottom: 1px solid #21262d;
      font-size: 0.9rem;
      color: #8b949e;
    }
    .history-list li span { color: #f0f6fc; }
    .empty { color: #8b949e; font-size: 0.9rem; font-style: italic; }
  </style>
</head>
<body>
  <h1>Hello, World!</h1>
  <p class="subtitle">Deployed on AWS ECS Fargate via Terraform</p>
  <div class="badge">Running</div>

  <div class="card">
    <h2>Echo Playground</h2>
    <div class="input-row">
      <input type="text" id="msgInput" placeholder="Try: Hello World  or  Veerathorn" />
      <button onclick="sendMessage()">Send</button>
    </div>
    <div class="response-box" id="responseBox"></div>
  </div>

  <div class="card">
    <h2>Submission History</h2>
    <ul class="history-list" id="historyList">
      <li class="empty">No submissions yet.</li>
    </ul>
  </div>

  <script>
    const history = [];

    async function sendMessage() {
      const input = document.getElementById("msgInput");
      const msg = input.value.trim();
      if (!msg) return;

      const res = await fetch("/echo", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg }),
      });

      const data = await res.json();
      const box = document.getElementById("responseBox");
      box.style.display = "block";
      box.textContent = data.reply;

      // Add to history
      history.unshift({ input: msg, reply: data.reply, time: data.timestamp });
      renderHistory();
      input.value = "";
    }

    document.getElementById("msgInput").addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendMessage();
    });

    function renderHistory() {
      const list = document.getElementById("historyList");
      if (history.length === 0) {
        list.innerHTML = '<li class="empty">No submissions yet.</li>';
        return;
      }
      list.innerHTML = history.map(h =>
        `<li>[${h.time}] You: <span>${h.input}</span> → ${h.reply}</li>`
      ).join("");
    }
  </script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the interactive Hello World page."""
    return HTMLResponse(content=HTML_CONTENT, status_code=200)


@app.post("/echo")
async def echo(payload: EchoRequest, request: Request):
    """
    Accept a user message, log it, and return a response.
    All logs are captured by CloudWatch via ECS awslogs driver.
    """
    msg = payload.message.strip()
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    client_ip = request.client.host

    if msg.lower() == "hello world":
        reply = "Hello SS&C! 👋"
    elif msg.lower() == "veerathorn":
        reply = "Hi! It's me Veerathorn, Nice to meet you! 🙌"
    else:
        reply = "Please try one of the options: type 'Hello World' or 'Veerathorn'"

    # Structured log — visible in CloudWatch Log Groups → /ecs/ssnc-hello-world
    logger.info(
        "ECHO_REQUEST | ip=%s | input=%r | reply=%r",
        client_ip, msg, reply,
    )

    return {
        "reply": reply,
        "timestamp": timestamp,
    }


@app.get("/health")
def health():
    """Health check endpoint — used by ALB target group."""
    return {"status": "healthy"}
