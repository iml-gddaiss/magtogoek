import glob
import threading
import serial
import logging
import sys
import codecs
import binascii
import struct
from twisted.internet import reactor, protocol, endpoints
from twisted.protocols import basic
from twisted.internet.serialport import SerialPort

from log import logger


class SerialDevice(basic.LineReceiver):
    """
    Serial device that will send data to
    all the TCP clients connected.
    Custom serial protocol for the serial port.
    """
    def __init__(self, factory, tcp_server):
        self.factory = factory
        self.tcp_server = tcp_server

    def connectionMade(self):
        """
        Connect the serial port
        """
        logger.debug('Serial Connection made!')

    def connectionLost(self, reason):
        """
        Disconnect the serial port
        """
        #self.factory.clients.remove(self)
        logger.debug('Serial Connection lost ' +  str(reason))
        self.tcp_server.reconnect()

    def dataReceived(self, data):
        """Send data to all the clients
        connected on the TCP port
        """
        #print("Response: {0}", format(data))
        for c in self.tcp_server.factory.clients:
            c.transport.write(data)
            #c.sendLine(data)

    def lineReceived(self, line):
        logger.debug('Serial line received: ', line)

    def rawDataReceived(self, data):
        logger.debug('Serial Raw Data received: ', data)


class SerialTcpProtocol(basic.LineReceiver):
    """
    Create TCP Connections for user that
    want to get serial data
    """

    def __init__(self, factory, comm_port, baud):
        self.factory = factory
        self.comm_port = comm_port
        self.baud = baud

        if self.factory.serial_port is None:
            # Create a Serial Port device to read in serial data
            self.factory.serial_port = SerialPort(SerialDevice(self, self), comm_port, reactor, baudrate=baud)
            logger.debug('Serial Port started')

    def reconnect(self):
        """
        Reconnect the serial connection with the previous serial settings.
        :return:
        """
        self.resetSerialConnection(self.comm_port, self.baud)
        logger.info("Reconnect serial port: " + self.comm_port + " Baud: " + self.baud)

    def resetSerialConnection(self, comm_port, baud):
        """
        Reset the Serial Port device to read in serial data
        """
        self.comm_port = comm_port.strip()
        self.baud = baud
        logger.debug("comm_port: " + self.comm_port)
        logger.debug("Baud: " + str(self.baud))

        logger.debug("Disconnect serial port")
        self.factory.serial_port.loseConnection()

        self.factory.serial_port = SerialPort(SerialDevice(self, self), self.comm_port, reactor, baudrate=self.baud)
        logger.debug('Serial Port Restarted')

    def connectionMade(self):
        """
        Add TCP connections
        """
        self.factory.clients.add(self)
        logger.debug('TCP Connection made')

    def connectionLost(self, reason):
        """
        Disconnect TCP Connections
        """
        self.factory.clients.remove(self)
        logger.debug('TCP Connection lost')

    def dataReceived(self, data):
        """
        Receive data from the TCP port and send the data to the serial port
        """
        # Parse command
        self.parse_cmds(data)

    def lineReceived(self, line):
        logger.debug('TCP line received: ', line)
        #for c in self.factory.clients:
            #source = u"<{}> ".format(self.transport.getHost()).encode("ascii")
            #c.sendLine(source + line)
            #print('line received: ', line)

    def rawDataReceived(self, data):
        logger.debug('TCP Raw data received: ', data)

    def CMD_reconnect(self, cmd):
        """
        Decode the RECONNECT command to configure a new serial port.
        RECONNECT, COM12, 115200
        """
        params = cmd.split(',')
        if len(params) < 3:
            logger.error('Missing parameters to command: ' + cmd)
            return

        # Comm Port
        comm_port = params[1].strip()
        logger.debug("COMM Port: " + comm_port)

        try:
            baud = int(params[2].strip())
            logger.debug("Baud Rate: " + str(baud))
        except Exception as err:
            logger.error('Baud rate must be an integer', err)
            return

        # Reset the serial port
        self.resetSerialConnection(comm_port, baud)
        logger.debug("Reconnect Serial to: " + comm_port + " baud: " + str(baud))

    def CMD_change_baud(self, cmd):
        """
        Decode the BAUD command to configure a new serial port.
        This will reuse the last serial port comm port used.
        BAUD, 115200
        """
        params = cmd.split(',')
        if len(params) < 2:
            logger.error('Missing parameters to command: ' + cmd)
            return

        try:
            baud = int(params[1].strip())
            logger.debug("Baud Rate: " + str(baud))
        except Exception as err:
            logger.error('Baud rate must be an integer', err)
            return

        # Reset the serial port
        self.resetSerialConnection(self.comm_port, baud)
        logger.debug("Change Serial baud to: " + self.comm_port + " baud: " + str(baud))

    def parse_cmds(self, data):
        """
        Parse the commands given by the user.
        """
        logger.debug("Data: " + str(data))
        try:
            # Decode the byte array to a string
            cmd = data.decode('utf-16').strip()

            # Split the commands
            cmd_split = cmd.split(',')
            logger.debug("Command: " + cmd)

            if len(cmd_split) > 0:
                # Make command upper case so do not have to try every combination
                cur_cmd = cmd_split[0].strip().upper()

                if 'BREAK' in cur_cmd:
                    self.factory.serial_port.sendBreak()
                    logger.debug('Hardware BREAK')
                elif 'RECONNECT' in cur_cmd:
                    logger.debug("Attempt to reconnect...")
                    self.CMD_reconnect(cmd)
                elif 'BAUD' in cur_cmd:
                    logger.debug("Attempt to change baud...")
                    self.CMD_change_baud(cmd)
                    logger.debug('Baud Changed')
                else:
                    self.factory.serial_port.write((cmd + "\r").encode())
                    logger.debug("Data: " + str(data))
                    logger.debug("Command: " + cmd)
        except AttributeError as err:
            logger.error("Serial Port error: ", err)
        except Exception as err:
            logger.error("Serial Port Error: ", err)
        #except serial.portNotOpenError as err:
        #    print("Serial Port is not open. ", err)
        #except:
        #    logger.error('Error writing data to serial port')

        source = str(self.transport.getPeer())
        logger.debug(source + " - " + 'TCP data received: ' + cmd)


