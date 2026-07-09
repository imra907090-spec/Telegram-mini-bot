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
    waiting_for_num = State()
    waiting_for_bonus = State()
    waiting_for_broadcast = State()
    waiting_for_ss = State()
    waiting_for_srv_name = State()
    waiting_for_srv_price = State()
    waiting_for_srv_file = State()
    waiting_for_tg_link = State()
    waiting_for_wa_link = State()

# --- ডেটাবেজ ফাংশন (সেটিংস ঠিক রেখে) ---
def load_db():
    if not os.path.exists(DB_FILE):
        default_data = {
            "users": {},
            "settings": {'bkash': '01700000000', 'nagad': '01700000000', 'rocket': '01700000000', 'ref_bonus': 1.5, 'admin_tg': 'https://t.me/admin', 'admin_wa': 'https://wa.me/8801700000000'},
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
    db_data = load_db()
    if uid not in db_data["users"]:
        db_data["users"][uid] = {'balance': 0.0, 'refer_count': 0}
        save_db(db_data)
    
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start={uid}"
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Open Store", web_app=types.WebAppInfo(url=MINI_APP_URL))]])
    await message.answer(f"👋 স্বাগতম! আপনার রেফার লিংক:\n<code>{ref_link}</code>", reply_markup=kb)

@router.message(Command('admin'))
async def admin_panel(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📱 পেমেন্ট নাম্বার পরিবর্তন", callback_data="adm_numbers")],
            [types.InlineKeyboardButton(text="🛍️ সার্ভিস অ্যাড করুন", callback_data="adm_add_srv")],
            [types.InlineKeyboardButton(text="📞 সাপোর্ট লিংক পরিবর্তন", callback_data="adm_support")],
            [types.InlineKeyboardButton(text="📢 ব্রডকাস্ট", callback_data="adm_broadcast")]
        ])
        await message.answer("⚙️ Admin Panel:", reply_markup=kb)

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
    await message.answer("সার্ভিসের ফাইলটি সেন্ড করুন:")
    await state.set_state(AdminStates.waiting_for_srv_file)

@router.message(AdminStates.waiting_for_srv_file, F.document)
async def add_srv_step4(message: types.Message, state: FSMContext):
    data = await state.get_data()
    db_data = load_db()
    srv_id = str(len(db_data["services"]) + 1)
    db_data["services"][srv_id] = {"name": data['srv_name'], "price": data['srv_price'], "file_id": message.document.file_id}
    save_db(db_data)
    await message.answer("✅ সার্ভিস সফলভাবে যোগ হয়েছে!")
    await state.clear()

# (এখানে আপনার অন্যান্য লজিক ও WebApp ডাটা হ্যান্ডলারটি আগের মতো যোগ করে নিন)

dp.include_router(router)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
