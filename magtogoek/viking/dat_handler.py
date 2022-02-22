"""
DateL February 15 2022
Made by jeromejguay
This script is used to decode the data send by Viking as of February 2022 format version.

The Buoy Data
-------------
[NOM]: Buoy information
    'PMZA-RIKI,110000,240521,8.3.1,000018C0D36B,00.3,00.0,48 39.71N,068 34.90W'
[COMP]: Compass data
    '000DA1B4,FFC58202,-4.634,88.61,0.654,27.98,11.14,24.94'
[OCR]: Radiance, Irradiance
    (note used)
[Triplet]: Water Surface Fluorescence
    'BBFL2W-1688	05/24/21	10:59:03	700	1376	2.786E-03	695	190	1.066E+00	460	85	3.454E+00'
[Par_digi]: PAR (Photosynthetic Active Radiation)
    '110100,240521,SATPRS1093,30.415,510.646,-1.7,5.7,11.0,162'
[SUNA]: Near surface Nitrate concentration
    'SATSLC1363,2021145,12.000192,7.63,0.1068,0.2978,0.2471,0.00,0.000160'
    (0) Model/serial          (1) YearDdays     (2) Hours of day
    (3) uMol,                 (4) mgN/L,        (5) absorbance 254.31 nm,
    (6) absorbance 350.16 nm, (7) bromide mg/L, (8) spectrum average,
[GPS]: GPS
    '110132,A,4839.7541,N,06834.8903,W,003.7,004.4,240521,017.5,W,*7B'
    (0) GPRMC:
    (1) time : (utc) hhmmss.ss
    (2) A/V : Position status. A = Data valid, V = Data invalid.
    (3) lat : DDmm.mmmm
    (4) N/S :
    (5) lon : DDmm.mmmm
    (6) E/W :
    (7) speed : Knots, x.x
    (8) true course:  x.x True degree
    (9) date: ddmmyy
    (10) variation, magnetic x.x
    (11) E/W, mode + checksum : ((A)utonomous, (D)ifferential, (E)stimated, (M)anual input, (N) data not valid.
[CTD]: Surface Temperature, Salinity et Density
    '   7.3413,  2.45966,  23.2697, 18.1612'
[CTDO]: Surace Temperature, Salinity, Dissolved Oxygen
    '...'
[RTI]: Rowetech ADCP. Near surface velocities (6 meter deep ?)
    bin number, position_cm, 4-beam_vel, 4-enu, 4-corr, 4-amp, ... 16 more for bt.
    '1,407,-258,-157,-263,-32,-160,-369,-202,-30,100,100,100,100,84,83,83,84'
    'Bot,-3,-6,-50,56,129,101,-4,-4,100,100,100,100,76,78,78,77'
[RDI]: Teledyne ADCP. Near surface velocities (6 meter deep ?)
    '110000,240521,E3FFBB0022001400'
[WAVE_M]: Waves (Multi-Électronique sensor)
    date, hour, wave period, averaged wave height, averaged wave height (1/3 period, highest waves), max height.
    '2021/05/24,10:45:00,6.61,0.60,0.48,1.29'
[WAVE_S]: Waves (Seaview sensor)
    NMEA str, Heading, average height, dominant period, wave direction, Hmax, Hmax2, Pmax. angR, angP, date time, index*chk
    '$PSVSW,201.63,1.239,8.695,266.983,1.811,1.575,9.668,3.039,11.004,2021-09-21 00:28:51,2048*76'
[WXT520]: Meteo Conditions
    'Dn=163D,Dm=181D,Dx=192D,Sn=18.0K,Sm=22.7K,Sx=28.0K'
    'Rc=0.00M,Rd=0s,Ri=0.0M,Hc=0.0M,Hd=0s,Hi=0.0M'
    'Ta=6.8C,Ua=45.0P,Pa=1025.4H'
    'Th=7.6C,Vh=14.1#,Vs=14.4V,Vr=3.503V'
    Dn = minimal wind direction
    Dm = average wind direction
    Dx = maximal wind direction
    Sn = minimal wind strength
    Sm = average wind strength
    Sx = maximal wind strength
    Rc = rain accumulation since midnight in mm
    Rd = rain duration since midnight in second
    Ri = rain intensity in mm/h
    Hc = Hail accumulation in hits/cm²
    Hd = Hail duration since midnight in second
    Hi = Hail intensity in hits/cm²/h
    Ta = temperature in celsius
    Ua = ambient humidity
    Pa = atmospheric pressure.
[WMT700]: Wind:
    'Dn=162.41D,Dm=179.40D,Dx=196.13D,Sn=14.74K,Sm=21.53K,Sx=27.46K'
[wPH]: Surface (water) pH.
    'SEAFET02138,2021-05-24T11:01:26,1266,0000,7.9519,7.9825,-0.892024,-0.938712,7.4124,3.4,7.6'
    sample_number, error_flag, PH_ext, PH_int, ph_ext_volt, ph_ext_volt, pH_temperature, relative_humidity, internal_temperature
[CO2_A]: CO2 in Air. (A/D : analogue device ?. units-> counts)
    Measurement type,Year,Month,Day,Hour,Minute,Second,Zero A/D,Current A/D.
    CO2_ppm,IRGA temperature,Humidity_mbar,Humidity sensor temperature,Gas stream pressure_mbar,
    Las could be `Battery voltage` or `IRGA temperature sensor`.
    'W M,2021,05,25,11,51,24,55544,52106,448.94,40.00,10.70,13.40,1000,12.3'
[CO2_W]: Near surface CO2 in Water
    See CO2_A
[Debit]: Near surface current measured by flow meter.
    '00000167'
    20_000 Pulse = 1 nautical miles. Pulse are measured over 60 seconds.
    1 Pulse = 0.0926 m -> 1 Pulse over 60s -> 0.001543 m/s
[p0] ou [p1]: Power
    (not used)
[VEMCO] Acoustic receiver
     Date       Time    ,Protocal, Serial number
    '2018-05-05 04:27:35,A69-1602,46179'

[MO]: Short string. Not Used
    '942+03272+00360##########799290270601014514000902010401417310###73000502F9FF0300,000,[W]A forced start yoyo was sent'
    Used to get information about the winch (ctd-yoyo) that is a [W] tag within the short string.

    [W]Not in time slot
    -Indicate that we’re not inside the time slot designed to do a MiniWinch mission.
    [W]Too soon after a power-up
    -Indicate that the Buoy Controller just restart and there wasn’t a MiniWinch mission since.
    [W]A start yoyo was sent
    -Indicate that a MiniWinch mission command was send.
    [W]A yoyo mission is in progress
    -Indicate that a MiniWinch mission is still running
    [W]94>  2.6149,  2.57904,   95.000,  28.2356
    -Indicate that a MiniWinch mission ended normally and contains the string received by the CTD
     of the profiler, when this one was in his lowest in his mission.
    [W]Interval not elapsed
    -Indicate there wasn’t a MiniWinch mission because the interval programmed between two
     missions is not elapsed.


    Other message found in files: But not in documentation...
    [W]A forced start yoyo was sent
    [W]35>*** Cable or CTD Jam Detected, Trying To Stop And Retract ***
    [W]22>Error ! Motor Stopped But Drum Running
    [W]Waves too high
    [W]I.N.E
    [W]30>Attention ! Stop On Switch Overrun
    [W]Voltage is too low


    Generated winch files.
    --------------
    <buoy name>_WCH_<date>.dat
    #1 Date GPS
    #2 Hour GPS
    #3 The message received of the Mini-Winch controller. It can be text if it begins with [W]94> you got the data
    received by the CTD when it was at it lowest; or the temperature (°C), Conductivity (S/m), Pressure (decibars), salinity (PSU).

Data That Need Processing
-------------------------
    WpH

Notes
-----
    FIXME The RAW data file descriptions of the data should be added somewhere.
    OCR are not current installed on the buoy. A function was made but is not in used. Furthermore, the documentation
    was not clear on how to decode the hexadecimal values. Here is an exAmple of the OCR string.
    [OCR],29,220916
    D,32,7FF61F47,7FF96AAD,80019C5D,7FF8EEBB,7FF0B2E5,7FFB045E,7FFC0AF4,6CEF2E,5058B5,560C72,516F8D,78A870,48660F,9B89F3,7FF61F00,7FF96AC0,80019C40,7FF8EF00,7FF0B300,7FFB03C0,7FFC0A80
    W,12,7FED43A9,7FF5BCC5,8005D91A,8015D956,7FFCD34E,7FF14B6D,7FFC38AC,29BF350,FA9F3A,9ABAD1,1B610D7,3DD6947,CF5AC95,1635C01,7FED4540,7FF5BD00,8005D900,8015D780,7FFCD6C0,7FF13EC0,7FFC3780

TODO
----
    Get CTD-YOYO winch files.
    Reshape adcp data and others.
"""

