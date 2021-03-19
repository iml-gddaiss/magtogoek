from rti_python.Ensemble.Ensemble import Ensemble
import logging


class GoodEarth:
    """
    Good Earth DataSet.
    Indicate if the beam data is good.
    [Bin x Beam] data.
    """

    def __init__(self, num_elements, element_multiplier):
        self.ds_type = 20                                              # Int
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000007\0"
        self.GoodEarth = []
        # Create enough entries for all the (bins x beams)
        # Initialize with bad values
        for bins in range(num_elements):
            bins = []
            for beams in range(element_multiplier):
                bins.append([0])

            self.GoodEarth.append(bins)

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the Good Earth.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                self.GoodEarth[bin_num][beam] = Ensemble.GetInt32(packet_pointer, Ensemble().BytesInInt32, data)
                packet_pointer += Ensemble().BytesInInt32

        logging.debug(self.GoodEarth)

    def encode(self):
        """
        Encode the data into RTB format.
        :return:
        """
        result = []

        # Generate header
        result += Ensemble.generate_header(self.ds_type,
                                           self.num_elements,
                                           self.element_multiplier,
                                           self.image,
                                           self.name_len,
                                           self.Name)

        # Add the data
        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                val = self.GoodEarth[bin_num][beam]
                result += Ensemble.int32_to_bytes(val)

        return result

    def encode_csv(self, dt, ss_code, ss_config, blank, bin_size):
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

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                # Get the value
                val = self.GoodEarth[bin_num][beam]

                # Create the CSV string
                str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_GOOD_EARTH, ss_code, ss_config, bin_num, beam, blank, bin_size, val))

        return str_result
