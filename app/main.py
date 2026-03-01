from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="SSNC Hello World")

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Hello World - SS&C</title>
  <style>
    body {
      margin: 0;
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      background-color: #0d1117;
      font-family: Arial, sans-serif;
      color: #f0f6fc;
    }
    .container { text-align: center; }
    h1 { font-size: 3rem; margin-bottom: 0.5rem; }
    p  { font-size: 1.2rem; color: #8b949e; }
    .badge {
      display: inline-block;
      margin-top: 1rem;
      padding: 0.4rem 1rem;
      background: #238636;
      border-radius: 20px;
      font-size: 0.9rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Hello, World!</h1>
    <p>Deployed on AWS ECS Fargate via Terraform</p>
    <div class="badge">Running</div>
  </div>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def root():
    """Serve the Hello World page."""
    return HTMLResponse(content=HTML_CONTENT, status_code=200)


@app.get("/health")
def health():
    """Health check endpoint — used by ALB target group."""
    return {"status": "healthy"}
