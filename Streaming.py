from flask import Flask, Response, request
import os
import time
import json
from datetime import datetime
import requests

app = Flask(__name__)

# Directories and files
QURAN_FOLDER = "static/quran_library"
ANALYTICS_FILE = "quran_listeners.json"
os.makedirs(QURAN_FOLDER, exist_ok=True)
current_track = {"name": ""}
listener_log = []

# Log listener IP with country
def log_listener(ip):
    try:
        geo = requests.get(f"http://ip-api.com/json/{ip}").json()
        country = geo.get("country", "Unknown")
        listener_log.append({
            "ip": ip,
            "country": country,
            "timestamp": datetime.now().isoformat()
        })
        if len(listener_log) > 1000:
            listener_log.pop(0)
        with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
            json.dump(listener_log, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"❌ Error logging listener: {e}")

# Load audio files
def get_mp3_files():
    return sorted([os.path.join(QURAN_FOLDER, f) for f in os.listdir(QURAN_FOLDER) if f.endswith(".mp3")])

# Streaming generator
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
                print(f"❌ Playback error: {e}")
                continue

# Load analytics
def load_analytics():
    try:
        with open(ANALYTICS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        now = datetime.now()
        today = [d for d in data if datetime.fromisoformat(d["timestamp"]).date() == now.date()]
        week = [d for d in data if (now - datetime.fromisoformat(d["timestamp"])).days <= 7]
        countries = {}
        for entry in today:
            countries[entry["country"]] = countries.get(entry["country"], 0) + 1
        sorted_countries = sorted(countries.items(), key=lambda x: -x[1])[:5]
        top_countries = [f"{c[0]}: {c[1]} مستمع" for c in sorted_countries]
        return {
            "current": len(set(d["ip"] for d in today[-50:])),
            "top_countries": top_countries,
            "today_hours": round(len(today) * 0.033, 1),
            "week_hours": round(len(week) * 0.033, 1)
        }
    except Exception as e:
        print(f"❌ Load analytics error: {e}")
        return {"current": 0, "top_countries": [], "today_hours": 0, "week_hours": 0}

@app.route("/stream.mp3")
def stream_mp3():
    ip = request.remote_addr
    log_listener(ip)
    return Response(generate_stream(), mimetype="audio/mpeg")

@app.route("/")
def index():
    stats = load_analytics()
    countries_html = ''.join([f'<li>{c}</li>' for c in stats['top_countries']])
    return f"""
    <!DOCTYPE html>
    <html lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>راديو شبلي لبث تلاوة القرآن الكريم</title>
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@500&display=swap" rel="stylesheet">
        <style>
            body {{
                background: #1e1e2f;
                color: #fff;
                font-family: 'Cairo', sans-serif;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 30px;
                text-align: center;
            }}
            .card {{
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                padding: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                width: 90%;
                max-width: 500px;
                margin-bottom: 30px;
                backdrop-filter: blur(10px);
            }}
            audio {{ width: 100%; margin-top: 1rem; border-radius: 10px; }}
            footer {{ margin-top: 2rem; font-size: 0.9rem; opacity: 0.7; }}
            ul {{ list-style: none; padding-right: 0; text-align: right; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📖 راديو شبلي لتلاوة القرآن الكريم</h1>
            <p>🔁 تلاوات قرآنية على مدار الساعة</p>
            <audio controls autoplay>
                <source src="/stream.mp3" type="audio/mpeg">
                المتصفح لا يدعم تشغيل الراديو.
            </audio>
            <p>🎧 التلاوة الحالية: {current_track["name"]}</p>
        </div>

        <div class="card">
            <h2>📊 تحليلات الاستماع</h2>
            <p><strong>👥 الآن:</strong> {stats["current"]} مستمع</p>
          #  <p><strong>🌍 الدول الأكثر استماعًا:</strong></p>
         #   <ul>{countries_html}</ul>
            <p><strong>⏰ اليوم:</strong> {stats["today_hours"]} ساعة</p>
            <p><strong>📅 هذا الأسبوع:</strong> {stats["week_hours"]} ساعة</p>
        </div>

        <footer>© {datetime.now().year} راديو شبلي | بث قرآني بالذكاء الاصطناعي</footer>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
