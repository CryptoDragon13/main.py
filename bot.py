import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

import config
from config import (
    BOT_TOKEN, COIN_NAME, COIN_SYMBOL, BOT_USERNAME, TASKS,
    ADMIN_IDS, REFERRAL_REWARD, USE_WEBHOOK,
    WEBHOOK_PATH, WEBHOOK_URL, WEBAPP_HOST, WEBAPP_PORT,
)
import db
import keyboards as kb

logging.basicConfig(level=logging.INFO)

if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
    raise RuntimeError(
        "لازم تحط توكن البوت الحقيقي! عدّل BOT_TOKEN في .env أو في متغيرات "
        "البيئة الخاصة بالاستضافة."
    )

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------------------- أدوات مساعدة ----------------------

def ensure_user(message: Message, referred_by: int = None):
    db.create_user_if_not_exists(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        referred_by=referred_by,
    )


async def check_channel_membership(user_id: int, channel_username: str) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except TelegramBadRequest:
        return False


def profile_text(user_row) -> str:
    pending = db.compute_pending(user_row)
    return (
        f"👤 <b>{user_row['first_name']}</b>\n"
        f"Lvl {user_row['level']}\n\n"
        f"💰 الرصيد: <b>{round(user_row['pool_balance'], 4)} {COIN_SYMBOL}</b>\n"
        f"🎁 رصيد الإحالات (لشراء الأجهزة فقط): <b>{round(user_row['referral_balance'], 4)} {COIN_SYMBOL}</b>\n"
        f"⚡ السرعة الحالية: {user_row['speed']} {COIN_SYMBOL}/ساعة\n\n"
        f"📈 المتراكم دلوقتي: {pending} {COIN_SYMBOL} (اضغط CLAIM عشان تضيفه)"
    )


# ---------------------- /start ----------------------

@dp.message(CommandStart())
async def cmd_start(message: Message):
    args = message.text.split(maxsplit=1)
    referred_by = None
    if len(args) > 1 and args[1].isdigit():
        candidate = int(args[1])
        if candidate != message.from_user.id:
            referred_by = candidate

    is_new = db.create_user_if_not_exists(
        user_id=message.from_user.id,
        username=message.from_user.username or "",
        first_name=message.from_user.first_name or "",
        referred_by=referred_by,
    )

    welcome = (
        f"👋 أهلاً بيك في {COIN_NAME} Miner!\n\n"
        f"⛏ تعدين {COIN_SYMBOL} داخل اللعبة (100% مجاني، مفيش أي دفع حقيقي).\n"
        f"⚡ ارفع مستوى جهازك عشان تزود سرعة التعدين.\n"
        f"👥 ادعُ أصحابك واكسب مكافآت إضافية بعد ما ينشطوا فعليًا.\n\n"
        f"استخدم القائمة تحت للتنقل."
    )
    await message.answer(welcome, reply_markup=kb.main_menu_kb())


# ---------------------- Mine ----------------------

@dp.message(F.text == "⛏ Mine")
async def show_mine(message: Message):
    ensure_user(message)
    user = db.get_user(message.from_user.id)
    pending = db.compute_pending(user)
    text = (
        f"⛏ <b>Mining</b>\n\n"
        f"الرصيد الحالي: {round(user['pool_balance'], 4)} {COIN_SYMBOL}\n"
        f"السرعة: {user['speed']} {COIN_SYMBOL}/ساعة\n"
        f"المتراكم لسه محتاج Claim: <b>{pending} {COIN_SYMBOL}</b>"
    )
    await message.answer(text, reply_markup=kb.mine_kb())


@dp.callback_query(F.data == "claim")
async def cb_claim(callback: CallbackQuery):
    added = db.claim(callback.from_user.id)
    db.try_activate_referral(callback.from_user.id)
    user = db.get_user(callback.from_user.id)
    await callback.answer(f"تم إضافة {added} {COIN_SYMBOL} ✅", show_alert=True)
    text = (
        f"⛏ <b>Mining</b>\n\n"
        f"الرصيد الحالي: {round(user['pool_balance'], 4)} {COIN_SYMBOL}\n"
        f"السرعة: {user['speed']} {COIN_SYMBOL}/ساعة\n"
        f"المتراكم لسه محتاج Claim: 0 {COIN_SYMBOL}"
    )
    try:
        await callback.message.edit_text(text, reply_markup=kb.mine_kb())
    except TelegramBadRequest:
        pass


# ---------------------- Miners ----------------------

@dp.message(F.text == "⚡ Miners")
async def show_miners(message: Message):
    ensure_user(message)
    user = db.get_user(message.from_user.id)
    await message.answer(
        "⚡ <b>أجهزة التعدين</b>\nارفع مستواك عشان تزود سرعة التعدين:",
        reply_markup=kb.miners_kb(user["level"]),
    )


@dp.callback_query(F.data == "upgrade_miner")
async def cb_upgrade(callback: CallbackQuery):
    ok, msg = db.upgrade_miner(callback.from_user.id)
    await callback.answer(msg, show_alert=True)
    user = db.get_user(callback.from_user.id)
    try:
        await callback.message.edit_reply_markup(reply_markup=kb.miners_kb(user["level"]))
    except TelegramBadRequest:
        pass


@dp.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


# ---------------------- Tasks ----------------------

