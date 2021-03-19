import copy
import logging
import os

from obsub import event
from rti_python.Codecs.BinaryCodec import BinaryCodec


class ReadBinaryFile:
    def playback(self, ens_file_path):
        """
        Playback the given file.  This will read the file
        then call ensemble_rcv to process the ensemble.
        :param ens_file_path: Ensemble file path.
        :return:
        """
        # RTB ensemble delimiter
        DELIMITER = b"\x80" * 16

        BLOCK_SIZE = 4096

        # Get the total file size to keep track of total bytes read and show progress
        file_size = os.path.getsize(ens_file_path)
        bytes_read = 0

        # Create a buffer
        buff = bytes()

        with open(ens_file_path, "rb") as f:

            # Read in the file
            # for chunk in iter(lambda: f.read(4096), b''):
            #    self.adcp_codec.add(chunk)

            data = f.read(BLOCK_SIZE)  # Read in data

            # Keep track of bytes read
            bytes_read += BLOCK_SIZE
            self.file_progress(bytes_read, file_size, ens_file_path)

            while data:  # Verify data was found
                buff += data  # Accumulate the buffer
                if DELIMITER in buff:  # Check for the delimiter
                    chunks = buff.split(
                        DELIMITER
                    )  # If delimiter found, split to get the remaining buffer data
                    buff = chunks.pop()  # Put the remaining data back in the buffer

                    for chunk in chunks:  # Take out the ens data
                        self.process_playback_ens(
                            DELIMITER + chunk
                        )  # Process the binary ensemble data

                data = f.read(BLOCK_SIZE)  # Read the next batch of data

                # Keep track of bytes read
                bytes_read += BLOCK_SIZE
                # self.file_progress(bytes_read, file_size, ens_file_path)
                self.file_progress(BLOCK_SIZE, file_size, ens_file_path)

        # Process whatever is remaining in the buffer
        self.process_playback_ens(DELIMITER + buff)

        # Close the file
        f.close()

    def process_playback_ens(self, ens_bin):
        """
        Process the playback ensemble found.  This will verify the ensemble is good.
        If the data is verified to be a good ensemble, then decode the ensemble and
        pass it to the event handler.
        :param ens_bin: Binary Ensemble data to decode
        :return:
        """
        # Verify the ENS data is good
        # This will check that all the data is there and the checksum is good
        if BinaryCodec.verify_ens_data(ens_bin):
            # Decode the ens binary data
            logging.debug("Decoding binary data to ensemble: " + str(len(ens_bin)))
            ens = BinaryCodec.decode_data_sets(ens_bin)

            if ens.IsEnsembleData:
                logging.debug("Ensemble Found: " + str(ens.EnsembleData.EnsembleNumber))
            else:
                logging.debug("Ensemble Found")

            if ens:
                # Pass the ensemble to the event handler
                self.ensemble_event(ens)

    @event
    def ensemble_event(self, ens):
        """
        Event to subscribe to receive decoded ensembles.
        :param ens: Ensemble object.
        :return:
        """
        if ens.IsEnsembleData:
            logging.debug(str(ens.EnsembleData.EnsembleNumber))

    @event
    def file_progress(self, bytes_read, total_bytes, ens_file_path):
        """
        Monitor the progress of reading the file.  This will give the
        bytes read, total bytes and the file name.
        :param bytes_read: Bytes read.
        :param total_bytes: Total bytes read.
        :param ens_file_path: File path.
        :return:
        """
        logging.debug(
            "ReadBinaryFile: Bytes Read: "
            + str(bytes_read)
            + " - Total Bytes: "
            + str(total_bytes)
            + " -- "
            + ens_file_path
        )


if __name__ == "__main__":

    import tkinter as tk
    from tkinter import filedialog

    def process_ens_func(sender, ens):
        """
        Receive the data from the file.  It will process the file.
        When an ensemble is found, it will call this function with the
        complete ensemble.
        :param ens: Ensemble to process.
        :return:
        """
        if ens.IsEnsembleData:
            print(str(ens.EnsembleData.EnsembleNumber), end="\r")

    def read_file_progress(sender, bytes_read, total_bytes, ens_file_path):
        """
        Monitor the file progress.
        :param sender:
        :param bytes_read: Bytes read.
        :param total_bytes: Total bytes.
        :param ens_file_path: File path.
        :return:
        """
        logging.debug(
            "Bytes Read: "
            + str(bytes_read)
            + " - Total Bytes: "
            + str(total_bytes)
            + " -- "
            + ens_file_path
        )

    # Create the file reader to read the binary file
    read_binary = ReadBinaryFile()
    read_binary.ensemble_event += process_ens_func
    read_binary.file_progress += read_file_progress

    # Just define the file path
    # file_path = "/path/to/file/ensembles.ens"

    # GUI to ask for file
    # Ask for a file
    # You can use any way to get the file path
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()

    # Pass the file path to the reader
    read_binary.playback(file_path)
