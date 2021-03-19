import datetime
import humanize
import os
import logging

class RtiBinaryWriter:
    """
    Create a writer to write data to a file.
    """

    def __init__(self, folder_path=None, header="RTI_", extension=".ens", max_file_size=16):
        """
        Create an object to write binary data to a file.
        :param folder_path: Folder path to store the data.  Default: User Folder depending on OS
        :param header: What to put in the beginning of the file name.  Default: RTI_
        :param extension: File extension.  Default: .ens
        :param max_file_size: Maximum file size.  Default: 16mb
        """

        BYTES_PER_MB = 1048576
        self.max_file_size = max_file_size * BYTES_PER_MB
        self.folder_path = folder_path
        self.header = header
        self.extension = extension

        # If know folder path was given, set a default folder
        if not self.folder_path:
            self.folder_path = os.path.expanduser('~')

        # If the folder does not exist, create it
        if not os.path.exists(self.folder_path):
            os.chdir(self.folder_path)

        # Create a file name
        self.file_path = self.create_file_name(self.folder_path, header=header, extension=extension)
        self.file = open(self.file_path, "wb")

        self.bytes_written = 0          # Bytes written for current file
        self.total_bytes = 0            # All bytes written since start

    def write(self, data):
        """
        Write the data to the file.
        :param data: Binary data to write to the file.
        :return:
        """
        try:
            # Write data
            self.file.write(data)

            # Monitor bytes written
            self.bytes_written += len(data)
            self.total_bytes += len(data)

            # Check if the file exceeds the max file size
            # If it does, create a new file
            if self.bytes_written > self.max_file_size:
                self.file_path = self.create_file_name(self.folder_path, self.header, self.extension)
                self.close()
                self.file = open(self.file_path, "wb")
                self.bytes_written = 0
        except Exception as e:
            logging.error("Error writing the file.  ", e)

    def get_current_file_bytes_written(self):
        """
        Get the bytes written in the current file.
        :return:
        """
        return humanize.naturalsize(self.bytes_written, binary=True)

    def get_total_bytes_written(self):
        """
        Get the bytes written in all the files for this object.
        :return:
        """
        return humanize.naturalsize(self.total_bytes, binary=True)

    def get_file_path(self):
        """
        Get the file path of the current file.
        :return:
        """
        return self.file.name

    def close(self):
        """
        Close the file.
        :return:
        """
        self.file.close()

    def create_file_name(self, folder, header="RTI_", extension=".ens"):
        """
        Create a file name based off the time and data.  User the header
        and extension given.
        :param folder: Folder to store the file.
        :param header: Header for the file.
        :param extension: Extension for the file.
        :return: File created.
        """
        now = datetime.datetime.now()
        file_name_date = now.strftime("%Y%m%d_%H%M%S")

        return folder + os.sep + header + file_name_date + extension
