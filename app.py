#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
from datetime import datetime
from flask import Flask
import requests

# ===== FLASK APP FOR KEEP-ALIVE =====
app = Flask(__name__)

@app.route('/')
def home():
    return "\u26A1 CURSEDKID CHATGPT PLUS \u26A1"

@app.route('/health')
def health():
    return "OK"

# ===== BOT CONFIGURATION =====
TOKEN = "8467227933:AAGFc1a2dY3NQ9jtE37LNAeYJkGtoOqtEfU"
DATA_FILE = "credentials.json"
SALES_FILE = "sales.json"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"

# ===== DATA STORE =====
class Store:
    def __init__(self):
        self.data = self.load()
        self.sales = self.load_sales()
    
    def load(self):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def load_sales(self):
        try:
            with open(SALES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"total_sales": 0, "total_revenue": 0, "sold_items": []}
    
    def save_sales(self):
        with open(SALES_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.sales, f, indent=2, ensure_ascii=False)
    
    def add(self, email, password, key):
        entry_id = str(len(self.data) + 1)
        self.data[entry_id] = {
            "email": email,
            "password": password,
            "key": key,
            "timestamp": str(datetime.now()),
            "status": "available"
        }
        self.save()
        return entry_id
    
    def get_all(self):
        return {k: v for k, v in self.data.items() if v.get('status') == 'available'}
    
    def mark_sold(self, entry_id, price):
        if entry_id in self.data and self.data[entry_id].get('status') == 'available':
            self.data[entry_id]["status"] = "sold"
            self.data[entry_id]["sold_price"] = price
            self.data[entry_id]["sold_date"] = str(datetime.now())
            self.save()
            
            self.sales["total_sales"] += 1
            self.sales["total_revenue"] += int(price)
            self.sales["sold_items"].append({
                "id": entry_id,
                "email": self.data[entry_id]["email"],
                "price": price,
                "date": str(datetime.now())
            })
            self.save_sales()
            return True
        return False

store = Store()

# ===== TELEGRAM FUNCTIONS =====
def send_message(chat_id, text, reply_to_message_id=None):
    url = f"{BASE_URL}/sendMessage"
    data = {"chat_id": chat_id, "text": text}
    if reply_to_message_id:
        data["reply_to_message_id"] = reply_to_message_id
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
        "\u26A1 CURSEDKID CHATGPT PLUS \u26A1\n"
        "\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\n\n"
        "\uD83D\uDCCC COMMANDS:\n"
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
        send_message(chat_id, "\u274C /add [email] [password] [key]\nExample: /add test@email.com Pass123 KEY")
        return
    
    email = args[0]
    password = args[1]
    key = args[2]
    
    entry_id = store.add(email, password, key)
    
    output = f"""\u2709\uFE0F Email : {email}
\uD83D\uDD10 Password : {password}

\u2705 Go to 2fa.live and submit this key
\uD83D\uDD11 Key : {key}

\uD83D\uDCCC Status: AVAILABLE
\uD83C\uDD94 ID: {entry_id}"""
    
    send_message(chat_id, output)
    send_message(chat_id, f"\u2705 Credentials stored successfully! ID: {entry_id}")

def handle_sold_with_id(chat_id, args):
    if len(args) < 2:
        send_message(chat_id, "\u274C Use: /sold [price] [id]\nExample: /sold 250 1\n\nUse /list to see available accounts with IDs.")
        return
    
    try:
        price = int(args[0])
        entry_id = args[1]
    except ValueError:
        send_message(chat_id, "\u274C Price must be a number\nExample: /sold 250 1")
        return
    
    if store.mark_sold(entry_id, price):
        sold_item = store.data[entry_id]
        output = f"""\u2705 ACCOUNT SOLD!

\u2709\uFE0F Email : {sold_item['email']}
\uD83D\uDCB0 Price : \u20B9{price} INR
\uD83D\uDCC5 Sold at : {sold_item['sold_date']}

\uD83D\uDCCA SALES SUMMARY:
Total Sales: {store.sales['total_sales']}
Total Revenue: \u20B9{store.sales['total_revenue']} INR
Available Accounts: {len(store.get_all())}"""
        
        send_message(chat_id, output)
    else:
        send_message(chat_id, f"\u274C Account ID {entry_id} not found or already sold.\nUse /list to see available accounts.")

def handle_list(chat_id):
    data = store.get_all()
    
    if not data:
        send_message(chat_id, "\uD83D\uDCED No available credentials. Total sold: " + str(store.sales['total_sales']))
        return
    
    output = "\uD83D\uDCCB AVAILABLE ACCOUNTS\n"
    output += "\u2550" * 30 + "\n\n"
    
    for entry_id, entry in data.items():
        output += f"\uD83C\uDD94 ID: {entry_id}\n"
        output += f"\u2709\uFE0F Email : {entry['email']}\n"
        output += f"\uD83D\uDD11 Key : {entry['key']}\n"
        output += f"\u23F1 Added : {entry['timestamp']}\n"
        output += "-" * 30 + "\n"
    
    output += f"\n\uD83D\uDCCA Total Available: {len(data)}"
    send_message(chat_id, output[:4000])

def handle_stats(chat_id):
    available = len(store.get_all())
    sold = store.sales['total_sales']
    revenue = store.sales['total_revenue']
    
    output = f"""
\uD83D\uDCCA CURSEDKID STOCK STATISTICS
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

\uD83D\uDCCC AVAILABLE ACCOUNTS: {available}
\uD83D\uDCB0 TOTAL SALES: {sold}
\uD83D\uDCB2 TOTAL REVENUE: \u20B9{revenue} INR

\uD83D\uDCC8 PERFORMANCE:
\u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502 Available   : {available:<10} \u2502
\u2502 Sold        : {sold:<10} \u2502
\u2502 Total Stock : {available + sold:<10} \u2502
\u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518

\uD83D\uDD52 Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
\u26A1 Bot: CURSEDKID CHATGPT PLUS v2.0
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
    elif command == "/sold":
        handle_sold_with_id(chat_id, args)
    elif command == "/list":
        handle_list(chat_id)
    elif command == "/stats":
        handle_stats(chat_id)

def run_bot():
    print("[CURSEDKID] Bot thread started")
    test = requests.get(f"{BASE_URL}/getMe")
    if test.status_code != 200:
        print("[CURSEDKID] \u274C Invalid bot token!")
        return
    print("[CURSEDKID] \u2705 Bot connected successfully!")
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

if __name__ == "__main__":
    print("\u2550" * 50)
    print("\u26A1 CURSEDKID CHATGPT PLUS v2.0 \u26A1")
    print("\u2550" * 50)
    print(f"TOKEN: {TOKEN[:10]}...{TOKEN[-5:]}")
    print("\u2550" * 50)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    print(f"[CURSEDKID] Flask server starting on port {port}")
    app.run(host="0.0.0.0", port=port)