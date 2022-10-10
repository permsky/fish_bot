import logging
import os
from datetime import datetime, timedelta
from textwrap import dedent

import redis
import telegram
from dotenv import load_dotenv
from functools import partial
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    Updater
)

from keyboards import (
    get_back_to_menu_keyboard,
    get_cart_keyboard,
    get_menu_keyboard,
    get_order_keyboard
)
from moltin_handlers import (
    add_product_to_cart,
    create_cart,
    create_customer,
    delete_cart_item,
    get_all_products,
    get_cart_items,
    get_product,
    get_product_main_image,
    get_product_stock,
    get_token,
    update_customer
)

logger = logging.getLogger(__name__)


def handle_users_reply(
    update: telegram.update.Update,
    context: CallbackContext,
    client_id: str,
    client_secret: str,
    db: redis.Redis
) -> None:
    '''State-machine implementation.'''
    expiration_datetime = context.bot_data.get('expiration_datetime')
    current_datetime = datetime.now()
    if not expiration_datetime or current_datetime > expiration_datetime:
        token, expired_in = get_token(
            client_id=client_id,
            client_secret=client_secret
        )
        context.bot_data['moltin_token'] = token
        context.bot_data['expiration_datetime'] = current_datetime \
            + timedelta(expired_in - 100)

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
        'START': partial(start, chat_id=chat_id),
        'HANDLE_MENU': partial(handle_menu, chat_id=chat_id),
        'HANDLE_DESCRIPTION': partial(handle_description, chat_id=chat_id),
        'HANDLE_CART': partial(handle_cart, chat_id=chat_id),
        'WAITING_EMAIL': partial(handle_email, chat_id=chat_id),
    }
    state_handler = states_functions[user_state]
    try:
        next_state = state_handler(update, context)
        db.set(chat_id, next_state)
    except Exception as err:
        print(err)


def start(
    update: telegram.update.Update,
    context: CallbackContext,
    chat_id: str
) -> str:
    '''Send a message when the command /start is issued.'''
    products = get_all_products(
        url='https://api.moltin.com/pcm/products/',
        token=context.bot_data.get('moltin_token')
    )
    context.bot.send_message(
        text='Please choose:',
        chat_id=chat_id,
        reply_markup=get_menu_keyboard(products)
    )
    if update.callback_query:
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
    return 'HANDLE_MENU'


def handle_menu(
    update: telegram.update.Update,
    context: CallbackContext,
    chat_id: str
) -> str:
    '''Telegram-bot menu handler.'''
    query = update.callback_query
    token = context.bot_data.get('moltin_token')
    if query.data == 'cart':
        cart_items = get_cart_items(cart_id=chat_id, token=token)
        return send_cart_content(
            update=update,
            context=context,
            chat_id=chat_id,
            cart_items=cart_items
        )
    product_id = context.user_data['product_id'] = query.data
    product = get_product(product_id=product_id, token=token)
    main_image_url = get_product_main_image(
        product_id=product_id,
        token=token
    )
    stock = get_product_stock(product_id=product_id, token=token)
    reply_text = f'''\
    {product["attributes"]["name"]}

    {product["meta"]["display_price"]["without_tax"]["formatted"]} per kg
    {stock["available"]} kg on stock
    {product["attributes"]["description"]}
    '''
    context.bot.send_photo(
        chat_id=chat_id,
        photo=main_image_url,
        caption=dedent(reply_text),
        reply_markup=get_order_keyboard()
    )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=query.message.message_id
    )
    return 'HANDLE_DESCRIPTION'


def handle_description(
    update: telegram.update.Update,
    context: CallbackContext,
    chat_id: str
) -> str:
    '''Return to products menu.'''
    query_data = update.callback_query.data
    token = context.bot_data.get('moltin_token')
    if query_data == 'back':
        return start(update=update, context=context)
    elif query_data.isdigit():
        if not context.user_data.get('cart_id'):
            create_cart(chat_id=chat_id, token=token)
            context.user_data['cart_id'] = chat_id
        add_product_to_cart(
            token=token,
            cart_id=chat_id,
            product_id=context.user_data.get('product_id'),
            quantity=query_data
        )
        return 'HANDLE_DESCRIPTION'
    elif query_data == 'cart':
        cart_items = get_cart_items(cart_id=chat_id, token=token)
        return send_cart_content(
            update=update,
            context=context,
            chat_id=chat_id,
            cart_items=cart_items
        )


