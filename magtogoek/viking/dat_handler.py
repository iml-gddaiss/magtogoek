"""
[NOM]: Information sur la bouée
[COMP]: Orientation de la bouée
[OCR]: Radiance, Irradiance
[Triplet]: Fluorescence de l’eau de surface
[Par_digi]: PAR atmosphérique
[GPS]: Position de la bouée
[CTD]: Température, salinité et densité des eaux de surface
[CTDO]: Température, salinité et oxygène dissous des eaux de surface
[RTI] ou [RDI]: Courants à 6m sous la surface
[WAVE_M]: Vagues (senseur Multi-Électronique)
[WAVE_S]: Vagues (senseur Seaview)
[WXT520]: Conditions météorologiques
[WMT700]: Vents
[wPH]: pH de surface
[Debit]: Courant de surface mesuré par le débimètre
[p0] ou [p1]: État de l’alimentation électrique
[MO]: Combinaison de plusieurs données de la bouée (voir fichier Format string courte.pdf)
[CO2_A]: CO2 dans l’atmosphère
[CO2_W]: CO2 de l’eau de surface
[SUNA]: Concentration en nitrate dans les eaux de surface
"""

DATA_TEST = """

[NOM],PMZA-RIKI,110000,240521,8.3.1,000018C0D36B,00.3,00.0,48 39.71N,068 34.90W
[COMP],000DA1B4,FFC58202,-4.634,88.61,0.654,27.98,11.14,24.94
[Triplet],BBFL2W-1688	05/24/21	10:59:03	700	1376	2.786E-03	695	190	1.066E+00	460	85	3.454E+00
[Par_digi],110100,240521,SATPRS1093,30.415,510.646,-1.7,5.7,11.0,162
[SUNA],SATSLC1363,2021144,10.999906,16.47,0.2307,0.7115,0.9167,0.00,0.000445
[GPS],110132,A,4839.7541,N,06834.8903,W,003.7,004.4,240521,017.5,W*7B
[CTD],   7.3413,  2.45966,  23.2697, 18.1612
[RDI],110000,240521,E3FFBB0022001400
[WAVE_M],2021/05/24,10:45:00,6.61,0.60,0.48,1.29
[WXT520],Dn=163D,Dm=181D,Dx=192D,Sn=18.0K,Sm=22.7K,Sx=28.0K
[WXT520],Ta=6.8C,Ua=45.0P,Pa=1025.4H
[WXT520],Rc=0.00M,Rd=0s,Ri=0.0M,Hc=0.0M,Hd=0s,Hi=0.0M
[WXT520],Th=7.6C,Vh=14.1#,Vs=14.4V,Vr=3.503V
[WMT700],Dn=162.41D,Dm=179.40D,Dx=196.13D,Sn=14.74K,Sm=21.53K,Sx=27.46K
[WpH],SEAFET02138,2021-05-24T11:01:26,   1266, 0000,7.9519,7.9825,-0.892024,-0.938712,  7.4124,  3.4, 7.6
[Debit],00000167
[p1] 12.3, 00.0, 18.9, 00.2, 19.0, 01.5, 18.9, 01.2, 14.6, 18.6, 00.9, 01.6, 14.2, 14.0, 01.3, 14.4, 14.2, 14.1, 14.2, 05.0, 14.1,-00.0, 00.8, 0, 00.1, 00.0, 14.3, 00.1, 14.4
[VEMCO],No answer
[MO],D21027179068450254073423262786-31066+03454+00510##########795190660601214429000804000517537004000E3FFBB0022001400,000
[FIN]

"""

OCR_TEST = """[OCR],29,220916
D,32,7FF61F47,7FF96AAD,80019C5D,7FF8EEBB,7FF0B2E5,7FFB045E,7FFC0AF4,6CEF2E,5058B5,560C72,516F8D,78A870,48660F,9B89F3,7FF61F00,7FF96AC0,80019C40,7FF8EF00,7FF0B300,7FFB03C0,7FFC0A80
W,12,7FED43A9,7FF5BCC5,8005D91A,8015D956,7FFCD34E,7FF14B6D,7FFC38AC,29BF350,FA9F3A,9ABAD1,1B610D7,3DD6947,CF5AC95,1635C01,7FED4540,7FF5BD00,8005D900,8015D780,7FFCD6C0,7FF13EC0,7FFC3780"""

DATA_BLOCK_END_TAG = '[\FIN\]'

import struct
from typing import List, Tuple, Dict, Union
from math import atan2, sqrt, pi, asin, acos
import numpy as np
import re

