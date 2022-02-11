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


For WXT520 and WMT700
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

"""

import struct
from typing import List, Tuple, Dict, Union
from math import atan2, sqrt, pi
from datetime import datetime, timedelta
import re

DATA_TEST = """


[NOM],PMZA-RIKI,110000,240521,8.3.1,000018C0D36B,00.3,00.0,48 39.71N,068 34.90W
[COMP],000DA1B4,FFC58202,-4.634,88.61,0.654,27.98,11.14,24.94
[Triplet],BBFL2W-1688	05/24/21	10:59:03	700	1376	2.786E-03	695	190	1.066E+00	460	85	3.454E+00
[Par_digi],110100,240521,SATPRS1093,30.415,510.646,-1.7,5.7,11.0,162
[SUNA],SATSLC1363,2021144,10.999906,16.47,0.2307,0.7115,0.9167,0.00,0.000445
[GPS],110132,A,4839.7541,N,06834.8903,W,003.7,004.4,240521,017.5,W*7B
[CTD],   7.3413,  2.45966,  23.2697, 18.1612
[RTI],1,407,-258,-157,-263,-32,-160,-369,-202,-30,100,100,100,100,84,83,83,84
Bot,-3,-6,-50,56,129,101,-4,-4,100,100,100,100,76,78,78,77 
[RDI],110000,240521,E3FFBB0022001400
[WAVE_M],2021/05/24,10:45:00,6.61,0.60,0.48,1.29
[WAVE_S],$PSVSW,165.15,0.251,8.041,72.285,3.376,0.319,2.272,0.438,2.250,2017-02-24,20:52:15,90*71
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

