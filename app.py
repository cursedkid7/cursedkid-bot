import os
import json
import random
import string
import threading
from datetime import datetime
from flask import Flask
import requests

# ===== FLASK APP FOR KEEP-ALIVE =====
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ CURSEDKID CHATGPT PLUS ⚡"

@app.route('/health')
def health():
    return "OK"

# ===== BOT CONFIGURATION =====
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8467227933:AAGFc1a2dY3NQ9jtE37LNAeYJkGtoOqtEfU")
DATA_FILE = "credentials.json"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ===== DATA STORE =====
class Store:
    def __init__(self):
        self.data = self.load()
    
    def load(self):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add(self, email, password, key):
        entry_id = str(len(self.data) + 1)
        self.data[entry_id] = {
            "email": email,
            "password": password,
            "key": key,
            "timestamp": str(datetime.now())
        }
        self.save()
        return entry_id
    
    def get_all(self):
        return self.data

store = Store()

# ===== TELEGRAM FUNCTIONS =====
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, data=data, timeout=10)
        return r.json()
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def get_updates(offset=None):
    url = f"{BASE_URL}/getUpdates"
    params = {"timeout": 30}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=35)
        return r.json().get("result", [])
    except Exception as e:
        print(f"[ERROR] {e}")
        return []

# ===== COMMAND HANDLERS =====
def handle_start(chat_id):
    msg = (
        "⚡ CURSEDKID CHATGPT PLUS ⚡\n"
        "═══════════════════════════\n\n"
        "📌 COMMANDS:\n"
        "/add email password key - Store credentials\n"
        "/list - View all stored\n"
        "/stats - System info\n"
        "/start - Show this menu\n\n"
        "Example: /add test@email.com Pass123 5HK3MXBG5DDWNEYNSPRY4LFXLEUUP4OV"
    )
    send_message(chat_id, msg)

def handle_add(chat_id, args):
    if len(args) < 3:
        send_message(chat_id, "❌ /add [email] [password] [key]\nExample: /add test@email.com Pass123 5HK3MXBG5DDWNEYNSPRY4LFXLEUUP4OV")
        return
    
    email = args[0]
    password = args[1]
    key = args[2]
    
    store.add(email, password, key)
    
    output = f"""✉️ Email : {email}
🔐 Password : {password}

✅ Go to 2fa.live and submit this key
🔑 Key : {key}"""
    
    send_message(chat_id, output)
    send_message(chat_id, f"✅ Credentials stored successfully!")

def handle_list(chat_id):
    data = store.get_all()
    if not data:
        send_message(chat_id, "📭 No credentials stored.")
        return
    
    output = "📋 STORED CREDENTIALS\n"
    output += "═" * 30 + "\n\n"
    
    for entry_id, entry in data.items():
        output += f"ID: {entry_id}\n"
        output += f"✉️ Email : {entry['email']}\n"
        output += f"🔑 Key : {entry['key']}\n"
        output += f"⏱ {entry['timestamp']}\n"
        output += "-" * 30 + "\n"
    
    send_message(chat_id, output[:4000])

def handle_stats(chat_id):
    data = store.get_all()
    output = f"""
📊 CURSEDKID STATISTICS
═══════════════════════

Total Credentials: {len(data)}
Status: ONLINE
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Bot: CURSEDKID CHATGPT PLUS v1.0
"""
    send_message(chat_id, output)

def process_update(update):
    message = update.get("message")
    if not message:
        return
    
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    if not chat_id or not text:
        return
    
    parts = text.split()
    if not parts:
        return
    
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    print(f"[CMD] {command} from {chat_id}")
    
    if command == "/start":
        handle_start(chat_id)
    elif command == "/add":
        handle_add(chat_id, args)
    elif command == "/list":
        handle_list(chat_id)
    elif command == "/stats":
        handle_stats(chat_id)

def run_bot():
    """Main bot polling loop - runs in background thread"""
    print("[CURSEDKID] Bot thread started")
    
    # Verify token
    test = requests.get(f"{BASE_URL}/getMe")
    if test.status_code != 200:
        print("[CURSEDKID] ❌ Invalid bot token!")
        return
    
    print("[CURSEDKID] ✅ Bot connected successfully!")
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                process_update(update)
                offset = update.get("update_id", 0) + 1
            import time
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] {e}")
            import time
            time.sleep(5)

# ===== MAIN ENTRY POINT =====
if __name__ == "__main__":
    print("═" * 50)
    print("⚡ CURSEDKID CHATGPT PLUS ⚡")
    print("═" * 50)
    print(f"TOKEN: {TOKEN[:10]}...{TOKEN[-5:]}")
    print("═" * 50)
    
    # Start bot in background thread
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask server
    port = int(os.environ.get("PORT", 5000))
    print(f"[CURSEDKID] Flask server starting on port {port}")
    app.run(host="0.0.0.0", port=port)