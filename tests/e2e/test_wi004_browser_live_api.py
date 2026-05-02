from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, parse, request

import websocket


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_http(url: str, *, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return
        except (error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            time.sleep(0.5)
    raise RuntimeError(f"{url} did not become ready: {last_error}")


def _terminate(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)


class ChromePage:
    def __init__(self, ws_url: str) -> None:
        self.ws = websocket.create_connection(ws_url, timeout=5, suppress_origin=True)
        self.next_id = 0

    def close(self) -> None:
        self.ws.close()

    def command(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        message_id = self.next_id
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        while True:
            payload = json.loads(self.ws.recv())
            if payload.get("id") == message_id:
                if "error" in payload:
                    raise RuntimeError(payload["error"])
                return payload.get("result", {})

    def evaluate(self, expression: str):
        result = self.command(
            "Runtime.evaluate",
            {"expression": expression, "awaitPromise": True, "returnByValue": True},
        )
        return result.get("result", {}).get("value")


def _open_chrome_page(chrome_debug_port: int, url: str) -> ChromePage:
    _wait_for_http(f"http://127.0.0.1:{chrome_debug_port}/json/version")
    new_tab = request.Request(
        f"http://127.0.0.1:{chrome_debug_port}/json/new?{parse.quote(url, safe='')}",
        method="PUT",
    )
    with request.urlopen(new_tab, timeout=5) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return ChromePage(payload["webSocketDebuggerUrl"])


def _wait_for_expression(page: ChromePage, expression: str, *, timeout_seconds: int = 30):
    deadline = time.time() + timeout_seconds
    last_value = None
    while time.time() < deadline:
        last_value = page.evaluate(expression)
        if last_value:
            return last_value
        time.sleep(0.25)
    raise AssertionError(f"expression did not become truthy: {expression}; last={last_value!r}")


def test_browser_owner_command_uses_live_fastapi_via_vite_proxy(tmp_path):
    api_port = _free_port()
    vite_port = _free_port()
    chrome_debug_port = _free_port()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    env["VELENTRADE_API_PROXY_TARGET"] = f"http://127.0.0.1:{api_port}"

    api_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "--factory",
            "velentrade.api.app:build_app",
            "--host",
            "127.0.0.1",
            "--port",
            str(api_port),
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    vite_process = subprocess.Popen(
        [
            "npm",
            "--prefix",
            "frontend",
            "run",
            "dev",
            "--",
            "--host",
            "127.0.0.1",
            "--port",
            str(vite_port),
            "--strictPort",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    chrome_process = subprocess.Popen(
        [
            "chromium-browser",
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            f"--remote-debugging-port={chrome_debug_port}",
            f"--user-data-dir={tmp_path / 'chrome-profile'}",
            "about:blank",
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    page: ChromePage | None = None
    try:
        _wait_for_http(f"http://127.0.0.1:{api_port}/api/team")
        _wait_for_http(f"http://127.0.0.1:{vite_port}")
        page = _open_chrome_page(chrome_debug_port, f"http://127.0.0.1:{vite_port}")
        _wait_for_expression(page, "document.body && document.body.innerText.includes('自由对话')")

        page.evaluate("[...document.querySelectorAll('button')].find((item) => item.innerText.includes('自由对话')).click()")
        _wait_for_expression(page, "document.body.innerText.includes('输入一句话后生成预览')")
        page.evaluate(
            """
            const input = document.querySelector('input[aria-label="自然语言请求"]');
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(input, '请正式研究浦发银行');
            input.dispatchEvent(new Event('input', { bubbles: true }));
            """
        )
        page.evaluate("[...document.querySelectorAll('button')].find((item) => item.innerText.includes('生成请求预览')).click()")
        _wait_for_expression(page, "document.body.innerText.includes('确认生成任务卡')")
        _wait_for_expression(
            page,
            "(() => { const button = [...document.querySelectorAll('button')].find((item) => item.innerText.includes('确认生成任务卡')); return button && !button.disabled; })()",
        )
        page.evaluate("[...document.querySelectorAll('button')].find((item) => item.innerText.includes('确认生成任务卡')).click()")
        _wait_for_expression(page, "document.body.innerText.includes('任务卡已生成：')")
        _wait_for_expression(page, "document.body.innerText.includes('打开投资档案')")
        page.evaluate("[...document.querySelectorAll('a')].find((item) => item.innerText.includes('打开投资档案')).click()")
        _wait_for_expression(page, "window.location.pathname.startsWith('/investment/')")
        _wait_for_expression(page, "document.body.innerText.includes('投资档案') && document.body.innerText.includes('S0')")
        task_count = _wait_for_expression(
            page,
            "fetch('/api/tasks').then((response) => response.json()).then((payload) => payload.data.task_center.length)",
        )
        assert task_count >= 1
    finally:
        if page is not None:
            page.close()
        for process in (chrome_process, vite_process, api_process):
            _terminate(process)
