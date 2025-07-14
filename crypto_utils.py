# crypto_utils.py
import requests
import json
import os

SUBSCRIBER_FILE = "subscribers.json"

def get_price(coin_ids):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'ids': coin_ids,
        'order': 'market_cap_desc'
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        result = {}
        for coin in data:
            result[coin['id']] = {
                'usd': coin['current_price'],
                'market_cap': coin['market_cap'],
                'change_24h': coin['price_change_percentage_24h'],
                'logo': coin['image']
            }
        return result
    except requests.RequestException as e:
        print(f"Failed to fetch prices: {e}")
        return {}

def get_top_coins(limit=1000):
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        coins = response.json()
        return [coin['id'] for coin in coins]
    else:
        return []

def load_subscribers():
    try:
        with open(SUBSCRIBER_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                return {}
    except FileNotFoundError:
        with open(SUBSCRIBER_FILE, "w") as f:
            f.write("{}")
        return {}

def save_subscribers(subscribers):
    with open(SUBSCRIBER_FILE, "w") as f:
        json.dump(subscribers, f, indent=4)

def _add_subscriber(chat_id):
    subscribers = load_subscribers()
    if str(chat_id) not in subscribers:
        subscribers[chat_id] = {
                "timezone": "Asia/Shanghai",
                "coins": ["bitcoin", "ethereum", "dogecoin"],
                "time": "08:00"
            }
        save_subscribers(subscribers)
        return True
    return False

def _remove_subscriber(chat_id):
    subscribers = load_subscribers()
    chat_id = str(chat_id)
    if chat_id in subscribers:
        del subscribers[chat_id]
        save_subscribers(subscribers)
        return True
    return False

