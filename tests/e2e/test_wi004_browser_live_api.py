from __future__ import annotations

import json
import os
import socket
import ssl
import subprocess
import time
from pathlib import Path
from urllib import error, parse, request

import websocket


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OWNER_WORKBENCH_URL = os.environ.get("VELENTRADE_OWNER_WORKBENCH_URL", "https://127.0.0.1:8443").rstrip("/")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_http(url: str, *, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            context = ssl._create_unverified_context() if url.startswith("https://") else None
            with request.urlopen(url, timeout=2, context=context) as response:
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


def _fetch_json(url: str) -> dict:
    context = ssl._create_unverified_context() if url.startswith("https://") else None
    with request.urlopen(url, timeout=5, context=context) as response:
        return json.loads(response.read().decode("utf-8"))


def _start_live_workbench(tmp_path):
    chrome_debug_port = _free_port()
    chrome_process = subprocess.Popen(
        [
            "chromium-browser",
            "--headless",
            "--disable-gpu",
            "--ignore-certificate-errors",
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

    _wait_for_http(f"{OWNER_WORKBENCH_URL}/api/team")
    _wait_for_http(OWNER_WORKBENCH_URL)
    return chrome_process, chrome_debug_port, OWNER_WORKBENCH_URL


def test_browser_owner_command_uses_live_api_on_8443(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        page = _open_chrome_page(chrome_debug_port, base_url)
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
        _terminate(chrome_process)


def test_browser_overview_pending_approval_uses_live_id_and_posts_decision(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        page = _open_chrome_page(chrome_debug_port, base_url)
        _wait_for_expression(page, "document.body && document.body.innerText.includes('自由对话')")
        approval_id = _wait_for_expression(
            page,
            "fetch('/api/approvals').then((response) => response.json()).then((payload) => payload.data.approval_center[0].approval_id)",
        )
        assert approval_id and approval_id != "ap-001"
        _wait_for_expression(
            page,
            "[...document.querySelectorAll('a')].some((item) => item.innerText.includes('待办') && item.getAttribute('href') === '/governance?panel=todos')",
        )
        page.evaluate(
            """
            window.__velentradeErrors = [];
            window.addEventListener('error', (event) => window.__velentradeErrors.push(event.message));
            window.addEventListener('unhandledrejection', (event) => window.__velentradeErrors.push(String(event.reason)));
            """
        )
        page.evaluate("[...document.querySelectorAll('a')].find((item) => item.innerText.includes('待办')).click()")
        _wait_for_expression(page, "window.location.pathname === '/governance' && window.location.search === '?panel=todos'")
        _wait_for_expression(
            page,
            f"[...document.querySelectorAll('a')].some((item) => item.innerText.includes('办理审批') && item.getAttribute('href') === '/governance/approvals/{approval_id}')",
        )
        page.evaluate("[...document.querySelectorAll('a')].find((item) => item.innerText.includes('办理审批')).click()")
        _wait_for_expression(page, f"window.location.pathname === '/governance/approvals/{approval_id}'")
        time.sleep(1)
        approval_body = page.evaluate("(document.body.innerText || document.body.innerHTML.slice(0, 5000)) + '\\nERRORS:' + JSON.stringify(window.__velentradeErrors || [])")
        assert "可选动作" in approval_body and "approval_not_found" not in approval_body, approval_body
        page.evaluate(
            """
            const buttons = [...document.querySelectorAll('button')];
            const button = buttons.find((item) => item.innerText.includes('要求修改')) || buttons.find((item) => item.innerText.includes('通过'));
            button.click();
            """
        )
        _wait_for_expression(page, "document.body.innerText.includes('后端状态')")
        decision = _wait_for_expression(
            page,
            f"fetch('/api/approvals').then((response) => response.json()).then((payload) => payload.data.approval_center.find((item) => item.approval_id === '{approval_id}').decision)",
        )
        assert decision in {"approved", "request_changes"}
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)


def test_browser_manual_todo_routes_to_finance_form_and_writes_asset(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        page = _open_chrome_page(chrome_debug_port, base_url)
        _wait_for_expression(page, "document.body && document.body.innerText.includes('自由对话')")

        page.evaluate(
            """
            fetch('/api/requests/briefs', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                raw_text: '帮我下单腾讯',
                source: 'owner_command',
                requested_scope: { intent: 'formal_investment_decision', asset_scope: 'non_a_asset', target_action: 'trade' },
                authorization_boundary: 'request_brief_only'
              })
            })
              .then((response) => response.json())
              .then((payload) => fetch(`/api/requests/briefs/${payload.data.brief_id}/confirmation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ decision: 'confirm', client_seen_version: payload.data.version || 1 })
              }));
            """
        )
        _wait_for_expression(
            page,
            "fetch('/api/tasks').then((response) => response.json()).then((payload) => payload.data.task_center.some((item) => item.task_type === 'manual_todo'))",
        )

        page.evaluate("[...document.querySelectorAll('a')].find((item) => item.innerText.includes('全景')).click()")
        _wait_for_expression(page, "window.location.pathname === '/'")
        page.evaluate("[...document.querySelectorAll('a')].find((item) => item.innerText.includes('待办')).click()")
        _wait_for_expression(page, "window.location.pathname === '/governance' && window.location.search === '?panel=todos'")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('人工待办：') && document.body.innerText.includes('去办理')",
        )
        todo_href = _wait_for_expression(
            page,
            "[...document.querySelectorAll('a')].find((item) => item.innerText.includes('去办理'))?.getAttribute('href')",
        )
        assert todo_href.startswith("/finance?todo="), todo_href
        page.evaluate(
            f"""
            window.history.pushState({{}}, '', {json.dumps(todo_href)});
            window.dispatchEvent(new PopStateEvent('popstate'));
            """
        )
        _wait_for_expression(page, "window.location.pathname === '/finance' && window.location.search.includes('todo=')")
        _wait_for_expression(page, "document.body.innerText.includes('正在办理：') && document.body.innerText.includes('提交财务档案')")
        page.evaluate(
            """
            const amount = document.querySelector('input[aria-label="估值金额"]');
            const source = document.querySelector('input[aria-label="资料来源"]');
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            setter.call(amount, '123456');
            amount.dispatchEvent(new Event('input', { bubbles: true }));
            setter.call(source, '浏览器验收');
            source.dispatchEvent(new Event('input', { bubbles: true }));
            """
        )
        page.evaluate("[...document.querySelectorAll('button')].find((item) => item.innerText.includes('提交财务档案')).click()")
        _wait_for_expression(page, "document.body.innerText.includes('财务档案已更新')")
        asset_count = _wait_for_expression(
            page,
            "fetch('/api/finance/overview').then((response) => response.json()).then((payload) => payload.data.asset_profile.length)",
        )
        assert asset_count >= 1
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)


def test_browser_investment_dossier_header_stays_compact(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001")
        page.command(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1600, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        _wait_for_expression(page, "document.body && document.body.innerText.includes('浦发银行 A 股研究')")
        _wait_for_expression(page, "!document.body.innerText.includes('正在读取最新数据')")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('辩论摘要') && document.body.innerText.includes('分析师要点') && document.body.innerText.includes('CIO 要求先补齐资产质量和息差证据')",
        )
        metrics = _wait_for_expression(
            page,
            """
            (() => {
              const header = document.querySelector('.compact-dossier-header');
              const rail = document.querySelector('.stage-rail');
              const board = document.querySelector('.stage-summary-board');
              if (!header || !rail || !board) return null;
              const headerRect = header.getBoundingClientRect();
              const railRect = rail.getBoundingClientRect();
              const boardRect = board.getBoundingClientRect();
              return {
                headerHeight: Math.round(headerRect.height),
                railTop: Math.round(railRect.top),
                railBottom: Math.round(railRect.bottom),
                headerGap: Math.round(railRect.top - headerRect.bottom),
                boardTop: Math.round(boardRect.top),
                boardBottom: Math.round(boardRect.bottom),
                topDelta: Math.abs(Math.round(boardRect.top - railRect.top)),
                bottomDelta: Math.abs(Math.round(boardRect.bottom - railRect.bottom))
              };
            })()
            """,
        )
        assert metrics["headerHeight"] <= 44, metrics
        assert metrics["headerGap"] <= 52, metrics
        assert metrics["topDelta"] <= 6, metrics
        assert metrics["bottomDelta"] <= 6, metrics
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)


def test_browser_wf001_dossier_shows_hard_dissent_and_debate_process_from_live_api(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        dossier_payload = _fetch_json(f"{base_url}/api/workflows/wf-001/dossier")["data"]
        assert any(
            item["role"] == "fundamental" and item.get("hard_dissent_reason")
            for item in dossier_payload["role_payload_drilldowns"]
        )
        assert dossier_payload["debate"]["rounds_used"] == 2
        assert dossier_payload["debate"]["cio_synthesis"]
        assert dossier_payload["debate"]["owner_summary"] == "CIO 要求先补齐资产质量和息差证据，S3 暂不放行到 S4。"
        assert dossier_payload["debate"]["core_disputes"][0]["why_it_matters"]
        assert dossier_payload["debate"]["view_change_details"]
        assert dossier_payload["debate"]["retained_dissent_details"]
        assert dossier_payload["debate"]["round_details"]
        assert dossier_payload["debate"]["next_actions"]

        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage=S2")
        _wait_for_expression(page, "document.body && document.body.innerText.includes('浦发银行 A 股研究')")
        _wait_for_expression(page, "!document.body.innerText.includes('正在读取最新数据')")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('分析师立场矩阵') && document.body.innerText.includes('结论摘要') && document.body.innerText.includes('基本面分析师') && !document.body.innerText.includes('硬异议与补证焦点') && !document.body.innerText.includes('S2 阶段判断')",
        )
        page.evaluate("[...document.querySelectorAll('[role=\"button\"]')].find((item) => item.innerText.includes('硬异议：')).click()")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('硬异议详情') && document.body.innerText.includes('资产质量修复证据不足')",
        )
        _wait_for_expression(
            page,
            "(() => { const text = [...document.querySelectorAll('.summary-focus-list .summary-focus-item')].map((item) => item.innerText).join('\\n'); return text.includes('去向：进入 S3 辩论') && text.includes('硬异议：基本面证据不足') && text.includes('证据：4 位分析师已交，平均证据 72%') && text.includes('下一步：补资产质量和息差证据'); })()",
        )
        page.evaluate("[...document.querySelectorAll('[role=\"button\"]')].find((item) => item.innerText.includes('基本面分析师')).click()")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('资产质量修复证据不足') && document.body.innerText.includes('需要补充不良率、拨备覆盖率和息差趋势')",
        )
        s2_text = page.evaluate("document.body.innerText")
        for token in ["fundamental", "neutral", "positive", "partial", "pass", "payload", "[object Object]"]:
            assert token not in s2_text

        page.close()
        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage=S3")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('CIO 要求先补齐资产质量和息差证据') && document.body.innerText.includes('观点变化') && document.body.innerText.includes('低估值可能是价值陷阱') && document.body.innerText.includes('共识 75% · 行动强度 60%') && document.querySelectorAll('.s3-debate-summary .stage-summary-pair').length >= 6 && document.querySelectorAll('.s3-debate-summary .stage-detail-row').length >= 4 && document.querySelectorAll('.stage-summary-board button').length === 0 && !document.body.innerText.includes('查看辩论详情') && !document.body.innerText.includes('完整辩论详情')",
        )
        s3_text = page.evaluate("document.body.innerText")
        assert "量化分析师：偏正面 -> 观察" in s3_text
        assert "这只影响成交，不是当前 S3 辩论受阻的原因。" not in s3_text
        for token in ["reopen_s3_debate", "not_released", "[object Object]"]:
            assert token not in s3_text
        page.evaluate("[...document.querySelectorAll('[role=\"button\"]')].find((item) => item.innerText.includes('核心分歧')).click()")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('核心分歧详情') && document.body.innerText.includes('低估值可能是价值陷阱')",
        )
        page.evaluate("[...document.querySelectorAll('[role=\"button\"]')].find((item) => item.innerText.includes('观点变化')).click()")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('观点变化详情') && document.body.innerText.includes('量化分析师：偏正面 -> 观察') && !document.body.innerText.includes('核心分歧详情')",
        )
        page.evaluate("[...document.querySelectorAll('[role=\"button\"]')].find((item) => item.innerText.includes('保留异议')).click()")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('保留异议详情') && document.body.innerText.includes('不良率拐点未确认') && document.body.innerText.includes('不能直接放行 S4')",
        )
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)


