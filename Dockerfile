FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# لو هتشغل بالـ Webhook فعّل البورت ده (لازم يطابق قيمة PORT في متغيرات البيئة)
EXPOSE 8080

CMD ["python", "bot.py"]
