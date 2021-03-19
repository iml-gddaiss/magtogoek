import pytest
import os
from rti_python.River.CalcDischarge import CalcDischarge
from rti_python.River.CalcDischarge import FlowMode
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.EnsembleData import EnsembleData
from rti_python.Ensemble.AncillaryData import AncillaryData
from rti_python.Ensemble.EarthVelocity import EarthVelocity
from rti_python.Ensemble.BottomTrack import BottomTrack
from rti_python.Utilities.read_binary_file import ReadBinaryFile




results = []


def test_calc_discharge():
    ens = Ensemble()

    ens_data = EnsembleData()
    ens_data.NumBeams = 4
    ens_data.NumBins = 4
    ens.AddEnsembleData(ens_data)

    anc = AncillaryData()
    anc.BinSize = 1
    anc.FirstBinRange = 0.5
    ens.AddAncillaryData(anc)

    vel = EarthVelocity(4, 4)
    vel.Velocities[0][0] = 1.0
    vel.Velocities[0][1] = 1.1
    vel.Velocities[0][2] = 0.2
    vel.Velocities[0][3] = 0.0
    vel.Velocities[1][0] = 1.1
    vel.Velocities[1][1] = 1.2
    vel.Velocities[1][2] = 0.3
    vel.Velocities[1][3] = 0.0
    vel.Velocities[2][0] = 1.2
    vel.Velocities[2][1] = 1.3
    vel.Velocities[2][2] = 0.4
    vel.Velocities[2][3] = 0.0
    vel.Velocities[3][0] = 1.4
    vel.Velocities[3][1] = 1.5
    vel.Velocities[3][2] = 0.6
    vel.Velocities[3][3] = 0.0
    ens.AddEarthVelocity(vel)

    bt = BottomTrack()
    bt.NumBeams = 4
    bt.Range = [23.5, 24.2, 22.4, 26.1]
    ens.AddBottomTrack(bt)

    discharge = CalcDischarge()
    boat_draft = 0.1
    beam_angle = 20
    pulse_length = 0.8
    pulse_lag = 0.1
    bt_east = 0.9
    bt_north = 0.9
    bt_vert = 0.1
    delta_time = 0.15
    top_flow_mode = FlowMode.Constants
    top_pwr_func_exponent = CalcDischarge.ONE_SIXTH_POWER_LAW
    bottom_flow_mode = FlowMode.PowerFunction

    result = discharge.calculate_ensemble_flow(ens,
                                               boat_draft,
                                               beam_angle,
                                               pulse_length,
                                               pulse_lag,
                                               bt_east,
                                               bt_north,
                                               bt_vert,
                                               delta_time,
                                               top_flow_mode,
                                               top_pwr_func_exponent,
                                               bottom_flow_mode)

    assert result.valid == True
    assert -0.2284 == pytest.approx(result.bottom_flow, 0.001)
    assert -0.00135 == pytest.approx(result.top_flow, 0.001)
    assert -0.054 == pytest.approx(result.measured_flow, 0.001)


def process_ens_func(sender, ens):
    """
    Receive the data from the file.  It will process the file.
    When an ensemble is found, it will call this function with the
    complete ensemble.
    :param sender: NOT USED
    :param ens: Ensemble to process.
    :return:
    """

    discharge = CalcDischarge()
    boat_draft = 0.1
    beam_angle = 20
    pulse_length = 0.8
    pulse_lag = 0.1
    bt_east = ens.BottomTrack.EarthVelocity[0]
    bt_north = ens.BottomTrack.EarthVelocity[1]
    bt_vert = ens.BottomTrack.EarthVelocity[2]
    delta_time = 1.00
    top_flow_mode = FlowMode.PowerFunction
    top_pwr_func_exponent = CalcDischarge.ONE_SIXTH_POWER_LAW
    bottom_flow_mode = FlowMode.PowerFunction

    result = discharge.calculate_ensemble_flow(ens,
                                               boat_draft,
                                               beam_angle,
                                               pulse_length,
                                               pulse_lag,
                                               bt_east,
                                               bt_north,
                                               bt_vert,
                                               delta_time,
                                               top_flow_mode,
                                               top_pwr_func_exponent,
                                               bottom_flow_mode)

    results.append(result)
    #good_ens += 1
    #top_q += result.top_flow
    #bottom_Q += result.bottom_flow


def test_discharge_file():
    file_path = "/Users/rico/Documents/rti/data/River/Jack/20130701102612_rti.bin"
    #file_path = "G:\\rti\\data\\River\\Jack\\20130701102612_rti.bin"

    results.clear()

    if os.path.exists(file_path):

        # Create the file reader to read the binary file
        read_binary = ReadBinaryFile()
        read_binary.ensemble_event += process_ens_func

        # Pass the file path to the reader
        read_binary.playback(file_path)

        assert 1204 == len(results)

        total_q = 0.0
        top_q = 0.0
        bottom_q = 0.0
        good_ens = 0
        bad_ens = 0
        for result in results:
            if result.valid:
                good_ens += 1
                top_q += result.top_flow
                bottom_q += result.bottom_flow
                total_q += result.measured_flow
            else:
                bad_ens += 1

        #assert -146.742 == pytest.approx(top_q, 0.001)
        assert 12 == bad_ens
        #assert 14.238 == pytest.approx(total_q, 0.001)
        #assert 4.405 == pytest.approx(bottom_q, 0.001)