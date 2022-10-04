from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_menu_keyboard(products: list[dict]) -> InlineKeyboardMarkup:
    '''Return telegram-bot inline keyboard for main menu.'''
    keyboard = list()
    for product in products:
        product_name = product['attributes']['name']
        keyboard.append(
            [InlineKeyboardButton(product_name, callback_data=product['id'])]
        )
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='cart')])
    return InlineKeyboardMarkup(keyboard)


def get_order_keyboard() -> InlineKeyboardMarkup:
    '''Return telegram-bot inline keyboard for product ordering.'''
    keyboard = [
        [
            InlineKeyboardButton('1 kg', callback_data=1),
            InlineKeyboardButton('5 kg', callback_data=5),
            InlineKeyboardButton('10 kg', callback_data=10)
        ],
        [InlineKeyboardButton('Корзина', callback_data='cart')],
        [InlineKeyboardButton('Назад', callback_data='back')]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cart_keyboard(cart_items: list[dict]) -> InlineKeyboardMarkup:
    '''Return telegram-bot inline keyboard for cart.'''
    keyboard = list()
    for cart_item in cart_items:
        keyboard.append(
            [InlineKeyboardButton(
                f'Убрать из корзины {cart_item["name"]}',
                callback_data=cart_item['id']
            )]
        )
    keyboard.append(
        [InlineKeyboardButton('Оплатить', callback_data='pay')]
    )
    keyboard.append(
        [InlineKeyboardButton('В меню', callback_data='back')]
    )
    return InlineKeyboardMarkup(keyboard)


def get_back_to_menu_keyboard() -> InlineKeyboardMarkup:
    '''Return telegram-bot inline back to menu keyboard.'''
    keyboard = [[InlineKeyboardButton('В меню', callback_data='back')]]
    return InlineKeyboardMarkup(keyboard)