[NOM],PMZA-RIKI,120000,250521,8.3.2,000018C0D36B,00.3,00.0,48 40.20N,068 34.66W
[COMP],002588EA,002DCE47,-4.585,47.86,1.417,16.51,8.561,22.66
[Triplet],BBFL2W-1688	05/25/21	11:59:03	700	797	1.573E-03	695	432	2.832E+00	460	80	3.000E+00
[Par_digi],120100,250521,SATPRS1093,30.415,428.540,-12.9,1.8,11.1,111
[SUNA],SATSLC1363,2021145,12.000192,7.63,0.1068,0.2978,0.2471,0.00,0.000160
[GPS],120134,A,4840.2018,N,06834.6630,W,002.0,148.3,250521,017.5,W*74
[CTD],   8.3489,  2.77301,  25.7928, 20.0126
[RDI],120000,250521,55029601F1FFF5FF
[WAVE_M],2021/05/25,11:45:00,3.68,1.33,1.22,1.86
[WXT520],Dn=174D,Dm=184D,Dx=194D,Sn=30.7K,Sm=40.2K,Sx=47.3K
[WXT520],Ta=9.8C,Ua=66.5P,Pa=1010.4H
[WXT520],Th=9.6C,Vh=12.6#,Vs=12.9V,Vr=3.503V
[WMT700],Dn=157.92D,Dm=187.84D,Dx=204.67D,Sn=25.92K,Sm=35.70K,Sx=64.71K
[WpH],SEAFET02138,2021-05-25T12:01:27,   1313, 0000,8.0198,7.9583,-0.887574,-0.939757,  8.2520,  3.5, 8.4
[CO2_W],W M,2021,05,25,11,51,24,55544,52106,448.94,40.00,10.70,13.40,1000,12.3
[CO2_A],A M,2021,05,25,11,53,24,55544,51944,453.14,40.00,10.30,13.90,1036,14.8
[Debit],00000154
[p1] 09.8, 00.0, 16.9, 00.2, 16.9, 00.2, 16.9, 00.3, 13.7, 16.6,-00.5, 00.3, 13.8, 13.4, 01.3, 13.5, 13.8, 13.3, 13.3, 05.0, 13.8, 00.8, 00.9, 0, 00.1, 00.0, 13.4, 00.1, 13.5
[VEMCO],No answer
[MO],D35064187098660104083425791573-32832+03000+004280448904531801980361301813507080904010501820148###55029601F1FFF5FF,000,[W]22>Error ! Motor Stopped But Drum Running
[FIN]
"""

OCR_TEST = """[OCR],29,220916
D,32,7FF61F47,7FF96AAD,80019C5D,7FF8EEBB,7FF0B2E5,7FFB045E,7FFC0AF4,6CEF2E,5058B5,560C72,516F8D,78A870,48660F,9B89F3,7FF61F00,7FF96AC0,80019C40,7FF8EF00,7FF0B300,7FFB03C0,7FFC0A80
W,12,7FED43A9,7FF5BCC5,8005D91A,8015D956,7FFCD34E,7FF14B6D,7FFC38AC,29BF350,FA9F3A,9ABAD1,1B610D7,3DD6947,CF5AC95,1635C01,7FED4540,7FF5BD00,8005D900,8015D780,7FFCD6C0,7FF13EC0,7FFC3780"""

TAGS = ["NOM", "COMP", "OCR", "Triplet", "Par_digi", "SUNA", "GPS", "CTD", "CTDO", "RTI", "RDI", "WAVE_M", "WXT520",
        "WMT700", "WpH", "Debit", "p1", "VEMCO", "MO", "FIN"]
DATA_BLOCK_REGEX = re.compile(r"(\[NOM].+?)\[FIN]", re.DOTALL)
DATA_TAG_REGEX = re.compile(rf"\[({'|'.join(TAGS)})],?((?:(?!\[).)*)", re.DOTALL)


def main():
    return decode_transmitted_data(DATA_TEST)


def decode_transmitted_data(data_received: str, century: int = 21):
    """
    TODO Modified for file reading

    Parameters
    ----------
    century
    data_received

    Returns
    -------

    """

    decoded_data = dict().fromkeys(TAGS)
    decoded_data['WXT520'] = dict()
    for data_block in DATA_BLOCK_REGEX.finditer(data_received):
        for data_sequence in DATA_TAG_REGEX.finditer(data_block.group(1)):
            tag = data_sequence.group(1)
            data = data_sequence.group(2)
            if tag == "NOM":
                decoded_data["NOM"] = _decode_NOM(data, century=century)
            elif tag == "COMP":
                decoded_data["COMP"] = _decode_COMP(data)
            elif tag == "Triplet":
                decoded_data["Triplet"] = _decode_Triplet(data, century=century)
            elif tag == "Par_digi":
                decoded_data["Par_digi"] = _decode_Par_digi(data, century=century)
            elif tag == "GPS":
                decoded_data["GPS"] = _decode_GPS(data, century=century)
            elif tag == "CTD":
                decoded_data["CTD"] = _decode_CTD(data)
            elif tag == "CTDO":
                decoded_data["CTDO"] = _decode_CTDO(data)
            elif tag == "RTI":
                decoded_data["RTI"] = _decode_RTI(data)
            elif tag == "RDI":
                decoded_data["RDI"] = _decode_RDI(data, century=century)
            elif tag == "WAVE_M":
                decoded_data["WAVE_M"] = _decode_WAVE_M(data)
            elif tag == "WAVE_S":
                decoded_data["WAVE_S"] = _decode_WAVE_M(data)
            elif tag == "WXT520":
                decoded_data["WXT520"] = {**decoded_data["WXT520"], **_decode_WXT520(data)}
            elif tag == "WMT700":
                decoded_data["WMT700"] = _decode_WMT700(data)

    return decoded_data


def _decode_NOM(data: str, century: int):
    """
    PMZA-RIKI,110000,240521,8.3.1,000018C0D36B,00.3,00.0,48 39.71N,068 34.90W

    Possible 11th tag 0 or 1 for absence or presence of water in Controller case.
    """
    data = data.strip('\n').split(',')
    time = _make_timestamp(str(century - 1) + data[2][4:6], data[2][2:4], data[2][0:2],
                           data[1][0:2], data[1][2:4], data[1][4:6])
    latitude = data[7].split(' ')
    longitude = data[8].split(' ')
    latitude = {'S': -1, 'N': 1}[latitude[1][-1]] * (int(latitude[0]) + round(float(latitude[1][:-1]) / 60, 2))
    longitude = {'W': -1, 'E': 1}[longitude[1][-1]] * (int(longitude[0]) + round(float(longitude[1][:-1]) / 60, 2))
    water_in_case = None
    if len(data) > 9:
        water_in_case = int(data[9])

    return {'buoy_name': data[0], 'time': time,
            'firmware': data[3], 'controller_sn': data[4],
            'pc_data_flash': data[5], 'pc_winch_flash': data[6],
            'latitude_N': latitude, 'longitude_E': longitude,
            'water_in_case': water_in_case}


def _decode_COMP(data: str):
    """
    000DA1B4,FFC58202,-4.634,88.61,0.654,27.98,11.14,24.94
    TODO return cos and sin and do atan2 on the entire array ?
    """
    data = data.strip('\n').split(',')
    heading = round(atan2(
        struct.unpack('>i', bytes.fromhex(data[0]))[0],
        struct.unpack('>i', bytes.fromhex(data[1]))[0]) / pi * 180, 2)
    return {'heading': heading, 'pitch': float(data[2]), 'roll': float(data[4]), 'tilt': float(data[6]),
            'pitch_std': round(sqrt(float(data[3])), 2), 'roll_std': round(sqrt(float(data[5])), 2),
            'tilt_std': round(sqrt(float(data[7])), 2)}


# Not currenly used
#def _decode_OCR(data: str, century: int):
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


def _decode_Triplet(data: str, century: int):
    """BBFL2W-1688	05/24/21	10:59:03	700	1376	2.786E-03	695	190	1.066E+00	460	85	3.454E+00"""
    data = data.strip('\n').split('\t')
    date = data[1].split('/')
    hours = data[2].split(":")
    time = _make_timestamp(str(century - 1) + date[2], date[0], date[1], hours[0], hours[1], hours[2])
    ids = data[0].split('-')
    return {'model_number': ids[0], 'serial_number': ids[1], 'time': time,
            'wavelengths': list(map(int, [data[3], data[6], data[9]])),
            'gross_value': list(map(float, [data[4], data[7], data[10]])),
            'calculated_value': list(map(float, [data[5], data[8], data[11]]))}


def _decode_Par_digi(data: str, century: int):
    """110100,240521,SATPRS1093,30.415,510.646,-1.7,5.7,11.0,162"""
    data = data.strip('\n').split(',')
    time = _make_timestamp(str(century - 1) + data[1][4:6], data[1][2:4], data[1][0:2],
                           data[0][0:2], data[0][2:4], data[0][4:6])
    model_number, serial_number = re.match(r"([A-z]+)([0-9]+)", data[2]).groups()
    return {'time': time, 'model_number': model_number, 'serial_number': serial_number, 'timer_s': float(data[4]),
            'PAR': float(data[4]), 'pitch': float(data[5]), 'roll': float(data[6]),
            'intern_temperature': float(data[7]),
            'checksum': int(data[8])}


def _decode_SUNA(data: str):
    """                             D,     E,     M,     N,
                                 uMol,mg N/L,254.31,350.16,
    SATSLC1363,2021145,12.000192,7.63,0.1068,0.2978,0.2471,0.00,0.000160
     """
    data=data.replace(' ', '').split(',')
    model_number, serial_number = re.match(r"([A-z]+)([0-9]+)", data[0]).groups()
    datetime(2021, 1, 1) + timedelta(days=145)

    return {"umol": None, "mgL": None, "absorbance_254_31": None, "absorbance_350_16": None}


def _decode_GPS(data: str, century: int):
    """110132,A,4839.7541,N,06834.8903,W,003.7,004.4,240521,017.5,W,*7B
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
    data = data.strip('\n').split(',')
    latitude = {'S': -1, 'N': 1}[data[3]] * (int(data[2][:-7]) + round(float(data[2][-7:]) / 60, 2))
    longitude = {'W': -1, 'E': 1}[data[5]] * (int(data[4][:-7]) + round(float(data[4][-7:]) / 60, 2))
    time = _make_timestamp(str(century - 1) + data[8][4:6], data[8][2:4], data[8][0:2],
                           data[0][0:2], data[0][2:4], data[0][4:6])
    variation = {'W': -1, 'E': 1}[data[10][0]] * float(data[9])
    return {'latitude_N': latitude, 'longitude': longitude, 'speed': float(data[6]),
            'time': time, 'course': float(data[7]), 'variation_E': variation, 'checksum': int(data[8])}


