from rti_python.Ensemble.Ensemble import Ensemble


class EnsembleQC:

    @staticmethod
    def scan_ensemble(ens):
        """
        Fix the velocity data in the ensemble.

        This will scan for bad velocity and try to replace it with a good value.
        :param ens: Ensemble to scan
        :return:
        """
        if ens.IsBeamVelocity:
            EnsembleQC.scan_bad_velocity(ens.Wt.Velocities)
        if ens.IsInstrumentVelocity:
            EnsembleQC.scan_bad_velocity(ens.InstrumentVelocity.Velocities)
        if ens.IsEarthVelocity:
            EnsembleQC.scan_bad_velocity(ens.EarthVelocity.Velocities)
            EnsembleQC.scan_mag_dir(ens.EarthVelocity.Magnitude)
            EnsembleQC.scan_mag_dir(ens.EarthVelocity.Direction)

    @staticmethod
    def scan_bad_velocity(vel_list):
        """
        Try to clean up the data.  This will try to replace the BAD_VELOCITY
        with a good value.
        
        This will replace the bad value with the average of the top and bottom bin
        surrounding the bad bin.
        
        If it is the first bin, use the second bin as the replacement.
        
        If it is the last bin, use the second to last 2 bin's average.
        
        Every other bin, average the top and bottom bin.
        :param vel_list: Velocity list to remove the bad velocity values.
        :return: 
        """""
        # Verify we have data
        if vel_list and len(vel_list) > 0:

            num_bins = len(vel_list)
            num_beams = len(vel_list[0])
            last_bin_num = num_bins - 1

            # Go through each bin looking for a bad vel
            for bin_num in range(num_bins):
                for beam_num in range(num_beams):

                    # Check for bad velocity
                    if Ensemble.is_bad_velocity(vel_list[bin_num][beam_num]):

                        # Check for first bin
                        if bin_num == 0:
                            # First bin
                            # Use the second bin if it is good
                            if len(vel_list) > 1:
                                if not Ensemble.is_bad_velocity(vel_list[bin_num+1][beam_num]):
                                    # Set the second bin value as the first also
                                    vel_list[bin_num][beam_num] = vel_list[bin_num+1][beam_num]

                        # Check for last bin
                        elif bin_num == last_bin_num:

                            # Use the average of the second to last 2 bins if it is good
                            if len(vel_list) > 3:
                                # Second 2 last bins
                                second_last_bin_num = len(vel_list)-2
                                third_last_bin_num = len(vel_list)-3
                                second_last_bin = vel_list[second_last_bin_num][beam_num]
                                third_last_bin = vel_list[third_last_bin_num][beam_num]

                                if not Ensemble.is_bad_velocity(second_last_bin) and not Ensemble.is_bad_velocity(third_last_bin):
                                    # Set the last bin as the average of the second to last 2 bins
                                    vel_list[bin_num][beam_num] = (second_last_bin + third_last_bin) / 2

                        # Average the top and bottom bin
                        else:
                            # Top Bin and Bottom Bin to use to get the average
                            top_bin_num = bin_num - 1
                            bottom_bin_num = bin_num + 1
                            top_bin = vel_list[top_bin_num][beam_num]
                            bottom_bin = vel_list[bottom_bin_num][beam_num]

                            if not Ensemble.is_bad_velocity(top_bin) and not Ensemble.is_bad_velocity(bottom_bin):
                                # Set the bin to the average of the top and bottom bin
                                vel_list[bin_num][beam_num] = (top_bin + bottom_bin) / 2

    @staticmethod
    def scan_mag_dir(vel_list):
        """
        Try to clean up the data.  This will try to replace the BAD_VELOCITY
        with a good value.

        This will replace the bad value with the average of the top and bottom bin
        surrounding the bad bin.

        If it is the first bin, use the second bin as the replacement.

        If it is the last bin, use the second to last 2 bin's average.

        Every other bin, average the top and bottom bin.
        :param vel_list: Velocity list to remove the bad velocity values.
        :return: 
        """""
        # Verify we have data
        if vel_list and len(vel_list) > 0:

            num_bins = len(vel_list)
            last_bin_num = num_bins - 1

            # Go through each bin looking for a bad vel
            for bin_num in range(num_bins):

                # Check for bad velocity
                if Ensemble.is_bad_velocity(vel_list[bin_num]):

                    # Check for first bin
                    if bin_num == 0:
                        # First bin
                        # Use the second bin if it is good
                        if len(vel_list) > 1:
                            if not Ensemble.is_bad_velocity(vel_list[bin_num + 1]):
                                # Set the second bin value as the first also
                                vel_list[bin_num] = vel_list[bin_num + 1]

                    # Check for last bin
                    elif bin_num == last_bin_num:

                        # Use the average of the second to last 2 bins if it is good
                        if len(vel_list) > 3:
                            # Second 2 last bins
                            second_last_bin_num = len(vel_list) - 2
                            third_last_bin_num = len(vel_list) - 3
                            second_last_bin = vel_list[second_last_bin_num]
                            third_last_bin = vel_list[third_last_bin_num]

                            if not Ensemble.is_bad_velocity(second_last_bin) and not Ensemble.is_bad_velocity(
                                    third_last_bin):
                                # Set the last bin as the average of the second to last 2 bins
                                vel_list[bin_num] = (second_last_bin + third_last_bin) / 2

                    # Average the top and bottom bin
                    else:
                        # Top Bin and Bottom Bin to use to get the average
                        top_bin_num = bin_num - 1
                        bottom_bin_num = bin_num + 1
                        top_bin = vel_list[top_bin_num]
                        bottom_bin = vel_list[bottom_bin_num]

                        if not Ensemble.is_bad_velocity(top_bin) and not Ensemble.is_bad_velocity(bottom_bin):
                            # Set the bin to the average of the top and bottom bin
                            vel_list[bin_num] = (top_bin + bottom_bin) / 2



