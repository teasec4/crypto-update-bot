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

def get_top_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 10,
        'page': 1
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return [coin['id'] for coin in data]
    except requests.RequestException as e:
        print(f"Failed to fetch top coins: {e}")
        return []

def load_subscribers(chat_id=None):
    try:
        with open(SUBSCRIBER_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            else:
                return {str(chat_id): "Asia/Shanghai" for chat_id in data}
    except FileNotFoundError:
        return {}

def save_subscribers(subscribers):
    with open(SUBSCRIBER_FILE, "w") as f:
        json.dump(subscribers, f, indent=4)

def _add_subscriber(chat_id):
    subscribers = load_subscribers()
    if str(chat_id) not in subscribers:
        subscribers[str(chat_id)] = "Asia/Shanghai"
        save_subscribers(subscribers)
        return True
    return False

def _remove_subscriber(chat_id):
    subscribers = load_subscribers()
    if chat_id in subscribers:
        del subscribers[chat_id]
        save_subscribers(subscribers)
        return True
    return False

