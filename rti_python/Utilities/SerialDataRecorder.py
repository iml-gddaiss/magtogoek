import getopt
import os
import logging
import sys
import socket
import threading

from Comm.AdcpSerialPortServer import AdcpSerialPortServer

logger = logging.getLogger("Ensemble File Report")
logger.setLevel(logging.DEBUG)
FORMAT = '[%(asctime)-15s][%(levelname)s][%(funcName)s] %(message)s'
logging.basicConfig(format=FORMAT)


class SerialDataRecorder:
    """
    Record the serial data.  This will work as a data logger.
    It will record the serial data and write it to the file path given.
    If no file path is given it will write it in the same directory as
    the application is run.
    """

    # Max file size.  16mbs
    MAX_FILE_SIZE = 1048576 * 16

    # Recorder File name
    RECORDER_FILE_NAME = "Adcp"

    def __init__(self, verbose=False):
        self.serial_server = None
        self.serial_server_thread = None
        self.comm_port = ""
        self.baud = 0
        self.tcp_port = 0
        self.verbose = verbose
        self.folder_path = ''

        self.raw_serial_socket = None
        self.isAlive = True
        self.file = None
        self.file_size = 0
        self.file_name = self.RECORDER_FILE_NAME

    def connect(self, comm_port, baud, folder_path, file_name, tcp_port=55056):
        """
        Connect to the serial port server to receive data.
        :param comm_port: Comm port to connect to.
        :param baud: Baud Rate.
        :param folder_path: Folder path to store the recorded data.
        :param file_name: File name used to create a new file.
        :param tcp_port: TCP Port to receive the data.
        """
        self.comm_port = comm_port
        self.baud = baud
        self.tcp_port = tcp_port
        self.folder_path = folder_path
        self.file_name = file_name
        self.serial_server = AdcpSerialPortServer(tcp_port,
                                                  comm_port,
                                                  baud)

        # Start a tcp connection to monitor incoming data and record
        self.serial_server_thread = threading.Thread(name='AdcpWriter',
                                                     target=self.create_raw_serial_socket(self.tcp_port))
        self.serial_server_thread.start()

    def create_raw_serial_socket(self, port):
        """
        Connect to the ADCP serial server.  This TCP server outputs data from
        the serial port.  Start reading the data.
        """
        try:
            # Create a file
            self.create_file_writer()

            # Create socket
            self.raw_serial_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.raw_serial_socket.connect(('localhost', int(port)))
            self.raw_serial_socket.settimeout(1)    # Set timeout to stop thread if terminated
        except ConnectionRefusedError as err:
            logger.error("Serial Send Socket: ", err)
        except Exception as err:
            logger.error('Serial Send Socket: ", Error Opening socket', err)

        # Start to read the raw data
        self.read_tcp_socket()

    def read_tcp_socket(self):
        """
        Read the data from the TCP port.  This is the raw data from the serial port.
        Then write this data to the file.
        """
        while self.isAlive:
            try:
                # Read data from socket
                data = self.raw_serial_socket.recv(4096)

                # If data exist process
                if len(data) > 0:
                    # Write the data to the file
                    self.file.write(data)

                    # Keep track of the file size
                    self.file_size += len(data)

                    # Limit the output prompt
                    #if self.file_size % 5 == 0:
                    #    print('.', end="", flush=True)

                    # Check the file size to see if a new file needs to be created
                    if self.file_size > self.MAX_FILE_SIZE:
                        self.close_file_write()                 # Close this file
                        self.create_file_writer()               # Open a new file

            except socket.timeout:
                # Just a socket timeout, continue on
                pass
            except Exception as e:
                logger.error("Exception in reading data.", e)
                self.stop_adcp_server()

        print("Read Thread turned off")

    def create_file_writer(self):
        """
        Create a file writer.  This will open the file and have it ready
        to write data to the file.
        """
        file_path = self.get_new_file()
        logger.debug("Open File name: " + file_path)

        self.file_size = 0
        self.file = open(file_path, 'wb')

    def close_file_write(self):
        """
        Close the file.
        """
        logger.debug("Close the file")
        self.file.close()

    def get_new_file(self):
        """
        Create a new file path.  If the file exist,
        update the index until a new unique name is created.
        :return: New File name.
        """
        index = 0
        file_name = self.file_name + str(index)

        if not os.path.isdir(self.folder_path):
            os.makedirs(self.folder_path)

        # Create a new file name
        file_path = os.path.join(self.folder_path, file_name + ".ens")

        # Continue to create a file until a new file name is found
        while os.path.exists(file_path):
            index += 1
            file_name = self.file_name + str(index)
            file_path = os.path.join(self.folder_path, file_name + ".ens")

        return file_path

    def stop_adcp_server(self):
        """
        Stop the ADCP Serial TCP server
        """
        # Stop the thread loop
        self.isAlive = False

        if self.serial_server is not None:
            self.serial_server.close()
            logger.debug("serial server stopped")
        else:
            logger.debug('No serial connection')

        # Close the socket
        self.raw_serial_socket.close()

        # Stop the server thread
        if self.serial_server_thread is not None:
            self.serial_server_thread.join()

        # Close the open file
        self.close_file_write()

        logger.debug("Stop the Recorder")


def main(argv):
    comm_port = ''
    baud = '115200'
    tcp_port = '55056'
    folder_path = 'recorder'
    verbose = False
    file_name = "Adcp"
    try:
        opts, args = getopt.getopt(argv, "hlvc:b:f:p:n:", ["comm=", "baud=", "folder=", "name=", "tcp=", "verbose"])
    except getopt.GetoptError:
        print('SerialDataRecorder.py -c <comm> -b <baud> -f <folder> -p <tcp> -n <file_name> -v')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('usage: SerialDataRecorder.py ')
            print('-c <comm>\t : Serial Comm Port.  Use -l to list all the ports.')
            print('-b <baud>\t : Serial Baud Rate. Default 115200.')
            print('-p <tcp>\t : TCP Port to output the serial data.  Default 55056.  Change if used already.')
            print('-f <folder>\t : Folder path to store the serial data.  Default is same path as application.')
            print('-n <file_name>\t : File name for the files.  Default is "Adcp.')
            print('-v\t : Verbose output.')
            print('Utilities:')
            print('-l\t : Print all available Serial Ports')
            sys.exit()
        elif opt == '-l':
            AdcpSerialPortServer.list_serial_ports()
            sys.exit()
        elif opt in ('-c', "--comm"):
            comm_port = arg
        elif opt in ("-b", "--baud"):
            baud = arg
        elif opt in ("-f", "--folder"):
            folder_path = arg
        elif opt in ("-p", "--tcp"):
            tcp_port = arg
        elif opt in ("-n", "--name"):
            file_name = arg
        elif opt in ("-v", "--verbose"):
            verbose = True
            print("Verbose ON")
    print('Comm Port: ', comm_port)
    print('Baud Rate: ', baud)
    print('TCP Port: ', tcp_port)
    print('Folder Path: ', folder_path)
    print('File Name: ', file_name)
    print("Available Serial Ports:")
    serial_list = AdcpSerialPortServer.list_serial_ports()

    # Verify a good serial port was given
    if comm_port in serial_list:
        # Run serial port
        sdr = SerialDataRecorder(verbose).connect(comm_port, baud, folder_path, file_name, tcp_port)
        sdr.stop_adcp_server()
    else:
        print("----------------------------------------------------------------")
        print("BAD SERIAL PORT GIVEN")
        print("Please use -c to give a good serial port.")
        print("-l will give you a list of all available serial ports.")

if __name__ == "__main__":
    main(sys.argv[1:])

