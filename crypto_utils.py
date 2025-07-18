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