def test_browser_wf001_dossier_stage_layout_has_no_overlap_or_wide_blank(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage=S1")
        page.command(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1600, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        _wait_for_expression(page, "document.body && document.body.innerText.includes('数据准备')")
        s1_metrics = _wait_for_expression(
            page,
            """
            (() => {
              const text = document.body ? document.body.innerText : '';
              const card = document.querySelector('.s1-data-readiness-card');
              const rows = [...document.querySelectorAll('.owner-data-source-row')];
              if (!rows.length) {
                return {
                  hasCompactCard: !!card,
                  hasStatusGrid: !!document.querySelector('.s1-status-grid'),
                  hasSourceTable: !!document.querySelector('.s1-source-table'),
                  hasImpactChain: !!document.querySelector('.s1-impact-chain'),
                  twoColumnGrid: !!document.querySelector('.direct-info-grid.two'),
                  rows: 0,
                  overlaps: 0,
                  emptyState: text.includes('暂无可展示数据来源') || text.includes('本轮 S1 没有成功获取可用数据'),
                  placeholderLeak: text.includes('后端未返回数据来源') || text.includes('后端未返回字段明细')
                };
              }
              const overlaps = rows.flatMap((row) => {
                const cells = [...row.children].map((item) => item.getBoundingClientRect());
                return cells.slice(1).map((rect, index) => rect.left < cells[index].right - 1);
              });
              return {
                hasCompactCard: !!card,
                hasStatusGrid: !!document.querySelector('.s1-status-grid'),
                hasSourceTable: !!document.querySelector('.s1-source-table'),
                hasImpactChain: !!document.querySelector('.s1-impact-chain'),
                twoColumnGrid: !!document.querySelector('.direct-info-grid.two'),
                rows: rows.length,
                overlaps: overlaps.filter(Boolean).length,
                emptyState: false,
                placeholderLeak: text.includes('后端未返回数据来源') || text.includes('后端未返回字段明细')
              };
            })()
            """,
        )
        assert s1_metrics["hasCompactCard"], s1_metrics
        assert s1_metrics["hasStatusGrid"], s1_metrics
        assert s1_metrics["hasImpactChain"], s1_metrics
        assert not s1_metrics["twoColumnGrid"], s1_metrics
        assert s1_metrics["overlaps"] == 0, s1_metrics
        assert not s1_metrics["placeholderLeak"], s1_metrics
        s1_text = page.evaluate("document.body.innerText")
        if s1_metrics["rows"] == 0:
            assert s1_metrics["emptyState"], s1_metrics
        else:
            assert s1_metrics["hasSourceTable"], s1_metrics
            assert "已取得字段" in s1_text
            for field in ["标的代码", "交易日", "收盘价", "成交量", "来源时间戳"]:
                assert field in s1_text
            assert "可用于研究判断" in s1_text
            assert "未取得 · 不能用于成交" in s1_text
        assert "缺失 · 缺失" not in s1_text
        assert "已获取：标的代码、交易日、收盘价、成交量、来源时间戳" not in s1_text
        assert "已获取 · 可用于研究判断" not in s1_text
        assert "字段：标的代码" not in s1_text

        page.close()
        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage=S2")
        page.command(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1600, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        _wait_for_expression(page, "document.body && document.body.innerText.includes('分析师立场矩阵')")
        page.evaluate("[...document.querySelectorAll('[role=\"button\"]')].find((item) => item.innerText.includes('基本面分析师')).click()")
        layout_metrics = _wait_for_expression(
            page,
            """
            (() => {
              const board = document.querySelector('.stage-summary-board');
              const sheet = document.querySelector('.dossier-detail-sheet');
              if (!board || !sheet) return null;
              const boardRect = board.getBoundingClientRect();
              const sheetRect = sheet.getBoundingClientRect();
              return {
                gap: Math.round(sheetRect.left - boardRect.right),
                rightBlank: Math.round(window.innerWidth - sheetRect.right),
                sheetWidth: Math.round(sheetRect.width)
              };
            })()
            """,
        )
        assert 8 <= layout_metrics["gap"] <= 32, layout_metrics
        assert layout_metrics["rightBlank"] <= 56, layout_metrics
        assert layout_metrics["sheetWidth"] >= 500, layout_metrics

        page.close()
        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage=S2")
        page.command(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1600, "height": 900, "deviceScaleFactor": 1, "mobile": False},
        )
        _wait_for_expression(page, "document.body && document.body.innerText.includes('分析师立场矩阵')")
        matrix_metrics = _wait_for_expression(
            page,
            """
            (() => {
              const header = document.querySelector('.analyst-matrix-header');
              const row = document.querySelector('.analyst-matrix-card .matrix-row');
              const conclusionRow = document.querySelector('.s2-conclusion-list [role="button"]');
              if (!header || !row) return null;
              const headerRole = header.children[0].getBoundingClientRect();
              const rowRole = row.children[0].getBoundingClientRect();
              const rowStyle = getComputedStyle(row);
              const conclusionStyle = conclusionRow ? getComputedStyle(conclusionRow) : null;
              return {
                headerRoleWidth: Math.round(headerRole.width),
                rowRoleWidth: Math.round(rowRole.width),
                rowHeight: Math.round(row.getBoundingClientRect().height),
                rowFontSize: parseFloat(rowStyle.fontSize),
                conclusionFontSize: conclusionStyle ? parseFloat(conclusionStyle.fontSize) : 0
              };
            })()
            """,
        )
        assert matrix_metrics["headerRoleWidth"] <= 190, matrix_metrics
        assert matrix_metrics["rowRoleWidth"] <= 190, matrix_metrics
        assert matrix_metrics["rowHeight"] >= 42, matrix_metrics
        assert matrix_metrics["rowFontSize"] >= 13, matrix_metrics
        assert matrix_metrics["conclusionFontSize"] >= 13, matrix_metrics

        page.close()
        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage=S3")
        page.command(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1600, "height": 760, "deviceScaleFactor": 1, "mobile": False},
        )
        _wait_for_expression(page, "document.body && document.body.innerText.includes('辩论摘要') && document.body.innerText.includes('事件分析师')")
        s3_metrics = _wait_for_expression(
            page,
            """
            (() => {
              const firstPair = document.querySelector('.s3-debate-summary .stage-summary-pair');
              const analystRows = [...document.querySelectorAll('.s3-analyst-summary-row')];
              const panel = document.querySelector('.s3-analyst-summary-row')?.closest('.direct-info-panel');
              const board = document.querySelector('.stage-summary-board');
              if (!firstPair || analystRows.length !== 4 || !panel || !board) return null;
              const label = firstPair.children[0].getBoundingClientRect();
              const value = firstPair.children[1].getBoundingClientRect();
              const row = firstPair.getBoundingClientRect();
              const panelRect = panel.getBoundingClientRect();
              const boardRect = board.getBoundingClientRect();
              return {
                labelWidth: Math.round(label.width),
                valueStartOffset: Math.round(value.left - row.left),
                labelValueGap: Math.round(value.left - label.right),
                analystCount: analystRows.length,
                lastAnalystBottom: Math.round(analystRows[3].getBoundingClientRect().bottom),
                analystPanelBottom: Math.round(panelRect.bottom),
                boardBottom: Math.round(boardRect.bottom),
                viewportBottom: window.innerHeight,
                analystPanelScrollOverflow: Math.ceil(panel.scrollHeight - panel.clientHeight)
              };
            })()
            """,
        )
        assert s3_metrics["labelWidth"] <= 96, s3_metrics
        assert s3_metrics["valueStartOffset"] <= 128, s3_metrics
        assert s3_metrics["labelValueGap"] <= 32, s3_metrics
        assert s3_metrics["analystCount"] == 4, s3_metrics
        assert s3_metrics["lastAnalystBottom"] <= s3_metrics["analystPanelBottom"] + 1, s3_metrics
        assert s3_metrics["boardBottom"] <= s3_metrics["viewportBottom"] - 12, s3_metrics
        assert s3_metrics["analystPanelScrollOverflow"] <= 1, s3_metrics

        for stage in ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7"]:
            page.close()
            page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage={stage}")
            page.command(
                "Emulation.setDeviceMetricsOverride",
                {"width": 1600, "height": 760, "deviceScaleFactor": 1, "mobile": False},
            )
            _wait_for_expression(page, "document.body && !document.body.innerText.includes('正在读取最新数据')")
            stage_density = _wait_for_expression(
                page,
                """
                (() => {
                  const board = document.querySelector('.stage-summary-board');
                  const content = document.querySelector('.stage-summary-board > .stage-summary-grid, .stage-summary-board > .direct-info-grid');
                  if (!board || !content) return null;
                  const boardRect = board.getBoundingClientRect();
                  const contentRect = content.getBoundingClientRect();
                  return {
                    stage: new URL(location.href).searchParams.get('stage'),
                    boardHeight: Math.round(boardRect.height),
                    contentHeight: Math.round(contentRect.height),
                    contentBottom: Math.round(contentRect.bottom),
                    boardBottom: Math.round(boardRect.bottom),
                    freeBelow: Math.round(boardRect.bottom - contentRect.bottom)
                  };
                })()
                """,
            )
            assert stage_density["freeBelow"] >= 16, stage_density
            assert stage_density["contentHeight"] <= stage_density["boardHeight"] - 16, stage_density
            stage_overflow = _wait_for_expression(
                page,
                """
                (() => {
                  const panels = [...document.querySelectorAll('.stage-summary-board .direct-info-panel, .stage-summary-board .summary-card, .stage-summary-board .stage-summary-section-list')];
                  if (!panels.length) return null;
                  return panels.map((panel) => ({
                    className: panel.className,
                    text: panel.innerText.slice(0, 40),
                    overflow: Math.ceil(panel.scrollHeight - panel.clientHeight)
                  }));
                })()
                """,
            )
            assert all(item["overflow"] <= 1 for item in stage_overflow), {"stage": stage, "overflow": stage_overflow}

        page.close()
        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001?stage=S7")
        page.command(
            "Emulation.setDeviceMetricsOverride",
            {"width": 1600, "height": 760, "deviceScaleFactor": 1, "mobile": False},
        )
        _wait_for_expression(page, "document.body && document.body.innerText.includes('归因复盘')")
        s7_fit_metrics = _wait_for_expression(
            page,
            """
            (() => {
              const rail = document.querySelector('.stage-rail');
              const board = document.querySelector('.stage-summary-board');
              const s7 = [...document.querySelectorAll('.stage-chip')].find((item) => item.innerText.includes('S7'));
              if (!rail || !board || !s7) return null;
              const railRect = rail.getBoundingClientRect();
              const boardRect = board.getBoundingClientRect();
              const s7Rect = s7.getBoundingClientRect();
              const viewportBottom = window.innerHeight;
              return {
                viewportBottom,
                railBottom: Math.round(railRect.bottom),
                boardBottom: Math.round(boardRect.bottom),
                s7Bottom: Math.round(s7Rect.bottom),
                documentScrollHeight: document.documentElement.scrollHeight,
                bodyScrollHeight: document.body.scrollHeight
              };
            })()
            """,
        )
        assert s7_fit_metrics["railBottom"] <= s7_fit_metrics["viewportBottom"] - 12, s7_fit_metrics
        assert s7_fit_metrics["boardBottom"] <= s7_fit_metrics["viewportBottom"] - 12, s7_fit_metrics
        assert s7_fit_metrics["s7Bottom"] <= s7_fit_metrics["viewportBottom"] - 12, s7_fit_metrics
        assert s7_fit_metrics["documentScrollHeight"] <= s7_fit_metrics["viewportBottom"], s7_fit_metrics
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)


