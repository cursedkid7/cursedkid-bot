import os
import requests
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "BOT RUNNING"

@app.route('/health')
def health():
    return "OK"

TOKEN = "8467227933:AAGFc1a2dY3NQ9jtE37LNAeYJkGtoOqtEfU"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

def send_startup_message():
    try:
        url = f"{BASE_URL}/sendMessage"
        data = {
            "chat_id": 5489125607,
            "text": "⚡ CURSEDKID BOT IS ONLINE ⚡\n\nBot started successfully!"
        }
        r = requests.post(url, data=data, timeout=10)
        print("Startup message sent:", r.json())
        return True
    except Exception as e:
        print("Startup message failed:", e)
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("CURSEDKID BOT - MINIMAL VERSION")
    print("=" * 50)
    
    # Send test message
    send_startup_message()
    
    # Start Flask
    port = int(os.environ.get("PORT", 5000))
    print(f"Server starting on port {port}")
    app.run(host="0.0.0.0", port=port)