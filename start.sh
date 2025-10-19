#!/bin/bash
# -----------------------------------------------------------------
# نام اسکریپت: start.sh
# توضیحات:
# این اسکریپت اجرا کننده، دو پروسه پایتون را همزمان اجرا می‌کند:
# 1. calculator.py : کارگر محاسبات آربیتراژ (در پس‌زمینه)
# 2. api_server.py : سرور API برای نمایش نتایج (در پس‌زمینه)
#
# این اسکریپت توسط سرویس systemd به نام 'tarde_internal_api.service'
# فراخوانی می‌شود و در صورت کرش کردن هر یک از دو پروسه‌ی بالا،
# کل اسکریپت خارج می‌شود (exit 1) تا systemd آن را ری‌استارت کند.
# -----------------------------------------------------------------

# پیدا کردن مسیر دقیق پوشه‌ی پروژه (جایی که این اسکریپت هست)
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# فعال‌سازی محیط مجازی پایتون (venv)
source "$DIR/venv/bin/activate"

# چاپ پیام شروع در لاگ‌های systemd
echo "Starting Wallex Arbitrage services (Calculator worker and API server)..."

# اجرای محاسبه‌گر (calculator.py) در پس‌زمینه
python "$DIR/calculator.py" &
CALC_PID=$!

# اجرای سرور API (api_server.py) در پس‌زمینه
python "$DIR/api_server.py" &
API_PID=$!

# تعریف یک تابع برای پاکسازی (بستن پروسه‌ها)
cleanup() {
    echo "Stopping child processes (PID: $CALC_PID, $API_PID)..."
    # ارسال سیگنال توقف (SIGTERM) به هر دو پروسه
    kill $CALC_PID
    kill $API_PID
    # منتظر ماندن تا هر دو کاملاً بسته شوند
    wait $CALC_PID
    wait $API_PID
}

# اگر سرویس متوقف شد (systemctl stop)، تابع cleanup را اجرا کن
trap cleanup SIGINT SIGTERM

# منتظر ماندن برای اولین پروسه‌ای که کرش کند یا متوقف شود
wait -n $CALC_PID $API_PID

# اگر اسکریپت به اینجا برسد، یعنی یکی از پروسه‌ها کرش کرده
echo "A child process has exited. Initiating restart of all services..."
cleanup
exit 1 # خروج با کد خطا، تا systemd سرویس را ری‌استارت کند
