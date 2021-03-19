import math
import json
import os
import pytest
import rti_python.ADCP.AdcpCommands


def calculate_predicted_range(**kwargs):
    """
    :param SystemFrequency=: System frequency for this configuration.
    :param CWPON=: Flag if Water Profile is turned on.
    :param CWPBL=: WP Blank in meters.
    :param CWPBS=: WP bin size in meters.
    :param CWPBN=: Number of bins.
    :param CWPBB_LagLength=: WP lag length in meters.
    :param CWPBB=: WP broadband or narrowband.
    :param CWPP=: Number of pings to average.
    :param CWPTBP=: Time between each ping in the average.
    :param CBTON=: Is Bottom Track turned on.
    :param CBTBB=: BT broadband or narrowband.
    :param BeamAngle=: Beam angle in degrees. Default 20 degrees.
    :param BeamDiameter=: The beam diameter in meters.
    :param CyclesPerElement=: Cycles per element.
    :param Salinity=: Salinity in ppt.
    :param Temperature=: Temperature in C.
    :param XdcrDepth=: Tranducer Depth in meter.
    :return: BT Range, WP Range, Range First Bin, Configured Ranges
    """

    # Get the configuration from the json file
    script_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(script_dir, 'predictor.json')
    try:
        config = json.loads(open(json_file_path).read())
    except Exception as e:
        print("Error opening JSON file Range", e)
        return (0.0, 0.0, 0.0, 0.0)

    return _calculate_predicted_range(kwargs.pop('CWPON', config['DEFAULT']['CWPON']),
                                        kwargs.pop('CWPBB', config['DEFAULT']['CWPBB']),
                                        kwargs.pop('CWPBS', config['DEFAULT']['CWPBS']),
                                        kwargs.pop('CWPBN', config['DEFAULT']['CWPBN']),
                                        kwargs.pop('CWPBL', config['DEFAULT']['CWPBL']),
                                        kwargs.pop('CBTON', config['DEFAULT']['CBTON']),
                                        kwargs.pop('CBTBB', config['DEFAULT']['CBTBB']),
                                        kwargs.pop('SystemFrequency', config['DEFAULT']['SystemFrequency']),
                                        kwargs.pop('BeamDiameter', config["BeamDiameter"]),
                                        kwargs.pop('CyclesPerElement', config["CyclesPerElement"]),
                                        kwargs.pop('BeamAngle', config["BeamAngle"]),
                                        kwargs.pop('SpeedOfSound', config["SpeedOfSound"]),
                                        kwargs.pop('CWPBB_LagLength', config["DEFAULT"]["CWPBB_LagLength"]),
                                        kwargs.pop('BroadbandPower', config["BroadbandPower"]),
                                        kwargs.pop('Salinity', config["Salinity"]),
                                        kwargs.pop('Temperature', config["Temperature"]),
                                        kwargs.pop('XdcrDepth', config["XdcrDepth"]))