import struct
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Union
from math import atan2, sqrt, pi
from datetime import datetime, timedelta
import re
from magtogoek.utils import get_files_from_expression

import matplotlib
import matplotlib.pyplot as plt

matplotlib.use('Qt5Agg')

FILL_VALUE = -32768 # Reusing the same fill value as teledyne (RDI)

TAGS = ["NOM", "COMP", "Triplet", "Par_digi", "SUNA", "GPS",
        "CTD", "CTDO", "RTI", "RDI", "WAVE_M", "WAVE_S", "WXT520",
        "WMT700", "WpH", "CO2_W", "CO2_A", "Debit", "VEMCO"]  # "OCR", "MO", "FIN"]

DATA_BLOCK_REGEX = re.compile(r"(\[NOM].+?)\[FIN]", re.DOTALL)
DATA_TAG_REGEX = re.compile(rf"\[({'|'.join(TAGS)})],?((?:(?!\[).)*)", re.DOTALL)

NOM_KEYS = ['time', 'latitude_N', 'longitude_E']
COMP_KEYS = ['heading', 'pitch', 'roll', 'tilt', 'pitch_std', 'roll_std', 'tilt_std']
TRIPLET_KEYS = ['time', 'model_number', 'serial_number',
                'wavelengths_700', 'gross_value_700', 'calculated_value_700',
                'wavelengths_695', 'gross_value_695', 'calculated_value_695',
                'wavelengths_460', 'gross_value_460', 'calculated_value_460']
