"""
Tag String Structure

InitTagString = [INIT]Buoy_Name,Date,Time,Latitude,Longitude,Heading,Pitch,Roll,COG,SOG,Magnetic_Variation,Water_Detection_Main
PowerTagString = [POWR]VBatt1,ABatt1,VBatt2,ABatt2,VSolar,ASolar,AMain,ATurbine,AWinch,PM_RH,Relay_State
Echo-Triplet: [TRP1]Scattering,Chlorophyll,FDOM
SBE37TagString = [CTD]Temperature,Conductivity,Salinity,Density
PHTagString = [PH]Ext_pH_Calc,Int_pH_Calc,Error_Flag,Ext_pH,Int_pH
SunaTAGString = [SUNA]Dark_Nitrate,Light_Nitrate,Dark_Nitrogen_in_Nitrate,Light_Nitrogen_in_Nitrate,Dark_Bromide,Light_Bromide
WindTagString = [WindTAG]  Wind_Dir_Min,Wind_Dir_Ave,Wind_Dir_Max,Wind_Spd_Min,Wind_Spd_Ave,Wind_Spd_Max
ATMSTagString = [ATMS]Air_Temp,Air_Humidity,Air_Pressure,PAR,Rain_Total,Rain_Duration,Rain_Intensity
WaveTagString = [WAVE]Wave_Date,Wave_Time,Wave_Period,Wave_Hm0,Wave_H13,Wave_Hmax
ADCPTagString = [RDI]ADCPDate,ADCPTime,EW,NS,Vert,Err
PCO2TagString = [PCO2]PCO2A_CO2,PCO2W_CO2,PCO2W_Gaz_Pressure,PCO2A_Gaz_Pressure,PCO2A_Humidity
WinchTagString = [WNCH]messages
    messages:
        Air temperature is too low
        Waves are too high
        Wave period is too short
        Buoy is moving too fast
        Voltage is too low
        Mission Completed
        No Mission in Progress
        Mission in Progress
        Mission Started
        No String received from CTD
        Interval not reach
EndTagString = "[END]"

Max String Length:

    WNCH : 36
"""

import os
import re
from typing import Dict, List
from pathlib import Path


# Tag found in transmitted file.
INSTRUMENTS_TAG = ['INIT', 'POWR', 'TRP1', 'CTD', 'PH', 'SUNA', 'W536', 'W700', 'ATMS', 'WAVE', 'RDI', 'PCO2', 'WNCH']

DATA_TAG_REGEX = re.compile(rf"\[({'|'.join(INSTRUMENTS_TAG)})]((?:(?!\[).)*)", re.DOTALL)

WIND_TAG = 'xxxx' #FIXME

TAG_VARIABLES = {
    'init': ['buoy_name', 'date', 'time', 'latitude', 'longitude', 'heading', 'pitch', 'roll', 'cog', 'sog', 'magnetic_declination', 'water_detection'],
    'powr': ['volt_batt_1', 'amp_batt_1', 'volt_batt_2', 'amp_batt_2', 'volt_solar', 'amp_solar', 'amp_main', 'amp_turbine', 'amp_winch', 'pm_rh', 'relay_state'],
    'trp1': ['scattering', 'chlorophyll', 'fdom'],
    'ctd': ['temperature', 'conductivity', 'salinity', 'density'],
    'ph': ['ext_ph_calc', 'int_ph_calc', 'error_flag', 'ext_ph', 'int_ph'],
    'suna': ['dark_nitrate', 'light_nitrate', 'dark_nitrogen_in_nitrate', 'light_nitrogen_in_nitrate', 'dark_bromide', 'light_bromide'],
    'w700': ['wind_dir_min', 'wind_dir_ave', 'wind_dir_max', 'wind_spd_min', 'wind_spd_ave', 'wind_spd_max'],
    'w536': ['wind_dir_min', 'wind_dir_ave', 'wind_dir_max', 'wind_spd_min', 'wind_spd_ave', 'wind_spd_max'],
    'atms': ['air_temperature', 'air_humidity', 'air_pressure', 'par', 'rain_total', 'rain_duration', 'rain_intensity'],
    'wave': ['date', 'time', 'period', 'hm0', 'h13', 'hmax'],
    'rdi': ['date', 'time', 'u', 'v', 'w', 'err'],
    'pco2': ['air_co2', 'water_co2', 'water_gaz_pressure', 'air_gaz_pressure', 'air_humidity'],
    'wnch': ['message']
}


def _unpack_data(data: str) -> list:
    """Returns Data as a dictionary of {TAG:DATA}"""

    unpacked_data = {}
    for data_sequence in DATA_TAG_REGEX.finditer(data):
        tag = data_sequence.group(1).lower()
        data = data_sequence.group(2).split(",")

        unpacked_data[tag] = {key: value for key, value in zip(TAG_VARIABLES[tag], data)}

    return unpacked_data