def handle_cart(
    update: telegram.update.Update,
    context: CallbackContext,
    chat_id: str
) -> str:
    '''Return to products menu.'''
    query_data = update.callback_query.data
    token = context.bot_data.get('moltin_token')
    if query_data == 'back':
        start(update=update, context=context)
        return 'HANDLE_MENU'
    elif query_data == 'pay':
        context.bot.send_message(
            text='Введите ваш e-mail',
            chat_id=chat_id
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'WAITING_EMAIL'
    else:
        cart = delete_cart_item(
            cart_id=chat_id,
            product_id=query_data,
            token=token
        )
        if not cart['data']:
            context.user_data['cart_id'] = None
        return send_cart_content(
            update=update,
            context=context,
            chat_id=chat_id,
            cart_items=cart
        )


def send_cart_content(
    update: telegram.update.Update,
    context: CallbackContext,
    chat_id: str,
    cart_items: dict
) -> str:
    '''Send cart content to telegram.'''
    if not context.user_data.get('cart_id'):
        context.bot.send_message(
            text='Корзина пуста',
            chat_id=chat_id,
            reply_markup=get_back_to_menu_keyboard()
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.callback_query.message.message_id
        )
        return 'HANDLE_CART'
    cart_item_texts = list()
    for cart_item in cart_items['data']:
        price_without_tax = cart_item['meta']['display_price']['without_tax']
        formatted_price = price_without_tax["value"]["formatted"]
        text = f'''\
        {cart_item["name"]}
        {cart_item["description"]}
        {price_without_tax["unit"]["formatted"]} per kg
        {cart_item["quantity"]}kg in cart for {formatted_price}
        '''
        cart_item_texts.append(dedent(text))
    cost = cart_items["meta"]["display_price"]["without_tax"]["formatted"]
    total_cost = f'\nTotal: {cost}'
    cart_item_texts.append(total_cost)
    text = '\n'.join(cart_item_texts)
    context.bot.send_message(
        text=text,
        chat_id=chat_id,
        reply_markup=get_cart_keyboard(cart_items['data'])
    )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )
    return 'HANDLE_CART'


def handle_email(
    update: telegram.update.Update,
    context: CallbackContext,
    chat_id: str
) -> str:
    '''Handle user e-mail.'''
    email = update.message.text
    token = context.bot_data.get('moltin_token')
    name = (
        f'{update.message.chat.last_name} {update.message.chat.first_name}'
        f' ({chat_id})'
    )
    customer_id = context.user_data.get('customer_id')
    if not customer_id:
        customer = create_customer(
            token=token,
            name=name,
            email=email,
            password=str(chat_id)
        )
        context.user_data['customer_id'] = customer['data']['id']
        context.bot.send_message(
            text=f'Вы указали следующий e-mail: {email}',
            chat_id=chat_id,
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.message.message_id
        )
        context.bot.delete_message(
            chat_id=chat_id,
            message_id=update.message.message_id - 1
        )
        return 'START'
    customer = update_customer(
        token=token,
        customer_id=customer_id,
        email=email
    )
    context.bot.send_message(
        text=f'Вы указали следующий e-mail: {email}',
        chat_id=chat_id,
    )
    context.bot.delete_message(
        chat_id=chat_id,
        message_id=update.callback_query.message.message_id
    )
    return 'START'


def main() -> None:
    '''Start the Telegram-bot.'''
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    load_dotenv()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    tg_token = os.getenv('TG_TOKEN')
    db_host = os.getenv('DB_HOST', default='localhost')
    db_port = os.getenv('DB_PORT', default=6379)
    db_password = os.getenv('DB_PASSWORD', default=None)

    redis_db = redis.Redis(
        host=db_host,
        port=db_port,
        password=db_password,
        decode_responses=True
    )

    updater = Updater(tg_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(
        CallbackQueryHandler(
            partial(
                handle_users_reply,
                db=redis_db,
                client_id=client_id,
                client_secret=client_secret
            )
        )
    )
    dispatcher.add_handler(
        MessageHandler(
            Filters.text,
            partial(
                handle_users_reply,
                db=redis_db,
                client_id=client_id,
                client_secret=client_secret
            )
        )
    )
    dispatcher.add_handler(
        CommandHandler(
            'start',
            partial(
                handle_users_reply,
                db=redis_db,
                client_id=client_id,
                client_secret=client_secret
            )
        )
    )
    updater.start_polling()


if __name__ == '__main__':
    main()
