"""
Minimal HTTP server that runs alongside the Celery worker on Render.

Render's free web service type requires a process to bind a port.
Celery doesn't bind ports — it connects outward to Redis.
This tiny server runs on PORT (defaulting to 8001) and responds to
Render's health checks so the container isn't killed for not binding.

Usage (in render.yaml dockerCommand for the worker):
    sh -c "python worker_health.py & celery -A app.workers.tasks worker --loglevel=info --concurrency=1"

The & runs the health server in the background, then Celery starts
in the foreground. If Celery exits, the container exits (correct behavior).
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"worker alive")

    def log_message(self, format, *args):
        # Suppress access logs to keep Render logs clean
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()