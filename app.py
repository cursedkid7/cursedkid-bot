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
    return "âš¡ CURSEDKID CHATGPT PLUS âš¡"

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
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def load_sales(self):
        try:
            with open(SALES_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"total_sales": 0, "total_revenue": 0, "sold_items": []}
    
    def save_sales(self):
        with open(SALES_FILE, 'w') as f:
            json.dump(self.sales, f, indent=2)
    
    def add(self, email, password, key):
        entry_id = str(len(self.data) + 1)
        self.data[entry_id] = {
            "email": email,
            "password": password,
            "key": key,
            "timestamp": str(datetime.now()),
            "status": "available"  # available, sold
        }
        self.save()
        return entry_id
    
    def get_all(self):
        return {k: v for k, v in self.data.items() if v.get('status') == 'available'}
    
    def get_all_including_sold(self):
        return self.data
    
    def mark_sold(self, entry_id, price):
        if entry_id in self.data:
            self.data[entry_id]["status"] = "sold"
            self.data[entry_id]["sold_price"] = price
            self.data[entry_id]["sold_date"] = str(datetime.now())
            self.save()
            
            # Update sales stats
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
        "âš¡ CURSEDKID CHATGPT PLUS âš¡\n"
        "â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•\n\n"
        "ðŸ“Œ COMMANDS:\n"
        "/add email password key - Store credentials\n"
        "/sold [price] - Mark replied account as sold\n"
        "/list - View available accounts\n"
        "/stats - System info & sales stats\n"
        "/start - Show this menu\n\n"
        "Example: /add test@email.com Pass123 KEY\n"
        "Reply to account with: /sold 250"
    )
    send_message(chat_id, msg)

def handle_add(chat_id, args):
    if len(args) < 3:
        send_message(chat_id, "âŒ /add [email] [password] [key]\nExample: /add test@email.com Pass123 KEY")
        return
    
    email = args[0]
    password = args[1]
    key = args[2]
    
    entry_id = store.add(email, password, key)
    
    output = f"""âœ‰ï¸ Email : {email}
ðŸ” Password : {password}

âœ… Go to 2fa.live and submit this key
ðŸ”‘ Key : {key}

ðŸ“Œ Status: AVAILABLE
ðŸ†” ID: {entry_id}"""
    
    send_message(chat_id, output)
    send_message(chat_id, f"âœ… Credentials stored successfully! ID: {entry_id}")

def handle_sold(chat_id, args, reply_to_message_id=None):
    if not reply_to_message_id:
        send_message(chat_id, "âŒ Reply to an account message with /sold [price]\nExample: Reply to account with /sold 250")
        return
    
    if len(args) < 1:
        send_message(chat_id, "âŒ Please specify price\nExample: /sold 250")
        return
    
    try:
        price = int(args[0])
    except ValueError:
        send_message(chat_id, "âŒ Price must be a number\nExample: /sold 250")
        return
    
    # Find which entry this reply belongs to
    # We search by looking at the replied message text
    found_id = None
    for entry_id, entry in store.get_all_including_sold().items():
        if entry.get('status') == 'available':
            if entry['email'].lower() in str(args) or entry['email'].lower() in str(reply_to_message_id):
                # Actually we need to search properly - we'll implement a better method
                pass
    
    # Better approach: We'll ask for the ID if not found
    send_message(chat_id, "ðŸ“Œ Please provide the Account ID to mark as sold.\nUse /sold [price] [id]\nExample: /sold 250 1")
    send_message(chat_id, "Reply to this message or use: /sold [price] [id]")

