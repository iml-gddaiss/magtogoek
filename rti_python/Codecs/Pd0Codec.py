import struct
import sys
import numpy as np
import math
import datetime as dt
import logging
from obsub import event
from typing import List, Set, Dict, Tuple, Optional


class Pd0Codec:

    @event
    def ensemble_event(self, ens):
        """
        Event to subscribe to receive the latest ensemble data.
        :param ens: Ensemble object
        :return:
        """
        if ens:
            logging.debug(str(ens))

    def decode(self, file_path: str):
        """
        Decode the ensemble data based on the file path given.
        Then pass all the ensembles to the event.
        :param file_path: File path to the PD0 data file.
        :type file_path: String file path.
        :return: Number of ensembles found and number of errors with ensembles.
        :rtype: int, int
        """

        ens2process = [0, -1]   # [start, end] ensembles to export.  end = -1 for all ensembles in file
        verbose = True  # diagnostic, True = turn on output, False = silent

        maxens, ens_len, ens_data, data_start_posn = self.analyze_pd0_file(file_path, verbose)

        infile = open(file_path, 'rb')

        infile.seek(data_start_posn)

        if (ens2process[1] < 0) or ens2process[1] == np.inf:
            ens2process[1] = maxens

        # we want to save the time stamp from this ensemble since it is the
        # time from which all other times in the file will be relative to
        t0 = ens_data['VLeader']['dtobj']

        ensemble_count = 0
        verbose = False  # diagnostic, True = turn on output, False = silent
        nslantbeams = 4

        # priming read - for the while loop
        # note that ensemble lengths can change in the middle of the file!
        # horribly inefficient, but here we go, one step backward, two forward...
        bookmark = infile.tell()  # save beginning of next ensemble
        # need to read the header from the file to know the ensemble size
        header = self.read_header(infile)
        if header['sourceID'] != b'\x7f':
            print('non-currents ensemble found at %d' % bookmark)

        if ens_len != header['nbytesperens'] + 2:
            ens_len = header['nbytesperens'] + 2  # update to what we have

        # go back to where this ensemble started before we checked the header
        infile.seek(bookmark)
        ens = infile.read(ens_len)
        ens_error = None

        while len(ens) > 0:
            # print('-- ensemble %d length %g, file position %g' % (ensemble_count, len(ens), infile.tell()))
            # print(ens_data['header'])
            ens_data, ens_error = self.parse_ensemble(ens, verbose)

            # Pass the ensemble to the event
            if ens_data:
                self.ensemble_event(ens_data)

            ensemble_count += 1

            if ensemble_count > maxens:
                print('stopping at estimated end of file ensemble %d' % ens2process[1])
                break

            n = 10000

            ensf, ensi = math.modf(ensemble_count / n)
            if ensf == 0:
                print('%d ensembles read at %s and Rowe #%d' % (ensemble_count, ens_data['VLeader']['dtobj'],
                                                                ens_data['VLeader']['Ensemble_Number']))

            if ensemble_count >= ens2process[1] - 1:
                print('stopping at requested ensemble %d' % ens2process[1])
                break

            # note that ensemble lengths can change in the middle of the file!
            # TODO - is there a faster way to do this??
            bookmark = infile.tell()  # save beginning of next ensemble
            # TODO - since we are jumping around, we should check here to see
            #   how close to the end of the file we are - if it is within one
            #   header length - we are done
            #   need to read the header from the file to know the ensemble size
            header = self.read_header(infile)

            if header is None:
                # we presume this is the end of the file, since we don't have header info
                print('end of file reached with incomplete header')
                break

            if header['sourceID'] != b'\x7f':
                print('non-currents ensemble found at %d' % bookmark)

            if ens_len != header['nbytesperens'] + 2:
                ens_len = header['nbytesperens'] + 2  # update to what we have

            # TODO - fix this so that we aren't going back and forth, it is really slow
            # go back to where this ensemble started before we checked the header
            infile.seek(bookmark)
            ens = infile.read(ens_len)

        else:  # while len(ens) > 0:
            print('end of file reached')

        if ensemble_count < maxens:
            print('end of file reached after %d ensembles, less than estimated in the file' % ensemble_count)
        elif ensemble_count > maxens:
            print('end of file reached after %d ensembles, more than estimated in the file' % ensemble_count)

        infile.close()

        print('%d ensembles read' % (ensemble_count))

        return ensemble_count, ens_error

    def parse_ensemble(self, ens_bytes: [], verbose: bool):
        """
        convert the binary data for one ensemble to a dictionary of readable data
        :param binary ens_bytes: the raw binary data for the ensemble
        :param verbose: print out the data as it is converted
        :return: a dictionary of the data, a string describing any errors
        """
        ens_data = {}
        ens_error = None
        ens_data['Header'] = self.parse_header(ens_bytes)

        for i in range(ens_data['Header']['ndatatypes']):
            # go to each offset and parse depending on what we find
            offset = ens_data['Header']['offsets'][i]
            # raw, val = __parseTRDIushort(ensbytes, offset)
            val = struct.unpack('<H', ens_bytes[offset:offset + 2])[0]
            if val == 0:  # \x00\x00
                if verbose:
                    print('Fixed Leader found at %g' % offset)
                ens_data['FLeader'] = self.parse_fixed_leader(ens_bytes, offset)
                # we need this to decode the other data records
                ncells = int(ens_data['FLeader']['Number_of_Cells'])
                nbeams = 4  # the 5th beam has it's own record
            elif val == 128:  # \x80\x00
                if verbose:
                    print('Variable Leader found at %g' % offset)
                ens_data['VLeader'] = self.parse_variable_leader(ens_bytes, offset)
                # print(VLeader)
            elif val == 256:  # raw == b'\x00\x01': 256
                if verbose:
                    print('Velocity found at %g' % offset)
                ens_data['VData'] = self.parse_velocity(ens_bytes, offset, ncells, nbeams)
            elif val == 512:  # raw == b'\x00\x02':
                if verbose:
                    print('Correlation found at %g' % offset)
                ens_data['CData'] = self.parse_correlation(ens_bytes, offset, ncells, nbeams)
            elif val == 768:  # raw == b'\x00\x03':
                if verbose:
                    print('Intensity found at %g' % offset)
                ens_data['IData'] = self.parse_intensity(ens_bytes, offset, ncells, nbeams)
            elif val == 1024:  # raw == b'\x00\x04':
                if verbose:
                    print('PGood found at %g' % offset)
                ens_data['GData'] = self.parse_percent_good(ens_bytes, offset, ncells, nbeams)
            elif val == 1280:  # raw == b'\x00\x05':
                if verbose:
                    print('Status profile found at %g' % offset)
            elif val == 1536:  # raw == b'\x00\x06':
                if verbose:
                    print('BT found at %g' % offset)
                ens_data['BTData'] = self.parse_bottom_track(ens_bytes, offset, nbeams)
            elif val == 1792:  # raw == b'\x00\x07':
                # this not defined in TRDI docs
                pass
            elif val == 2048:  # raw == b'\x00\x08':
                if verbose:
                    print('MicroCAT data found at %g' % offset)
            elif val == 12800:  # raw == b'\x00\x32': #12800
                if verbose:
                    print('Instrument transformation found at %g' % offset)
                ens_data['XformMatrix'] = self.parse_transformation_matrix(ens_bytes, offset, nbeams)
            elif val == 28672:  # raw == b'\x00\x70':
                if verbose:
                    print('V Series system config found at %g' % offset)
                ens_data['VSysConfig'] = self.parse_vertical_system_configuration(ens_bytes, offset)
            elif val == 28673:  # raw == b'\x01\x70':
                if verbose:
                    print('V Series ping setup found at %g' % offset)
                ens_data['VPingSetup'] = self.parse_vertical_ping_setup(ens_bytes, offset)
            elif val == 28674:  # raw == b'\x02\x70':
                if verbose:
                    print('V Series ADC Data found at %g' % offset)
                    # currently not defined well in TRDI docs
            elif val == 28675:  # raw == b'\x03\x70':
                if verbose:
                    print('V Series System Configuration Data found at %g' % offset)
                    # currently not defined well in TRDI docs
            elif val == 3841:  # raw == b'\x01\x0f':
                if verbose:
                    print('Vertical Beam Leader Data found at %g' % offset)
                ens_data['VBeamLeader'] = self.parse_vertical_beam_leader(ens_bytes, offset)
            elif val == 2560:  # raw == b'\x00\x0a':
                if verbose:
                    print('Vertical Beam Velocity Data found at %g' % offset)
                ens_data['VBeamVData'] = self.parse_vertical_velocity(ens_bytes, offset,
                                                                      ens_data['VBeamLeader']['Vertical_Depth_Cells'])
            elif val == 2816:  # raw == b'\x00\x0b':
                if verbose:
                    print('Vertical Beam Correlation Data found at %g' % offset)
                ens_data['VBeamCData'] = self.parse_vertical_correlation(ens_bytes, offset,
                                                                         ens_data['VBeamLeader'][
                                                                             'Vertical_Depth_Cells'])
            elif val == 3072:  # raw == b'\x00\x0c':
                if verbose:
                    print('Vertical Beam Amplitude Data found at %g' % offset)
                ens_data['VBeamIData'] = self.parse_vertical_intensity(ens_bytes, offset,
                                                                       ens_data['VBeamLeader']['Vertical_Depth_Cells'])
            elif val == 3328:  # raw == b'\x00\x0d':
                if verbose:
                    print('Vertical Beam Percent Good Data found at %g' % offset)
                ens_data['VBeamGData'] = self.parse_vertical_percent_good(ens_bytes, offset,
                                                                          ens_data['VBeamLeader'][
                                                                              'Vertical_Depth_Cells'])
            elif val == 28676:  # raw == b'\x40\x70':
                if verbose:
                    print('V Series Event Log Data found at %g' % offset)
            elif val == 11:  # raw == b'\x0b\x00':
                if verbose:
                    print('Wavesmon 4 Wave Parameters found at %g' % offset)
                ens_data['WaveParams'] = self.parse_wave_parameters(ens_bytes, offset)
            elif val == 12:  # raw == b'\x0c\x00':
                if verbose:
                    print('Wavesmon 4 Sea and Swell found at %g' % offset)
                ens_data['WaveSeaSwell'] = self.parse_wave_sea_swell(ens_bytes, offset)
            else:
                print('ID %d unrecognized at %g' % (val, offset))
                ens_error = 'no ID'

        csum = self.compute_checksum(ens_bytes)
        if csum != (ens_bytes[-2] + (ens_bytes[-1] << 8)):
            ens_error = 'checksum failure'

        return ens_data, ens_error

    def analyze_pd0_file(self, pd0file, verbose=False):
        """
        determine the input file size, read some ensembles, make an estimate of the number of ensembles within, return the
            data from the first ensemble.
        :param str pd0file: path and file name to raw ADC data file in pd0 format
        :param bool verbose: output ensemble information
        :return: number of ensembles in file, number of bytes in each ensemble, data from the first ensemble,
            number of bytes to the start of the data
        """
        infile = open(pd0file, 'rb')

        while infile.tell() < 3000:
            b1 = infile.read(1)
            if b1 == b'\x7f':
                b2 = infile.read(1)
                if b2 == b'\x7f':
                    break
        else:
            print('Desired TRDI 7f7f ID not found within 3 kB from beginning of the file')
            infile.close()
            sys.exit(1)

        start_of_data = infile.tell() - 2
        if start_of_data != 0:
            print('data starts %d bytes into the file' % start_of_data)
        infile.seek(start_of_data)

        # need to read the header from the file to know the ensemble size
        header = self.read_TRDI_header(infile)

        if header['sourceID'] != b'\x7f':
            print('error - this is not a currents file')
            infile.close()

        # number of bytes per ensemble in the header does not include the checksum
        ens_len = header['nbytesperens'] + 2
        print('ensemble length = %g' % ens_len)
        print(header)
        # it is faster to define the netCDF file with a known length
        # for this we need to estimate how many ensembles we will be reading
        # for some reason, sys.getsizeof(infile) does not report the true length
        # of the input file, so we will go to the end and see how far we have gone
        # there is a problem though.  While TRDI's documentation says the V Series
        # System Configuration data is always sent, this is not the case, so reading
        # only the first ensemble will not give the ensemble size typical over the
        # entire file
        # rewind and read this several ensembles because further in the ensemble
        # length can change on files output from Velocity
        infile.seek(start_of_data)

        nens2check = 5
        nbytesperens = [0 for i in range(nens2check)]
        ndatatypes = [0 for i in range(nens2check)]

        for i in range(nens2check):
            fileposn = infile.tell()
            header = self.read_header(infile)
            ens_len = header['nbytesperens'] + 2
            infile.seek(fileposn)
            ens_data, ens_error = self.parse_ensemble(infile.read(ens_len), verbose)
            if ens_error is not None:
                print('problem reading the first ensemble: ' + ens_error)
                # infile.close()
                # sys.exit(1)

            if i == 0:
                first_ens_data = ens_data
            print('ensemble %d has %d bytes and %d datatypes' % (ens_data['VLeader']['Ensemble_Number'],
                                                                 ens_data['Header']['nbytesperens'],
                                                                 ens_data['Header']['ndatatypes']))
            nbytesperens[i] = ens_data['Header']['nbytesperens'] + 2
            ndatatypes[i] = ens_data['Header']['ndatatypes']

        # the guess here is that if the first two ensembles are not the same,
        # it's the second ensemble that is representative of the data
        if nbytesperens[0] != nbytesperens[1]:
            ens_len = nbytesperens[1]
        else:
            ens_len = nbytesperens[0]

        infile.seek(0, 2)
        nbytesinfile = infile.tell()
        max_ens = (nbytesinfile / ens_len) - 1
        print('estimating %g ensembles in file using a %d ensemble size' % (max_ens, ens_len))

        infile.close()

        print(ens_data['Header'])
        print('ensemble length = %g' % ens_len)
        print('estimating %g ensembles in file' % max_ens)

        # return max_ens, ens_len, ens_data, start_of_data
        return max_ens, ens_len, first_ens_data, start_of_data

    def read_header(self, infile):
        """
        read the TRDI header bytes directly from a file pointer position and test for end of file
        :param infile: pointer to a file open for reading
        :return: a dictionary of the TRDI Header data
        """
        header_data = {}
        try:
            header_data['headerID'] = infile.read(1)
        except:
            return None
        try:
            header_data['sourceID'] = infile.read(1)
        except:
            return None
        try:
            header_data['nbytesperens'] = struct.unpack('<H', infile.read(2))[0]
        except:
            return None
        infile.read(1)  # spare, skip it
        header_data['ndatatypes'] = infile.read(1)[0]  # remember, bytes objects are arrays
        offsets = [0] * header_data['ndatatypes']  # predefine a list of ints to fill
        for i in range(header_data['ndatatypes']):
            offsets[i] = struct.unpack('<H', infile.read(2))[0]

        header_data['offsets'] = offsets

        return header_data

    def parse_header(self, bstream):
        """
        parse the TRDI header data for the number of data types and byte offsets to each
        :param bytes bstream: the raw binary header information
        :return: dictionary of readable header data
        """
        header_data = {
            'headerID': bstream[0],  # byte 1
            'sourceID': bstream[1],  # byte 2
            'nbytesperens': struct.unpack('<H', bstream[2:4])[0],
            # spare, skip it, byte 5
            'ndatatypes': bstream[5]  # byte 6
        }
        offsets = [0] * header_data['ndatatypes']  # predefine a list of ints to fill
        for i in range(header_data['ndatatypes']):
            offsets[i] = struct.unpack('<H', bstream[6 + i * 2:6 + i * 2 + 2])[0]

        header_data['offsets'] = offsets

        return header_data

    def parse_fixed_leader(self, bstream, offset):
        """
        parse the Fixed Leader section of data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: dictionary of readable fixed leader data
        """
        f_leader_data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 0:
            print("expected fixed leader ID, instead found %g", leader_id)
            return -1
        f_leader_data['CPU_Version'] = "%s.%s" % (bstream[offset + 2], bstream[offset + 4])

        f_leader_data['System_Configuration_LSB'] = self.bitstrLE(bstream[offset + 4])
        # anyone who has a better way to convert these bits, please tell me!
        f_leader_data['System_Frequency'] = int(f_leader_data['System_Configuration_LSB'][5:8], 2)
        sys_freqs = (75, 150, 300, 600, 1200, 2400)
        f_leader_data['System_Frequency'] = sys_freqs[f_leader_data['System_Frequency']]
        if f_leader_data['System_Configuration_LSB'][4] == "1":
            f_leader_data['Beam_Pattern'] = 'Convex'
        else:
            f_leader_data['Beam_Pattern'] = 'Concave'
        f_leader_data['Sensor_Configuration'] = int(f_leader_data['System_Configuration_LSB'][2:4], 2) + 1
        if f_leader_data['System_Configuration_LSB'][1] == "1":
            f_leader_data['Transducer_Head_Is_Attached'] = 'Yes'
        else:
            f_leader_data['Transducer_Head_Is_Attached'] = 'No'
        if f_leader_data['System_Configuration_LSB'][0] == "1":
            f_leader_data['Orientation'] = 'Up-facing beams'
        else:
            f_leader_data['Orientation'] = 'Down-facing beams'

        f_leader_data['System_Configuration_MSB'] = self.bitstrLE(bstream[offset + 5])
        f_leader_data['Beam_Angle'] = int(f_leader_data['System_Configuration_MSB'][5:8], 2)
        # the angles 15, 20, and 30 are used by the Workhorse
        # the angle 25 is used by the Sentinel V, and so far, is always 25
        angles = (15, 20, 30, 0, 0, 0, 0, 25)
        f_leader_data['Beam_Angle'] = angles[f_leader_data['Beam_Angle']]
        f_leader_data['Beam_Configuration'] = int(f_leader_data['System_Configuration_MSB'][0:4], 2)
        if f_leader_data['Beam_Configuration'] == 4:
            f_leader_data['Beam_Configuration'] = '4-bm janus'
        elif f_leader_data['Beam_Configuration'] == 5:
            f_leader_data['Beam_Configuration'] = '5-bm janus cfig demod'
        elif f_leader_data['Beam_Configuration'] == 15:
            f_leader_data['Beam_Configuration'] = '5-bm janus cfig (2 demod)'
        else:
            f_leader_data['Beam_Configuration'] = 'unknown'

        f_leader_data['Simulated_Data'] = bstream[offset + 6]

        f_leader_data['Lag_Length'] = bstream[offset + 7]
        f_leader_data['Number_of_Beams'] = bstream[offset + 8]
        f_leader_data['Number_of_Cells'] = bstream[offset + 9]
        f_leader_data['Pings_Per_Ensemble'] = struct.unpack('<h', bstream[offset + 10:offset + 12])[0]
        f_leader_data['Depth_Cell_Length_cm'] = struct.unpack('<h', bstream[offset + 12:offset + 14])[0]
        f_leader_data['Blank_after_Transmit_cm'] = struct.unpack('<h', bstream[offset + 14:offset + 16])[0]
        f_leader_data['Signal_Processing_Mode'] = bstream[offset + 16]
        f_leader_data['Low_Corr_Threshold'] = bstream[offset + 17]
        f_leader_data['No._Code_Reps'] = bstream[offset + 18]
        f_leader_data['PGd_Minimum'] = bstream[offset + 19]
        f_leader_data['Error_Velocity_Threshold'] = struct.unpack('<h', bstream[offset + 20:offset + 22])[0]
        # TODO ping group time needs to be formatted better
        f_leader_data['Time_Between_Ping Groups'] = "%03d:%02d:%02d" % (bstream[offset + 22], bstream[offset + 23],
                                                                        bstream[offset + 24])

        f_leader_data['Coord_Transform_LSB'] = self.bitstrLE(bstream[offset + 25])
        f_leader_data['Coord_Transform'] = int(f_leader_data['Coord_Transform_LSB'][3:5], 2)
        xforms = ('BEAM', 'INST', 'SHIP', 'EARTH')
        f_leader_data['Coord_Transform'] = xforms[f_leader_data['Coord_Transform']]
        if f_leader_data['Coord_Transform_LSB'][5] == '1':
            f_leader_data['Tilts_Used'] = 'Yes'
        else:
            f_leader_data['Tilts_Used'] = 'No'
        if f_leader_data['Coord_Transform_LSB'][6] == '1':
            f_leader_data['3-Beam_Solution_Used'] = 'Yes'
        else:
            f_leader_data['3-Beam_Solution_Used'] = 'No'
        if f_leader_data['Coord_Transform_LSB'][7] == '1':
            f_leader_data['Bin_Mapping_Used'] = 'Yes'
        else:
            f_leader_data['Bin_Mapping_Used'] = 'No'

        f_leader_data['Heading_Alignment_Hundredths_of_Deg'] = struct.unpack('<h', bstream[offset + 26:offset + 28])[0]
        f_leader_data['Heading_Bias_Hundredths_of_Deg'] = struct.unpack('<h', bstream[offset + 28:offset + 30])[0]

        f_leader_data['Sensor_Source_Byte'] = self.bitstrLE(bstream[offset + 30])
        if f_leader_data['Sensor_Source_Byte'][1] == '1':
            f_leader_data['Calculate_EC_from_ED_ES_and_ET'] = 'Yes'
        else:
            f_leader_data['Calculate_EC_from_ED_ES_and_ET'] = 'No'
        if f_leader_data['Sensor_Source_Byte'][2] == '1':
            f_leader_data['Uses_ED_from_depth_sensor'] = 'Yes'
        else:
            f_leader_data['Uses_ED_from_depth_sensor'] = 'No'
        if f_leader_data['Sensor_Source_Byte'][3] == '1':
            f_leader_data['Uses_EH_from_transducer_heading_sensor'] = 'Yes'
        else:
            f_leader_data['Uses_EH_from_transducer_heading_sensor'] = 'No'
        if f_leader_data['Sensor_Source_Byte'][4] == '1':
            f_leader_data['Uses_EP_from_transducer_pitch_sensor'] = 'Yes'
        else:
            f_leader_data['Uses_EP_from_transducer_pitch sensor'] = 'No'
        if f_leader_data['Sensor_Source_Byte'][5] == '1':
            f_leader_data['Uses_ER_from_transducer_roll_sensor'] = 'Yes'
        else:
            f_leader_data['Uses_ER_from_transducer_roll_sensor'] = 'No'
        if f_leader_data['Sensor_Source_Byte'][6] == '1':
            f_leader_data['Uses_ES_from_conductivity_sensor'] = 'Yes'
        else:
            f_leader_data['Uses_ES_from_conductivity_sensor'] = 'No'
        if f_leader_data['Sensor_Source_Byte'][7] == '1':
            f_leader_data['Uses_ET_from_transducer_temperature_sensor'] = 'Yes'
        else:
            f_leader_data['Uses_ET_from_transducer_temperature_sensor'] = 'No'

        f_leader_data['Sensor_Avail_Byte'] = self.bitstrLE(bstream[offset + 31])
        if f_leader_data['Sensor_Avail_Byte'][1] == '1':
            f_leader_data['Speed_of_sound_sensor_available'] = 'Yes'
        else:
            f_leader_data['Speed_of_sound_sensor_available'] = 'No'
        if f_leader_data['Sensor_Avail_Byte'][2] == '1':
            f_leader_data['Depth_sensor_available'] = 'Yes'
        else:
            f_leader_data['Depth_sensor_available'] = 'No'
        if f_leader_data['Sensor_Avail_Byte'][3] == '1':
            f_leader_data['Heading_sensor_available'] = 'Yes'
        else:
            f_leader_data['Heading_sensor_available'] = 'No'
        if f_leader_data['Sensor_Avail_Byte'][4] == '1':
            f_leader_data['Pitch_sensor_available'] = 'Yes'
        else:
            f_leader_data['Pitch_sensor_available'] = 'No'
        if f_leader_data['Sensor_Avail_Byte'][5] == '1':
            f_leader_data['Roll_sensor_available'] = 'Yes'
        else:
            f_leader_data['Roll_sensor_available'] = 'No'
        if f_leader_data['Sensor_Avail_Byte'][6] == '1':
            f_leader_data['Conductivity_sensor_available'] = 'Yes'
        else:
            f_leader_data['Conductivity_sensor_available'] = 'No'
        if f_leader_data['Sensor_Avail_Byte'][7] == '1':
            f_leader_data['Temperature_sensor_available'] = 'Yes'
        else:
            f_leader_data['Temperature_sensor_available'] = 'No'

        f_leader_data['Bin_1_distance_cm'] = struct.unpack('<h', bstream[offset + 32:offset + 34])[0]
        f_leader_data['Xmit_pulse_length_cm'] = struct.unpack('<h', bstream[offset + 34:offset + 36])[0]
        f_leader_data['Ref_Lyr_Avg_Starting_cell'] = bstream[offset + 36]
        f_leader_data['Ref_Lyr_Avg_Ending_cell'] = bstream[offset + 37]
        f_leader_data['False_Target_Threshold'] = bstream[offset + 38]
        f_leader_data['Transmit_lag_distance_cm'] = struct.unpack('<h', bstream[offset + 40:offset + 42])[0]
        f_leader_data['CPU_Board_Serial_Number'] = ""
        for i in range(8):
            f_leader_data['CPU_Board_Serial_Number'] = f_leader_data['CPU_Board_Serial_Number'] + \
                                                       ("%x" % bstream[offset + 42 + i])

        f_leader_data['System_Bandwidth'] = struct.unpack('<h', bstream[offset + 50:offset + 52])[0]
        f_leader_data['System_Power'] = bstream[offset + 52]
        f_leader_data['Base_Frequency_Index'] = bstream[offset + 53]
        # TODO these two need to be interpreted as spare if WH ADCP
        # rawBytes, f_leader_data['Serial Number for Remus only'] = struct.unpack('<H',infile.read(2))[0]
        # f_leader_data['Beam Angle for H-ADCP only'] = "%g" % infile.read(1)[0]

        return f_leader_data

    def parse_variable_leader(self, bstream, offset):
        """
        parse the Variable Leader section of data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: dictionary of readable variable leader data
        """
        v_leader_data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 128:
            print("expected variable leader ID, instead found %g", leader_id)
            return -1
        v_leader_data['Ensemble_Number'] = struct.unpack('<H', bstream[offset + 2:offset + 4])[0]
        v_leader_data['Year'] = bstream[offset + 4]
        if v_leader_data['Year'] < 50:  # circa 2000
            v_leader_data['Year'] += 2000
        else:
            v_leader_data['Year'] += 1900

        v_leader_data['Month'] = bstream[offset + 5]
        v_leader_data['Day'] = bstream[offset + 6]
        v_leader_data['Hour'] = bstream[offset + 7]
        v_leader_data['Minute'] = bstream[offset + 8]
        v_leader_data['Second'] = bstream[offset + 9]
        v_leader_data['Hundredths'] = bstream[offset + 10]
        v_leader_data['Ensemble_#_MSB'] = bstream[offset + 11]
        v_leader_data['Ensemble_Number'] = v_leader_data['Ensemble_Number'] + (v_leader_data['Ensemble_#_MSB'] << 16)

        v_leader_data['timestr'] = "%04d:%02d:%02d %02d:%02d:%02d.%03d" % (
            v_leader_data['Year'], v_leader_data['Month'],
            v_leader_data['Day'], v_leader_data['Hour'], v_leader_data['Minute'],
            v_leader_data['Second'], v_leader_data['Hundredths'])

        # compute time and time2
        jd = self.julian(v_leader_data['Year'], v_leader_data['Month'], v_leader_data['Day'],
                    v_leader_data['Hour'], v_leader_data['Minute'], v_leader_data['Second'],
                    v_leader_data['Hundredths'])
        v_leader_data['dtobj'] = dt.datetime(v_leader_data['Year'], v_leader_data['Month'], v_leader_data['Day'],
                                             v_leader_data['Hour'], v_leader_data['Minute'], v_leader_data['Second'],
                                             v_leader_data['Hundredths'] * 10000)
        # centiseconds * 10000 = microseconds
        jddt = Pd0Codec.ajd(v_leader_data['dtobj'])
        v_leader_data['julian_day_from_as_datetime_object'] = jddt
        v_leader_data['julian_day_from_julian'] = jd
        # v_leader_data['time'] = jd
        v_leader_data['EPIC_time'] = int(math.floor(jd))
        v_leader_data['EPIC_time2'] = int((jd - math.floor(jd)) * (24 * 3600 * 1000))

        v_leader_data['BIT_Result_Byte_13'] = self.bitstrLE(bstream[offset + 12])
        v_leader_data['Demod_1_error_bit'] = int(v_leader_data['BIT_Result_Byte_13'][3])
        v_leader_data['Demod_0_error_bit'] = int(v_leader_data['BIT_Result_Byte_13'][4])
        v_leader_data['Timing_Card_error_bit'] = int(v_leader_data['BIT_Result_Byte_13'][6])

        v_leader_data['Speed_of_Sound'] = struct.unpack('<H', bstream[offset + 14:offset + 16])[0]
        v_leader_data['Depth_of_Transducer'] = struct.unpack('<H', bstream[offset + 16:offset + 18])[0]
        v_leader_data['Heading, Pitch, Roll units'] = "hundredths_of_a_degree"
        v_leader_data['Heading'] = struct.unpack('<H', bstream[offset + 18:offset + 20])[0]
        v_leader_data['Pitch'] = struct.unpack('<h', bstream[offset + 20:offset + 22])[0]
        v_leader_data['Roll'] = struct.unpack('<h', bstream[offset + 22:offset + 24])[0]
        v_leader_data['Salinity'] = struct.unpack('<H', bstream[offset + 24:offset + 26])[0]
        v_leader_data['Temperature'] = struct.unpack('<H', bstream[offset + 26:offset + 28])[0]
        v_leader_data['MPT_minutes'] = bstream[offset + 28]
        v_leader_data['MPT_seconds'] = bstream[offset + 29]
        v_leader_data['MPT_hundredths'] = bstream[offset + 30]
        v_leader_data['H/Hdg_Std_Dev'] = bstream[offset + 31]
        v_leader_data['P/Pitch_Std_Dev'] = bstream[offset + 32]
        v_leader_data['R/Roll_Std_Dev'] = bstream[offset + 33]
        # the V Series PDO Output is different for the ADC channels
        # V PD0 this is ADC Channel 0 not used
        v_leader_data['Xmit_Current'] = bstream[offset + 34]  # ADC Channel 0
        # V PD0 this is ADC Channel 1 XMIT Voltage
        v_leader_data['Xmit_Voltage'] = bstream[offset + 35]  # ADC Channel 1
        # V PD0 this is ADC Channel 2 not used
        v_leader_data['Ambient_Temp'] = bstream[offset + 36]  # ADC Channel 2
        # V PD0 this is ADC Channel 3 not used
        v_leader_data['Pressure_(+)'] = bstream[offset + 37]  # ADC Channel 3
        # V PD0 this is ADC Channel 4 not used
        v_leader_data['Pressure_(-)'] = bstream[offset + 38]  # ADC Channel 4
        # V PD0 this is ADC Channel 5 not used
        v_leader_data['Attitude_Temp'] = bstream[offset + 39]  # ADC Channel 5
        # V PD0 this is ADC Channel 6 not used
        v_leader_data['Attitude'] = bstream[offset + 40]  # ADC Channel 6
        # V PD0 this is ADC Channel 7 not used
        v_leader_data['Contamination_Sensor'] = bstream[offset + 41]  # ADC Channel 7

        v_leader_data['Error_Status_Word_Low_16_bits_LSB'] = self.bitstrLE(bstream[offset + 42])
        v_leader_data['Bus_Error_exception'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][7])
        v_leader_data['Address_Error_exception'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][6])
        v_leader_data['Illegal_Instruction_exception'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][5])
        v_leader_data['Zero_Divide_exception'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][4])
        v_leader_data['Emulator_exception'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][3])
        v_leader_data['Unassigned_exception'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][2])
        v_leader_data['Watchdog_restart_occurred'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][1])
        v_leader_data['Battery_Saver_power'] = int(v_leader_data['Error_Status_Word_Low_16_bits_LSB'][0])

        v_leader_data['Error_Status_Word_Low_16_bits_MSB'] = self.bitstrLE(bstream[offset + 43])
        v_leader_data['Pinging'] = int(v_leader_data['Error_Status_Word_Low_16_bits_MSB'][7])
        v_leader_data['Cold_Wakeup_occurred'] = int(v_leader_data['Error_Status_Word_Low_16_bits_MSB'][1])
        v_leader_data['Unknown_Wakeup_occurred'] = int(v_leader_data['Error_Status_Word_Low_16_bits_MSB'][0])

        v_leader_data['Error_Status_Word_High_16_bits_LSB'] = self.bitstrLE(bstream[offset + 44])
        v_leader_data['Clock_Read_error_occurred'] = int(v_leader_data['Error_Status_Word_High_16_bits_LSB'][7])
        v_leader_data['Unexpected_alarm'] = int(v_leader_data['Error_Status_Word_High_16_bits_LSB'][6])
        v_leader_data['Clock_jump_forward'] = int(v_leader_data['Error_Status_Word_High_16_bits_LSB'][5])
        v_leader_data['Clock_jump_backward'] = int(v_leader_data['Error_Status_Word_High_16_bits_LSB'][4])

        v_leader_data['Error_Status_Word_High_16_bits_MSB'] = self.bitstrLE(bstream[offset + 42])
        v_leader_data['Power_Fail_(Unrecorded)'] = int(v_leader_data['Error_Status_Word_High_16_bits_MSB'][4])
        v_leader_data['Spurious_level_4_intr_(DSP)'] = int(v_leader_data['Error_Status_Word_High_16_bits_MSB'][3])
        v_leader_data['Spurious_level_5_intr_(UART)'] = int(v_leader_data['Error_Status_Word_High_16_bits_MSB'][2])
        v_leader_data['Spurious_level_6_intr_(CLOCK)'] = int(v_leader_data['Error_Status_Word_High_16_bits_MSB'][1])
        v_leader_data['Level_7_interrupt_occurred'] = int(v_leader_data['Error_Status_Word_High_16_bits_MSB'][0])

        # pressure of the water at the transducer head relative to one atmosphere (sea level)
        # v_leader_data['Pressure word byte 1'] = bitstrLE(bstream[offset+48])
        # v_leader_data['Pressure word byte 2'] = bitstrLE(bstream[offset+49])
        # v_leader_data['Pressure word byte 3'] = bitstrLE(bstream[offset+50])
        # v_leader_data['Pressure word byte 4'] = bitstrLE(bstream[offset+51])
        v_leader_data['Pressure_deca-pascals'] = bstream[offset + 48] + (bstream[offset + 49] << 8) + (
                    bstream[offset + 50] << 16) + \
                                                 (bstream[offset + 51] << 24)
        v_leader_data['Pressure_variance_deca-pascals'] = bstream[offset + 52] + (bstream[offset + 53] << 8) + \
                                                          (bstream[offset + 54] << 16) + (bstream[offset + 55] << 24)

        v_leader_data['RTC_Century'] = bstream[offset + 57]
        v_leader_data['RTC_Year'] = bstream[offset + 58]
        v_leader_data['RTC_Month'] = bstream[offset + 59]
        v_leader_data['RTC_Day'] = bstream[offset + 60]
        v_leader_data['RTC_Hour'] = bstream[offset + 61]
        v_leader_data['RTC_Minute'] = bstream[offset + 62]
        v_leader_data['RTC_Second'] = bstream[offset + 63]
        v_leader_data['RTC_Hundredths'] = bstream[offset + 64]

        return v_leader_data

    def parse_velocity(self, bstream, offset, ncells, nbeams):
        """
        parse the velocity data, each velocity value is stored as a two byte, twos complement integer [-32768 to 32767]
        with the LSB sent first.  Units are mm/s.  A value of -32768 = 0x8000 is a bad velocity value
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :param int nbeams: number of acoustic beams
        :return: velocity data as a beam x cell numpy array of ints
        """

        if bstream[offset + 1] != 1:
            print("expected velocity ID, instead found %g", bstream[offset + 1])
            return -1

        # start with a numpy array of bad values
        data = np.ones((nbeams, ncells), dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            for ibeam in range(nbeams):
                data[ibeam, icell] = struct.unpack('<h', bstream[offset + ibyte:offset + ibyte + 2])[0]
                ibyte = ibyte + 2

        return data

    def parse_correlation(self, bstream, offset, ncells, nbeams):
        """
        parse the correlation data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :param int nbeams: number of acoustic beams
        :return: correlation data as a beam x cell numpy array of ints
        """
        if bstream[offset + 1] != 2:
            print("expected correlation ID, instead found %g", bstream[offset + 1])
            return -1

        # start with a numpy array of bad values
        data = np.ones((nbeams, ncells), dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            for ibeam in range(nbeams):
                data[ibeam, icell] = bstream[offset + ibyte]
                ibyte = ibyte + 1

        return data

    def parse_intensity(self, bstream, offset, ncells, nbeams):
        """
        parse the intensity data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :param int nbeams: number of acoustic beams
        :return: intensity data as a beam x cell numpy array of ints
        """
        if bstream[offset + 1] != 3:
            print("expected intensity ID, instead found %g", bstream[offset + 1])
            return -1

        # start with a numpy array of bad values
        data = np.ones((nbeams, ncells), dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            for ibeam in range(nbeams):
                data[ibeam, icell] = bstream[offset + ibyte]
                ibyte = ibyte + 1

        return data

    def parse_percent_good(self, bstream, offset, ncells, nbeams):
        """
        parse the Percent Good data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :param int nbeams: number of acoustic beams
        :return: percent good data as a beam x cell numpy array of ints
        """
        if bstream[offset + 1] != 4:
            print("expected intensity ID, instead found %g", bstream[offset + 1])
            return -1

        # start with a numpy array of bad values
        data = np.ones((nbeams, ncells), dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            for ibeam in range(nbeams):
                data[ibeam, icell] = bstream[offset + ibyte]
                ibyte = ibyte + 1

        return data

    def parse_transformation_matrix(self, bstream, offset, nbeams):
        """
        parse the transformation matrix data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int nbeams: number of acoustic beams
        :return: transformation matrix data as a beam x 3 numpy array of ints
        """
        if bstream[offset + 1] != 50:  # \x00\x32
            print("expected transformation matrix ID, instead found %g", bstream[offset + 1])
            return -1

        # start with a numpy array of bad values
        data = np.zeros((nbeams, 3), dtype=int)
        ibyte = 2

        for iaxis in range(3):
            for ibeam in range(nbeams):
                data[ibeam, iaxis] = struct.unpack('<h', bstream[offset + ibyte:offset + ibyte + 2])[0]
                ibyte = ibyte + 2

        return data

    def parse_vertical_ping_setup(self, bstream, offset):
        """
        parse the TRDI V ping setup data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: a dict of readable ping setup settings
        """
        v_ping_setup_data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 28673:  # \x70\x01 stored little endian
            print("expected V Series Ping Setup ID, instead found %g" % leader_id)
            return -1
        v_ping_setup_data['Ensemble_Interval_ms'] = bstream[offset + 4] + (bstream[offset + 5] << 8) + (
                bstream[offset + 6] << 16) + (bstream[offset + 7] << 24)
        v_ping_setup_data['Number_of_Pings'] = struct.unpack('<H', bstream[offset + 10:offset + 12])[0]
        v_ping_setup_data['Time_Between_Pings_ms'] = bstream[offset + 10] + (bstream[offset + 11] << 8) + (
                bstream[offset + 12] << 16) + (bstream[offset + 13] << 24)
        v_ping_setup_data['Offset_Between_Ping_Groups_ms'] = bstream[offset + 14] + (bstream[offset + 15] << 8) + (
                bstream[offset + 16] << 16) + (bstream[offset + 17] << 24)
        v_ping_setup_data['Ping_Sequence_Number'] = struct.unpack('<h', bstream[offset + 22:offset + 24])[0]
        v_ping_setup_data['Ambiguity_Velocity'] = struct.unpack('<h', bstream[offset + 24:offset + 26])[0]
        v_ping_setup_data['RX_Gain'] = bstream[offset + 26]
        v_ping_setup_data['RX_Beam_Mask'] = bstream[offset + 27]
        v_ping_setup_data['TX_Beam_Mask'] = bstream[offset + 28]
        v_ping_setup_data['Ensemble_Offset'] = bstream[offset + 30] + (bstream[offset + 31] << 8) + (
                    bstream[offset + 32] << 16) + (
                                                       bstream[offset + 33] << 24)
        v_ping_setup_data['Ensemble_Count'] = bstream[offset + 34] + (bstream[offset + 35] << 8)
        v_ping_setup_data['Deployment_Start_Century'] = bstream[offset + 36]
        v_ping_setup_data['Deployment_Start_Year'] = bstream[offset + 37]
        v_ping_setup_data['Deployment_Start_Month'] = bstream[offset + 38]
        v_ping_setup_data['Deployment_Start_Day'] = bstream[offset + 39]
        v_ping_setup_data['Deployment_Start_Hour'] = bstream[offset + 40]
        v_ping_setup_data['Deployment_Start_Minute'] = bstream[offset + 41]
        v_ping_setup_data['Deployment_Start_Second'] = bstream[offset + 42]
        v_ping_setup_data['Deployment_Start_Hundredths'] = bstream[offset + 43]

        return v_ping_setup_data

    def parse_vertical_system_configuration(self, bstream, offset):
        """
        parse the TRDI V system configuration data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: a dict of readable system configuration settings
        """
        v_sys_config_data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 28672:  # \x70\x00 stored little endian
            print("expected V Series System Config ID, instead found %g" % leader_id)
            return -1
        v_sys_config_data['Firmware_Version'] = "%02d:%02d:%02d:%02d" % (bstream[offset + 2], bstream[offset + 3],
                                                                         bstream[offset + 4], bstream[offset + 5])
        v_sys_config_data['System_Frequency'] = bstream[offset + 6] + (bstream[offset + 7] << 8) + (
                bstream[offset + 8] << 16) + (bstream[offset + 9] << 24)
        v_sys_config_data['Pressure_Rating'] = struct.unpack('<H', bstream[offset + 10:offset + 12])[0]

        return v_sys_config_data

    def parse_vertical_beam_leader(self, bstream, offset):
        """
        parse the TRDI V beam leader data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: a dict of readable beam leader settings
        """
        v_beam_leader_data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 3841:  # \x0f\x01 stored little endian
            print("expected Vertical Beam Leader ID, instead found %g" % leader_id)
            return -1
        v_beam_leader_data['Vertical_Depth_Cells'] = struct.unpack('<H', bstream[offset + 2:offset + 4])[0]
        v_beam_leader_data['Vertical_Pings'] = struct.unpack('<H', bstream[offset + 4:offset + 6])[0]
        v_beam_leader_data['Vertical_Depth_Cell_Size_cm'] = struct.unpack('<H', bstream[offset + 6:offset + 8])[0]
        v_beam_leader_data['Vertical_First_Cell_Range_cm'] = struct.unpack('<H', bstream[offset + 8:offset + 10])[0]
        v_beam_leader_data['Vertical_Mode'] = struct.unpack('<H', bstream[offset + 10:offset + 12])[0]
        # 1 = low resolution slant beam cells = vertical beam cells
        # 2 = High resolution, dedicated surface tracking ping with 4:1 transmit/receive ratio or larger
        v_beam_leader_data['Vertical_Transmit_cm'] = struct.unpack('<H', bstream[offset + 12:offset + 14])[0]
        v_beam_leader_data['Vertical_Lag_Length_cm'] = struct.unpack('<H', bstream[offset + 14:offset + 16])[0]
        v_beam_leader_data['Transmit_Code_Elements'] = struct.unpack('<H', bstream[offset + 16:offset + 18])[0]
        v_beam_leader_data['Ping_Offset_Time'] = struct.unpack('<H', bstream[offset + 30:offset + 32])[0]

        return v_beam_leader_data

    def parse_vertical_velocity(self, bstream, offset, ncells):
        """
        parse the vertical beam velocity data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :return: vertical beam velocity data as a numpy array of ints
        """
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 2560:  # \x0a\x00 stored little endian
            print("expected Vertical Beam velocity ID, instead found %g" % leader_id)
            return -1

        # start with a numpy array of bad values
        data = np.ones(ncells, dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            data[icell] = struct.unpack('<h', bstream[offset + ibyte:offset + ibyte + 2])[0]
            ibyte += 2

        return data

    def parse_vertical_correlation(self, bstream, offset, ncells):
        """
        parse the vertical beam correlation data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :return: vertical beam correlation data as a numpy array of ints
        """
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 2816:  # \x0b\x00 stored little endian
            print("expected Vertical Beam correlation ID, instead found %g" % leader_id)
            return -1

        # start with a numpy array of bad values
        data = np.ones((ncells,), dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            data[icell] = bstream[offset + ibyte]
            ibyte += 1

        return data

    def parse_vertical_intensity(self, bstream, offset, ncells):
        """
        parse the vertical beam intensity data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :return: vertical beam intensity data as a numpy array of ints
        """
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 3072:  # \x0c\x00 stored little endian
            print("expected Vertical Beam intensity ID, instead found %g" % leader_id)
            return -1

        # start with a numpy array of bad values
        data = np.ones((ncells,), dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            data[icell] = bstream[offset + ibyte]
            ibyte += 1

        return data

    def parse_vertical_percent_good(self, bstream, offset, ncells):
        """
        parse the vertical beam percent good data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int ncells: number of cells in the profile
        :return: vertical beam percent good data as a numpy array of ints
        """
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 3328:  # \x0d\x00 stored little endian
            print("expected Vertical Beam percent good ID, instead found %g" % leader_id)
            return -1

        # start with a numpy array of bad values
        data = np.ones((ncells,), dtype=int) * -32768
        ibyte = 2
        for icell in range(ncells):
            data[icell] = bstream[offset + ibyte]
            ibyte += 1

        return data

    def parse_event_log(self, bstream, offset):
        """
        parse the event log data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: event log data as a dict
        """
        v_event_log_data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 28676:  # \x70\x04 stored little endian
            print("expected V Series Event Log ID, instead found %g" % leader_id)
            return -1

        v_event_log_data['Fault_Count'] = struct.unpack('<H', bstream[offset + 2:offset + 4])[0]
        # TODO read the fault codes and output to a text file

        return v_event_log_data

    def parse_wave_parameters(self, bstream, offset):
        """
        parse the wave parameters (wave statistics)
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: wave data as a dict
        """
        data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 11:  # \x00\x0b stored little endian
            print("expected Wave Parameters ID, instead found %g" % leader_id)
            return -1
        data['Hs'] = struct.unpack('<H', bstream[offset + 2:offset + 4])[0]
        data['Tp'] = struct.unpack('<H', bstream[offset + 4:offset + 6])[0]
        data['Dp'] = struct.unpack('<H', bstream[offset + 6:offset + 8])[0]
        data['Dm'] = struct.unpack('<H', bstream[offset + 16:offset + 18])[0]
        data['SHmax'] = struct.unpack('<H', bstream[offset + 30:offset + 32])[0]
        data['SH13'] = struct.unpack('<H', bstream[offset + 32:offset + 34])[0]
        data['SH10'] = struct.unpack('<H', bstream[offset + 34:offset + 36])[0]
        data['STmax'] = struct.unpack('<H', bstream[offset + 36:offset + 38])[0]
        data['ST13'] = struct.unpack('<H', bstream[offset + 38:offset + 40])[0]
        data['ST10'] = struct.unpack('<H', bstream[offset + 40:offset + 42])[0]
        data['T01'] = struct.unpack('<H', bstream[offset + 42:offset + 44])[0]
        data['Tz'] = struct.unpack('<H', bstream[offset + 44:offset + 46])[0]
        data['Tinv1'] = struct.unpack('<H', bstream[offset + 46:offset + 48])[0]
        data['S0'] = struct.unpack('<H', bstream[offset + 48:offset + 50])[0]
        data['Source'] = bstream[offset + 52]

        return data

    def parse_wave_sea_swell(self, bstream, offset):
        """
        parse the wave sea swell parameters (wave statistics)
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :return: wave sea swell data as a dict
        """
        data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 12:  # \x00\x0c stored little endian
            print("expected Wave Sea and Swell ID, instead found %g" % leader_id)
            return -1
        data['HsSea'] = struct.unpack('<H', bstream[offset + 2:offset + 4])[0]
        data['HsSwell'] = struct.unpack('<H', bstream[offset + 4:offset + 6])[0]
        data['TpSea'] = struct.unpack('<H', bstream[offset + 6:offset + 8])[0]
        data['TpSwell'] = struct.unpack('<H', bstream[offset + 8:offset + 10])[0]
        data['DpSea'] = struct.unpack('<H', bstream[offset + 10:offset + 12])[0]
        data['DpSwell'] = struct.unpack('<H', bstream[offset + 12:offset + 14])[0]
        data['SeaSwellPeriod'] = struct.unpack('<H', bstream[offset + 44:offset + 46])[0]

        return data

    def parse_bottom_track(self, bstream, offset, nbeams):
        """
        parse the bottom track data
        :param bytes bstream: an entire ensemble
        :param int offset: the location in the bytes object of the first byte of this data format
        :param int nbeams: number of acoustic beams
        :return: bottom track data as a dict
        """
        data = {}
        leader_id = struct.unpack('<H', bstream[offset:offset + 2])[0]
        if leader_id != 1536:  # \x00\x06 stored little endian
            print("expected Bottom Track ID, instead found %g" % leader_id)
            return -1
        data['Pings_per_ensemble'] = struct.unpack('<H', bstream[offset + 2:offset + 4])[0]
        data['delay_before_reacquire'] = struct.unpack('<H', bstream[offset + 4:offset + 6])[0]
        data['Corr_Mag_Min'] = bstream[offset + 6]
        data['Eval_Amp_Min'] = bstream[offset + 7]
        data['PGd_Minimum'] = bstream[offset + 8]
        data['Mode'] = bstream[offset + 9]
        data['Err_Vel_Max'] = struct.unpack('<H', bstream[offset + 10:offset + 12])[0]
        data['BT_Range_LSB'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 16
        for ibeam in range(nbeams):
            data['BT_Range_LSB'][ibeam] = struct.unpack('<h', bstream[offset + ibyte:offset + ibyte + 2])[0]
            ibyte = ibyte + 2
        # the meaning and direction depends on the coordinate system used
        data['BT_Vel'] = np.ones(nbeams, dtype=float) * 1e35
        ibyte = 24
        for ibeam in range(nbeams):
            data['BT_Vel'][ibeam] = struct.unpack('<h', bstream[offset + ibyte:offset + ibyte + 2])[0]
            ibyte = ibyte + 2
        data['BT_Corr'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 32
        for ibeam in range(nbeams):
            data['BT_Corr'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['BT_Amp'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 36
        for ibeam in range(nbeams):
            data['BT_Amp'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['BT_PGd'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 40
        for ibeam in range(nbeams):
            data['BT_PGd'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['Ref_Layer_Min'] = struct.unpack('<H', bstream[offset + 44:offset + 46])[0]
        data['Ref_Layer_Near'] = struct.unpack('<H', bstream[offset + 46:offset + 48])[0]
        data['Ref_Layer_Far'] = struct.unpack('<H', bstream[offset + 48:offset + 50])[0]
        data['Ref_Layer_Vel'] = np.ones(nbeams, dtype=float) * 1e35
        ibyte = 50
        for ibeam in range(nbeams):
            data['Ref_Layer_Vel'][ibeam] = struct.unpack('<h', bstream[offset + ibyte:offset + ibyte + 2])[0]
            ibyte = ibyte + 2
        data['Ref_Layer_Corr'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 58
        for ibeam in range(nbeams):
            data['Ref_Layer_Corr'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['Ref_Layer_Amp'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 62
        for ibeam in range(nbeams):
            data['Ref_Layer_Amp'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['Ref_Layer_PGd'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 66
        for ibeam in range(nbeams):
            data['Ref_Layer_PGd'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['BT_Max_Depth'] = struct.unpack('<H', bstream[offset + 70:offset + 72])[0]
        data['RSSI_Amp'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 72
        for ibeam in range(nbeams):
            data['RSSI_Amp'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['GAIN'] = bstream[offset + 76]
        data['BT_Range_MSB'] = np.ones(nbeams, dtype=int) * -32768
        ibyte = 77
        for ibeam in range(nbeams):
            data['BT_Range_MSB'][ibeam] = bstream[offset + ibyte]
            ibyte = ibyte + 1
        data['BT_Range'] = np.ones(nbeams, dtype=int) * -32768
        for ibeam in range(nbeams):
            data['BT_Range'][ibeam] = data['BT_Range_LSB'][ibeam] + (data['BT_Range_MSB'][ibeam] << 16)

        return data

    def compute_checksum(self, ensemble):
        """Compute a checksum from header, length, and ensemble"""
        cs = 0
        for byte in range(len(ensemble) - 2):
            cs += ensemble[byte]
        return cs & 0xffff

    def julian(self, year, month, day, hour, mn, sec, hund):
        """
        convert hours, minutes and seconds to decimal hours
        reference:
            http://stackoverflow.com/questions/31142181/calculating-julian-date-in-python/41769526#41769526
            and R. Signell's old matlab conversion code julian.m and hms2h.m
        :param int year: year
        :param int month: month
        :param int day: day
        :param int hour: hour
        :param int mn: minute
        :param int sec: second
        :param int hund: hundredth of second
        :return: julian day
        """
        #
        #
        decimalsec = sec + hund / 100
        decimalhrs = hour + mn / 60 + decimalsec / 3600
        mo = month + 9
        yr = year - 1

        if month > 2:
            mo -= 3
            yr = year

        c = math.floor(yr / 100)
        yr = yr - c * 100
        d = day
        j = math.floor((146097 * c) / 4) + math.floor((1461 * yr) / 4) + \
            math.floor((153 * mo + 2) / 5) + d + 1721119

        # If you want julian days to start and end at noon,
        # replace the following line with:
        # j=j+(decimalhrs-12)/24;
        j = j + decimalhrs / 24

        return j

    def analyze_pd0_file(self, pd0file, verbose=False):
        """
        determine the input file size, read some ensembles, make an estimate of the number of ensembles within, return the
            data from the first ensemble.
        :param str pd0file: path and file name to raw ADC data file in pd0 format
        :param bool verbose: output ensemble information
        :return: number of ensembles in file, number of bytes in each ensemble, data from the first ensemble,
            number of bytes to the start of the data
        """
        infile = open(pd0file, 'rb')

        while infile.tell() < 3000:
            b1 = infile.read(1)
            if b1 == b'\x7f':
                b2 = infile.read(1)
                if b2 == b'\x7f':
                    break
        else:
            print('Desired TRDI 7f7f ID not found within 3 kB from beginning of the file')
            infile.close()
            sys.exit(1)

        start_of_data = infile.tell() - 2
        if start_of_data != 0:
            print('data starts %d bytes into the file' % start_of_data)
        infile.seek(start_of_data)

        # need to read the header from the file to know the ensemble size
        header = self.read_header(infile)

        if header['sourceID'] != b'\x7f':
            print('error - this is not a currents file')
            infile.close()

        # number of bytes per ensemble in the header does not include the checksum
        ens_len = header['nbytesperens'] + 2
        print('ensemble length = %g' % ens_len)
        print(header)
        # it is faster to define the netCDF file with a known length
        # for this we need to estimate how many ensembles we will be reading
        # for some reason, sys.getsizeof(infile) does not report the true length
        # of the input file, so we will go to the end and see how far we have gone
        # there is a problem though.  While TRDI's documentation says the V Series
        # System Configuration data is always sent, this is not the case, so reading
        # only the first ensemble will not give the ensemble size typical over the
        # entire file
        # rewind and read this several ensembles because further in the ensemble
        # length can change on files output from Velocity
        infile.seek(start_of_data)

        nens2check = 5
        nbytesperens = [0 for i in range(nens2check)]
        ndatatypes = [0 for i in range(nens2check)]

        for i in range(nens2check):
            fileposn = infile.tell()
            header = self.read_header(infile)
            ens_len = header['nbytesperens'] + 2
            infile.seek(fileposn)
            ens_data, ens_error = self.parse_ensemble(infile.read(ens_len), verbose)
            if ens_error is not None:
                print('problem reading the first ensemble: ' + ens_error)
                # infile.close()
                # sys.exit(1)

            if i == 0:
                first_ens_data = ens_data
            print('ensemble %d has %d bytes and %d datatypes' % (ens_data['VLeader']['Ensemble_Number'],
                                                                 ens_data['Header']['nbytesperens'],
                                                                 ens_data['Header']['ndatatypes']))
            nbytesperens[i] = ens_data['Header']['nbytesperens'] + 2
            ndatatypes[i] = ens_data['Header']['ndatatypes']

        # the guess here is that if the first two ensembles are not the same,
        # it's the second ensemble that is representative of the data
        if nbytesperens[0] != nbytesperens[1]:
            ens_len = nbytesperens[1]
        else:
            ens_len = nbytesperens[0]

        infile.seek(0, 2)
        nbytesinfile = infile.tell()
        max_ens = (nbytesinfile / ens_len) - 1
        print('estimating %g ensembles in file using a %d ensemble size' % (max_ens, ens_len))

        infile.close()

        print(ens_data['Header'])
        print('ensemble length = %g' % ens_len)
        print('estimating %g ensembles in file' % max_ens)

        # return max_ens, ens_len, ens_data, start_of_data
        return max_ens, ens_len, first_ens_data, start_of_data

    def bitstrLE(self, byte):
        """
        make a bit string from little endian byte

        :param byte byte: a byte
        :return: a string of ones and zeros, the bits in the byte
        """
        # surely there's a better way to do this!!
        bits = ""
        for i in [7, 6, 5, 4, 3, 2, 1, 0]:  # Little Endian
            if (byte >> i) & 1:
                bits += "1"
            else:
                bits += "0"
        return bits

    def bitstrBE(self, byte):
        """
        make a bit string from big endian byte
        :param byte byte: a byte
        :return: a string of ones and zeros, the bbits in the byte
        """
        # surely there's a better way to do this!!
        bits = ""
        for i in range(8):  # Big Endian
            if (byte[0] >> i) & 1:
                bits += "1"
            else:
                bits += "0"
        return bits

    @staticmethod
    def jdn(dto):
        """
        convert datetime object to Julian Day Number
        :param object dto: datetime
        :return: int Julian Day Number
        """
        year = dto.year
        month = dto.month
        day = dto.day

        not_march = month < 3
        if not_march:
            year -= 1
            month += 12

        fr_y = math.floor(year / 100)
        reform = 2 - fr_y + math.floor(fr_y / 4)
        jjs = day + (
                math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + reform - 1524)

        return jjs

    @staticmethod
    def ajd(dto):
        """
        Given datetime object returns Astronomical Julian Day.
        Day is from midnight 00:00:00+00:00 with day fractional
        value added.
        :param object dto: datetime
        :return: int Astronomical Julian Day
        """
        jdd = Pd0Codec.jdn(dto)
        day_fraction = dto.hour / 24.0 + dto.minute / 1440.0 + dto.second / 86400.0
        return jdd + day_fraction - 0.5