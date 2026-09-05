import os
import sys
import json
from pathlib import Path
import pandas as pd
import requests
import streamlit as st
from langchain_core.messages import HumanMessage

# Add workspace root to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from agents.data_agent import data_agent
from utils.database import DatabaseUtil

st.set_page_config(
    page_title="DATA_AGENT • Google Material Workspace",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Google Light Material Design Theme with High Contrast Dark Grey Text)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto+Mono:wght@400;500&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"], .stApp, main {
        font-family: 'Google Sans', 'Inter', sans-serif !important;
        background-color: #FFFFFF !important;
        color: #3C4043 !important;
    }

    /* Top Streamlit Bar Header */
    header[data-testid="stHeader"] {
        background-color: #FFFFFF !important;
        border-bottom: 1px solid #E0E0E0 !important;
    }
    header[data-testid="stHeader"] * {
        color: #3C4043 !important;
    }

    /* Force high contrast dark grey text across all headings, paragraphs, and markdown */
    p, span, label, h1, h2, h3, h4, h5, h6, li, td, th, div[data-testid="stMarkdownContainer"] p {
        color: #202124 !important;
    }

    /* Sidebar Google Material Styling */
    section[data-testid="stSidebar"], div[data-testid="stSidebarContent"], div[data-testid="stSidebarUserContent"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #E0E0E0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #3C4043 !important;
    }

    /* Bottom Chat Input Container Override */
    div[data-testid="stBottom"], div[data-testid="stBottom"] > div {
        background-color: #FFFFFF !important;
        border-top: 1px solid #E0E0E0 !important;
    }
    div[data-testid="stChatInput"], div[data-testid="stChatInputContainer"], textarea[data-testid="stChatInputTextArea"] {
        background-color: #FFFFFF !important;
        border: 1px solid #DADCE0 !important;
        border-radius: 24px !important;
        color: #202124 !important;
        box-shadow: 0 1px 3px rgba(60,64,67,0.1) !important;
    }
    div[data-testid="stChatInput"] textarea::placeholder {
        color: #757575 !important;
    }

    /* Inputs, Selectboxes, and Text Areas */
    input, textarea, div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] {
        background-color: #FFFFFF !important;
        color: #202124 !important;
        border-color: #DADCE0 !important;
        border-radius: 8px !important;
    }

    /* Status, Alert, and Expander Widgets */
    div[data-testid="stExpander"], div[data-testid="stStatusWidget"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 12px !important;
        color: #202124 !important;
    }

    /* Google Animated Fluid River Ribbon Header Banner */
    .river-banner {
        width: 100%;
        height: 80px;
        background: linear-gradient(-45deg, #4285F4, #EA4335, #FBBC05, #34A853, #1A73E8);
        background-size: 400% 400%;
        animation: riverFlow 12s ease infinite;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0 24px;
        margin-bottom: 24px;
        box-shadow: 0 4px 12px rgba(66, 133, 244, 0.2);
    }
    .river-banner * {
        color: #FFFFFF !important;
    }
    @keyframes riverFlow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .river-banner-title {
        font-size: 1.35rem;
        font-weight: 700;
        letter-spacing: -0.3px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .river-banner-sub {
        font-size: 0.85rem;
        opacity: 0.95;
    }

    /* Streamlit Chat Messages High Contrast Styling */
    div[data-testid="stChatMessage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 16px !important;
        box-shadow: 0 1px 3px rgba(60,64,67,0.08) !important;
        padding: 16px 20px !important;
        margin-bottom: 16px !important;
    }

    div[data-testid="stChatMessage"] * {
        color: #3C4043 !important;
    }

    /* Code Block High Contrast */
    pre, code, div[data-testid="stCodeBlock"] {
        background-color: #F8F9FA !important;
        color: #202124 !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 10px !important;
    }

    /* Material Cards & Buttons */
    .stButton > button {
        border-radius: 24px !important;
        border: 1px solid #DADCE0 !important;
        background-color: #FFFFFF !important;
        color: #3C4043 !important;
        font-weight: 500 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 1px 2px rgba(60,64,67,0.1) !important;
    }
    .stButton > button:hover {
        background-color: #E8F0FE !important;
        border-color: #1A73E8 !important;
        color: #1A73E8 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(26,115,232,0.15) !important;
    }

    /* Google Badges with Inline SVG support */
    .badge-sql {
        background: #E8F0FE;
        color: #1A73E8 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #D2E3FC;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 8px;
    }
    .badge-etl {
        background: #FEF7E0;
        color: #B06000 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #FCE8E6;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 8px;
    }
    .badge-safe {
        background: #E6F4EA;
        color: #137333 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #CEEAD6;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 8px;
    }
    .badge-unsafe {
        background: #FCE8E6;
        color: #D93025 !important;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.8rem;
        border: 1px solid #FAD2CF;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        margin-right: 8px;
    }
    </style>
""", unsafe_allow_html=True)



# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# SVG Icons
SVG_SQL = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#1A73E8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>'
SVG_ETL = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#B06000" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'
SVG_SAFE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#137333" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>'
SVG_UNSAFE = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#D93025" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>'
SVG_SPARKLES = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>'

# Sidebar Navigation
with st.sidebar:
    st.title("DATA_AGENT")
    st.caption("Multi-Agent System Architecture")
    
    st.divider()
    
    # Backend API Server Check
    api_url = st.text_input("FastAPI Service URL", value="http://localhost:8000")
    api_connected = False
    try:
        r = requests.get(f"{api_url}/api/health", timeout=1.5)
        if r.status_code == 200:
            st.success("FastAPI Backend Connected")
            api_connected = True
        else:
            st.warning("Backend response warning")
    except Exception:
        st.info("Standalone Direct-Invoke Mode")

    st.divider()

    # Database Schema Explorer
    st.subheader("PostgreSQL Schema")
    if st.button("Refresh Schema Details", use_container_width=True):
        with st.spinner("Fetching live database schema..."):
            try:
                conn_details = {
                    "host": os.environ.get("host", "localhost"),
                    "port": os.environ.get("port", "5432"),
                    "user": os.environ.get("user", "postgres"),
                    "password": os.environ.get("password", ""),
                    "dbname": os.environ.get("database", "postgres"),
                }
                db = DatabaseUtil(conn_details)
                schema_txt = db.schema_details("public")
                st.session_state["schema_details"] = schema_txt
            except Exception as e:
                st.error(f"Failed to fetch schema: {e}")

    if "schema_details" in st.session_state:
        with st.expander("View Active DB Schema", expanded=False):
            st.text_area("Schema Metadata", st.session_state["schema_details"], height=250)

    st.divider()

    # ETL File Hub
    st.subheader("ETL File Hub")
    search_dirs = [BASE_DIR / "data", BASE_DIR / "data" / "extract"]
    found_files = []
    for folder in search_dirs:
        if folder.exists():
            for item in folder.glob("*"):
                if item.is_file() and item.suffix.lower() in [".csv", ".json", ".parquet"]:
                    found_files.append(item)

    if found_files:
        selected_file = st.selectbox("Select extracted file:", [f.name for f in found_files])
        if selected_file:
            file_obj = next(f for f in found_files if f.name == selected_file)
            st.caption(f"Path: `{file_obj.relative_to(BASE_DIR)}` | Size: `{file_obj.stat().st_size / 1024:.1f} KB`")
            
            if st.button("Preview File Data", use_container_width=True):
                try:
                    ext = file_obj.suffix.lower()
                    if ext == ".csv":
                        df_preview = pd.read_csv(file_obj)
                    elif ext == ".json":
                        df_preview = pd.read_json(file_obj)
                    elif ext == ".parquet":
                        df_preview = pd.read_parquet(file_obj)
                    st.dataframe(df_preview.head(10), use_container_width=True)
                except Exception as ex:
                    st.error(f"Could not read data: {ex}")

            with open(file_obj, "rb") as f:
                st.download_button("Download File", f, file_name=file_obj.name, use_container_width=True)
    else:
        st.info("No extracted datasets in data/ directory yet.")

# Main Interactive Workspace
st.markdown(f"""
    <div class="river-banner">
        <div>
            <div class="river-banner-title">{SVG_SPARKLES} DATA_AGENT Google Workspace</div>
            <div class="river-banner-sub">Autonomous LangGraph Orchestrator • Text-to-SQL Guardrails • API Dynamic ETL Engine</div>
        </div>
        <div style="background:rgba(255,255,255,0.25); padding:6px 14px; border-radius:20px; font-weight:600; font-size:0.8rem;">
            System Active
        </div>
    </div>
""", unsafe_allow_html=True)


# Quick Action Chips
st.markdown("##### Quick Action Preset Prompts")
c1, c2, c3 = st.columns(3)
preset_clicked = None
if c1.button("SQL: Payment Methods"):
    preset_clicked = "What are the different types of Payment Methods in our database?"
if c2.button("ETL: API Data Extract"):
    preset_clicked = "I want to extract the data from the API endpoint 'https://pokeapi.co/api/v2/pokemon' and save it to data/extract folder in the csv format"
if c3.button("Security: Unsafe DROP Query"):
    preset_clicked = "DROP TABLE customers;"

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "data" in msg and msg["data"]:
            data = msg["data"]
            # Router Badge
            r_type = data.get("route", "unknown").upper()
            if r_type == "SQL":
                st.markdown(f'<span class="badge-sql">{SVG_SQL} Routed to: SQL Analyst</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="badge-etl">{SVG_ETL} Routed to: ETL Analyst</span>', unsafe_allow_html=True)

            # Security Guardrail Badge
            is_safe = data.get("is_safe", "Yes")
            if is_safe == "Yes":
                st.markdown(f'<span class="badge-safe">{SVG_SAFE} Security Judge: SAFE READ-ONLY</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="badge-unsafe">{SVG_UNSAFE} Security Judge: BLOCKED UNSAFE COMMAND</span>', unsafe_allow_html=True)

            if data.get("generated_sql"):
                st.markdown("**Generated SQL:**")
                st.code(data["generated_sql"], language="sql")

            if data.get("execution_result"):
                st.markdown("**Database Execution Output:**")
                st.text(data["execution_result"])

# Chat Input Handler
user_input = st.chat_input("Ask a database query or request API extraction...")

prompt_to_run = preset_clicked or user_input

if prompt_to_run:
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt_to_run})
    with st.chat_message("user"):
        st.markdown(prompt_to_run)

    # Process response
    with st.chat_message("assistant"):
        with st.status("Executing Multi-Agent Trajectory...", expanded=True) as status_box:
            result_data = {}
            try:
                if api_connected:
                    status_box.update(label="Sending request to FastAPI backend...", state="running")
                    res = requests.post(f"{api_url}/api/chat", json={"message": prompt_to_run})
                    result_data = res.json()
                else:
                    status_box.update(label="Executing LangGraph agent state machine...", state="running")
                    initial_state = {
                        "messages": [HumanMessage(content=prompt_to_run)],
                        "route_response": ""
                    }
                    res = data_agent.invoke(initial_state)
                    
                    route = str(res.get("route_response", "unknown")).lower()
                    messages = res.get("messages", [])
                    
                    result_data = {
                        "route": route,
                        "curated_question": "",
                        "is_safe": "Yes",
                        "security_comments": "",
                        "generated_sql": "",
                        "execution_result": "",
                        "final_answer": ""
                    }
                    
                    if messages:
                        last_msg = messages[-1]
                        if isinstance(last_msg, dict):
                            if "generated_sql_query" in last_msg or route == "sql":
                                result_data["curated_question"] = last_msg.get("curated_ques", "")
                                result_data["is_safe"] = last_msg.get("is_safe", "Yes")
                                result_data["security_comments"] = last_msg.get("comments", "")
                                result_data["generated_sql"] = last_msg.get("generated_sql_query", "")
                                result_data["execution_result"] = last_msg.get("sql_query_execution_result", "")
                                result_data["final_answer"] = last_msg.get("final_answer", "")
                            elif "messages" in last_msg and isinstance(last_msg["messages"], list) and last_msg["messages"]:
                                last_msg_item = last_msg["messages"][-1]
                                result_data["final_answer"] = getattr(last_msg_item, "content", str(last_msg_item))
                        else:
                            result_data["final_answer"] = str(last_msg)

                status_box.update(label="Execution Complete!", state="complete", expanded=False)

            except Exception as err:
                status_box.update(label=f"Execution Failed: {err}", state="error")
                result_data = {"final_answer": f"Error during agent execution: {err}"}

        # Render Trajectory Output Cards
        r_type = result_data.get("route", "unknown").upper()
        if r_type == "SQL":
            st.markdown(f'<span class="badge-sql">{SVG_SQL} Routed to: SQL Analyst</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="badge-etl">{SVG_ETL} Routed to: ETL Analyst</span>', unsafe_allow_html=True)

        is_safe = result_data.get("is_safe", "Yes")
        if is_safe == "Yes":
            st.markdown(f'<span class="badge-safe">{SVG_SAFE} Security Judge: SAFE READ-ONLY</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="badge-unsafe">{SVG_UNSAFE} Security Judge: BLOCKED UNSAFE COMMAND</span>', unsafe_allow_html=True)
            if result_data.get("security_comments"):
                st.warning(f"Judge Comments: {result_data['security_comments']}")

        if result_data.get("generated_sql"):
            st.markdown("**Generated SQL Query:**")
            st.code(result_data["generated_sql"], language="sql")

        if result_data.get("execution_result"):
            st.markdown("**Database Execution Output:**")
            st.text(result_data["execution_result"])

        final_ans = result_data.get("final_answer", "")
        st.markdown(f"### Final Answer\n{final_ans}")

        # Store in session state
        st.session_state.messages.append({
            "role": "assistant",
            "content": final_ans,
            "data": result_data
        })

