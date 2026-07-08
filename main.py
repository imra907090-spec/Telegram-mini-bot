import logging
import json
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
import firebase_admin
from firebase_admin import credentials, db

# --- কনফিগারেশন ---
API_TOKEN = '8647369071:AAEg2UdyvQGZGcxykDGkbz5oqsoabOVYOIk'
ADMIN_ID = 8273597769  # আপনার টেলিগ্রাম আইডি এখানে দিন
MINI_APP_URL = "https://telegramminib.netlify.app/" # আপনার হোস্ট করা মিনি অ্যাপের ফাইনাল লিংক

# ফায়ারবেস ইনিশিয়াল সেটিংস (সিক্রেট ফাইল ছাড়া সরাসরি কানেকশন)
if not firebase_admin._apps:
    firebase_admin.initialize_app(options={
        'databaseURL': 'https://telegram-mini-bot-5cb21-default-rtdb.asia-southeast1.firebasedatabase.app/'
    })

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)

# aiogram এর ভার্সন ৩ এবং ২ উভয়ের জন্যই ক্র্যাশ-প্রুফ মেমোরি স্টোরেজ ট্রিক
try:
    from aiogram.contrib.fsm_storage.memory import MemoryStorage
    storage = MemoryStorage()
except ModuleNotFoundError:
    from aiogram.fsm.storage.memory import MemoryStorage
    storage = MemoryStorage()

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
    ref = db.reference(f'users/{uid}')
    data = ref.get()
    if not data:
        data = {'balance': 0.0, 'refer_count': 0, 'referred_by': None}
        ref.set(data)
    return data

def get_settings():
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

# --- কিবোর্ডস ---
def main_menu():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🚀 Open Store Mini-App", web_app=types.WebAppInfo(url=MINI_APP_URL)))
    return kb

def admin_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📱 পেমেন্ট নাম্বার ও লোগো পরিবর্তন", callback_data="adm_numbers"),
        types.InlineKeyboardButton("🎁 রেফার বোনাস পরিবর্তন", callback_data="adm_bonus"),
        types.InlineKeyboardButton("🛍️ নতুন সার্ভিস (কোড ফাইল) আপলোড", callback_data="adm_add_service"),
        types.InlineKeyboardButton("📞 সাপোর্ট লিংক পরিবর্তন (TG/WA)", callback_data="adm_support_links"),
        types.InlineKeyboardButton("📢 ব্রডকাস্ট (সবাইকে মেসেজ)", callback_data="adm_broadcast")
    )
    return kb

# --- স্টার্ট মেসেজ ---
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    uid = message.from_user.id
    args = message.get_args()
    
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
    
    await msg.edit_text(
        f"👋 <b>Welcome, {message.from_user.first_name}!</b>\n━━━━━━━━━━━━━━━━━━\n"
        f"🔗 <b>Your Invite Link:</b>\n<code>{ref_link}</code>\n\n"
        f"⚡ <i>নিচের বাটনটি ক্লিক করে আমাদের প্রিমিয়াম সলিড ম্যাট ডার্ক মিনি অ্যাপটি ওপেন করুন:</i>", 
        reply_markup=main_menu()
    )

@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def admin_panel(message: types.Message):
    await message.reply("⚙️ <b>Welcome to Admin Control Panel</b>", reply_markup=admin_menu())

# --- মিনি অ্যাপ (Web App Data) রিসিভার ---
@dp.message_handler(content_types='web_app_data')
async def web_app_data_receive(message: types.Message, state: FSMContext):
    uid = message.from_user.id
    data = json.loads(message.web_app_data.data)
    
    if data['action'] == "deposit":
        await state.update_data(dep_data=data)
        await message.reply(
            f"📥 <b>Deposit Request Initiated!</b>\n━━━━━━━━━━━━━━━━━━\n"
            f"💵 Amount: <b>৳{data['amount']} BDT</b>\n"
            f"📱 Gateway: <b>{data['method'].upper()}</b>\n"
            f"🆔 TxID: <code>{data['txid']}</code>\n"
            f"👤 Sender: <code>{data['sender']}</code>\n\n"
            f"⚠️ পেমেন্ট ভেরিফাই করতে এখনই পেমেন্টের <b>স্ক্রিনশট (Screenshot)</b> টি ছবি আকারে সেন্ড করুন:"
        )
        await AdminStates.waiting_for_ss.set()

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