def test_browser_wf001_trace_uses_live_process_records_without_default_ids(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        runs = _fetch_json(f"{base_url}/api/workflows/wf-001/agent-runs")["data"]
        events = _fetch_json(f"{base_url}/api/workflows/wf-001/collaboration-events")["data"]
        handoffs = _fetch_json(f"{base_url}/api/workflows/wf-001/handoffs")["data"]
        assert runs
        assert events
        assert handoffs
        assert any(item.get("run_goal") for item in runs)
        assert any((item.get("payload") or {}).get("business_summary") for item in events)

        page = _open_chrome_page(chrome_debug_port, f"{base_url}/investment/wf-001/trace")
        _wait_for_expression(page, "document.body && document.body.innerText.includes('流程审计')")
        _wait_for_expression(page, "!document.body.innerText.includes('正在读取最新数据')")
        _wait_for_expression(
            page,
            "document.body.innerText.includes('CIO 汇总四位分析师 Memo') && document.body.innerText.includes('CIO 将保留的基本面硬异议交给风控复核')",
        )
        text = page.evaluate("document.body.innerText")
        for token in ["run-", "ctx-", "AgentRun", "profile@", "event-wf001", "handoff-wf001"]:
            assert token not in text
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)


def test_browser_finance_approval_and_config_hide_known_backend_tokens(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        approvals = _fetch_json(f"{base_url}/api/approvals")["data"]["approval_center"]
        assert approvals
        approval_id = approvals[0]["approval_id"]

        checked_routes = [
            f"{base_url}/finance",
            f"{base_url}/governance/approvals/{approval_id}",
            f"{base_url}/governance/team/fundamental_analyst/config",
        ]
        forbidden_tokens = [
            "approve_exception_only_if_risk_accepted",
            "current_attempt_only",
            "follow_optimizer",
            "cio_deviation",
            "timeout_means_no_execution",
            "trade_chain_allowed",
            "tax_reminder",
            "default_skill_packages",
            "fundamental_analyst",
            "[object Object]",
        ]
        for route in checked_routes:
            if page is not None:
                page.close()
            page = _open_chrome_page(chrome_debug_port, route)
            _wait_for_expression(page, "document.body && !document.body.innerText.includes('正在读取最新数据')")
            text = page.evaluate("document.body ? document.body.innerText : ''") or ""
            for token in forbidden_tokens:
                assert token not in text, f"{token} leaked on {route}"
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)


