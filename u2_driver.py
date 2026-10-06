#!/usr/bin/env python3
"""uiautomator2 driver for MuMu Player.

Drop-in upgrade from main.py — same CLI interface plus u2-powered extras.

Usage:
  python u2_driver.py read                    # list all elements (text + bounds)
  python u2_driver.py read "cari"             # filter elements
  python u2_driver.py tap 150 908             # tap coordinates
  python u2_driver.py tap "Settings"          # find text and tap
  python u2_driver.py text "hello"            # type text (clears field first)
  python u2_driver.py text --append "hello"   # type without clearing
  python u2_driver.py key HOME                # keyevent
  python u2_driver.py shot                    # screenshot -> screen.png
  python u2_driver.py info                    # device + current app info
  python u2_driver.py wait "Next" 10          # wait for element (timeout secs)
  python u2_driver.py exists "Next"           # check if element exists
  python u2_driver.py swipe up                # swipe direction (up/down/left/right)
  python u2_driver.py app-start com.pkg       # start app by package
  python u2_driver.py app-stop com.pkg        # stop app
  python u2_driver.py app-current             # current foreground app
  python u2_driver.py shell "ls /sdcard"      # run shell command on device
  python u2_driver.py accounts                # list accounts from akun.txt
  python u2_driver.py login 0                 # full login flow for account N
  python u2_driver.py login all               # login all accounts sequentially
  python u2_driver.py inspect                 # open uiautodev inspector (browser)
"""
import sys
import time
from pathlib import Path

import uiautomator2 as u2

DEVICE = "127.0.0.1:7555"
HERE = Path(__file__).parent


def connect():
    d = u2.connect(DEVICE)
    return d


def dump_elements(d, flt=""):
    """List visible elements with text."""
    rows = []
    for el in d.xpath('//*[@text!="" or @content-desc!="" or @hint!=""]').all():
        label = el.attrib.get("text") or el.attrib.get("content-desc") or el.attrib.get("hint") or ""
        if not label:
            continue
        if flt and flt.lower() not in label.lower():
            continue
        r = el.rect
        cx, cy = r[0] + r[2] // 2, r[1] + r[3] // 2
        clickable = el.attrib.get("clickable") == "true"
        rows.append((label, cx, cy, clickable))
    return rows


def find_element(d, text):
    """Return u2 element matching text (partial match)."""
    el = d(textContains=text)
    if el.exists:
        return el
    el = d(descriptionContains=text)
    if el.exists:
        return el
    return None


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


def wait_and_tap(d, text, timeout=10):
    """Wait for element with text, then tap it. Returns True if found."""
    el = d(textContains=text)
    if el.wait(timeout=timeout):
        el.click()
        return True
    el = d(text=text)
    if el.wait(timeout=timeout):
        el.click()
        return True
    return False


def login_account(d, idx):
    """Full Google login flow for account at index."""
    accs = accounts()
    if idx >= len(accs):
        print(f"Account index {idx} out of range (have {len(accs)})")
        return False

    email, pw = accs[idx]
    print(f"[{idx}] Logging in {email}...")

    # Open add-account settings
    d.shell("am start -a android.settings.ADD_ACCOUNT_SETTINGS")
    time.sleep(3)

    # Fill email
    el = find_element(d, "Email or phone")
    if not el:
        print("  Email field not found. Wrong screen?")
        d.screenshot(str(HERE / "screen.png"))
        return False

    el.click()
    time.sleep(0.5)
    d.send_keys(email)
    time.sleep(0.5)

    if not wait_and_tap(d, "NEXT", 5) and not wait_and_tap(d, "Next", 5):
        print("  NEXT button not found after email")
        return False
    time.sleep(4)

    # Fill password
    el = find_element(d, "Enter your password")
    if not el:
        print("  Password field not found")
        d.screenshot(str(HERE / "screen.png"))
        return False

    el.click()
    time.sleep(0.5)
    d.send_keys(pw)
    time.sleep(0.5)

    if not wait_and_tap(d, "NEXT", 5) and not wait_and_tap(d, "Next", 5):
        print("  NEXT button not found after password")
        return False
    time.sleep(4)

    # Accept Terms of Service
    if wait_and_tap(d, "I agree", 10):
        print("  ToS accepted")
        time.sleep(3)

    # Google Services — tap MORE then ACCEPT
    el = find_element(d, "MORE")
    if el:
        el.click()
        time.sleep(2)
    if wait_and_tap(d, "ACCEPT", 10):
        print("  Google Services accepted")
        time.sleep(3)

    # Second I agree (sometimes appears)
    if find_element(d, "I agree"):
        wait_and_tap(d, "I agree", 5)
        time.sleep(3)

    print(f"  Done: {email}")
    return True


def main():
    d = connect()
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return

    cmd = a[0]

    if cmd == "read":
        flt = a[1] if len(a) > 1 else ""
        for i, (label, cx, cy, clk) in enumerate(dump_elements(d, flt), 1):
            flag = "[tap]" if clk else "     "
            safe = label.encode("ascii", "replace").decode()
            print(f"{i:2}. {flag} {cx},{cy:<5} {safe}")

    elif cmd == "tap":
        if len(a) == 3 and a[1].isdigit():
            d.click(int(a[1]), int(a[2]))
        else:
            text = a[1]
            el = find_element(d, text)
            if el:
                el.click()
                print(f"tapped: {text}")
            else:
                print(f"'{text}' not found")

    elif cmd == "text":
        if len(a) >= 3 and a[1] == "--append":
            d.send_keys(a[2])
        else:
            d.send_keys(a[1], clear=True)

    elif cmd == "key":
        d.press(a[1].lower())

    elif cmd == "shot":
        p = HERE / "screen.png"
        d.screenshot(str(p))
        print(f"saved: {p}")

    elif cmd == "info":
        print(f"Device: {d.info}")
        print(f"App: {d.app_current()}")
        print(f"Window: {d.window_size()}")

    elif cmd == "wait":
        text = a[1]
        timeout = int(a[2]) if len(a) > 2 else 10
        found = d(textContains=text).wait(timeout=timeout)
        print(f"{'found' if found else 'timeout'}: {text}")

    elif cmd == "exists":
        text = a[1]
        ex = d(textContains=text).exists
        print(f"{'yes' if ex else 'no'}: {text}")

    elif cmd == "swipe":
        direction = a[1].lower()
        d.swipe_ext(direction, scale=0.8)

    elif cmd == "app-start":
        d.app_start(a[1])

    elif cmd == "app-stop":
        d.app_stop(a[1])

    elif cmd == "app-current":
        info = d.app_current()
        print(f"{info['package']}/{info['activity']}")

    elif cmd == "shell":
        out = d.shell(a[1])
        print(out.output.strip())

    elif cmd == "accounts":
        for i, (e, _) in enumerate(accounts()):
            print(f"{i}: {e}")

    elif cmd == "login":
        if a[1] == "all":
            for i in range(len(accounts())):
                login_account(d, i)
                if i < len(accounts()) - 1:
                    print("  Jeda 5 detik antar akun...")
                    time.sleep(5)
        else:
            login_account(d, int(a[1]))

    elif cmd == "inspect":
        import subprocess
        print("Starting uiautodev inspector on http://localhost:17310 ...")
        subprocess.Popen(["uiauto.dev", "server"], creationflags=0x00000008)
        print("Open browser: http://localhost:17310")

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
