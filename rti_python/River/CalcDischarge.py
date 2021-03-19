import math
import datetime
import numpy as np
from enum import Enum
from rti_python.Ensemble.Ensemble import Ensemble


class EnsembleFlowInfo:

    def __init__(self):
        self.top_flow = 0.0
        self.bottom_flow = 0.0
        self.measured_flow = 0.0
        self.valid = False
        self.measured_bin_info = []

class MeasuredBinInfo:

    def __init__(self):
        self.depth = 0.0
        self.flow = 0.0
        self.valid = False

class FlowMode(Enum):
    """
    TRDI restricts the constant
    method to use of the top depth cell only and the power-law
    estimate to using all of the available depth cells, but provides
    an additional 3-point slope method to fit situations where wind
    significantly affects the velocity at the water surface.
    """

    # This constant extrapolation method is often used where there
    # is an upstream wind or an irregular velocity profile through the
    # measured portion of the water column.
    Constants = 1

    # A method using
    # a one-sixth power law (Chen, 1989) eventually was chosen
    # because of its robust noise rejection capability during most
    # streamflow conditions.
    # The power-law estimation scheme is an approximation only
    # and emulates a Manning-like vertical distribution of horizontal
    # water velocities. Different power coefficients can be used to
    # adjust the shape of the curve fit to emulate profiles measured
    # in an estuarine environment or in areas that have bedforms that
    # produce nonstandard hydrologic conditions.
    PowerFunction = 2

    # 3-point slope method to fit situations where wind
    # significantly affects the velocity at the water surface
    Slope = 3


class Slope:

    def __init__(self):
        self.a = 0.0
        self.b = 0.0
        self.c = 0.0

    def setXYs(self, x_list: [], y_list: []):
        if len(x_list) != len(y_list) and len(x_list) > 0:
            return

        accum_x = 0.0
        accum_y = 0.0
        accum_xx = 0.0
        accum_xy = 0.0

        list_length = len(x_list)

        for index in range(x_list):
            accum_x += x_list[index]
            accum_y += y_list[index]
            accum_xx += (x_list[index] * x_list[index])
            accum_xy += (x_list[index] * y_list[index])

        avg_x = accum_x / list_length
        avg_y = accum_y / list_length
        cal_base = list_length * accum_xx - accum_x * accum_x

        if cal_base == 0.0:
            self.b = 0.0
            self.a = 1.0
            self.c = -avg_x
        else:
            slope = (list_length * accum_xy - accum_x * accum_y) / cal_base
            b_val = (accum_y * accum_xx - accum_x * accum_xy) / cal_base
            self.b = 1.0
            self.a = -slope
            self.c = -b_val

    def cal_x(self, y: float) -> float:
        if self.a == 0.0:
            return 0.0

        return 0.0 - (self.b * y + self.c) / self.a

    def cal_y(self, x: float) -> float:
        if self.b == 0.0:
            return 0.0

        return 0.0 - (self.a * x + self.c) / self.b