TAGS = ["NOM", "COMP", "OCR", "Triplet","Par_digi", "[SUNA]", "GPS", "CTD", "CTDO", "RTI", "RDI", "[WAVE_M]", "[WXT520]",
        "[WXT520]", "[WXT520]", "[WXT520]", "[WMT700]", "[WpH]", "[Debit]", "[p1]", "[VEMCO]", "MO", "[FIN]"]

def main():
    #return _decode_OCR(OCR_TEST.split(','), 21)
    return decode_transmitted_data(DATA_TEST)


def decode_transmitted_data(data_received: str, century: int=21):
    """
    TODO Modified for file reading

    Parameters
    ----------
    century
    data_received

    Returns
    -------

    """

    block_start_index = 0
    block_end_index = 0
    iter_data = re.finditer(DATA_BLOCK_END_TAG, data)

    next(iter_data).span[1]


    re.split(r'(\[.*\])', data_received)
    data = [line.split(',') for line in data_received.splitlines()] #FIXME shoud split on tag
    decoded_data = dict().fromkeys(TAGS)
    for line in data:
        if line[0] == "[NOM]":
            decoded_data["NOM"] = _decode_NOM(line, century=century)
        if line[0] == "[COMP]":
            decoded_data["COMP"] = _decode_COMP(line)
        #if line[0] == "[OCR]":
        #    decoded_data["OCR"] = _decode_OCR(line, century=century)
        if line[0] == "[Triplet]":
            decoded_data["Triplet"] = _decode_Triplet(line, century=century)
        if line[0] == "[Par_digi]":
            decoded_data["Par_digi"] = _decode_Par_digi(line, century=century)
        if line[0] == "[GPS]":
            decoded_data["GPS"] = _decode_GPS(line, century=century)
        if line[0] == "[CTD]":
            decoded_data["CTD"] = _decode_CTD(line)
        if line[0] == "[CTDO]":
            decoded_data["CTDO"] = _decode_CTDO(line)
        if line[0] == "[RTI]":
            decoded_data["RTI"] = _decode_RTI(line)
        if line[0] == "[RDI]":
            decoded_data["RDI"] = _decode_RDI(line, century=century)
        if line[0] == "[MO]":
            decoded_data["MO"] = _decode_MO(line)

    return decoded_data


def _decode_NOM(data: List[str], century: int):
    """
    [NOM],PMZA-RIKI,110000,240521,8.3.1,000018C0D36B,00.3,00.0,48 39.71N,068 34.90W
    Possible 11th tag 0 or 1 for absence or presence of water in Controller case.
    """
    time = _make_timestamp(str(century - 1) + data[3][4:6], data[3][2:4], data[3][0:2],
                           data[2][0:2], data[2][2:4], data[2][4:6])
    latitude = data[8].split(' ')
    longitude = data[9].split(' ')
    latitude = {'S': -1, 'N': 1}[latitude[1][-1]] * int(latitude[0]) + round(float(latitude[1][:-1]) / 60, 2)
    longitude = {'W': -1, 'E': 1}[longitude[1][-1]] * int(longitude[0]) + round(float(longitude[1][:-1]) / 60, 2)
    water_in_case = None
    if len(data) > 10:
        water_in_case = int(data[10])

    return {'buoy_name': data[1], 'time': time,
            'firmware': data[4], 'controller_sn': data[5],
            'pc_data_flash': data[6], 'pc_winch_flash': data[7],
            'latitude_N': latitude, 'longitude_E': longitude,
            'water_in_case': water_in_case}


def _decode_COMP(data: str):
    """
    [COMP],000DA1B4,FFC58202,-4.634,88.61,0.654,27.98,11.14,24.94
    """
    heading = np.round(atan2(
        struct.unpack('>i', bytes.fromhex(data[1]))[0],
        struct.unpack('>i', bytes.fromhex(data[2]))[0]) / pi * 180, 2)
    return {'heading': heading, 'pitch':float(data[3]), 'roll': float(data[5]), 'tilt': float(data[7]),
            'pitch_std': round(sqrt(float(data[4])),2),  'roll_std': round(sqrt(float(data[6])),2),
            'tilt_std': round(sqrt(float(data[8])),2)}


