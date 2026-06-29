#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import threading
from datetime import datetime
from flask import Flask
import requests

# ===== FLASK APP =====
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

# ===== SIMPLE DATA STORE - NO CLASS =====
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"[ERROR] Loading data: {e}")
        return {}

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Saving data: {e}")
        return False

def load_sales():
    try:
        if os.path.exists(SALES_FILE):
            with open(SALES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"total_sales": 0, "total_revenue": 0, "sold_items": []}
    except Exception as e:
        print(f"[ERROR] Loading sales: {e}")
        return {"total_sales": 0, "total_revenue": 0, "sold_items": []}

def save_sales(sales):
    try:
        with open(SALES_FILE, 'w', encoding='utf-8') as f:
            json.dump(sales, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[ERROR] Saving sales: {e}")
        return False

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
    
    # Load current data
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
    
    # Store data
    data[entry_id] = {
        "email": email,
        "password": password,
        "key": key,
        "timestamp": str(datetime.now()),
        "status": "available"
    }
    
    if save_data(data):
        output = f"""\u2709\uFE0F Email : {email}
\uD83D\uDD10 Password : {password}

\u2705 Go to 2fa.live and submit this key
\uD83D\uDD11 Key : {key}

\uD83D\uDCCC Status: AVAILABLE
\uD83C\uDD94 ID: {entry_id}"""
        
        send_message(chat_id, output)
        send_message(chat_id, f"\u2705 Credentials stored!\n\uD83C\uDD94 ID: {entry_id}\n\nUse: /sold [price] {entry_id}")
    else:
        send_message(chat_id, "\u274C Failed to save credentials. Check logs.")

def handle_sold(chat_id, args):
    if len(args) < 2:
        send_message(chat_id, "\u274C Use: /sold [price] [id]\nExample: /sold 250 1\n\nUse /list to see available accounts.")
        return
    
    try:
        price = int(args[0])
        entry_id = str(args[1])  # Convert to string for dict key
    except ValueError:
        send_message(chat_id, "\u274C Price must be a number\nExample: /sold 250 1")
        return
    
    # Load current data
    data = load_data()
    sales = load_sales()
    
    # Check if entry exists
    if entry_id not in data:
        send_message(chat_id, f"\u274C Account ID {entry_id} not found.\n\nAvailable IDs: {', '.join([k for k, v in data.items() if v.get('status') == 'available'])}\n\nUse /list to see all available accounts.")
        return
    
    entry = data[entry_id]
    
    # Check if already sold
    if entry.get('status') == 'sold':
        send_message(chat_id, f"\u274C Account ID {entry_id} is already sold.\n\nUse /list to see remaining available accounts.")
        return
    
    # Mark as sold
    entry["status"] = "sold"
    entry["sold_price"] = price
    entry["sold_date"] = str(datetime.now())
    
    # Update sales
    sales["total_sales"] += 1
    sales["total_revenue"] += int(price)
    sales["sold_items"].append({
        "id": entry_id,
        "email": entry["email"],
        "price": price,
        "date": str(datetime.now())
    })
    
    # Save both
    if save_data(data) and save_sales(sales):
        # Count available
        available = len([k for k, v in data.items() if v.get('status') == 'available'])
        
        output = f"""\u2705 ACCOUNT SOLD!

\u2709\uFE0F Email : {entry['email']}
\uD83D\uDCB0 Price : \u20B9{price} INR
\uD83D\uDCC5 Sold at : {entry['sold_date']}

\uD83D\uDCCA SALES SUMMARY:
Total Sales: {sales['total_sales']}
Total Revenue: \u20B9{sales['total_revenue']} INR
Available Accounts: {available}"""
        
        send_message(chat_id, output)
    else:
        send_message(chat_id, "\u274C Failed to save sale. Check logs.")

def handle_list(chat_id):
    data = load_data()
    
    available = {k: v for k, v in data.items() if v.get('status') == 'available'}
    
    if not available:
        sales = load_sales()
        send_message(chat_id, f"\uD83D\uDCED No available credentials.\n\nTotal sold: {sales['total_sales']}\nTotal revenue: \u20B9{sales['total_revenue']} INR")
        return
    
    output = "\uD83D\uDCCB AVAILABLE ACCOUNTS\n"
    output += "\u2550" * 30 + "\n\n"
    
    for entry_id in sorted(available.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        entry = available[entry_id]
        output += f"\uD83C\uDD94 ID: {entry_id}\n"
        output += f"\u2709\uFE0F Email : {entry['email']}\n"
        output += f"\uD83D\uDD11 Key : {entry['key']}\n"
        output += f"\u23F1 Added : {entry['timestamp']}\n"
        output += "-" * 30 + "\n"
    
    sales = load_sales()
    output += f"\n\uD83D\uDCCA Total Available: {len(available)}"
    output += f"\n\uD83D\uDCB0 Total Sales: {sales['total_sales']}"
    output += f"\n\uD83D\uDCB2 Total Revenue: \u20B9{sales['total_revenue']} INR"
    send_message(chat_id, output[:4000])

def handle_stats(chat_id):
    data = load_data()
    sales = load_sales()
    
    available = len([k for k, v in data.items() if v.get('status') == 'available'])
    sold = sales['total_sales']
    revenue = sales['total_revenue']
    total = available + sold
    
    output = f"""
\uD83D\uDCCA CURSEDKID STOCK STATISTICS
\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550

\uD83D\uDCCC AVAILABLE ACCOUNTS: {available}
\uD83D\uDCB0 TOTAL SALES: {sold}
\uD83D\uDCB2 TOTAL REVENUE: \u20B9{revenue} INR
\uD83D\uDCCA TOTAL STOCK: {total}

\uD83D\uDCC8 PERFORMANCE:
\u250C\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510
\u2502 Available   : {available:<10} \u2502
\u2502 Sold        : {sold:<10} \u2502
\u2502 Total Stock : {total:<10} \u2502
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
    
    print(f"[CMD] {command} from {chat_id} | Args: {args}")
    
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
    
    # Initialize files
    load_data()
    load_sales()
    
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    print(f"[CURSEDKID] Flask server starting on port {port}")
    app.run(host="0.0.0.0", port=port)