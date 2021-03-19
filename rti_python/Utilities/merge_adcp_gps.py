import os
from os import listdir
from os.path import isfile, join
import logging
from tqdm import tqdm
import pynmea2
import datetime
import time
import pandas as pd

from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.NmeaData import NmeaData


class MergeAdcpGps:
    """
    Merage the ADCP and GPS data.
    Put the ADCP data in a folder.
    Put the GPS data in a separate folder.
    Give to the two folder paths.
    It will then map all the GPS data to a time.
    It will then read in the ADCP and match the time from the GPS and the ADCP.

    """

    def __init__(self, gps_folder_path, adcp_folder_path):
        """
        Give the GPS folder and ADCP folder paths.
        It will then read in all the GPS data and map it to a time.
        It will then read in all the ADCP data and add the GPS data to the ADCP data.
        :param self:
        :param gps_folder_path: GPS Folder
        :param adcp_folder_path: ADCP Folder
        :return:
        """
        # Usually GPS messages come in blocks
        # List the last GPS message in the block
        # Then the GPS file will be divided by this message
        # A date and time will then be associated with this block based
        # off one of the GPS messages (GGA) in the block
        self.LAST_GPS_ID = '$GPRMC'

        # GPS Dataframe List.  The list will contain a a NMEA dataset
        # and a datetime as the index
        self.gps_df = pd.DataFrame(columns=['dt', 'nmea'])

        # ADCP List.  List of all the ADCP data.
        self.adcp_list = []

        # Write in batches, so buffer up the data to write
        self.batch_write = bytes()

        # Load the GPS data
        self.load_gps_dir(gps_folder_path)

        # Load the ADCP data and merge it with GPS data
        self.load_adcp_dir(adcp_folder_path)


    def load_gps_dir(self, folder_path):
        """
        Load all the GPS data in the GPS directory.
        :param folder_path: GPS folder path.
        :return:
        """

        if not os.path.exists(folder_path):
            print("GPS Folder does not exist")
            return

        # Get a list of all the files in the GPS dir
        gps_files = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]

        # Read in all the GPS data
        for gps in gps_files:
            self.read_gps_data(folder_path + os.sep + gps)

    def read_gps_data(self, file_name):
        """
        Read in the GPS data from the file.
        Create blocks of GPS data based off the last GPS ID.
        :param file_name: File path
        :return:
        """

        # Create a NMEA dataset to create a GPS block
        nmea_dataset = NmeaData()

        with open(file_name, 'r', encoding='utf-8') as f:

            print("Loading GPS data: " + file_name)

            # Read in the line from the file
            for gps_line in tqdm(f):
                # Add the NMEA data to the dataset
                nmea_dataset.add_nmea(gps_line)

                # When the last GPS id is found, add it to the list
                if self.LAST_GPS_ID in gps_line:

                    # Create a new entry in the dataframe
                    if nmea_dataset.datetime:
                        self.gps_df = self.gps_df.append({'dt': datetime.datetime.combine(datetime.datetime.now().date(), nmea_dataset.datetime), 'nmea': nmea_dataset}, ignore_index=True)

                    # Create a new dataset
                    nmea_dataset = NmeaData()

        # Close the file
        f.close()

        # Move datetime column to the index
        self.gps_df['datetime'] = pd.to_datetime(self.gps_df['dt'])
        self.gps_df = self.gps_df.set_index('datetime')
        self.gps_df.drop(['dt'], axis=1, inplace=True)

    def load_adcp_dir(self, folder_path):
        """
        Load all the ADCP data in the ADCP directory.
        :param folder_path: ADCP folder path.
        :return:
        """

        if not os.path.exists(folder_path):
            print("ADCP Folder does not exist")
            return

        # Get a list of all the files in the GPS dir
        adcp_files = [f for f in listdir(folder_path) if isfile(join(folder_path, f))]

        # Read in all the GPS data
        for adcp in adcp_files:
            self.read_adcp_data(folder_path + os.sep + adcp)

    def read_adcp_data(self, file_path):
        """
        Read in the data from the file.  Find all the ensembles.
        :param file_path: File path to file.
        :return:
        """
        DELIMITER = b'\x80' * 16
        datetime_delta = datetime.timedelta(seconds=1)          # Time range for GPS data and Ens data

        # Create Output file path
        file_name = os.path.splitext(file_path)[0]              # Get the file name
        mod_file_path = file_name + "_gps.ens"                  # Create a new file path

        # Create a buffer
        buff = bytes()

        print("Processing ADCP Data: " + file_path)

        with tqdm(total=os.path.getsize(file_path)) as pbar:

            # Open the output file
            with open(mod_file_path, "wb") as output_file:
                # Open the file
                file = open(file_path, 'rb')

                data = file.read(4096)                                  # Read in data
                pbar.update(len(data))                                  # Update the progressbar

                while data:                                             # Verify data was found
                    buff += data                                        # Accumulate the buffer
                    if DELIMITER in buff:                               # Check for the delimiter
                        chunks = buff.split(DELIMITER)                  # If delimiter found, split to get the remaining buffer data
                        buff = chunks.pop()                             # Put the remaining data back in the buffer
                        for chunk in chunks:                            # Take out the ens data
                            self.process_ens_bin(DELIMITER + chunk,     # Combine the delimiter and ens data
                                                 datetime_delta,        # Time Range
                                                 output_file)           # Output file
                    data = file.read(4096)                              # Read the next batch of data
                    pbar.update(len(data))                              # Update the progressbar

                # Process whatever is remaining in the buffer



                # Close the input files
                file.close()

                # Write the remaining ensembles to the file
                output_file.write(self.batch_write)

            # Close the output file
            output_file.close()

    def process_ens_bin(self, ens_bin, datetime_delta, output_file):
        """
        Process an ensemble.  Given the binary data.  Verify you can decode
        the data.  If you can decode the data, then look for the GPS data associated
        with the time in the ensemble.  If you find a match, merge the GPS data into
        the ADCP data.  Then write the ensemble back to the new file.

        Write the output file in batches to save on writes.
        :param ens_bin: Binary ensemble data to decode.
        :param datetime_delta: Time difference to find the GPS data that matches
        :param output_file: Output file path
        :return:
        """
        # Verify the ENS data is good
        # This will check that all the data is there and the checksum is good
        if BinaryCodec.verify_ens_data(ens_bin):
            # Decode the ens binary data
            ens = BinaryCodec.decode_data_sets(ens_bin)

            # Add the ensemble to the list
            if ens:
                # Find the GPS datetime in the dictionary matching the datetime range
                min_time = (ens.EnsembleData.datetime() - datetime_delta).time()
                max_time = (ens.EnsembleData.datetime() + datetime_delta).time()
                matching_key = self.gps_df[min_time:max_time]

                # Get the last matching key
                nmea_ds = None
                if not matching_key.empty:
                    nmea_ds = matching_key[-1:]['nmea'].item()

                # Add the NMEA data to the file if it exist
                if nmea_ds:
                    ens.AddNmeaData(nmea_ds)

                # Accumulate the buffer
                self.batch_write += ens.encode()

                if len(self.batch_write) > 4096 * 30:
                    # Write the ensemble to the file
                    output_file.write(self.batch_write)

                    # Clear the buffer
                    self.batch_write = bytes()


if __name__ == '__main__':

    # Separate all the GPS and ADCP into 2 folders
    # Give the folders for the GPS and ADCP data.
    #gps_folder = "G:\\RTI\\data\\uw\\gps_min"
    #adcp_folder = "G:\\RTI\\data\\uw\\ADCP_min"
    gps_folder = "C:\\RTI\\Data\\uw\\gps_min"
    adcp_folder = "C:\\RTI\\Data\\uw\\ADCP_min"


    MergeAdcpGps(gps_folder, adcp_folder)
    print("process complete")