from http.server import BaseHTTPRequestHandler
import json


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(
            {
                "ok": True,
                "service": "beast-bot",
                "platform": "vercel",
                "hint": "POST Telegram updates to /api/webhook",
            }
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        self.do_GET()