def _decode_CTD(data: str):
    """   7.3413,  2.45966,  23.2697, 18.1612"""
    data = data.strip('\n').replace(' ', '').split(',')
    return {'temperature': float(data[0]), 'conductivity': float(data[1]), 'salinity': float(data[2]),
            'density': float(data[3])}


def _decode_CTDO(data: str):
    """No test string in files."""
    data = data.strip('\n').replace(' ', '').split(',')
    return {'temperature': float(data[0]), 'conductivity': float(data[1]), 'oxygen': float(data[2]),
            'salinity': float(data[3])}


def _decode_RTI(data: str):
    """No test string in files.
    1,407,-258,-157,-263,-32,-160,-369,-202,-30,100,100,100,100,84,83,83,84
    Bot,-3,-6,-50,56,129,101,-4,-4,100,100,100,100,76,78,78,77

    bin number, position_cm, 4-beam_vel, 4-enu, 4-corr, 4-amp, ... 16 more for bt.
    """
    data = data.replace('\n', ',').split(',')
    beam_vel = list(map(int, data[2:6]))
    enu = list(map(int, data[6:10]))
    corr = list(map(int, data[10:14]))
    amp = list(map(int, data[14:18]))
    bt_beam_vel = list(map(int, data[19:23]))
    bt_enu = list(map(int, data[23:27]))
    bt_corr = list(map(int, data[27:31]))
    bt_amp = list(map(int, data[31:35]))

    return {'bin': data[0], 'position_cm': data[1],
            'beam_vel_mms': beam_vel, 'enu_mms': enu, 'corr_pc': corr, 'amp_dB': amp,
            'bt_beam_vel_mms': bt_beam_vel, 'bt_enu_mms': bt_enu, 'bt_corr_pc': bt_corr, 'bt_amp_dB': bt_amp}


