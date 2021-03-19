import logging
import serial
import threading
import time
import humanize
import os
import tkinter
from tkinter import filedialog
from tkinter import *
import rti_python.Comm.adcp_serial_port as serial_port
import rti_python.Writer.rti_binary as RtiBinaryWriter
from typing import List


def get_serial_ports() -> List[str]:
    return serial_port.get_serial_ports()


def get_baud_rates() -> List[str]:
    return serial_port.get_baud_rates()


def get_serial_ports_tuple() -> List[tuple]:
    result = []

    for port in serial_port.get_serial_ports():
        result.append((port, port))

    return result


def get_baud_rates_tuple() -> List[tuple]:
    result = []

    for baud in serial_port.get_baud_rates():
        result.append((baud, baud))

    return result


class DataLoggerHardware:

    def __init__(self):
        # Serial port connection
        self.serial = None
        self.serial_thread = None
        self.serial_thread_alive = False
        self.download_thread = None
        self.download_thread_alive = False
        self.cmd_lock = threading.Lock()
        self.read_lock = threading.Lock()
        self.write_lock = threading.Lock()
        
        # Last response from serial port
        self.last_response = ""

        # Lastest config from SD card
        self.rd_config = {}

        # Recording
        self.serial_recorder = None
        self.is_recording = False
        self.recording_folder_path = "C:\\rti_capture"
        self.blocks_read = 0
        self.blocks_left = 0
        self.total_blocks = 0
        self.MAX_BLOCK_STEP = 100

        # Download
        self.downloading = False
        self.cancel_download = False
        self.bytes_written = 0
        self.current_file_size = 0
        self.MAX_FILE_SIZE = 16

    def connect_serial(self,
                       port: str,
                       baud: int) -> dict:
        """
        Connect the serial port and start the read thread.
        Return the configuration of the Datalogger.
        """

        # Intializize the config
        #logger_config = {}
        #logger_config["Status"] = "Disconnected"

        # Make the serial connection
        try:
            self.serial = serial_port.AdcpSerialPort(port, baud)
        except ValueError as ve:
            logging.error("Error opening serial port. " + str(ve))
            return self.rd_config
        except serial.SerialException as se:
            logging.error("Error opening serial port. " + str(se))
            return self.rd_config
        except Exception as e:
            logging.error("Error opening serial port. " + str(e))
            return self.rd_config

        # Start the read thread
        #self.serial_thread_alive = True
        #self.serial_thread = threading.Thread(name="Serial Thread", target=thread_worker, args=(self,))
        #self.serial_thread.start()

        # Check if the connection was made
        if self.serial.is_open():
            # Read the config
            self.rd_config = self.read_config()
            self.rd_config["Status"] = "Connected"
            return self.rd_config
        
        # No connection made
        self.rd_config["Status"] = "Disconnected"
        return self.rd_config

    def disconnect_serial(self):
        """
        Disconnect the serial port and stop the read thread.
        """
        # Stop the thread
        self.serial_thread_alive = False

        # Disconnect the serial port
        if self.serial:
            self.serial.disconnect()
            self.serial = None

    def verify_connection(self):
        """
        Verify the serial connection is good.
        """
        return self.serial and self.serial.is_open()

    def get_status(self) -> dict:
        """
        Get the current status of the hardware and download progress.
        """
        status = self.rd_config
        status["IsRecording"] = self.is_recording
        status["FolderPath"] = self.recording_folder_path
        status["BlocksRead"] = self.blocks_read
        status["BlocksLeft"] = self.blocks_left
        status["TotalBlocks"] = self.total_blocks
        status["MaxBlockStep"] = self.MAX_BLOCK_STEP
        status["CancelDownload"] = self.cancel_download
        status["BytesWritten"] = self.bytes_written
        status["CurrentFileSize"] = self.current_file_size
        status["MaxFileSize"] = self.MAX_FILE_SIZE
        status["PrettyBlocksRead"] = humanize.filesize.naturalsize(self.blocks_read * 512)
        status["PrettyTotalBlocks"] = humanize.filesize.naturalsize(self.total_blocks * 512)
        status["PrettyBlocksLeft"] = humanize.filesize.naturalsize(self.blocks_left * 512)
        if self.total_blocks > 0:
            status["DownloadProgress"] = (self.blocks_read / self.total_blocks) * 100.0
        else:
            status["DownloadProgress"] = 0

        if self.serial_recorder:
            status["CurrentFileName"] = self.serial_recorder.file_path
        else:
            status["CurrentFileName"] = ""

        return status

    def read_config(self) -> dict:
        """
        Read the configuration of the data logger.
        Return a dictionary with the configuration.
        """
        # Verify connection is open
        if self.verify_connection():
            # Send the RD command to get the configuration
            self.serial.send_cmd("RD")
            
            # Wait to get the response
            time.sleep(0.25)

            # Read the data from the serial port
            data = self.serial.read(self.serial.raw_serial.in_waiting)

            try:
                # Convert to ascii
                ascii_data = data.decode('ascii')

                # Get the config
                self.rd_config = self.decode_rd(ascii_data)

                # Decode the response
                return self.rd_config
            except Exception as ex:
                logging.error("Error getting the config." + str(ex))
                return self.rd_config

            return self.rd_config

    def browse_folder(self):
        """
        Select the Folder path.
        """
        root = tkinter.Tk()
        root.withdraw() #use to hide tkinter window

        folder_path = filedialog.askdirectory(parent=root, title='Please select a directory')
        if len(folder_path) > 0:
            self.recording_folder_path = folder_path

        return self.recording_folder_path

    def download(self):
        """
        Download the data on the datalogger.  Record each block
        to the computer.
        """
        """
        # Download until all the blocks are read
        while not self.cancel_download and self.blocks_left > 0:
            # Determine how many blocks to read at a time
            block_step = self.get_block_step()

            # Create and send the command to read the next block
            cmd = "BR " + str(self.blocks_read) + "," + str(block_step)
            self.serial.send_cmd(cmd)

            # Wait for the response and read the data
            data = self.serial.read(self.serial.raw_serial.in_waiting)

            # Check checksum

            # Record the response
            self.record_data(data)

            # Keep track of the progress
            self.blocks_read += block_step
            self.blocks_left -= block_step

            print(str(self.blocks_read) + " " + str(self.blocks_left) + " " + str(self.cancel_download))
        """
        if not self.download_thread_alive:
            self.download_thread_alive = True
            self.download_thread = threading.Thread(name="Download Thread", target=download_thread_worker, args=(self,))
            self.download_thread.start()

    def get_block_step(self):
        """
        Maximize the number of blocks to reads.
        This will check if the max number can be used.
        If it is greater than the blocks left, then use
        the blocks left.
        """
        block_step = self.MAX_BLOCK_STEP
        if block_step > self.blocks_left:
            block_step = self.blocks_left

        return block_step

    def decode_rd(self, rd_data: str) -> dict:
        """
        Decode the RD command.
        1 Block = 512 bytes

        RD
        Total Space    62367743 KB
        Used Space      4259695 KB
        User Blocks           4 through 9
        First Block          10
        Next  Block     8519400
        Next  Byte          232
        Last Block    124735487
        Overruns 0
        Loops 0
        Format 2020/02/11 07:20:23
        Time Stamps:
        """
        # Init the dict
        config = {}
        config['TotalSpace'] = 0
        config['UsedSpace'] = 0
        config["FirstBlock"] = 0
        config["NextByte"] = 0
        config["NextBlock"] = 0
        config["LastBlock"] = 0
        config["TotalBlocks"] = 0

        # Decode the RD data
        lines = rd_data.split("\n")
        try:
            for line in lines:
                values = line.split() 
                if "Total Space" in line:
                    config['TotalSpace'] = int(values[2])
                if "Used Space" in line:
                    config['UsedSpace'] = int(values[2])
                if "First Block" in line:
                    config["FirstBlock"] = int(values[2])
                if "Next  Block" in line:
                    config["NextBlock"] = int(values[2])
                if "Next  Byte" in line:
                    config["NextByte"] = int(values[2])
                if "Last Block" in line:
                    config["LastBlock"] = int(values[2])
        except Exception as ex:
            logging.error("Error processing the RD data.\n" + str(ex) + rd_data)

        if config['NextBlock'] > 0 and config['FirstBlock'] > 0:
            self.total_blocks = config['NextBlock'] - config['FirstBlock'] - 1
            config["TotalBlocks"] = self.total_blocks

        return config

    def turn_on_record(self, folder_path: str):
        """
        Turn on recording.
        Set the recorder.  Then set the flags.
        """
        self.serial_recorder = RtiBinaryWriter.RtiBinaryWriter(folder_path, "RTI_", ".ens", self.MAX_FILE_SIZE)
        logging.debug("Start Recording " + folder_path)
        self.is_recording = True
        self.recording_folder_path = folder_path
        self.bytes_written = 0
        self.current_file_size = 0

    def turn_off_record(self):
        """
        Turn off recording.  
        Close the recorder.  Then set the recorder to None
        Then set the flag that recording is off.
        """
        if self.serial_recorder:
            self.serial_recorder.close()
            logging.debug("Stop Recording")
        self.serial_recorder = None

        self.is_recording = False
        self.record_path = ""

    def record_data(self, data):
        """
        Record data.  Verify the recorder is on.  Then write the
        incoming data from the thread worker to the file.

        The binarywriter will handle the file name and checking
        for a max file size.
        """
        if self.serial_recorder:
            try:
                # Record the data
                self.serial_recorder.write(data)
            except Exception as ex:
                logging.error("Error recording data: " + str(ex))

            # Keep track of file sizes
            self.bytes_written += len(data)
            self.current_file_size += len(data)

            print(".")