def _decode_OCR(data: str, century: int):
    """No test string in files.
    FIXME: NO idea if its working.
    [OCR],29,220916
    D,32,7FF61F47,7FF96AAD,80019C5D,7FF8EEBB,7FF0B2E5,7FFB045E,7FFC0AF4,6CEF2E,5058B5,560C72,516F8D,78A870,48660F,9B89F3,7FF61F00,7FF96AC0,80019C40,7FF8EF00,7FF0B300,7FFB03C0,7FFC0A80
    W,12,7FED43A9,7FF5BCC5,8005D91A,8015D956,7FFCD34E,7FF14B6D,7FFC38AC,29BF350,FA9F3A,9ABAD1,1B610D7,3DD6947,CF5AC95,1635C01,7FED4540,7FF5BD00,8005D900,8015D780,7FFCD6C0,7FF13EC0,7FFC3780

    NOTES
    -----
    Bytes are missing for some value. Pad with leading zero ?

    """
    _data = []
    for segment in data:
        _data += segment.split('\n')
    hours = _data[1].rjust(6,'0')
    time = _make_timestamp(str(century - 1) + _data[2][4:6], _data[2][2:4], _data[2][0:2],
                           hours[0:2], hours[2:4], hours[4:6])
    dry_sn = _data[4]
    wet_sn = _data[27]
    dry_values = struct.unpack('>'+21*'f', bytes.fromhex(''.join([v.rjust(8,'0') for v in _data[5:26]])))
    wet_values =struct.unpack('>'+21*'f', bytes.fromhex(''.join([v.rjust(8,'0') for v in _data[28:]])))

    return {'time': time, 'dry_sn': dry_sn, 'wet_sn': wet_sn, 'dry_values': dry_values, 'wet_values': wet_values}


def _decode_Triplet(data: str, century: int):
    """[Triplet],BBFL2W-1688	05/24/21	10:59:03	700	1376	2.786E-03	695	190	1.066E+00	460	85	3.454E+00"""
    data = data[1].split('\t')
    date = data[1].split('/')
    hours = data[2].split(":")
    time =_make_timestamp(str(century-1)+date[2], date[0], date[1], hours[0], hours[1], hours[2])
    ids = data[0].split('-')
    return {'model_number': ids[0], 'serial_number': ids[1], 'time': time,
            'wavelengths': list(map(int, [data[3],data[6],data[9]])),
            'gross_value': list(map(float, [data[4],data[7], data[10]])),
            'calculated_value': list(map(float, [data[5],data[8],data[11]]))}


def _decode_Par_digi(data: str, century: int):
    """[Par_digi],110100,240521,SATPRS1093,30.415,510.646,-1.7,5.7,11.0, 162"""
    time = _make_timestamp(str(century - 1) + data[2][4:6], data[2][2:4], data[2][0:2],
                           data[1][0:2], data[1][2:4], data[1][4:6])
    model_number, serial_number = re.match(r"([A-z]+)([0-9]+)", data[3]).groups()
    return {'time': time, 'model_number': model_number, 'serial_number': serial_number, 'timer_s': float(data[4]),
            'PAR': float(data[5]), 'pitch':float(data[6]),'roll':float(data[7]),'intern_temperature':float(data[8]),
            'checksum':int(data[9])}


def _decode_GPS(data: str, century: int):
    """[GPS], 110132, A, 4839.7541, N, 06834.8903, W, 003.7, 004.4, 240521, 017.5, W, * 7B
    0 GPRMC:
    1 time : (utc) hhmmss.ss
    2 A/V : Position status. A = Data valid, V = Data invalid.
    3 lat : DDmm.mmmm
    4 N/S :
    5 lon : DDmm.mmmm
    6 E/W :
    7 speed : Knots, x.x
    8 true course:  x.x True degree
    9 date: ddmmyy
    10 variation, magnetic x.x
    11 E/W, mode + checksum : ((A)utonomous, (D)ifferential, (E)stimated, (M)anual input, (N) data not valid.

"""
    latitude = {'S': -1, 'N': 1}[data[4]]*int(data[3][:-7]) + round(float(data[3][-7:]) / 60, 2)
    longitude = {'W': -1, 'E': 1}[data[6]] * int(data[5][:-7]) + round(float(data[5][-7:]) / 60, 2)
    time = _make_timestamp(str(century - 1) + data[9][4:6], data[9][2:4], data[9][0:2],
                           data[1][0:2], data[1][2:4],data[1][4:6])
    variation = {'W': -1, 'E': 1}[data[11][0]] * float(data[10])
    return {'latitude_N': latitude, 'longitude': longitude,'speed': float(data[7]),
            'time': time, 'course': float(data[8]), 'variation_E': variation, 'checksum':int(data[9])}


def _decode_CTD(data: str):
    """[CTD],   7.3413,  2.45966,  23.2697, 18.1612"""

    return {'temperature': float(data[1]),'conductivity': float(data[2]), 'salinity': float(data[3]),
            'density': float(data[4])}


