"""Serve the app: python3 -m appointment_reminders.app.server [--port 8000] [--trouble provider,bookings,worker]. ./lab demo runs this for you.

The service's logs go to this terminal, as a real server's would. --trouble makes the stand-in services fail the way real ones do.

Every module in app/api/ is loaded, so a route that a PR adds there is live too.
"""
from __future__ import annotations

import argparse
import importlib
import json
import logging
import os
import pkgutil
import traceback
from html import escape
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlsplit

from appointment_reminders.app import api
from appointment_reminders.app.api.web import Redirect, Request, TooManyRequests, app
from appointment_reminders.app.state import sample_world
from appointment_reminders.service.startup import load_settings


def load_routes() -> None:
    for module in pkgutil.iter_modules(api.__path__):
        importlib.import_module(f"{api.__name__}.{module.name}")


def make_handler(world):
    class Handler(BaseHTTPRequestHandler):
        def _serve(self, method: str) -> None:
            url = urlsplit(self.path)
            form = {}
            if method == "POST":
                length = int(self.headers.get("Content-Length") or 0)
                form = {k: v[0] for k, v in parse_qs(self.rfile.read(length).decode()).items()}
            request = Request(method, url.path, {k: v[0] for k, v in parse_qs(url.query).items()}, form, world)
            try:
                result = app.handle(request)
            except LookupError:
                return self._send(404, "text/plain", "Not found")
            except TooManyRequests:
                return self._send(429, "text/plain", "Too many requests: this route's rate limit was hit")
            except Exception:
                logging.getLogger(__name__).exception("error serving %s", url.path)
                return self._send(500, "text/html", f"<h1>Something broke</h1><pre>{escape(traceback.format_exc())}</pre>")
            if isinstance(result, Redirect):
                self.send_response(303)
                self.send_header("Location", f"{result.location}?msg={quote(result.message)}" if result.message else result.location)
                self.end_headers()
            elif isinstance(result, dict):
                self._send(200, "application/json", json.dumps(result, default=str))
            else:
                self._send(200, "text/html; charset=utf-8", result)

        def _send(self, status: int, kind: str, text: str) -> None:
            data = text.encode()
            self.send_response(status)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            self._serve("GET")

        def do_POST(self) -> None:
            self._serve("POST")

        def log_message(self, *args) -> None:  # keep the terminal quiet
            pass
    return Handler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--trouble", default="", help="comma-separated: provider, bookings, worker")
    args = parser.parse_args()
    load_settings({**os.environ, "GATEWAY_URL": os.environ.get("GATEWAY_URL", "https://provider.example.com")})
    world = sample_world()
    for name in filter(None, args.trouble.split(",")):
        if name not in world.trouble.FLAGS:
            parser.error(f"--trouble takes {', '.join(world.trouble.FLAGS)}, not {name}")
        world.trouble.on.add(world.trouble.FLAGS[name])
    logging.basicConfig(format="%(asctime)s %(levelname)-7s %(name)s: %(message)s", datefmt="%H:%M:%S", level=logging.WARNING)
    logging.getLogger("appointment_reminders").setLevel(logging.DEBUG)
    load_routes()
    try:
        server = ThreadingHTTPServer((args.host, args.port), make_handler(world))
    except OSError:
        raise SystemExit(f"Port {args.port} is already in use, probably by another demo. Stop that one with Ctrl-C in its terminal, or use --port 8001.")
    print(f"Appointment reminders is running on port {args.port}  (Ctrl-C to stop)", flush=True)
    print("Click Open in Browser, or open this port from the Ports tab.", flush=True)
    for name in sorted(world.trouble.on):
        print(f"Simulating trouble: {world.trouble.NAMES[name]}", flush=True)
    print("The service's logs appear below.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
