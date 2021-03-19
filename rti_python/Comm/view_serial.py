import glob
import socket
import sys
import threading
import logging

import serial
from PySide2 import QtCore, QtGui, QtWidgets

from Codecs.AdcpCodec import AdcpCodec
from Comm.AdcpSerialPortServer import AdcpSerialPortServer

import configparser
settings = configparser.ConfigParser()
settings._interpolation = configparser.ExtendedInterpolation()
settings.read('../settings.ini')

logger = logging.getLogger("Ensemble File Report")
logger.setLevel(logging.DEBUG)
FORMAT = '[%(asctime)-15s][%(levelname)s][%(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)

class view_serial(QtWidgets.QWidget):
    """
    Create the QT display
    """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        # Global variables

        self.serial_server = None
        self.raw_serial_socket = None
        self.raw_serial_alive = False
        self.ensemble_reader_thread = None
        self.adcp_writer_thread = None
        self.serial_buffer = ""

        raw_serial_tcp_port = settings.get('SerialServerSection', 'RawSerialTcpPort')
        ens_udp_port = settings.get('SerialServerSection', 'JsonEnsUdpPort')

        # QT GUI

        self.tcp_port_combobox = QtWidgets.QComboBox()
        self.tcp_port_combobox.setEditable(True)
        self.tcp_port_combobox.addItems([raw_serial_tcp_port, ""])

        self.ens_udp_port_combobox = QtWidgets.QComboBox()
        self.ens_udp_port_combobox.setEditable(True)
        self.ens_udp_port_combobox.addItems([ens_udp_port, ""])

        self.comm_port_combobox = QtWidgets.QComboBox()
        self.comm_port_combobox.addItems(self.serial_ports())

        self.comm_baud_combobox = QtWidgets.QComboBox()
        self.comm_baud_combobox.setEditable(True)
        self.comm_baud_combobox.addItems(["921600", "115200", "19200", ""])
        self.comm_baud_combobox.setCurrentIndex(1)

        connect = QtWidgets.QPushButton("Connect")
        connect.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
        connect.clicked.connect(self.start_adcp_server)

        disconnect = QtWidgets.QPushButton("Reconnect")
        disconnect.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
        disconnect.clicked.connect(self.reconnect_adcp_server)

        self.command_txtbox = QtWidgets.QLineEdit()

        send_cmd_btn = QtWidgets.QPushButton("Send")
        #send_cmd_btn.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
        send_cmd_btn.clicked.connect(self.send_cmd_adcp_server)

        send_break_btn = QtWidgets.QPushButton("BREAK")
        #send_break_btn.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
        send_break_btn.clicked.connect(self.send_break_adcp_server)

        #quit = QtWidgets.QPushButton("Quit")
        #quit.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
        #self.connect(quit, QtCore.SIGNAL("clicked()"),
        #             QtWidgets.qApp, QtCore.SLOT("quit()"))

        self.serial_txtbox = QtWidgets.QTextEdit()
        self.serial_txtbox.setMinimumHeight(500)

        clear_btn = QtWidgets.QPushButton("Clear")
        #send_break_btn.setFont(QtGui.QFont("Times", 18, QtGui.QFont.Bold))
        clear_btn.clicked.connect(self.clear_serial)

        # Add Widgets
        gridLayout = QtWidgets.QGridLayout()
        gridLayout.addWidget(self.tcp_port_combobox, 0, 0)
        gridLayout.addWidget(self.ens_udp_port_combobox, 0, 1)
        gridLayout.addWidget(self.comm_port_combobox, 1, 0)
        gridLayout.addWidget(self.comm_baud_combobox, 1, 1)
        gridLayout.addWidget(connect, 2, 0)
        gridLayout.addWidget(disconnect, 2, 1)
        gridLayout.addWidget(self.command_txtbox, 3, 0)
        gridLayout.addWidget(send_cmd_btn, 3, 1)
        gridLayout.addWidget(send_break_btn, 3, 2)
        gridLayout.addWidget(self.serial_txtbox, 4, 0, 2, 3)    # row, cl, rs, cs
        gridLayout.addWidget(clear_btn, 5, 2)

        # Set Spacing
        #gridLayout.setColumnStretch(1, 10)
        gridLayout.setRowStretch(4, 20)

        # Add Menu
        #self.createMenu()
        #gridLayout.setMenuBar(self.createMenu())
        gridLayout.addWidget(self.createMenu())

        # Set Window attributes
        self.setLayout(gridLayout)
        self.setWindowTitle("Echo - RoweTech Inc.")


    def createMenu(self):
        menuBar = QtWidgets.QMenuBar()

        fileMenu = QtWidgets.QMenu("File")
        exitAction = fileMenu.addAction("E&xit")
        menuBar.addMenu(fileMenu)

        #exitAction.triggered.connect(self.exit)

        return menuBar

    def closeEvent(self, event):
        """
        Override the close event for the QWidget.
        If a serial port is open, close the connection.
        """
        logger.debug('Closing serial')
        self.stop_adcp_server()

        # Close window
        event.accept()

    def start_adcp_server(self):
        """
        Start the ADCP Serial TCP server
        """
        self.serial_server = AdcpSerialPortServer(self.get_tcp_port(),
                                                  self.comm_port_combobox.currentText(),
                                                  self.get_baud())

        # Create an ensemble reader
        #self.ensemble_reader_thread = threading.Thread(name='EnsembleReader', target=EnsembleReader.EnsembleReader(self.get_tcp_port())).start()

        # Connect to serial server to send commands
        self.adcp_writer_thread = threading.Thread(name='AdcpWriter', target=self.create_raw_serial_socket(self.get_tcp_port())).start()

        logger.debug("start server")

    def create_raw_serial_socket(self, port):
        """
        Connect to the ADCP serial server.
        """
        try:
            self.raw_serial_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.raw_serial_socket.connect(('localhost', int(port)))
            self.raw_serial_socket.settimeout(1)    # Set timeout to stop thread if terminated
        except ConnectionRefusedError as err:
            logger.error("Serial Send Socket: ", err)
        except Exception as err:
            logger.error('Serial Send Socket: ", Error Opening socket', err)

        # Start a thread to read the raw data
        self.ensemble_reader_thread = ReadRawSerialThread(self.raw_serial_socket, int(self.ens_udp_port_combobox.currentText()))
        self.ensemble_reader_thread.raw_data.connect(self.on_raw_read)
        self.ensemble_reader_thread.start()

    @QtCore.Slot(object)
    def on_raw_read(self, data):
        """
        Buffer up the data received from the serial port from
        the TCP server.  Then set it to the text.
        :param data: Data received from the TCP server which came from the
                     serial port.
        """
        try:
            self.serial_buffer += bytes(data).decode()
        except Exception as err:
            #print("error decoding", err)
            # Decoding does not work for the binary data, only commands
            self.serial_buffer += str(data).strip()

        # Chop off the top portion of the message
        slicer = slice(-1130, None)
        self.serial_buffer = self.serial_buffer[slicer]

        # Set the text to the textbox
        self.serial_txtbox.setText(self.serial_buffer)

    def stop_adcp_server(self):
        """
        Stop the ADCP Serial TCP server
        """
        if self.serial_server is not None:
            self.serial_server.close()
            logger.debug("serial server stopped")
        else:
            logger.debug('No serial connection')

        # Close the socket
        self.raw_serial_socket.close()

        if self.adcp_writer_thread is not None:
            self.adcp_writer_thread.join()

        if self.ensemble_reader_thread is not None:
            #self.ensemble_reader_thread.terminate()
            #self.ensemble_reader_thread.setTerminationEnabled(True)
            self.ensemble_reader_thread.stop()

    def send_cmd_adcp_server(self):
        """
        Send the command to the socket
        """
        # Get the command from the txtbox
        cmd = self.command_txtbox.text().strip()

        # Encode the data to byte array and send to socket
        self.raw_serial_socket.send((cmd.strip()).encode())

    def send_break_adcp_server(self):
        """
        Send the BREAK command to the socket
        """
        cmd = "BREAK"

        # Encode the data to byte array and send to socket
        self.raw_serial_socket.send((cmd.strip()).encode("utf-16"))

    def reconnect_adcp_server(self):
        """
        Reconnect the serial port connection with the new
        settings.
        """
        logger.debug("reconnect")
        cmd = "RECONNECT, " + self.comm_port_combobox.currentText() + "," + self.comm_baud_combobox.currentText()

        # Encode the data to byte array and send to socket
        self.raw_serial_socket.send((cmd.strip()).encode("utf-16"))

    def get_baud(self):
        """
        Convert the baud rate from string to int.
        If an error, set the baud rate to 115200

        :returns: baud rate
        """
        try:
            baud = int(self.comm_baud_combobox.currentText())
        except Exception as err:
            logger.error("Error setting baud rate: ", err)
            self.comm_baud_combobox.setCurrentIndex(1)
            return "115200"

        return baud

    def get_tcp_port(self):
        """
        Convert the TCP port from string to int.
        If an error, set the default port to 55056

        :returns: TCP Port
        """
        try:
            port = int(self.tcp_port_combobox.currentText())
        except Exception as err:
            logger.error("Error setting TCP Port: ", err)
            self.tcp_port_combobox.setCurrentIndex(0)
            return "55056"

        return str(port)

    def clear_serial(self):
        """
        Clear the serial port display.
        """
        # Set the text to the textbox
        self.serial_txtbox.setText("")

    def find_port(self):
        """
        Finds available port for Tornado / Flask
        :return: Available port
        :rtype: int
        """

        port_attempts = 0
        while port_attempts < 1000:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(('localhost', 0))
                app_port = sock.getsockname()[1]
                sock.close()
                logger.debug("PORT: " + str(app_port))
                return app_port
            except Exception as err:
                port_attempts += 1
                logger.error(err)

        logger.error("FAILED AFTER 1000 PORT ATTEMPTS")
        sys.exit(1)


