import requests

BASE_URL = 'http://1.tcp.cpolar.cn:20272'

def get_accounts():
    response = requests.get(f'{BASE_URL}/accounts')
    return response.json()

def create_account(account):
    response = requests.post(f'{BASE_URL}/accounts', json=account)
    return response.json()

def update_account(account_id, account):
    response = requests.put(f'{BASE_URL}/accounts/{account_id}', json=account)
    return response.json()

def delete_account(account_id):
    response = requests.delete(f'{BASE_URL}/accounts/{account_id}')
    return response.json()

def verify_admin(username, password):
    response = requests.post(f'{BASE_URL}/verify_admin', json={'username': username, 'password': password})
    return response.json().get('status') == 'success'
