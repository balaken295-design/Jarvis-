"""Jarvis web UI server. Run: python jarvis_server.py   (add --no-browser to skip opening a tab)
Serves the HUD page, a /chat endpoint (Ollama brain) and a /stats endpoint (live PC stats).
"""
import json
import platform
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import psutil

import jarvis_ollama as brain

PAGE = Path(__file__).with_name("jarvis_ui.html")
LANG_NOTE = (
    " The user may speak English or Tamil (தமிழ்). Always reply in the language the user used; "
    "if they use Tamil, reply in simple Tamil script. Tool arguments such as app names and URLs "
    "must always be in English, e.g. 'notepad' for நோட்பேட். Replies are spoken aloud, so keep them short."
)
messages = [{"role": "system", "content": brain.SYSTEM_PROMPT + LANG_NOTE}]
lock = threading.Lock()

NOWIN = 0x08000000 if platform.system() == "Windows" else 0  # hide console flashes
_net = [psutil.net_io_counters(), time.time()]
_temp = [None, 0.0]


def run(cmd, timeout=3):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, creationflags=NOWIN).stdout.strip()
    except Exception:
        return ""


def gpu():
    """NVIDIA GPUs only (uses nvidia-smi, installed with the NVIDIA driver)."""
    out = run(["nvidia-smi", "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total,name",
               "--format=csv,noheader,nounits"])
    try:
        u, t, mu, mt, name = [x.strip() for x in out.splitlines()[0].split(",")]
        return {"load": float(u), "temp": float(t), "mem": round(float(mu) / float(mt) * 100), "name": name}
    except Exception:
        return None


def cpu_temp():
    """Windows often hides CPU temperature; returns None when unavailable."""
    if time.time() - _temp[1] < 10:
        return _temp[0]
    val = None
    try:
        for entries in psutil.sensors_temperatures().values():
            if entries:
                val = entries[0].current
                break
    except Exception:
        pass
    if val is None and platform.system() == "Windows":
        out = run(["powershell", "-NoProfile", "-Command",
                   "(Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature "
                   "| Select-Object -First 1).CurrentTemperature"], 5)
        try:
            val = round(float(out) / 10 - 273.15, 1)
        except ValueError:
            pass
    _temp[:] = [val, time.time()]
    return val


def stats():
    now, io = time.time(), psutil.net_io_counters()
    dt = max(now - _net[1], 0.1)
    up = (io.bytes_sent - _net[0].bytes_sent) / dt / 1024
    down = (io.bytes_recv - _net[0].bytes_recv) / dt / 1024
    _net[:] = [io, now]
    bat = psutil.sensors_battery()
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage(str(Path.home().anchor or "/")).percent,
        "battery": {"pct": round(bat.percent), "plugged": bat.power_plugged} if bat else None,
        "up": round(up), "down": round(down),
        "cpu_temp": cpu_temp(), "gpu": gpu(),
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, body, ctype):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/stats"):
            self._send(json.dumps(stats()).encode(), "application/json")
        else:
            self._send(PAGE.read_bytes(), "text/html; charset=utf-8")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        text = json.loads(self.rfile.read(length) or b"{}").get("message", "").strip()
        with lock:
            if len(messages) > 40:  # keep memory small
                del messages[1:]
            messages.append({"role": "user", "content": text})
            try:
                reply = brain.chat_turn(messages)
            except Exception as e:
                reply = f"Sorry, my brain hit an error: {e}"
        self._send(json.dumps({"reply": reply}).encode(), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    # 127.0.0.1 = only this PC can talk to Jarvis (it can open apps, so keep it private)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Jarvis running at http://localhost:8000  (Ctrl+C to stop)")
    if "--no-browser" not in sys.argv:
        webbrowser.open("http://localhost:8000")
    server.serve_forever()
