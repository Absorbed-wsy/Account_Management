from PyQt5 import QtWidgets, QtGui, QtCore
from api import get_accounts, create_account, update_account, delete_account, verify_admin
from datetime import datetime
import threading
import re
import time

class Led(QtWidgets.QWidget):
    def __init__(self, parent=None, size=20, on_color=QtGui.QColor('red'), off_color=QtGui.QColor('green')):
        super(Led, self).__init__(parent)
        self.setFixedSize(size, size)
        self.on_color = on_color
        self.off_color = off_color
        self.state = False

    def set_state(self, state):
        self.state = state
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        color = self.on_color if self.state else self.off_color
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(0, 0, self.width(), self.height())

class AccountManagementApp(QtWidgets.QWidget):
    accounts_loaded = QtCore.pyqtSignal(list)
    status_message = QtCore.pyqtSignal(str)
    add_lock = threading.Lock()
    fetch_lock = threading.Lock()

    def __init__(self):
        super().__init__()
        print("Initializing UI")
        self.admin_logged_in = False
        self.init_ui()
        self.accounts_loaded.connect(self.on_accounts_loaded)
        self.status_message.connect(self.show_message)
        self.refresh_account_list()
        self.start_auto_refresh()

    def init_ui(self):
        self.setWindowTitle('Account Management Tool')
        self.resize(1024, 768)  # 初始窗口大小
        self.center()  # 窗口居中

        layout = QtWidgets.QVBoxLayout()

        # 创建上方操作区
        self.top_frame = QtWidgets.QHBoxLayout()
        layout.addLayout(self.top_frame)

        self.username_label = QtWidgets.QLabel("Username (Email)")
        self.top_frame.addWidget(self.username_label)
        self.username_entry = QtWidgets.QLineEdit()
        self.top_frame.addWidget(self.username_entry)

        self.password_label = QtWidgets.QLabel("Password (min 8 characters)")
        self.top_frame.addWidget(self.password_label)
        self.password_entry = QtWidgets.QLineEdit()
        self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)
        self.top_frame.addWidget(self.password_entry)

        self.added_time_label = QtWidgets.QLabel("Added Time")
        self.top_frame.addWidget(self.added_time_label)
        self.added_time_entry = QtWidgets.QDateTimeEdit()
        self.added_time_entry.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.added_time_entry.setDateTime(QtCore.QDateTime.currentDateTime())
        self.top_frame.addWidget(self.added_time_entry)

        self.remark_label = QtWidgets.QLabel("Remark")
        self.top_frame.addWidget(self.remark_label)
        self.remark_entry = QtWidgets.QLineEdit()
        self.top_frame.addWidget(self.remark_entry)

        self.add_button = QtWidgets.QPushButton("Add Account")
        self.add_button.clicked.connect(self.add_account)
        self.top_frame.addWidget(self.add_button)

        self.refresh_button = QtWidgets.QPushButton('Refresh')
        self.refresh_button.clicked.connect(self.refresh_account_list)
        self.top_frame.addWidget(self.refresh_button)

        self.login_button = QtWidgets.QPushButton('Login')
        self.login_button.clicked.connect(self.show_login_dialog)
        self.top_frame.addWidget(self.login_button)

        # 创建账号表格
        self.account_table = QtWidgets.QTableWidget()
        self.account_table.setColumnCount(9)
        self.account_table.setHorizontalHeaderLabels(['Username', 'Password', 'GPT', 'Midjourney', 'Usage Count', 'Added Time', 'Remark', 'Actions', 'Delete'])
        self.account_table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.account_table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # 设置用户名列的宽度为内容适应
        layout.addWidget(self.account_table)

        self.setLayout(layout)

    def center(self):
        """使窗口在屏幕中央显示"""
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)

    def start_auto_refresh(self):
        """每10分钟自动刷新一次"""
        def auto_refresh():
            while True:
                time.sleep(600)  # 每10分钟刷新一次
                self.refresh_account_list()

        threading.Thread(target=auto_refresh, daemon=True).start()

    def show_login_dialog(self):
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.admin_logged_in = True
            self.login_button.setStyleSheet("background-color: green; color: white;")

    def refresh_account_list(self):
        if not self.fetch_lock.acquire(blocking=False):
            print("Fetch accounts already in progress")
            return

        def run():
            retries = 3
            while retries > 0:
                try:
                    print("Fetching accounts")
                    accounts = get_accounts()
                    print(f"Fetched accounts: {accounts}")
                    for account in accounts:
                        if 'added_time' not in account:
                            account['added_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    sorted_accounts = self.sort_accounts(accounts)
                    self.accounts_loaded.emit(sorted_accounts)
                    break
                except Exception as e:
                    print(f"Error in fetching accounts: {e}")
                    retries -= 1
                    time.sleep(1)  # Wait for 1 second before retrying
            self.fetch_lock.release()

        threading.Thread(target=run).start()

    def sort_accounts(self, accounts):
        """排序账户列表"""
        def account_key(account):
            gpt_status = account['gpt_status']
            midjourney_status = account['midjourney_status']
            usage_count = account['usage_count']
            username = account['username']
            # 排序规则：GPT和Midjourney均可用 > 任一可用 > 均不可用（按usage_count升序）> 按用户名排序
            return (
                gpt_status and midjourney_status,
                gpt_status or midjourney_status,
                usage_count,
                username
            )

        sorted_accounts = sorted(accounts, key=account_key)
        return sorted_accounts

    def on_accounts_loaded(self, accounts):
        print("Accounts loaded")
        try:
            self.account_table.setRowCount(len(accounts))
            for row, account in enumerate(accounts):
                print(f"Processing account: {account}")
                self.account_table.setItem(row, 0, QtWidgets.QTableWidgetItem(account['username']))
                self.account_table.setItem(row, 1, QtWidgets.QTableWidgetItem(account['password']))
                
                gpt_led = Led(self, size=20)
                gpt_led.set_state(account['gpt_status'])
                self.account_table.setCellWidget(row, 2, gpt_led)
                
                midjourney_led = Led(self, size=20)
                midjourney_led.set_state(account['midjourney_status'])
                self.account_table.setCellWidget(row, 3, midjourney_led)
                
                usage_count_item = QtWidgets.QTableWidgetItem(str(account['usage_count']))
                usage_count_item.setBackground(QtGui.QColor('red') if account['usage_count'] >= 3 else QtGui.QColor('green'))
                self.account_table.setItem(row, 4, usage_count_item)

                added_time = account.get('added_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                time_diff = self.calculate_time_diff(added_time)
                self.account_table.setItem(row, 5, QtWidgets.QTableWidgetItem(time_diff))
                
                remark_button = QtWidgets.QPushButton('Edit Remark')
                remark_button.clicked.connect(lambda _, a=account: self.edit_remark(a))
                self.account_table.setCellWidget(row, 6, remark_button)

                edit_button = QtWidgets.QPushButton('Edit')
                edit_button.clicked.connect(lambda _, a=account: self.edit_account(a))
                self.account_table.setCellWidget(row, 7, edit_button)

                delete_button = QtWidgets.QPushButton('Delete')
                delete_button.clicked.connect(lambda _, a=account: self.delete_account(a))
                self.account_table.setCellWidget(row, 8, delete_button)
        except Exception as e:
            print(f"Error in loading accounts: {e}")

    def add_account(self):
        print("Adding account")
        username = self.username_entry.text()
        password = self.password_entry.text()

        # 验证用户名是否符合邮箱格式
        if not re.match(r"[^@]+@[^@]+\.[^@]+", username):
            QtWidgets.QMessageBox.warning(self, 'Invalid Username', 'The username must be a valid email address.')
            return

        # 验证密码是否不少于8位
        if len(password) < 8:
            QtWidgets.QMessageBox.warning(self, 'Invalid Password', 'The password must be at least 8 characters long.')
            return

        new_account = {
            'username': username,
            'password': password,
            'gpt_status': False,
            'midjourney_status': False,
            'custom_platforms': {},
            'usage_count': 0,
            'added_time': self.added_time_entry.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'remark': self.remark_entry.text()
        }
        
        if not self.add_lock.acquire(blocking=False):
            print("Add button is already processing")
            return
        
        self.add_button.setEnabled(False)  # Disable the button to prevent multiple clicks
        def run():
            try:
                print("Sending request to create account")
                create_account(new_account)
                print("Request sent to create account")
                self.refresh_account_list()
                self.status_message.emit("Account added successfully.")
            except Exception as e:
                print(f"Error: {e}")
                self.status_message.emit("Failed to add account.")
            finally:
                self.add_button.setEnabled(True)  # Re-enable the button
                self.add_lock.release()

        threading.Thread(target=run).start()

    def edit_account(self, account):
        print(f"Editing account: {account['username']}")
        try:
            dialog = EditAccountDialog(account)
            if dialog.exec_():
                updated_account = dialog.get_account_data()
                updated_account['username'] = account['username']  # 添加用户名
                updated_account.setdefault('custom_platforms', {})
                updated_account.setdefault('remark', '')
                def run():
                    try:
                        update_account(account['id'], updated_account)
                        sorted_accounts = self.sort_accounts(get_accounts())
                        self.accounts_loaded.emit(sorted_accounts)
                        self.status_message.emit("Account updated successfully.")
                    except Exception as e:
                        print(f"Error: {e}")
                        self.status_message.emit("Failed to update account.")
                threading.Thread(target=run).start()
        except Exception as e:
            print(f"Error: {e}")
            self.status_message.emit("Failed to update account.")

    def delete_account(self, account):
        print(f"Deleting account: {account['username']}")
        if not self.admin_logged_in:
            self.show_login_dialog()
            if not self.admin_logged_in:
                QtWidgets.QMessageBox.warning(self, 'Unauthorized', 'Only admin can delete accounts.')
                return

        reply = QtWidgets.QMessageBox.question(self, 'Confirm Delete', f'Are you sure you want to delete the account {account["username"]}?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            def run():
                try:
                    delete_account(account['id'])
                    self.refresh_account_list()
                    self.status_message.emit("Account deleted successfully.")
                except Exception as e:
                    print(f"Error: {e}")
                    self.status_message.emit("Failed to delete account.")

            threading.Thread(target=run).start()

    def calculate_time_diff(self, added_time):
        added_time_dt = datetime.strptime(added_time, '%Y-%m-%d %H:%M:%S')
        now = datetime.now()
        diff = now - added_time_dt
        return f"{diff.days} days, {diff.seconds // 3600} hours"

    def edit_remark(self, account):
        print(f"Editing remark for account: {account['username']}")
        try:
            dialog = EditRemarkDialog(account)
            if dialog.exec_():
                updated_remark = dialog.get_remark()
                account['remark'] = updated_remark
                def run():
                    try:
                        update_account(account['id'], account)
                        self.refresh_account_list()
                        self.status_message.emit("Remark updated successfully.")
                    except Exception as e:
                        print(f"Error: {e}")
                        self.status_message.emit("Failed to update remark.")
                threading.Thread(target=run).start()
        except Exception as e:
            print(f"Error: {e}")
            self.status_message.emit("Failed to update remark.")

    @QtCore.pyqtSlot(str)
    def show_message(self, message):
        QtWidgets.QMessageBox.information(self, 'Status', message)

class LoginDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Admin Login")
        layout = QtWidgets.QFormLayout(self)

        self.username_entry = QtWidgets.QLineEdit()
        layout.addRow("Username:", self.username_entry)

        self.password_entry = QtWidgets.QLineEdit()
        self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addRow("Password:", self.password_entry)

        self.login_button = QtWidgets.QPushButton("Login")
        self.login_button.clicked.connect(self.check_credentials)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def check_credentials(self):
        username = self.username_entry.text()
        password = self.password_entry.text()
        def run():
            try:
                if verify_admin(username, password):
                    self.accept()
                else:
                    self.status_message.emit("Invalid username or password.")
            except Exception as e:
                print(f"Error: {e}")
        threading.Thread(target=run).start()

class EditAccountDialog(QtWidgets.QDialog):
    def __init__(self, account):
        super().__init__()
        self.account = account
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Account")
        layout = QtWidgets.QFormLayout(self)

        self.password_entry = QtWidgets.QLineEdit(self.account['password'])
        self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addRow("Password:", self.password_entry)

        self.gpt_status_checkbox = QtWidgets.QCheckBox()
        self.gpt_status_checkbox.setChecked(self.account['gpt_status'])
        layout.addRow("GPT Status:", self.gpt_status_checkbox)

        self.midjourney_status_checkbox = QtWidgets.QCheckBox()
        self.midjourney_status_checkbox.setChecked(self.account['midjourney_status'])
        layout.addRow("Midjourney Status:", self.midjourney_status_checkbox)

        self.usage_count_entry = QtWidgets.QSpinBox()
        self.usage_count_entry.setValue(self.account['usage_count'])
        layout.addRow("Usage Count:", self.usage_count_entry)

        self.added_time_entry = QtWidgets.QDateTimeEdit()
        self.added_time_entry.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.added_time_entry.setDateTime(QtCore.QDateTime.fromString(self.account['added_time'], "yyyy-MM-dd HH:mm:ss"))
        layout.addRow("Added Time:", self.added_time_entry)

        self.remark_entry = QtWidgets.QLineEdit(self.account.get('remark', ''))
        layout.addRow("Remark:", self.remark_entry)

        self.save_button = QtWidgets.QPushButton("Save")
        self.save_button.clicked.connect(self.save_account)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def save_account(self):
        reply = QtWidgets.QMessageBox.question(self, 'Confirm Save', 'Are you sure you want to save changes?',
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.accept()

    def get_account_data(self):
        return {
            'password': self.password_entry.text(),
            'gpt_status': self.gpt_status_checkbox.isChecked(),
            'midjourney_status': self.midjourney_status_checkbox.isChecked(),
            'usage_count': self.usage_count_entry.value(),
            'added_time': self.added_time_entry.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            'remark': self.remark_entry.text(),
            'custom_platforms': self.account.get('custom_platforms', {})
        }

class EditRemarkDialog(QtWidgets.QDialog):
    def __init__(self, account):
        super().__init__()
        self.account = account
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Edit Remark")
        layout = QtWidgets.QVBoxLayout(self)

        self.remark_text = QtWidgets.QTextEdit(self.account.get('remark', ''))
        self.remark_text.setFixedWidth(400)  # 设置宽度
        layout.addWidget(self.remark_text)

        self.save_button = QtWidgets.QPushButton("Save Remark")
        self.save_button.clicked.connect(self.accept)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def get_remark(self):
        return self.remark_text.toPlainText()

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    mainWin = AccountManagementApp()
    mainWin.show()
    app.exec_()
