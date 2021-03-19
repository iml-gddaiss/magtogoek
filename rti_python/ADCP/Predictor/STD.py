import json
import os
import math
import pytest


def calculate_std(**kwargs):
    """
    Calculate the standard deviation based off the parameters given in m/s.  This will
    give you the variance or predicted error in the data.

    :param CWPP=: WP Number of pings.
    :param CWPBS=: WP Bin size in meters.
    :param CWPBB_LagLength=: WP Lag length in meters.
    :param BeamAngle=: Beam angle in degrees.
    :param CWPBB_TransmitPulseType=: WP Broadband or narrowband.
    :param SystemFrequency=: System frequency in hz.
    :param SpeedOfSound=: Speed of Sound in m/s.
    :param CyclesPerElement=: Cycles per elements.
    :param SNR=: SNR in db.
    :param Beta=: Environmental decorrelation.
    :param NbFudge=: Narrowband fudge number.
    :return: Standard deviation in m/s.
    """

    # Get the configuration from the json file
    script_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(script_dir, 'predictor.json')

    try:
        config = json.loads(open(json_file_path).read())
    except Exception as e:
        print("Error getting the configuration file.  STD", e)
        return 0.0

    return _calculate_std(kwargs.pop('CWPP', config['DEFAULT']['CWPP']),
                          kwargs.pop('CWPBS', config['DEFAULT']['CWPBS']),
                          kwargs.pop('CWPBB_LagLength', config['DEFAULT']['CWPBB_LagLength']),
                          kwargs.pop('BeamAngle', config['BeamAngle']),
                          kwargs.pop('CWPBB', config['DEFAULT']['CWPBB']),
                          kwargs.pop('SystemFrequency', config['DEFAULT']['SystemFrequency']),
                          kwargs.pop('SpeedOfSound', config['DEFAULT']['SpeedOfSound']),
                          kwargs.pop('CyclesPerElement', config['CyclesPerElement']),
                          kwargs.pop('SNR', config['SNR']),
                          kwargs.pop('Beta', config['Beta']),
                          kwargs.pop('NbFudge', config['NbFudge']))