PAR_DIGI_KEYS = ['time', 'model_number', 'serial_number', 'timer_s', 'PAR', 'pitch', 'roll', 'intern_temperature']
SUNA_KEYS = ["time", "model_number", "serial_number", "uMol", "mgNL", "absorbance_254_31",
             "absorbance_350_16", "bromide_mgL", "spectrum_average"]
GPS_KEYS = ['time', 'latitude_N', 'longitude_E', 'speed', 'course', 'variation_E']
CTD_KEYS = ['temperature', 'conductivity', 'salinity', 'density']
CTDO_KEYS = ['temperature', 'conductivity', 'oxygen', 'salinity']
RTI_KEYS = ['bin', 'position_cm',
            'beam1', 'beam2','beam3', 'beam4',
            'u', 'v', 'w', 'e',
            'corr1', 'corr2', 'corr3', 'corr4',
            'amp1', 'amp2', 'amp3', 'amp4',
            'bt_beam1', 'bt_beam2', 'bt_beam3', 'bt_beam4',
            'bt_u', 'bt_v','bt_w', 'bt_e',
            'bt_corr1', 'bt_corr2', 'bt_corr3', 'bt_corr4',
            'bt_amp1', 'bt_amp2', 'bt_amp3', 'bt_amp4']
RDI_KEYS = ['time', 'u', 'v', 'w', 'e']
WAVE_M_KEYS = ['time', "period", "average_height", "significant_height", "maximal_height"]
WAVE_S_KEYS = ['time', 'heading', 'average_height', 'dominant_period', 'wave_direction',
               'Hmax', 'Hmax2', 'pmax', 'roll', 'pitch']
WXT520_KEYS = ['Dn', 'Dm', 'Dx', 'Sn', 'Sm', 'Sx', 'Rc', 'Rd', 'Ri', 'Hc', 'Hd', 'Hi',
               'Ta', 'Ua', 'Pa', 'Th', 'Vh', 'Vs', 'Vr']
WMT700_KEYS = ['Dn', 'Dm', 'Dx', 'Sn', 'Sm', 'Sx']
WPH_KEYS = ['time', 'model', 'serial_number', 'sample_number', 'error_flag',
            'ext_ph', 'int_ph', 'ph_temperature', 'rel_humidity', 'int_temperature']
CO2_W_KEYS = ["time", "auto-zero", "current", "co2_ppm", "irga_temperature", "humidity_mbar",
              "humidity_sensor_temperature", "cell_gas_pressure_mar"]
CO2_A_KEYS = ['time', 'auto-zero', 'current', "co2_ppm", 'irga_temperature', 'humidity_mbar',
              'humidity_sensor_temperature', "cell_gas_pressure_mar"]
DEBIT_KEYS = ['flow_ms']
VEMCO_KEYS = ['time', 'protocol', 'serial_number']


