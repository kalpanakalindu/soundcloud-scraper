"""Vercel entry point for the SoundCloud Scraper (a bottle/WSGI app).

Vercel looks for a WSGI callable named `app`. This file mounts the scraper's
routes, restores the original request path (vercel.json passes it as `__p`),
and adds CORS headers so your web player (on another domain) can call it.
"""
import os
import sys
from urllib.parse import parse_qsl, urlencode

# Make the repo root importable (routes.py, config.py, soundcloud/ live there)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bottle
import routes  # noqa: F401  (registers all 42 endpoints on bottle's default app)

_bottle_app = bottle.default_app()

CORS = [
    ("Access-Control-Allow-Origin", "*"),
    ("Access-Control-Allow-Methods", "GET, OPTIONS"),
    ("Access-Control-Allow-Headers", "*"),
]


def _restore_path(environ):
    """vercel.json rewrites /anything -> /api/index?__p=anything.
    Put the original path back so bottle can route it."""
    pairs = parse_qsl(environ.get("QUERY_STRING", ""), keep_blank_values=True)
    original = None
    rest = []
    for key, value in pairs:
        if key == "__p" and original is None:
            original = value
        else:
            rest.append((key, value))

    if original is not None:
        environ["PATH_INFO"] = "/" + original.lstrip("/")
        environ["QUERY_STRING"] = urlencode(rest)
    elif environ.get("PATH_INFO", "").rstrip("/") == "/api/index":
        environ["PATH_INFO"] = "/"


def app(environ, start_response):
    # Answer browser preflight requests
    if environ.get("REQUEST_METHOD") == "OPTIONS":
        start_response("204 No Content", CORS)
        return [b""]

    _restore_path(environ)

    def _start(status, headers, exc_info=None):
        headers = [h for h in headers if h[0].lower() != "access-control-allow-origin"]
        return start_response(status, headers + CORS, exc_info)

    return _bottle_app(environ, _start)
