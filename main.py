import logging
import json
import asyncio
import os
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command

# --- কনফিগারেশন ---
API_TOKEN = '8647369071:AAEg2UdyvQGZGcxykDGkbz5oqsoabOVYOIk'
ADMIN_ID = 8273597769  
MINI_APP_URL = "https://telegramminib.netlify.app/" 
LOG_CHANNEL_ID = -1003698770950 
DB_FILE = 'local_database.json'

storage = MemoryStorage()
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=storage)
router = Router()

logging.basicConfig(level=logging.INFO)

# --- FSM States ---
class AdminStates(StatesGroup):
    waiting_for_srv_name = State()
    waiting_for_srv_price = State()
    waiting_for_srv_file = State()
    adm_target_method = State()
    waiting_for_method_num = State()
    waiting_for_method_logo = State()
    waiting_for_broadcast = State()
    waiting_for_tg_link = State()
    waiting_for_wa_link = State()

# --- ডেটাবেজ ফাংশন ---
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "users": {},
            "settings": {'bkash': '01700000000', 'nagad': '01700000000', 'rocket': '01700000000', 'admin_tg': 'https://t.me/admin', 'admin_wa': 'https://wa.me/8801700000000'},
            "services": {}, "history": {}
        }
        with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(default_data, f, indent=4)
        return default_data
    with open(DB_FILE, 'r', encoding='utf-8') as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4, ensure_ascii=False)

# --- হ্যান্ডলারস ---
@router.message(Command('start'))
async def start_handler(message: types.Message):
    uid = str(message.from_user.id)
    db = load_db()
    if uid not in db["users"]:
        db["users"][uid] = {'balance': 0.0, 'refer_count': 0}
        save_db(db)
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    
    # ইউনিক এবং প্রিমিয়াম ওয়েলকাম ডিজাইন
    welcome_text = (
        f"🌟 <b>স্বাগতম, {message.from_user.full_name}!</b> 🌟\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Secure Surf Zone X</b> - প্রিমিয়াম ডিজিটাল শপ।\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 <b>আপনার ইউনিক রেফারেল লিংক:</b>\n<code>{ref_link}</code>\n\n"
        f"🚀 <i>নিচের বাটনটি ক্লিক করে আমাদের প্রিমিয়াম স্টোরে প্রবেশ করুন এবং সেরা সার্ভিসগুলো উপভোগ করুন।</i>"
    )
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Open Store Mini-App", web_app=types.WebAppInfo(url=MINI_APP_URL))]])
    await message.answer(welcome_text, reply_markup=kb)

@router.message(Command('admin'))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📱 পেমেন্ট নাম্বার", callback_data="adm_numbers"), types.InlineKeyboardButton(text="🖼️ লোগো আপলোড", callback_data="adm_logo")],
            [types.InlineKeyboardButton(text="🛍️ সার্ভিস অ্যাড করুন", callback_data="adm_add_srv")],
            [types.InlineKeyboardButton(text="📞 সাপোর্ট লিংক", callback_data="adm_support")],
            [types.InlineKeyboardButton(text="📢 ব্রডকাস্ট", callback_data="adm_broadcast")]
        ])
        await message.answer("⚙️ <b>Admin Control Panel</b>", reply_markup=kb)

# --- অ্যাডমিন ফিচারস (সব সেটিং এখানে অক্ষুণ্ণ রাখা হয়েছে) ---
@router.callback_query(F.data == "adm_numbers")
async def edit_num(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("মেথড লিখুন (bkash, nagad, rocket):")
    await state.set_state(AdminStates.adm_target_method)

@router.message(AdminStates.adm_target_method)
async def ask_num(message: types.Message, state: FSMContext):
    await state.update_data(method=message.text.lower())
    await message.answer("নতুন নাম্বারটি দিন:")
    await state.set_state(AdminStates.waiting_for_method_num)

@router.message(AdminStates.waiting_for_method_num)
async def save_num(message: types.Message, state: FSMContext):
    data = await state.get_data(); db = load_db()
    db["settings"][data['method']] = message.text
    save_db(db); await message.answer("✅ নাম্বার আপডেট হয়েছে!"); await state.clear()

@router.callback_query(F.data == "adm_logo")
async def ask_logo(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("কোন মেথডের লোগো? (bkash, nagad, rocket):")
    await state.set_state(AdminStates.adm_target_method)

@router.message(AdminStates.adm_target_method, F.text)
async def get_logo_img(message: types.Message, state: FSMContext):
    await state.update_data(method=message.text.lower())
    await message.answer("এখন লোগোটি ছবি হিসেবে পাঠান:")
    await state.set_state(AdminStates.waiting_for_method_logo)

@router.message(AdminStates.waiting_for_method_logo, F.photo)
async def save_logo(message: types.Message, state: FSMContext):
    data = await state.get_data(); db = load_db()
    db["settings"][f"{data['method']}_logo"] = message.photo[-1].file_id
    save_db(db); await message.answer("✅ লোগো আপডেট হয়েছে!"); await state.clear()

@router.callback_query(F.data == "adm_support")
async def edit_support(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("নতুন Telegram লিংক দিন:")
    await state.set_state(AdminStates.waiting_for_tg_link)

@router.message(AdminStates.waiting_for_tg_link)
async def save_tg(message: types.Message, state: FSMContext):
    db = load_db(); db["settings"]["admin_tg"] = message.text
    save_db(db); await message.answer("Telegram আপডেট হয়েছে! এখন WhatsApp লিংক দিন:")
    await state.set_state(AdminStates.waiting_for_wa_link)

@router.message(AdminStates.waiting_for_wa_link)
async def save_wa(message: types.Message, state: FSMContext):
    db = load_db(); db["settings"]["admin_wa"] = message.text
    save_db(db); await message.answer("✅ সাপোর্ট লিংক আপডেট হয়েছে!"); await state.clear()

@router.callback_query(F.data == "adm_broadcast")
async def broadcast_start(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("ব্রডকাস্ট মেসেজটি লিখুন:")
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast)
async def broadcast_send(message: types.Message, state: FSMContext):
    db = load_db(); count = 0
    for uid in db["users"]:
        try: await bot.send_message(int(uid), message.text); count += 1
        except: continue
    await message.answer(f"✅ {count} জনকে মেসেজ পাঠানো হয়েছে!"); await state.clear()

@router.callback_query(F.data == "adm_add_srv")
async def add_srv_step1(call: types.CallbackQuery, state: FSMContext):
    await call.message.answer("সার্ভিসের নাম দিন:")
    await state.set_state(AdminStates.waiting_for_srv_name)

@router.message(AdminStates.waiting_for_srv_name)
async def add_srv_step2(message: types.Message, state: FSMContext):
    await state.update_data(srv_name=message.text)
    await message.answer("সার্ভিসের দাম দিন:")
    await state.set_state(AdminStates.waiting_for_srv_price)

@router.message(AdminStates.waiting_for_srv_price)
async def add_srv_step3(message: types.Message, state: FSMContext):
    await state.update_data(srv_price=message.text)
    await message.answer("ফাইলটি সেন্ড করুন:")
    await state.set_state(AdminStates.waiting_for_srv_file)

@router.message(AdminStates.waiting_for_srv_file, F.document)
async def add_srv_step4(message: types.Message, state: FSMContext):
    data = await state.get_data(); db = load_db()
    srv_id = str(len(db["services"]) + 1)
    db["services"][srv_id] = {"name": data['srv_name'], "price": data['srv_price'], "file_id": message.document.file_id}
    save_db(db); await message.answer("✅ সার্ভিস অ্যাড হয়েছে!"); await state.clear()

dp.include_router(router)

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