class VikingData():
    """Object to store Viking data. """
    def __init__(self, buoy_name: str, firmware: str, controller_sn: str):
        self.buoy_name: str = buoy_name
        self.firmware: str = firmware
        self.controller_sn: str = controller_sn

        self.time: list = []
        self.latitude: list = []
        self.longitude: list = []
        self.comp: list = {key: [] for key in COMP_KEYS}
        self.triplet: list = {key: [] for key in TRIPLET_KEYS}
        self.par_digi: list = {key: [] for key in PAR_DIGI_KEYS}
        self.suna: list = {key: [] for key in SUNA_KEYS}
        self.gps: list = {key: [] for key in GPS_KEYS}
        self.ctd: list = {key: [] for key in CTD_KEYS}
        self.ctdo: list = {key: [] for key in CTDO_KEYS}
        self.rti: list = {key: [] for key in RTI_KEYS}
        self.rdi: list = {key: [] for key in RDI_KEYS}
        self.wave_m: list = {key: [] for key in WAVE_M_KEYS}
        self.wave_s: list = {key: [] for key in WAVE_S_KEYS}
        self.wxt520: list = {key: [] for key in WXT520_KEYS}
        self.wmt700: list = {key: [] for key in WMT700_KEYS}
        self.wph: list = {key: [] for key in WPH_KEYS}
        self.co2_w: list = {key: [] for key in CO2_W_KEYS}
        self.co2_a: list = {key: [] for key in CO2_A_KEYS}
        self.debit: list = {key: [] for key in DEBIT_KEYS}
        self.vemco: list = {key: [] for key in VEMCO_KEYS}

    def __repr__(self):
        repr = f"""{self.__class__} 
buoy_name: {self.buoy_name}
firmware: {self.firmware}
controller_sn: {self.controller_sn}
data: (length: {len(self)})  
"""
        for tag in self.tags:
            if self.__dict__[tag] is not None:
                repr+=f"  {tag}: (" + ", ".join(list(self.__dict__[tag].keys())) + ")\n"
        return repr

    def __len__(self):
        return len(self.time)

    @property
    def tags(self):
        return ['comp', 'triplet', 'par_digi', 'suna', 'gps', 'ctd', 'ctdo', 'rti', 'rdi',
                'wave_m', 'wave_s', 'wxt520', 'wmt700', 'wph', 'co2_w', 'co2_a', 'debit', 'vemco']

    def _squeeze_data(self):
        """Set tag where all data are missing to None"""
        for tag in self.tags:
            uniques_values = set()
            [uniques_values.update(value) for value in self.__dict__[tag].values()]
            if len(uniques_values) == 1:
                self.__dict__[tag] = None

#    def _reshape_for_missing_data(self):
#        """Some of rti, rdi and triplet missing values need to be reshaped."""
#        if self.rti is not None:
#            for key in ['beam_vel_mms', 'enu_mms', 'corr_pc', 'amp_dB',
#                        'bt_beam_vel_mms', 'bt_enu_mms', 'bt_corr_pc', 'bt_amp_dB']:
#                for index, value in enumerate(self.rti[key]):
#                    if value == FILL_VALUE:
#                        self.rti[key][index] = 4*(FILL_VALUE,)
#
#       if self.rdi is not None:
#            for index, value in enumerate(self.rdi['enu_mms']):
#                if value == FILL_VALUE:
#                    self.rdi['enu_mms'][index] = 4 * (FILL_VALUE,)
#        if self.triplet is not None:
#            for key in ['wavelengths', 'gross_value']:
#                for index, value in enumerate(self.triplet[key]):
#                    if value == FILL_VALUE:
#                        self.triplet[key][index] = 3 * (FILL_VALUE,)


class VikingReader():
    """Use to read RAW dat files from viking buoy.
    The data are puts in VikingData object and are accessible as attributes."""
    def __init__(self):
        self._buoys_data: Dict[str: VikingData] = {}

    def __repr__(self):
        repr = f"""{self.__class__} 
buoys:\n"""
        for buoy, viking_data in self._buoys_data.items():
            repr += f"  {buoy}: (length = {len(viking_data)})\n"
        return repr

    def read(self, filenames, century=21):
        filenames = get_files_from_expression(filenames)
        decoded_data = []
        for _filename in filenames:
            with open(_filename) as f:
                data_received = f.read()
                decoded_data += _decode_transmitted_data(data_received=data_received, century=century)

        self._make_viking_data(decoded_data)

        return self

    def _make_viking_data(self, decoded_data: dict):

        buoys = set([(block['buoy_name'], block['firmware'], block['controller_sn']) for block in decoded_data])

        for buoy in buoys:
            self._buoys_data[buoy[0]] = VikingData(*buoy)
            self.__setattr__(buoy[0], self._buoys_data[buoy[0]])

        tags = ['comp', 'triplet', 'par_digi', 'suna', 'gps', 'ctd', 'ctdo', 'rti', 'rdi',
                'wave_m', 'wave_s', 'wxt520', 'wmt700', 'wph', 'co2_w', 'co2_a', 'debit', 'vemco']

        for data_block in decoded_data:
            buoy_data = self._buoys_data[data_block['buoy_name']]

            buoy_data.time.append(data_block['time'])
            buoy_data.latitude.append(data_block['latitude_N'])
            buoy_data.longitude.append(data_block['longitude_E'])

            for tag in tags:
                tag_data = buoy_data.__dict__[tag]
                if data_block[tag] is None:
                    for key, value in tag_data.items():
                        value.append(FILL_VALUE)
                else:
                    for key, value in tag_data.items():
                        value.append(data_block[tag][key])

        viking_data: VikingData
        for viking_data in self._buoys_data.values():
            viking_data._squeeze_data()


