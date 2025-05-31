from flask import Flask, Response, request
import os
import time
import json
from datetime import datetime

app = Flask(__name__)

# Directory and analytics setup
QURAN_FOLDER = "static/quran_library"
ANALYTICS_FILE = "listener_log_quran.json"
os.makedirs(QURAN_FOLDER, exist_ok=True)

current_track = {"name": ""}

# Load listener data
def load_listener_log():
    if not os.path.exists(ANALYTICS_FILE):
        return []
    with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Save listener data
def save_listener_log(log):
    with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)

# Log listener
def log_listener(ip):
    log = load_listener_log()
    log.append({"ip": ip, "timestamp": datetime.now().isoformat()})
    # Keep last 1000 records
    if len(log) > 1000:
        log = log[-1000:]
    save_listener_log(log)

# Get listener stats
def get_listener_stats():
    log = load_listener_log()
    now = datetime.now()
    today = [l for l in log if datetime.fromisoformat(l["timestamp"]).date() == now.date()]
    week = [l for l in log if (now - datetime.fromisoformat(l["timestamp"])).days < 7]
    last_30_min = [l for l in log if (now - datetime.fromisoformat(l["timestamp"])).seconds < 1800]
    return {
        "current": len(set(l["ip"] for l in last_30_min)),
        "total": len(set(l["ip"] for l in log)),
        "today_hours": round(len(today) * 0.033, 1),
        "week_hours": round(len(week) * 0.033, 1)
    }

# Get list of MP3s
def get_mp3_files():
    return sorted([os.path.join(QURAN_FOLDER, f) for f in os.listdir(QURAN_FOLDER) if f.endswith(".mp3")])

# Stream generator
def generate_stream():
    while True:
        files = get_mp3_files()
        if not files:
            yield b""
            time.sleep(2)
            continue
        for path in files:
            current_track["name"] = os.path.basename(path)
            print(f"📖 Now playing: {current_track['name']}")
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(4096):
                        yield chunk
                        time.sleep(0.001)
            except Exception as e:
                print(f"Error: {e}")
                continue

@app.route("/stream.mp3")
def stream_mp3():
    log_listener(request.remote_addr)
    return Response(generate_stream(), mimetype="audio/mpeg")

@app.route("/")
def index():
    stats = get_listener_stats()
    return f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>راديو شبلي لبث تلاوة القرآن الكريم 24/7</title>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@500&display=swap" rel="stylesheet">
        <style>
            body {{
                background: linear-gradient(to bottom, #1a1a2e, #16213e);
                color: #ffffff;
                font-family: 'Cairo', sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                min-height: 100vh;
                margin: 0;
                padding: 0;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                padding: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                width: 90%;
                max-width: 500px;
                margin-bottom: 2rem;
                backdrop-filter: blur(10px);
            }}
            h1 {{
                margin-top: 0;
                font-size: 2rem;
            }}
            audio {{
                width: 100%;
                margin-top: 1rem;
                border-radius: 10px;
            }}
            footer {{
                margin-top: 1rem;
                font-size: 0.9rem;
                opacity: 0.7;
            }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📖 راديو شبلي لتلاوة القرآن الكريم</h1>
            <p>🔁 تلاوات مسجلة تُبث على مدار 24 ساعة بدون انقطاع</p>
            <audio controls autoplay>
                <source src="/stream.mp3" type="audio/mpeg">
                متصفحك لا يدعم تشغيل التلاوة.
            </audio>
            <p>🎧 التلاوة الحالية: {current_track['name']}</p>
        </div>

        <div class="card">
            <h2>📊 التحليلات</h2>
            <p><strong>👥 المستمعون الآن:</strong> {stats['current']}</p>
            <p><strong>📈 إجمالي عدد المستمعين:</strong> {stats['total']}</p>
            <p><strong>🕒 ساعات الاستماع اليوم:</strong> {stats['today_hours']} ساعة</p>
            <p><strong>📅 ساعات الاستماع هذا الأسبوع:</strong> {stats['week_hours']} ساعة</p>
        </div>

        <footer>© {datetime.now().year} راديو شبلي | بث تلاوة القرآن الكريم باستخدام تقنيات الذكاء الاصطناعي</footer>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
