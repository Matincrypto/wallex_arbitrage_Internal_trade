# calculator.py

import requests
import json
import time
import logging
from datetime import datetime

# --- وارد کردن تنظیمات از فایل کانفیگ ---
import config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def safe_float_conversion(value):
    if value is None:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (ValueError, TypeError):
        return None

def get_best_ask_price_from_depth(market_symbol, timeout=10):
    api_url = "https://api.wallex.ir/v1/depth"
    params = {"symbol": market_symbol}
    try:
        response = requests.get(api_url, params=params, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if data.get("success") and "result" in data:
            ask_orders = data["result"].get("ask", [])
            if ask_orders:
                return float(ask_orders[0]["price"])
            else:
                return None # Order book is empty, which is a reason to fallback
        return None
            
    except requests.exceptions.HTTPError as e:
        # خطای 422 به معنی نیاز به استفاده از قیمت جایگزین است
        if e.response.status_code == 422:
            return None # Fallback is needed
        else:
            logger.error(f"An unexpected HTTP error occurred for {market_symbol}: {e}")
            return "error" # An actual error occurred
    except requests.exceptions.RequestException:
        return "error" # A network error occurred

def get_all_market_data():
    api_url = "https://api.wallex.ir/hector/web/v1/markets"
    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not data.get("success"):
            logger.error(f"API returned an error on fetching all markets: {data.get('message')}")
            return None
        
        markets_data = {}
        raw_markets = data.get("result", {}).get("markets", [])
        for market in raw_markets:
            symbol = market.get("symbol")
            if symbol:
                price = safe_float_conversion(market.get("price"))
                volume = safe_float_conversion(market.get("quote_volume_24h"))
                if price is not None:
                    markets_data[symbol] = {
                        "price": price,
                        "volume": volume
                    }
        return markets_data
    except Exception as e:
        logger.error(f"Error processing market list from Wallex API: {e}")
        return None

def save_data_to_json(data, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"Analysis data successfully saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save data to JSON file {filename}: {e}")

def run_analysis():
    logger.info(f"--- Starting Hybrid Analysis (with Fallback Logic) at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    all_markets = get_all_market_data()
    if not all_markets:
        logger.error("No market data retrieved. Aborting analysis cycle.")
        return

    tether_market_data = all_markets.get("USDTTMN")
    if not tether_market_data or not tether_market_data.get("price"):
        logger.error("Could not fetch valid Tether price. Cannot perform analysis.")
        return
    tether_price_tmn = tether_market_data["price"]
    logger.info(f"Using general Tether price (USDTTMN): {tether_price_tmn:,.2f} Toman")
    
    potential_opportunities = []

    for symbol, usdt_market_data in all_markets.items():
        if symbol.endswith("USDT") and symbol != "USDTTMN":
            base_asset = symbol[:-4]
            tmn_symbol = f"{base_asset}TMN"

            if tmn_symbol in all_markets:
                usdt_price = usdt_market_data.get("price")
                entry_price = None
                price_type = ""

                # --- START: منطق جدید و چندمرحله‌ای برای یافتن قیمت ورود ---
                
                # اولویت ۱: تلاش برای دریافت قیمت دقیق از دفتر سفارشات
                precise_price = get_best_ask_price_from_depth(tmn_symbol)

                if precise_price == "error":
                    logger.error(f"Skipping {tmn_symbol} due to a network error in depth API.")
                    continue # Skip this symbol if there was an unhandled error

                if precise_price is not None:
                    entry_price = precise_price
                    price_type = "realtime_order_book"
                    logger.info(f"Found precise price for {tmn_symbol}: {entry_price:,.2f}")
                else:
                    # اولویت ۲: اگر بازار غیرفعال بود، از آخرین قیمت معامله‌شده استفاده کن
                    fallback_price = all_markets[tmn_symbol].get("price")
                    if fallback_price:
                        entry_price = fallback_price
                        price_type = "fallback_last_trade"
                        logger.warning(f"Order book for {tmn_symbol} is inactive. Using fallback price: {entry_price:,.2f}")
                
                # --- END: منطق جدید ---

                if usdt_price and entry_price:
                    calculated_exit_price_tmn = usdt_price * tether_price_tmn
                    price_difference = calculated_exit_price_tmn - entry_price
                    percentage_difference = (price_difference / entry_price) * 100

                    tmn_market_data = all_markets[tmn_symbol]
                    usdt_volume = usdt_market_data.get("volume")
                    tmn_volume = tmn_market_data.get("volume")
                    is_usdt_liquid = (usdt_volume is not None) and (usdt_volume >= config.MIN_QUOTE_VOLUME_USDT_FOR_LIQUIDITY)
                    is_tmn_liquid = (tmn_volume is not None) and (tmn_volume >= config.MIN_QUOTE_VOLUME_TMN_FOR_LIQUIDITY)

                    if (percentage_difference > config.MIN_PERCENT_DIFFERENCE_FOR_OPPORTUNITY and
                        is_usdt_liquid and is_tmn_liquid):
                        
                        opportunity_detail = {
                            "entry_price": entry_price,
                            "pair": f"tmn/{base_asset}",
                            "exit_price": round(calculated_exit_price_tmn, 4),
                            "expected_profit_percentage": round(percentage_difference, 2),
                            "asset_name": base_asset,
                            "strategy_name": "Internal",
                            "exchange_name": "Wallex",
                            "price_type": price_type # <-- نوع قیمت استفاده شده
                        }
                        potential_opportunities.append(opportunity_detail)
                
                time.sleep(0.2)

    logger.info(f"Analysis completed. Found {len(potential_opportunities)} potential opportunities.")
    
    output_data = {
        "last_updated": datetime.now().isoformat(),
        "tether_price_tmn": tether_price_tmn,
        "opportunities_found": len(potential_opportunities),
        "opportunities": sorted(potential_opportunities, key=lambda x: x['expected_profit_percentage'], reverse=True)
    }
    
    save_data_to_json(output_data, config.JSON_OUTPUT_FILE)
    logger.info("--- Analysis cycle finished. ---")

if __name__ == "__main__":
    while True:
        try:
            run_analysis()
        except Exception as e:
            logger.critical(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
        wait_time = config.RUN_INTERVAL_SECONDS
        logger.info(f"Waiting for {wait_time} seconds before the next run...")

        time.sleep(wait_time)

