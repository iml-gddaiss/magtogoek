from rti_python.Ensemble.Ensemble import Ensemble
import logging
import pandas as pd


class Correlation:
    """
    Correlation DataSet.
    [Bin x Beam] data.
    """

    def __init__(self, num_elements, element_multiplier):
        self.ds_type = 10
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000005\0"
        self.Correlation = []
        # Create enough entries for all the (bins x beams)
        # Initialize with bad values
        for bins in range(num_elements):
            bins = []
            for beams in range(element_multiplier):
                bins.append([Ensemble().BadVelocity])

            self.Correlation.append(bins)

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the velocities.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                self.Correlation[bin_num][beam] = Ensemble.GetFloat(packet_pointer, Ensemble().BytesInFloat, data)
                packet_pointer += Ensemble().BytesInFloat

        logging.debug(self.Correlation)

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
                val = self.Correlation[bin_num][beam]
                result += Ensemble.float_to_bytes(val)

        return result

    def encode_csv(self, dt, ss_code, ss_config, blank, bin_size):
        """
        Encode the Correlation into CSV format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :param blank: Blank or first bin position in meters.
        :param bin_size: Bin Size in meters.
        :return: List of CSV lines.
        """
        str_result = []

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                # Get the value
                val = self.Correlation[bin_num][beam]

                # Create the CSV string
                str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_CORR, ss_code, ss_config, bin_num, beam, blank, bin_size, val))

        return str_result

    def is_good_bin(self, bin_num: int, min_corr: float) -> bool:
        """
        Verify if the given bin has good data based on the minimum correlation
        value given.
        :param bin_num: Bin Number
        :param min_corr: Minimum Correlation value.
        :return: TRUE = All beams have amplitude values greater than min value given.
        """
        # Verify a good bin number is given
        if bin_num >= self.num_elements:
            return False

        # Verify the amplitude value is greater then the given min value
        bad_count = 0
        for beam in range(self.element_multiplier):
            if self.Correlation[bin_num][beam] < min_corr:
                bad_count += 1

        # If any bad values are found in the bin, return false
        if bad_count > 1:
            return False

        return True

    def pd0_counts(self, num_repeat: int, pd0_beam_num: int):
        """
        The value has to be converted from percentage to 0 - 255
        Scale 0 % - 100 % to 0 - 255
        255 = 100 %
        0 = 0 %
        50 % = 0.50 * 255 = 127.5 = 255 / 2

        Also remap the Beam numbers to match PD0 beams.
        RTB and PD0 do not share the same Beam Order
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param num_repeat: Number of code repeats.
        :type num_repeat: Integer
        :param pd0_beam_num: PD0 Beam number.
        :type pd0_beam_num: Integer
        :return: Correlation data as PD0 counts format.  Beams are reordered
        :rtype: List of Correlation values.
        """

        if num_repeat == 0:
            num_repeat = 1
        repeats = (num_repeat - 1.0) / num_repeat

        # Vertical Beam
        if self.element_multiplier == 1:
            beam0 = [v[0] for v in self.Correlation]                            # PD0 Vertical - RTB 0
            return [round(v * 255.0) for v in beam0]                            # Convert to counts

        if pd0_beam_num == 0 and pd0_beam_num <= self.element_multiplier:
            beam2 = [v[2] for v in self.Correlation]                            # PD0 0 - RTB 2
            return [round((v * 128.0) / repeats) for v in beam2]                # Convert to counts

        if pd0_beam_num == 1 and pd0_beam_num <= self.element_multiplier:
            beam3 = [v[3] for v in self.Correlation]                            # PD0 1 - RTB 3
            return [round((v * 128.0) / repeats) for v in beam3]                # Convert to counts

        if pd0_beam_num == 2 and pd0_beam_num <= self.element_multiplier:
            beam1 = [v[1] for v in self.Correlation]                            # PD0 2 - RTB 1
            return [round((v * 128.0) / repeats) for v in beam1]                # Convert to counts

        if pd0_beam_num == 3 and pd0_beam_num <= self.element_multiplier:
            beam0 = [v[0] for v in self.Correlation]                            # PD0 3 - RTB 0
            return [round((v * 128.0) / repeats) for v in beam0]                # Convert to counts

        return None