def main():
    #m = multiple_test()
    # [(tag, [len(value) for value in m.__dict__[tag].values()]) for tag in m.tags if m.__dict__[tag] is not None]
    m = single_test()
    return m


def single_test():
    return VikingReader().read('/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat')


def multiple_test():
    return VikingReader().read('/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_[0-9]*.dat')


def _decode_transmitted_data(data_received: str, century: int = 21) -> dict:
    decoded_data = []
    tag_key = ['comp', 'triplet', 'par_digi', 'suna', 'gps', 'ctd', 'ctdo', 'rti', 'rdi',
               'wave_m', 'wave_s', 'wxt520', 'wmt700', 'wph', 'co2_w', 'co2_a', 'debit', 'vemco']
    for data_block in DATA_BLOCK_REGEX.finditer(data_received):
        wxt520 = dict()
        decoded_block = dict().fromkeys(tag_key)
        for data_sequence in DATA_TAG_REGEX.finditer(data_block.group(1)):
            tag = data_sequence.group(1)
            data = data_sequence.group(2)
            if tag == "NOM":
                decoded_block.update(_decode_NOM(data, century=century))
            elif tag == "COMP":
                decoded_block["comp"] = _decode_COMP(data)
            elif tag == "Triplet":
                decoded_block["triplet"] = _decode_Triplet(data, century=century)
            elif tag == "Par_digi":
                decoded_block["par_digi"] = _decode_Par_digi(data, century=century)
            elif tag == "SUNA":
                decoded_block['suna'] =_decode_SUNA(data)
            elif tag == "GPS":
                decoded_block["gps"] = _decode_GPS(data, century=century)
            elif tag == "CTD":
                decoded_block["ctd"] = _decode_CTD(data)
            elif tag == "CTDO":
                decoded_block["ctdo"] = _decode_CTDO(data)
            elif tag == "RTI":
                decoded_block["rti"] = _decode_RTI(data)
            elif tag == "RDI":
                decoded_block["rdi"] = _decode_RDI(data, century=century)
            elif tag == "WAVE_M":
                decoded_block["wave_m"] = _decode_WAVE_M(data)
            elif tag == "WAVE_S":
                decoded_block["wave_s"] = _decode_WAVE_S(data)
            elif tag == "WXT520":
                wxt520.update(_decode_WXT520(data))
            elif tag == "WMT700":
                decoded_block["wmt700"] = _decode_WMT700(data)
            elif tag == "WpH":
                decoded_block["wph"] = _decode_WpH(data)
            elif tag == "CO2_W":
                decoded_block["co2_w"] = _decode_CO2_W(data)
            elif tag == "CO2_A":
                decoded_block["co2_a"] = _decode_CO2_A(data)
            elif tag == "Debit":
                decoded_block["debit"] = _decode_Debit(data)

        if bool(wxt520.keys()) is True:
            decoded_block["wxt520"] = wxt520
        decoded_data.append(decoded_block)

    return decoded_data


def _decode_NOM(data: str, century: int) -> dict:
    data = data.strip('\n').split(',')
    latitude, longitude = None, None
    if "#" not in data[7]:
        _lat = data[7].split(' ')
        latitude = {'S': -1, 'N': 1}[_lat[1][-1]] * (int(_lat[0]) + round(float(_lat[1][:-1]) / 60, 2))
        _lon = data[8].split(' ')
        longitude = {'W': -1, 'E': 1}[_lon[1][-1]] * (int(_lon[0]) + round(float(_lon[1][:-1]) / 60, 2))
    return {'buoy_name': data[0].lower().replace(' ', '_').replace('-', '_'),
            'time': _make_timestamp(str(century - 1) + data[2][4:6], data[2][2:4], data[2][0:2],
                                    data[1][0:2], data[1][2:4], data[1][4:6]),
            'firmware': data[3],
            'controller_sn': data[4],
            # 'pc_data_flash': data[5],
            # 'pc_winch_flash': data[6],
            'latitude_N': latitude,
            'longitude_E': longitude}


def _decode_COMP(data: str) -> dict:
    data = data.strip('\n').split(',')
    heading = round(atan2(
        struct.unpack('>i', bytes.fromhex(data[0]))[0],
        struct.unpack('>i', bytes.fromhex(data[1]))[0]) / pi * 180, 2)
    return {'heading': heading,
            'pitch': _safe_float(data[2]),
            'roll': _safe_float(data[4]),
            'tilt': _safe_float(data[6]),
            'pitch_std': round(sqrt(_safe_float(data[3])), 2),
            'roll_std': round(sqrt(_safe_float(data[5])), 2),
            'tilt_std': round(sqrt(_safe_float(data[7])), 2)}


