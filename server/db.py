# -*- coding: utf-8 -*-
import sqlite3
import json
import os

def init_db():
    db_file = os.path.join(os.path.dirname(__file__), 'accounts.db')
    schema_file = os.path.join(os.path.dirname(__file__), '../database/schema.sql')
    
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    
    # 尝试添加缺失的列（如果不存在）
    try:
        c.execute("ALTER TABLE accounts ADD COLUMN added_time TEXT")
    except sqlite3.OperationalError:
        pass  # 列已经存在

    try:
        c.execute("ALTER TABLE accounts ADD COLUMN remark TEXT")
    except sqlite3.OperationalError:
        pass  # 列已经存在

    with open(schema_file) as f:
        conn.executescript(f.read())
    conn.close()

def add_account(data):
    db_file = os.path.join(os.path.dirname(__file__), 'accounts.db')
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    print("Adding account to database: {}".format(data))
    c.execute("INSERT INTO accounts (username, password, gpt_status, midjourney_status, custom_platforms, usage_count, added_time, remark) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (data['username'], data['password'], data['gpt_status'], data['midjourney_status'], json.dumps(data['custom_platforms']), data['usage_count'], data['added_time'], data['remark']))
    conn.commit()
    conn.close()

def get_accounts():
    db_file = os.path.join(os.path.dirname(__file__), 'accounts.db')
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    c.execute("SELECT * FROM accounts")
    rows = c.fetchall()
    accounts = []
    for row in rows:
        accounts.append({
            'id': row[0],
            'username': row[1],
            'password': row[2],
            'gpt_status': bool(row[3]),
            'midjourney_status': bool(row[4]),
            'custom_platforms': json.loads(row[5]),
            'usage_count': row[6],
            'added_time': row[7],
            'remark': row[8]
        })
    conn.close()
    return accounts

def update_account(account_id, data):
    db_file = os.path.join(os.path.dirname(__file__), 'accounts.db')
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    print("Updating account {} in database: {}".format(account_id, data))
    c.execute("UPDATE accounts SET password = ?, gpt_status = ?, midjourney_status = ?, custom_platforms = ?, usage_count = ?, added_time = ?, remark = ? WHERE id = ?",
              (data['password'], data['gpt_status'], data['midjourney_status'], json.dumps(data['custom_platforms']), data['usage_count'], data['added_time'], data['remark'], account_id))
    conn.commit()
    conn.close()

def delete_account(account_id):
    db_file = os.path.join(os.path.dirname(__file__), 'accounts.db')
    conn = sqlite3.connect(db_file)
    c = conn.cursor()
    print("Deleting account {} from database".format(account_id))
    c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
