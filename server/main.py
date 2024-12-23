# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
import sqlite3
from db import init_db, add_account, get_accounts, update_account, delete_account
from threading import Thread
from flask import copy_current_request_context
from datetime import datetime
import json

app = Flask(__name__)
init_db()

@app.route('/accounts', methods=['GET'])
def list_accounts():
    @copy_current_request_context
    def run():
        accounts = get_accounts()
        for account in accounts:
            if 'added_time' not in account:
                account['added_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(accounts)

    def thread_func():
        result = run()
        return result

    thread = Thread(target=thread_func)
    thread.start()
    thread.join()
    return thread_func()

@app.route('/accounts', methods=['POST'])
def create_account():
    data = request.json
    print("Received request to create account: {}".format(data))
    @copy_current_request_context
    def run():
        add_account(data)
        return jsonify({'status': 'success'})

    def thread_func():
        result = run()
        return result

    print("Starting thread to add account")
    thread = Thread(target=thread_func)
    thread.start()
    thread.join()  # Wait for the thread to finish
    print("Thread to add account finished")
    return jsonify({'status': 'success'})  # Do not call thread_func() again

@app.route('/accounts/<int:account_id>', methods=['PUT'])
def edit_account(account_id):
    data = request.json
    data.setdefault('custom_platforms', {})
    data.setdefault('remark', '')
    print("Received request to update account {}: {}".format(account_id, data))
    @copy_current_request_context
    def run():
        update_account(account_id, data)
        return jsonify({'status': 'success'})

    def thread_func():
        result = run()
        return result

    thread = Thread(target=thread_func)
    thread.start()
    thread.join()
    return thread_func()

@app.route('/accounts/<int:account_id>', methods=['DELETE'])
def delete_account_route(account_id):
    print("Received request to delete account {}".format(account_id))
    @copy_current_request_context
    def run():
        delete_account(account_id)
        return jsonify({'status': 'success'})

    def thread_func():
        result = run()
        return result

    thread = Thread(target=thread_func)
    thread.start()
    thread.join()
    return thread_func()

@app.route('/verify_admin', methods=['POST'])
def verify_admin_route():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    if username == 'endless-shengyangw' and password == 'F42a9d88':
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'fail'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=12345)
