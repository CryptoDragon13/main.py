# بوت تعدين وهمي (Tap/Passive-to-Earn) — جاهز للرفع على استضافة

بوت لعبة داخل تليجرام: عملة افتراضية 100%، **مفيش أي دفع أو سحب فلوس حقيقية**.
المستخدم "يعدّن" عملة داخل اللعبة بمرور الوقت، يقدر يرفع مستوى جهازه، يعمل مهام
بسيطة (انضمام لقناة، متابعة سوشيال ميديا)، ويدعو أصحابه.

## المميزات
- ⛏ **تعدين تراكمي**: كل مستخدم عنده سرعة (عملة/ساعة)، والرصيد بيتراكم تلقائي
  لحد ما يضغط **Claim**، بحد أقصى ساعات تراكم (قابل للتعديل في `config.py`).
- ⚡ **ترقية أجهزة التعدين**: 8 مستويات، كل مستوى بيزود السرعة ومحتاج رصيد معين.
- 📝 **مهام**: مهام انضمام قناة بيتم التحقق منها تلقائيًا (`getChatMember`)،
  ومهام تانية (متابعة تويتر/يوتيوب) بتتحط في قائمة مراجعة الأدمن.
- 👥 **إحالات محمية**: رابط دعوة لكل مستخدم، لكن مكافأة المُحيل **متتفعلش**
  غير لما المُحال يثبت نشاط حقيقي (عدد Claims + وقت معين من التسجيل)،
  عشان تقلل حسابات الإحالة الوهمية.
- 👤 **بروفايل**: عرض الرصيد، رصيد الإحالات (مقصور على شراء الأجهزة)، والسرعة.
- 🚀 **جاهز للنشر**: يدعم تشغيل بـ Polling أو Webhook، Docker، Procfile، ومتغيرات بيئة.

## بنية المشروع

```
atf_clone_bot/
├── bot.py             # نقطة الدخول + كل الـ handlers
├── config.py          # كل الإعدادات (بتتقرأ من .env)
├── db.py              # طبقة قاعدة البيانات (SQLite)
├── keyboards.py        # لوحات المفاتيح (Reply + Inline)
├── requirements.txt
├── .env.example        # مثال لمتغيرات البيئة - انسخه لـ .env
├── .gitignore
├── Procfile            # لاستضافات Railway/Heroku
├── runtime.txt         # إصدار Python لبعض الاستضافات
├── Dockerfile          # للنشر عن طريق Docker
└── README.md
```

## 1) الإعداد الأول

