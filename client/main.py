from ui import AccountManagementApp
from PyQt5 import QtWidgets

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    mainWin = AccountManagementApp()
    mainWin.show()
    app.exec_()
