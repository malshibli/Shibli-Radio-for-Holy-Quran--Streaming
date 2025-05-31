from flask import Flask, Response
from flask_cors import CORS
import os
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)

QURAN_FOLDER = "static/quran_library"
os.makedirs(QURAN_FOLDER, exist_ok=True)
current_track = {"name": ""}

# Get all .mp3 files sorted
def get_mp3_files():
    files = [os.path.join(QURAN_FOLDER, f) for f in os.listdir(QURAN_FOLDER) if f.endswith(".mp3")]
    files.sort()
    return files

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
                print(f"Error playing {path}: {e}")
                continue

# Streaming endpoint
@app.route("/stream.mp3")
def stream_mp3():
    return Response(generate_stream(), mimetype="audio/mpeg")

# Home page with player only
@app.route("/")
def index():
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

        <footer>© {datetime.now().year} راديو شبلي | بث تلاوة القرآن الكريم</footer>
    </body>
    </html>
    """

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
