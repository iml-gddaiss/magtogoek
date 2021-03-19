import json
import os
import math
import pytest


def calculate_max_velocity(**kwargs):
    """
    Calculate the maximum velocity the ADCP can measure including the boat speed in m/s.  This speed is the
    speed the ADCP is capable of measuring, if the speed exceeds this value, then the data will be incorrect
    due to rollovers.

    :param _CWPBB_ Broadband or Narrowband.
    :param CWPBB_LagLength=: WP lag length in meters.
    :param CWPBS=: Bin Size.
    :param BeamAngle=: Beam angle in degrees.
    :param SystemFrequency=: System frequency in hz.
    :param SpeedOfSound=: Speed of Sound in m/s.
    :param CyclesPerElement=: Cycles per element.
    :return: Maximum velocity the ADCP can read in m/s.
    """

    # Get the configuration from the json file
    script_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(script_dir, 'predictor.json')

    try:
        config = json.loads(open(json_file_path).read())
    except Exception as e:
        print("Error getting the configuration file.  MaxVelocity", e)
        return 0.0

    # _CWPBB_LagLength_, _BeamAngle_, _SystemFrequency_, _SpeedOfSound_, _CyclesPerElement_
    return _calculate_max_velocity(kwargs.pop('CWPBB', config['DEFAULT']['CWPBB']),
                                   kwargs.pop('CWPBB_LagLength', config['DEFAULT']['CWPBB_LagLength']),
                                   kwargs.pop('CWPBS', config['DEFAULT']['CWPBS']),
                                   kwargs.pop('BeamAngle', config['BeamAngle']),
                                   kwargs.pop('SystemFrequency', config['DEFAULT']['SystemFrequency']),
                                   kwargs.pop('SpeedOfSound', config['SpeedOfSound']),
                                   kwargs.pop('CyclesPerElement', config['CyclesPerElement']))


def _calculate_max_velocity(_CWPBB_, _CWPBB_LagLength_, _CWPBS_, _BeamAngle_, _SystemFrequency_, _SpeedOfSound_, _CyclesPerElement_):
    """
    Calculate the maximum velocity the ADCP can measure including the boat speed in m/s.  This speed is the
    speed the ADCP is capable of measuring, if the speed exceeds this value, then the data will be incorrect
    due to rollovers.

    :param _CWPBB_ Broadband or Narrowband.
    :param _CWPBB_LagLength_: WP lag length in meters.
    :param _BeamAngle_: Beam angle in degrees.
    :param _SystemFrequency_: System frequency in hz.
    :param _SpeedOfSound_: Speed of Sound in m/s.
    :param _CyclesPerElement_: Cycles per element.
    :return: Maximum velocity the ADCP can read in m/s.
    """

    # Get the configuration from the json file
    script_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(script_dir, 'predictor.json')

    try:
        config = json.loads(open(json_file_path).read())
    except Exception as e:
        print("Error getting the configuration file.  MaxVelocity", e)
        return 0.0

    # Prevent divide by 0
    if _CyclesPerElement_ == 0:
        _CyclesPerElement_ = 1

    if _SpeedOfSound_ == 0:
        _SpeedOfSound_ = 1490

    if _SystemFrequency_ == 0:
        _SystemFrequency_ = config["DEFAULT"]["1200000"]["FREQ"]

    #  Sample Rate
    sumSampling = 0.0;
    if _SystemFrequency_ > config["DEFAULT"]["1200000"]["FREQ"]:                                                                        # 1200 khz
        sumSampling += config["DEFAULT"]["1200000"]["SAMPLING"] * config["DEFAULT"]["1200000"]["CPE"] / _CyclesPerElement_
    elif (_SystemFrequency_ > config["DEFAULT"]["600000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["1200000"]["FREQ"]):      # 600 khz
        sumSampling += config["DEFAULT"]["600000"]["SAMPLING"] * config["DEFAULT"]["600000"]["CPE"] / _CyclesPerElement_
    elif (_SystemFrequency_ > config["DEFAULT"]["300000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["600000"]["FREQ"]):       # 300 khz
        sumSampling += config["DEFAULT"]["300000"]["SAMPLING"] * config["DEFAULT"]["300000"]["CPE"] / _CyclesPerElement_
    elif (_SystemFrequency_ > config["DEFAULT"]["150000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["300000"]["FREQ"]):       # 150 khz
        sumSampling += config["DEFAULT"]["150000"]["SAMPLING"] * config["DEFAULT"]["150000"]["CPE"] / _CyclesPerElement_
    elif (_SystemFrequency_ > config["DEFAULT"]["75000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["150000"]["FREQ"]):        # 75 khz
        sumSampling += config["DEFAULT"]["75000"]["SAMPLING"] * config["DEFAULT"]["75000"]["CPE"] / _CyclesPerElement_
    elif (_SystemFrequency_ > config["DEFAULT"]["38000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["75000"]["FREQ"]):         # 38 khz
        sumSampling += config["DEFAULT"]["38000"]["SAMPLING"] * config["DEFAULT"]["38000"]["CPE"] / _CyclesPerElement_

    sampleRate = _SystemFrequency_ * (sumSampling)

    # Meters Per Sample
    metersPerSample = 0
    if sampleRate == 0:
        metersPerSample = 0.0
    else:
        metersPerSample = math.cos(_BeamAngle_ / 180.0 * math.pi) * _SpeedOfSound_ / 2.0 / sampleRate

    # Lag Samples
    lagSamples = 0
    if metersPerSample == 0:
        lagSamples = 0
    else:
        lagSamples = 2 * math.trunc((math.trunc(_CWPBB_LagLength_ / metersPerSample) + 1.0) / 2.0)

    # Ua Hz
    uaHz = 0.0
    if lagSamples == 0:
        uaHz = 0.0
    else:
        uaHz = sampleRate / (2.0 * lagSamples)

    # Ua Radial
    uaRadial = 0.0
    if _SystemFrequency_ == 0:
        uaRadial = 0.0
    else:
        uaRadial = uaHz * _SpeedOfSound_ / (2.0 * _SystemFrequency_)

    #### NARROWBAND ####

    # Beam Angle Radian
    beamAngleRad = _BeamAngle_ / 180.0 * math.pi

    # Ta
    Ta = 2.0 * _CWPBS_ / _SpeedOfSound_ / math.cos(beamAngleRad)

    # L
    L = 0.5 * _SpeedOfSound_ * Ta

    # Check for vertical beam.No Beam angle
    if _BeamAngle_ == 0:
        return uaRadial

    # Narrowband lag length
    if _CWPBB_ == 0:
        return L / math.sin(_BeamAngle_ / 180.0 * math.pi)

    return uaRadial / math.sin(_BeamAngle_ / 180.0 * math.pi)


# UNIT TEST
# Run with pytext MaxVelocity.py
def test_narrowband():
    assert pytest.approx(calculate_max_velocity(CWPBB=0, CWPBB_LagLength=1.0, CWPBS=0.60, BeamAngle=20, SystemFrequency=1152000, SpeedOfSound=1467), 0.001) == 1.867


def test_broadband():
    assert pytest.approx(calculate_max_velocity(CWPBB=1, CWPBB_LagLength=1.0, CWPBS=0.60, BeamAngle=20, SystemFrequency=1152000, SpeedOfSound=1490), 0.001) == 0.658


def test_broadband300():
    assert pytest.approx(calculate_max_velocity(CWPBB=1, CWPBB_LagLength=1.0, CWPBS=4.0, BeamAngle=20, SystemFrequency=288000.0, SpeedOfSound=1490), 0.001) == 2.669