class ReadRawSerialThread(QtCore.QThread):
    """
    Create a Read raw serial data from TCP port thread.
    """

    raw_data = QtCore.Signal(object)

    def __init__(self, tcp_socket, ens_port, parent=None):
        QtCore.QThread.__init__(self, parent)
        self.socket = tcp_socket
        self.isAlive = True
        logger.debug("Read Socket thread started")

        # Initialize the ADCP Codec
        self.codec = AdcpCodec(ens_port)

        # Setup Waves
        ens_in_burst = settings.get('WavesProjectSection', 'EnsemblesInBurst')
        file_path = settings.get('WavesProjectSection', 'CaptureFilePath')
        lat = settings.get('WavesProjectSection', 'Lat')
        lon = settings.get('WavesProjectSection', 'Lon')
        bin1 = settings.get('WavesProjectSection', 'Bin1')
        bin2 = settings.get('WavesProjectSection', 'Bin2')
        bin3 = settings.get('WavesProjectSection', 'Bin3')
        self.codec.enable_waveforce_codec(int(ens_in_burst), file_path, float(lat), float(lon), int(bin1), int(bin2), int(bin3))

    def stop(self):
        """
        Stop the thread by setting the isAlive flag.
        """
        self.isAlive = False

    def run(self):
        """
        Run the loop that views the data from the serial port.
        :return:
        """
        self.exec()


    def exec(self):
        """
        Run the loop to view data from the serial port.
        Emit the data so the view can view the data.

        """
        while self.isAlive:
            try:
                # Read data from socket
                data = self.socket.recv(4096)

                # If data exist process
                if len(data) > 0:
                    self.raw_data.emit(data)

                    # Pass data to the decoder
                    self.codec.add(data)
            except socket.timeout:
                # Just a socket timeout, continue on
                pass

        logger.debug("Read Thread turned off")


