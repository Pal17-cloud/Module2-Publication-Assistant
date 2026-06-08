"""
app.py — FastAPI Web Application
==================================
Provides a simple web interface for the Publication Assistant pipeline.
Users can submit a GitHub repository URL and optimization goal through
a browser form and receive the generated README instantly.

Usage:
    uvicorn app:app --reload
    Then open: http://localhost:8000
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse

load_dotenv()

app = FastAPI(
    title="Publication Assistant",
    description="A Multi-Agent System for Automated Documentation Optimization",
    version="1.0.0",
)

INPUT_FORM = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Publication Assistant</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }}
        .card {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 2.5rem;
            width: 100%;
            max-width: 600px;
        }}
        h1 {{ font-size: 1.5rem; color: #f0f6fc; margin-bottom: 0.5rem; }}
        .subtitle {{ color: #8b949e; font-size: 0.9rem; margin-bottom: 2rem; }}
        label {{
            display: block;
            font-size: 0.85rem;
            font-weight: 600;
            color: #8b949e;
            margin-bottom: 0.4rem;
            margin-top: 1.2rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        input {{
            width: 100%;
            padding: 0.75rem 1rem;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            color: #c9d1d9;
            font-size: 0.95rem;
            outline: none;
        }}
        input:focus {{ border-color: #58a6ff; }}
        .hint {{ font-size: 0.78rem; color: #6e7681; margin-top: 0.3rem; }}
        .error {{
            background: #3d1a1a;
            border: 1px solid #f85149;
            border-radius: 8px;
            padding: 0.75rem 1rem;
            color: #f85149;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }}
        button {{
            width: 100%;
            margin-top: 1.8rem;
            padding: 0.85rem;
            background: #238636;
            border: none;
            border-radius: 8px;
            color: #fff;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
        }}
        button:hover {{ background: #2ea043; }}
        .badge {{
            display: inline-block;
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 20px;
            padding: 0.2rem 0.7rem;
            font-size: 0.75rem;
            color: #8b949e;
            margin-right: 0.4rem;
            margin-bottom: 1.5rem;
        }}
    </style>
</head>
<body>
    <div class="card">
        <h1>Publication Assistant</h1>
        <p class="subtitle">A Multi-Agent System for Automated Documentation Optimization</p>
        <span class="badge">LangGraph</span>
        <span class="badge">GPT-4o</span>
        <span class="badge">MIT License</span>
        {error_block}
        <form method="post" action="/generate" onsubmit="return validateForm()">
            <label for="url">GitHub Repository URL</label>
            <input
                type="text"
                id="url"
                name="url"
                placeholder="https://github.com/username/repository"
                value="{url_value}"
                required
            />
            <p class="hint">Must be a public GitHub repository URL.</p>
            <label for="goal">Optimization Goal</label>
            <input
                type="text"
                id="goal"
                name="goal"
                placeholder="e.g. Optimize for senior computer vision researchers"
                value="{goal_value}"
            />
            <p class="hint">Describe your target audience. Leave blank for general optimization.</p>
            <button type="submit">Generate README</button>
        </form>
    </div>
    <script>
        function validateForm() {{
            const url = document.getElementById('url').value.trim();
            if (!url) {{
                alert('Please enter a GitHub repository URL.');
                return false;
            }}
            if (!url.startsWith('http://') && !url.startsWith('https://')) {{
                alert('URL must start with http:// or https://');
                return false;
            }}
            if (!url.includes('github.com')) {{
                alert('Please enter a valid GitHub URL containing github.com');
                return false;
            }}
            return true;
        }}
    </script>
</body>
</html>
"""

