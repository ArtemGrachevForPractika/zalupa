import requests
import time
from telegram import Bot

# Вставь сюда свой токен и chat_id:
TELEGRAM_TOKEN = '7828022099:AAEJXXLLfd90Imb6H2GmhIOaFmnO1B_UlKY'
TELEGRAM_CHAT_ID = '5034124602'

# Telegram-бот
bot = Bot(token=TELEGRAM_TOKEN)

def send_telegram_message(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {e}")

# Настройки
FUNDING_THRESHOLD = 0.003  # 0.30%
SLEEP_TIME = 60  # задержка между проверками

# Bybit
def get_bybit_funding():
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    result = []
    try:
        r = requests.get(url, timeout=10)
        data = r.json().get("result", {}).get("list", [])
        for item in data:
            symbol = item.get("symbol", "")
            rate_str = item.get("fundingRate", "0")

            # Пропускаем, если значение пустое или нечисловое
            try:
                rate = float(rate_str)
            except ValueError:
                continue

            if "USDT" in symbol and abs(rate) >= FUNDING_THRESHOLD:
                result.append((symbol, rate * 100))
    except Exception as e:
        print(f"Ошибка Bybit: {e}")
    return result

# Binance
def get_binance_funding():
    url = "https://fapi.binance.com/fapi/v1/premiumIndex"
    result = []
    try:
        r = requests.get(url, timeout=10)
        for item in r.json():
            funding = float(item.get("lastFundingRate", 0))
            if abs(funding) >= FUNDING_THRESHOLD:
                result.append((item["symbol"], funding * 100))
    except Exception as e:
        print(f"Ошибка Binance: {e}")
    return result

# MEXC
def get_mexc_funding():
    url = "https://contract.mexc.com/api/v1/contract/funding_rate"
    result = []
    try:
        r = requests.get(url, timeout=10)
        for item in r.json().get("data", []):
            funding = float(item.get("fundingRate", 0))
            if abs(funding) >= FUNDING_THRESHOLD:
                result.append((item["symbol"], funding * 100))
    except Exception as e:
        print(f"Ошибка MEXC: {e}")
    return result


def get_htx_funding():
    url_contracts = "https://api.hbdm.com/linear-swap-api/v1/swap_contract_info"
    result = []
    try:
        r = requests.get(url_contracts, timeout=10)
        contracts = r.json().get("data", [])
        for item in contracts:
            symbol = item.get("contract_code", "")
            if "USDT" not in symbol:
                continue

            # Получаем ставку по каждой монете
            fr_url = f"https://api.hbdm.com/linear-swap-api/v1/swap_funding_rate?contract_code={symbol}"
            fr = requests.get(fr_url, timeout=10)
            funding_data = fr.json().get("data", {})

            rate = float(funding_data.get("funding_rate", 0))
            if abs(rate) >= FUNDING_THRESHOLD:
                result.append((symbol, rate * 100))
    except Exception as e:
        print(f"Ошибка HTX: {e}")
    return result

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Gate.io
def get_gate_funding():
    url = "https://api.gate.io/api/v4/futures/usdt/funding_rates"
    result = []
    try:
        r = requests.get(url, timeout=10, verify=False)
        for item in r.json():
            funding = float(item.get("funding_rate", 0))
            if abs(funding) >= FUNDING_THRESHOLD:
                result.append((item["contract"], funding * 100))
    except Exception as e:
        print(f"Ошибка Gate.io: {e}")
    return result

# KuCoin
def get_kucoin_funding():
    base_url = "https://api-futures.kucoin.com"
    result = []
    try:
        # Получаем список активных контрактов
        r = requests.get(f"{base_url}/api/v1/contracts/active", timeout=10)
        contracts = r.json().get("data", [])

        for item in contracts:
            symbol = item.get("symbol", "")
            if not symbol.endswith("USDTM"):
                continue  # берём только USDT контракты

            # Получаем funding rate по каждой монете
            fr_url = f"{base_url}/api/v1/funding-rate?symbol={symbol}"
            fr = requests.get(fr_url, timeout=10)
            funding_data = fr.json().get("data", {})

            rate_str = funding_data.get("fundingRate", "0")
            try:
                rate = float(rate_str)
            except ValueError:
                continue

            if abs(rate) >= FUNDING_THRESHOLD:
                result.append((symbol, rate * 100))
    except Exception as e:
        print(f"Ошибка KuCoin: {e}")
    return result

# OKX
def get_okx_funding():
    base_url = "https://www.okx.com"
    result = []
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        # Получаем список всех фьючерсных инструментов (SWAP)
        instruments_url = f"{base_url}/api/v5/public/instruments?instType=SWAP"
        response = requests.get(instruments_url, headers=headers, timeout=10)
        instruments = response.json().get("data", [])

        for inst in instruments:
            inst_id = inst.get("instId")
            if not inst_id or not inst_id.endswith("USDT-SWAP"):
                continue  # интересуют только USDT контракты

            # Получаем ставку финансирования
            fr_url = f"{base_url}/api/v5/public/funding-rate?instId={inst_id}"
            fr_response = requests.get(fr_url, headers=headers, timeout=10)
            funding_data = fr_response.json().get("data", [])

            if not funding_data:
                continue

            rate = float(funding_data[0].get("fundingRate", 0))

            # Фильтр по порогу
            if abs(rate) >= FUNDING_THRESHOLD:
                result.append((inst_id, rate * 100))  # Переводим в %

    except Exception as e:
        print(f"Ошибка OKX: {e}")
    return result

# Phemex
def get_phemex_funding():
    url = "https://api.phemex.com/exchange/public/contracts"
    result = []
    try:
        r = requests.get(url, timeout=10)
        contracts = r.json().get("data", {}).get("contracts", [])

        for item in contracts:
            symbol = item.get("symbol", "")
            funding = item.get("fundingRate", None)

            if not symbol.endswith("USDT"):
                continue
            if funding is None:
                continue

            try:
                rate = float(funding)
            except ValueError:
                continue

            if abs(rate) >= FUNDING_THRESHOLD:
                result.append((symbol, rate * 100))
    except Exception as e:
        print(f"Ошибка Phemex: {e}")
    return result


# Универсальная функция вывода
def print_results(results, exchange):
    if results:
        header = f"📢 {exchange} — найдено монет: {len(results)}"
        print(f"\n{header}")
        message = [header]
        for symbol, rate in results:
            line = f"   {symbol}: {rate:.4f}%"
            print(line)
            message.append(line)
        send_telegram_message('\n'.join(message))
    else:
        print(f"{exchange}: ставок ≥ {FUNDING_THRESHOLD*100:.2f}% не найдено")

# Главная функция
def main():
    print(f"📊 Запуск бота | Порог: {FUNDING_THRESHOLD*100:.2f}% | Обновление каждые {SLEEP_TIME} сек")
    while True:
        try:
            print("\n==============================")
            print_results(get_bybit_funding(), "Bybit")
            print_results(get_binance_funding(), "Binance")
            print_results(get_mexc_funding(), "MEXC")
            print_results(get_kucoin_funding(), "KuCoin")
            print_results(get_htx_funding(), "HTX")
            print_results(get_gate_funding(), "Gate.io")
            print_results(get_phemex_funding(), "Phemex")
            print_results(get_okx_funding(), "OKX")

        except Exception as e:
            print("Ошибка основного цикла:", e)
        time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
