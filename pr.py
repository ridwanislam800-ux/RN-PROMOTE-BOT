import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import requests
import random
import time

# ==========================================
# ⚙️ CONFIGURATION & DIGITAL SETUP
# ==========================================
BOT_TOKEN = "8918470077:AAHRsGl-juI5u8Dtp2eYeqVQLc1HvGGcFl0" # <-- এখানে আপনার টোকেন দিন
ADMIN_ID = 8477879892
MANDATORY_CHANNELS = ["@rn_promote_99", "@rn_promote_official"]
AUTO_POST_CHANNEL = "@rn_promote_99"
CONTACT_USER = "@mr_shadowx_99"

# 🔥 FIREBASE CONFIGURATION (REST API)
FIREBASE_URL = "https://pr-bot-e9a5f-default-rtdb.firebaseio.com"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==========================================
# 🔥 FIREBASE DATABASE HELPER FUNCTIONS
# ==========================================
def get_db(path):
    try:
        res = requests.get(f"{FIREBASE_URL}/{path}.json")
        return res.json() if res.status_code == 200 else None
    except:
        return None

def set_db(path, data):
    requests.put(f"{FIREBASE_URL}/{path}.json", json=data)

def update_db(path, data):
    requests.patch(f"{FIREBASE_URL}/{path}.json", json=data)

def push_db(path, data):
    res = requests.post(f"{FIREBASE_URL}/{path}.json", json=data)
    return res.json().get('name') if res.status_code == 200 else None

# ==========================================
# 🛠️ USER MANAGEMENT FUNCTIONS
# ==========================================
def add_user(user_id, username, referred_by=0):
    user = get_db(f"users/{user_id}")
    if not user:
        # Create new user
        new_user_data = {
            "username": username,
            "balance": 0,
            "referred_by": referred_by,
            "is_banned": False
        }
        set_db(f"users/{user_id}", new_user_data)
        
        # Add refer bonus if valid
        if referred_by != 0 and referred_by != user_id:
            ref_user = get_db(f"users/{referred_by}")
            if ref_user:
                new_balance = ref_user.get("balance", 0) + 1
                update_db(f"users/{referred_by}", {"balance": new_balance})
                try:
                    bot.send_message(referred_by, "💠 <b>নতুন রেফার বোনাস!</b>\nএকজন নতুন ইউজার আপনার লিংকে জয়েন করেছে। আপনি 1 Coin পেয়েছেন! 💸")
                except:
                    pass

def get_user(user_id):
    return get_db(f"users/{user_id}")

def add_balance(user_id, amount):
    user = get_db(f"users/{user_id}")
    if user:
        new_balance = user.get("balance", 0) + amount
        update_db(f"users/{user_id}", {"balance": new_balance})
        return True
    return False

def is_banned(user_id):
    user = get_user(user_id)
    return user.get("is_banned", False) if user else False

# ==========================================
# 🎨 DIGITAL KEYBOARDS
# ==========================================
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("📋 Task"), KeyboardButton("👤 Profile"))
    markup.add(KeyboardButton("📝 Post"), KeyboardButton("🔗 Refer"))
    markup.add(KeyboardButton("💳 Deposit"), KeyboardButton("💲 Price"))
    return markup

def cancel_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("❌ Cancel"))
    return markup

# ==========================================
# 🛡️ CAPTCHA & VERIFICATION SYSTEM
# ==========================================
temp_data = {}

def generate_captcha(user_id):
    num1, num2 = random.randint(1, 10), random.randint(1, 10)
    ans = num1 + num2
    temp_data[f"cap_{user_id}"] = ans
    
    markup = InlineKeyboardMarkup()
    options = [ans, ans+random.randint(1,3), ans-random.randint(1,3), ans+random.randint(4,6)]
    random.shuffle(options)
    
    row = [InlineKeyboardButton(str(opt), callback_data=f"cap_{opt}_{user_id}") for opt in options]
    markup.add(*row)
    return f"🤖 <b>সিস্টেম সিকিউরিটি চেক:</b>\nদয়া করে নিচের অংকটি সমাধান করুন:\n\n{num1} + {num2} = ?", markup

def check_channel_joins(user_id, channels):
    for ch in channels:
        try:
            status = bot.get_chat_member(ch, user_id).status
            if status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