class AdcpFactory(protocol.Factory):
    """
    Create a serial connection and allow
    TCP clients to view the data
    """
    def __init__(self, comm_port, baud):
        self.clients = set()
        self.serial_port = None
        self.serial_comm_port = comm_port
        self.serial_baud = baud

    def buildProtocol(self, addr):
        return SerialTcpProtocol(self, self.serial_comm_port, self.serial_baud)


class AdcpSerialPortServer:
    """
    Create a serial connection and allow TCP
    clients to view the data
    """
    def __init__(self, port, comm_port, baud):
        self.port = "tcp:" + port       # TCP Port
        self.comm_port = comm_port      # Serial Port
        self.baud = baud                # Baud Rate
        self.thread = None

        logger.info("Start TCP server at: " + str(port))

        # Set the TCP port to output ADCP data
        endpoints.serverFromString(reactor, self.port).listen(AdcpFactory(self.comm_port, self.baud))
        logger.info("Serial port connected on " + str(self.comm_port) + " baud: " + str(baud))
        logger.info("TCP Port open on " + str(self.port))

        # Run the reactor in a thread
        if not reactor.running:
            self.thread = threading.Thread(name='AdcpSerialPort', target=reactor.run, args=(False,)).start()

    def close(self):
        """
        Close the thread to the server
        """
        reactor.stop()
        logger.debug("Reactor Stopped")

        if self.thread is not None:
            self.thread.join()
        logger.debug("ADCP Serial Port Thread stopped")

        #for t in threading.enumerate():
        #    if t.getName() == 'AdcpSerialPort':
        #        t.join()
        #        print("Stop the ADP serial port thread")

    @staticmethod
    def list_serial_ports():
        """ Lists serial port names

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
                print(port)
            except OSError as err:
                logger.error(err)
                pass
            except serial.SerialException as err:
                logger.error(err)
                pass

        return result

# Set the PORT to output ADCP data
#endpoints.serverFromString(reactor, "tcp:55056").listen(AdcpFactory('/dev/cu.usbserial-FTYNODPO', 115200))
#reactor.run()
