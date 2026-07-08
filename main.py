import logging
import json
import asyncio
import os

# aiogram v3 এর লেটেস্ট ভার্সন আর্কিটেকচার ইমপোর্ট
try:
    from aiogram import Bot, Dispatcher, types
    from aiogram.fsm.storage.memory import MemoryStorage
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.state import State, StatesGroup
    from aiogram.client.default import DefaultBotProperties
    storage = MemoryStorage()
    V3_MODE = True
except ModuleNotFoundError:
    from aiogram import Bot, Dispatcher, types
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    from aiogram.dispatcher import FSMContext
    from aiogram.dispatcher.filters.state import State, StatesGroup
    from aiogram.utils import executor
    storage = MemoryStorage()
    V3_MODE = False

# --- কনফিগারেশন ---
API_TOKEN = '8647369071:AAEg2UdyvQGZGcxykDGkbz5oqsoabOVYOIk'
ADMIN_ID = 8273597769  
MINI_APP_URL = "https://telegramminib.netlify.app/" 

# 📢 আপনার টেলিগ্রাম লগ চ্যানেলের ID এখানে বসান (অবশ্যই -100 দিয়ে শুরু হতে হবে)
LOG_CHANNEL_ID = -1003698770950 

DB_FILE = 'local_database.json'

logging.basicConfig(level=logging.INFO)

# --- লোকাল JSON ডেটাবেজ লজিক ---
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "users": {},
            "settings": {
                'bkash': '017XXXXXXXX', 'nagad': '019XXXXXXXX', 
                'rocket': '015XXXXXXXX', 'binance': 'TRC20_WALLET_HERE',
                'bkash_logo': '', 'nagad_logo': '', 'rocket_logo': '', 'binance_logo': '',
                'ref_bonus': 1.50, 'min_wd': 50.0,
                'admin_tg': 'https://t.me/your_admin_username',
                'admin_wa': 'https://wa.me/88017XXXXXXXX'
            },
            "services": {},
            "history": {}
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
        return default_data
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_user(uid):
    db_data = load_db()
    uid_str = str(uid)
    if uid_str not in db_data["users"]:
        db_data["users"][uid_str] = {'balance': 0.0, 'refer_count': 0, 'referred_by': None}
        save_db(db_data)
    return db_data["users"][uid_str]

def get_settings():
    db_data = load_db()
    return db_data["settings"]

# Bot এবং Dispatcher ইনিশিয়ালাইজেশন
if V3_MODE:
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)
else:
    bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)

# --- FSM States ---
class AdminStates(StatesGroup):
    waiting_for_num = State()
    waiting_for_bonus = State()
    waiting_for_broadcast = State()
    waiting_for_ss = State()

# --- কিবোর্ডস ---
def main_menu():
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚀 Open Store Mini-App", web_app=types.WebAppInfo(url=MINI_APP_URL))]
    ]) if V3_MODE else types.InlineKeyboardMarkup()
    if not V3_MODE:
        kb.add(types.InlineKeyboardButton("🚀 Open Store Mini-App", web_app=types.WebAppInfo(url=MINI_APP_URL)))
    return kb

def admin_menu():
    if V3_MODE:
        return types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📱 পেমেন্ট নাম্বার ও লোগো পরিবর্তন", callback_data="adm_numbers")],
            [types.InlineKeyboardButton(text="🎁 রেফার বোনাস পরিবর্তন", callback_data="adm_bonus")],
            [types.InlineKeyboardButton(text="📢 ব্রডকাস্ট (সবাইকে মেসেজ)", callback_data="adm_broadcast")]
        ])
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📱 পেমেন্ট নাম্বার ও লোগো পরিবর্তন", callback_data="adm_numbers"),
            types.InlineKeyboardButton("🎁 রেফার বোনাস পরিবর্তন", callback_data="adm_bonus"),
            types.InlineKeyboardButton("📢 ব্রডকাস্ট (সবাইকে মেসেজ)", callback_data="adm_broadcast")
        )
        return kb

