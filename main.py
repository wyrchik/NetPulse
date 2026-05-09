import os
import sys
import logging
import threading
import asyncio
from flask import Flask, send_from_directory, jsonify, request
from api.routes import api_blueprint
from scanner.logger import setup_logger
logger = setup_logger()
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
web_dir = os.path.join(base_path, "web")
os.makedirs(web_dir, exist_ok=True)
app = Flask(__name__, static_folder=web_dir)
app.register_blueprint(api_blueprint, url_prefix='/api')
@app.route('/')
def root():
    return send_from_directory(web_dir, 'index.html')
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(web_dir, filename)
def run_server():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def start_app():
    import threading
    import time
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    try:
        import webview
        webview.create_window("NetPulse", "http://127.0.0.1:5000", width=1200, height=800)
        webview.start()
    except Exception as e:
        print(f"\n[ERROR] Native GUI failed to load: {e}")
        print("Please ensure you have PyQt6 or GTK bindings installed.")
        print("Run: pip install PyQt6 PyQt6-WebEngine")
        sys.exit(1)

if __name__ == "__main__":
    start_app()
