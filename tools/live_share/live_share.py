#!/usr/bin/env python3
"""
live_share.py — live text clipboard + file drop, two machines, one button to flip.

Usage:
    python3 tools/live_share/live_share.py [port]                (default port 8000)
    python3 tools/live_share/live_share.py 8000 --max-upload-mb 100
    python3 tools/live_share/live_share.py --print-hosts         (print /etc/hosts setup and exit)
    python3 tools/live_share/live_share.py --print-hosts liveshare  (custom hostname)

Ubuntu PC  → http://liveshare:8000  (after one-time /etc/hosts setup)
Laptop     → http://liveshare:8000  (after one-time /etc/hosts setup)

Clicking the button on EITHER side flips both simultaneously.
Files are held in RAM — they vanish when the server stops.
"""

import http.server
import io
import json
import re
import socket
import sys
import threading
import time
from urllib.parse import urlparse


def _get_lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


# ── CLI args ───────────────────────────────────────────────────────────────────
_MAX_UPLOAD_MB = 50
for _i, _a in enumerate(sys.argv):
    if _a == "--max-upload-mb" and _i + 1 < len(sys.argv):
        try:
            _MAX_UPLOAD_MB = int(sys.argv[_i + 1])
        except ValueError:
            pass

# ── --print-hosts helper (runs and exits immediately) ─────────────────────────
if "--print-hosts" in sys.argv:
    _ph_idx = sys.argv.index("--print-hosts")
    _dns_name = (
        sys.argv[_ph_idx + 1]
        if _ph_idx + 1 < len(sys.argv)
        and not sys.argv[_ph_idx + 1].startswith("-")
        else "liveshare"
    )
    _lan_ip = _get_lan_ip()
    # detect default port from remaining args
    _ph_port = 8000
    for _a in sys.argv[1:]:
        if _a.isdigit():
            _ph_port = int(_a)
            break
    print(f"""
  ┌─────────────────────────────────────────────────────────┐
  │  One-time /etc/hosts setup for http://{_dns_name}:{_ph_port}
  └─────────────────────────────────────────────────────────┘

  On THIS Ubuntu PC — add to /etc/hosts:
      127.0.0.1   {_dns_name}

  On the LAPTOP — add to /etc/hosts:
    Linux / macOS:
      sudo sh -c 'echo "{_lan_ip}   {_dns_name}" >> /etc/hosts'

    Windows (run as admin in PowerShell):
      Add-Content C:\\Windows\\System32\\drivers\\etc\\hosts "{_lan_ip}   {_dns_name}"

  After editing:
      http://{_dns_name}:{_ph_port}   → works on BOTH machines

  To undo:  remove the "{_dns_name}" line from both hosts files.
""")
    sys.exit(0)

# ── Shared state ───────────────────────────────────────────────────────────────
_lock = threading.Lock()

_state = {
    "text": "",
    "version": 0,
    "source_side": "ubuntu",
}

# _files: { filename: {"name": str, "size": int, "data": bytes, "uploaded_at": float} }
_files: dict = {}


def _side_from_request(handler) -> str:
    client_ip = handler.client_address[0]
    fwd = handler.headers.get("X-Forwarded-For", "")
    ip = fwd.split(",")[0].strip() if fwd else client_ip
    return "ubuntu" if ip in ("127.0.0.1", "::1", "localhost") else "laptop"


def _state_for_side(side: str) -> dict:
    d = dict(_state)
    d["my_role"] = "source" if d["source_side"] == side else "receiver"
    d["files"] = [
        {
            "name": v["name"],
            "size": v["size"],
            "uploaded_at": round(v["uploaded_at"]),
        }
        for v in _files.values()
    ]
    return d


