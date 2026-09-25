import os, json, time, requests
import telebot
from telebot import types

BOT_TOKEN = os.environ.get(8768455593:AAEdUBwJxD3K9lFMI8UK1NxcMOLY6zLQx-Y)
bot = telebot.TeleBot(BOT_TOKEN)
DB_FILE = "users.json"

# Load DB
def load_db():
    if not os.path.exists(DB_FILE): return {}
    with open(DB_FILE, "r") as f: return json.load(f)
def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f)

def get_btc_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()
        return r['bitcoin']['usd']
    except: return 63500

def ensure_user(user_id, referrer=None):
    db = load_db()
    uid = str(user_id)
    if uid not in db:
        db[uid] = {"balance": 0.0, "ref_count": 0, "mined": 0, "last_mine": 0, "tasks_done": []}
        # Referral Bonus
        if referrer and referrer!= uid and referrer in db:
            db[referrer]["balance"] += 0.50
            db[referrer]["ref_count"] += 1
        save_db(db)
    return db

@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    ref = args[1] if len(args) > 1 else None
    ensure_user(message.from_user.id, ref)
    show_dashboard(message)

def show_dashboard(message):
    db = load_db()
    user = db[str(message.from_user.id)]
    btc_price = get_btc_price()

    text = f"""💰 **MONEY DASHBOARD**

👤 User: {message.from_user.first_name}
💵 Balance: ${user['balance']:.4f}
👥 Referrals: {user['ref_count']}
⛏️ Mined: {user['mined']} times
₿ BTC Price: ${btc_price:,.2f}

Choose an action below:"""

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("💰 Balance", callback_data="balance"),
        types.InlineKeyboardButton("⛏️ Mine", callback_data="mine"),
        types.InlineKeyboardButton("₿ BTC Price", callback_data="btc"),
        types.InlineKeyboardButton("📋 Tasks", callback_data="tasks"),
        types.InlineKeyboardButton("👥 Referral", callback_data="ref")
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    db = load_db()
    uid = str(call.from_user.id)
    user = db.get(uid, {"balance":0, "ref_count":0, "mined":0, "last_mine":0, "tasks_done":[]})
    btc_price = get_btc_price()

    if call.data == "balance":
        bot.answer_callback_query(call.id, f"Balance: ${user['balance']:.4f}")

    elif call.data == "btc":
        bot.send_message(call.message.chat.id, f"₿ Current BTC Price: ${btc_price:,.2f} USD\n\nPowered by CoinGecko")

    elif call.data == "mine":
        now = time.time()
        if now - user['last_mine'] < 3600: # 1 hour cooldown
            remain = int(3600 - (now - user['last_mine']))
            bot.answer_callback_query(call.id, f"Wait {remain//60} mins to mine again!", show_alert=True)
            return
        user['balance'] += 0.0001
        user['mined'] += 1
        user['last_mine'] = now
        db[uid] = user
        save_db(db)
        bot.answer_callback_query(call.id, "⛏️ Mined +$0.0001!", show_alert=True)
        bot.send_message(call.message.chat.id, f"✅ Mined successfully!\nNew Balance: ${user['balance']:.4f}")

    elif call.data == "tasks":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Join Channel (Reward $0.10)", callback_data="task_join"))
        bot.send_message(call.message.chat.id, "📋 **Available Tasks:**\n\n1. Join our channel to earn $0.10", reply_markup=markup, parse_mode="Markdown")

    elif call.data == "task_join":
        if "join" in user['tasks_done']:
            bot.answer_callback_query(call.id, "Already done!")
            return
        user['balance'] += 0.10
        user['tasks_done'].append("join")
        db[uid] = user
        save_db(db)
        bot.send_message(call.message.chat.id, f"✅ Task Completed! +$0.10\nBalance: ${user['balance']:.4f}")

    elif call.data == "ref":
        link = f"https://t.me/{bot.get_me().username}?start={uid}"
        bot.send_message(call.message.chat.id, f"👥 **Referral System**\n\nYour Link:\n`{link}`\n\nYou get $0.50 per referral!\nYour referrals: {user['ref_count']}", parse_mode="Markdown")

bot.infinity_polling()