def _decode_RDI(data: str, century: int):
    data = data.strip('\n').split(',')
    """110000,240521,E3FFBB0022001400"""
    time = _make_timestamp(str(century - 1) + data[1][4:6], data[1][2:4], data[1][0:2],
                           data[0][0:2], data[0][2:4], data[0][4:6])
    return {'time': time, 'enu_mms': list(struct.unpack('hhhh', bytes.fromhex(data[2])))}


def _decode_WAVE_M(data: str):
    """2021/05/24,10:45:00,6.61,0.60,0.48,1.29
    FIXME THE 5 ELEMENTS IS NOT MENTIONED IN THE DESCRIPTION Will guess period, averaged, min, max
    """
    data = data.strip('\n').split(',')
    time = data[0].replace('/', '-')+'T'+data[1]
    return {'time': time, "period": float(data[2]), "averaged_height": float(data[3]), "minimal_height": float(data[4]), "maximal_height": float(data[5])}


def _decode_WAVE_S(data: str):
    """Test string for documentations
    $PSVSW,165.15,0.251,8.041,72.285,3.376,0.319,2.272,0.438,2.250,2017-02-24,20:52:15,90*71"""
    data = data.strip('\n').split(',')
    time = data[11]+'T'+data[12]
    return {'time':time ,'heading': float(data[1]), 'direction': float(data[2]), 'average': float(data[3]),
            'height': float(data[4]), 'period': float(data[5]), 'maximal_height': float(data[6]),
            'maximal_height_2': float(data[7]), 'Pmax': float(data[8]), 'roll': float(data[9]),
            'pitch': float(data[10]), 'index_checksum': data[13]}


def _decode_WXT520(data: str):
    """Dn=163D,Dm=181D,Dx=192D,Sn=18.0K,Sm=22.7K,Sx=28.0K
    Ta=6.8C,Ua=45.0P,Pa=1025.4H
    Rc=0.00M,Rd=0s,Ri=0.0M,Hc=0.0M,Hd=0s,Hi=0.0M
    Th=7.6C,Vh=14.1#,Vs=14.4V,Vr=3.503V

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
    Pa = atmospheric pressure."""
    regex = r'([A-z]+)=(\d+(?:\.\d+)?)'
    return {key: float(value) for key, value in re.findall(regex, data.strip('\n'))}