def test_browser_governance_team_cards_open_live_profiles_without_blank_page(tmp_path):
    chrome_process, chrome_debug_port, base_url = _start_live_workbench(tmp_path)
    page: ChromePage | None = None
    try:
        for agent_id in ["cio", "fundamental_analyst"]:
            if page is not None:
                page.close()
            page = _open_chrome_page(chrome_debug_port, f"{base_url}/governance?panel=team")
            _wait_for_expression(page, "document.body && document.body.innerText.includes('团队')")
            page.evaluate(
                """
                window.__velentradeErrors = [];
                window.addEventListener('error', (event) => window.__velentradeErrors.push(event.message));
                window.addEventListener('unhandledrejection', (event) => window.__velentradeErrors.push(String(event.reason)));
                """
            )
            _wait_for_expression(
                page,
                f"[...document.querySelectorAll('a')].some((item) => item.getAttribute('href') === '/governance/team/{agent_id}')",
            )
            page.evaluate(
                f"""
                const link = [...document.querySelectorAll('a')]
                  .find((item) => item.getAttribute('href') === '/governance/team/{agent_id}');
                link.click();
                """
            )
            _wait_for_expression(page, f"window.location.pathname === '/governance/team/{agent_id}'")
            _wait_for_expression(
                page,
                "document.body.innerText.includes('能做什么') && document.body.innerText.includes('版本与权限') && document.body.innerText.includes('能力提升方案')",
            )
            _wait_for_expression(page, "!document.body.innerText.includes('正在读取最新数据')")
            text = page.evaluate("document.body ? document.body.innerText : ''") or ""
            assert text.strip(), f"profile page for {agent_id} rendered blank"
            assert "[object Object]" not in text
            assert agent_id not in text
            errors = page.evaluate("window.__velentradeErrors || []")
            assert errors == [], errors
    finally:
        if page is not None:
            page.close()
        _terminate(chrome_process)
