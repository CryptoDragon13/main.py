"""
طبقة قاعدة البيانات - SQLite بسيطة بدون أي اتصال بمحافظ حقيقية أو دفع فعلي.
كل الأرصدة هنا افتراضية بالكامل (نقاط لعبة داخلية).
"""
import time
import sqlite3
from contextlib import contextmanager

from config import DB_PATH, DEFAULT_SPEED, MINER_TIERS, TASKS


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        cur = conn.cursor()
        yield cur
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db_cursor() as cur:
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            level INTEGER DEFAULT 1,
            speed REAL DEFAULT %f,
            pool_balance REAL DEFAULT 0,
            referral_balance REAL DEFAULT 0,
            last_update_ts INTEGER,
            referred_by INTEGER,
            claims_count INTEGER DEFAULT 0,
            is_activated INTEGER DEFAULT 0,
            created_at INTEGER
        )
        """ % DEFAULT_SPEED)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER,
            referred_id INTEGER UNIQUE,
            status TEXT DEFAULT 'pending',
            created_at INTEGER
        )
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_tasks (
            user_id INTEGER,
            task_id INTEGER,
            status TEXT DEFAULT 'pending_review',
            completed_at INTEGER,
            PRIMARY KEY (user_id, task_id)
        )
        """)


# ---------------------- المستخدمين ----------------------

def get_user(user_id: int):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        return cur.fetchone()


