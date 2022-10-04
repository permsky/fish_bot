import requests


def get_token(client_id: str, client_secret: str) -> str:
    '''Get authorization token.'''
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }
    response = requests.post(
        url='https://api.moltin.com/oauth/access_token',
        data=payload
    )
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


def get_product_main_image(product_id: str, token: str) -> str:
    '''Download product main image.'''
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(
        url=(
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
    return response.json()['data']['link']['href']


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
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': int(quantity),
        }
    }
    response = requests.post(
        url=url,
        headers=headers,
        json=payload
    )
    response.raise_for_status()
    return response.json()


def get_cart_items(cart_id: str, token: str) -> dict:
    '''Get cart items.'''
    response = requests.get(
        url=f'https://api.moltin.com/v2/carts/{cart_id}/items',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()


def create_cart(chat_id: str, token: str) -> str:
    '''Create cart.'''
    response = requests.get(
        url=f'https://api.moltin.com/v2/carts/{chat_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()


def get_product_stock(product_id: str, token: str) -> dict:
    '''Get product's stock information.'''
    response = requests.get(
        url=f'https://api.moltin.com/v2/inventories/{product_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()['data']


def delete_cart_item(cart_id: str, product_id: str, token: str) -> dict:
    '''Delete certain cart item.'''
    response = requests.delete(
        url=f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    response.raise_for_status()
    return response.json()


def create_customer(
    token: str,
    name: str,
    email: str,
    password: str
) -> dict:
    '''Create moltin customer.'''
    customer_creds = {
        'data': {
            'type': 'customer',
            'name': name,
            'email': email,
            'password': password
        }
    }
    response = requests.post(
        url='https://api.moltin.com/v2/customers',
        headers={'Authorization': f'Bearer {token}'},
        json=customer_creds
    )
    response.raise_for_status()
    return response.json()


def update_customer(token: str, customer_id: str, email: str) -> dict:
    '''Get customer by id.'''
    response = requests.put(
        url=f'https://api.moltin.com/v2/customers/{customer_id}',
        headers={'Authorization': f'Bearer {token}'},
        json={'data': {'type': 'customer', 'email': email}}
    )
    response.raise_for_status()
    return response.json()
