"""Локальний JSON-сервер для навантажувального тесту."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from urllib.parse import urlsplit


class JsonHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        found = urlsplit(self.path).path == "/"
        payload = {"status": "ok"} if found else {"error": "not found"}
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200 if found else 404)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def serve(host="127.0.0.1", port=8085):
    with ThreadingHTTPServer((host, port), JsonHandler) as server:
        print(f"JSON server http://{host}:{server.server_address[1]}/", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JSON-сервер для Molotov")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8085)
    args = parser.parse_args()
    try:
        serve(args.host, args.port)
    except KeyboardInterrupt:
        print("\nJSON-сервер зупинено.", flush=True)
