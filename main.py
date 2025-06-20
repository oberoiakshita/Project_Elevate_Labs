import threading
import logging
from app import app
from honeypot import HoneypotServer

logger = logging.getLogger(__name__)

def start_honeypot():
    """Start the honeypot server in a separate thread"""
    try:
        honeypot = HoneypotServer(host='0.0.0.0', port=2222)
        honeypot.start()
    except Exception as e:
        logger.error(f"Failed to start honeypot: {e}")

if __name__ == "__main__":
    # Start honeypot server in background thread
    honeypot_thread = threading.Thread(target=start_honeypot, daemon=True)
    honeypot_thread.start()
    logger.info("Honeypot server started on port 2222")
    
    # Start Flask web dashboard
    logger.info("Starting web dashboard on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
