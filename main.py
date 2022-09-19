import os
from pprint import pprint

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater
)


def main() -> None:
    load_dotenv()
    url = os.getenv('MOLTIN_API_URL')
    store_id = os.getenv('STORE_ID')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }

    token_response = requests.post(
        url='https://api.moltin.com/oauth/access_token', 
        data=data
    )
    token_response.raise_for_status()
    access_token = token_response.json()['access_token']

    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    product_response = requests.get(
        url='https://api.moltin.com/pcm/products',
        headers=headers
    )
    product_response.raise_for_status()
    pprint(product_response.json())

    prices_response = requests.get(
            url='https://api.moltin.com/pcm/pricebooks/e7f0699d-3cd3-49b3-8cf3-9f855dc2b7e7/prices',
            headers=headers
        )
    prices_response.raise_for_status()
    pprint(prices_response.json())
    


if __name__ == '__main__':
    main()
