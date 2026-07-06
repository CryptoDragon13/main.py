from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from config import TASKS, MINER_TIERS, BOT_USERNAME


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⛏ Mine"), KeyboardButton(text="⚡ Miners")],
            [KeyboardButton(text="📝 Tasks"), KeyboardButton(text="👥 Friends")],
            [KeyboardButton(text="👤 Profile")],
        ],
        resize_keyboard=True,
    )


def mine_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 CLAIM", callback_data="claim")],
    ])


def miners_kb(current_level: int) -> InlineKeyboardMarkup:
    rows = []
    for tier in MINER_TIERS:
        level, name, speed, cost = tier
        if level <= current_level:
            label = f"✅ {name} (Active)"
            cb = "noop"
        elif level == current_level + 1:
            label = f"⬆️ {name} — يحتاج {cost} عملة"
            cb = "upgrade_miner"
        else:
            label = f"🔒 {name} (Lvl {level})"
            cb = "noop"
        rows.append([InlineKeyboardButton(text=label, callback_data=cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tasks_kb(user_id: int, task_statuses: dict) -> InlineKeyboardMarkup:
    rows = []
    for task in TASKS:
        status = task_statuses.get(task["id"])
        if status == "completed":
            label = f"✅ {task['title']} (+{task['reward']})"
            cb = "noop"
        elif status == "pending_review":
            label = f"⏳ {task['title']} (قيد المراجعة)"
            cb = "noop"
        else:
            label = f"👉 {task['title']} (+{task['reward']})"
            cb = f"task_{task['id']}"
        rows.append([InlineKeyboardButton(text=label, callback_data=cb)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def friends_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 نسخ رابط الدعوة", callback_data="copy_ref_link")],
    ])
