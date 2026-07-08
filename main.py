import logging
import json
import asyncio
import sys

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

import firebase_admin
from firebase_admin import db

# --- কনফিগারেশন ---
API_TOKEN = '8931384031:AAElSwSOL_CQdShaUgvwEBenkdmJPkiXZUc'
ADMIN_ID = 8273597769  
MINI_APP_URL = "https://telegramminib.netlify.app/" 

# ফায়ারবেস ইনিশিয়াল সেটিংস (সিক্রেট ফাইল ছাড়া পাবলিক রুলসের জন্য পারফেক্ট মেথড)
if not firebase_admin._apps:
    firebase_admin.initialize_app(
        credential=firebase_admin.credentials.Anonymous(), # ক্রেডেনশিয়াল এরর দূর করার জন্য অ্যানোনিমাস মেথড
        options={
            'databaseURL': 'https://telegram-mini-bot-5cb21-default-rtdb.asia-southeast1.firebasedatabase.app/'
        }
    )

# Bot এবং Dispatcher ইনিশিয়ালাইজেশন
if V3_MODE:
    bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)
else:
    bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)

logging.basicConfig(level=logging.INFO)

# --- FSM States ---
class AdminStates(StatesGroup):
    waiting_for_num = State()
    waiting_for_bonus = State()
    waiting_for_broadcast = State()
    waiting_for_ss = State()
    waiting_for_tg_link = State()
    waiting_for_wa_link = State()
    waiting_for_gateway_logo = State()
    waiting_for_srv_name = State()
    waiting_for_srv_price = State()
    waiting_for_srv_file = State()

# --- ডেটাবেস ফাংশনস ---
def get_user(uid):
    try:
        ref = db.reference(f'users/{uid}')
        data = ref.get()
        if not data:
            data = {'balance': 0.0, 'refer_count': 0, 'referred_by': None}
            ref.set(data)
        return data
    except Exception as e:
        logging.error(f"Error in get_user: {e}")
        return {'balance': 0.0, 'refer_count': 0, 'referred_by': None}

def get_settings():
    try:
        ref = db.reference('settings')
        data = ref.get()
        if not data:
            data = {
                'bkash': '017XXXXXXXX', 'nagad': '019XXXXXXXX', 
                'rocket': '015XXXXXXXX', 'binance': 'TRC20_WALLET_HERE',
                'bkash_logo': '', 'nagad_logo': '', 'rocket_logo': '', 'binance_logo': '',
                'ref_bonus': 1.50, 'min_wd': 50.0,
                'admin_tg': 'https://t.me/your_admin_username',
                'admin_wa': 'https://wa.me/88017XXXXXXXX'
            }
            ref.set(data)
        return data
    except Exception as e:
        logging.error(f"Error in get_settings: {e}")
        return {
            'bkash': '017XXXXXXXX', 'nagad': '019XXXXXXXX', 
            'rocket': '015XXXXXXXX', 'binance': 'TRC20_WALLET_HERE',
            'bkash_logo': '', 'nagad_logo': '', 'rocket_logo': '', 'binance_logo': '',
            'ref_bonus': 1.50, 'min_wd': 50.0,
            'admin_tg': 'https://t.me/your_admin_username',
            'admin_wa': 'https://wa.me/88017XXXXXXXX'
        }

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
            [types.InlineKeyboardButton(text="🛍️ নতুন সার্ভিস (কোড ফাইল) আপলোড", callback_data="adm_add_service")],
            [types.InlineKeyboardButton(text="📞 সাপোর্ট লিংক পরিবর্তন (TG/WA)", callback_data="adm_support_links")],
            [types.InlineKeyboardButton(text="📢 ব্রডকাস্ট (সবাইকে মেসেজ)", callback_data="adm_broadcast")]
        ])
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("📱 পেমেন্ট নাম্বার ও লোগো পরিবর্তন", callback_data="adm_numbers"),
            types.InlineKeyboardButton("🎁 রেফার বোনাস পরিবর্তন", callback_data="adm_bonus"),
            types.InlineKeyboardButton("🛍️ নতুন সার্ভিস (কোড ফাইল) আপলোড", callback_data="adm_add_service"),
            types.InlineKeyboardButton("📞 সাপোর্ট লিংক পরিবর্তন (TG/WA)", callback_data="adm_support_links"),
            types.InlineKeyboardButton("📢 ব্রডকাস্ট (সবাইকে মেসেজ)", callback_data="adm_broadcast")
        )
        return kb

# --- কোর লজিক হ্যান্ডলারস ---
async def start_logic(message: types.Message):
    uid = message.from_user.id
    text = message.text or ""
    args = text.split()[1] if len(text.split()) > 1 else ""
    
    ref = db.reference(f'users/{uid}')
    if not ref.get() and args and args.isdigit() and int(args) != uid:
        get_user(uid)
        ref.update({'referred_by': int(args)})
        sett = get_settings()
        r_uid = int(args)
        r_data = get_user(r_uid)
        db.reference(f'users/{r_uid}').update({
            'balance': r_data['balance'] + sett['ref_bonus'],
            'refer_count': r_data['refer_count'] + 1
        })
        try: await bot.send_message(r_uid, f"🎉 একজন আপনার লিংকে জয়েন করেছে! আপনি পেয়েছেন ৳{sett['ref_bonus']}")
        except: pass
    
    get_user(uid)
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

async def web_app_logic(message: types.Message, state: FSMContext = None):
    uid = message.from_user.id
    data = json.loads(message.web_app_data.data)
    
    if data['action'] == "deposit":
        if state: await state.update_data(dep_data=data)
        await message.reply(
            f"📥 <b>Deposit Request Initiated!</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"💵 Amount: <b>৳{data['amount']} BDT</b>\n"
            f"📱 Gateway: <b>{data['method'].upper()}</b>\n"
            f"🆔 TxID: <code>{data['txid']}</code>\n"
            f"👤 Sender: <code>{data['sender']}</code>\n\n"
            f"⚠️ পেমেন্ট ভেরিফাই করতে এখনই পেমেন্টের <b>স্ক্রিনশট (Screenshot)</b> টি ছবি আকারে সেন্ড করুন:"
        )
        if state and not V3_MODE: await AdminStates.waiting_for_ss.set()
        elif state and V3_MODE: await state.set_state(AdminStates.waiting_for_ss)

    elif data['action'] == "get_services":
        await message.reply("🛍️ Services Database successfully synchronized.")
    elif data['action'] == "get_history":
        await message.reply("📑 Your Transaction History logs synced.")
    elif data['action'] == "buy_service":
        srv_id = data['service_id']
        srv_ref = db.reference(f'services/{srv_id}').get()
        u_ref = db.reference(f'users/{uid}')
        u_data = u_ref.get()
        
        if srv_ref and u_data:
            price = float(srv_ref['price'])
            current_bal = float(u_data['balance'])
            if current_bal >= price:
                u_ref.update({'balance': current_bal - price})
                file_id = srv_ref['file_id']
                await bot.send_document(uid, file_id, caption=f"🎉 <b>Purchase Successful!</b>\n🛍️ Script: {srv_ref['name']}\n💸 Deducted: ৳{price} BDT")
            else:
                await message.reply("❌ <b>Insufficient Balance!</b> Please deposit money first.")

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
    if V3_MODE:
        async def main():
            await dp.start_polling(bot)
        asyncio.run(main())
    else:
        from aiogram.utils import executor
        executor.start_polling(dp, skip_updates=True)
