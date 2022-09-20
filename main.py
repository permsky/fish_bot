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


def get_token(url: str, client_id: str, client_secret: str) -> str:
    '''Get authorization token.'''
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(url=url, data=payload)
    response.raise_for_status()
    token = response.json()
    return token['access_token'], token['expires_in']


def get_all_products(url: str, access_token: str) -> list[dict]:
    '''Get all products from moltin API.'''
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'EP-Channel': 'web store'
    }
    response = requests.get(
        url=url,
        headers=headers
    )
    response.raise_for_status()
    return response.json()['data']


def get_product(url: str, access_token: str) -> list[dict]:
    '''Get certain product from moltin API.'''
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'EP-Channel': 'web store'
    }
    response = requests.get(
        url=url,
        headers=headers
    )
    response.raise_for_status()
    return response.json()['data']


def create_cart(url: str, access_token: str) -> str:
    '''Create cart.'''
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    response = requests.get(
        url=url,
        headers=headers
    )
    response.raise_for_status()
    return response.json()


def add_product_to_cart(
    access_token: str,
    cart_id: str,
    product_id: str
) -> None:
    '''Add product to cart.'''
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
    }
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    payload = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": 1,
        }
    }
    response = requests.post(
        url=url,
        headers=headers,
        json=payload
    )
    if response.status_code == 400:
        return response.json()
    response.raise_for_status()
    return response.json()


def get_cart_items(cart_id: str, access_token: str) -> dict:
    '''Get cart items.'''
    headers = {
        'Authorization': f'Bearer {access_token}',
    }
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    return response.json()


def main() -> None:
    load_dotenv()
    url = os.getenv('MOLTIN_API_URL')
    store_id = os.getenv('STORE_ID')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    token_url = 'https://api.moltin.com/oauth/access_token'
    products_url = 'https://api.moltin.com/pcm/products/'
    carts_url = 'https://api.moltin.com/v2/carts/'
    chat_id = '123456789'

    access_token, expiration_time = get_token(
        url=token_url,
        client_id=client_id,
        client_secret=client_secret
    )
    # pprint(f'token: {access_token}')

    products = get_all_products(
        url=products_url,
        access_token=access_token
    )
    # pprint(products)
    product_id = products[1]['id']

    cart = create_cart(
        url=carts_url + chat_id,
        access_token=access_token
    )
    # pprint(cart)
    cart = add_product_to_cart(
        access_token=access_token,
        cart_id=chat_id,
        product_id=product_id
    )
    # pprint(cart)
    cart_items = get_cart_items(
        cart_id=chat_id,
        access_token=access_token
    )
    pprint(cart_items)


if __name__ == '__main__':
    main()