# ── Multipart parser (stdlib only) ────────────────────────────────────────────
def _parse_multipart(content_type: str, body: bytes):
    """Yield (name, filename, data) tuples from a multipart/form-data body."""
    m = re.search(r"boundary=([^\s;]+)", content_type)
    if not m:
        return
    boundary = ("--" + m.group(1)).encode()
    parts = body.split(boundary)
    for part in parts[1:]:
        if part.strip() in (b"", b"--", b"--\r\n"):
            continue
        # Split headers from body
        if b"\r\n\r\n" in part:
            headers_raw, data = part.split(b"\r\n\r\n", 1)
        elif b"\n\n" in part:
            headers_raw, data = part.split(b"\n\n", 1)
        else:
            continue
        # Strip trailing boundary marker
        data = data.rstrip(b"\r\n")
        if data.endswith(b"--"):
            data = data[:-2].rstrip(b"\r\n")
        headers_raw = headers_raw.lstrip(b"\r\n")
        # Extract filename
        fname_m = re.search(rb'filename="([^"]+)"', headers_raw)
        name_m = re.search(rb'name="([^"]+)"', headers_raw)
        fname = (
            fname_m.group(1).decode("utf-8", errors="replace")
            if fname_m
            else None
        )
        name = (
            name_m.group(1).decode("utf-8", errors="replace")
            if name_m
            else None
        )
        yield name, fname, data


