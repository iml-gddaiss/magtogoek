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
[OCR],----------------------------------------------------------------
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
from typing import List, Tuple, Dict

TAGS = ["NOM", "COMP", "[Triplet]"," [Par_digi]", "[SUNA]", "[GPS]", "[CTD]", "[RDI]", "[WAVE_M]", "[WXT520]",
        "[WXT520]", "[WXT520]", "[WXT520]", "[WMT700]", "[WpH]", "[Debit]", "[p1]", "[VEMCO]", "[MO]", "[FIN]"]


def main():
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
    data = [line.split(',') for line in data_received.splitlines()]
    decoded_data = dict().fromkeys(TAGS)
    for line in data:
        if line[0] == "[NOM]":
            decoded_data["NOM"] = _decode_NOM(line, century=century)
        if line[0] == "[COMP]":
            decoded_data["COMP"] = _decode_COMP(line)

    return decoded_data


def _decode_NOM(data: List[str], century: int):
    """
    [NOM],PMZA-RIKI,110000,240521,8.3.1,000018C0D36B,00.3,00.0,48 39.71N,068 34.90W
    Possible 11th tag 0 or 1 for absence or presence of water in Controller case.
    """


    time = str(century - 1) + data[3][4:6] + "-" + data[3][2:4] + "-" + data[3][0:2] \
                  + "T" + data[2][0:2] + ":" + data[2][2:4] + ":" + data[2][4:6]
    latitude = data[8].split(' ')
    longitude = data[9].split(' ')
    latitude = {'S': -1, 'N': 1}[latitude[1][-1]] * int(latitude[0]) + round(float(latitude[1][:-1]) / 60, 4)
    longitude = {'W': -1, 'E': 1}[longitude[1][-1]] * int(longitude[0]) + round(float(longitude[1][:-1]) / 60, 4)
    water_in_case = None
    if len(data) > 10:
        water_in_case = int(data[10])

    return {'buoy_name': data[1], 'time': time,
           'firmware': data[4], 'controller_sn': data[5],
           'pc_data_flash': data[6], 'pc_winch_flash': data[7],
           'latitude': latitude, 'longitude': longitude,
            'water_in_case': water_in_case}


def _decode_COMP(data: str):
    """ 000DA1B4,FFC58202 -> 167
    -4.634,88.61,0.654,27.98,11.14,24.94 -> -4.6, 9.4, 0.7, 5.3, 11.1, 5.0
    averaged of the reading ?"""
    return {'tot_sin_head': int(data[1], 16), 'tot_cos_head':int(data[2],16), 'averaged_pitch':float(data[3]),
            'std_pitch':float(data[4]), 'averaged_roll':float(data[5]), 'std_roll':float(data[6]),
            'averaged_tilt':float(data[7]), 'std_tilt':float(data[8])}


def _decode_OCR(data: str):
    pass


def _decode_Triplet(data: str):
    pass


def _decode_Par_digi(data: str):
    pass


def _decode_GPS(data: str):
    pass


def _decode_CTD(data: str):
    pass


def _decode_CTDO(data: str):
    pass


def _decode_RTI(data: str):
    pass


def _decode_WAVE_M(data: str):
    pass


def _decode_WAVE_S(data: str):
    pass


def _decode_WXT520(data: str):
    pass


def _decode_WXT700(data: str):
    pass


def _decode_WpH(data: str):
    pass


def _decode_CO2_W(data: str):
    pass


def _decode_CO2_A(data: str):
    pass


def _decode_Debit(data: str):
    pass


def _decode_p1(data: str):
    pass


def _decode_MO(data: str):
    pass


def _decode_W(data: str):
    pass


data = main()