1. اعمل بوت جديد من [@BotFather](https://t.me/BotFather) وخد التوكن.
2. اعرف يوزر البوت بتاعك (من غير @).
3. اعرف آيدي حسابك في تليجرام (جرب [@userinfobot](https://t.me/userinfobot)).
4. انسخ `.env.example` لملف اسمه `.env`:
```bash
   cp .env.example .env
```
5. افتح `.env` واملأ:
   - `BOT_TOKEN` — توكن البوت.
   - `BOT_USERNAME` — يوزر البوت.
   - `ADMIN_IDS` — آيدي حسابك (أو أكتر من آيدي مفصولين بفاصلة).
6. لو حابب تغيّر اسم العملة أو المهام أو مستويات الأجهزة، عدّلهم مباشرة في
   `config.py` (قسم `COIN_NAME`, `TASKS`, `MINER_TIERS`, `REFERRAL_*`).

## 2) التشغيل محليًا (للتجربة)

```bash
python -m venv venv
source venv/bin/activate   # على ويندوز: venv\Scripts\activate
pip install -r requirements.txt
python bot.py
```

البوت هيشتغل بـ Polling افتراضيًا (مفيش حاجة إضافية مطلوبة).

## 3) النشر على استضافة

### أ) Railway / أي منصة بتدعم "Worker" أو "Background Service"
هي أسهل طريقة لأن Polling مش محتاج بورت مفتوح:
1. ارفع المشروع على GitHub.
2. اعمل New Project → Deploy from GitHub Repo.
3. من Variables، ضيف نفس المتغيرات اللي في `.env.example` (`BOT_TOKEN`, `BOT_USERNAME`, `ADMIN_IDS`).
4. سيب `USE_WEBHOOK=false` (أو متضيفوش خالص).
5. Railway هيقرأ `Procfile` تلقائي ويشغل `python bot.py`.

### ب) Render (Background Worker) — الأفضل لو متاح في خطتك
1. New → Background Worker.
2. اربط الريبو، Build Command: `pip install -r requirements.txt`، Start Command: `python bot.py`.
3. ضيف المتغيرات زي فوق، `USE_WEBHOOK=false`.

### ج) Render (Web Service المجاني) أو أي استضافة بتتطلب بورت مفتوح
الخطط المجانية أحيانًا بتشترط "Web Service" بيسمع على بورت (مش Worker). في الحالة دي:
1. حط `USE_WEBHOOK=true` في المتغيرات.
2. حط `WEBHOOK_BASE_URL` = رابط تطبيقك بعد النشر (مثال: `https://your-app.onrender.com`).
3. سيب `PORT` فاضي (المنصة بتحدده تلقائي).
4. البوت هيشغل سيرفر aiohttp داخلي ويسجل الـ webhook تلقائي عند التشغيل.

### د) VPS خاص بيك (Ubuntu مثلًا)
```bash
sudo apt update && sudo apt install -y python3-venv git
git clone <your-repo-url> atf_bot && cd atf_bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # واملأ القيم
```
شغله دايمًا في الخلفية باستخدام واحدة من دول:
- **systemd** (الأفضل للإنتاج):
  اعمل ملف `/etc/systemd/system/atfbot.service`:
```ini
  [Unit]
  Description=ATF Clone Telegram Bot
  After=network.target

  [Service]
  WorkingDirectory=/path/to/atf_bot
  ExecStart=/path/to/atf_bot/venv/bin/python bot.py
  Restart=always
  User=your_linux_user

  [Install]
  WantedBy=multi-user.target
```
  بعدين:
```bash
  sudo systemctl daemon-reload
  sudo systemctl enable --now atfbot
  sudo systemctl status atfbot
```
- **أو pm2**:
```bash
  npm install -g pm2
  pm2 start "venv/bin/python bot.py" --name atfbot
  pm2 save && pm2 startup
```

### هـ) Docker (أي سيرفر بيدعم Docker)
```bash
docker build -t atf-bot .
docker run -d --name atf-bot \
  --env-file .env \
  -p 8080:8080 \
  --restart unless-stopped \
  atf-bot
```

## 4) ملاحظات مهمة قبل ما ترفع البوت فعليًا

- **قاعدة البيانات**: افتراضيًا SQLite (ملف واحد محلي). أغلب الاستضافات
  الـ "ephemeral" (زي Render/Railway الافتراضي) بتمسح الملفات المحلية عند
  إعادة التشغيل/الـ redeploy — يعني ممكن تفقد بيانات المستخدمين!
  لو محتاج تخزين دائم:
  - على Railway: ضيف Volume واربطه بمسار `DB_PATH`.
  - أو استخدم قاعدة بيانات خارجية (Postgres مجاني على Railway/Render/Neon) — قولّي
    لو عايز أحول `db.py` لـ PostgreSQL بدل SQLite.
- **المهام اليدوية** (متابعة تويتر/يوتيوب) بتتوافق عليها بأمر
  `/approve <user_id> <task_id>` من أي حساب أدمن مُضاف في `ADMIN_IDS`.
- **مفيش أي كود بيتعامل مع محافظ حقيقية أو TON فعلي أو أي بوابة دفع** — كل
  الأرصدة نقاط لعبة داخلية بس.
- غيّر `COIN_NAME`, `COIN_SYMBOL`, والمهام والروابط في `config.py` قبل ما تنشر
  عشان تبقى مطابقة لمشروعك فعليًا.
