from flask import Flask, request
import os
import datetime

app = Flask(__name__)

LOG_DIR = "chat_logs"
os.makedirs(LOG_DIR, exist_ok=True)

@app.route("/log", methods=["POST"])
def log():
    data = request.json
    user = data.get("user", "anonymous")
    message = data.get("message", "")
    response = data.get("response", "")

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(LOG_DIR, f"{user}.txt")

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}]\nUSER: {message}\nAI: {response}\n\n")

    return {"status": "logged"}

if __name__ == "__main__":
    app.run(port=5050)