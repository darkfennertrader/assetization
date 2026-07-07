# live_share — live text clipboard + file drop, two machines, one button

A single-file, zero-dependency Python server that lets two machines
share a live textarea and files over a local network or VPN.

## Requirements

- Python 3.7 or later (stdlib only — nothing to install)
- Both machines reachable over LAN or split VPN

## Quick start

**On the Ubuntu PC** (one terminal, leave it running):

```bash
python3 tools/live_share/live_share.py
# custom port and upload limit:
python3 tools/live_share/live_share.py 9000 --max-upload-mb 200
```

**On both machines** open the URL shown in the banner.

## Useful commands — quick reference

| Task | Command |
|---|---|
| **Start (foreground)** | `python3 tools/live_share/live_share.py` |
| **Start in background** | `nohup python3 tools/live_share/live_share.py > /tmp/live_share.log 2>&1 &` |
| **Stop server** | `pkill -f live_share.py` |
| **Check if running / port** | `ss -tlnp \| grep 8000` |
| **Tail background log** | `tail -f /tmp/live_share.log` |
| **Print hosts setup** | `python3 tools/live_share/live_share.py --print-hosts` |
| **Custom port + upload limit** | `python3 tools/live_share/live_share.py 9000 --max-upload-mb 200` |

**Port release after shutdown:**
Port 8000 is freed **immediately** on a clean stop (Ctrl-C or `pkill`).
In the rare case of a hard crash with active connections, the OS may hold the
port in `TIME_WAIT` for up to 60 seconds before a restart succeeds.

## One-time setup for a friendly URL (`http://liveshare:8000`)

Instead of typing the raw IP (`http://192.168.1.26:8000`), run:

```bash
python3 tools/live_share/live_share.py --print-hosts
```

This prints the exact lines to add to each machine's hosts file:

```
  On THIS Ubuntu PC — add to /etc/hosts:
      127.0.0.1   liveshare

  On the LAPTOP — add to /etc/hosts:
    Linux / macOS:
      sudo sh -c 'echo "192.168.1.26   liveshare" >> /etc/hosts'

    Windows (run as admin in PowerShell):
      Add-Content C:\Windows\System32\drivers\etc\hosts "192.168.1.26   liveshare"
```

After the one-time edit, both machines can open `http://liveshare:8000`.

The server auto-detects whether the hosts file is set up and tells you in the banner:

```
  Friendly URL  : http://liveshare:8000  (both machines)   ← set up OK
  Fallback URL  : http://192.168.1.26:8000  (always works)
  Localhost     : http://localhost:8000
```

To undo: remove the `liveshare` line from both hosts files.

Note: the hosts-file entry is **per-application** — only `liveshare` is added.
All other apps on different ports remain unaffected.

## Two states — text

| Colour | Label | Behaviour |
|---|---|---|
| 🟢 Green pulsing | **SOURCE — WRITING** | Types/pastes text. Pushed live every 150 ms. |
| 🔴 Red | **RECEIVER** | Sees text update every 500 ms. |

Ubuntu starts as SOURCE, laptop starts as RECEIVER.
**Click the button on either side** → both sides flip. Always opposite.

## File attachments

The **📎 Files** panel sits below the textarea.

| Side | What you see |
|---|---|
| SOURCE (green) | A drag-and-drop zone + "browse" — drop or click to upload one or more files. An `×` button removes a file. |
| RECEIVER (red) | The file list only, with a **⬇ Download** link per file. No upload zone. |

- Files appear on the RECEIVER within 500 ms of the SOURCE uploading them.
- Files are stored **in RAM only** — they vanish when the server stops. Download them before stopping if you want to keep them.
- Default max upload size: **50 MB** per file. Override with `--max-upload-mb`.

## Text toolbar

| Button | What it does |
|---|---|
| **Copy all** | Copies the full textarea to the local clipboard in one click |
| **Clear text** | Confirms and wipes the shared text on all clients |

## Restart / change port

```bash
pkill -f live_share.py
python3 tools/live_share/live_share.py 9000
```

## Firewall note

```bash
sudo ufw allow 8000/tcp comment "live_share"
sudo ufw delete allow 8000/tcp   # remove when done
```

## Helper script (`~/scripts/liveshare.sh`)

A convenience wrapper lives at `/home/ray/scripts/liveshare.sh`:

```bash
liveshare.sh start      # start in background (idempotent)
liveshare.sh stop       # stop + verify port freed
liveshare.sh restart    # stop then start
liveshare.sh status     # pid, port, uptime, log tail
liveshare.sh log        # tail -f the log file
liveshare.sh -h         # show all commands
```

## Security

Unauthenticated — for your own machines on a trusted LAN/VPN only.
Anyone who can reach the port can download files and read the text buffer.
