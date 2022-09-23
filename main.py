from curses.ascii import isdigit
import logging
import os
from pathlib import Path
from pprint import pprint

import redis
import requests
import telegram
from dotenv import load_dotenv
from functools import partial
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
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


def get_all_products(url: str, token: str) -> list[dict]:
    '''Get all products from moltin API.'''
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'EP-Channel': 'web store'
    }
    response = requests.get(
        url=url,
        headers=headers
    )
    response.raise_for_status()
    return response.json()['data']


def get_product(product_id: str, token: str) -> list[dict]:
    '''Get certain product from moltin API.'''
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'EP-Channel': 'web store'
    }
    response = requests.get(
        url=f'https://api.moltin.com/catalog/products/{product_id}',
        headers=headers
    )
    response.raise_for_status()
    return response.json()['data']


def download_product_main_image(product_id: str, token: str) -> str:
    '''Download product main image.'''
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        url= (
            f'https://api.moltin.com/pcm/products/{product_id}'
            f'/relationships/main_image'
        ),
        headers=headers
    )
    response.raise_for_status()
    image_id = response.json()['data']['id']
    response = requests.get(
        url=f'https://api.moltin.com/v2/files/{image_id}',
        headers=headers
    )
    response.raise_for_status()
    main_image = response.json()['data']
    filepath = Path('images', main_image['file_name'])
    if not filepath.exists():
        response = requests.get(main_image['link']['href'])
        response.raise_for_status()
        with open(filepath, 'wb') as image_file:
            image_file.write(response.content)
    return filepath


def create_cart(
    update: telegram.update.Update,
    context: CallbackContext,
    token: str
) -> str:
    '''Create cart.'''
    chat_id = context.user_data.get('chat_id')
    response = requests.get(
        url=f'https://api.moltin.com/v2/carts/{chat_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()


def add_product_to_cart(
    token: str,
    cart_id: str,
    product_id: str,
    quantity: str
) -> dict:
    '''Add product to cart.'''
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    payload = {
        "data": {
            "id": product_id,
            "type": "cart_item",
            "quantity": int(quantity),
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


def handle_users_reply(
    update: telegram.update.Update,
    context: CallbackContext,
    token: str,
    db: redis.Redis
) -> None:
    '''State-machine implementation.'''
    if update.message:
        user_reply = update.message.text
        chat_id = context.user_data['chat_id'] = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
        context.user_data['chat_id'] = chat_id
    else:
        return
    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db.get(chat_id)
    
    states_functions = {
        'START': partial(start, token=token),
        'HANDLE_MENU': partial(button, token=token),
        'HANDLE_DESCRIPTION': partial(handle_description, token=token),
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def get_product_stock(product_id: str, token: str) -> dict:
    '''Get product's stock information.'''
    headers = {
        'Authorization': f'Bearer {token}',
    }
    url = f'https://api.moltin.com/v2/inventories/{product_id}'
    response = requests.get(url=url, headers=headers)
    response.raise_for_status()
    return response.json()['data']


def start(
    update: telegram.update.Update,
    context: CallbackContext,
    token: str,
) -> str:
    '''Send a message when the command /start is issued.'''
    products = get_all_products(
        url='https://api.moltin.com/pcm/products/',
        token=token
    )
    keyboard = list()
    for product in products:
        product_name = product['attributes']['name']
        keyboard.append(
            [InlineKeyboardButton(
                product_name,
                callback_data=product['id']
            )]
        )
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(
        text='Please choose:',
        chat_id=context.user_data.get('chat_id'),
        reply_markup=reply_markup)
    return 'HANDLE_MENU'


def button(
    update: telegram.update.Update,
    context: CallbackContext,
    token: str
) -> str:
    query = update.callback_query
    product_id = context.user_data['product_id'] = query.data
    chat_id = context.user_data.get('chat_id')
    product = get_product(product_id=product_id, token=token)
    main_image_filepath = download_product_main_image(
        product_id=product_id,
        token=token
    )
    stock = get_product_stock(product_id=product_id, token=token)
    reply_text = (
        f'{product["attributes"]["name"]}\n\n'
        f'{product["meta"]["display_price"]["without_tax"]["formatted"]} per kg'
        f'\n{stock["available"]} kg on stock'
        f'\n{product["attributes"]["description"]}'
    )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=query.message.message_id
    )
    with open(main_image_filepath, 'rb') as image_file:
        reply_markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton('1 kg',callback_data=1),
                    InlineKeyboardButton('5 kg',callback_data=5),
                    InlineKeyboardButton('10 kg',callback_data=10)
                ], 
                [InlineKeyboardButton('Назад',callback_data='back')]
            ]
        )
        context.bot.send_photo(
            chat_id=chat_id,
            photo=image_file,
            caption=reply_text,
            reply_markup=reply_markup
        )
    return 'HANDLE_DESCRIPTION'


def handle_description(
    update: telegram.update.Update,
    context: CallbackContext,
    token: str
) -> None:
    '''Return to products menu.'''
    query_data = update.callback_query.data
    chat_id=context.user_data.get('chat_id')
    if query_data == 'back':
        return start(update=update, context=context, token=token)
    elif query_data.isdigit():
        if not context.user_data.get('cart_id'):
            create_cart(update=update, context=context, token=token)
            context.user_data['cart_id'] = chat_id
        cart = add_product_to_cart(
            token=token,
            cart_id=chat_id,
            product_id=context.user_data.get('product_id'),
            quantity=query_data
        )
        pprint(cart)
        return 'HANDLE_DESCRIPTION'


def main() -> None:
    '''Start the Telegram-bot.'''
    load_dotenv()
    url = os.getenv('MOLTIN_API_URL')
    store_id = os.getenv('STORE_ID')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    tg_token = os.getenv('TG_TOKEN')
    db_host = os.getenv('DB_HOST', default='localhost')
    db_port = os.getenv('DB_PORT', default=6379)
    db_password = os.getenv('DB_PASSWORD', default=None)
    token_url = 'https://api.moltin.com/oauth/access_token'

    redis_db = redis.Redis(
        host=db_host,
        port=db_port,
        password=db_password,
        decode_responses=True
    )

    access_token, expiration_time = get_token(
        url=token_url,
        client_id=client_id,
        client_secret=client_secret
    )

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(handle_users_reply, db=redis_db, token=access_token)
        )
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(handle_users_reply, db=redis_db, token=access_token)
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            'start',
            partial(handle_users_reply, db=redis_db, token=access_token)
        )
    )
    updater.start_polling()


if __name__ == '__main__':
    main()