# ── Embedded HTML / CSS / JS ───────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Live Share</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
      background: #1e1e2e;
      color: #cdd6f4;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem 1rem;
      gap: 0.6rem;
    }

    h1 {
      font-size: 1.3rem;
      font-weight: 600;
      letter-spacing: 0.04em;
      color: #cba6f7;
    }

    /* ── Toggle button ────────────────────────────────────────────────────── */
    #toggle-btn {
      display: flex;
      align-items: center;
      gap: 0.65rem;
      padding: 0.55rem 1.8rem;
      border: 2px solid;
      border-radius: 50px;
      cursor: pointer;
      font-size: 1rem;
      font-weight: 700;
      letter-spacing: 0.06em;
      transition: all 0.2s ease;
      background: transparent;
      user-select: none;
    }
    #toggle-btn.receiver { color: #f38ba8; border-color: #f38ba8; }
    #toggle-btn.receiver:hover { background: rgba(243,139,168,0.08); }
    #toggle-btn.source   { color: #a6e3a1; border-color: #a6e3a1; box-shadow: 0 0 16px rgba(166,227,161,0.28); }
    #toggle-btn.source:hover   { background: rgba(166,227,161,0.08); }

    #led {
      width: 13px; height: 13px; border-radius: 50%; flex-shrink: 0;
      transition: background 0.2s, box-shadow 0.2s;
    }
    .receiver #led { background: #f38ba8; box-shadow: 0 0 5px 2px rgba(243,139,168,0.65); }
    .source   #led { background: #a6e3a1; box-shadow: 0 0 8px 3px rgba(166,227,161,0.8);
                     animation: pulse-green 1.6s ease-in-out infinite; }

    @keyframes pulse-green {
      0%, 100% { box-shadow: 0 0 8px 3px rgba(166,227,161,0.8); }
      50%       { box-shadow: 0 0 20px 7px rgba(166,227,161,0.25); }
    }

    #sub-hint { font-size: 0.7rem; color: #6c7086; height: 1em; }
    #status   { font-size: 0.72rem; height: 1em; color: #6c7086; }
    #status.error { color: #f38ba8; }

    /* ── Textarea ─────────────────────────────────────────────────────────── */
    #editor {
      width: min(920px, 100%);
      height: 40vh;
      background: #313244;
      color: #cdd6f4;
      border: 1px solid #45475a;
      border-radius: 10px;
      padding: 1rem;
      font-size: 0.95rem;
      font-family: "Fira Mono", "Cascadia Code", "DejaVu Sans Mono", monospace;
      line-height: 1.6;
      resize: vertical;
      outline: none;
      transition: border-color 0.2s;
    }
    #editor:focus { border-color: #cba6f7; }

    /* ── Text toolbar ─────────────────────────────────────────────────────── */
    .toolbar {
      display: flex; gap: 0.6rem; align-items: center;
    }
    button.tool {
      padding: 0.38rem 1rem; border: none; border-radius: 7px; cursor: pointer;
      font-size: 0.82rem; font-weight: 500; transition: opacity 0.15s;
    }
    button.tool:hover { opacity: 0.82; }
    #btn-copy  { background: #89b4fa; color: #1e1e2e; }
    #btn-clear { background: #f38ba8; color: #1e1e2e; }
    #char-count { font-size: 0.72rem; color: #6c7086; margin-left: 0.4rem; }

    /* ── Files section ────────────────────────────────────────────────────── */
    #files-section {
      width: min(920px, 100%);
      background: #313244;
      border: 1px solid #45475a;
      border-radius: 10px;
      overflow: hidden;
    }

    #files-header {
      padding: 0.6rem 1rem;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      color: #cba6f7;
      border-bottom: 1px solid #45475a;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    /* Drop zone (SOURCE only) */
    #drop-zone {
      margin: 0.75rem 1rem;
      border: 2px dashed #45475a;
      border-radius: 8px;
      padding: 1rem;
      text-align: center;
      color: #6c7086;
      font-size: 0.82rem;
      cursor: pointer;
      transition: border-color 0.2s, color 0.2s;
      user-select: none;
    }
    #drop-zone.drag-over {
      border-color: #a6e3a1;
      color: #a6e3a1;
    }
    #drop-zone:hover {
      border-color: #89b4fa;
      color: #89b4fa;
    }
    #file-input { display: none; }

    /* Progress bar */
    #upload-progress {
      margin: 0 1rem 0.5rem;
      display: none;
    }
    #upload-progress progress {
      width: 100%; height: 6px; border-radius: 3px;
      accent-color: #a6e3a1;
    }
    #upload-label {
      font-size: 0.72rem; color: #6c7086; margin-top: 0.2rem;
    }

    /* File list */
    #file-list {
      margin: 0 1rem 0.75rem;
    }
    .file-row {
      display: flex;
      align-items: center;
      gap: 0.6rem;
      padding: 0.42rem 0;
      border-bottom: 1px solid #3b3d51;
      font-size: 0.82rem;
    }
    .file-row:last-child { border-bottom: none; }
    .file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .file-size { color: #6c7086; flex-shrink: 0; width: 6rem; text-align: right; font-size: 0.75rem; }
    .file-dl {
      background: #89b4fa; color: #1e1e2e;
      border: none; border-radius: 6px; padding: 0.22rem 0.7rem;
      font-size: 0.75rem; font-weight: 600; cursor: pointer;
      text-decoration: none; flex-shrink: 0;
    }
    .file-dl:hover { opacity: 0.82; }
    .file-rm {
      background: none; border: none; color: #6c7086;
      font-size: 1rem; cursor: pointer; flex-shrink: 0; line-height: 1;
      padding: 0 0.2rem;
    }
    .file-rm:hover { color: #f38ba8; }
    #no-files { padding: 0.6rem 0; color: #6c7086; font-size: 0.8rem; text-align: center; }
  </style>
</head>
<body>
  <h1>&#128203; Live Share</h1>

  <button id="toggle-btn" class="receiver" onclick="toggleSource()">
    <span id="led"></span>
    <span id="toggle-label">RECEIVER</span>
  </button>
  <div id="sub-hint">&nbsp;</div>
  <div id="status">connecting…</div>

  <textarea id="editor" spellcheck="false"
    placeholder="SOURCE types here. RECEIVER sees the text live."></textarea>

  <div class="toolbar">
    <button class="tool" id="btn-copy"  onclick="copyAll()">Copy all</button>
    <button class="tool" id="btn-clear" onclick="clearAll()">Clear text</button>
    <span id="char-count">0 chars</span>
  </div>

  <!-- ── Files ─────────────────────────────────────────────────────────── -->
  <div id="files-section">
    <div id="files-header">&#128206; Files</div>

    <!-- Upload controls — only shown when SOURCE -->
    <div id="drop-zone" onclick="document.getElementById('file-input').click()">
      Drop files here, or click to browse
    </div>
    <input type="file" id="file-input" multiple>

    <div id="upload-progress">
      <progress id="upload-bar" value="0" max="100"></progress>
      <div id="upload-label"></div>
    </div>

    <div id="file-list">
      <div id="no-files">No files yet</div>
    </div>
  </div>

<script>
(function () {
  "use strict";

  const editor    = document.getElementById("editor");
  const toggleBtn = document.getElementById("toggle-btn");
  const labelEl   = document.getElementById("toggle-label");
  const subHint   = document.getElementById("sub-hint");
  const statusEl  = document.getElementById("status");
  const charCount = document.getElementById("char-count");
  const dropZone  = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const uploadPrg = document.getElementById("upload-progress");
  const uploadBar = document.getElementById("upload-bar");
  const uploadLbl = document.getElementById("upload-label");
  const fileList  = document.getElementById("file-list");

  let myRole        = "receiver";
  let localVersion  = 0;
  let pushTimer     = null;
  let toggling      = false;
  let knownFiles    = [];   // last seen file list (for change detection)

  // ── Role helpers ───────────────────────────────────────────────────────────
  function applyRole(r) {
    myRole = r;
    toggleBtn.className = r;
    if (r === "source") {
      labelEl.textContent = "SOURCE — WRITING";
      subHint.textContent = "click to hand off to the other side";
      editor.focus();
    } else {
      labelEl.textContent = "RECEIVER";
      subHint.textContent = "click to become SOURCE";
    }
    // Upload zone and remove buttons only for SOURCE
    dropZone.style.display = (r === "source") ? "" : "none";
    fileInput.disabled     = (r !== "source");
  }

  function setStatus(msg, isError) {
    statusEl.textContent = msg;
    statusEl.className   = isError ? "error" : "";
  }

  function updateCharCount() {
    charCount.textContent = editor.value.length.toLocaleString() + " chars";
  }

  function fmtSize(bytes) {
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + " MB";
    if (bytes >= 1024)    return (bytes / 1024).toFixed(0) + " KB";
    return bytes + " B";
  }

  // ── File list rendering ────────────────────────────────────────────────────
  function renderFiles(files) {
    fileList.innerHTML = "";
    if (!files || files.length === 0) {
      fileList.innerHTML = '<div id="no-files">No files yet</div>';
      return;
    }
    files.forEach(f => {
      const row = document.createElement("div");
      row.className = "file-row";

      const name = document.createElement("span");
      name.className = "file-name";
      name.textContent = f.name;
      name.title = f.name;

      const size = document.createElement("span");
      size.className = "file-size";
      size.textContent = fmtSize(f.size);

      const dl = document.createElement("a");
      dl.className = "file-dl";
      dl.textContent = "\u2b07 Download";
      dl.href = "/files/" + encodeURIComponent(f.name);
      dl.download = f.name;

      const rm = document.createElement("button");
      rm.className = "file-rm";
      rm.textContent = "\u00d7";
      rm.title = "Remove";
      rm.disabled = (myRole !== "source");
      rm.style.visibility = (myRole === "source") ? "visible" : "hidden";
      rm.onclick = () => deleteFile(f.name);

      row.appendChild(name);
      row.appendChild(size);
      row.appendChild(dl);
      row.appendChild(rm);
      fileList.appendChild(row);
    });
  }

  // ── Toggle ─────────────────────────────────────────────────────────────────
  window.toggleSource = async function () {
    if (toggling) return;
    toggling = true;
    setTimeout(() => { toggling = false; }, 600);
    try {
      const res  = await fetch("/toggle", { method: "POST" });
      const data = await res.json();
      applyRole(data.my_role);
      setStatus("flipped \u2192 " + data.source_side + " is SOURCE", false);
    } catch (_) {
      setStatus("offline", true);
    }
  };

  // ── Text push ──────────────────────────────────────────────────────────────
  editor.addEventListener("input", () => {
    updateCharCount();
    if (myRole !== "source") return;
    clearTimeout(pushTimer);
    pushTimer = setTimeout(pushText, 150);
  });

  async function pushText() {
    if (myRole !== "source") return;
    try {
      const res = await fetch("/text", {
        method : "POST",
        headers: { "Content-Type": "application/json" },
        body   : JSON.stringify({ text: editor.value }),
      });
      if (res.ok) {
        const data = await res.json();
        localVersion = data.version;
        setStatus("v" + localVersion, false);
      }
    } catch (_) {
      setStatus("offline", true);
    }
  }

  // ── Poll ───────────────────────────────────────────────────────────────────
  async function poll() {
    try {
      const res  = await fetch("/text");
      if (!res.ok) { setStatus("error " + res.status, true); return; }
      const data = await res.json();

      if (data.my_role !== myRole) {
        applyRole(data.my_role);
        setStatus("role changed: " + data.my_role, false);
      }

      if (myRole !== "source" && data.version !== localVersion) {
        const ss  = editor.selectionStart;
        const se  = editor.selectionEnd;
        const top = editor.scrollTop;
        editor.value = data.text;
        localVersion = data.version;
        updateCharCount();
        try {
          editor.selectionStart = Math.min(ss, data.text.length);
          editor.selectionEnd   = Math.min(se, data.text.length);
          editor.scrollTop      = top;
        } catch (_) {}
        setStatus("v" + localVersion, false);
      } else if (myRole !== "source") {
        setStatus("live \u2713", false);
      }

      // Update file list if changed
      const fj = JSON.stringify(data.files || []);
      if (fj !== JSON.stringify(knownFiles)) {
        knownFiles = data.files || [];
        renderFiles(knownFiles);
      }
    } catch (_) {
      setStatus("offline", true);
    }
  }

  // ── File upload ────────────────────────────────────────────────────────────
  async function uploadFiles(fileObjs) {
    if (myRole !== "source") return;
    const arr = Array.from(fileObjs);
    for (let i = 0; i < arr.length; i++) {
      const f   = arr[i];
      const fd  = new FormData();
      fd.append("file", f, f.name);

      uploadPrg.style.display = "";
      uploadBar.value  = 0;
      uploadLbl.textContent = "Uploading " + f.name + "…";

      try {
        // Use XHR for progress events
        await new Promise((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open("POST", "/files");
          xhr.upload.onprogress = e => {
            if (e.lengthComputable) uploadBar.value = (e.loaded / e.total) * 100;
          };
          xhr.onload = () => {
            if (xhr.status === 200 || xhr.status === 201) {
              uploadLbl.textContent = f.name + " uploaded \u2713";
              resolve();
            } else {
              let msg = xhr.statusText;
              try { msg = JSON.parse(xhr.responseText).error || msg; } catch (_) {}
              reject(new Error(msg));
            }
          };
          xhr.onerror = () => reject(new Error("network error"));
          xhr.send(fd);
        });
      } catch (err) {
        uploadLbl.textContent = "Upload failed: " + err.message;
        uploadBar.value = 0;
        await new Promise(r => setTimeout(r, 3000));
      }
    }
    setTimeout(() => { uploadPrg.style.display = "none"; }, 2000);
    poll(); // immediate refresh
  }

  // Drag and drop
  dropZone.addEventListener("dragover", e => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", e => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files.length) uploadFiles(fileInput.files);
    fileInput.value = "";   // reset so same file can be re-selected
  });

  // ── File delete ────────────────────────────────────────────────────────────
  async function deleteFile(name) {
    try {
      await fetch("/files/" + encodeURIComponent(name), { method: "DELETE" });
      poll();
    } catch (_) {
      setStatus("delete failed", true);
    }
  }

  // ── Text toolbar ───────────────────────────────────────────────────────────
  window.copyAll = async function () {
    try {
      await navigator.clipboard.writeText(editor.value);
      setStatus("copied \u2713", false);
    } catch (_) {
      editor.select();
      document.execCommand("copy");
      setStatus("copied (fallback) \u2713", false);
    }
  };

  window.clearAll = async function () {
    if (!confirm("Clear the shared text on all clients?")) return;
    editor.value = "";
    updateCharCount();
    await fetch("/text", {
      method : "POST",
      headers: { "Content-Type": "application/json" },
      body   : JSON.stringify({ text: "" }),
    });
    setStatus("cleared", false);
  };

  // ── Bootstrap ──────────────────────────────────────────────────────────────
  applyRole("receiver");    // initial; poll() will correct to source if needed
  poll();
  setInterval(poll, 500);
  updateCharCount();
}());
</script>
</body>
</html>
"""


# ── Request handler ────────────────────────────────────────────────────────────
class Handler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):  # noqa: N802
        pass

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj: dict) -> None:
        self._send(code, "application/json", json.dumps(obj).encode())

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length)

    def _json_body(self) -> dict:
        try:
            return json.loads(self._read_body())
        except json.JSONDecodeError:
            return {}

    def do_OPTIONS(self):  # noqa: N802
        self._send(204, "text/plain", b"")

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        side = _side_from_request(self)

        if path in ("/", "/index.html"):
            self._send(200, "text/html; charset=utf-8", HTML.encode())

        elif path == "/text":
            with _lock:
                self._json(200, _state_for_side(side))

        elif path.startswith("/files/"):
            fname = path[len("/files/") :]
            try:
                from urllib.parse import unquote

                fname = unquote(fname)
            except Exception:
                pass
            with _lock:
                entry = _files.get(fname)
            if entry is None:
                self._json(404, {"error": "not found"})
                return
            data = entry["data"]
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Content-Length", str(len(data)))
            self.send_header(
                "Content-Disposition", f'attachment; filename="{fname}"'
            )
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        elif path == "/files":
            with _lock:
                lst = [
                    {
                        "name": v["name"],
                        "size": v["size"],
                        "uploaded_at": round(v["uploaded_at"]),
                    }
                    for v in _files.values()
                ]
            self._json(200, {"files": lst})

        else:
            self._json(404, {"error": "not found"})

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):  # noqa: N802
        path = urlparse(self.path).path
        side = _side_from_request(self)

        if path == "/text":
            data = self._json_body()
            with _lock:
                _state["version"] += 1
                _state["text"] = str(data.get("text", ""))
                self._json(200, _state_for_side(side))

        elif path == "/toggle":
            with _lock:
                _state["source_side"] = (
                    "laptop" if _state["source_side"] == "ubuntu" else "ubuntu"
                )
                self._json(200, _state_for_side(side))

        elif path == "/files":
            ct = self.headers.get("Content-Type", "")
            cl = int(self.headers.get("Content-Length", 0))
            max_bytes = _MAX_UPLOAD_MB * 1024 * 1024

            if cl > max_bytes:
                self._json(
                    413, {"error": f"File too large (max {_MAX_UPLOAD_MB} MB)"}
                )
                return

            body = self.rfile.read(cl)

            saved = 0
            for _name, fname, data in _parse_multipart(ct, body):
                if fname:
                    with _lock:
                        _files[fname] = {
                            "name": fname,
                            "size": len(data),
                            "data": data,
                            "uploaded_at": time.time(),
                        }
                    saved += 1

            if saved == 0:
                self._json(400, {"error": "no files parsed"})
            else:
                self._json(200, {"saved": saved})

        else:
            self._json(404, {"error": "not found"})

    # ── DELETE ────────────────────────────────────────────────────────────────
    def do_DELETE(self):  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/files/"):
            fname = path[len("/files/") :]
            try:
                from urllib.parse import unquote

                fname = unquote(fname)
            except Exception:
                pass
            with _lock:
                removed = _files.pop(fname, None)
            if removed:
                self._json(200, {"removed": fname})
            else:
                self._json(404, {"error": "not found"})
        else:
            self._json(404, {"error": "not found"})


# ── Entry point ────────────────────────────────────────────────────────────────
def main() -> None:
    port = (
        int(sys.argv[1])
        if len(sys.argv) > 1 and sys.argv[1].isdigit()
        else 8000
    )
    server = http.server.ThreadingHTTPServer(("", port), Handler)

    lan_ip = _get_lan_ip()

    # Check if the friendly name resolves to this machine's LAN IP
    try:
        resolved = socket.gethostbyname("liveshare")
        hosts_ok = resolved == lan_ip
    except OSError:
        hosts_ok = False

    print(f"\n  Live Share server running  (max upload: {_MAX_UPLOAD_MB} MB)")
    print(f"  ─────────────────────────────────────────────")
    if hosts_ok:
        print(f"  Friendly URL  : http://liveshare:{port}  (both machines)")
    else:
        print(
            f"  Preferred URL : http://liveshare:{port}  ← /etc/hosts not set up yet"
        )
        print(f"                  run:  python3 live_share.py --print-hosts")
    print(f"  Fallback URL  : http://{lan_ip}:{port}  (always works)")
    print(f"  Localhost     : http://localhost:{port}")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Ubuntu starts as SOURCE (green), laptop as RECEIVER (red).")
    print(f"  Click the button on EITHER side to flip both.")
    print(f"  Files are stored in RAM — they vanish when the server stops.")
    print(f"  ─────────────────────────────────────────────")
    print(f"  Press Ctrl-C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
