from rti_python.Ensemble.Ensemble import Ensemble
import logging


class BeamVelocity:
    """
    Beam Velocity DataSet.
    [Bin x Beam] data.
    """

    def __init__(self, num_elements, element_multiplier):
        """
        Beam Velocity data.
        :param num_elements: Number of bins
        :param element_multiplier: Number of beams.
        """
        self.ds_type = 10
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000001\0"
        self.Velocities = []
        # Create enough entries for all the (bins x beams)
        # Initialize with bad values
        for bins in range(num_elements):
            bins = []
            for beams in range(element_multiplier):
                bins.append([Ensemble().BadVelocity])

            self.Velocities.append(bins)

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the velocities.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                self.Velocities[bin_num][beam] = Ensemble.GetFloat(packet_pointer, Ensemble().BytesInFloat, data)
                packet_pointer += Ensemble().BytesInFloat

        logging.debug(self.Velocities)

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
                val = self.Velocities[bin_num][beam]
                result += Ensemble.float_to_bytes(val)

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
                val = self.Velocities[bin_num][beam]

                # Create the CSV string
                str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_BEAM_VEL, ss_code, ss_config, bin_num, beam, blank, bin_size, val))

        return str_result

    def pd0_mm_per_sec(self, pd0_beam_num: int):
        """
        Convert the Beam Velocity from m/s to mm/s and as an integer.

        Also remap the Beam numbers to match PD0 beams.
        RTB and PD0 do not share the same Beam Order
        RTB BEAM 0,1,2,3 = PD0 BEAM 3,2,0,1

        :param pd0_beam_num: PD0 Beam number.
        :type pd0_beam_num: Integer
        :return: A list of all the velocities for the given PD0 beam, converted to mm/s for the beam.  The beam will be based on reordering for PD0
        :rtype: List or None if beam number is not correct.
        """

        # Remap the beam number
        # beam order 3,2,0,1
        rti_beam_num = 0
        if self.element_multiplier == 1:                # Vertical beam
            rti_beam_num = 0
        elif pd0_beam_num == 0:
            rti_beam_num = 2
        elif pd0_beam_num == 1:
            rti_beam_num = 3
        elif pd0_beam_num == 2:
            rti_beam_num = 1
        elif pd0_beam_num == 3:
            rti_beam_num = 0

        # Replace the RTB BAD_Velocity (88.888) to PD0 BAD_VELOCITY (-32768)
        pd0_vel_data = []
        for bin_idx in range(self.num_elements):
            if Ensemble.is_bad_velocity(self.Velocities[bin_idx][rti_beam_num]):
                pd0_vel_data.append(-32768)
            else:
                pd0_vel_data.append(round(self.Velocities[bin_idx][rti_beam_num] * 1000.0))  # Convert to mm/s and integer

        return pd0_vel_data

