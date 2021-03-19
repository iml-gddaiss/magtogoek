from rti_python.Ensemble.Ensemble import Ensemble
import logging


class Amplitude:
    """
    Amplitude DataSet.
    [Bin x Beam] data.
    """

    def __init__(self, num_elements, element_multiplier):
        self.ds_type = 10
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000004\0"
        self.Amplitude = []

        #self.EnsembleNumber = ensemble_number
        #self.SerialNumber = serial_number
        #self.DateTime = date_time

        # Create enough entries for all the (bins x beams)
        # Initialize with bad values
        for bins in range(num_elements):
            bins = []
            for beams in range(element_multiplier):
                bins.append([Ensemble().BadVelocity])

            self.Amplitude.append(bins)

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the velocities.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                self.Amplitude[bin_num][beam] = Ensemble.GetFloat(packet_pointer, Ensemble().BytesInFloat, data)
                packet_pointer += Ensemble().BytesInFloat

        logging.debug(self.Amplitude)

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
                val = self.Amplitude[bin_num][beam]
                result += Ensemble.float_to_bytes(val)

        return result

    def encode_csv(self, dt, ss_code, ss_config, blank, bin_size):
        """
        Encode the Amplitude into CSV format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :param blank: Blank or first bin position in meters.
        :param bin_size: Size of the bin in meters.
        :return: List of CSV lines.
        """
        str_result = []

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                # Get the value
                val = self.Amplitude[bin_num][beam]

                # Create the CSV string
                str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_AMP, ss_code, ss_config, bin_num, beam, blank, bin_size, val))

        return str_result

    def is_good_bin(self, bin_num: int, min_amp: float) -> bool:
        """
        Verify if the given bin has good data based on the minimum amplitude
        value given.
        :param bin_num: Bin Number
        :param min_amp: Minimum amplitude value.
        :return: TRUE = All beams have amplitude values greater than min value given.
        """
        # Verify a good bin number is given
        if bin_num >= self.num_elements:
            return False

        # Verify the amplitude value is greater then the given min value
        bad_count = 0
        for beam in range(self.element_multiplier):
            if self.Amplitude[bin_num][beam] < min_amp:
                bad_count += 1

        # If any bad values are found in the bin, return false
        if bad_count > 1:
            return False

        return True

    def pd0_counts(self, pd0_beam_num: int):
        """
        Convert the Amplitude to Counts.
        0.5dB per count.

        Also remap the Beam numbers to match PD0 beams.
        RTB and PD0 do not share the same Beam Order
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param pd0_beam_num: PD0 Beam number.
        :type pd0_beam_num: Integer
        :return: A list of all the Amplitude for the given PD0 beam, converted to counts for the beam.  The beam will be based on reordering for PD0
        :rtype: List or None if beam number is not correct.
        """

        # Vertical Beam ONLY
        if self.element_multiplier == 1:
            beam0 = [v[0] for v in self.Amplitude]              # Beam 0
            return [round(v * 2.0) for v in beam0]              # Convert to counts

        if pd0_beam_num == 0 and pd0_beam_num <= self.element_multiplier:
            beam2 = [v[2] for v in self.Amplitude]              # PD0 0 - RTB 2
            return [round(v * 2.0) for v in beam2]              # Convert to counts

        if pd0_beam_num == 1 and pd0_beam_num <= self.element_multiplier:
            beam3 = [v[3] for v in self.Amplitude]              # PD0 1 - RTB 3
            return [round(v * 2.0) for v in beam3]              # Convert to counts

        if pd0_beam_num == 2 and pd0_beam_num <= self.element_multiplier:
            beam1 = [v[1] for v in self.Amplitude]              # PD0 2 - RTB 1
            return [round(v * 2.0) for v in beam1]              # Convert to counts

        if pd0_beam_num == 3 and pd0_beam_num <= self.element_multiplier:
            beam0 = [v[0] for v in self.Amplitude]              # PD0 3 - RTB 0
            return [round(v * 2.0) for v in beam0]              # Convert to counts

        return None
