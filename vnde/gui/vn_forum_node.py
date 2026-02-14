#!/usr/bin/env python3
import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DATA_DIR = os.path.expanduser("~/.local/share/vnde")
POSTS_FILE = os.path.join(DATA_DIR, "forum_posts.json")
PEERS_FILE = os.path.join(DATA_DIR, "forum_peers.json")

NODE_PORT = int(os.environ.get("VNFORUM_PORT", "17890"))
DISCOVERY_PORT = int(os.environ.get("VNFORUM_DISCOVERY_PORT", "17891"))

DISCOVERY_INTERVAL = 6
SYNC_INTERVAL = 12
PEER_TTL = 90

LOCK = threading.Lock()
HOSTNAME = socket.gethostname()


def ensure_store():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    if not os.path.exists(PEERS_FILE):
        with open(PEERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)


def load_json(path, fallback):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def save_json(path, data):
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def normalize_post(post):
    p = dict(post)
    p.setdefault("title", "")
    p.setdefault("body", "")
    p.setdefault("author", "user")
    p.setdefault("origin", HOSTNAME)
    p.setdefault("created", time.strftime("%d/%m/%Y %H:%M"))
    p.setdefault("created_ts", int(time.time()))
    p.setdefault("id", str(uuid.uuid4()))
    return p


def merge_posts(incoming):
    ensure_store()
    with LOCK:
        local = load_json(POSTS_FILE, [])
        by_id = {}
        for p in local:
            np = normalize_post(p)
            by_id[np["id"]] = np
        for p in incoming:
            np = normalize_post(p)
            by_id[np["id"]] = np
        merged = sorted(by_id.values(), key=lambda x: x.get("created_ts", 0), reverse=True)
        save_json(POSTS_FILE, merged)
        return len(merged)


def update_peer(ip, port, host):
    ensure_store()
    with LOCK:
        peers = load_json(PEERS_FILE, {})
        peers[ip] = {"port": int(port), "host": host, "last_seen": int(time.time())}
        save_json(PEERS_FILE, peers)


def live_peers():
    ensure_store()
    now = int(time.time())
    with LOCK:
        peers = load_json(PEERS_FILE, {})
        peers = {k: v for k, v in peers.items() if now - int(v.get("last_seen", 0)) <= PEER_TTL}
        save_json(PEERS_FILE, peers)
        return peers


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            self._send(200, {"ok": True, "host": HOSTNAME, "port": NODE_PORT})
            return
        if self.path == "/posts":
            ensure_store()
            self._send(200, load_json(POSTS_FILE, []))
            return
        if self.path == "/peers":
            self._send(200, live_peers())
            return
        self._send(404, {"ok": False, "error": "not_found"})

    def do_POST(self):
        if self.path != "/merge":
            self._send(404, {"ok": False, "error": "not_found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, list):
                raise ValueError("payload must be list")
            total = merge_posts(data)
            self._send(200, {"ok": True, "total_posts": total})
        except Exception as e:
            self._send(400, {"ok": False, "error": str(e)})

    def log_message(self, _fmt, *_args):
        return


def discovery_broadcast():
    payload = json.dumps({"type": "vnforum_hello", "port": NODE_PORT, "host": HOSTNAME}).encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    while True:
        try:
            sock.sendto(payload, ("255.255.255.255", DISCOVERY_PORT))
        except Exception:
            pass
        time.sleep(DISCOVERY_INTERVAL)


def discovery_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", DISCOVERY_PORT))
    while True:
        try:
            raw, addr = sock.recvfrom(4096)
            msg = json.loads(raw.decode("utf-8"))
            if msg.get("type") != "vnforum_hello":
                continue
            ip = addr[0]
            if ip.startswith("127."):
                continue
            port = int(msg.get("port", NODE_PORT))
            host = str(msg.get("host", "peer"))
            update_peer(ip, port, host)
        except Exception:
            pass


def fetch_posts(ip, port):
    url = f"http://{ip}:{port}/posts"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=2.5) as r:
        return json.loads(r.read().decode("utf-8"))


def sync_loop():
    while True:
        peers = live_peers()
        for ip, info in peers.items():
            port = int(info.get("port", NODE_PORT))
            try:
                posts = fetch_posts(ip, port)
                if isinstance(posts, list):
                    merge_posts(posts)
            except (urllib.error.URLError, TimeoutError, ValueError, OSError):
                continue
        time.sleep(SYNC_INTERVAL)


def already_running():
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{NODE_PORT}/status", timeout=0.8) as r:
            data = json.loads(r.read().decode("utf-8"))
            return bool(data.get("ok"))
    except Exception:
        return False


def main():
    ensure_store()
    if already_running():
        return

    threading.Thread(target=discovery_broadcast, daemon=True).start()
    threading.Thread(target=discovery_listener, daemon=True).start()
    threading.Thread(target=sync_loop, daemon=True).start()

    httpd = ThreadingHTTPServer(("0.0.0.0", NODE_PORT), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