# --- কোর লজিক হ্যান্ডলারস ---
async def start_logic(message: types.Message):
    uid = message.from_user.id
    text = message.text or ""
    args = text.split()[1] if len(text.split()) > 1 else ""
    
    db_data = load_db()
    uid_str = str(uid)
    
    is_new_user = uid_str not in db_data["users"]
    
    if is_new_user and args and args.isdigit() and int(args) != uid:
        get_user(uid)
        db_data = load_db()
        db_data["users"][uid_str]['referred_by'] = int(args)
        
        sett = get_settings()
        r_uid_str = str(args)
        
        if r_uid_str in db_data["users"]:
            db_data["users"][r_uid_str]['balance'] += sett['ref_bonus']
            db_data["users"][r_uid_str]['refer_count'] += 1
            save_db(db_data)
            
            try: await bot.send_message(int(args), f"🎉 একজন আপনার লিংকে জয়েন করেছে! আপনি পেয়েছেন ৳{sett['ref_bonus']}")
            except: pass
            
            try:
                await bot.send_message(
                    LOG_CHANNEL_ID,
                    f"🔗 <b>New Referral Alert!</b>\n━━━━━━━━━━━━━━━━━━\n"
                    f"👤 New User: <code>{uid}</code> ({message.from_user.first_name})\n"
                    f"🙋‍♂️ Referred By: <code>{args}</code>\n"
                    f"🎁 Bonus Added: ৳{sett['ref_bonus']} BDT"
                )
            except: pass
    else:
        get_user(uid)
        
    if is_new_user:
        try:
            await bot.send_message(
                LOG_CHANNEL_ID,
                f"👤 <b>New User Registered!</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"🆔 ID: <code>{uid}</code>\n"
                f"📛 Name: {message.from_user.full_name}\n"
                f"Username: @{message.from_user.username or 'None'}"
            )
        except: pass
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    
    msg = await message.reply("🔄 <b>Loading Secure Surf Zone X...</b>")
    await asyncio.sleep(0.4)
    
    welcome_text = (
        f"👋 <b>Welcome, {message.from_user.first_name}!</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>\n\n"
        f"⚡ <i>নিচের বাটনটি ক্লিক করে আমাদের প্রিমিয়াম সলিড ম্যাট ডার্ক মিনি অ্যাপটি ওপেন করুন:</i>"
    )
    
    if V3_MODE:
        await bot.edit_message_text(chat_id=message.chat.id, message_id=msg.message_id, text=welcome_text, reply_markup=main_menu())
    else:
        await msg.edit_text(welcome_text, reply_markup=main_menu())