class CalcDischarge:

    # One-sixth power law common value
    ONE_SIXTH_POWER_LAW = 1/6
    MINIMUM_AMPLITUDE = 0.25
    MINIMUM_CORRELATION = 0.10

    def __init__(self):
        self.version = 1.1

    @staticmethod
    def cross_product(vel_east: float, vel_north: float, vel_bt_east: float, vel_bt_north: float):
        return (vel_north + vel_bt_north) * vel_bt_east - (vel_east + vel_bt_east) * vel_bt_north

    def calculate_ensemble_flow(self,
                                ens: Ensemble,
                                boat_draft: float,
                                beam_angle: float,
                                pulse_length: float,
                                pulse_lag: float,
                                bt_east: float,
                                bt_north: float,
                                bt_vert: float,
                                delta_time: float,
                                top_flow_mode: FlowMode = FlowMode.Constants,
                                top_pwr_func_exponent: float = ONE_SIXTH_POWER_LAW,
                                bottom_flow_mode: FlowMode = FlowMode.PowerFunction,
                                min_amp=MINIMUM_AMPLITUDE,
                                min_corr=MINIMUM_CORRELATION,
                                heading_offset=None) -> EnsembleFlowInfo:
        """
        Calculate the measured unit flow.
        :param ens:
        :param boat_draft:
        :param beam_angle:
        :param pulse_length:
        :param pulse_lag:
        :param bt_east:
        :param bt_north:
        :param bt_vert:
        :param delta_time: Time difference between ensembles.
        :param top_flow_mode:
        :param top_pwr_func_exponent:
        :param bottom_flow_mode:
        :param min_amp:
        :param min_corr:
        :param heading_offset: Heading angle correction.
        :return:
        """

        # Initialize the values
        ensemble_flow_info = EnsembleFlowInfo()
        ensemble_flow_info.valid = False

        # Check vessel velocity
        if abs(bt_east) > 80.0 or abs(bt_north) > 80.0:
            return ensemble_flow_info

        # Check for bad cell size
        if ens.IsAncillaryData and ens.AncillaryData.BinSize < 1E-06:
            return ensemble_flow_info

        # num1
        range_count = 0
        # Minimum depth of bottom track
        bt_min_depth = float('NaN')
        # Get the average bottom track range
        accum_range = 0.0
        if ens.IsBottomTrack:
            # num4
            for bt_range in ens.BottomTrack.Range:
                if bt_range >= 1E-06:

                    # Find minimum depth
                    if math.isnan(bt_min_depth):
                        bt_min_depth = bt_range
                    elif bt_range < bt_min_depth:
                        bt_min_depth = bt_range

                    # Accumulate for the average
                    range_count += 1
                    accum_range += bt_range

        # No good range values so bottom is not seen
        if range_count == 0.0:
            return ensemble_flow_info

        # Average Depth
        # num4
        avg_depth = accum_range / range_count

        # Possible maximum depth
        depth_angle = bt_min_depth * math.cos(beam_angle / 180.0 * math.pi) + boat_draft - max((pulse_length + pulse_lag) / 2.0, ens.AncillaryData.BinSize / 2.0)

        # Distance from water surface to the bottom
        overall_depth = avg_depth + boat_draft

        # First valid bin
        measured_bin_info_top = None
        measured_bin_info_bottom = None

        # First Bin Position
        first_bin_pos = ens.AncillaryData.FirstBinRange + boat_draft

        # List of bins
        measured_bin_info_list = []
        bin_list = []
        bin_index = 0
        # Accumulated Flow
        accum_flow = 0.0
        # Accumulated East Velocity
        accum_east_vel = 0.0
        # Accumulated North Velocity
        accum_north_vel = 0.0
        # Number of good bins
        accum_bins = 0

        bin_depth_index = first_bin_pos
        for bin_index in range(ens.EnsembleData.NumBins):
            if bin_depth_index < depth_angle and ens.EnsembleData.NumBeams >= 2:

                # num3
                earth_vel = [ens.EarthVelocity.Velocities[bin_index][0], ens.EarthVelocity.Velocities[bin_index][1]]
                cross_prod_bin = self.cross_product(ens.EarthVelocity.Velocities[bin_index][0],
                                                    ens.EarthVelocity.Velocities[bin_index][1],
                                                    bt_east,
                                                    bt_north)

                # Store the bin info
                # Equation A16
                # Calculate the total flow of a bin with the cross product of the accumulated velocities * dt * dz
                # Qbin = (Vw X Vb)*dt*dz
                # Cross product of water velocity and boat velocity
                # dt is delta time
                # dz is change in bin size
                measured_bin_info = MeasuredBinInfo()
                measured_bin_info.depth = bin_depth_index                                                 # Bin Depth
                measured_bin_info.flow = cross_prod_bin * delta_time * ens.AncillaryData.BinSize          # Flow for bin
                measured_bin_info.valid = ens.is_good_bin(bin_index, min_amp, min_corr)                   # Valid bin
                measured_bin_info_list.append(measured_bin_info)

                # Set the top most bin
                if measured_bin_info.valid and not measured_bin_info_top:
                    measured_bin_info_top = measured_bin_info

                # Set the bottom most bin
                if measured_bin_info.valid:
                    measured_bin_info_bottom = measured_bin_info

                # Accumulate flow
                accum_flow += measured_bin_info.flow

                # Accumulate East Velocity
                accum_east_vel += ens.EarthVelocity.Velocities[bin_index][0]

                # Accumulate North Velocity
                accum_north_vel += ens.EarthVelocity.Velocities[bin_index][1]

                # Accumulate good bins
                accum_bins += 1

                # Accumulate the list of bins
                bin_list.append(bin_index)

                # Increment the bin position
                bin_depth_index += ens.AncillaryData.BinSize

        # Store the bin info
        ensemble_flow_info.measured_bin_info = measured_bin_info_list

        # Verify the top bin is good
        if not measured_bin_info_top or not measured_bin_info_top.valid:
            return ensemble_flow_info

        # Get the depths
        depth1 = measured_bin_info_top.depth
        depth2 = measured_bin_info_bottom.depth
        x1 = overall_depth                                                  # Depth of the water
        x2 = overall_depth - depth1 + ens.AncillaryData.BinSize / 2.0       # Depth Not including the top
        x3 = overall_depth - depth2 - ens.AncillaryData.BinSize / 2.0       # Depth Not including the bottom

        # Accumulate the overall velocity and take the cross product
        # to get the overall discharge
        # Equation A16
        # Calculate the total flow of a bin with the cross product of the accumulated velocities * dt * dz
        # Qbin = (Vw X Vb)*dt*dz
        # Cross product of water velocity and boat velocity
        # dt is delta time
        # dz is change in bin (depth)
        vel_accum = [accum_east_vel / accum_bins, accum_north_vel / accum_bins]
        cross_prod_accum_vel = self.cross_product(vel_accum[0], vel_accum[1], bt_east, bt_north)
        ensemble_flow_info.measured_flow = cross_prod_accum_vel * delta_time * (x2 - x3)

        ################
        # CALCULATE TOP
        # Calculate the top flow based on the mode selected
        if top_flow_mode == FlowMode.Constants:
            # Use the flow from the top most bin only (TRDI)
            ensemble_flow_info.top_flow = measured_bin_info_top.flow / ens.AncillaryData.BinSize * (x1 - x2)
        elif top_flow_mode == FlowMode.PowerFunction:
            # Use the Power Law to calculate the top flow
            y1 = top_pwr_func_exponent + 1.0
            ensemble_flow_info.top_flow = accum_flow * ((x1 ** y1) - (x2 ** y1)) / ((x2 ** y1) - (x3 ** y1))
        elif top_flow_mode == FlowMode.Slope:
            if len(bin_list) < 6:
                ensemble_flow_info.top_flow = measured_bin_info_top.flow / ens.AncillaryData.BinSize * (x1 - x2)

            else:
                # Accumulate the velocities and bin depths
                # 3 Point Slope
                depth_list = []
                east_vel_list = []
                north_vel_list = []
                for bin_slope_index in range(3):
                    # Get the bin in the list of good bins
                    index_bin = bin_list[bin_slope_index]

                    # Calculate the depth of the bin
                    depth_bin = ens.AncillaryData.FirstBinRange + boat_draft + (index_bin * ens.AncillaryData.BinSize)

                    if not heading_offset:
                        # Get the east and north velocity
                        east_vel_bin = ens.EarthVelocity.Velocities[index_bin][0]
                        north_vel_bin = ens.EarthVelocity.Velocities[index_bin][1]
                    else:
                        east_vel_bin = ens.EarthVelocity.Velocities[index_bin][0] * math.cos(heading_offset) - ens.EarthVelocity.Velocities[index_bin][1] * math.sin(heading_offset)
                        north_vel_bin = ens.EarthVelocity.Velocities[index_bin][0] * math.sin(heading_offset) + ens.EarthVelocity.Velocities[index_bin][1] * math.cos(heading_offset)

                    # Add it to the list
                    depth_list.append(depth_bin)
                    east_vel_list.append(east_vel_bin)
                    north_vel_list.append(north_vel_bin)

                # Average depth
                x4 = (x1 - x2) / 2.0

                # Calculate the slope for East and North velocity
                slope_vel_east = Slope()
                slope_vel_north = Slope()
                slope_vel_east.setXYs(earth_vel, depth_list)
                slope_vel_north.setXYs(north_vel_list, depth_list)

                # Prevent divide by zero
                if (depth_list[1] - depth_list[0]) != 0:
                    slope_vel_east = slope_vel_east.cal_y(x4)
                    slope_vel_north = slope_vel_north.cal_y(x4)
                else:
                    ensemble_flow_info.top_flow = measured_bin_info.flow / ens.AncillaryData.BinSize * (x1 - x2)

                # Calculate the cross product of the slope of the top bins
                cross_prod_top_accum_vel = self.cross_product(slope_vel_east,
                                                              slope_vel_north,
                                                              bt_east,
                                                              bt_north)
                ensemble_flow_info.top_flow = delta_time * (x1-x2) * cross_prod_top_accum_vel

        ##################
        # CALCULATE BOTTOM
        # Set the Bottom Flow
        if bottom_flow_mode == FlowMode.PowerFunction:
            y2 = top_pwr_func_exponent + 1.0
            ensemble_flow_info.bottom_flow = accum_flow * (x3 ** y2) / ((x2 ** y2) - (x3 ** y2))
        elif bottom_flow_mode == FlowMode.Constants:
            ensemble_flow_info.bottom_flow = measured_bin_info_bottom.flow / ens.AncillaryData.BinSize * x3

        # Return the ensemble flow results
        ensemble_flow_info.valid = True
        return ensemble_flow_info

    def calculate_avg_vel(self,
                          ens: Ensemble,
                          boat_draft: float,
                          beam_angle: float,
                          pulse_length: float,
                          pulse_width: float,
                          top_pwr_func_exponent: float = ONE_SIXTH_POWER_LAW,
                          min_amp=MINIMUM_AMPLITUDE,
                          min_corr=MINIMUM_CORRELATION):
        """
        Calculate the surface and bottom average velocity.
        :param ens:
        :param boat_draft:
        :param beam_angle:
        :param pulse_length:
        :param pulse_width:
        :param top_pwr_func_exponent:
        :param min_amp:
        :param min_corr:
        :return:
        """

        da = ens.AncillaryData.BinSize

        if da < 1e-6:
            return

        bt_min_depth = float('NaN')
        depth_count = 0
        depth_accum = 0.0

        if ens.IsBottomTrack:
            # num4
            for bt_range in ens.BottomTrack.Range:
                # Verify a good range value
                if bt_range >= 1E-06:

                    # Find minimum depth
                    if math.isnan(bt_min_depth):
                        bt_min_depth = bt_range
                    else:
                        if bt_range < bt_min_depth:
                            bt_min_depth = bt_range

                    # Accumulate depths
                    depth_count += 1
                    depth_accum += bt_range

        # Calculate average depth
        if depth_count == 0:
            return
        bt_avg_depth = depth_accum / depth_count

        # Possible maximum depth
        dlg_max = bt_min_depth * math.cos(beam_angle / 180.0 * math.pi) + boat_draft - max((pulse_length + pulse_width) / 2, da / 2.0)

        # Distance from water surface to bottom
        depth_total = bt_avg_depth + boat_draft

        # First valid bin
        first_valid_bin = MeasuredBinInfo()
        first_valid_bin.valid = False

        # Last Valid bin
        last_valid_bin = MeasuredBinInfo()

        # First Bin Depth
        bin_depth = ens.AncillaryData.FirstBinRange + boat_draft

        # Accumulate East and North Velocity
        sum_east_vel = 0
        sum_north_vel = 0

        bin_depth_index = bin_depth

        for bin_index in range(ens.EnsembleData.NumBins):
            if bin_depth_index < dlg_max:

                # Get the bin info
                bin_info = MeasuredBinInfo()
                bin_info.Depth = bin_depth
                bin_info.valid = ens.is_good_bin(bin_index, min_amp, min_corr)                   # Valid bin

                # Set the first good and last bin info
                if bin_info.valid:
                    if not first_valid_bin.valid:
                        first_valid_bin = bin_info
                    last_valid_bin = bin_info

                sum_east_vel += ens.EarthVelocity.Velocities[bin_index][0]
                sum_north_vel += ens.EarthVelocity.Velocities[bin_index][1]

            # Increment the bin position
            bin_depth_index += ens.AncillaryData.BinSize

        # Check if any bins are good
        if not first_valid_bin.valid:
            return

        # Set the top and bottom depth
        depth_top = first_valid_bin.depth
        depth_bottom = last_valid_bin.depth

        z3 = depth_total
        z2 = depth_total - depth_top + da / 2.0
        z1 = depth_total - depth_bottom - da / 2.0

        # Surface velocity
        a = top_pwr_func_exponent + 1
        top_vx = sum_east_vel * da / (depth_top - da / 2.0) * ((z3 ** a) - (z2 ** a)) / ((z2 ** a) - (z1 ** a))
        top_vy = sum_north_vel * da / (depth_top - da / 2.0) * ((z3 ** a) - (z2 ** a)) / ((z2 ** a) - (z1 ** a))

        bottom_vx = sum_east_vel * da / z1 * (z1 ** a) / ((z2 ** a) - (z1 ** a))
        bottom_vy = sum_north_vel * da / z1 * (z1 ** a) / ((z2 ** a) - (z1 ** a))

        return top_vx, top_vy, bottom_vx, bottom_vy