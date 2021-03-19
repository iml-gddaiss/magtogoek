import serial
from serial import threaded
import sys
import glob
import time
import logging


class AdcpSerialPort:
    def __init__(self,
                 port: str,
                 baud: int = 115200,
                 bytesize: int = serial.EIGHTBITS,
                 parity: int = serial.PARITY_NONE,
                 stopbits: int = serial.STOPBITS_ONE):

        self.raw_serial = serial.Serial(port=port,
                                        baudrate=baud,
                                        timeout=1,
                                        bytesize=bytesize,
                                        parity=parity,
                                        stopbits=stopbits)

        if not self.raw_serial.is_open:
            self.raw_serial.open()
            logging.error("Serial Port could not be opened")
        else:
            logging.debug("Serial Port Connected")

        logging.debug(self.raw_serial.get_settings())

        #self.protocol = serial.threaded.ReaderThread(self.serial, AdcpSerialPort.ReadHandler)

    def send_break(self, break_len=1.25):
        self.raw_serial.send_break(break_len)

    def disconnect(self):
        self.raw_serial.close()

    def is_open(self):
        return self.raw_serial.is_open

    def readline(self):
        self.raw_serial.readline()

    def read(self, size: int):
        return self.raw_serial.read(size)

    def write(self, data):
        self.raw_serial.write(data)

    def in_waiting(self):
        return self.raw_serial.in_waiting

    def start_pinging(self):
        self.send_cmd("START")

    def stop_pinging(self):
        # Send a BREAK
        self.send_break()

        # Wait
        time.sleep(1.0)

        # Send STOP command
        self.send_cmd("STOP")

    def send_cmd(self, cmd, use_cr: bool=True):
        # Add a carriage return to the end of the command
        if use_cr:
            cmd = cmd + '\r'

        # Write the command to the serial port
        self.raw_serial.write(cmd.encode())

    class ReadHandler(serial.threaded.LineReader):
        def __init__(self):
            super(AdcpSerialPort.ReadHandler, self).__init__()
            self.received_lines = []

        def handle_line(self, data):
            self.received_lines.append(data)

        def connection_made(self, transport):
            self.received_lines.append(transport)
            logging.debug("Connection made at: " + str(transport))

        def connection_lost(self, exc):
            self.received_lines.append(exc)
            logging.debug("Connection lost: " + str(exc))


def get_baud_rates():
    """
    List of baud rates.
    :return: List of available baud rates.
    """
    result = []
    result.append("2400")
    result.append("4800")
    result.append("9600")
    result.append("19200")
    result.append("38400")
    result.append("57600")
    result.append("115200")
    result.append("230400")
    result.append("460800")
    result.append("500000")
    result.append("576000")
    result.append("921600")

    return result


def get_serial_ports():
    """
    Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result