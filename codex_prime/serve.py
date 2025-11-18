"""Minimal HTTP server for Codex Prime."""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from typing import Any
from pathlib import Path


class CodexHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Codex Prime API."""

    def do_POST(self) -> None:
        """Handle POST requests."""
        if self.path == '/chat':
            self._handle_chat()
        else:
            self.send_error(404, "Endpoint not found")

    def _handle_chat(self) -> None:
        """Handle /chat endpoint."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            project_id = data.get('project_id', 'default')
            message = data.get('message', '')
            commands = data.get('commands', [])

            # TODO: Implement actual agent processing
            response = {
                'answer': f'[Processed message: {message}]',
                'drift_score': 0.2,
                'memories_used': ['Sample memory 1', 'Sample memory 2'],
                'project_id': project_id
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON")
        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, format: str, *args: Any) -> None:
        """Custom log formatting."""
        print(f"[{self.log_date_time_string()}] {format % args}")


def serve(host: str = '0.0.0.0', port: int = 8080) -> None:
    """
    Start HTTP server.

    Args:
        host: Host to bind to
        port: Port to listen on
    """
    server = HTTPServer((host, port), CodexHandler)
    print(f"Codex Prime server listening on {host}:{port}")
    print(f"Endpoint: POST /chat")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == '__main__':
    serve()
