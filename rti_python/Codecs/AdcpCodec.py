import logging
from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Codecs.BinaryCodecUdp import BinaryCodecUdp
from obsub import event


class AdcpCodec:
    """
    ADCP Codec will decode the 
    ADCP data.  There are more than one ADCP format, this will use all the different
    codecs to decode the data.
    """

    def __init__(self, is_udp=False, udp_port=55057):
        if not is_udp:
            self.binary_codec = BinaryCodec()
        else:
            self.binary_codec = BinaryCodecUdp(udp_port)

        # Setup the event handler
        self.binary_codec.ensemble_event += self.process_ensemble

    def shutdown(self):
        """
        Shutdown the object.
        :return:
        """
        self.binary_codec.shutdown()

    def add(self, data):
        """
        Add the data to the codecs.
        :param data: Raw data to add to the codecs.
        """
        self.binary_codec.add(data)

    def process_ensemble(self, sender, ens):
        """
        Take the ensemble from the codec and pass it to all the subscribers.
        If the WaveForce codec is enabled, pass the ensemble to the WaveForce
        codec to process.
        :param ens: Ensemble data.
        """
        logging.debug("Received processed ensemble")

        # Pass ensemble to all subscribers of the ensemble data.
        self.ensemble_event(ens)

    @event
    def ensemble_event(self, ens):
        """
        Event to subscribe to this object to receive the latest ensemble data.
        :param ens: Ensemble object.
        :return:
        """
        logging.debug("Ensemble received")

    def decode_BREAK(self, break_ascii: str):
        """
        Decode a BREAK statement.
        This will return a dictionary with the BREAK information.
        This is a way to get the serial number and firmware version.

        Copyright (c) 2009-2019 Rowe Technologies Inc. All rights reserved.
        Doppler Velocity Log
        DP600
        SN: 01300000000000000000000000000682
        FW: 00.02.142 Jun 23 2020 10:29:48
        """
        break_result = {
            "serial_number": 0,
            "serial_number_str": "",
            "firmware_str": "",
            "freq_list_str": "",
            "mode": "",
        }

        # Break up the result to lines
        break_lines = break_ascii.splitlines(keepends=False)

        for break_line in break_lines:
            # Get the serial number
            if "SN" in break_line:
                serial_line = break_line.split(':')
                if len(serial_line) > 1:
                    break_result["serial_number_str"] = serial_line[1]

                    # Convert the last 5 charaters to a serial number integer
                    break_result["serial_number"] = int(serial_line[1][-5:])

            # Get the Firwmare
            if "FW" in break_line:
                fw_line = break_line.split(':')
                if len(fw_line) > 1:
                    break_result["firmware_str"] = fw_line[1]

        # Get the remaining information
        if len(break_lines) >= 6:
            break_result["mode"] = break_lines[2]
            break_result["freq_list_str"] = break_lines[3]

        return break_result