def _decode_WMT700(data: str):
    """Dn=162.41D,Dm=179.40D,Dx=196.13D,Sn=14.74K,Sm=21.53K,Sx=27.46K

    Dn = minimal wind direction
    Dm = average wind direction
    Dx = maximal wind direction
    Sn = minimal wind strength
    Sm = average wind strength
    Sx = maximal wind strength
    """
    regex = r'([A-z]+)=(\d+(?:\.\d+)?)'
    return {key: float(value) for key, value in re.findall(regex, data.strip('\n'))}


def _decode_WpH(data: str):
    """SEAFET02138,2021-05-24T11:01:26,1266,0000,7.9519,7.9825,-0.892024,-0.938712,7.4124,3.4,7.6
    sample_number, error_flag, PH_ext, PH_int, ph_ext_volt, ph_ext_volt, pH_temperature, relative_humidity, internal_temperature
    """
    data = data.strip('\n').split(',')
    model, serial_number = re.match(r"([A-z]+)([0-9]+)", data[0]).groups()
    return {'model': model, 'serial_number': serial_number, 'time': data[1], 'sample_number':data[2],
            'error_flag': data[3], 'ext_ph': float(data[4]), 'int_ph': float(data[5]), 'ext_volt': float(data[6]),
            'int_volt': float(data[7]), 'ph_temperature': float(data[8]), 'rel_humidity': float(data[9]),
            'int_temperature': float(data[10])}


def _decode_CO2_W(data: str):
    """No test string in files. (A / D : analogue device ?. unist-> counts)
    Measurement type,Year,Month,Day,Hour,Minute,Second,Zero A/D,Current A/D,
    CO2_ppm,IRGA temperature,Humidity_mbar,Humidity sensor temperature,Cell gas pressure_mbar,Battery voltage

    W M,2021,05,25,11,51,24,55544,52106,448.94,40.00,10.70,13.40,1000,12.3"""

    data = data.split(',')

    return{'time':_make_timestamp(*data[1:7]), 'auto-zero': int(data[7]), 'current': int(data[8]),
           "co2_ppm": float(data[8]), 'irga_temperature': float(data[9]), 'humidity_mbar': float(data[10]),
           'humidity_sensor_temperature' : float(data[11]), "cell_gas_pressure_mar": float(data[12]),
           "battery_volt": float(data[12])}


def _decode_CO2_A(data: str):
    """No test string in files.
    A M,2021,05,25,11,53,24,55544,51944,453.14,40.00,10.30,13.90,1036,14.8"""
    return {'time': _make_timestamp(*data[1:7]), 'auto-zero': int(data[7]), 'current': int(data[8]),
            "co2_ppm": float(data[8]), 'irga_temperature': float(data[9]), 'humidity_mbar': float(data[10]),
            'humidity_sensor_temperature': float(data[11]), "cell_gas_pressure_mar": float(data[12]),
            "battery_volt": float(data[12])}


def _decode_Debit(data: str):
    """00000167
    20_000 Pulse = 1 nautical miles. Number of pulse during 60 seconds.
    """
    return {'flow_ms': (int(data)/2e4)*1852/60}


#    Not currently used.
#def _decode_p1(data: str):
#    """
#    [p1] 12.3, 00.0, 18.9, 00.2, 19.0, 01.5, 18.9, 01.2, 14.6, 18.6, 00.9, 01.6, 14.2, 14.0, 01.3, 14.4, 14.2, 14.1, 14.2, 05.0, 14.1,-00.0, 00.8, 0, 00.1, 00.0, 14.3, 00.1, 14.4"""
#    data = data.replace(' ', '').split(',')
#    pass
#
#def _decode_MO(data: str):
#    """[MO],D21027179068450254073423262786-31066+03454+00510##########795190660601214429000804000517537004000E3FFBB0022001400,000"""
#    84:87 Buoy Compass ture namely with comp. magnetic deflection made on board.
#    return {'buoy_compass_true': data[1][-27:-19]}


def _make_timestamp(Y: str, M: str, D: str, h: str, m: str, s: str) -> str:
    return Y + "-" + M + "-" + D + "T" + h + ":" + m + ":" + s


data = main()
