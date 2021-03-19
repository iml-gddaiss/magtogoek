from rti_python.Ensemble.Ensemble import Ensemble
import logging


class RangeTracking:
    """
    Range Tracking DataSet.
    Values that give details about the wave heights.
    """

    def __init__(self, num_elements=8, element_multiplier=1):
        self.ds_type = 10                   # Float
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000015\0"

        self.NumBeams = 0.0
        self.SNR = []
        self.Range = []
        self.Pings = []
        self.Amplitude = []
        self.Correlation = []
        self.BeamVelocity = []
        self.InstrumentVelocity = []
        self.EarthVelocity = []

    def decode(self, data):
        """
        Take the data bytearray.  Decode the data to populate
        the values.
        :param data: Bytearray for the dataset.
        """
        packet_pointer = Ensemble.GetBaseDataSize(self.name_len)

        self.NumBeams = Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 0, Ensemble().BytesInFloat, data)

        self.num_elements = (8 * int(self.NumBeams)) + 1

        if self.NumBeams == 4.0:
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 1, Ensemble().BytesInFloat, data))
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 2, Ensemble().BytesInFloat, data))
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 3, Ensemble().BytesInFloat, data))
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 4, Ensemble().BytesInFloat, data))

            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 5, Ensemble().BytesInFloat, data))
            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 6, Ensemble().BytesInFloat, data))
            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 7, Ensemble().BytesInFloat, data))
            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 8, Ensemble().BytesInFloat, data))

            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 9, Ensemble().BytesInFloat, data))
            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 10, Ensemble().BytesInFloat, data))
            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 11, Ensemble().BytesInFloat, data))
            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 12, Ensemble().BytesInFloat, data))

            if len(data) > 80:
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 13, Ensemble().BytesInFloat, data))
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 14, Ensemble().BytesInFloat, data))
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 15, Ensemble().BytesInFloat, data))
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 16, Ensemble().BytesInFloat, data))

                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 17, Ensemble().BytesInFloat, data))
                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 18, Ensemble().BytesInFloat, data))
                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 19, Ensemble().BytesInFloat, data))
                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 20, Ensemble().BytesInFloat, data))

                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 21, Ensemble().BytesInFloat, data))
                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 22, Ensemble().BytesInFloat, data))
                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 23, Ensemble().BytesInFloat, data))
                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 24, Ensemble().BytesInFloat, data))

                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 25, Ensemble().BytesInFloat, data))
                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 26, Ensemble().BytesInFloat, data))
                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 27, Ensemble().BytesInFloat, data))
                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 28, Ensemble().BytesInFloat, data))

                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 29, Ensemble().BytesInFloat, data))
                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 30, Ensemble().BytesInFloat, data))
                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 31, Ensemble().BytesInFloat, data))
                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 32, Ensemble().BytesInFloat, data))

        elif self.NumBeams == 3.0:
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 1, Ensemble().BytesInFloat, data))
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 2, Ensemble().BytesInFloat, data))
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 3, Ensemble().BytesInFloat, data))

            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 4, Ensemble().BytesInFloat, data))
            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 5, Ensemble().BytesInFloat, data))
            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 6, Ensemble().BytesInFloat, data))

            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 7, Ensemble().BytesInFloat, data))
            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 8, Ensemble().BytesInFloat, data))
            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 9, Ensemble().BytesInFloat, data))

            if len(data) > 68:
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 10, Ensemble().BytesInFloat, data))
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 11, Ensemble().BytesInFloat, data))
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 12, Ensemble().BytesInFloat, data))

                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 13, Ensemble().BytesInFloat, data))
                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 14, Ensemble().BytesInFloat, data))
                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 15, Ensemble().BytesInFloat, data))

                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 16, Ensemble().BytesInFloat, data))
                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 17, Ensemble().BytesInFloat, data))
                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 18, Ensemble().BytesInFloat, data))

                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 19, Ensemble().BytesInFloat, data))
                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 20, Ensemble().BytesInFloat, data))
                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 21, Ensemble().BytesInFloat, data))

                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 22, Ensemble().BytesInFloat, data))
                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 23, Ensemble().BytesInFloat, data))
                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 24, Ensemble().BytesInFloat, data))

        elif self.NumBeams == 2.0:
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 1, Ensemble().BytesInFloat, data))
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 2, Ensemble().BytesInFloat, data))

            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 3, Ensemble().BytesInFloat, data))
            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 4, Ensemble().BytesInFloat, data))

            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 5, Ensemble().BytesInFloat, data))
            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 6, Ensemble().BytesInFloat, data))

            if len(data) > 56:
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 7, Ensemble().BytesInFloat, data))
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 8, Ensemble().BytesInFloat, data))

                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 9, Ensemble().BytesInFloat, data))
                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 10, Ensemble().BytesInFloat, data))

                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 11, Ensemble().BytesInFloat, data))
                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 12, Ensemble().BytesInFloat, data))

                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 13, Ensemble().BytesInFloat, data))
                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 14, Ensemble().BytesInFloat, data))

                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 15, Ensemble().BytesInFloat, data))
                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 16, Ensemble().BytesInFloat, data))

        elif self.NumBeams == 1.0:
            self.SNR.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 1, Ensemble().BytesInFloat, data))
            self.Range.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 2, Ensemble().BytesInFloat, data))
            self.Pings.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 3, Ensemble().BytesInFloat, data))

            if len(data) > 44:
                self.Amplitude.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 4, Ensemble().BytesInFloat, data))
                self.Correlation.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 5, Ensemble().BytesInFloat, data))
                self.BeamVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 6, Ensemble().BytesInFloat, data))
                self.InstrumentVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 7, Ensemble().BytesInFloat, data))
                self.EarthVelocity.append(Ensemble.GetFloat(packet_pointer + Ensemble().BytesInFloat * 8, Ensemble().BytesInFloat, data))

        logging.debug(self.NumBeams)
        logging.debug(self.SNR)
        logging.debug(self.Range)
        logging.debug(self.Pings)
        logging.debug(self.Amplitude)
        logging.debug(self.Correlation)
        logging.debug(self.BeamVelocity)
        logging.debug(self.InstrumentVelocity)
        logging.debug(self.EarthVelocity)

    def encode(self):
        """
        Encode the data into RTB format.
        :return:
        """
        result = []

        self.num_elements = (8 * int(self.NumBeams)) + 1     # 8 is the number of list plus 1 for NumBeams

        # Generate header
        result += Ensemble.generate_header(self.ds_type,
                                           self.num_elements,
                                           self.element_multiplier,
                                           self.image,
                                           self.name_len,
                                           self.Name)

        # Add the data
        result += Ensemble.float_to_bytes(self.NumBeams)

        for beam in range(len(self.SNR)):
            result += Ensemble.float_to_bytes(self.SNR[beam])

        for beam in range(len(self.Range)):
            result += Ensemble.float_to_bytes(self.Range[beam])

        for beam in range(len(self.Pings)):
            result += Ensemble.float_to_bytes(self.Pings[beam])

        for beam in range(len(self.Amplitude)):
            result += Ensemble.float_to_bytes(self.Amplitude[beam])

        for beam in range(len(self.Correlation)):
            result += Ensemble.float_to_bytes(self.Correlation[beam])

        for beam in range(len(self.BeamVelocity)):
            result += Ensemble.float_to_bytes(self.BeamVelocity[beam])

        for beam in range(len(self.InstrumentVelocity)):
            result += Ensemble.float_to_bytes(self.InstrumentVelocity[beam])

        for beam in range(len(self.EarthVelocity)):
            result += Ensemble.float_to_bytes(self.EarthVelocity[beam])

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

        # Create the CSV strings
        for beams in range(len(self.Range)):
            str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_RT_RANGE, ss_code, ss_config, 0, beams, blank, bin_size, self.Range[beams]))

        for beams in range(len(self.Pings)):
            str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_RT_PINGS, ss_code, ss_config, 0, beams, blank, bin_size, self.Pings[beams]))

        for beams in range(len(self.BeamVelocity)):
            str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_RT_BEAM_VEL, ss_code, ss_config, 0, beams, blank, bin_size, self.BeamVelocity[beams]))

        for beams in range(len(self.InstrumentVelocity)):
            str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_RT_INSTR_VEL, ss_code, ss_config, 0, beams, blank, bin_size, self.InstrumentVelocity[beams]))

        for beams in range(len(self.EarthVelocity)):
            str_result.append(Ensemble.gen_csv_line(dt, Ensemble.CSV_RT_EARTH_VEL, ss_code, ss_config, 0, beams, blank, bin_size, self.EarthVelocity[beams]))

        return str_result

    def avg_range(self):
        """
        Average the range values.
        Only accumulate the good values.
        :return: Average of the range values.
        """

        # Accumulate the data
        avg = 0.0
        cnt = 0
        for rng in self.Range:
            if rng > 0.0:
                avg += rng
                cnt += 1

        # Average the data and return it
        if cnt >= 1:
            return avg / cnt

        return 0.0


