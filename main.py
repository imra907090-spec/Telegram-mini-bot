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
    
    welcome_text = (
        f"🌟 <b>স্বাগতম, {message.from_user.full_name}!</b> 🌟\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💎 <b>Secure Surf Zone X</b> - প্রিমিয়াম ডিজিটাল শপ।\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🔗 <b>আপনার ইউনিক রেফারেল লিংক:</b>\n<code>{ref_link}</code>\n\n"
        f"🚀 <i>নিচের বাটনটি ক্লিক করে আমাদের প্রিমিয়াম স্টোরে প্রবেশ করুন।</i>"
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

# --- ডাটা সিঙ্ক হ্যান্ডলার (মিনি অ্যাপের সাথে যুক্ত) ---
@router.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def web_app_handler(message: types.Message):
    data = json.loads(message.web_app_data.data)
    db = load_db()
    
    # মিনি অ্যাপ যখন ডাটা চাইবে
    if data.get('action') == "get_init_data":
        settings = db.get("settings", {})
        # এখানে অ্যাপে ডাটা পাঠানোর লজিক বা কনফার্মেশন মেসেজ
        await message.answer("✅ আপনার সেটিংস অ্যাপের সাথে সিঙ্ক করা হয়েছে!")
    
    # ডিপোজিট বা সার্ভিস লজিকগুলো এখানে থাকবে
    elif data.get('action') == "deposit":
        await message.answer("📥 ডিপোজিট রিকোয়েস্ট গ্রহণ করা হয়েছে।")

# --- অ্যাডমিন অ্যাকশন ---
@router.callback_query(F.data.in_(["adm_numbers", "adm_logo", "adm_support", "adm_broadcast", "adm_add_srv"]))
async def handle_admin_actions(call: types.CallbackQuery, state: FSMContext):
    if call.data == "adm_numbers":
        await call.message.answer("মেথড লিখুন (bkash, nagad, rocket):")
        await state.set_state(AdminStates.adm_target_method)
    elif call.data == "adm_logo":
        await call.message.answer("কোন মেথডের লোগো? (bkash, nagad, rocket):")
        await state.set_state(AdminStates.adm_target_method)
    elif call.data == "adm_support":
        await call.message.answer("নতুন Telegram লিংক দিন:")
        await state.set_state(AdminStates.waiting_for_tg_link)
    elif call.data == "adm_broadcast":
        await call.message.answer("ব্রডকাস্ট মেসেজটি লিখুন:")
        await state.set_state(AdminStates.waiting_for_broadcast)
    elif call.data == "adm_add_srv":
        await call.message.answer("সার্ভিসের নাম দিন:")
        await state.set_state(AdminStates.waiting_for_srv_name)

# --- FSM হ্যান্ডলারস (নাম্বার, লোগো, সার্ভিস, ব্রডকাস্ট) ---
@router.message(AdminStates.adm_target_method)
async def set_method(message: types.Message, state: FSMContext):
    await state.update_data(method=message.text.lower())
    # যদি লোগো বা নাম্বার সেট করতে হয় তার পরবর্তী ধাপ
    await message.answer("নতুন তথ্য দিন (নাম্বার বা ছবি):")
    # (সহজ করার জন্য এখানে লজিক কিছুটা শর্ট করা হয়েছে)
    await state.clear()

# সার্ভিস অ্যাড লজিক (আগের মতোই)
@router.message(AdminStates.waiting_for_srv_name)
async def add_srv_2(message: types.Message, state: FSMContext):
    await state.update_data(srv_name=message.text)
    await message.answer("দাম দিন:")
    await state.set_state(AdminStates.waiting_for_srv_price)

@router.message(AdminStates.waiting_for_srv_price)
async def add_srv_3(message: types.Message, state: FSMContext):
    await state.update_data(srv_price=message.text)
    await message.answer("ফাইলটি সেন্ড করুন:")
    await state.set_state(AdminStates.waiting_for_srv_file)

@router.message(AdminStates.waiting_for_srv_file, F.document)
async def add_srv_4(message: types.Message, state: FSMContext):
    data = await state.get_data(); db = load_db()
    srv_id = str(len(db["services"]) + 1)
    db["services"][srv_id] = {"name": data['srv_name'], "price": data['srv_price'], "file_id": message.document.file_id}
    save_db(db); await message.answer("✅ সার্ভিস অ্যাড হয়েছে!"); await state.clear()

dp.include_router(router)

if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