def _calculate_predicted_range(_CWPON_, _CWPBB_TransmitPulseType_, _CWPBS_, _CWPBN_, _CWPBL_,
                       _CBTON_, _CBTBB_TransmitPulseType_,
                       _SystemFrequency_, _BeamDiameter_, _CyclesPerElement_,
                       _BeamAngle_, _SpeedOfSound_, _CWPBB_LagLength_, _BroadbandPower_,
                               _Salinity_, _Temperature_, _XdcrDepth_):
    """
    Get the predicted ranges for the given setup.  This will use the parameter given to calculate
    the bottom track predicted range, the water profile predicted range, range to the first bin and
    the configured range.  All results are in meters.


    All values with underscores before and after the name are given variables by the user.  All caps
    variables are given by the JSON configuration.  All other variables are calculated.

    :param _CWPON_: Flag if Water Profile is turned on.
    :param _CWPBB_TransmitPulseType_: WP broadband or narrowband.
    :param _CWPBB_LagLength_: WP lag length in meters.
    :param _CWPBS_: Bin size in meters.
    :param _CWPBN_: Number of bins.
    :param _CWPBL_: Blank distance in meters.
    :param _CBTON_: Flag if Bottom Track is turned on.
    :param _CBTBB_TransmitPulseType_: BT broadband or narrowband.
    :param _SystemFrequency_: System frequency in hz.
    :param _BeamDiameter_: Beam diameter in meters.
    :param _CyclesPerElement_: Cycles per element.
    :param _BeamAngle_: Beam angle in degrees.
    :param _SpeedOfSound_: Speed of sound in m/s.
    :param _BroadbandPower_: Broadband power.
    :param _Salinity_: Salinity in ppt.
    :param _Temperature_: Temperature in C.
    :param _XdcrDepth_: Transducer Depth in meter.
    :return: BT Range, WP Range, Range First Bin, Configured Range
    """

    script_dir = os.path.dirname(__file__)
    json_file_path = os.path.join(script_dir, 'predictor.json')

    try:
        # Get the configuration from the json file
        config = json.loads(open(json_file_path).read())
    except Exception as e:
        print("Error getting the configuration file.  Range", e)
        return (0.0, 0.0, 0.0, 0.0)

    # Speed of sound must be a value
    if _SpeedOfSound_ == 0:
        _SpeedOfSound_ = 1490

    # Wave length
    waveLength = _SpeedOfSound_ / _SystemFrequency_

    # DI
    dI = 0.0
    if waveLength == 0:
        dI = 0.0
    else:
        dI = 20.0 * math.log10(math.pi * _BeamDiameter_ / waveLength)

    # Absorption

    absorption = calc_absorption(_SystemFrequency_, _SpeedOfSound_, _Salinity_, _Temperature_, _XdcrDepth_)


    # 1200khz
    btRange_1200000 = 0.0
    wpRange_1200000 = 0.0
    refBin_1200000 = 0.0
    xmtW_1200000 = 0.0
    rScale_1200000 = math.cos(_BeamAngle_ / 180.0 * math.pi) / math.cos(config["DEFAULT"]["1200000"]["BEAM_ANGLE"] / 180.0 * math.pi);
    dI_1200000 = 20.0 * math.log10(math.pi * config["DEFAULT"]["1200000"]["DIAM"] / waveLength);

    dB_1200000 = 0.0;
    if (config["DEFAULT"]["1200000"]["BIN"] == 0) or (_CyclesPerElement_ == 0):
        dB_1200000 = 0.0
    else:
        dB_1200000 = 10.0 * math.log10(_CWPBS_ / config["DEFAULT"]["1200000"]["BIN"]) + dI - dI_1200000 - 10.0 * math.log10(config["DEFAULT"]["1200000"]["CPE"]  / _CyclesPerElement_)

    absorption_range_1200000 = config["DEFAULT"]["1200000"]["RANGE"] + ((config["DEFAULT"]["1200000"]["ABSORPTION_SCALE"] - absorption) * config["DEFAULT"]["1200000"]["RANGE"])

    if _SystemFrequency_ > config["DEFAULT"]["1200000"]["FREQ"]:
        # Ref in and xmt watt
        refBin_1200000 = config["DEFAULT"]["1200000"]["BIN"]
        xmtW_1200000 = config["DEFAULT"]["1200000"]["XMIT_W"]

        if _CBTON_:
            # Check if NB
            if _CBTBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCBTBB_Mode.NARROWBAND_LONG_RANGE.value:
                btRange_1200000 = 2.0 * rScale_1200000 * (absorption_range_1200000 + config["DEFAULT"]["1200000"]["BIN"] * dB_1200000 + 15.0 * config["DEFAULT"]["1200000"]["BIN"])
            else:
                btRange_1200000 = 2.0 * rScale_1200000 * (absorption_range_1200000 + config["DEFAULT"]["1200000"]["BIN"] * dB_1200000)
        else:
            btRange_1200000 = 0.0

        if _CWPON_:
            # Check if NB
            if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:
                wpRange_1200000 = rScale_1200000 * (absorption_range_1200000 + config["DEFAULT"]["1200000"]["BIN"] * dB_1200000 + config["DEFAULT"]["NB_PROFILE_REF"] * config["DEFAULT"]["1200000"]["BIN"])
            else:
                wpRange_1200000 = rScale_1200000 * (absorption_range_1200000 + config["DEFAULT"]["1200000"]["BIN"] * dB_1200000)
        else:
            wpRange_1200000 = 0.0
    else:
        btRange_1200000 = 0.0
        wpRange_1200000 = 0.0


    # 600khz
    btRange_600000 = 0.0
    wpRange_600000 = 0.0
    refBin_600000 = 0.0
    xmtW_600000 = 0.0
    rScale_600000 = math.cos(_BeamAngle_ / 180.0 * math.pi) / math.cos(config["DEFAULT"]["600000"]["BEAM_ANGLE"] / 180.0 * math.pi)
    dI_600000 = 20.0 * math.log10(math.pi * config["DEFAULT"]["600000"]["DIAM"] / waveLength)

    dB_600000 = 0.0;
    if config["DEFAULT"]["600000"]["BIN"] == 0 or _CyclesPerElement_ == 0:
        dB_600000 = 0.0;
    else:
        dB_600000 = 10.0 * math.log10(_CWPBS_ / config["DEFAULT"]["600000"]["BIN"]) + dI - dI_600000 - 10.0 * math.log10(config["DEFAULT"]["600000"]["CPE"] / _CyclesPerElement_)

    absorption_range_600000 = config["DEFAULT"]["600000"]["RANGE"] + ((config["DEFAULT"]["600000"]["ABSORPTION_SCALE"] - absorption) * config["DEFAULT"]["600000"]["RANGE"])

    if (_SystemFrequency_ > config["DEFAULT"]["600000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["1200000"]["FREQ"]):
        # Ref Bin and xmt watt
        refBin_600000 = config["DEFAULT"]["600000"]["BIN"];
        xmtW_600000 = config["DEFAULT"]["600000"]["XMIT_W"];

        if _CBTON_:
            # Check if NB
            if _CBTBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCBTBB_Mode.NARROWBAND_LONG_RANGE.value:
                btRange_600000 = 2.0 * rScale_600000 * (absorption_range_600000 + config["DEFAULT"]["600000"]["BIN"] * dB_600000 + 15.0 * config["DEFAULT"]["600000"]["BIN"] )
            else:
                btRange_600000 = 2.0 * rScale_600000 * (absorption_range_600000 + config["DEFAULT"]["600000"]["BIN"] * dB_600000)
        else:
            btRange_600000 = 0.0

        if _CWPON_:
            # Checck if NB
            if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:
                wpRange_600000 = rScale_600000 * (absorption_range_600000 + config["DEFAULT"]["600000"]["BIN"] * dB_600000 + config["DEFAULT"]["NB_PROFILE_REF"] * config["DEFAULT"]["600000"]["BIN"] )
            else:
                wpRange_600000 = rScale_600000 * (absorption_range_600000 + config["DEFAULT"]["600000"]["BIN"] * dB_600000)
        else:
            wpRange_600000 = 0.0
    else:
        btRange_600000 = 0.0
        wpRange_600000 = 0.0


    # 300khz
    btRange_300000 = 0.0
    wpRange_300000 = 0.0
    refBin_300000 = 0.0
    xmtW_300000 = 0.0
    rScale_300000 = math.cos(_BeamAngle_ / 180.0 * math.pi) / math.cos(config["DEFAULT"]["300000"]["BEAM_ANGLE"] / 180.0 * math.pi)
    dI_300000 = 20.0 * math.log10(math.pi * config["DEFAULT"]["300000"]["DIAM"] / waveLength)

    dB_300000 = 0.0
    if (config["DEFAULT"]["300000"]["BIN"] == 0) or (_CyclesPerElement_ == 0):
        dB_300000 = 0.0
    else:
        dB_300000 = 10.0 * math.log10(_CWPBS_ / config["DEFAULT"]["300000"]["BIN"]) + dI - dI_300000 - 10.0 * math.log10(config["DEFAULT"]["300000"]["CPE"] / _CyclesPerElement_)

    absorption_range_300000 = config["DEFAULT"]["300000"]["RANGE"] + ((config["DEFAULT"]["300000"]["ABSORPTION_SCALE"] - absorption) * config["DEFAULT"]["300000"]["RANGE"])

    if (_SystemFrequency_ > config["DEFAULT"]["300000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["600000"]["FREQ"]):
        # Ref Bin and xmt watt
        refBin_300000 = config["DEFAULT"]["300000"]["BIN"]
        xmtW_300000 = config["DEFAULT"]["300000"]["XMIT_W"]

        if _CBTON_:
            # Check if NB
            if _CBTBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCBTBB_Mode.NARROWBAND_LONG_RANGE.value:
                btRange_300000 = 2.0 * rScale_300000 * (absorption_range_300000 + config["DEFAULT"]["300000"]["BIN"] * dB_300000 + 15.0 * config["DEFAULT"]["300000"]["BIN"])
            else:
                btRange_300000 = 2.0 * rScale_300000 * (absorption_range_300000 + config["DEFAULT"]["300000"]["BIN"] * dB_300000)
        else:
            btRange_300000 = 0.0

        if _CWPON_:
            # Checck if NB
            if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:
                wpRange_300000 = rScale_300000 * (absorption_range_300000 + config["DEFAULT"]["300000"]["BIN"] * dB_300000 + config["DEFAULT"]["NB_PROFILE_REF"] * config["DEFAULT"]["300000"]["BIN"])
            else:
                wpRange_300000 = rScale_300000 * (absorption_range_300000 + config["DEFAULT"]["300000"]["BIN"] * dB_300000)
        else:
            wpRange_300000 = 0.0
    else:
        # Return 0 if not selected
        btRange_300000 = 0.0
        wpRange_300000 = 0.0


    # 150khz
    btRange_150000 = 0.0
    wpRange_150000 = 0.0
    refBin_150000 = 0.0
    xmtW_150000 = 0.0
    rScale_150000 = math.cos(_BeamAngle_ / 180.0 * math.pi) / math.cos(config["DEFAULT"]["150000"]["BEAM_ANGLE"] / 180.0 * math.pi)
    dI_150000 = 20.0 * math.log10(math.pi * config["DEFAULT"]["150000"]["DIAM"] / waveLength)

    dB_150000 = 0.0;
    if (config["DEFAULT"]["150000"]["BIN"] == 0) or (_CyclesPerElement_ == 0):
        dB_150000 = 0.0
    else:
        dB_150000 = 10.0 * math.log10(_CWPBS_ / config["DEFAULT"]["150000"]["BIN"]) + dI - dI_150000 - 10.0 * math.log10(config["DEFAULT"]["150000"]["CPE"] / _CyclesPerElement_)

    absorption_range_150000 = config["DEFAULT"]["150000"]["RANGE"] + ((config["DEFAULT"]["150000"]["ABSORPTION_SCALE"] - absorption) * config["DEFAULT"]["150000"]["RANGE"])

    if (_SystemFrequency_ > config["DEFAULT"]["150000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["300000"]["FREQ"]):
        # Ref Bin and xmt watt
        refBin_150000 = config["DEFAULT"]["150000"]["BIN"]
        xmtW_150000 = config["DEFAULT"]["150000"]["XMIT_W"]

        if _CBTON_:
            # Check if NB
            if _CBTBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCBTBB_Mode.NARROWBAND_LONG_RANGE.value:
                btRange_150000 = 2.0 * rScale_150000 * (absorption_range_150000 + config["DEFAULT"]["150000"]["BIN"] * dB_150000 + 15.0 * config["DEFAULT"]["150000"]["BIN"])
            else:
                btRange_150000 = 2.0 * rScale_150000 * (absorption_range_150000 + config["DEFAULT"]["150000"]["BIN"] * dB_150000)
        else:
            btRange_150000 = 0.0

        if _CWPON_:
            # Checck if NB
            if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:
                wpRange_150000 = rScale_150000 * (absorption_range_150000 + config["DEFAULT"]["150000"]["BIN"] * dB_150000 + config["DEFAULT"]["NB_PROFILE_REF"] * config["DEFAULT"]["150000"]["BIN"])
            else:
                wpRange_150000 = rScale_150000 * (absorption_range_150000 + config["DEFAULT"]["150000"]["BIN"] * dB_150000)
        else:
            wpRange_150000 = 0.0
    else:
        # Return 0 if not selected
        btRange_150000 = 0.0
        wpRange_150000 = 0.0


    # 75khz
    btRange_75000 = 0.0
    wpRange_75000 = 0.0
    refBin_75000 = 0.0
    xmtW_75000 = 0.0
    rScale_75000 = math.cos(_BeamAngle_ / 180.0 * math.pi) / math.cos(config["DEFAULT"]["75000"]["BEAM_ANGLE"] / 180.0 * math.pi)
    dI_75000 = 20.0 * math.log10(math.pi * config["DEFAULT"]["75000"]["DIAM"] / waveLength)

    dB_75000 = 0.0;
    if (config["DEFAULT"]["75000"]["BIN"] == 0) or (_CyclesPerElement_ == 0):
        dB_75000 = 0.0
    else:
        dB_75000 = 10.0 * math.log10(_CWPBS_ / config["DEFAULT"]["75000"]["BIN"]) + dI - dI_75000 - 10.0 * math.log10(config["DEFAULT"]["75000"]["CPE"] / _CyclesPerElement_)

    absorption_range_75000 = config["DEFAULT"]["75000"]["RANGE"] + ((config["DEFAULT"]["75000"]["ABSORPTION_SCALE"] - absorption) * config["DEFAULT"]["75000"]["RANGE"])

    if (_SystemFrequency_ > config["DEFAULT"]["75000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["150000"]["FREQ"]):
        # Ref Bin and xmt watt
        refBin_75000 = config["DEFAULT"]["75000"]["BIN"]
        xmtW_75000 = config["DEFAULT"]["75000"]["XMIT_W"]

        if _CBTON_:
            # Check if NB
            if _CBTBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCBTBB_Mode.NARROWBAND_LONG_RANGE.value:
                btRange_75000 = 2.0 * rScale_75000 * (absorption_range_75000 + config["DEFAULT"]["75000"]["BIN"] * dB_75000 + 15.0 * config["DEFAULT"]["75000"]["BIN"])
            else:
                btRange_75000 = 2.0 * rScale_75000 * (absorption_range_75000 + config["DEFAULT"]["75000"]["BIN"] * dB_75000)
        else:
            btRange_75000 = 0.0

        if _CWPON_:
            # Checck if NB
            if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:
                wpRange_75000 = rScale_75000 * (absorption_range_75000 + config["DEFAULT"]["75000"]["BIN"] * dB_75000 + config["DEFAULT"]["NB_PROFILE_REF"] * config["DEFAULT"]["75000"]["BIN"])
            else:
                wpRange_75000 = rScale_75000 * (absorption_range_75000 + config["DEFAULT"]["75000"]["BIN"] * dB_75000)
        else:
            wpRange_75000 = 0.0;
    else:
        # Return 0 if not selected
        btRange_75000 = 0.0
        wpRange_75000 = 0.0


    # 38khz
    btRange_38000 = 0.0
    wpRange_38000 = 0.0
    refBin_38000 = 0.0
    xmtW_38000 = 0.0
    rScale_38000 = math.cos(_BeamAngle_ / 180.0 * math.pi) / math.cos(config["DEFAULT"]["38000"]["BEAM_ANGLE"] / 180.0 * math.pi)
    dI_38000 = 20.0 * math.log10(math.pi * config["DEFAULT"]["38000"]["DIAM"] / waveLength)

    dB_38000 = 0.0;
    if (config["DEFAULT"]["38000"]["BIN"] == 0) or (_CyclesPerElement_ == 0):
        dB_38000 = 0.0
    else:
        dB_38000 = 10.0 * math.log10(_CWPBS_ / config["DEFAULT"]["38000"]["BIN"]) + dI - dI_38000 - 10.0 * math.log10(config["DEFAULT"]["38000"]["CPE"] / _CyclesPerElement_)

    absorption_range_38000 = config["DEFAULT"]["38000"]["RANGE"] + ((config["DEFAULT"]["38000"]["ABSORPTION_SCALE"] - absorption) * config["DEFAULT"]["38000"]["RANGE"])

    if (_SystemFrequency_ > config["DEFAULT"]["38000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["75000"]["FREQ"]):
        # Ref Bin and xmt watt
        refBin_38000 = config["DEFAULT"]["38000"]["BIN"]
        xmtW_38000 = config["DEFAULT"]["38000"]["XMIT_W"]

        if _CBTON_:
            # Check if NB
            if _CBTBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCBTBB_Mode.NARROWBAND_LONG_RANGE.value:
                btRange_38000 = 2.0 * rScale_38000 * (absorption_range_38000 + config["DEFAULT"]["38000"]["BIN"] * dB_38000 + 15.0 * config["DEFAULT"]["38000"]["BIN"]);
            else:
                btRange_38000 = 2.0 * rScale_38000 * (absorption_range_38000 + config["DEFAULT"]["38000"]["BIN"] * dB_38000)
        else:
            btRange_38000 = 0.0

        if _CWPON_:
            # Checck if NB
            if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:
                wpRange_38000 = rScale_38000 * (absorption_range_38000 + config["DEFAULT"]["38000"]["BIN"] * dB_38000 + config["DEFAULT"]["NB_PROFILE_REF"] * config["DEFAULT"]["38000"]["BIN"])
            else:
                wpRange_38000 = rScale_38000 * (absorption_range_38000 + config["DEFAULT"]["38000"]["BIN"] * dB_38000)
        else:
            wpRange_38000 = 0.0
    else:
        # Return 0 if not selected
        btRange_38000 = 0.0
        wpRange_38000 = 0.0


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
    elif (_SystemFrequency_ > config["DEFAULT"]["38000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["75000"]["FREQ"]):         #38 khz
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


    # Xmt Scale
    xmtScale = 1.0;
    if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:        # Check if NB
        xmtScale = 1.0
    else:
        # Check for bad value
        if lagSamples == 0:
            xmtScale = 1.0
        # Check which Broadband power is used
        elif _BroadbandPower_:
            xmtScale = (lagSamples - 1.0) / lagSamples
        else:
            xmtScale = 1.0 / lagSamples


    # Range Reduction
    rangeReduction = 0.0;

    # Get the sum of all the selected WP XmtW and RefBin
    sumXmtW = xmtW_1200000 + xmtW_600000 + xmtW_300000 + xmtW_150000 + xmtW_75000 + xmtW_38000
    sumRefBin = refBin_1200000 + refBin_600000 + refBin_300000 + refBin_150000 + refBin_75000 + refBin_38000
    beamXmtPowerProfile = xmtScale * sumXmtW

    # Check for bad values
    if sumXmtW == 0:
        rangeReduction = 0.0
    else:
        rangeReduction = 10.0 * math.log10(beamXmtPowerProfile / sumXmtW) * sumRefBin + 1.0


    # Bin Samples
    binSamples = 0;
    if metersPerSample == 0:
        binSamples = 0
    else:
        binSamples = math.trunc(_CWPBS_ / metersPerSample)


    # Code Repeats
    codeRepeats = 0;
    if lagSamples == 0:
        codeRepeats = 0
    else:
        # Cast BinSamples and LagSamples to double because Truncate only takes doubles
        # Make the result of Truncate an int
        if (math.trunc(binSamples / lagSamples)) + 1.0 < 2.0:
            codeRepeats = 2
        else:
            codeRepeats = (math.trunc(binSamples / lagSamples)) + 1


    # First Bin Position
    pos = 0.0;
    if _CWPBB_TransmitPulseType_ == rti_python.ADCP.AdcpCommands.eCWPBB_TransmitPulseType.NARROWBAND.value:
        pos = (2.0 * _CWPBS_ + 0.05) / 2.0
    else:
        if _CWPBB_TransmitPulseType_ > 1:
            pos = _CWPBS_
        else:
            pos = (lagSamples * (codeRepeats - 1.0) * metersPerSample + _CWPBS_ + _CWPBB_LagLength_) / 2.0

    firstBinPosition = _CWPBL_ + pos;


    # Profile Range based off Settings
    profileRangeSettings = _CWPBL_ + (_CWPBS_ * _CWPBN_);


    # Set the predicted ranges PredictedRanges
    wp = 0.0;
    bt = 0.0;

    if _SystemFrequency_ > config["DEFAULT"]["1200000"]["FREQ"]:                                                                        # 1200 khz
        bt = btRange_1200000
        wp = wpRange_1200000 + rangeReduction
    elif (_SystemFrequency_ > config["DEFAULT"]["600000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["1200000"]["FREQ"]):      # 600 khz
        bt = btRange_600000
        wp = wpRange_600000 + rangeReduction
    elif (_SystemFrequency_ > config["DEFAULT"]["300000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["600000"]["FREQ"]):       # 300 khz
        bt = btRange_300000
        wp = wpRange_300000 + rangeReduction
    elif (_SystemFrequency_ > config["DEFAULT"]["150000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["300000"]["FREQ"]):       # 150 khz
        bt = btRange_150000
        wp = wpRange_150000 + rangeReduction
    elif (_SystemFrequency_ > config["DEFAULT"]["75000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["150000"]["FREQ"]):        # 75 khz
        bt = btRange_75000
        wp = wpRange_75000 + rangeReduction
    elif (_SystemFrequency_ > config["DEFAULT"]["38000"]["FREQ"]) and (_SystemFrequency_ < config["DEFAULT"]["75000"]["FREQ"]):         #38 khz
        bt = btRange_38000;
        wp = wpRange_38000 + rangeReduction;

    return (bt, wp, firstBinPosition, profileRangeSettings)


def calc_absorption(_SystemFrequency_, _SpeedOfSound_, _Salinity_, _Temperature_, _XdcrDepth_):
    """
    Calculate the water absorption.
    :param _SystemFrequency_: System frequency
    :param _SpeedOfSound_:  Speed of Sound m/s
    :param _Salinity_: Salinity in ppt.
    :param _Temperature_: Water Temperature in C
    :param _XdcrDepth_: Transducer Depth in m.
    :return: Water Absorption.
    """

    if _SpeedOfSound_ == 0 or _Salinity_ == 0 or _SystemFrequency_ == 0:
        return 0

    pH = 8.0
    P1 = 1.0

    # Frequency
    freq = _SystemFrequency_ / 1000.0

    # A1
    # dB Km^-1 KHz^-1
    A1 = 8.68 / _SpeedOfSound_ * 10.0 ** (0.78 * pH - 5.0)

    # f1
    f1 = 2.8 * ((_Salinity_ / 35.0) ** 0.5) * (10.0 ** (4.0 - 1245.0 / (273.0 + _Temperature_)))

    # A2
    #  dB km^-1 kHz^-1
    A2 = 21.44 * _Salinity_ / _SpeedOfSound_ * (1.0 + 0.025 * _Temperature_)

    # P2
    P2 = 1.0 - 1.37 * (10.0 ** (-4.0)) * _XdcrDepth_ + 6.2 * (10.0 ** (-9.0)) * (_XdcrDepth_ ** 2)

    # f2
    # kHz
    f2 = 8.17 * (10.0 ** (8.0 - 1990.0 / (273.0 + _Temperature_))) / (1.0 + 0.0018 * (_Salinity_ - 35.0))

    # A3
    A3 = 4.93 * (10.0 ** (-4.0)) - 2.59 * (10.0 ** (-5.0)) * _Temperature_ + 9.11 * (10.0 ** (-7.0)) * (_Temperature_ ** 2.0)

    # P3
    P3 = 1.0 - 3.83 * (10.0 ** (-5.0)) * _XdcrDepth_ + 4.9 * (10.0 ** (-10.0)) * (_XdcrDepth_ ** 2.0)

    # Boric Acid Relaxation
    bar = A1 * P1 * f1 * (freq ** 2.0) / ((freq ** 2.0) + (f1 ** 2.0)) / 1000.0

    # MgSO3 Magnesium Sulphate Relaxation
    msr = A2 * P2 * f2 * (freq ** 2.0) / ((freq ** 2.0) + (f2 ** 2.0)) / 1000.0

    # Freshwater Attenuation
    fa = A3 * P3 * (freq ** 2.0) / 1000.0

    # Absorption
    return bar + msr + fa


def test_calc_range():
    (bt_range, wp_range, first_bin, cfg_range) = calculate_predicted_range(CWPON=True,
                                                                           CWPBB=1,
                                                                           CWPBS=4.0,
                                                                           CWPBN=30,
                                                                           CWPBL=1.0,
                                                                           CBTON=True,
                                                                           CBTBB=1,
                                                                           SystemFrequency=288000.0,
                                                                           BeamDiameter=0.075,
                                                                           CyclesPerElement=12,
                                                                           BeamAngle=20,
                                                                           SpeedOfSound=1490,
                                                                           CWPBB_LagLength=1.0,
                                                                           BroadbandPower=True,
                                                                           Temperature=10.0,
                                                                           Salinity=35.0,
                                                                           XdcrDepth=0.0)

    user_cfg_range = 1.0 + (4.0 * 30)

    assert pytest.approx(wp_range, 0.01) == 100.05
    assert pytest.approx(bt_range, 0.01) == 199.14
    assert pytest.approx(first_bin, 0.01) == 5.484
    assert pytest.approx(cfg_range, 0.01) == user_cfg_range


def test_calc_range_nb():
    (bt_range, wp_range, first_bin, cfg_range) = calculate_predicted_range(CWPON=True,
                                                                           CWPBB=0,
                                                                           CWPBS=4.0,
                                                                           CWPBN=30,
                                                                           CWPBL=1.0,
                                                                           CBTON=True,
                                                                           CBTBB=0,
                                                                           SystemFrequency=288000.0,
                                                                           BeamDiameter=0.075,
                                                                           CyclesPerElement=12,
                                                                           BeamAngle=20,
                                                                           SpeedOfSound=1490,
                                                                           CWPBB_LagLength=1.0,
                                                                           BroadbandPower=True,
                                                                           Temperature=10.0,
                                                                           Salinity=35.0,
                                                                           XdcrDepth=0.0)

    user_cfg_range = 1.0 + (4.0 * 30)

    assert pytest.approx(wp_range, 0.01) == 152.57
    assert pytest.approx(bt_range, 0.01) == 319.14
    assert pytest.approx(first_bin, 0.01) == 5.025
    assert pytest.approx(cfg_range, 0.01) == user_cfg_range