# --- স্ক্রিনশট প্রসেসিং ---
@dp.message_handler(content_types=['photo'], state=AdminStates.waiting_for_ss)
async def process_ss(message: types.Message, state: FSMContext):
    state_data = await state.get_data()
    dep = state_data['dep_data']
    uid = message.from_user.id
    photo_id = message.photo[-1].file_id
    
    h_ref = db.reference(f'history/{uid}').push()
    h_ref.set({'method': dep['method'], 'amount': dep['amount'], 'txid': dep['txid'], 'status': 'pending'})
    
    await message.reply("⏳ Your payment screenshot is under review by Admin. Status updated to: <b>PENDING</b>.")
    
    akb = types.InlineKeyboardMarkup()
    akb.add(
        types.InlineKeyboardButton("🟢 Approve & Add Cash", callback_data=f"v_app_{uid}_{dep['amount']}_{h_ref.key}"),
        types.InlineKeyboardButton("🔴 Reject Request", callback_data=f"v_rej_{uid}_{h_ref.key}")
    )
    
    await bot.send_photo(
        ADMIN_ID, photo_id,
        caption=f"🚨 <b>New Deposit Alert!</b>\n━━━━━━━━━━━━━━━━━━\n"
                f"👤 User: <code>{uid}</code>\n"
                f"💵 Amount: <b>৳{dep['amount']} BDT</b>\n"
                f"💳 Gateway: <b>{dep['method'].upper()}</b>\n"
                f"🔢 Sender Num: <code>{dep['sender']}</code>\n"
                f"🆔 TxID: <code>{dep['txid']}</code>",
        reply_markup=akb
    )
    await state.finish()

# --- অ্যাডমিন কলব্যাকস ---
@dp.callback_query_handler(lambda c: c.data.startswith('v_') or c.data.startswith('adm_') or c.data.startswith('ch_') or c.data.startswith('logo_') or c.data.startswith('set_'))
async def admin_callbacks(call: types.CallbackQuery, state: FSMContext):
    uid = call.from_user.id
    if uid != ADMIN_ID: return

    if call.data.startswith('v_app_'):
        _, _, target_id, amt, h_key = call.data.split('_')
        u_ref = db.reference(f'users/{target_id}')
        u_data = u_ref.get()
        u_ref.update({'balance': u_data['balance'] + float(amt)})
        db.reference(f'history/{target_id}/{h_key}').update({'status': 'approved'})
        await bot.send_message(target_id, f"✅ Your deposit of ৳{amt} BDT has been Confirmed & Approved!")
        await call.message.edit_caption("🟢 Deposit successfully approved!")
        
    elif call.data.startswith('v_rej_'):
        _, _, target_id, h_key = call.data.split('_')
        db.reference(f'history/{target_id}/{h_key}').update({'status': 'rejected'})
        await bot.send_message(target_id, f"❌ Your deposit request was rejected. Please contact support.")
        await call.message.edit_caption("🔴 Deposit Request Rejected!")

    elif call.data == "adm_numbers":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton("bKash Num", callback_data="ch_bkash"),
            types.InlineKeyboardButton("bKash Logo", callback_data="logo_bkash"),
            types.InlineKeyboardButton("Nagad Num", callback_data="ch_nagad"),
            types.InlineKeyboardButton("Nagad Logo", callback_data="logo_nagad"),
            types.InlineKeyboardButton("Rocket Num", callback_data="ch_rocket"),
            types.InlineKeyboardButton("Rocket Logo", callback_data="logo_rocket"),
            types.InlineKeyboardButton("Binance Addr", callback_data="ch_binance"),
            types.InlineKeyboardButton("Binance Logo", callback_data="logo_binance")
        )
        await call.message.edit_text("আপনি কোনটি পরিবর্তন করতে চান সিলেক্ট করুন:", reply_markup=kb)

    elif call.data.startswith("ch_"):
        gateway = call.data.split("_")[1]
        await state.update_data(target_gateway=gateway)
        await call.message.answer(f"📝 নতুন {gateway.upper()} নাম্বারটি টাইপ করে পাঠান:")
        await AdminStates.waiting_for_num.set()

    elif call.data.startswith("logo_"):
        gateway = call.data.split("_")[1]
        await state.update_data(target_logo_gateway=gateway)
        await call.message.answer(f"🖼️ নতুন {gateway.upper()} লোগোর ছবিটি ইমেজ আকারে সেন্ড করুন:")
        await AdminStates.waiting_for_gateway_logo.set()

    elif call.data == "adm_support_links":
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("Telegram Profile Link", callback_data="set_tg"),
            types.InlineKeyboardButton("WhatsApp Contact Link", callback_data="set_wa")
        )
        await call.message.edit_text("কোন লাইভ সাপোর্ট লিংকটি বদলাবেন?", reply_markup=kb)

    elif call.data == "set_tg":
        await call.message.answer("🔗 আপনার নতুন Telegram কন্ট্যাক্ট লিংকটি দিন:")
        await AdminStates.waiting_for_tg_link.set()
    elif call.data == "set_wa":
        await call.message.answer("🔗 আপনার নতুন WhatsApp API লিংকটি দিন:")
        await AdminStates.waiting_for_wa_link.set()

    elif call.data == "adm_add_service":
        await call.message.answer("🛍️ কোডিং সার্ভিসটির নাম বা টাইটেল (Title) লিখুন:")
        await AdminStates.waiting_for_srv_name.set()

    elif call.data == "adm_broadcast":
        await call.message.answer("📢 বটের সকল ইউজারের কাছে পাঠানোর জন্য নোটিশটি লিখুন:")
        await AdminStates.waiting_for_broadcast.set()