def _decode_Triplet(data: str, century: int) -> dict:
    data = data.strip('\n').split('\t')
    date = data[1].split('/')
    hours = data[2].split(":")
    ids = data[0].split('-')
    w_700 = tuple(map(_safe_int, [data[3], data[6], data[9]]))
    w_695 = tuple(map(_safe_float, [data[4], data[7], data[10]]))
    w_460 = tuple(map(_safe_float, [data[5], data[8], data[11]]))
    return {'time': _make_timestamp(str(century - 1) + date[2], date[0], date[1], hours[0], hours[1], hours[2]),
            'model_number': ids[0],
            'serial_number': ids[1],
            'wavelengths_700': w_700[0], 'gross_value_700': w_700[1], 'calculated_value_700': w_700[2],
            'wavelengths_695': w_695[0], 'gross_value_695': w_695[1], 'calculated_value_695': w_695[2],
            'wavelengths_460': w_460[0], 'gross_value_460': w_460[1], 'calculated_value_460': w_460[2]
            }


def _decode_Par_digi(data: str, century: int) -> dict:
    data = data.strip('\n').split(',')
    model_number, serial_number = re.match(r".*?([A-z]+)([0-9]+)", data[2]).groups()
    return {'time': _make_timestamp(str(century - 1) + data[1][4:6], data[1][2:4], data[1][0:2],
                                    data[0][0:2], data[0][2:4], data[0][4:6]),
            'model_number': model_number,
            'serial_number': serial_number,
            'timer_s': _safe_float(data[4]),
            'PAR': _safe_float(data[4]),
            'pitch': _safe_float(data[5]),
            'roll': _safe_float(data[6]),
            'intern_temperature': _safe_float(data[7]), }


def _decode_SUNA(data: str) -> dict:
    data = data.replace(' ', '').split(',')
    model_number, serial_number = re.match(r".*?([A-z]+)([0-9]+)", data[0]).groups()
    time = None
    if '#' not in data[1] + data[2]:
        time = (datetime(int(data[1][0:4]), 1, 1)
                + timedelta(days=int(data[1][4:]), hours=float(data[2]))).strftime('%y-%m-%dT%H:%M:%S')
    return {"time": time,
            "model_number": model_number,
            "serial_number": serial_number,
            "uMol": _safe_float(data[3]),
            "mgNL": _safe_float(data[4]),
            "absorbance_254_31": _safe_float(data[5]),
            "absorbance_350_16": _safe_float(data[6]),
            "bromide_mgL": _safe_float(data[7]),
            "spectrum_average": _safe_float(data[8])}


def _decode_GPS(data: str, century: int) -> dict:
    data = data.strip('\n').split(',')
    return {'time': _make_timestamp(str(century - 1) + data[8][4:6], data[8][2:4], data[8][0:2],
                                    data[0][0:2], data[0][2:4], data[0][4:6]),
            'latitude_N': {'S': -1, 'N': 1}[data[3]] * (int(data[2][:-7]) + round(float(data[2][-7:]) / 60, 2)),
            'longitude_E': {'W': -1, 'E': 1}[data[5]] * (int(data[4][:-7]) + round(float(data[4][-7:]) / 60, 2)),
            'speed': _safe_float(data[6]),
            'course': _safe_float(data[7]),
            'variation_E': {'W': -1, 'E': 1}[data[10][0]] * float(data[9]), }
    # 'checksum': _safe_int(data[8])}


def _decode_CTD(data: str) -> dict:
    """"""
    data = data.strip('\n').replace(' ', '').split(',')
    return {'temperature': _safe_float(data[0]),
            'conductivity': _safe_float(data[1]),
            'salinity': _safe_float(data[2]),
            'density': _safe_float(data[3])}


def _decode_CTDO(data: str) -> dict:
    """No test string in files."""
    data = data.strip('\n').replace(' ', '').split(',')
    return {'temperature': _safe_float(data[0]),
            'conductivity': _safe_float(data[1]),
            'oxygen': _safe_float(data[2]),
            'salinity': _safe_float(data[3])}


