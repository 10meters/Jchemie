from pyngrok import ngrok
import subprocess
import time
import os
import sys

# Always resolve absolute path to this script’s folder
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STREAMLIT_FILE = os.path.join(SCRIPT_DIR, "Sales_Performance.py")
PORT = 8501

# Change working directory to the script folder
os.chdir(SCRIPT_DIR)

# Start Streamlit using absolute path
streamlit_process = subprocess.Popen(
    [sys.executable, "-m", "streamlit", "run", STREAMLIT_FILE, "--server.port", str(PORT)],
    cwd=SCRIPT_DIR
)

# Wait a bit for Streamlit to boot
time.sleep(5)

# Start ngrok tunnel
public_url = ngrok.connect(PORT).public_url
print(f"\nYour app is publicly available at: {public_url}\n")

# Keep script running
try:
    streamlit_process.wait()
except KeyboardInterrupt:
    ngrok.kill()
    streamlit_process.terminate()