async def admin_logic(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.reply("⚙️ <b>Welcome to Admin Control Panel</b>", reply_markup=admin_menu())

# --- মিনি অ্যাপ ডাটা প্রসেসিং লজিক ---
async def web_app_logic(message: types.Message, state: FSMContext = None):
    data = json.loads(message.web_app_data.data)
    uid = message.from_user.id
    uid_str = str(uid)
    db_data = load_db()
    
    # ১. ডিপোজিট রিকোয়েস্ট হ্যান্ডলার
    if data['action'] == "deposit":
        if state: await state.update_data(dep_data=data)
        
        # লোকাল ডাটায় হিস্ট্রি যুক্ত করা
        txid = data['txid']
        if "history" not in db_data:
            db_data["history"] = {}
        
        db_data["history"][txid] = {
            "uid": uid,
            "method": data['method'],
            "amount": data['amount'],
            "txid": txid,
            "sender": data['sender'],
            "status": "pending"
        }
        save_db(db_data)
        
        deposit_text = (
            f"📥 <b>Deposit Request Initiated!</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"💵 Amount: <b>৳{data['amount']} BDT</b>\n"
            f"📱 Gateway: <b>{data['method'].upper()}</b>\n"
            f"🆔 TxID: <code>{txid}</code>\n"
            f"👤 Sender: <code>{data['sender']}</code>\n\n"
            f"⚠️ পেমেন্ট ভেরিফাই করতে এখনই পেমেন্টের <b>স্ক্রিনশট (Screenshot)</b> টি ছবি আকারে সেন্ড করুন:"
        )
        await message.reply(deposit_text)
        
        try:
            await bot.send_message(
                LOG_CHANNEL_ID,
                f"💰 <b>New Deposit Request!</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 User ID: <code>{uid}</code>\n"
                f"💵 Amount: ৳{data['amount']} BDT\n"
                f"📱 Method: {data['method'].upper()}\n"
                f"🆔 TxID: <code>{txid}</code>\n"
                f"📞 Sender Number: <code>{data['sender']}</code>\n"
                f"🟩 Status: Pending"
            )
        except: pass

        if state and not V3_MODE: await AdminStates.waiting_for_ss.set()
        elif state and V3_MODE: await state.set_state(AdminStates.waiting_for_ss)

    # ২. মিনি অ্যাপে সার্ভিস ডাটা পাঠানো
    elif data['action'] == "get_services":
        services_list = db_data.get("services", {})
        # মিনি অ্যাপের window.postMessage ক্যাচ করার লজিক (টেলিগ্রাম এর নিজস্ব বটের মাধ্যমে রিপ্লাই)
        await message.reply(f"🛍️ Services Store Synchronized. Available active products: {len(services_list)}")
        
    # ৩. মিনি অ্যাপে ডিপোজিট হিস্ট্রি পাঠানো
    elif data['action'] == "get_history":
        user_history = {k: v for k, v in db_data.get("history", {}).items() if str(v.get('uid')) == uid_str}
        await message.reply(f"📑 Deposit Logs Synchronized. Total transactions: {len(user_history)}")

    # ৪. সার্ভিস বা স্ক্রিপ্ট কেনাকাটা হ্যান্ডলার
    elif data['action'] == "buy_service":
        srv_id = data['service_id']
        srv = db_data.get("services", {}).get(srv_id)
        user_info = get_user(uid)
        
        if srv:
            price = float(srv['price'])
            current_bal = float(user_info['balance'])
            if current_bal >= price:
                # ব্যালেন্স মাইনাস করা
                db_data["users"][uid_str]['balance'] = current_bal - price
                save_db(db_data)
                
                file_id = srv['file_id']
                await bot.send_document(uid, file_id, caption=f"🎉 <b>Purchase Successful!</b>\n🛍️ Product: {srv['name']}\n💸 Deducted: ৳{price} BDT")
            else:
                await message.reply("❌ <b>Insufficient Balance!</b> Please deposit money first.")
        else:
            await message.reply("❌ Service not found or expired.")

# --- ইভেন্ট রাউটিং ও পলিস ইন্টিগ্রেশন ---
if V3_MODE:
    from aiogram import Router, F
    from aiogram.filters import Command
    router = Router()
    @router.message(Command('start'))
    async def start_v3(message: types.Message): await start_logic(message)
    @router.message(Command('admin'))
    async def admin_v3(message: types.Message): await admin_logic(message)
    @router.message(F.content_type == types.ContentType.WEB_APP_DATA)
    async def web_v3(message: types.Message, state: FSMContext): await web_app_logic(message, state)
    dp.include_router(router)
else:
    dp.register_message_handler(start_logic, commands=['start'])
    dp.register_message_handler(admin_logic, commands=['admin'])
    dp.register_message_handler(web_app_logic, content_types='web_app_data')

# --- এক্সিকিউটর স্টার্ট ---
if __name__ == '__main__':
    load_db()
    if V3_MODE:
        async def main():
            await dp.start_polling(bot)
        asyncio.run(main())
    else:
        from aiogram.utils import executor
        executor.start_polling(dp, skip_updates=True)
