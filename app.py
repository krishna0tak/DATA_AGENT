import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

# Add workspace to python path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from agents.data_agent import data_agent
from utils.database import DatabaseUtil
import pandas as pd

app = FastAPI(
    title="DATA_AGENT API",
    description="Autonomous Multi-Agent AI System for Data Engineering & SQL Analytics",
    version="0.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

def get_db_connection_params():
    return {
        "host": os.environ.get("host", "localhost"),
        "port": os.environ.get("port", "5432"),
        "user": os.environ.get("user", "postgres"),
        "password": os.environ.get("password", ""),
        "dbname": os.environ.get("database", "postgres"),
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok", "agent": "DATA_AGENT"}

@app.get("/api/schema")
def get_database_schema(schema_name: str = "public"):
    """Fetches live schema details from PostgreSQL database."""
    try:
        conn = get_db_connection_params()
        db = DatabaseUtil(conn)
        raw_schema = db.schema_details(schema_name)
        return {
            "schema_name": schema_name,
            "raw_details": raw_schema
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schema: {str(e)}")

@app.get("/api/etl/files")
def list_etl_files():
    """Lists extracted and transformed dataset files."""
    files_info = []
    search_dirs = [BASE_DIR / "data", BASE_DIR / "data" / "extract"]
    
    for folder in search_dirs:
        if folder.exists():
            for item in folder.glob("*"):
                if item.is_file() and item.suffix.lower() in [".csv", ".json", ".parquet"]:
                    files_info.append({
                        "name": item.name,
                        "relative_path": str(item.relative_to(BASE_DIR)).replace("\\", "/"),
                        "absolute_path": str(item).replace("\\", "/"),
                        "size_bytes": item.stat().st_size,
                        "extension": item.suffix.lower()
                    })
    return {"files": files_info}

@app.get("/api/etl/preview")
def preview_etl_file(file_path: str = Query(..., description="Relative or absolute path to data file")):
    """Previews the top rows of a data file."""
    target = Path(file_path)
    if not target.is_absolute():
        target = BASE_DIR / target

    if not target.exists():
        raise HTTPException(status_code=404, detail="Data file not found")

    try:
        ext = target.suffix.lower()
        if ext == ".csv":
            df = pd.read_csv(target).head(10)
        elif ext == ".json":
            df = pd.read_json(target).head(10)
        elif ext == ".parquet":
            df = pd.read_parquet(target).head(10)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")
        
        # Clean up NaNs for JSON response
        df = df.fillna("")
        return {
            "file_name": target.name,
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "total_preview_rows": len(df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

@app.post("/api/chat")
def process_chat(req: ChatRequest):
    """Executes DATA_AGENT graph and returns structured trajectory details."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        initial_state = {
            "messages": [HumanMessage(content=req.message)],
            "route_response": ""
        }
        res = data_agent.invoke(initial_state)

        route = str(res.get("route_response", "unknown")).lower()
        messages = res.get("messages", [])

        output = {
            "input_question": req.message,
            "route": route,
            "route_label": "SQL Analytics Agent" if route == "sql" else "ETL Data Engineering Agent",
            "curated_question": "",
            "is_safe": "Yes",
            "security_comments": "",
            "generated_sql": "",
            "execution_result": "",
            "final_answer": ""
        }

        if messages:
            last_sub_state = messages[-1]
            if isinstance(last_sub_state, dict):
                if "generated_sql_query" in last_sub_state or route == "sql":
                    # SQL sub-agent result
                    output["curated_question"] = last_sub_state.get("curated_ques", "")
                    output["is_safe"] = last_sub_state.get("is_safe", "Yes")
                    output["security_comments"] = last_sub_state.get("comments", "")
                    output["generated_sql"] = last_sub_state.get("generated_sql_query", "")
                    output["execution_result"] = last_sub_state.get("sql_query_execution_result", "")
                    output["final_answer"] = last_sub_state.get("final_answer", "")
                elif "messages" in last_sub_state and isinstance(last_sub_state["messages"], list) and last_sub_state["messages"]:
                    # ETL sub-agent result
                    last_msg_item = last_sub_state["messages"][-1]
                    output["final_answer"] = getattr(last_msg_item, "content", str(last_msg_item))
            else:
                output["final_answer"] = str(last_sub_state)

        return output
    except Exception as e:
        print(f"Error in process_chat: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

@app.get("/", response_class=HTMLResponse)
def serve_dashboard():
    """Serves a bright, clean FastAPI Web Dashboard with Google Material aesthetics and Fluid River Canvas."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DATA_AGENT Workspace</title>
        <link href="https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto+Mono:wght@400;500&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" rel="stylesheet" />
        <style>
            :root {
                --g-blue: #1A73E8;
                --g-blue-light: #E8F0FE;
                --g-blue-hover: #1765CC;
                --g-red: #D93025;
                --g-red-light: #FCE8E6;
                --g-yellow: #F9AB00;
                --g-yellow-light: #FEF7E0;
                --g-green: #137333;
                --g-green-light: #E6F4EA;
                --bg-main: #FFFFFF;
                --bg-surface: #F8F9FA;
                --bg-hover: #F1F3F4;
                --border-color: #E0E0E0;
                --border-focus: #1A73E8;
                --text-primary: #202124;
                --text-secondary: #5F6368;
                --shadow-sm: 0 1px 2px 0 rgba(60,64,67,0.15), 0 1px 3px 1px rgba(60,64,67,0.1);
                --shadow-md: 0 4px 12px rgba(32,33,36,0.08);
                --radius-pill: 24px;
                --radius-card: 16px;
            }

            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Google Sans', 'Inter', sans-serif; }
            body { background: var(--bg-surface); color: var(--text-primary); display: flex; height: 100vh; overflow: hidden; }

            /* Material Ink Ripple Effect */
            .ripple-container { position: relative; overflow: hidden; }
            span.ripple {
                position: absolute;
                border-radius: 50%;
                transform: scale(0);
                animation: ripple 600ms linear;
                background-color: rgba(66, 133, 244, 0.25);
                pointer-events: none;
            }
            @keyframes ripple {
                to { transform: scale(4); opacity: 0; }
            }

            /* Entry Animation */
            @keyframes riverFadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }

            /* App Sidebar */
            .sidebar {
                width: 330px;
                background: var(--bg-main);
                border-right: 1px solid var(--border-color);
                display: flex;
                flex-direction: column;
                padding: 24px 20px;
                z-index: 10;
                box-shadow: 1px 0 3px rgba(0,0,0,0.02);
            }

            .brand-header {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 24px;
            }
            .brand-logo {
                width: 40px;
                height: 40px;
                border-radius: 12px;
                background: linear-gradient(135deg, var(--g-blue), #4285F4);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 6px rgba(26,115,232,0.3);
            }
            .brand-title {
                font-size: 1.2rem;
                font-weight: 700;
                color: var(--text-primary);
                letter-spacing: -0.3px;
            }
            .brand-badge {
                background: var(--g-blue-light);
                color: var(--g-blue);
                font-size: 0.7rem;
                padding: 2px 8px;
                border-radius: 12px;
                font-weight: 700;
                text-transform: uppercase;
            }

            .sidebar-section { margin-bottom: 24px; }
            .section-label {
                font-size: 0.78rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.06em;
                color: var(--text-secondary);
                margin-bottom: 12px;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .btn {
                background: var(--g-blue);
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: var(--radius-pill);
                font-weight: 500;
                font-size: 0.9rem;
                cursor: pointer;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .btn:hover {
                background: var(--g-blue-hover);
                box-shadow: var(--shadow-md);
                transform: translateY(-1px);
            }
            .btn-outline {
                background: var(--bg-main);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                width: 100%;
                justify-content: flex-start;
                padding: 11px 16px;
                border-radius: 12px;
                margin-bottom: 10px;
            }
            .btn-outline:hover {
                background: var(--bg-hover);
                border-color: var(--g-blue);
                color: var(--g-blue);
            }

            .scroll-box {
                max-height: 180px;
                overflow-y: auto;
                background: var(--bg-surface);
                border-radius: 12px;
                border: 1px solid var(--border-color);
                padding: 12px;
                font-size: 0.82rem;
                white-space: pre-wrap;
                font-family: 'Roboto Mono', monospace;
                color: #3c4043;
                margin-top: 6px;
            }

            /* Main Content Workspace */
            .main {
                flex: 1;
                display: flex;
                flex-direction: column;
                background: var(--bg-main);
                position: relative;
                overflow: hidden;
            }

            /* Fluid River Banner Canvas Header */
            .river-header {
                position: relative;
                height: 90px;
                background: #FFFFFF;
                border-bottom: 1px solid var(--border-color);
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 0 32px;
                overflow: hidden;
            }
            #riverCanvas {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                opacity: 0.85;
            }
            .header-info {
                position: relative;
                z-index: 2;
            }
            .header-title {
                font-size: 1.15rem;
                font-weight: 700;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .header-subtitle {
                font-size: 0.82rem;
                color: var(--text-secondary);
                margin-top: 2px;
            }
            .status-pill {
                position: relative;
                z-index: 2;
                background: var(--bg-main);
                border: 1px solid var(--border-color);
                padding: 6px 14px;
                border-radius: var(--radius-pill);
                font-size: 0.8rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 8px;
                box-shadow: var(--shadow-sm);
            }
            .dot-green {
                width: 8px;
                height: 8px;
                background: var(--g-green);
                border-radius: 50%;
                display: inline-block;
                animation: pulseGreen 2s infinite;
            }
            @keyframes pulseGreen {
                0% { box-shadow: 0 0 0 0 rgba(19,115,51,0.4); }
                70% { box-shadow: 0 0 0 8px rgba(19,115,51,0); }
                100% { box-shadow: 0 0 0 0 rgba(19,115,51,0); }
            }

            /* Chat Stream Workspace */
            .chat-container {
                flex: 1;
                overflow-y: auto;
                padding: 28px 32px;
                display: flex;
                flex-direction: column;
                gap: 20px;
                background: var(--bg-surface);
            }

            .card {
                background: var(--bg-main);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-card);
                padding: 20px 24px;
                box-shadow: var(--shadow-sm);
                animation: riverFadeIn 0.35s cubic-bezier(0.2, 0, 0, 1);
                transition: box-shadow 0.25s, transform 0.25s;
            }
            .card:hover {
                box-shadow: var(--shadow-md);
            }

            .card-header {
                display: flex;
                align-items: center;
                justify-content: space-between;
                margin-bottom: 12px;
                padding-bottom: 10px;
                border-bottom: 1px solid var(--border-color);
                font-weight: 600;
                font-size: 0.95rem;
            }

            /* Tags & Badges */
            .tag {
                padding: 4px 12px;
                border-radius: var(--radius-pill);
                font-size: 0.78rem;
                font-weight: 600;
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
            .tag-sql { background: var(--g-blue-light); color: var(--g-blue); }
            .tag-etl { background: var(--g-yellow-light); color: #B06000; }
            .tag-safe { background: var(--g-green-light); color: var(--g-green); }
            .tag-unsafe { background: var(--g-red-light); color: var(--g-red); }

            pre {
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 14px 18px;
                border-radius: 12px;
                font-family: 'Roboto Mono', monospace;
                font-size: 0.88rem;
                overflow-x: auto;
                margin: 10px 0;
                border: 1px solid #333;
                position: relative;
            }
            .code-output {
                background: #F1F3F4;
                color: #202124;
                border-left: 4px solid var(--g-blue);
                padding: 12px 16px;
                border-radius: 6px;
                font-family: 'Roboto Mono', monospace;
                font-size: 0.84rem;
                white-space: pre-wrap;
                margin-top: 8px;
            }

            /* Preset Prompts Section */
            .presets-bar {
                display: flex;
                gap: 10px;
                padding: 12px 32px;
                background: var(--bg-main);
                border-top: 1px solid var(--border-color);
                flex-wrap: wrap;
            }
            .chip {
                background: var(--bg-surface);
                color: var(--text-primary);
                border: 1px solid var(--border-color);
                padding: 8px 16px;
                border-radius: var(--radius-pill);
                font-size: 0.82rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s cubic-bezier(0.2, 0, 0, 1);
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
            .chip:hover {
                background: var(--g-blue-light);
                border-color: var(--g-blue);
                color: var(--g-blue);
                transform: translateY(-1px);
            }

            /* Bottom Input Section */
            .input-box {
                padding: 18px 32px 24px 32px;
                background: var(--bg-main);
                display: flex;
                gap: 12px;
                align-items: center;
            }
            .input-wrapper {
                flex: 1;
                position: relative;
                display: flex;
                align-items: center;
            }
            .input-wrapper span {
                position: absolute;
                left: 16px;
                color: var(--text-secondary);
            }
            .input-wrapper input {
                width: 100%;
                background: var(--bg-surface);
                border: 1px solid var(--border-color);
                border-radius: var(--radius-pill);
                padding: 14px 20px 14px 48px;
                color: var(--text-primary);
                font-size: 0.95rem;
                outline: none;
                transition: all 0.2s ease;
            }
            .input-wrapper input:focus {
                background: var(--bg-main);
                border-color: var(--border-focus);
                box-shadow: 0 0 0 3px rgba(26,115,232,0.15);
            }
        </style>
    </head>
    <body>
        <!-- Left Sidebar Navigation -->
        <div class="sidebar">
            <div class="brand-header">
                <div class="brand-logo">
                    <span class="material-symbols-outlined">auto_awesome</span>
                </div>
                <div>
                    <div class="brand-title">DATA_AGENT</div>
                    <span class="brand-badge">Autonomous</span>
                </div>
            </div>

            <div class="sidebar-section">
                <div class="section-label">
                    <span class="material-symbols-outlined" style="font-size:1.1rem;">database</span>
                    PostgreSQL Live Schema
                </div>
                <button class="btn btn-outline ripple-container" onclick="fetchSchema(event)">
                    <span class="material-symbols-outlined" style="font-size:1.1rem;">refresh</span>
                    Load Database Tables
                </button>
                <div id="schemaBox" class="scroll-box">Click button above to inspect live PostgreSQL database tables...</div>
            </div>

            <div class="sidebar-section">
                <div class="section-label">
                    <span class="material-symbols-outlined" style="font-size:1.1rem;">folder_open</span>
                    ETL Data Storage Hub
                </div>
                <button class="btn btn-outline ripple-container" onclick="fetchETLFiles(event)">
                    <span class="material-symbols-outlined" style="font-size:1.1rem;">view_list</span>
                    List Extracted Datasets
                </button>
                <div id="etlBox" class="scroll-box">No datasets listed yet...</div>
            </div>
        </div>

        <!-- Main Fluid Workspace -->
        <div class="main">
            <!-- Fluid River Header Canvas -->
            <div class="river-header">
                <canvas id="riverCanvas"></canvas>
                <div class="header-info">
                    <div class="header-title">
                        <span class="material-symbols-outlined" style="color:var(--g-blue);">water_drop</span>
                        Autonomous Multi-Agent Workspace
                    </div>
                    <div class="header-subtitle">LangGraph State Machine • Text-to-SQL Guardrails • API Dynamic ETL Engine</div>
                </div>
                <div class="status-pill">
                    <span class="dot-green"></span>
                    FastAPI Engine Active
                </div>
            </div>

            <!-- Chat Message Feed -->
            <div id="chatBox" class="chat-container">
                <div class="card">
                    <div class="card-header">
                        <span style="display:flex; align-items:center; gap:8px;">
                            <span class="material-symbols-outlined" style="color:var(--g-blue);">auto_awesome</span>
                            Welcome to DATA_AGENT Workspace
                        </span>
                        <span class="tag tag-sql">System Operational</span>
                    </div>
                    <p style="color: var(--text-secondary); line-height: 1.5; font-size: 0.92rem;">
                        Ask natural language data questions to generate SQL with safety inspection, or request automated API data extraction into CSV/JSON datasets.
                    </p>
                </div>
            </div>

            <!-- Floating Preset Prompt Chips -->
            <div class="presets-bar">
                <button class="chip ripple-container" onclick="setPrompt('What payment methods are in our database?', event)">
                    <span class="material-symbols-outlined" style="font-size:1rem; color:var(--g-blue);">payments</span>
                    SQL: Payment Methods
                </button>
                <button class="chip ripple-container" onclick="setPrompt('I want to extract data from https://pokeapi.co/api/v2/pokemon and save to data/extract folder in csv format', event)">
                    <span class="material-symbols-outlined" style="font-size:1rem; color:var(--g-yellow);">download</span>
                    ETL: API Extract Pokemon
                </button>
                <button class="chip ripple-container" onclick="setPrompt('DROP TABLE customers;', event)">
                    <span class="material-symbols-outlined" style="font-size:1rem; color:var(--g-red);">gavel</span>
                    Security: Test DROP Table
                </button>
            </div>

            <!-- Input Controls -->
            <div class="input-box">
                <div class="input-wrapper">
                    <span class="material-symbols-outlined">search</span>
                    <input type="text" id="userInput" placeholder="Ask a SQL query or issue an ETL extraction instruction..." onkeypress="handleKey(event)">
                </div>
                <button class="btn ripple-container" onclick="sendQuery(event)">
                    <span>Submit</span>
                    <span class="material-symbols-outlined" style="font-size:1.1rem;">send</span>
                </button>
            </div>
        </div>

        <script>
            // --- Fluid River Waves Canvas Physics ---
            const canvas = document.getElementById('riverCanvas');
            const ctx = canvas.getContext('2d');
            let width, height;
            let waveOffset = 0;
            let mouseX = -1000, mouseY = -1000;

            function resizeCanvas() {
                width = canvas.width = canvas.parentElement.clientWidth;
                height = canvas.height = canvas.parentElement.clientHeight || 90;
            }
            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();

            window.addEventListener('mousemove', (e) => {
                const rect = canvas.getBoundingClientRect();
                mouseX = e.clientX - rect.left;
                mouseY = e.clientY - rect.top;
            });

            function drawRiver() {
                ctx.clearRect(0, 0, width, height);
                waveOffset += 0.012;

                const colors = [
                    { r: 26, g: 115, b: 232, alpha: 0.18 }, // Google Blue
                    { r: 217, g: 48, b: 37, alpha: 0.14 },  // Google Red
                    { r: 249, g: 171, b: 0, alpha: 0.14 },  // Google Yellow
                    { r: 19, g: 115, b: 51, alpha: 0.16 }   // Google Green
                ];

                colors.forEach((color, i) => {
                    ctx.beginPath();
                    ctx.moveTo(0, height);

                    for (let x = 0; x <= width; x += 12) {
                        const distToMouse = Math.hypot(x - mouseX, height/2 - mouseY);
                        const mousePush = Math.max(0, (140 - distToMouse) / 140) * 12;

                        const y = height / 2 + 
                                  Math.sin(x * 0.006 + waveOffset + i * 1.4) * (14 + i * 4) +
                                  Math.cos(x * 0.01 - waveOffset * 0.7 + i) * 8 +
                                  (i % 2 === 0 ? mousePush : -mousePush);
                        ctx.lineTo(x, y);
                    }

                    ctx.lineTo(width, height);
                    ctx.lineTo(0, height);
                    ctx.closePath();

                    const grad = ctx.createLinearGradient(0, 0, width, 0);
                    grad.addColorStop(0, `rgba(${color.r}, ${color.g}, ${color.b}, ${color.alpha})`);
                    grad.addColorStop(0.5, `rgba(${colors[(i+1)%4].r}, ${colors[(i+1)%4].g}, ${colors[(i+1)%4].b}, ${color.alpha * 1.3})`);
                    grad.addColorStop(1, `rgba(${color.r}, ${color.g}, ${color.b}, ${color.alpha * 0.8})`);

                    ctx.fillStyle = grad;
                    ctx.fill();
                });

                requestAnimationFrame(drawRiver);
            }
            drawRiver();

            // --- Material Ink Ripple Effect ---
            function createRipple(e) {
                const button = e.currentTarget;
                const circle = document.createElement("span");
                const diameter = Math.max(button.clientWidth, button.clientHeight);
                const radius = diameter / 2;
                const rect = button.getBoundingClientRect();

                circle.style.width = circle.style.height = `${diameter}px`;
                circle.style.left = `${e.clientX - rect.left - radius}px`;
                circle.style.top = `${e.clientY - rect.top - radius}px`;
                circle.classList.add("ripple");

                const ripple = button.getElementsByClassName("ripple")[0];
                if (ripple) ripple.remove();

                button.appendChild(circle);
            }

            function setPrompt(txt, e) {
                if (e) createRipple(e);
                document.getElementById('userInput').value = txt;
            }

            function handleKey(e) {
                if (e.key === 'Enter') sendQuery(e);
            }

            async function fetchSchema(e) {
                if (e) createRipple(e);
                const box = document.getElementById('schemaBox');
                box.innerText = "Fetching live PostgreSQL schema...";
                try {
                    const res = await fetch('/api/schema');
                    const data = await res.json();
                    box.innerText = data.raw_details || "No schema context returned.";
                } catch(err) {
                    box.innerText = "Error loading schema: " + err.message;
                }
            }

            async function fetchETLFiles(e) {
                if (e) createRipple(e);
                const box = document.getElementById('etlBox');
                box.innerText = "Listing datasets...";
                try {
                    const res = await fetch('/api/etl/files');
                    const data = await res.json();
                    if (!data.files || data.files.length === 0) {
                        box.innerText = "No extracted datasets found in data/ folder.";
                        return;
                    }
                    box.innerText = data.files.map(f => `📄 ${f.name} (${(f.size_bytes/1024).toFixed(1)} KB)`).join('\\n');
                } catch(err) {
                    box.innerText = "Error loading files: " + err.message;
                }
            }

            async function sendQuery(e) {
                if (e) createRipple(e);
                const input = document.getElementById('userInput');
                const query = input.value.trim();
                if (!query) return;

                const chatBox = document.getElementById('chatBox');
                
                // Add User Message Card
                const userCard = document.createElement('div');
                userCard.className = 'card';
                userCard.innerHTML = `
                    <div class="card-header">
                        <span style="display:flex; align-items:center; gap:8px;">
                            <span class="material-symbols-outlined" style="color:var(--g-blue);">account_circle</span>
                            User Query
                        </span>
                    </div>
                    <p style="font-size:0.95rem; font-weight:500;">${query}</p>
                `;
                chatBox.appendChild(userCard);
                
                input.value = '';
                chatBox.scrollTop = chatBox.scrollHeight;

                // Add Agent Loading Card
                const loadingCard = document.createElement('div');
                loadingCard.className = 'card';
                loadingCard.id = 'loading-card';
                loadingCard.innerHTML = `
                    <div style="display:flex; align-items:center; gap:10px; color:var(--text-secondary);">
                        <span class="material-symbols-outlined" style="animation: spin 1.5s linear infinite; color:var(--g-blue);">sync</span>
                        <span>DATA_AGENT is processing query through LangGraph state machine...</span>
                    </div>
                    <style>@keyframes spin { 100% { transform: rotate(360deg); } }</style>
                `;
                chatBox.appendChild(loadingCard);
                chatBox.scrollTop = chatBox.scrollHeight;

                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: query })
                    });
                    const data = await response.json();
                    
                    loadingCard.remove();

                    const agentCard = document.createElement('div');
                    agentCard.className = 'card';
                    
                    const routeTag = data.route === 'sql' ? 
                        '<span class="tag tag-sql"><span class="material-symbols-outlined" style="font-size:0.9rem;">storage</span> SQL Analyst</span>' : 
                        '<span class="tag tag-etl"><span class="material-symbols-outlined" style="font-size:0.9rem;">dataset</span> ETL Analyst</span>';
                    
                    const safeTag = data.is_safe === 'Yes' ? 
                        '<span class="tag tag-safe"><span class="material-symbols-outlined" style="font-size:0.9rem;">shield</span> Safe Query</span>' : 
                        '<span class="tag tag-unsafe"><span class="material-symbols-outlined" style="font-size:0.9rem;">block</span> Blocked Unsafe Query</span>';

                    let contentHtml = `
                        <div class="card-header">
                            <span style="display:flex; align-items:center; gap:8px;">
                                <span class="material-symbols-outlined" style="color:var(--g-blue);">smart_toy</span>
                                DATA_AGENT Trajectory Output
                            </span>
                            <div style="display:flex; gap:8px;">${routeTag} ${safeTag}</div>
                        </div>
                    `;
                    
                    if (data.generated_sql) {
                        contentHtml += `<p style="font-weight:600; font-size:0.85rem; color:var(--text-secondary); margin-top:8px;">GENERATED POSTGRES SQL:</p><pre><code>${data.generated_sql}</code></pre>`;
                    }

                    if (data.execution_result) {
                        contentHtml += `<p style="font-weight:600; font-size:0.85rem; color:var(--text-secondary); margin-top:8px;">DATABASE EXECUTION RESULT:</p><div class="code-output">${data.execution_result}</div>`;
                    }

                    if (data.final_answer) {
                        contentHtml += `<div style="margin-top:14px; padding-top:12px; border-top:1px solid var(--border-color); font-size:0.95rem;"><strong>Final Response:</strong> ${data.final_answer}</div>`;
                    }

                    agentCard.innerHTML = contentHtml;
                    chatBox.appendChild(agentCard);
                    chatBox.scrollTop = chatBox.scrollHeight;

                } catch(err) {
                    loadingCard.innerHTML = `<span style="color:var(--g-red);">Error executing request: ${err.message}</span>`;
                }
            }
        </script>
    </body>
    </html>
    """