@dp.message(F.text == "📝 Tasks")
async def show_tasks(message: Message):
    ensure_user(message)
    statuses = {}
    for task in TASKS:
        row = db.get_task_status(message.from_user.id, task["id"])
        statuses[task["id"]] = row["status"] if row else None
    await message.answer(
        "📝 <b>المهام</b>\nكل مهمة بتضيف رصيد فورًا لمحفظتك جوا اللعبة:",
        reply_markup=kb.tasks_kb(message.from_user.id, statuses),
    )


@dp.callback_query(F.data.startswith("task_"))
async def cb_task(callback: CallbackQuery):
    task_id = int(callback.data.split("_", 1)[1])
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if not task:
        await callback.answer("المهمة دي مش موجودة.", show_alert=True)
        return

    if task["type"] == "channel_join":
        is_member = await check_channel_membership(callback.from_user.id, task["target"])
        if is_member:
            db.complete_task_auto(callback.from_user.id, task_id, task["reward"])
            await callback.answer(f"تم! +{task['reward']} {COIN_SYMBOL}", show_alert=True)
        else:
            await callback.answer(
                f"لازم تنضم للقناة الأول: {task['target']}", show_alert=True
            )
            return
    else:
        # مهمة يدوية: نحطها في قائمة مراجعة الأدمن
        db.mark_task_pending_review(callback.from_user.id, task_id)
        await callback.answer(
            "تم إرسال طلبك، هيتراجع من الأدمن قريبًا.", show_alert=True
        )
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    admin_id,
                    f"📋 مراجعة مهمة:\nUser: {callback.from_user.id} (@{callback.from_user.username})\n"
                    f"Task: {task['title']}\n"
                    f"للموافقة: /approve {callback.from_user.id} {task_id}"
                )
            except Exception:
                pass

    # تحديث القائمة
    statuses = {}
    for t in TASKS:
        row = db.get_task_status(callback.from_user.id, t["id"])
        statuses[t["id"]] = row["status"] if row else None
    try:
        await callback.message.edit_reply_markup(
            reply_markup=kb.tasks_kb(callback.from_user.id, statuses)
        )
    except TelegramBadRequest:
        pass


# ---------------------- أمر الأدمن للموافقة على المهام اليدوية ----------------------

@dp.message(Command("approve"))
async def cmd_approve(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("استخدام: /approve <user_id> <task_id>")
        return
    user_id, task_id = int(parts[1]), int(parts[2])
    task = next((t for t in TASKS if t["id"] == task_id), None)
    if not task:
        await message.answer("المهمة دي مش موجودة.")
        return
    db.approve_task(user_id, task_id, task["reward"])
    await message.answer(f"تمت الموافقة، تم إضافة {task['reward']} {COIN_SYMBOL} للمستخدم {user_id}.")
    try:
        await bot.send_message(user_id, f"✅ تم اعتماد مهمتك: {task['title']} (+{task['reward']} {COIN_SYMBOL})")
    except Exception:
        pass


# ---------------------- Friends / Referrals ----------------------

@dp.message(F.text == "👥 Friends")
async def show_friends(message: Message):
    ensure_user(message)
    total, active, latest = db.get_referral_stats(message.from_user.id)
    link = f"https://t.me/{BOT_USERNAME}?start={message.from_user.id}"

    lines = [
        "👥 <b>الأصحاب</b>",
        f"ادعُ أصحابك واكسب مكافأة تلقائية بس بعد التأكد من نشاطهم الفعلي.\n",
        f"🔗 رابط دعوتك:\n<code>{link}</code>\n",
        f"📊 إجمالي الدعوات: {total} | نشطة: {active}",
        f"🎁 مكافأة كل إحالة نشطة: +{REFERRAL_REWARD} {COIN_SYMBOL} (تُستخدم فقط لشراء أجهزة التعدين)\n",
    ]
    if latest:
        lines.append("آخر المدعوين:")
        for row in latest:
            status_icon = "✅ نشط" if row["status"] == "active" else "⏳ في الانتظار"
            uname = row["username"] or row["first_name"] or "مستخدم"
            lines.append(f"  • @{uname} — {status_icon}")

    await message.answer("\n".join(lines), reply_markup=kb.friends_kb())


@dp.callback_query(F.data == "copy_ref_link")
async def cb_copy_link(callback: CallbackQuery):
    link = f"https://t.me/{BOT_USERNAME}?start={callback.from_user.id}"
    await callback.answer()
    await callback.message.answer(f"<code>{link}</code>")


# ---------------------- Profile ----------------------

@dp.message(F.text == "👤 Profile")
async def show_profile(message: Message):
    ensure_user(message)
    user = db.get_user(message.from_user.id)
    await message.answer(profile_text(user))


# ---------------------- التشغيل ----------------------

async def on_startup_webhook():
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logging.info(f"Webhook set to {WEBHOOK_URL}")


async def on_shutdown_webhook():
    await bot.delete_webhook()


def run_webhook():
    """تشغيل عن طريق Webhook - مناسب للاستضافات اللي بتحتاج بورت مفتوح (Render Web Service مثلًا)."""
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    async def _on_startup(app):
        db.init_db()
        await on_startup_webhook()

    async def _on_shutdown(app):
        await on_shutdown_webhook()

    app.on_startup.append(_on_startup)
    app.on_shutdown.append(_on_shutdown)

    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT)


async def run_polling():
    """تشغيل عن طريق Polling - مناسب لأي VPS أو worker process (Railway/PM2/systemd/Docker)."""
    db.init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    if USE_WEBHOOK:
        run_webhook()
    else:
        asyncio.run(run_polling())