def download_thread_worker(vm):

    print("Download STARTED")

    # Get the configuration
    vm.read_config()

    # Set recording parameters
    vm.turn_on_record(vm.recording_folder_path)
    vm.blocks_read = 0
    vm.blocks_left = vm.total_blocks

    # Download until all the blocks are read
    while not vm.cancel_download and vm.blocks_left > 0:
        with vm.cmd_lock:
            # Determine how many blocks to read at a time
            block_step = vm.get_block_step()

            # Create and send the command to read the next block
            cmd = "BR " + str(vm.blocks_read) + "," + str(block_step)
            vm.serial.send_cmd(cmd)

        with vm.read_lock:
            timeout = 1000000
            cmd_len = len(cmd) + 3
            data_expected = cmd_len + (512 * block_step) + 2
            data = bytearray()
            #while vm.serial.raw_serial.in_waiting > 0 and timeout > 0:
            while len(data) < data_expected and timeout > 0:
                # Wait for the response and read the data
                serial_read = vm.serial.read(vm.serial.raw_serial.in_waiting)
                if serial_read:
                    data += serial_read
                timeout -= 1
                #time.sleep(0.15)

            print("Data Size: " + str(len(data)) + " Data expected: " + str(data_expected) + " Timeout: " + str(timeout))
            # Check checksum

            # Verify data was read
            if len(data) > 0:
                # Keep track of the progress
                vm.blocks_read += block_step
                vm.blocks_left -= block_step

                with vm.write_lock:
                    # Record the response
                    vm.record_data(data)

        print(str(vm.blocks_read) + " " + str(vm.blocks_left) + " " + str(vm.cancel_download))
        #time.sleep(0.15)

    # Download complete
    vm.download_thread_alive

    # Stop the recording and close the file
    vm.turn_off_record()

    print("Download COMPLETE")


def thread_worker(vm):
    """
    Thread worker to handle reading the serial port.
    :param vm: This VM to get access to the variables.
    :return:
    """
    while vm.serial_thread_alive:
        try:
            if vm.serial.raw_serial.in_waiting:
                # Read the data from the serial port
                data = vm.serial.read(vm.serial.raw_serial.in_waiting)

                try:
                    ascii_data = data.decode('ascii')
                    logging.debug(ascii_data)
                    print(ascii_data)

                    vm.last_response = ascii_data
                except Exception as ex:
                    # Do nothing
                    logging.error(str(ex))
                    logging.error(str(data))         # Display error

                # Record data if turned on
                #vm.record_data(data)

                # Publish the data
                #vm.on_serial_data(data)

            time.sleep(0.01)
        except serial.SerialException as se:
            logging.error("Error using the serial port.\n" + str(se))
            vm.disconnect_serial()
        except Exception as ex1:
            logging.error("Error processing the data.\n" + str(ex1))