def _calculate_std(_CWPP_, _CWPBS_, _CWPBB_LagLength_,
                  _BeamAngle_, _CWPBB_TransmitPulseType_,
                  _SystemFrequency_, _SpeedOfSound_, _CyclesPerElement_,
                  _SNR_, _Beta_, _NbFudge_):

    """
    Calculate the standard deviation based off the parameters given in m/s.  This will
    give you the variance or predicted error in the data.

    :param _CWPP_: WP Number of pings.
    :param _CWPBS_: WP Bin size in meters.
    :param _CWPBB_LagLength_: WP Lag length in meters.
    :param _BeamAngle_: Beam angle in degrees.
    :param _CWPBB_TransmitPulseType_: WP Broadband or narrowband.
    :param _SystemFrequency_: System frequency in hz.
    :param _SpeedOfSound_: Speed of Sound in m/s.
    :param _CyclesPerElement_: Cycles per elements.
    :param _SNR_: SNR in db.
    :param _Beta_: Environmental decorrelation.
    :param _NbFudge_: Narrowband fudge number.
    :return: Standard deviation in m/s.
    """

    # Get the configuration from the json file
    script_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(script_dir, 'predictor.json')

    try:
        config = json.loads(open(json_file_path).read())
    except Exception as e:
        print("Error getting the configuration file.  STD", e)
        return 0.0


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


    # Bin Samples
    binSamples = 0;
    if metersPerSample == 0:
        binSamples = 0
    else:
        binSamples = math.trunc(_CWPBS_ / metersPerSample)


    # Code Repeats
    codeRepeats = 0
    if lagSamples == 0:
        codeRepeats = 0
    else:
        # Make the result of Truncate an int
        if (math.trunc(binSamples / lagSamples)) + 1.0 < 2.0:
            codeRepeats = 2
        else:
            codeRepeats = (math.trunc(binSamples / lagSamples)) + 1


    # rho
    # Nominal Correlation
    rho = 0.0
    if _CWPBB_TransmitPulseType_ < 2:
        if (codeRepeats == 0) or (_SNR_ == 0):
            rho = 0
        else:
            snr = math.pow(10.0, _SNR_ / 10.0)
            rho = _Beta_ * ((codeRepeats - 1.0) / codeRepeats) / (1.0 + math.pow(1.0 / 10.0, _SNR_ / 10.0))
    else:
        rho = _Beta_


    # STD Radial
    stdDevRadial = 0.0
    if (lagSamples == 0) or (binSamples == 0):
        stdDevRadial = 0.0
    else:
        stdDevRadial = 0.034 * (118.0 / lagSamples) * math.sqrt(14.0 / binSamples) * math.pow((rho / 0.5), -2.0)


    # Broadband STD
    stdDevSystem = 0.0
    if _CWPP_ == 0:
        stdDevSystem = 0.0
    elif _BeamAngle_ == 0:
        # Use the radial for the standard deviation
        # This is for vertical beams
        stdDevSystem = stdDevRadial
    else:
        stdDevSystem = stdDevRadial / math.sqrt(_CWPP_) / math.sqrt(2.0) / math.sin(_BeamAngle_ / 180.0 * math.pi)


    # NbLamda
    nbLamda = 0.0
    if _SystemFrequency_ == 0:
        nbLamda = 0.0
    else:
        nbLamda = _SpeedOfSound_ / _SystemFrequency_


    # NbTa
    nbTa = 0.0
    if (_SpeedOfSound_ == 0) or ((_BeamAngle_ / 180.0 * math.pi) == 0):
        nbTa = 0.0
    else:
        nbTa = 2.0 * _CWPBS_ / _SpeedOfSound_ / math.cos(_BeamAngle_ / 180.0 * math.pi)


    # NbL
    nbL = 0.5 * _SpeedOfSound_ * nbTa


    # Narrowband STD Radial
    nbStdDevRadial = 0.0
    if (nbL == 0) or (_SNR_ == 0):
        nbStdDevRadial = 0
    else:
        nbStdDevRadial = _NbFudge_ * (_SpeedOfSound_ * nbLamda / (8 * math.pi * nbL)) * math.sqrt(1 + 36 / math.pow(10, (_SNR_ / 10)) + 30 / math.pow(math.pow(10, _SNR_ / 10), 2))


    #Narrowband STD
    nbStdDevHSystem = 0.0
    if (_CWPP_ == 0) or (_BeamAngle_ == 0):
        nbStdDevHSystem = 0.0
    else:
        nbStdDevHSystem = nbStdDevRadial / math.sin(_BeamAngle_ / 180 * math.pi) / math.sqrt(2) / math.sqrt(_CWPP_)


    # Check if using Broadband or Narrowband
    if _CWPBB_TransmitPulseType_ > 0:
        return stdDevSystem         # Broadband
    else:
        return nbStdDevHSystem      # Narrowband


def test_STD():
    assert pytest.approx(calculate_std(CWPP=9,
                         CWPBS=4,
                         CWPBB_LagLength=1.0,
                         BeamAngle=20,
                         CWPBB=1,
                         SystemFrequency=288000,
                         SpeedOfSound=1490,
                         CyclesPerElement=12,
                         SNR=30,
                         Beta=1.0,
                         NbFudge=1.4), 0.1) == 0.01


def test_STD_NB():
    assert pytest.approx(calculate_std(CWPP=9,
                         CWPBS=4,
                         CWPBB_LagLength=1.0,
                         BeamAngle=20,
                         CWPBB=0,
                         SystemFrequency=288000,
                         SpeedOfSound=1490,
                         CyclesPerElement=12,
                         SNR=30,
                         Beta=1.0,
                         NbFudge=1.4), 0.1) == 0.07
