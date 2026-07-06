"""
إعدادات البوت - عدّل القيم دي حسب مشروعك.
كل القيم بتتقرأ من متغيرات البيئة (.env) أولًا، ولو مش موجودة بتستخدم القيمة الافتراضية.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # يقرأ ملف .env لو موجود (مفيد وقت التشغيل المحلي)

# توكن البوت من BotFather
BOT_TOKEN = os.getenv("BOT_TOKEN", "PUT_YOUR_BOT_TOKEN_HERE")

# اسم البوت (يستخدم في بناء رابط الإحالة t.me/<BOT_USERNAME>?start=<user_id>)
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot_username")

# آيديز الأدمن، مفصولة بفاصلة في متغير البيئة، مثال: ADMIN_IDS=123456789,987654321
_admin_ids_raw = os.getenv("ADMIN_IDS", "123456789")
ADMIN_IDS = [int(x.strip()) for x in _admin_ids_raw.split(",") if x.strip()]

# مسار قاعدة البيانات
DB_PATH = os.getenv("DB_PATH", "atf_bot.sqlite3")

# ---------------- إعدادات التشغيل (Polling أو Webhook) ----------------
# على أغلب الاستضافات (Railway / VPS / worker على Render) سيب USE_WEBHOOK=false
# استخدم webhook بس لو مستضيف البوت كـ "Web Service" محتاج يفتح بورت (زي Render Web Service)
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"

# لازم يكون رابط https صحيح للدومين بتاع الاستضافة، مثال:
# https://your-app.up.railway.app
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", "")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_BASE_URL}{WEBHOOK_PATH}"

# البورت اللي السيرفر هيسمعه (أغلب الاستضافات بتحدده تلقائي عن طريق PORT)
WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 8080))

# اسم العملة الافتراضي (يظهر في كل الشاشات)
COIN_NAME = "TON-Mine"  # غيّرها للاسم اللي عايزه
COIN_SYMBOL = "TONM"

# ---------------- إعدادات التعدين ----------------
# سرعة التعدين الافتراضية (عملة/ساعة) لأي مستخدم جديد
DEFAULT_SPEED = 0.2

# أقصى عدد ساعات ممكن يتراكم فيها التعدين قبل ما المستخدم يعمل Claim
# (لو المستخدم غاب أكتر من كده، الزيادة بتقف عند الحد ده)
MAX_ACCUMULATION_HOURS = 3

# ---------------- إعدادات الإحالات ----------------
# قيمة مكافأة الإحالة الواحدة (عملة افتراضية داخل اللعبة فقط)
REFERRAL_REWARD = 0.01

# مكافأة الإحالة دي منفصلة عن الرصيد العادي، ومينفعش غير إنها
# تتصرف على شراء أجهزة تعدين جوا اللعبة (مش قابلة للسحب أو التحويل)
REFERRAL_BALANCE_RESTRICTED_TO_MINERS = True

# الحد الأدنى اللي المُحال لازم يوصله عشان الإحالة تتفعل وتتحسب فعليًا
# (نص ساعة تعدين فعلي على الأقل + عملية Claim واحدة على الأقل)
REFERRAL_ACTIVATION_MIN_CLAIMS = 1
REFERRAL_ACTIVATION_MIN_HOURS_SINCE_JOIN = 0.5

# ---------------- ليفلات أجهزة التعدين ----------------
# كل عنصر: (level, name, speed, unlock_requirement_coins)
MINER_TIERS = [
    (1, "Starter Rig 1", 0.2, 0),      # فعّال من البداية
    (2, "Starter Rig 2", 0.2, 100),
    (3, "Starter Rig 3", 0.3, 300),
    (4, "Starter Rig 4", 0.3, 600),
    (5, "Starter Rig 5", 0.4, 1000),
    (6, "Starter Rig 6", 0.5, 1500),
    (7, "Starter Rig 7", 0.6, 2200),
    (8, "Starter Rig 8", 0.7, 3000),
]

# ---------------- المهام (تتضاف يدوي هنا أو عن طريق أمر أدمن) ----------------
# type: "channel_join" -> يتحقق تلقائي من عضوية القناة عبر getChatMember
#       "manual"       -> يعتمد على تأكيد الأدمن (Done بيدخل في قائمة مراجعة)
TASKS = [
    {
        "id": 1,
        "title": "انضم لقناة تليجرام",
        "reward": 5,
        "type": "channel_join",
        "target": "@your_channel",  # يوزر القناة
    },
    {
        "id": 2,
        "title": "تابعنا على X (Twitter)",
        "reward": 5,
        "type": "manual",
        "target": "https://x.com/your_account",
    },
    {
        "id": 3,
        "title": "اشترك في قناة اليوتيوب",
        "reward": 10,
        "type": "manual",
        "target": "https://youtube.com/@your_channel",
    },
]
