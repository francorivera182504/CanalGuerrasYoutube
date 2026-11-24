"""Cliente mínimo del servidor MCP local de OpenReel (lee ~/.openreel/mcp-endpoint.json).
No imprime el token. Uso: from openreel_api import call; call("list_clips")"""
import json, os, urllib.request

def _ep():
    return json.load(open(os.path.expanduser("~/.openreel/mcp-endpoint.json"), encoding="utf-8"))

def call(name, args=None, timeout=600):
    ep = _ep()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": args or {}}}).encode()
    req = urllib.request.Request(ep["url"], body, {"Content-Type": "application/json",
                                                   "Authorization": "Bearer " + ep["token"]})
    res = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    r = res.get("result", {})
    text = "".join(c.get("text", "") for c in r.get("content", []))
    if r.get("isError") or "error" in res:
        raise RuntimeError(f"{name}: {text or res.get('error')}")
    # el JSON útil viene después de la primera línea en blanco
    if "\n\n" in text:
        try:
            return json.loads(text.split("\n\n", 1)[1])
        except Exception:
            pass
    return text
