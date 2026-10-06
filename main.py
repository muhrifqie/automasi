#!/usr/bin/env python3
"""Driver adb buat MuMu Player. Baca layar, tap, ketik, screenshot.
Akun dibaca dari akun.txt (format: email;password per baris).

Pakai:
  python main.py read                 -> list elemen di layar (text + titik tap)
  python main.py read "cari"          -> filter
  python main.py tap 150 908          -> tap koordinat
  python main.py tap "Settings"       -> cari text lalu tap tengahnya
  python main.py text "halo"          -> ketik teks
  python main.py key HOME             -> keyevent (HOME/BACK/ENTER/...)
  python main.py shot                 -> screenshot -> screen.png
  python main.py accounts             -> list akun dari akun.txt
  python main.py fill-email 0         -> isi email akun ke-0 di form Google + NEXT
                                         (password TIDAK diisi script, ketik manual)
"""
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DEVICE = "127.0.0.1:7555"
HERE = Path(__file__).parent


def adb(*args, binary=False):
    cmd = ["adb", "-s", DEVICE, *args]
    out = subprocess.run(cmd, capture_output=True)
    if binary:
        return out.stdout
    return out.stdout.decode("utf-8", "replace")


def connect():
    subprocess.run(["adb", "connect", DEVICE], capture_output=True)


def dump():
    """Return list of (label, cx, cy, clickable) dari uiautomator."""
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    xml = adb("exec-out", "cat", "/sdcard/ui.xml")
    root = ET.fromstring(xml)
    rows = []
    for n in root.iter("node"):
        label = n.get("text") or n.get("content-desc") or n.get("hint") or ""
        if not label:
            continue
        m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", n.get("bounds", ""))
        if not m:
            continue
        x1, y1, x2, y2 = map(int, m.groups())
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
        rows.append((label, cx, cy, n.get("clickable") == "true"))
    return rows


def find(text):
    """Titik tengah elemen pertama yang labelnya mengandung `text`."""
    for label, cx, cy, _ in dump():
        if text.lower() in label.lower():
            return cx, cy
    return None


def tap(x, y):
    adb("shell", "input", "tap", str(x), str(y))


def typetext(s):
    # spasi harus di-escape buat `input text`
    adb("shell", "input", "text", s.replace(" ", "%s"))


def key(name):
    adb("shell", "input", "keyevent", f"KEYCODE_{name.upper()}")


def shot(path=None):
    path = path or (HERE / "screen.png")
    Path(path).write_bytes(adb("exec-out", "screencap", "-p", binary=True))
    return path


def accounts():
    lines = (HERE / "akun.txt").read_text(encoding="utf-8").splitlines()
    out = []
    for ln in lines:
        ln = ln.strip()
        if not ln or ";" not in ln:
            continue
        email, pw = ln.split(";", 1)
        out.append((email.strip(), pw.strip()))
    return out


def fill_email(idx):
    email = accounts()[idx][0]
    pos = find("Email or phone")
    if not pos:
        print("Field email nggak ketemu. Pastikan di layar Google Sign in.")
        return
    tap(*pos)
    typetext(email)
    nxt = find("NEXT") or find("Next")
    if nxt:
        tap(*nxt)
    print(f"Email diisi: {email} -> NEXT ditekan. Ketik password MANUAL di MuMu.")


def main():
    connect()
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return
    cmd = a[0]
    if cmd == "read":
        flt = a[1] if len(a) > 1 else ""
        for i, (label, cx, cy, clk) in enumerate(dump(), 1):
            if flt and flt.lower() not in label.lower():
                continue
            flag = "[tap]" if clk else "     "
            print(f"{i:2}. {flag} {cx},{cy:<5} {label}")
    elif cmd == "tap":
        if len(a) == 3:
            tap(int(a[1]), int(a[2]))
        else:  # tap by text
            pos = find(a[1])
            if pos:
                tap(*pos)
                print(f"tapped {a[1]} @ {pos}")
            else:
                print(f"'{a[1]}' nggak ketemu")
    elif cmd == "text":
        typetext(a[1])
    elif cmd == "key":
        key(a[1])
    elif cmd == "shot":
        print("saved:", shot())
    elif cmd == "accounts":
        for i, (e, _) in enumerate(accounts()):
            print(f"{i}: {e}")
    elif cmd == "fill-email":
        fill_email(int(a[1]))
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