# --- FSM ডাটা হ্যান্ডলারস ---
@dp.message_handler(state=AdminStates.waiting_for_gateway_logo, content_types=['photo'], user_id=ADMIN_ID)
async def save_logo(message: types.Message, state: FSMContext):
    s_data = await state.get_data()
    gw = s_data['target_logo_gateway']
    file_info = await bot.get_file(message.photo[-1].file_id)
    live_url = f"https://api.telegram.org/file/bot{API_TOKEN}/{file_info.file_path}"
    db.reference(f'settings/{gw}_logo').set(live_url)
    await message.reply(f"✅ সফলভাবে {gw.upper()} অ্যাপের লাইভ লোগো আপডেট করা হয়েছে!")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_srv_name, user_id=ADMIN_ID)
async def srv_name(message: types.Message, state: FSMContext):
    await state.update_data(srv_name=message.text)
    await message.reply("৳ এই ফাইলের মূল্য (Price In BDT) কত হবে? শুধুমাত্র সংখ্যায় লিখুন:")
    await AdminStates.waiting_for_srv_price.set()

@dp.message_handler(state=AdminStates.waiting_for_srv_price, user_id=ADMIN_ID)
async def srv_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit(): return await message.reply("❌ শুধুমাত্র সংখ্যায় প্রাইস লিখুন:")
    await state.update_data(srv_price=message.text)
    await message.reply("📥 এবার মূল কোডিং ফাইল বা স্ক্রিপ্টটি (Document/Zip/Txt) এখানে ফাইল আকারে আপলোড করুন:")
    await AdminStates.waiting_for_srv_file.set()

@dp.message_handler(state=AdminStates.waiting_for_srv_file, content_types=['document'], user_id=ADMIN_ID)
async def srv_file(message: types.Message, state: FSMContext):
    s_data = await state.get_data()
    db.reference('services').push().set({
        'name': s_data['srv_name'], 'price': s_data['srv_price'], 'file_id': message.document.file_id
    })
    await message.reply(f"✅ <b>সার্ভিস স্টোরে ফাইল সাকসেসফুলি আপলোড হয়েছে!</b>\n🛍️ Name: {s_data['srv_name']}\n💸 Price: ৳{s_data['srv_price']} BDT")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_num, user_id=ADMIN_ID)
async def save_number(message: types.Message, state: FSMContext):
    s_data = await state.get_data()
    gw = s_data['target_gateway']
    db.reference(f'settings/{gw}').set(message.text)
    await message.reply(f"✅ {gw.upper()} পেমেন্ট নাম্বার লাইভ আপডেট করা হয়েছে।")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_tg_link, user_id=ADMIN_ID)
async def save_tg_link(message: types.Message, state: FSMContext):
    db.reference('settings/admin_tg').set(message.text)
    await message.reply("✅ Telegram Support Link updated instantly.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_wa_link, user_id=ADMIN_ID)
async def save_wa_link(message: types.Message, state: FSMContext):
    db.reference('settings/admin_wa').set(message.text)
    await message.reply("✅ WhatsApp Support Link updated instantly.")
    await state.finish()

@dp.message_handler(state=AdminStates.waiting_for_broadcast, user_id=ADMIN_ID)
async def broadcast_send(message: types.Message, state: FSMContext):
    users = db.reference('users').get() or {}
    count = 0
    for u_id in users.keys():
        try:
            await bot.send_message(u_id, message.text)
            count += 1
        except: pass
    await message.reply(f"📢 ব্রডকাস্ট সম্পন্ন হয়েছে! মোট {count} জন ইউজারের ইনবক্সে মেসেজ পাঠানো হয়েছে।")
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
