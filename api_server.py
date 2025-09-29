# api_server.py

from flask import Flask, jsonify, abort
import json
import os

# --- وارد کردن تنظیمات از فایل کانفیگ ---
import config

app = Flask(__name__)

@app.route('/Internal/arbitrage', methods=['GET'])
def get_arbitrage_results():
    """
    این اندپوینت آخرین نتایج تحلیل آربیتراژ را از فایل JSON می‌خواند و نمایش می‌دهد
    """
    json_path = config.JSON_OUTPUT_FILE
    
    # بررسی اینکه آیا فایل نتایج وجود دارد یا نه
    if not os.path.exists(json_path):
        # اگر فایل وجود نداشت، یک خطای 404 با پیام مناسب برمی‌گرداند
        abort(404, description="Results not found. The calculator may not have run yet.")

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        # اگر در خواندن فایل خطایی رخ دهد، یک خطای داخلی سرور برمی‌گرداند
        abort(500, description=f"An error occurred while reading the results file: {e}")

@app.route('/')
def index():
    """یک صفحه راهنما برای روت اصلی"""
    return "Welcome to Wallex Arbitrage API. Access results at /Internal/arbitrage"

if __name__ == '__main__':
    # در محیط واقعی بهتر است از سرورهای WSGI مانند Gunicorn یا Waitress استفاده کنید
    # مثال: gunicorn --bind 0.0.0.0:5001 api_server:app
    app.run(host='0.0.0.0', port=5001, debug=False)