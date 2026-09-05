import sys
import subprocess
import time
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

def run_fastapi():
    print("🚀 Starting FastAPI Server on http://localhost:8000 ...")
    return subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

def run_streamlit():
    print("⚡ Starting Streamlit Dashboard on http://localhost:8501 ...")
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", "streamlit_app.py", "--server.port", "8501", "--server.headless", "true"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DATA_AGENT Service Launcher")
    parser.add_argument("--api", action="store_true", help="Launch FastAPI server only")
    parser.add_argument("--streamlit", action="store_true", help="Launch Streamlit UI only")
    args = parser.parse_args()

    processes = []

    try:
        if args.api:
            p_api = run_fastapi()
            processes.append(p_api)
            p_api.wait()
        elif args.streamlit:
            p_st = run_streamlit()
            processes.append(p_st)
            p_st.wait()
        else:
            p_api = run_fastapi()
            processes.append(p_api)
            time.sleep(2)  # Give FastAPI 2 seconds to initialize
            p_st = run_streamlit()
            processes.append(p_st)
            
            print("\n✅ Both FastAPI (http://localhost:8000) and Streamlit (http://localhost:8501) are running!")
            print("Press Ctrl+C to stop all services.\n")
            
            for p in processes:
                p.wait()
    except KeyboardInterrupt:
        print("\nStopping services...")
        for p in processes:
            p.terminate()
        sys.exit(0)