def force_join_keyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💠 Join Channel 1", url="https://t.me/rn_promote_99"))
    markup.add(InlineKeyboardButton("💠 Join Channel 2", url="https://t.me/rn_promote_official"))
    markup.add(InlineKeyboardButton("✅ Verify", callback_data="verify_join"))
    return markup

# ==========================================
# 🚀 START & ENTRY POINTS
# ==========================================
@bot.message_handler(commands=['start', 'cancel'])
def start_bot(message):
    if is_banned(message.chat.id):
        return bot.reply_to(message, "🚫 <b>অ্যাক্সেস ডিনাইড:</b> আপনাকে সিস্টেম থেকে ব্যান করা হয়েছে।")
        
    # Handle /cancel
    if message.text == '/cancel':
        bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
        return bot.send_message(message.chat.id, "✅ সব প্রসেস বাতিল করা হয়েছে।", reply_markup=main_menu())

    # Handle Referral
    args = message.text.split()
    if len(args) > 1 and args[1].isdigit():
        temp_data[f"ref_{message.chat.id}"] = int(args[1])
        
    user = get_user(message.chat.id)
    if user:
        # Already registered
        bot.send_message(message.chat.id, "✅ <b>স্বাগতম!</b>\nডিজিটাল প্রমোট বটে আপনাকে আবার স্বাগতম। 💠", reply_markup=main_menu())
    else:
        # New user, send captcha
        text, markup = generate_captcha(message.chat.id)
        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('cap_'))