def _decode_CTDO(data: str):
    """No test string in files."""
    return {'temperature': float(data[1]),'conductivity': float(data[2]), 'oxygen': float(data[3]),
            'salinity': float(data[4])}


def _decode_RTI(data: str):
    """No test string in files.
    [RTI],1,407,-258,-157,-263,-32,-160,-369,-202,-30,100,100,100,100,84,83,83,84
    Bot,-3,-6,-50,56,129,101,-4,-4,100,100,100,100,76,78,78,77

    bin number, position_cm
    beam_vel, enu, corr, amp,
    """
    _data = []
    for segment in data:
        _data += segment.split('\n')

    beam_vel= list(map(int, _data[3:7]))
    enu = list(map(int, _data[7:11]))
    corr = list(map(int, _data[11:15]))
    amp = list(map(int, _data[15:19]))
    bt_beam_vel = list(map(int, _data[20:24]))
    bt_enu = list(map(int, _data[24:28]))
    bt_corr = list(map(int, _data[28:32]))
    bt_amp = list(map(int, _data[32:36]))

    return {'bin': _data[1], 'position_cm': _data[2],
            'beam_vel_mms': beam_vel, 'enu_mms': enu, 'corr_pc': corr, 'amp_dB' : amp,
            'bt_beam_vel_mms': bt_beam_vel, 'bt_enu_mms': bt_enu, 'bt_corr_pc': bt_corr, 'bt_amp_dB' : bt_amp}


def _decode_RDI(data: str, century: int):
    """[RDI],110000,240521,E3FFBB0022001400"""
    time = _make_timestamp(str(century - 1) + data[2][4:6], data[2][2:4], data[2][0:2],
                           data[1][0:2], data[1][2:4], data[1][4:6])
    return {'time': time, 'enu_mms': struct.unpack('hhhh', bytes.fromhex(data[3]))}


def _decode_WAVE_M(data: str):
    """[WAVE_M],2021/05/24,10:45:00,6.61,0.60,0.48,1.29"""
    pass


def _decode_WAVE_S(data: str):
    """No test string in files."""
    pass


def _decode_WXT520(data: str):
    """[WXT520],Dn=163D,Dm=181D,Dx=192D,Sn=18.0K,Sm=22.7K,Sx=28.0K"""
    """[WXT520],Ta=6.8C,Ua=45.0P,Pa=1025.4H"""
    """[WXT520],Rc=0.00M,Rd=0s,Ri=0.0M,Hc=0.0M,Hd=0s,Hi=0.0M"""
    """[WXT520],Th=7.6C,Vh=14.1#,Vs=14.4V,Vr=3.503V"""
    regex = r'([A-z]+)=(\d+(?:\.\d+)?)'
    match = re.findall(regex, ','.join(data))
    pass


def _decode_WXT700(data: str):
    """[WMT700],Dn=162.41D,Dm=179.40D,Dx=196.13D,Sn=14.74K,Sm=21.53K,Sx=27.46K"""
    pass


def _decode_WpH(data: str):
    """[WpH],SEAFET02138,2021-05-24T11:01:26,   1266, 0000,7.9519,7.9825,-0.892024,-0.938712,  7.4124,  3.4, 7.6"""
    pass


def _decode_CO2_W(data: str):
    """No test string in files."""
    pass


def _decode_CO2_A(data: str):
    """No test string in files."""
    pass

def _decode_Debit(data: str):
    """[Debit],00000167"""
    pass


def _decode_p1(data: str):
    """[p1] 12.3, 00.0, 18.9, 00.2, 19.0, 01.5, 18.9, 01.2, 14.6, 18.6, 00.9, 01.6, 14.2, 14.0, 01.3, 14.4, 14.2, 14.1, 14.2, 05.0, 14.1,-00.0, 00.8, 0, 00.1, 00.0, 14.3, 00.1, 14.4"""
    pass


def _decode_MO(data: str):
    """[VEMCO],No answer"""
    """[MO],D21027179068450254073423262786-31066+03454+00510##########795190660601214429000804000517537004000E3FFBB0022001400,000"""
    #84:87 Buoy Compass ture namely with comp. magnetic deflection made on board.
    return {'buoy_compass_true': data[1][-27:-19]}


def _make_timestamp(Y: str,M: str,D: str,h: str,m: str,s: str)->str:
    return Y + "-" + M + "-" + D + "T" + h + ":" + m + ":" + s

data = main()
