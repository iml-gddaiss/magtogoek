import threading
import socket
from log import logger
import abc


class ReadTcpPort:
    """
    Read data from the TCP port.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self):
        """
        Initialize the thread to read the data from the TCP port.
        """
        self.is_alive = True
        self.raw_serial_socket = None
        self.serial_server_thread = None

        # Start a tcp connection to monitor incoming data and record
        #self.serial_server_thread = threading.Thread(name='AdcpWriter', target=self.create_raw_serial_socket(tcp_port))
        #self.serial_server_thread.start()
        #self.create_raw_serial_socket(tcp_port)

    def connect(self, port):
        """
        Connect to the ADCP serial server.  This TCP server outputs data from
        the serial port.  Start reading the data.
        """
        try:
            # Create socket
            self.raw_serial_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.raw_serial_socket.connect(('localhost', int(port)))
            self.raw_serial_socket.settimeout(1)    # Set timeout to stop thread if terminated
            logger.debug('Start TCP socket')

            # Start to read the raw data
            #self.read_tcp_socket()
            self.serial_server_thread = threading.Thread(target=self.read_tcp_socket())
            self.serial_server_thread.start()
            logger.debug('Read TCP socket')
        except ConnectionRefusedError as err:
            logger.error("Serial Send Socket: ", err)
            exit()
        except Exception as err:
            logger.error('Serial Send Socket: ", Error Opening socket', err)
            exit()

    def read_tcp_socket(self):
        """
        Read the data from the TCP port.  This is the raw data from the serial port.
        """
        logger.debug('Start reading TCP port')
        while self.is_alive:
            try:
                # Read data from socket
                data = self.raw_serial_socket.recv(4096)

                # If data exist process
                if len(data) > 0:
                    self.process(data)

            except socket.timeout:
                # Just a socket timeout, continue on
                pass
            except Exception as e:
                logger.error("Exception in reading data.", e)
                self.disconnect()

        print("Read Thread turned off")

    def disconnect(self):
        """
        Stop the ADCP Serial TCP server
        """
        # Stop the thread loop
        self.is_alive = False

        logger.debug("Stop TCP port")

        # Close the socket
        self.raw_serial_socket.close()

    @abc.abstractmethod
    def process(self, data):
        """
        Abstract method to overload to process the data
        received.
        :param data: Data from the TCP port.
        :return:
        """
        #logger.debug(str(data))