def verify_captcha(call):
    data = call.data.split('_')
    ans, user_id = int(data[1]), int(data[2])
    
    if call.from_user.id != user_id:
        return bot.answer_callback_query(call.id, "❌ এটি আপনার ক্যাপচা নয়!", show_alert=True)
        
    correct_ans = temp_data.get(f"cap_{user_id}")
    if ans == correct_ans:
        bot.delete_message(call.message.chat.id, call.message.message_id)
        if not check_channel_joins(user_id, MANDATORY_CHANNELS):
            bot.send_message(user_id, "⚠️ <b>সিস্টেম অ্যালার্ট:</b>\nবটটি ব্যবহার করতে হলে আপনাকে আগে আমাদের চ্যানেলগুলোতে যুক্ত হতে হবে।", reply_markup=force_join_keyboard())
        else:
            ref_id = temp_data.get(f"ref_{user_id}", 0)
            add_user(user_id, call.from_user.username or "User", ref_id)
            bot.send_message(user_id, "✅ <b>ভেরিফিকেশন সফল!</b>\nডিজিটাল প্রমোট বটে আপনাকে স্বাগতম। 💠", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ ভুল উত্তর! আবার চেষ্টা করুন।", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "verify_join")
def verify_channels(call):
    if check_channel_joins(call.from_user.id, MANDATORY_CHANNELS):
        bot.delete_message(call.message.chat.id, call.message.message_id)
        ref_id = temp_data.get(f"ref_{call.from_user.id}", 0)
        add_user(call.from_user.id, call.from_user.username or "User", ref_id)
        bot.send_message(call.message.chat.id, "✅ <b>সিস্টেম ভেরিফাইড!</b>\nডিজিটাল প্রমোট বটে আপনাকে স্বাগতম। 💠", reply_markup=main_menu())
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো সবগুলো চ্যানেলে জয়েন করেননি!", show_alert=True)

# ==========================================
# 📱 GENERAL MENU COMMANDS
# ==========================================
@bot.message_handler(func=lambda message: message.text == "❌ Cancel")
def cancel_all(message):
    bot.clear_step_handler_by_chat_id(chat_id=message.chat.id)
    bot.send_message(message.chat.id, "✅ বাতিল করা হয়েছে।", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "👤 Profile")
def profile(message):
    if is_banned(message.chat.id): return
    user = get_user(message.chat.id)
    if not user: return start_bot(message)
    
    text = f"""
💠 <b>ডিজিটাল ইউজার প্রোফাইল</b> 💠
━━━━━━━━━━━━━━━━━━
👤 <b>ইউজার:</b> @{user.get('username')}
🆔 <b>আইডি:</b> <code>{message.chat.id}</code>
💰 <b>ব্যালেন্স:</b> {user.get('balance')} Coins
━━━━━━━━━━━━━━━━━━
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "💲 Price")
def price(message):
    text = f"""
📊 <b>অফিসিয়াল কয়েন প্রাইস লিস্ট</b> 📊
━━━━━━━━━━━━━━━━━━
💠 50 Coin = 50 TK
💠 100 Coin = 90 TK
💠 200 Coin = 170 TK
💠 500 Coin = 400 TK
💠 1000 Coin = 800 TK
━━━━━━━━━━━━━━━━━━
📞 <b>যেকোনো প্রয়োজনে যোগাযোগ করুন:</b> {CONTACT_USER}
"""
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda message: message.text == "🔗 Refer")
def refer(message):
    bot_info = bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={message.chat.id}"
    text = f"""
🚀 <b>ডিজিটাল রেফারেল সিস্টেম</b> 🚀
━━━━━━━━━━━━━━━━━━
আপনার রেফারেল লিংক ব্যবহার করে বন্ধুদের জয়েন করান এবং প্রতি জয়েনে 1 কয়েন ইনকাম করুন!
(⚠️ ফেক রেফার করলে একাউন্ট ব্যান করা হবে)

🔗 <b>আপনার লিংক:</b>
<code>{ref_link}</code>
━━━━━━━━━━━━━━━━━━
"""
    bot.send_message(message.chat.id, text)

# ==========================================
# 💳 DEPOSIT SYSTEM (FLAWLESS)
# ==========================================
@bot.message_handler(func=lambda message: message.text == "💳 Deposit")
def deposit_start(message):
    if is_banned(message.chat.id): return
    msg = bot.send_message(message.chat.id, "💸 <b>ডিপোজিট সিস্টেম:</b>\nকত কয়েন ডিপোজিট করতে চান? (Minimum 50)\n\n<i>বাতিল করতে চাইলে ❌ Cancel এ চাপুন।</i>", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, process_deposit_amount)

def process_deposit_amount(message):
    if message.text == "❌ Cancel": return cancel_all(message)
    if not message.text.isdigit() or int(message.text) < 50:
        msg = bot.send_message(message.chat.id, "❌ অংকটি সঠিক নয় বা 50 এর কম। পুনরায় সঠিক পরিমাণ লিখুন:")
        return bot.register_next_step_handler(msg, process_deposit_amount)
    
    amount = int(message.text)
    tk_amount = amount 
    if amount >= 1000: tk_amount = int((amount/1000)*800)
    elif amount >= 500: tk_amount = int((amount/500)*400)
    elif amount >= 200: tk_amount = int((amount/200)*170)
    elif amount >= 100: tk_amount = int((amount/100)*90)
    
    text = f"""
💳 <b>পেমেন্ট ইনফরমেশন:</b>

আপনাকে <b>{tk_amount} টাকা</b> সেন্ড মানি করতে হবে।
━━━━━━━━━━━━━━━━━━
🔹 <b>bKash:</b> <code>01644556523</code> (Personal)
🔹 <b>Nagad:</b> <code>01726747629</code> (Personal)
━━━━━━━━━━━━━━━━━━
✅ টাকা পাঠিয়ে <b>স্ক্রিনশটটি</b> এখানে দিন।
"""
    msg = bot.send_message(message.chat.id, text, reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, process_deposit_screenshot, amount)

def process_deposit_screenshot(message, amount):
    if message.text == "❌ Cancel": return cancel_all(message)
    if not message.photo:
        msg = bot.send_message(message.chat.id, "❌ আপনি কোনো স্ক্রিনশট দেননি। দয়া করে স্ক্রিনশট সেন্ড করুন:")
        return bot.register_next_step_handler(msg, process_deposit_screenshot, amount)
    
    # Push deposit to Firebase
    deposit_data = {
        "user_id": message.chat.id,
        "amount": amount,
        "status": "pending"
    }
    dep_id = push_db("deposits", deposit_data)
    
    photo = message.photo[-1].file_id
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Confirm", callback_data=f"dep_conf_{dep_id}"),
               InlineKeyboardButton("❌ Reject", callback_data=f"dep_rej_{dep_id}"))
    
    admin_msg = f"💳 <b>নতুন ডিপোজিট রিকোয়েস্ট</b>\n\n👤 ইউজার: {message.chat.id}\n💰 এমাউন্ট: {amount} Coin"
    bot.send_photo(ADMIN_ID, photo, caption=admin_msg, reply_markup=markup)
    
    bot.send_message(message.chat.id, "⏳ <b>অনুরোধ সাবমিট হয়েছে!</b>\nঅ্যাডমিন চেক করে ব্যালেন্স অ্যাড করে দিবে।", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('dep_'))
def handle_deposit_admin(call):
    if call.from_user.id != ADMIN_ID: return
    
    parts = call.data.split('_')
    action, dep_id = parts[1], parts[2]
    
    dep = get_db(f"deposits/{dep_id}")
    if not dep or dep.get("status") != "pending":
        return bot.answer_callback_query(call.id, "❌ এই রিকোয়েস্ট আগেই প্রসেস করা হয়েছে।", show_alert=True)
        
    user_id, amount = dep["user_id"], dep["amount"]
    
    if action == "conf":
        update_db(f"deposits/{dep_id}", {"status": "approved"})
        add_balance(user_id, amount)
        bot.edit_message_caption(f"✅ Approved. Amount: {amount} Coin Added to {user_id}", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_id, f"🎉 <b>ডিপোজিট সফল!</b>\nআপনার একাউন্টে {amount} Coins অ্যাড করা হয়েছে।")
        except: pass
    else:
        update_db(f"deposits/{dep_id}", {"status": "rejected"})
        bot.edit_message_caption(f"❌ Rejected request of {user_id}", call.message.chat.id, call.message.message_id)
        try:
            bot.send_message(user_id, f"❌ <b>ডিপোজিট বাতিল!</b>\nআপনার ডিপোজিট রিকোয়েস্ট অ্যাডমিন বাতিল করেছেন।")
        except: pass

# ==========================================
# 📝 POST TASK SYSTEM
# ==========================================
@bot.message_handler(func=lambda message: message.text == "📝 Post")
def post_task_start(message):
    user = get_user(message.chat.id)
    if not user or user.get("balance", 0) < 20:
        return bot.send_message(message.chat.id, "❌ আপনার ব্যালেন্স পর্যাপ্ত নয়। Task পোস্ট করতে মিনিমাম 20 Coin লাগবে।")
        
    msg = bot.send_message(message.chat.id, "⚙️ <b>টাস্ক ক্রিয়েশন সিস্টেম:</b>\nদয়া করে আপনার চ্যানেলের লিংকটি দিন (যেমন: https://t.me/username অথবা @username):", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, process_task_link)

def process_task_link(message):
    if message.text == "❌ Cancel": return cancel_all(message)
    channel_link = message.text
    
    # Format channel ID for API check
    chat_id = channel_link
    if "t.me/" in channel_link:
        chat_id = "@" + channel_link.split("t.me/")[1]
    
    try:
        member = bot.get_chat_member(chat_id, bot.get_me().id)
        if member.status not in ['administrator', 'creator']:
            raise Exception("Not admin")
    except:
        msg = bot.send_message(message.chat.id, "❌ বটটি এই চ্যানেলের এডমিন নয় অথবা লিংকটি ভুল। বটকে এডমিন বানিয়ে আবার লিংক দিন:")
        return bot.register_next_step_handler(msg, process_task_link)
        
    temp_data[f"post_link_{message.chat.id}"] = chat_id
    msg = bot.send_message(message.chat.id, "✅ চ্যানেল ভেরিফাইড!\n\nএবার বলুন, প্রতি মেম্বারের জন্য কত Coin দিতে চান? (মিনিমাম 1 Coin)")
    bot.register_next_step_handler(msg, process_task_reward)

def process_task_reward(message):
    if message.text == "❌ Cancel": return cancel_all(message)
    if not message.text.isdigit() or int(message.text) < 1:
        msg = bot.send_message(message.chat.id, "❌ পরিমাণটি সঠিক নয়। মিনিমাম 1 Coin লিখতে হবে:")
        return bot.register_next_step_handler(msg, process_task_reward)
        
    temp_data[f"post_reward_{message.chat.id}"] = int(message.text)
    msg = bot.send_message(message.chat.id, "👥 এবার বলুন, মোট কতজন মেম্বার (Worker) চান? (মিনিমাম 10)")
    bot.register_next_step_handler(msg, process_task_workers)

def process_task_workers(message):
    if message.text == "❌ Cancel": return cancel_all(message)
    if not message.text.isdigit() or int(message.text) < 10:
        msg = bot.send_message(message.chat.id, "❌ পরিমাণটি সঠিক নয়। মিনিমাম 10 লিখতে হবে:")
        return bot.register_next_step_handler(msg, process_task_workers)
        
    total_workers = int(message.text)
    reward = temp_data.get(f"post_reward_{message.chat.id}")
    link = temp_data.get(f"post_link_{message.chat.id}")
    total_cost = total_workers * reward
    
    user = get_user(message.chat.id)
    if user.get("balance", 0) < total_cost:
        return bot.send_message(message.chat.id, f"❌ আপনার ব্যালেন্স অপর্যাপ্ত। এই টাস্কের জন্য {total_cost} Coin প্রয়োজন।", reply_markup=main_menu())
        
    # Deduct balance
    add_balance(message.chat.id, -total_cost)
    
    # Save Task to Firebase
    task_data = {
        "creator_id": message.chat.id,
        "channel_link": link,
        "reward": reward,
        "total_workers": total_workers,
        "current_workers": 0,
        "status": "active"
    }
    push_db("tasks", task_data)
    
    bot.send_message(message.chat.id, "✅ <b>টাস্ক সফলভাবে তৈরি হয়েছে!</b>\nএটি নেটওয়ার্কে লাইভ হয়েছে।", reply_markup=main_menu())
    
    # Auto Post to Channel
    invite_link = f"https://t.me/{link.replace('@', '')}"
    post_text = f"""
🚀 <b>New Digital Task Available!</b> 🚀
━━━━━━━━━━━━━━━━━━
💰 <b>Reward:</b> {reward} Coins
👥 <b>Total Workers Needed:</b> {total_workers}
━━━━━━━━━━━━━━━━━━
📥 <a href="{invite_link}">Click Here to Join Channel</a>

🤖 <i>Bot: @{bot.get_me().username}</i>
"""
    try:
        bot.send_message(AUTO_POST_CHANNEL, post_text, disable_web_page_preview=True)
    except: pass

# ==========================================
# 📋 DO TASK SYSTEM
# ==========================================
@bot.message_handler(func=lambda message: message.text == "📋 Task")
def fetch_task(message):
    if is_banned(message.chat.id): return
    all_tasks = get_db("tasks") or {}
    user_history = get_db(f"history/{message.chat.id}") or {}
    
    available_task_id = None
    task_info = None
    
    for t_id, data in all_tasks.items():
        if data.get("status") == "active" and data.get("creator_id") != message.chat.id:
            if t_id not in user_history:
                available_task_id = t_id
                task_info = data
                break
                
    if not available_task_id:
        return bot.send_message(message.chat.id, "📭 <b>এই মুহূর্তে নতুন কোনো টাস্ক নেই।</b>\nদয়া করে কিছুক্ষণ পর আবার চেষ্টা করুন।")
        
    link = task_info.get("channel_link")
    reward = task_info.get("reward")
    btn_link = f"https://t.me/{link.replace('@', '')}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💠 Join Channel", url=btn_link))
    markup.add(InlineKeyboardButton("✅ Check", callback_data=f"check_task_{available_task_id}"))
    
    bot.send_message(message.chat.id, f"📌 <b>নতুন টাস্ক:</b>\n\nনিচের চ্যানেলে জয়েন করে Check বাটনে ক্লিক করুন এবং জিতে নিন <b>{reward} Coins!</b>", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('check_task_'))
def verify_task(call):
    task_id = call.data.split('_')[2]
    task = get_db(f"tasks/{task_id}")
    
    if not task or task.get("status") != "active":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return bot.answer_callback_query(call.id, "❌ এই টাস্কটি শেষ হয়ে গেছে বা ডিলিট করা হয়েছে!", show_alert=True)
        
    link = task.get("channel_link")
    reward = task.get("reward")
    
    if check_channel_joins(call.from_user.id, [link]):
        # Joined Successfully
        # Mark history
        update_db(f"history/{call.from_user.id}", {task_id: True})
        
        # Update Task Status
        current = task.get("current_workers", 0) + 1
        total = task.get("total_workers", 1)
        status = "active" if current < total else "completed"
        update_db(f"tasks/{task_id}", {"current_workers": current, "status": status})
        
        # Add Balance
        add_balance(call.from_user.id, reward)
        
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.answer_callback_query(call.id, f"🎉 টাস্ক সফল! আপনি {reward} Coins পেয়েছেন।", show_alert=True)
        bot.send_message(call.message.chat.id, f"✅ <b>টাস্ক সফল!</b>\n{reward} Coins আপনার ব্যালেন্সে যোগ করা হয়েছে।")
    else:
        bot.answer_callback_query(call.id, "❌ আপনি এখনো চ্যানেলে জয়েন করেননি! ভালো করে চেক করুন।", show_alert=True)

# ==========================================
# ⚙️ ADMIN PANEL SYSTEM (/adminpanel)
# ==========================================
def admin_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("👥 Manage User"), KeyboardButton("💰 User Balance"))
    markup.add(KeyboardButton("📢 Broadcast"), KeyboardButton("🏠 Exit Admin"))
    return markup

@bot.message_handler(commands=['adminpanel'])
def open_admin_panel(message):
    if message.chat.id != ADMIN_ID:
        return bot.send_message(message.chat.id, "🚫 <b>Error 403:</b> Unauthorized Access!")
    bot.send_message(message.chat.id, "⚙️ <b>Advanced Firebase Admin Control Panel</b> ⚙️", reply_markup=admin_menu())

@bot.message_handler(func=lambda message: message.text == "🏠 Exit Admin" and message.chat.id == ADMIN_ID)
def exit_admin(message):
    bot.send_message(message.chat.id, "✅ এডমিন প্যানেল বন্ধ করা হয়েছে।", reply_markup=main_menu())

# Manage User
@bot.message_handler(func=lambda message: message.text == "👥 Manage User" and message.chat.id == ADMIN_ID)
def admin_manage_user(message):
    msg = bot.send_message(message.chat.id, "ইউজারের ID দিন:", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, process_admin_manage_user)

def process_admin_manage_user(message):
    if message.text == "❌ Cancel": return cancel_all(message)
    user_id = message.text
    user = get_user(user_id)
    if not user: return bot.send_message(message.chat.id, "❌ ইউজার পাওয়া যায়নি।", reply_markup=admin_menu())
    
    status = "Banned" if user.get("is_banned") else "Active"
    text = f"👤 User Info:\nID: {user_id}\nUsername: @{user.get('username')}\nBalance: {user.get('balance')}\nStatus: {status}"
    
    markup = InlineKeyboardMarkup()
    if user.get("is_banned"):
        markup.add(InlineKeyboardButton("✅ Unban User", callback_data=f"adm_unban_{user_id}"))
    else:
        markup.add(InlineKeyboardButton("🚫 Ban User", callback_data=f"adm_ban_{user_id}"))
        
    bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('adm_'))
def handle_admin_actions(call):
    if call.from_user.id != ADMIN_ID: return
    action, user_id = call.data.split('_')[1], call.data.split('_')[2]
    
    is_ban = True if action == "ban" else False
    update_db(f"users/{user_id}", {"is_banned": is_ban})
    
    bot.answer_callback_query(call.id, f"User {action}ned successfully!", show_alert=True)
    bot.delete_message(call.message.chat.id, call.message.message_id)

# Broadcast
@bot.message_handler(func=lambda message: message.text == "📢 Broadcast" and message.chat.id == ADMIN_ID)
def admin_broadcast(message):
    msg = bot.send_message(message.chat.id, "ব্রডকাস্ট মেসেজ লিখুন (Text/Photo):", reply_markup=cancel_menu())
    bot.register_next_step_handler(msg, process_broadcast)

def process_broadcast(message):
    if message.text == "❌ Cancel": return bot.send_message(message.chat.id, "বাতিল", reply_markup=admin_menu())
    
    bot.send_message(message.chat.id, "⏳ ব্রডকাস্ট শুরু হয়েছে...")
    users = get_db("users") or {}
    success = 0
    for uid in users.keys():
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
            time.sleep(0.05) # Prevent Telegram Flood Limits
        except: pass
        
    bot.send_message(message.chat.id, f"✅ ব্রডকাস্ট সফল! মোট {success} জনকে পাঠানো হয়েছে।", reply_markup=admin_menu())

# ==========================================
# 🛑 BOT POLLING RUNNER
# ==========================================
print("🔥 Firebase Digital Bot is Running Safely...")
bot.infinity_polling(timeout=60, long_polling_timeout=60)
