from rti_python.Ensemble.Ensemble import Ensemble
import logging


class GoodBeam:
    """
    Good Beam DataSet.
    Indicate if the beam data is good.
    [Bin x Beam] data.
    """

    def __init__(self, num_elements, element_multiplier):
        self.ds_type = 20                               # Int
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000006\0"
        self.GoodBeam = []
        # Create enough entries for all the (bins x beams)
        # Initialize with bad values
        for bins in range(num_elements):
            bins = []
            for beams in range(element_multiplier):
                bins.append([0])

            self.GoodBeam.append(bins)

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the Good Beams.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                self.GoodBeam[bin_num][beam] = Ensemble.GetInt32(packet_pointer, Ensemble().BytesInInt32, data)
                packet_pointer += Ensemble().BytesInInt32

        logging.debug(self.GoodBeam)

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
                val = self.GoodBeam[bin_num][beam]
                result += Ensemble.int32_to_bytes(val)

        return result

    def encode_csv(self, dt, ss_code, ss_config, blank, bin_size):
        """
        Encode into CSV format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :param blank: Blank or First bin position in meters.
        :param bin_size: Bin size in meters.
        :return: List of CSV lines.
        """
        str_result = []

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                # Get the value
                val = self.GoodBeam[bin_num][beam]

                # Create the CSV string
                str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_GOOD_BEAM, ss_code, ss_config, bin_num, beam, blank, bin_size, val))

        return str_result

    def pd0_percent(self, pings_per_ens: int, pd0_beam_num: int):
        """
        Convert the Good Beams to Percent.

        Also remap the Beam numbers to match PD0 beams.
        RTB and PD0 do not share the same Beam Order
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param pd0_beam_num: PD0 Beam number.
        :type pd0_beam_num: Integer
        :param pings_per_ens: Number of pings in the ensemble.
        :type pings_per_ens: Integer
        :return: A list of all the velocities for the given PD0 beam, converted to mm/s for the beam.  The beam will be based on reordering for PD0
        :rtype: List or None if beam number is not correct.
        """

        # Vertical Beam ONLY
        if self.element_multiplier == 1:
            beam0 = [v[0] for v in self.GoodBeam]                                 # Beam 0
            return [round((v * 100.0) / pings_per_ens) for v in beam0]            # Convert to percent

        if pd0_beam_num == 0 and pd0_beam_num <= self.element_multiplier:
            beam2 = [v[2] for v in self.GoodBeam]                                 # PD0 0 - RTB 2
            return [round((v * 100.0) / pings_per_ens) for v in beam2]            # Convert to percent

        if pd0_beam_num == 1 and pd0_beam_num <= self.element_multiplier:
            beam3 = [v[3] for v in self.GoodBeam]                                 # PD0 1 - RTB 3
            return [round((v * 100.0) / pings_per_ens) for v in beam3]            # Convert to percent

        if pd0_beam_num == 2 and pd0_beam_num <= self.element_multiplier:
            beam1 = [v[1] for v in self.GoodBeam]                                 # PD0 2 - RTB 1
            return [round((v * 100.0) / pings_per_ens) for v in beam1]            # Convert to percent

        if pd0_beam_num == 3 and pd0_beam_num <= self.element_multiplier:
            beam0 = [v[0] for v in self.GoodBeam]                                 # PD0 3 - RTB 0
            return [round((v * 100.0) / pings_per_ens) for v in beam0]            # Convert to percent

        return None