def _decode_RTI(data: str) -> dict:
    data = data.replace('\n', ',').split(',')
    beam_vel_mms = tuple(map(_safe_int, data[2:6]))
    enu_mms = tuple(map(_safe_int, data[6:10]))
    corr_pc = tuple(map(_safe_int, data[10:14]))
    amp_dB = tuple(map(_safe_int, data[14:18]))
    bt_beam_vel_mms = tuple(map(_safe_int, data[19:23]))
    bt_enu_mms = tuple(map(_safe_int, data[23:27]))
    bt_corr_pc = tuple(map(_safe_int, data[27:31]))
    bt_amp_dB = tuple(map(_safe_int, data[31:35]))
    return {'bin': data[0],
            'position_cm': data[1],
            'beam1': beam_vel_mms[0]/1000, 'beam2': beam_vel_mms[1]/1000,
            'beam3': beam_vel_mms[2]/1000, 'beam4': beam_vel_mms[3]/1000,
            'u': enu_mms[0]/1000, 'v': enu_mms[0]/1000, 'w': enu_mms[0]/1000, 'e': enu_mms[3]/1000,
            'corr1': corr_pc[0], 'corr2': corr_pc[1], 'corr3': corr_pc[2], 'corr4': corr_pc[3],
            'amp1': amp_dB[0], 'amp2': amp_dB[1], 'amp3': amp_dB[2], 'amp4': amp_dB[3],
            'bt_beam1': bt_beam_vel_mms[0] / 1000, 'bt_beam2': bt_beam_vel_mms[1] / 1000,
            'bt_beam3': bt_beam_vel_mms[2] / 1000, 'bt_beam4': bt_beam_vel_mms[3] / 1000,
            'bt_u': bt_enu_mms[0] / 1000, 'bt_v': bt_enu_mms[0] / 1000,
            'bt_w': bt_enu_mms[0] / 1000, 'bt_e': bt_enu_mms[3] / 1000,
            'bt_corr1': bt_corr_pc[0], 'bt_corr2': bt_corr_pc[1],
            'bt_corr3': bt_corr_pc[2], 'bt_corr4': bt_corr_pc[3],
            'bt_amp1': bt_amp_dB[0], 'bt_amp2': bt_amp_dB[1],
            'bt_amp3': bt_amp_dB[2], 'bt_amp4': bt_amp_dB[3],
            }


def _decode_RDI(data: str, century: int):
    data = data.strip('\n').split(',')
    enu_mms = tuple(struct.unpack('hhhh', bytes.fromhex(data[2])))
    return {'time': _make_timestamp(str(century - 1) + data[1][4:6], data[1][2:4],
                                    data[1][0:2], data[0][0:2], data[0][2:4], data[0][4:6]),
            'u': enu_mms[0]/1000, 'v': enu_mms[0]/1000, 'w': enu_mms[0]/1000, 'e': enu_mms[3]/1000,
            }


def _decode_WAVE_M(data: str) -> dict:
    data = data.strip('\n').split(',')
    if "#" in data[0]:
        return None
    return {'time': data[0].replace('/', '-') + 'T' + data[1],
            "period": _safe_float(data[2]),
            "average_height": _safe_float(data[3]),
            "significant_height": _safe_float(data[4]),
            "maximal_height": _safe_float(data[5])}


def _decode_WAVE_S(data: str) -> dict:
    data = data.strip('\n').split(',')
    time = data[10].replace(' ', 'T')
    return {'time': data[10].replace(' ', 'T'),
            'heading': _safe_float(data[1]),
            'average_height': _safe_float(data[2]),
            'dominant_period': _safe_float(data[3]),
            'wave_direction': _safe_float(data[4]),
            'Hmax': _safe_float(data[5]),
            'Hmax2': _safe_float(data[6]),
            'pmax': _safe_float(data[7]),
            'roll': _safe_float(data[8]),
            'pitch': _safe_float(data[9])}


def _decode_WXT520(data: str) -> dict:
    keys = ['Dn', 'Dm', 'Dx', 'Sn', 'Sm', 'Sx',
            'Rc', 'Rd', 'Ri', 'Hc', 'Hd', 'Hi',
            'Ta', 'Ua', 'Pa',
            'Th', 'Vh', 'Vs', 'Vr']
    regex = r'([A-z]+)=(\d+(?:\.\d+)?)'
    decoded_data = dict().fromkeys(keys)
    for key, value in re.findall(regex, data.strip('\n')):
        decoded_data[key] = _safe_float(value)
    return decoded_data


def _decode_WMT700(data: str) -> dict:
    keys = ['Dn', 'Dm', 'Dx', 'Sn', 'Sm', 'Sx']
    regex = r'([A-z]+)=(\d+(?:\.\d+)?)'
    decoded_data = dict().fromkeys(keys)
    for key, value in re.findall(regex, data.strip('\n')):
        decoded_data[key] = _safe_float(value)
    return decoded_data


def _decode_WpH(data: str) -> dict:
    data = data.strip('\n').split(',')
    model, serial_number = re.match(r".*?([A-z]+)([0-9]+)", data[0]).groups()
    return {'model': model,
            'serial_number': serial_number,
            'time': data[1],
            'sample_number': data[2],
            'error_flag': data[3],
            'ext_ph': _safe_float(data[4]),
            'int_ph': _safe_float(data[5]),
            # 'ext_volt': _safe_float(data[6]),
            # 'int_volt': _safe_float(data[7]),
            'ph_temperature': _safe_float(data[8]),
            'rel_humidity': _safe_float(data[9]),
            'int_temperature': _safe_float(data[10])}


