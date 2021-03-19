from log import logger
import socket


class EnsembleReader:
    """
    Read in data from the given TCP.  Then decode the data
    and pass it on to another TCP port
    """

    def __init__(self, port):
        # Open a TCP port to read in the ensemble data
        self.port = port
        self.is_alive = True
        self.socket = None
        self.reconnect(port)
        self.read()

    def reconnect(self, tcp_port):
        """
        Connect to the server.
        """
        logger.debug("Ensemble Reader: ", tcp_port)

        self.is_alive = True

        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect(('localhost', int(tcp_port)))
        except ConnectionRefusedError as err:
            print("EnsembleReader: ", err)
            #sys.exit(2)
        except socket.error as err:
            print('EnsembleReader: Error Opening socket ', err)
            #sys.exit(2)

    def read(self):
        """
        Read data from the serial port
        """
        try:
            while self.is_alive:
                # Receive a response
                response = self.socket.recv()
                #print('"%s"' % response)

                # Decode the ensemble data

                # Reconnect
                if len(response) == 0:
                    print("Disconnected")

                    # Close the socket
                    self.close()

                    # Reconnect to the server
                    self.reconnect(self.port)

                    # Try to read again
                    self.read()

        except KeyboardInterrupt:
            # Ctrl-C will stop the application
            pass
        except:
            pass

        # Close the socket
        self.close()

    def close(self):
        """
        Close the socket.
        """
        self.is_alive = False

        self.socket.close()