def create_user_if_not_exists(user_id: int, username: str, first_name: str, referred_by: int = None):
    now = int(time.time())
    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE user_id=?", (user_id,))
        if cur.fetchone():
            return False
        cur.execute("""
            INSERT INTO users (user_id, username, first_name, speed, last_update_ts, referred_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, first_name, DEFAULT_SPEED, now, referred_by, now))

        if referred_by and referred_by != user_id:
            cur.execute("""
                INSERT OR IGNORE INTO referrals (referrer_id, referred_id, status, created_at)
                VALUES (?, ?, 'pending', ?)
            """, (referred_by, user_id, now))
        return True


def compute_pending(user_row) -> float:
    """يحسب كمية العملة المتراكمة من وقت آخر تحديث لحد دلوقتي، بحد أقصى للتراكم."""
    from config import MAX_ACCUMULATION_HOURS
    now = int(time.time())
    elapsed_hours = (now - user_row["last_update_ts"]) / 3600
    elapsed_hours = min(elapsed_hours, MAX_ACCUMULATION_HOURS)
    elapsed_hours = max(elapsed_hours, 0)
    return round(user_row["speed"] * elapsed_hours, 4)


def claim(user_id: int) -> float:
    """يضيف المتراكم لرصيد المستخدم ويرجع القيمة المُضافة."""
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        if not row:
            return 0.0
        pending = compute_pending(row)
        now = int(time.time())
        new_balance = row["pool_balance"] + pending
        new_claims = row["claims_count"] + 1
        cur.execute("""
            UPDATE users SET pool_balance=?, last_update_ts=?, claims_count=?
            WHERE user_id=?
        """, (new_balance, now, new_claims, user_id))
        return pending


def try_activate_referral(user_id: int):
    """
    يفعّل إحالة المستخدم لو حقق شرط النشاط (عدد Claims + وقت مرّ من التسجيل).
    الإحالة متتفعلش (وبالتالي مكافأة المُحيل متتحسبش) غير لما ده يحصل.
    """
    from config import (
        REFERRAL_ACTIVATION_MIN_CLAIMS,
        REFERRAL_ACTIVATION_MIN_HOURS_SINCE_JOIN,
        REFERRAL_REWARD,
    )
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = cur.fetchone()
        if not user or user["is_activated"]:
            return False

        hours_since_join = (int(time.time()) - user["created_at"]) / 3600
        if (user["claims_count"] >= REFERRAL_ACTIVATION_MIN_CLAIMS
                and hours_since_join >= REFERRAL_ACTIVATION_MIN_HOURS_SINCE_JOIN):

            cur.execute("UPDATE users SET is_activated=1 WHERE user_id=?", (user_id,))

            cur.execute("SELECT * FROM referrals WHERE referred_id=? AND status='pending'", (user_id,))
            ref = cur.fetchone()
            if ref:
                cur.execute("UPDATE referrals SET status='active' WHERE id=?", (ref["id"],))
                cur.execute("""
                    UPDATE users SET referral_balance = referral_balance + ?
                    WHERE user_id=?
                """, (REFERRAL_REWARD, ref["referrer_id"]))
            return True
    return False


def get_referral_stats(user_id: int):
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) c FROM referrals WHERE referrer_id=?", (user_id,))
        total = cur.fetchone()["c"]
        cur.execute("SELECT COUNT(*) c FROM referrals WHERE referrer_id=? AND status='active'", (user_id,))
        active = cur.fetchone()["c"]
        cur.execute("""
            SELECT u.username, u.first_name, r.status FROM referrals r
            JOIN users u ON u.user_id = r.referred_id
            WHERE r.referrer_id=? ORDER BY r.created_at DESC LIMIT 10
        """, (user_id,))
        latest = cur.fetchall()
        return total, active, latest


def get_next_miner_tier(current_level: int):
    for tier in MINER_TIERS:
        if tier[0] == current_level + 1:
            return tier
    return None


def upgrade_miner(user_id: int):
    """يحاول ترقية جهاز التعدين لو الرصيد كافي. يرجع (نجاح, رسالة)."""
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user = cur.fetchone()
        if not user:
            return False, "المستخدم مش موجود."

        next_tier = get_next_miner_tier(user["level"])
        if not next_tier:
            return False, "انت وصلت لأعلى مستوى تعدين متاح حاليًا."

        _, name, new_speed, cost = next_tier
        total_available = user["pool_balance"] + user["referral_balance"]
        if total_available < cost:
            return False, f"محتاج {cost} عملة على الأقل للترقية (متاح حاليًا {round(total_available,4)})."

        # اخصم من referral_balance الأول (لأنها مقيدة على شراء الأجهزة) وبعدين من pool_balance
        remaining_cost = cost
        new_referral_balance = user["referral_balance"]
        new_pool_balance = user["pool_balance"]

        from_referral = min(new_referral_balance, remaining_cost)
        new_referral_balance -= from_referral
        remaining_cost -= from_referral

        new_pool_balance -= remaining_cost

        cur.execute("""
            UPDATE users SET level=?, speed=?, pool_balance=?, referral_balance=?
            WHERE user_id=?
        """, (next_tier[0], new_speed, new_pool_balance, new_referral_balance, user_id))
        return True, f"تم ترقية جهازك إلى {name} (سرعة {new_speed}/ساعة)."


# ---------------------- المهام ----------------------

def get_task_status(user_id: int, task_id: int):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM user_tasks WHERE user_id=? AND task_id=?", (user_id, task_id))
        return cur.fetchone()


def mark_task_pending_review(user_id: int, task_id: int):
    now = int(time.time())
    with db_cursor() as cur:
        cur.execute("""
            INSERT OR IGNORE INTO user_tasks (user_id, task_id, status, completed_at)
            VALUES (?, ?, 'pending_review', NULL)
        """, (user_id, task_id))


def approve_task(user_id: int, task_id: int, reward: float):
    now = int(time.time())
    with db_cursor() as cur:
        cur.execute("""
            UPDATE user_tasks SET status='completed', completed_at=? WHERE user_id=? AND task_id=?
        """, (now, user_id, task_id))
        cur.execute("UPDATE users SET pool_balance = pool_balance + ? WHERE user_id=?", (reward, user_id))


def complete_task_auto(user_id: int, task_id: int, reward: float):
    """للمهام اللي بتتأكد أوتوماتيك (زي عضوية قناة) - بتضاف فورًا."""
    now = int(time.time())
    with db_cursor() as cur:
        cur.execute("""
            INSERT OR REPLACE INTO user_tasks (user_id, task_id, status, completed_at)
            VALUES (?, ?, 'completed', ?)
        """, (user_id, task_id, now))
        cur.execute("UPDATE users SET pool_balance = pool_balance + ? WHERE user_id=?", (reward, user_id))


def get_pending_reviews():
    with db_cursor() as cur:
        cur.execute("""
            SELECT ut.user_id, ut.task_id, u.username FROM user_tasks ut
            JOIN users u ON u.user_id = ut.user_id
            WHERE ut.status='pending_review'
        """)
        return cur.fetchall()
