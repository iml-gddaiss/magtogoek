import pynmea2
from rti_python.Ensemble.Ensemble import Ensemble
import logging
from pygeodesy import ellipsoidalVincenty
from decimal import *


class NmeaData:
    """
    NMEA DataSet.
    String data to decode.
    """

    def __init__(self, num_elements=0, element_multiplier=1):
        self.ds_type = 50           # Bytes
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000011\0"
        self.nmea_sentences = []

        # Initialize with bad values
        self.GPGGA = None
        self.GPVTG = None
        self.GPRMC = None
        self.GPGLL = None
        self.GPGSV = None
        self.GPGSA = None
        self.GPHDT = None
        self.GPHDG = None
        self.latitude = 0.0
        self.longitude = 0.0
        self.speed_knots = 0.0                              # Speed in Knots
        self.speed_m_s = 0.0                                # Speed in m/s
        self.heading = 0.0
        self.datetime = None                              # Date and Time from GGA

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the NMEA data.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        nmea_str = str(data[packet_pointer:], "UTF-8")

        self.num_elements = len(nmea_str)

        for msg in nmea_str.split():
            # Add the NMEA message
            self.add_nmea(msg)

        logging.debug(nmea_str)
        logging.debug(self.nmea_sentences)

    def add_nmea(self, msg):
        try:
            # Increment the number of elements
            self.num_elements += len(msg)

            # Parse the NMEA data
            nmea_msg = pynmea2.parse(msg)

            if isinstance(nmea_msg, pynmea2.types.talker.GGA):
                self.GPGGA = nmea_msg
                self.latitude = nmea_msg.latitude
                self.longitude = nmea_msg.longitude
                self.datetime = nmea_msg.timestamp
            if isinstance(nmea_msg, pynmea2.types.talker.VTG):
                self.GPVTG = nmea_msg
                self.speed_knots = nmea_msg.spd_over_grnd_kts
                self.speed_m_s = nmea_msg.spd_over_grnd_kts * Decimal(0.51444444444444)
            if isinstance(nmea_msg, pynmea2.types.talker.RMC):
                self.GPRMC = nmea_msg
            if isinstance(nmea_msg, pynmea2.types.talker.GLL):
                self.GPGLL = nmea_msg
            if isinstance(nmea_msg, pynmea2.types.talker.GSV):
                self.GPGSV = nmea_msg
            if isinstance(nmea_msg, pynmea2.types.talker.GSA):
                self.GPGSA = nmea_msg
            if isinstance(nmea_msg, pynmea2.types.talker.HDT):
                self.GPHDT = nmea_msg
                self.heading = nmea_msg.heading
            if isinstance(nmea_msg, pynmea2.types.talker.HDG):
                self.GPHDG = nmea_msg

            self.nmea_sentences.append(msg.strip())
        except pynmea2.nmea.ParseError as pe:
            logging.debug("Bad NMEA String")
        except Exception as e:
            logging.debug("Error decoding NMEA msg", e)

    def encode(self):
        """
        Encode the data into RTB format.
        :return:
        """
        result = []

        # Combine all the NMEA strings into one long string
        str_nmea = ""
        for nmea in self.nmea_sentences:
            str_nmea += nmea + "\n"

        # Generate the number of elements from the number of characters
        self.num_elements = len(str_nmea)

        # Generate header
        result += Ensemble.generate_header(self.ds_type,
                                           self.num_elements,
                                           self.element_multiplier,
                                           self.image,
                                           self.name_len,
                                           self.Name)

        # Convert the strings to bytes
        result += str_nmea.encode("UTF-8")

        return result

    def encode_csv(self, dt, ss_code, ss_config, blank=0, bin_size=0):
        """
        Encode into CSV format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :param blank: Blank or first bin position in meters.
        :param bin_size: Bin size in meters.
        :return: List of CSV lines.
        """
        str_result = []

        # Create the CSV strings for each NMEA string
        for nmea in self.nmea_sentences:
            str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_NMEA, ss_code, ss_config, 0, 0, blank, bin_size, nmea))

        return str_result

    def get_new_position(self, distance: float, bearing: float):
        """
        This function is typically used to create a ship track plot with a vector to represent the
        water current.  The distance will be the magnitude of the water currents, the bearing will be the
        direction of the water currents.  This will allow you to plot the LatLon and also a vector off this
        LatLon point.
        :param distance: Distance (magnitude)
        :param bearing: Direction to travel
        :return The new position based on the input and current position. (lat, lon)
        """
        return NmeaData.get_new_lat_lon_position(self.latitude, self.longitude, distance, bearing)

    @staticmethod
    def get_new_lat_lon_position(latitude: float, longitude: float, distance: float, bearing: float):
        """
        This function is typically used to create a ship track plot with a vector to represent the
        water current.  The distance will be the magnitude of the water currents, the bearing will be the
        direction of the water currents.  This will allow you to plot the LatLon and also a vector off this
        LatLon point.
        :param latitude: Start latitude position
        :param longitude: Start longitude position
        :param distance: Distance (magnitude)
        :param bearing: Direction to travel
        :return The new position based on the input and current position. (lat, lon)
        """
        # Choose a ellipsoid
        LatLon = ellipsoidalVincenty.LatLon

        # Verify we have a latitude and longitude value
        if latitude and longitude:
            # Set the current location
            curr_loc = LatLon(latitude, longitude)

            # Get the new position based on distance and bearing
            new_loc = curr_loc.destination(distance=distance, bearing=bearing)

            # Return lat, lon
            return new_loc.lat, new_loc.lon

        return 0.0, 0.0



