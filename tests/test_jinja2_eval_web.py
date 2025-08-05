import json
import os
import sys
import threading
from http.server import HTTPServer

import httpx
import pytest

# Ensure project root on path for module import
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from jinja2_eval_web import JinjaHandler


@pytest.fixture(scope="module")
def server():
    httpd = HTTPServer(("localhost", 0), JinjaHandler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        yield port
    finally:
        httpd.shutdown()
        thread.join()
        httpd.server_close()


def test_render_json_header(server):
    url = f"http://localhost:{server}/render"
    resp = httpx.post(url, data={"json": json.dumps({"a": 1}), "expr": "{{ data.a }}"})
    assert resp.status_code == 200
    assert resp.headers.get("X-Result-Type") == "json"
    assert resp.text.strip() == "1"


def test_invalid_json_returns_400(server):
    url = f"http://localhost:{server}/render"
    resp = httpx.post(url, data={"json": "{invalid", "expr": "{{ 1 }}"})
    assert resp.status_code == 400
    assert "JSON parsing error" in resp.text
