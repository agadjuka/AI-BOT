"""
Максимально простая версия для тестирования деплоя
"""
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "message": "Simple server is running"}')
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
    
    def do_POST(self):
        if self.path == '/webhook':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"ok": true}')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting simple server on port {port}")
    
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"Server started on http://0.0.0.0:{port}")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped")
        server.shutdown()
