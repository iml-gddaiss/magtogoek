from rti_python.Ensemble.Ensemble import Ensemble
import logging
import math
import numpy as np
from pandas import DataFrame


class EarthVelocity:
    """
    Earth Velocity DataSet.
    [Bin x Beam] data.
    """

    def __init__(self, num_elements, element_multiplier):
        self.ds_type = 10
        self.num_elements = num_elements
        self.element_multiplier = element_multiplier
        self.image = 0
        self.name_len = 8
        self.Name = "E000003\0"
        self.Velocities = []
        self.Magnitude = []
        self.Direction = []

        # Create enough entries for all the (bins x beams)
        # Initialize with bad values
        for bins in range(num_elements):
            bins = []
            for beams in range(element_multiplier):
                bins.append(Ensemble.BadVelocity)

            self.Velocities.append(bins)                    # Mark Vel Bad
            self.Magnitude.append(Ensemble.BadVelocity)     # Mark Mag Bad
            self.Direction.append(Ensemble.BadVelocity)     # Mark Dir Bad

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

        # Generate Water Current Magnitude and Direction
        self.generate_velocity_vectors()

        logging.debug(self.Velocities)

    def remove_vessel_speed(self, bt_east=0.0, bt_north=0.0, bt_vert=0.0):
        """
        Remove the vessel speed.  If the bottom track data is good and
        the velocity is good, then remove the vessel speed from the earth speed.

        The bottom track velocity is the vessel velocity.  You can also use GPS data as a backup.

        Calculate the East and North component from the GPS speed
        bt_east = Convert.ToSingle(speed * Math.Sin(MathHelper.DegreeToRadian(heading)));
        bt_north = Convert.ToSingle(speed * Math.Cos(MathHelper.DegreeToRadian(heading)));

        :param bt_east: Bottom Track East velocity
        :param bt_north: Bottom Track North velocity
        :param bt_vert: Bottom Track Vertical velocity
        :return:
        """
        # Remove the vessel speed
        for bin_num in range(len(self.Velocities)):
            if not Ensemble.is_bad_velocity(self.Velocities[bin_num][0]) and not Ensemble.is_bad_velocity(bt_east):
                self.Velocities[bin_num][0] = self.Velocities[bin_num][0] + bt_east            # Remove vessel speed
            if not Ensemble.is_bad_velocity(self.Velocities[bin_num][1]) and not Ensemble.is_bad_velocity(bt_north):
                self.Velocities[bin_num][1] = self.Velocities[bin_num][1] + bt_north           # Remove vessel speed
            if not Ensemble.is_bad_velocity(self.Velocities[bin_num][2]) and not Ensemble.is_bad_velocity(bt_vert):
                self.Velocities[bin_num][2] = self.Velocities[bin_num][2] + bt_vert            # Remove vessel speed

        # Generate the new vectors after removing the vessel speed
        self.generate_velocity_vectors()

    def generate_velocity_vectors(self):
        """
        Generate the velocity vectors for this object.
        This will set both Magnitude and direction.
        :return:
        """
        self.Magnitude, self.Direction = EarthVelocity.generate_vectors(self.Velocities)

    def average_mag_dir(self):
        """
        Generate the average Magnitude and direction for the entire ensemble.
        Assume the ship speed has already been removed.
        This will also filter for all bad velocities when taking the average.
        :return: [Avg_MAG, Avg_DIR] Average Magnitude and Direction.  None if no value can be calculated
        """
        # Get the average magnitude for all the bins
        # Ignore bad velocity
        mag_no_bad_vel = np.array(self.Magnitude)                               # Convert to NP Array
        mag_no_bad_vel[mag_no_bad_vel >= Ensemble.BadVelocity] = np.nan         # Replace bad velocity with Nan
        avg_mag = np.nanmean(mag_no_bad_vel)                                    # Take average

        # Get the average direction
        dir_no_bad_vel = np.array(self.Direction)                               # Convert to NP Array
        dir_no_bad_vel[dir_no_bad_vel == Ensemble.BadVelocity] = np.nan         # Replace bad velocity with Nan
        avg_dir = np.nanmean(dir_no_bad_vel)                                    # Take average

        # Return None if the result is NaN
        if np.isnan(avg_mag):
            avg_mag = None
        if np.isnan(avg_dir):
            avg_dir = None

        # Return Average Magnitude, Direction
        return avg_mag, avg_dir

    @staticmethod
    def generate_vectors(earth_vel):
        """
        Generate the velocity vectors.  This will calculate the magnitude and direction
        of the water.  If any of the data is marked bad in a bin, then the magnitude and
        direction will also be marked bad.

        Call this again and set the self.Magnitude and self.Direction when Bottom Track Velocity is
        available.

        :param earth_vel: Earth Velocities[bin][beam]
        :return: [magnitude], [direction]  List with a value for each bin
        """
        mag = []
        dir = []

        for bin_num in range(len(earth_vel)):
            # Calculate the magnitude and direction
            mag.append(Ensemble.calculate_magnitude(earth_vel[bin_num][0], earth_vel[bin_num][1], earth_vel[bin_num][2]))
            dir.append(Ensemble.calculate_direction(earth_vel[bin_num][0], earth_vel[bin_num][1]))

        return mag, dir

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
                str_result.append([Ensemble.gen_csv_line(dt, Ensemble.CSV_EARTH_VEL, ss_code, ss_config, bin_num, beam, blank, bin_size, val)])

        # Generate Magnitude and Direction CSV
        for bin_num in range(self.num_elements):
            mag = self.Magnitude[bin_num]
            dir = self.Direction[bin_num]
            str_result.append([Ensemble.gen_csv_line(dt, Ensemble.CSV_MAG, ss_code, ss_config, bin_num, 0, blank, bin_size, mag)])
            str_result.append([Ensemble.gen_csv_line(dt, Ensemble.CSV_DIR, ss_code, ss_config, bin_num, 0, blank, bin_size, dir)])

        return str_result

    def encode_df(self, dt, ss_code, ss_config, vel_bad_val=Ensemble.BadVelocity, mag_bad_val=Ensemble.BadVelocity, include_bad_vel=True, include_bad_mag=True):
        """
        Encode into Dataframe array format.
        :param dt: Datetime object.
        :param ss_code: Subsystem code.
        :param ss_config: Subsystem Configuration
        :param vel_bad_val: Change bad velocity value for Earth Velocity
        :param mag_bad_val: Change bad velocity value for Magnitude value
        :param include_bad_vel: Include the velocity if it is bad, or remove it
        :param include_bad_mag: Include the magnitude if it is bad, or remove it
        :return: List of CSV lines.
        """
        df_result = []

        for beam in range(self.element_multiplier):
            for bin_num in range(self.num_elements):
                # Get the value
                val = self.Velocities[bin_num][beam]

                # Check if we are including bad velocities
                if Ensemble.is_bad_velocity(val):
                    if include_bad_vel:
                        # Replace the bad velocity value
                        val = vel_bad_val

                        # Create the Dataframe array
                        df_result.append([dt, Ensemble.CSV_EARTH_VEL, ss_code, ss_config, bin_num, beam, val])
                else:
                    # Create the Dataframe array
                    df_result.append([dt, Ensemble.CSV_EARTH_VEL, ss_code, ss_config, bin_num, beam, val])

        # Generate Magnitude and Direction CSV
        for bin_num in range(self.num_elements):
            mag = self.Magnitude[bin_num]
            dir = self.Direction[bin_num]

            # Check if we are including bad magnitude
            if Ensemble.is_bad_velocity(mag):
                if include_bad_mag:
                    # Replace the bad magnitude value
                    mag = mag_bad_val

                    # Set the df values
                    df_result.append([dt, Ensemble.CSV_MAG, ss_code, ss_config, bin_num, beam, mag])
                    df_result.append([dt, Ensemble.CSV_DIR, ss_code, ss_config, bin_num, beam, dir])
            else:
                # Set the df values
                df_result.append([dt, Ensemble.CSV_MAG, ss_code, ss_config, bin_num, beam, mag])
                df_result.append([dt, Ensemble.CSV_DIR, ss_code, ss_config, bin_num, beam, dir])

            # Create the column names
            df_earth_columns = ["dt", "type", "ss_code", "ss_config", "bin_num", "beam", "val"]

        return DataFrame(df_result, columns=df_earth_columns)

    def is_good_bin(self, bin_num: int) -> bool:
        """
        Verify if the given bin has good data based on BAD_VELOCITY.
        :param bin_num: Bin Number
        :return: TRUE = All beams do not have BAD_VELOCITY.
        """
        # Verify a good bin number is given
        if bin_num >= self.num_elements:
            return False

        # Verify the amplitude value is greater then the given min value
        bad_count = 0
        for beam in range(self.element_multiplier):
            if Ensemble.is_bad_velocity(self.Velocities[bin_num][beam]):
                bad_count += 1

        # If any bad values are found in the bin, return false
        if bad_count > 1:
            return False

        return True