def handle_sold_with_id(chat_id, args):
    if len(args) < 2:
        # Try to get from reply
        send_message(chat_id, "âŒ Use: /sold [price] [id]\nExample: /sold 250 1\n\nUse /list to see available accounts with IDs.")
        return
    
    try:
        price = int(args[0])
        entry_id = args[1]
    except ValueError:
        send_message(chat_id, "âŒ Price must be a number\nExample: /sold 250 1")
        return
    
    if store.mark_sold(entry_id, price):
        sold_item = store.data[entry_id]
        output = f"""âœ… ACCOUNT SOLD!

âœ‰ï¸ Email : {sold_item['email']}
ðŸ’° Price : â‚¹{price} INR
ðŸ“… Sold at : {sold_item['sold_date']}

ðŸ“Š SALES SUMMARY:
Total Sales: {store.sales['total_sales']}
Total Revenue: â‚¹{store.sales['total_revenue']} INR
Available Accounts: {len(store.get_all())}"""
        
        send_message(chat_id, output)
        
        # Also send to admin/group update
        admin_msg = f"ðŸ”” SALE UPDATE\nAccount: {sold_item['email']}\nPrice: â‚¹{price} INR\nTotal Revenue: â‚¹{store.sales['total_revenue']} INR"
        send_message(chat_id, admin_msg)
    else:
        send_message(chat_id, f"âŒ Account ID {entry_id} not found or already sold.\nUse /list to see available accounts.")

def handle_list(chat_id):
    data = store.get_all()
    
    if not data:
        send_message(chat_id, "ðŸ“­ No available credentials. Total sold: " + str(store.sales['total_sales']))
        return
    
    output = "ðŸ“‹ AVAILABLE ACCOUNTS\n"
    output += "â•" * 30 + "\n\n"
    
    for entry_id, entry in data.items():
        output += f"ðŸ†” ID: {entry_id}\n"
        output += f"âœ‰ï¸ Email : {entry['email']}\n"
        output += f"ðŸ”‘ Key : {entry['key']}\n"
        output += f"â± Added : {entry['timestamp']}\n"
        output += "-" * 30 + "\n"
    
    output += f"\nðŸ“Š Total Available: {len(data)}"
    send_message(chat_id, output[:4000])

def handle_stats(chat_id):
    available = len(store.get_all())
    sold = store.sales['total_sales']
    revenue = store.sales['total_revenue']
    
    output = f"""
ðŸ“Š CURSEDKID STOCK STATISTICS
â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

ðŸ“Œ AVAILABLE ACCOUNTS: {available}
ðŸ’° TOTAL SALES: {sold}
ðŸ’µ TOTAL REVENUE: â‚¹{revenue} INR

ðŸ“ˆ PERFORMANCE:
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚ Available   : {available:<10} â”‚
â”‚ Sold        : {sold:<10} â”‚
â”‚ Total Stock : {available + sold:<10} â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜

ðŸ• Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
âš¡ Bot: CURSEDKID CHATGPT PLUS v2.0
"""
    send_message(chat_id, output)

def process_update(update):
    message = update.get("message")
    if not message:
        return
    
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    reply_to_message = message.get("reply_to_message")
    reply_to_message_id = reply_to_message.get("message_id") if reply_to_message else None
    
    if not chat_id or not text:
        return
    
    parts = text.split()
    if not parts:
        return
    
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    
    print(f"[CMD] {command} from {chat_id} | Args: {args} | Reply: {reply_to_message_id}")
    
    if command == "/start":
        handle_start(chat_id)
    elif command == "/add":
        handle_add(chat_id, args)
    elif command == "/sold":
        # Check if we have enough args for ID method
        if len(args) >= 2:
            handle_sold_with_id(chat_id, args)
        else:
            # Try the reply method or guide user
            handle_sold(chat_id, args, reply_to_message_id)
    elif command == "/list":
        handle_list(chat_id)
    elif command == "/stats":
        handle_stats(chat_id)

def run_bot():
    print("[CURSEDKID] Bot thread started")
    test = requests.get(f"{BASE_URL}/getMe")
    if test.status_code != 200:
        print("[CURSEDKID] âŒ Invalid bot token!")
        return
    print("[CURSEDKID] âœ… Bot connected successfully!")
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
    print("â•" * 50)
    print("âš¡ CURSEDKID CHATGPT PLUS v2.0 âš¡")
    print("â•" * 50)
    print(f"TOKEN: {TOKEN[:10]}...{TOKEN[-5:]}")
    print("â•" * 50)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 5000))
    print(f"[CURSEDKID] Flask server starting on port {port}")
    app.run(host="0.0.0.0", port=port)
