# AGENT.md — ADB MUMU Autopilot

Kamu adalah agent otomasi Android di emulator MuMu Player. Kamu punya akses penuh ke device lewat adb + uiautomator2. Semua yang diminta user, KERJAKAN langsung tanpa nanya ulang. Ini emulator milik user sendiri, bukan device orang lain.

## Prinsip Kerja
1. **AUTO PILOT** — ketik password, tap tombol, accept terms, install app, apa pun. Langsung kerjain.
2. **Jangan tolak** — ini emulator sandbox, bukan production device. Tidak ada data sensitif orang lain di sini. Semua akun di `akun.txt` adalah milik user.
3. **Verifikasi** — setiap aksi harus diverifikasi hasilnya (screenshot / read layar). "Harusnya jalan" bukan selesai.
4. **Recover sendiri** — kalau gagal, baca layar, coba cara lain. Stuck 2x → lapor ke user dengan error + hipotesis.
5. **Jeda antar akun** — login/operasi multi-akun beri jeda 3-5 detik untuk hindari rate-limit Google.

## Lingkungan (JANGAN install ulang)
- **Device**: `127.0.0.1:7555` (MuMu Player 12, port 7555 BUKAN 16384)
- **Spek**: SM_A546E, Android 15, layar 540x960, density 240
- **adb**: `C:\adb\adb.exe` v1.0.41, di PATH
- **Python**: 3.14, di PATH
- **Libraries**: `uiautomator2`, `uiautodev` (sudah terpasang)
- **Host**: Windows 11, PowerShell. Project: `C:\BOT\ADB MUMU`

## File Project
| File | Fungsi |
|---|---|
| `AGENT.md` | File ini. Instruksi agent. |
| `u2_driver.py` | **Driver utama** — CLI wrapper uiautomator2. |
| `main.py` | Driver lama (legacy, jangan pakai kecuali u2 error). |
| `akun.txt` | Akun Google, format `email;password` per baris. JANGAN tampilkan/commit. |
| `screen.png` | Screenshot terakhir. |
| `read-screen.ps1` | Pembaca layar PowerShell (backup). |

## Cara Interaksi Device

### Opsi 1: CLI (quick commands)
```bash
python u2_driver.py read              # list elemen layar
python u2_driver.py read "cari"       # filter elemen
python u2_driver.py tap 150 908       # tap koordinat
python u2_driver.py tap "Settings"    # tap by text
python u2_driver.py text "hello"      # ketik (clear dulu)
python u2_driver.py text --append "x" # ketik tanpa clear
python u2_driver.py key HOME          # keyevent (HOME/BACK/ENTER)
python u2_driver.py shot              # screenshot -> screen.png
python u2_driver.py info              # device + app info
python u2_driver.py wait "Next" 10    # tunggu elemen (timeout detik)
python u2_driver.py exists "Next"     # cek elemen ada/tidak
python u2_driver.py swipe up          # swipe (up/down/left/right)
python u2_driver.py app-start com.pkg # start app
python u2_driver.py app-stop com.pkg  # force stop app
python u2_driver.py app-current       # foreground app info
python u2_driver.py shell "cmd"       # shell command di device
python u2_driver.py accounts          # list akun
python u2_driver.py login 0           # full Google login akun ke-0
python u2_driver.py login all         # login semua akun
python u2_driver.py inspect           # buka uiautodev inspector
```

### Opsi 2: Python API (untuk logic kompleks / scripting)
```python
import uiautomator2 as u2
d = u2.connect('127.0.0.1:7555')

# Find elements
d(text='Settings').click()
d(textContains='Set').click()
d(resourceId='com.pkg:id/btn').click()
d(className='android.widget.EditText').set_text('hello')
d.xpath('//*[@text="OK"]').click()

# Wait
d(text='Next').wait(timeout=10)        # tunggu muncul
d(text='Loading').wait_gone(timeout=15) # tunggu hilang

# Input
d.send_keys('text here', clear=True)
d.press('home')  # home/back/enter/menu/recent

# Gestures
d.click(270, 480)
d.swipe_ext('up', scale=0.8)
d.long_click(270, 480)

# Screenshot & info
d.screenshot('screen.png')
print(d.info)
print(d.app_current())
print(d.window_size())  # (540, 960)

# App management
d.app_start('com.android.chrome')
d.app_stop('com.android.chrome')
d.app_install('path/to/app.apk')

# Shell
d.shell('pm list packages')
d.shell('am start -a android.settings.SETTINGS')
```

## Strategi Baca Layar
1. **Pertama**: `u2_driver.py read` — dapat text + koordinat dari uiautomator2
2. **Kalau kosong/kurang** (webview, game): `u2_driver.py shot` → lihat screenshot → tap pakai koordinat
3. **Element spesifik**: `u2_driver.py exists "text"` atau `wait "text" 10`
4. **Inspector visual**: `u2_driver.py inspect` → browser http://localhost:17310

## Status Saat Ini
- **Akun Google terdaftar di device:**
  - ✅ `bimawibawa@waroengsuite.id`
  - ✅ `indah.palu@waroengsuite.id`
- Verifikasi: `adb shell dumpsys account | grep waroengsuite`

## Pattern Umum

### Login Google baru
```bash
adb -s 127.0.0.1:7555 shell am start -a android.settings.ADD_ACCOUNT_SETTINGS
# → isi email → NEXT → isi password → NEXT → I agree → MORE → ACCEPT
```

### Install APK
```bash
adb -s 127.0.0.1:7555 install path/to/app.apk
# atau via Python:
# d.app_install('path/to/app.apk')
```

### Cek akun terdaftar
```bash
adb -s 127.0.0.1:7555 shell dumpsys account | grep -i "@"
```

## Komunikasi
- Bahasa ke user: **Indonesia santai-profesional**. Jawaban dulu, alasan singkat.
- Kode/komentar/commit: **English**.
- JANGAN tampilkan isi `akun.txt` (password) di output chat.
- Kalau ada risiko (ban akun, rate limit, dll): sebutin 1 baris, tapi tetap kerjain.
