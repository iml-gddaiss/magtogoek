import socket
import datetime

import logging

from rti_python.Codecs.BinaryCodec import BinaryCodec
from rti_python.Ensemble.Ensemble import Ensemble

from rti_python.Utilities.events import EventHandler


class EnsembleMetaData:
    """
    Meta Data for the ensemble.
    THis includes the revision and host information.
    """
    def __init__(self):
        self.Revision = "1.0"
        self.Host = socket.gethostname()
        self.HostIp = socket.gethostbyname(socket.gethostname())

        # Get the external IP address of the computer
        #url = "http://checkip.dyndns.org"
        #request = requests.get(url)
        #clean = request.text.split(': ', 1)[1]
        #your_ip = clean.split('</body></html>', 1)[0]
        #self.HostExtIp = your_ip


class ProjectInfo:
    """
    Information about the project that collected this data.
    """
    def __init__(self):
        self.ProjectName = ""
        self.Username = ""
        self.Lat = ""
        self.Lon = ""
        self.DateCreated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        self.DateModified = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

class BinaryCodecUdp(BinaryCodec):
    """
    Decode RoweTech ADCP Binary data.
    """

    def __init__(self, udp_port):
        super().__init__()
        # Set meta data
        self.Meta = EnsembleMetaData()

        # Set ProjectInfo
        #self.ProjectInfo = ProjectInfo()

        logging.info("Binary codec - UDP Port: " + str(udp_port))

        # Create socket
        self.udp_port = udp_port                                        # UDP Port
        self.udp_ip = '127.0.0.1'                                       # UDP IP (Localhost)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP Socket

    def shutdown(self):
        """
        Do nothing
        :return:
        """
        pass

    def process_ens(self, ensemble):
        # Pass to event handler
        self.ensemble_event(ensemble)

        try:
            # Stream data
            self.stream_data(ensemble)

            logging.debug("Stream ensemble data")
        except ConnectionRefusedError as err:
            logging.error("Error streaming ensemble data", err)
        except Exception as err:
            logging.error("Error streaming ensemble data", err)

    def stream_data(self, ens):
        """
        Stream the data to the UDP port.
        When converting the dataset to JSON, a newline will be added
        to end of the JSON string.  This will allow the user to separate
        the JSON strings.
        :param ens: Ensemble data to stream.
        """
        serial_number = ""
        ensemble_number = 0
        date_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

        if ens.IsEnsembleData:
            # Get the serial number, ensemble number and the date and time to share with all the data
            serial_number = ens.EnsembleData.SerialNumber
            ensemble_number = ens.EnsembleData.EnsembleNumber
            if ens.EnsembleData.Month > 0:
                date_time = datetime.datetime(year=ens.EnsembleData.Year,
                                              month=ens.EnsembleData.Month,
                                              day=ens.EnsembleData.Day,
                                              hour=ens.EnsembleData.Hour,
                                              minute=ens.EnsembleData.Minute,
                                              second=ens.EnsembleData.Second,
                                              microsecond=round(ens.EnsembleData.HSec*10000)).strftime("%Y-%m-%d %H:%M:%S.%f")

                # Stream the data
                ens.EnsembleData.DateTime = date_time
            else:
                logging.error("BAD Date and Time: " + str(ensemble_number))

            ens.EnsembleData.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.EnsembleData).encode())

        if ens.IsBeamVelocity:
            ens.Wt.EnsembleNumber = ensemble_number
            ens.Wt.SerialNumber = serial_number
            ens.Wt.DateTime = date_time
            ens.Wt.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.Wt).encode())

        if ens.IsInstrumentVelocity:
            ens.InstrumentVelocity.EnsembleNumber = ensemble_number
            ens.InstrumentVelocity.SerialNumber = serial_number
            ens.InstrumentVelocity.DateTime = date_time
            ens.InstrumentVelocity.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.InstrumentVelocity).encode())

        if ens.IsEarthVelocity:
            ens.EarthVelocity.EnsembleNumber = ensemble_number
            ens.EarthVelocity.SerialNumber = serial_number
            ens.EarthVelocity.DateTime = date_time
            ens.EarthVelocity.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.EarthVelocity).encode())

        if ens.IsAmplitude:
            ens.Amplitude.EnsembleNumber = ensemble_number
            ens.Amplitude.SerialNumber = serial_number
            ens.Amplitude.DateTime = date_time
            ens.Amplitude.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.Amplitude).encode())

        if ens.IsCorrelation:
            ens.Correlation.EnsembleNumber = ensemble_number
            ens.Correlation.SerialNumber = serial_number
            ens.Correlation.DateTime = date_time
            ens.Correlation.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.Correlation).encode())

        if ens.IsGoodBeam:
            ens.GoodBeam.EnsembleNumber = ensemble_number
            ens.GoodBeam.SerialNumber = serial_number
            ens.GoodBeam.DateTime = date_time
            ens.GoodBeam.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.GoodBeam).encode())

        if ens.IsGoodEarth:
            ens.GoodEarth.EnsembleNumber = ensemble_number
            ens.GoodEarth.SerialNumber = serial_number
            ens.GoodEarth.DateTime = date_time
            ens.GoodEarth.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.GoodEarth).encode())

        if ens.IsAncillaryData:
            ens.AncillaryData.EnsembleNumber = ensemble_number
            ens.AncillaryData.SerialNumber = serial_number
            ens.AncillaryData.DateTime = date_time
            ens.AncillaryData.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.AncillaryData).encode())

        if ens.IsBottomTrack:
            ens.BottomTrack.EnsembleNumber = ensemble_number
            ens.BottomTrack.SerialNumber = serial_number
            ens.BottomTrack.DateTime = date_time
            ens.BottomTrack.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.BottomTrack).encode())

        if ens.IsRangeTracking:
            ens.RangeTracking.EnsembleNumber = ensemble_number
            ens.RangeTracking.SerialNumber = serial_number
            ens.RangeTracking.DateTime = date_time
            ens.RangeTracking.Meta = self.Meta
            self.send_udp(Ensemble().toJSON(ens.RangeTracking).encode())

    def send_udp(self, data):
        """
        Send the data to the UDP port.
        Ensemble().toJSON added a newline at the end of the JSON
        string.  This will allow anyone looking for the JSON data
        to separate the JSON data by newline.
        :param data: Data to send.
        """
        self.socket.sendto(data, (self.udp_ip, self.udp_port))
