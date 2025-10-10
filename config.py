# config.py

# --- Wallex API Configuration ---
BASE_URL = "https://api.wallex.ir/v1/"

# --- Arbitrage Logic Configuration ---
MIN_PERCENT_DIFFERENCE_FOR_OPPORTUNITY = 2.0
MIN_QUOTE_VOLUME_USDT_FOR_LIQUIDITY = 1000.0
MIN_QUOTE_VOLUME_TMN_FOR_LIQUIDITY = 50000000.0

# --- Excel Formatting Thresholds ---
HIGHLIGHT_POSITIVE_ARB_THRESHOLD = 0.5
HIGHLIGHT_NEGATIVE_ARB_THRESHOLD = -0.5

# --- File Paths ---
# مسیر فایل JSON که به عنوان دیتابیس موقت بین دو اسکریپت عمل می‌کند
JSON_OUTPUT_FILE = "results.json"
EXCEL_OUTPUT_FILE = "wallex_internal_arbitrage_analysis.xlsx"

# --- Analysis Interval ---
# فاصله زمانی بین هر بار اجرای محاسبات (به ثانیه)
# این متغیر توسط ابزار زمان‌بندی (Scheduler) استفاده خواهد شد

RUN_INTERVAL_SECONDS = 300  # 5 دقیقه