def _decode_CO2_W(data: str) -> dict:
    data = data.strip('\n').split(',')
    return {"time": _make_timestamp(*data[1:7]),
            "auto-zero": _safe_int(data[7]),
            "current": _safe_int(data[8]),
            "co2_ppm": _safe_float(data[8]),
            "irga_temperature": _safe_float(data[9]),
            "humidity_mbar": _safe_float(data[10]),
            "humidity_sensor_temperature": _safe_float(data[11]),
            "cell_gas_pressure_mar": _safe_float(data[12])}


def _decode_CO2_A(data: str) -> dict:
    data = data.strip('\n').split(',')
    return {'time': _make_timestamp(*data[1:7]),
            'auto-zero': _safe_int(data[7]),
            'current': _safe_int(data[8]),
            "co2_ppm": _safe_float(data[8]),
            'irga_temperature': _safe_float(data[9]),
            'humidity_mbar': _safe_float(data[10]),
            'humidity_sensor_temperature': _safe_float(data[11]),
            "cell_gas_pressure_mar": _safe_float(data[12])}


def _decode_Debit(data: str) -> dict:
    if "#" in data:
        return {'flow_mas': None}
    else:
        return {'flow_ms': round(int(data.strip('\n'), 16) * 0.001543, 2)}


def _decode_VEMCO(data: str) -> dict:
    if "No answer" in data:
        return None
    data = data.replace('\n', '').split(',')
    return {'time': data[0].replace(' ', 'T'),
            'protocol': data[1],
            'serial_number': data[2]}

def _decode_MO(data: str) -> dict:
    return None

def _safe_float(value: str) -> Union[float, None]:
    return None if '#' in value else float(value)


def _safe_int(value: str) -> Union[int, None]:
    return None if '#' in value else int(value)


def _make_timestamp(Y: str, M: str, D: str, h: str, m: str, s: str) -> str:
    time = Y + "-" + M + "-" + D + "T" + h + ":" + m + ":" + s
    return None if "#" in time else time

# Not currenly used
# def _decode_OCR(data: str, century: int):
#    """No test string in files.
#    FIXME: NO idea if its working.
#    29,220916
#    D,32,7FF61F47,7FF96AAD,80019C5D,7FF8EEBB,7FF0B2E5,7FFB045E,7FFC0AF4,6CEF2E,5058B5,560C72,516F8D,78A870,48660F,9B89F3,7FF61F00,7FF96AC0,80019C40,7FF8EF00,7FF0B300,7FFB03C0,7FFC0A80
#    W,12,7FED43A9,7FF5BCC5,8005D91A,8015D956,7FFCD34E,7FF14B6D,7FFC38AC,29BF350,FA9F3A,9ABAD1,1B610D7,3DD6947,CF5AC95,1635C01,7FED4540,7FF5BD00,8005D900,8015D780,7FFCD6C0,7FF13EC0,7FFC3780
#
#    NOTES
#    -----
#    Bytes are missing for some value. Pad with leading zero ?
#
#    """
#    data = data.replace('\n', ',').split(',')
#    hours = data[0].rjust(6, '0')
#    time = _make_timestamp(str(century - 1) + data[1][4:6], data[1][2:4], data[1][0:2],
#                           hours[0:2], hours[2:4], hours[4:6])
#    dry_sn = data[3]
#    wet_sn = data[26]
#    dry_values = struct.unpack('>' + 21 * 'f', bytes.fromhex(''.join([v.rjust(8, '0') for v in data[4:25]])))
#    wet_values = struct.unpack('>' + 21 * 'f', bytes.fromhex(''.join([v.rjust(8, '0') for v in data[27:]])))
#
#    return {'time': time, 'dry_sn': dry_sn, 'wet_sn': wet_sn, 'dry_values': dry_values, 'wet_values': wet_values}

#    Not currently used.
# def _decode_p1(data: str):
#    """
#    [p1] 12.3, 00.0, 18.9, 00.2, 19.0, 01.5, 18.9, 01.2, 14.6, 18.6, 00.9, 01.6, 14.2, 14.0, 01.3, 14.4, 14.2, 14.1, 14.2, 05.0, 14.1,-00.0, 00.8, 0, 00.1, 00.0, 14.3, 00.1, 14.4"""
#    data = data.replace(' ', '').split(',')
#    pass
#
# def _decode_MO(data: str):
#    """[MO],D21027179068450254073423262786-31066+03454+00510##########795190660601214429000804000517537004000E3FFBB0022001400,000"""
#    84:87 Buoy Compass ture namely with comp. magnetic deflection made on board.
#    return {'buoy_compass_true': data[1][-27:-19]}
