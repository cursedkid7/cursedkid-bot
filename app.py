#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
import time
from datetime import datetime
from flask import Flask
import requests

# ===== FLASK APP =====
app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ CURSEDKID CHATGPT PLUS ⚡"

@app.route('/health')
def health():
    return "OK"

# ===== BOT CONFIGURATION =====
TOKEN = "7949577559:AAGBU6z90IF4fDzHwJFb9oYVhkKo8lHw2g4"
CHAT_ID = 5489125607  # Your group ID
DATA_FILE = "credentials.json"
SALES_FILE = "sales.json"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ===== DATA FUNCTIONS =====
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def load_sales():
    try:
        if os.path.exists(SALES_FILE):
            with open(SALES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"total_sales": 0, "total_revenue": 0, "sold_items": []}
    except:
        return {"total_sales": 0, "total_revenue": 0, "sold_items": []}

def save_sales(sales):
    try:
        with open(SALES_FILE, 'w', encoding='utf-8') as f:
            json.dump(sales, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

# ===== TELEGRAM FUNCTIONS =====
def send_message(chat_id, text):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    try:
        r = requests.post(url, data=data, timeout=10)
        print(f"[SEND] {text[:50]}...")
        return r.json()
    except Exception as e:
        print(f"[ERROR] Send: {e}")
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
        print(f"[ERROR] Get updates: {e}")
        return []

# ===== COMMAND HANDLERS =====
def handle_start(chat_id):
    msg = (
        "⚡ CURSEDKID CHATGPT PLUS ⚡\n"
        "═══════════════════════════\n\n"
        "📌 COMMANDS:\n"
        "/add email password key - Store credentials\n"
        "/sold [price] [id] - Mark account as sold\n"
        "/list - View available accounts\n"
        "/stats - System info & sales stats\n"
        "/start - Show this menu\n\n"
        "Example: /add test@email.com Pass123 KEY\n"
        "Use: /sold 250 1"
    )
    send_message(chat_id, msg)

def handle_add(chat_id, args):
    if len(args) < 3:
        send_message(chat_id, "❌ /add [email] [password] [key]")
        return
    
    data = load_data()
    email = args[0]
    password = args[1]
    key = args[2]
    
    # Generate ID
    if data:
        max_id = max([int(k) for k in data.keys() if k.isdigit()], default=0)
        entry_id = str(max_id + 1)
    else:
        entry_id = "1"
    
    data[entry_id] = {
        "email": email,
        "password": password,
        "key": key,
        "timestamp": str(datetime.now()),
        "status": "available"
    }
    
    if save_data(data):
        output = f"""✉️ Email : {email}
🔐 Password : {password}

✅ Go to 2fa.live and submit this key
🔑 Key : {key}

📌 Status: AVAILABLE
🆔 ID: {entry_id}"""
        
        send_message(chat_id, output)
        send_message(chat_id, f"✅ Credentials stored!\n🆔 ID: {entry_id}\n\nUse: /sold [price] {entry_id}")
    else:
        send_message(chat_id, "❌ Failed to save credentials.")

def handle_sold(chat_id, args):
    if len(args) < 2:
        send_message(chat_id, "❌ Use: /sold [price] [id]\nExample: /sold 250 1")
        return
    
    try:
        price = int(args[0])
        entry_id = str(args[1])
    except:
        send_message(chat_id, "❌ Price must be a number")
        return
    
    data = load_data()
    sales = load_sales()
    
    if entry_id not in data:
        available = [k for k, v in data.items() if v.get('status') == 'available']
        msg = f"❌ Account ID {entry_id} not found.\n\nAvailable IDs: {', '.join(available) if available else 'None'}"
        send_message(chat_id, msg)
        return
    
    entry = data[entry_id]
    if entry.get('status') == 'sold':
        send_message(chat_id, f"❌ Account ID {entry_id} is already sold.")
        return
    
    # Mark as sold
    entry["status"] = "sold"
    entry["sold_price"] = price
    entry["sold_date"] = str(datetime.now())
    
    sales["total_sales"] += 1
    sales["total_revenue"] += int(price)
    sales["sold_items"].append({
        "id": entry_id,
        "email": entry["email"],
        "price": price,
        "date": str(datetime.now())
    })
    
    if save_data(data) and save_sales(sales):
        available = len([k for k, v in data.items() if v.get('status') == 'available'])
        output = f"""✅ ACCOUNT SOLD!

✉️ Email : {entry['email']}
💰 Price : ₹{price} INR
📅 Sold at : {entry['sold_date']}

📊 SALES SUMMARY:
Total Sales: {sales['total_sales']}
Total Revenue: ₹{sales['total_revenue']} INR
Available Accounts: {available}"""
        
        send_message(chat_id, output)
    else:
        send_message(chat_id, "❌ Failed to mark as sold.")

def handle_list(chat_id):
    data = load_data()
    available = {k: v for k, v in data.items() if v.get('status') == 'available'}
    
    if not available:
        sales = load_sales()
        send_message(chat_id, f"📭 No available credentials.\n\nTotal sold: {sales['total_sales']}\nTotal revenue: ₹{sales['total_revenue']} INR")
        return
    
    output = "📋 AVAILABLE ACCOUNTS\n"
    output += "═" * 30 + "\n\n"
    
    for entry_id in sorted(available.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        entry = available[entry_id]
        output += f"🆔 ID: {entry_id}\n"
        output += f"✉️ Email : {entry['email']}\n"
        output += f"🔑 Key : {entry['key']}\n"
        output += f"⏱ Added : {entry['timestamp']}\n"
        output += "-" * 30 + "\n"
    
    sales = load_sales()
    output += f"\n📊 Total Available: {len(available)}"
    output += f"\n💰 Total Sales: {sales['total_sales']}"
    output += f"\n💵 Total Revenue: ₹{sales['total_revenue']} INR"
    
    send_message(chat_id, output[:4000])

def handle_stats(chat_id):
    data = load_data()
    sales = load_sales()
    
    available = len([k for k, v in data.items() if v.get('status') == 'available'])
    sold = sales['total_sales']
    revenue = sales['total_revenue']
    total = available + sold
    
    output = f"""
📊 CURSEDKID STOCK STATISTICS
═══════════════════════════════════

📌 AVAILABLE ACCOUNTS: {available}
💰 TOTAL SALES: {sold}
💵 TOTAL REVENUE: ₹{revenue} INR
📦 TOTAL STOCK: {total}

📈 PERFORMANCE:
┌─────────────────────────────────┐
│ Available   : {available:<10} │
│ Sold        : {sold:<10} │
│ Total Stock : {total:<10} │
└─────────────────────────────────┘

🕐 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
⚡ Bot: CURSEDKID CHATGPT PLUS v2.0
"""
    send_message(chat_id, output)

# ===== PROCESS UPDATES =====
def process_update(update):
    message = update.get("message")
    if not message:
        return
    
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    
    if not chat_id or not text:
        return
    
    print(f"[MSG] From {chat_id}: {text}")
    
    parts = text.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    if command == "/start":
        handle_start(chat_id)
    elif command == "/add":
        handle_add(chat_id, args)
    elif command == "/sold":
        handle_sold(chat_id, args)
    elif command == "/list":
        handle_list(chat_id)
    elif command == "/stats":
        handle_stats(chat_id)
    else:
        send_message(chat_id, f"❌ Unknown command: {command}\n\nSend /start for help.")

# ===== BOT MAIN LOOP =====
def run_bot():
    print("[CURSEDKID] Bot thread started")
    
    # Test connection
    test = requests.get(f"{BASE_URL}/getMe")
    if test.status_code != 200:
        print("[CURSEDKID] ❌ Invalid token!")
        return
    print("[CURSEDKID] ✅ Bot connected successfully!")
    
    # Send startup message
    send_message(CHAT_ID, "⚡ CURSEDKID BOT ONLINE ⚡\n\nBot is now active and ready!")
    
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                process_update(update)
                offset = update.get("update_id", 0) + 1
            time.sleep(1)
        except Exception as e:
            print(f"[ERROR] Loop: {e}")
            time.sleep(5)

# ===== MAIN ENTRY =====
if __name__ == "__main__":
    print("═" * 50)
    print("⚡ CURSEDKID CHATGPT PLUS v2.0 ⚡")
    print("═" * 50)
    print(f"TOKEN: {TOKEN[:10]}...{TOKEN[-5:]}")
    print(f"CHAT_ID: {CHAT_ID}")
    print("═" * 50)
    
    # Start bot in background
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Start Flask
    port = int(os.environ.get("PORT", 5000))
    print(f"[CURSEDKID] Flask server on port {port}")
    app.run(host="0.0.0.0", port=port)