RESULT_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Publication Assistant Result</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 2rem;
        }}
        .header {{
            max-width: 900px;
            margin: 0 auto 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        h1 {{ font-size: 1.3rem; color: #f0f6fc; }}
        .back-btn {{
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 0.5rem 1rem;
            color: #c9d1d9;
            text-decoration: none;
            font-size: 0.85rem;
        }}
        .grid {{
            max-width: 900px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }}
        .panel {{
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            overflow: hidden;
        }}
        .panel-header {{
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #30363d;
            font-size: 0.85rem;
            font-weight: 600;
            color: #8b949e;
            text-transform: uppercase;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .copy-btn {{
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 6px;
            padding: 0.3rem 0.7rem;
            color: #8b949e;
            font-size: 0.75rem;
            cursor: pointer;
        }}
        pre {{
            padding: 1.5rem;
            overflow-x: auto;
            font-size: 0.8rem;
            line-height: 1.6;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 600px;
            overflow-y: auto;
        }}
        .meta {{
            max-width: 900px;
            margin: 0 auto 1.5rem;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 1.5rem;
        }}
        .tag {{
            display: inline-block;
            background: #21262d;
            border: 1px solid #30363d;
            border-radius: 20px;
            padding: 0.2rem 0.7rem;
            font-size: 0.8rem;
            margin: 0.2rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Publication Assistant Result</h1>
        <a href="/" class="back-btn">Generate Another</a>
    </div>
    <div class="meta">
        <p><strong>Optimized Title:</strong> {optimized_title}</p>
        <p style="margin-top:0.5rem"><strong>Tags:</strong> {tags_html}</p>
        <p style="margin-top:0.5rem"><strong>QA Status:</strong> {qa_status}</p>
    </div>
    <div class="grid">
        <div class="panel">
            <div class="panel-header">
                Generated README.md
                <button class="copy-btn" onclick="copyText('readme-content')">Copy</button>
            </div>
            <pre id="readme-content">{readme_content}</pre>
        </div>
        <div class="panel">
            <div class="panel-header">Structural Critique Report</div>
            <pre>{critique_report}</pre>
        </div>
    </div>
    <script>
        function copyText(id) {{
            const text = document.getElementById(id).innerText;
            navigator.clipboard.writeText(text).then(() => {{
                alert('Copied to clipboard!');
            }});
        }}
    </script>
</body>
</html>
"""

ERROR_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Publication Assistant Error</title>
    <style>
        body {{ font-family: sans-serif; background: #0d1117; color: #c9d1d9;
               display: flex; align-items: center; justify-content: center;
               min-height: 100vh; padding: 2rem; }}
        .card {{ background: #161b22; border: 1px solid #f85149;
                 border-radius: 12px; padding: 2rem; max-width: 500px; width: 100%; }}
        h2 {{ color: #f85149; margin-bottom: 1rem; }}
        p {{ color: #8b949e; line-height: 1.6; margin-bottom: 1rem; }}
        a {{ color: #58a6ff; }}
    </style>
</head>
<body>
    <div class="card">
        <h2>{error_title}</h2>
        <p>{error_message}</p>
        <a href="/">Try Again</a>
    </div>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def home():
    html = INPUT_FORM.format(error_block="", url_value="", goal_value="")
    return HTMLResponse(content=html)


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, url: str = Form(...), goal: str = Form("")):
    url = url.strip()
    goal = goal.strip()

    if not url:
        error_block = '<div class="error">Repository URL is required.</div>'
        html = INPUT_FORM.format(error_block=error_block, url_value="", goal_value=goal)
        return HTMLResponse(content=html)

    if "github.com" not in url:
        error_block = '<div class="error">Please enter a valid GitHub URL.</div>'
        html = INPUT_FORM.format(error_block=error_block, url_value=url, goal_value=goal)
        return HTMLResponse(content=html)

    if not os.getenv("OPENAI_API_KEY"):
        html = ERROR_PAGE.format(
            error_title="Missing API Key",
            error_message="OPENAI_API_KEY is not set. Please add it to your .env file and restart the server."
        )
        return HTMLResponse(content=html, status_code=500)

    try:
        from publication_assistant import PublicationAssistantOrchestrator
        orchestrator = PublicationAssistantOrchestrator()
        result = orchestrator.run(url=url, goal=goal or "Optimize for general AI/ML developers")

    except ValueError as e:
        html = ERROR_PAGE.format(error_title="Invalid Input", error_message=str(e))
        return HTMLResponse(content=html, status_code=400)

    except EnvironmentError as e:
        html = ERROR_PAGE.format(error_title="Configuration Error", error_message=str(e))
        return HTMLResponse(content=html, status_code=500)

    except Exception as e:
        html = ERROR_PAGE.format(
            error_title="Pipeline Error",
            error_message=f"An unexpected error occurred: {str(e)}. Please check your API keys and try again."
        )
        return HTMLResponse(content=html, status_code=500)

    meta = result.get("metadata_recommendations", {})
    tags = meta.get("suggested_tags", [])
    tags_html = " ".join([f'<span class="tag">{t}</span>' for t in tags])
    qa_passed = result.get("qa_passed", False)

    html = RESULT_PAGE.format(
        optimized_title=meta.get("optimized_title", "N/A"),
        tags_html=tags_html or "None",
        qa_status="✅ Passed" if qa_passed else "⚠️ Review needed",
        readme_content=result.get("final_output", "No output generated."),
        critique_report=result.get("critique_report", "No report generated."),
    )
    return HTMLResponse(content=html)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
        "serper_configured": bool(os.getenv("SERPER_API_KEY")),
    }
