from flask import Flask, Response, request
from flask_cors import CORS
import os
import json
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

QURAN_FOLDER = "static/quran_library"
ANALYTICS_FILE = "listener_data.json"
os.makedirs(QURAN_FOLDER, exist_ok=True)
current_track = {"name": ""}
listener_log = []

def log_listener(ip):
    try:
        listener_log.append({
            "ip": ip,
            "timestamp": datetime.now().isoformat()
        })
        if len(listener_log) > 1000:
            listener_log.pop(0)
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(listener_log, f, indent=2)
    except Exception as e:
        print(f"❌ Listener log error: {e}")

def get_mp3_files():
    files = [os.path.join(QURAN_FOLDER, f) for f in os.listdir(QURAN_FOLDER) if f.endswith(".mp3")]
    files.sort()
    return files

def generate_stream():
    while True:
        files = get_mp3_files()
        if not files:
            yield b""
            time.sleep(2)
            continue
        for path in files:
            current_track["name"] = os.path.basename(path)
            try:
                with open(path, "rb") as f:
                    while chunk := f.read(4096):
                        yield chunk
                        time.sleep(0.001)
            except Exception as e:
                print(f"Error playing {path}: {e}")
                continue

@app.route("/stream.mp3")
def stream_mp3():
    ip = request.remote_addr
    log_listener(ip)
    return Response(generate_stream(), mimetype="audio/mpeg")

@app.route("/")
def index():
    listener_data = load_analytics()
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
                justify-content: center;
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
            <p><strong>👥 المستمعون الآن:</strong> {listener_data['current']}</p>
            <p><strong>📈 إجمالي عدد المستمعين:</strong> {listener_data['total']}</p>
            <p><strong>🕒 ساعات الاستماع اليوم:</strong> {listener_data['today_hours']} ساعة</p>
            <p><strong>📅 ساعات الاستماع هذا الأسبوع:</strong> {listener_data['week_hours']} ساعة</p>
        </div>

        <footer>© {datetime.now().year} راديو شبلي | بث تلاوة القرآن الكريم باستخدام تقنيات الذكاء الاصطناعي</footer>
    </body>
    </html>
    """

def load_analytics():
    try:
        if not os.path.exists(ANALYTICS_FILE):
            return {"current": 0, "total": 0, "today_hours": 0, "week_hours": 0}

        with open(ANALYTICS_FILE, encoding="utf-8") as f:
            data = json.load(f)

        now = datetime.now()
        today = [d for d in data if datetime.fromisoformat(d['timestamp']).date() == now.date()]
        week = [d for d in data if (now - datetime.fromisoformat(d['timestamp'])).days <= 7]
        unique_ips = set(d['ip'] for d in today[-50:])

        return {
            "current": len(unique_ips),
            "total": len(set(d['ip'] for d in data)),
            "today_hours": round(len(today) * 0.033, 1),
            "week_hours": round(len(week) * 0.033, 1)
        }
    except Exception as e:
        print(f"❌ Load analytics error: {e}")
        return {"current": 0, "total": 0, "today_hours": 0, "week_hours": 0}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
