'''
Start the main view of the application.
'''

import sys

from PyQt5 import QtWidgets

from rti_python.Comm.view_serial import view_serial

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = view_serial()
    widget.setGeometry(100, 100, 500, 355)
    widget.show()

    #app.connect(quit, QtCore.SIGNAL("aboutToQuit()"),
    #            QtWidgets.qApp, QtCore.SLOT(widget.close()))
    #app.aboutToQuit.connect(widget.close())

    sys.exit(app.exec_())
