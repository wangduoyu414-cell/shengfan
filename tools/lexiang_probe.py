#!/usr/bin/env python3
"""乐享 MCP 连通验证（X07，只读）：执行 D12 §8 的 V-LX01、V-LX03、V-LX04、V-LX06。

用法：
  export LEXIANG_COMPANY=你的乐享code          # 登录乐享后在 https://lexiangla.com/mcp 获取
  export LEXIANG_TOKEN=你的令牌                 # OAuth 令牌，或"会话管理"里新建会话得到的 access_token
  python3 lexiang_probe.py [--preset meta] [--auth header|url] [--query 关键词]

说明：
- 令牌只从环境变量读取，不打印、不写入文件（D07 §6）。
- 只调用读类工具（列工具、列知识库、检索）；不调用任何写入或删除工具。
- --auth header：放在 Authorization 请求头（OAuth 令牌）；--auth url：作为 access_token 参数（会话管理令牌）。
只用 Python 标准库。
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://mcp.lexiang-app.com/mcp"
READ_ONLY = {"knowledge_list_spaces", "search_kb_search", "search_kb_embedding_search",
             "knowledge_describe_ai_parse_content", "list_tool_categories", "search_tools", "get_tool_schema"}


class Client:
    def __init__(self, company, token, preset, auth):
        q = {"company_from": company}
        if preset:
            q["preset"] = preset
        if auth == "url":
            q["access_token"] = token
        self.url = f"{BASE}?{urllib.parse.urlencode(q)}"
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if auth == "header":
            self.headers["Authorization"] = f"Bearer {token}"
        self.session = None
        self.n = 0

    def call(self, method, params=None, notify=False):
        self.n += 1
        body = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            body["params"] = params
        if not notify:
            body["id"] = self.n
        h = dict(self.headers)
        if self.session:
            h["Mcp-Session-Id"] = self.session
        req = urllib.request.Request(self.url, data=json.dumps(body).encode(), headers=h, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                self.session = resp.headers.get("Mcp-Session-Id") or self.session
                raw = resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return {"error": {"code": e.code, "message": e.read().decode("utf-8", "replace")[:300]}}
        if notify or not raw.strip():
            return {}
        if raw.lstrip().startswith("{"):
            return json.loads(raw)
        for line in raw.splitlines():  # text/event-stream
            if line.startswith("data:"):
                try:
                    msg = json.loads(line[5:].strip())
                    if msg.get("id") == self.n:
                        return msg
                except json.JSONDecodeError:
                    continue
        return {"error": {"message": "无法解析响应"}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preset", default="")
    ap.add_argument("--auth", choices=["header", "url"], default="header")
    ap.add_argument("--query")
    a = ap.parse_args()
    company, token = os.environ.get("LEXIANG_COMPANY"), os.environ.get("LEXIANG_TOKEN")
    if not company or not token:
        sys.exit("请先设置环境变量 LEXIANG_COMPANY 和 LEXIANG_TOKEN（见脚本说明）。")
    c = Client(company, token, a.preset, a.auth)

    init = c.call("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                 "clientInfo": {"name": "lexiang-probe", "version": "1.0"}})
    if "error" in init:
        sys.exit(f"V-LX01 连接：失败 {init['error']}（检查 company_from 与令牌；令牌方式不对时试 --auth url）")
    print(f"V-LX01 连接：成功（服务端 {init.get('result', {}).get('serverInfo', {})}）")
    c.call("notifications/initialized", notify=True)

    tools = c.call("tools/list", {})
    names = [t["name"] for t in tools.get("result", {}).get("tools", [])]
    print(f"V-LX02 preset={a.preset or '（不填）'}：返回 {len(names)} 个工具：{', '.join(names)}")

    def call_tool(name, args):
        if name not in READ_ONLY:
            return {"error": {"message": f"拒绝调用非只读工具 {name}"}}
        return c.call("tools/call", {"name": name, "arguments": args})

    if "knowledge_list_spaces" in names:
        r = call_tool("knowledge_list_spaces", {})
        print(f"V-LX03 列知识库：{json.dumps(r.get('result', r.get('error')), ensure_ascii=False)[:800]}")
    else:
        print("V-LX03 列知识库：当前 preset 下没有该工具（元工具模式请用 search_tools / call_tool 手动验证）")

    if a.query:
        tool = next((t for t in tools.get("result", {}).get("tools", []) if t["name"] == "search_kb_search"), None)
        if not tool:
            print("V-LX04 关键词检索：当前 preset 下没有 search_kb_search")
        else:
            props = tool.get("inputSchema", {}).get("properties", {})
            key = next((k for k, v in props.items() if v.get("type") == "string"), None)
            if not key:
                print(f"V-LX04 关键词检索：无法确定参数名，参数定义为 {json.dumps(props, ensure_ascii=False)}")
            else:
                r = call_tool("search_kb_search", {key: a.query})
                print(f"V-LX04 关键词检索（{key}={a.query}）：{json.dumps(r.get('result', r.get('error')), ensure_ascii=False)[:1200]}")
    print("V-LX06 读取正文：请用检索结果中的条目编号，在已连接的平台中调用 knowledge_describe_ai_parse_content 验证。")


if __name__ == "__main__":
    main()
