"""
Date April 6 2022

Made by jeromejguay

Module that contains function to load all the data into a dataset. ( I think )

Data That Need Processing
-------------------------
    WpH -> Algorithm in magtogoek/viking/tools.py


    - BODC NAMES: https://vocab.nerc.ac.uk/search_nvs/P01/

    - METEOCE BODC:

        Time                                                 : SYTM_01 : SDN:P01::
        Longitude (East +ve)                                 : LOND_01 : SDN:P01::
        Latitude (North +ve)                                 : LATD_01 : SDN:P01::
        Horizontal Wind Speed                                : WSPD_01 : SDN:P01::EWSBZZ01
        Gust Wind Speed                                      : GSPD_01 : SDN:P01::EGTSZZ01
        Wind Direction relative to North (T)                 : WDIR_01 : SDN:P01::EWDASS01
        Dry Bulb Temperature                                 : DRYT_01 : SDN:P01::CTMPZZ01
        Relative Humidity                                    : RELH_01 : SDN:P01::CRELZZ01
        Atmospheric pressure                                 : ATMP_01 : SDN:P01::CAPHZZ01
        Temperature (1990 scale)                             : TE90_01 : SDN:P01::TEMPPR01
        Electrical Conductivity                              : CNDC_01 : SDN:P01::CNDCZZ01
        Practical Salinity                                   : PSAL_01 : SDN:P01::PSLTZZ01
        Sea Density                                          : DENS_01 : SDN:P01::SIGTEQ01
        Hydrogen Ion Concentration (pH)                      : PHPH_01 : SDN:P01::PHXXZZXX
        Fluorescence                                         : FLOR_01 : SDN:P01::FLUOZZZZ
        Partial pressure of carbon dioxide in the atmosphere : ACO2_01 : SDN:P01::ACO2XXXX
        Partial pressure of carbon dioxide in the water body : PCO2_01 : SDN:P01::PCO2XXXX
        Wave mean height                                     : VRMS_01 : SDN:P01::
        Wave maximum height                                  : VMXL_01 : SDN:P01::GMXLZZ01
        Wave period                                          : VTCA_01 : SDN:P01::

    - OTHER NAMES BODC:

        wave period                         : SDN:P01::GTAMZZ01
        average wave height                 : SDN:P01::
        average wave height one third       : SDN:P01::GAVHZZ01
        average wave height dominant period : SDN:P01::
        max wave height                     : SDN:P01::GCMXZZ01
        wave direction                      : SDN:P01::
        Hmax                                : SDN:P01::
        Hmax2                               : SDN:P01::
        Pmax                                : SDN:P01::

    - DO computation:
        https://github.com/TEOS-10/python-gsw/blob/master/gsw/gibbs/conversions.py
        https://github.com/ooici/ion-functions/blob/master/ion_functions/data/do2_functions.py

    - Everything is loaded as float since nans are not available for int type in numpy


"""

import re
# import struct
# from datetime import datetime, timedelta
# from math import atan2, sqrt, pi
from typing import List, Dict, Union

from magtogoek.viking.raw_dat_reader import VikingReader, VikingData
import matplotlib
import numpy as np
import xarray as xr
import pint

from magtogoek.utils import get_files_from_expression, nans

matplotlib.use('Qt5Agg')


DAT_TAGS = ['comp', 'triplet', 'par_digi', 'suna', 'gps', 'ctd', 'ctdo', 'rti', 'rdi',
            'wave_m', 'wave_s', 'wxt520', 'wmt700', 'wph', 'co2_w', 'co2_a', 'debit', 'vemco']

VARIABLES_NAMES = {
    'comp': {
        'heading': 'heading',
        'pitch': 'pitch',
        'roll': '_roll',
        'tilt': 'tilt',
        'pitch_std': 'pitch_std',
        'roll_std': 'roll_std',
        'tilt_std': 'tilt_std'
    },
    'triplet': {
        'time': '_time',
        'fluo_calculated': 'fluo',
        'chloro_calculated': 'chloro',
        'fdom_calculated': 'fdom'
    },
    'par_digi': {
        'time': '_time',
        'timer_s': 'timer',
        'PAR': 'PAR',
        'intern_temperature': 'intern_temperature'
    },
    'suna': {
        'time': '_time',
        'nitrate': 'nitrate',
        'nitrogen': 'nitrogen',
        'absorbance_254_31': 'absorbance_254_31',
        'absorbance_350_16': 'absorbance_350_16',
        'bromide': 'bromide',
        'spectrum_average': 'spectrum_average'
    },
    'gps': {
        'time': '_time',
        'longitude_E': 'lon',
        'latitude_N': 'lat',
        'speed': 'speed',
        'course': 'course',
        'variation_E': 'magnetic_variation'
    },
    'ctd': {
        'temperature': 'temperature',
        'conductivity': 'conductivity',
        'salinity': 'salinity',
        'density': 'density'
    },
    'ctdo': {
        'temperature': 'temperature',
        'conductivity': 'conductivity',
        'salinity': 'salinity',
        'oxygen': 'oxygen'
    },
    'rti': {
        'bin': 'bin',
        'position_cm': 'position',
        'beam1': 'beam1',
        'beam2': 'beam2',
        'beam3': 'beam3',
        'beam4': 'beam4',
        'u': 'u',
        'v': 'v',
        'w': 'w',
        'e': 'e',
        'corr1': 'corr1',
        'corr2': 'corr2',
        'corr3': 'corr3',
        'corr4': 'corr4',
        'amp1': 'amp1',
        'amp2': 'amp2',
        'amp3': 'amp3',
        'amp4': 'amp4',
        'bt_beam1': 'bt_beam1',
        'bt_beam2': 'bt_beam2',
        'bt_beam3': 'bt_beam3',
        'bt_beam4': 'bt_beam4',
        'bt_u': 'bt_u',
        'bt_v': 'bt_v',
        'bt_w': 'bt_w',
        'bt_e': 'bt_e',
        'bt_corr1': 'bt_corr1',
        'bt_corr2': 'bt_corr2',
        'bt_corr3': 'bt_corr3',
        'bt_corr4': 'bt_corr4',
        'bt_amp1': 'bt_amp1',
        'bt_amp2': 'bt_amp2',
        'bt_amp3': 'bt_amp3',
        'bt_amp4': 'bt_amp4'
    },
    'rdi': {
        'time': '_time',
        'u': 'u',
        'v': 'v',
        'w': 'w',
        'e': 'e'
    },
    'wave_m': {
        'time': '_time',
        'period': 'wave_period',
        'average_height': 'wave_mean_height',
        'significant_height': 'wave_significant_height',
        'maximal_height': 'wave_maximal_height'
    },
    'wave_s': {
        'time': '_time',
        'dominant_period': 'wave_period',
        'pmax2': 'wave_period_max',
        'wave_direction': 'wave_direction',
        'average_height': 'wave_mean_height',
        'Hmax': 'wave_maximal_height',
        'Hmax2': 'wave_maximal2_height'
    },
    'wxt520': {
        'Dm': 'wind_direction',
        'Dx': 'wind_direction_max',
        'Sn': 'wind_min',
        'Sx': 'wind_max',
        'Sm': 'wind_mean',
        'Ta': 'temperature',
        'Ua': 'humidity',
        'Pa': 'pressure'
    },
    'wmt700': {
        'Dm': 'wind_direction',
        'Dx': 'wind_direction_max',
        'Sn': 'wind_min',
        'Sx': 'wind_max',
        'Sm': 'wind_mean'
    },
    'wph': {
        'time': '_time',
        'ext_ph': 'ext_ph',
        'ext_volt': 'ext_volt',
        'ph_temperature': 'temperature',
        'error_flag': 'error_flag'
    },
    'co2_w': {
        'time': '_time',
        'auto_zero': 'auto_zero',
        'current': 'current',
        'co2_ppm': 'co2',
        'irga_temperature': 'irga_temperature',
        'humidity_mbar': 'humidity',
        'humidity_sensor_temperature': 'humidity_sensor_temperature',
        'cell_gas_pressure_mbar': 'cell_gas_pressure'
    },
    'co2_a': {
        'time': '_time',
        'auto_zero': 'auto_zero',
        'current': 'current',
        'co2_ppm': 'co2',
        'irga_temperature':
        'irga_temperature',
        'humidity_mbar': 'humidity',
        'humidity_sensor_temperature': 'humidity_sensor_temperature',
        'cell_gas_pressure_mbar': 'cell_gas_pressure'
    },
    'debit': {
        'flow': 'flow'
    },
    'vemco': {
        'time': '_time',
        'protocol': 'protocol',
        'serial_number': 'serial_number'
    }
}
VARIABLES_UNITS = {
    'gps': {'speed': 'meters per second'},
    'rti': {'position': 'meters',
            'u': 'meters per second', 'v': 'meters per second', 'w': 'meters per second', 'e': 'meters per second',
            'bt_u': 'meters per second', 'bt_v': 'meters per second',
            'bt_w': 'meters per second', 'bt_e': 'meters per second'},
    'rdi': {'u': 'meters per second', 'v': 'meters per second', 'w': 'meters per second', 'e': 'meters per second'},
    'wxt': {'Sn': 'meters per second', 'Sx': 'meters per second', 'Sm': 'meters per second'},
    'wmt': {'Sn': 'meters per second', 'Sx': 'meters per second', 'Sm': 'meters per second'}
}
    #'suna': {'nitrate': {'units': 'micro mole'}, 'nitrogen': {'units': 'mgN/L'}, 'bromide': {'units': 'mg/L'}},
    #'co2_w': {'current': {'units': 'counts'}, 'co2_ppm': {'units': 'ppm'},
    #          'humidity_mbar': {'units': 'mbar'}, 'cell_gas_pressure_mbar': {'units': 'mbar'}},
    #'co2_a': {'current': {'units': 'counts'}, 'co2_ppm': {'units': 'ppm'},
    #          'humidity_mbar': {'units': 'mbar'}, 'cell_gas_pressure_mbar': {'units': 'mbar'}},
    #'debit': {'flow': {'units': 'meter per second'}}

GLOBAL_ATTRS = {'triplet': {'model_number': 'model_number', 'serial_number': 'serial_number'},
                'par_digi': {'model_number': 'model_number', 'serial_number': 'serial_number'},
                'wph': {'serial_number': 'serial_number'},
                }

meteoc_variables = {
    'lon': ('nom', 'lon'),
    'lat': ('nom', 'lat'),
    'wind_mean': [('wxt520', 'Sm'),
                  ('wmt700', 'Sm')],
    'wind_direction_mean': [('wxt520', 'Dm'),
                            ('wmt700', 'Dm')],
    'wind_max': [('wxt520', 'Sx'),
                 ('wmt700', 'Sx')],
    'wind_direction_max': [('wxt520', 'Sx'),
                           ('wmt700', 'Sx')],
    'atm_temperature': ('wxt520', 'Ta'),
    'atm_humidity': ('wxt520', 'Ua'),
    'atm_pressure': ('wxt520', 'Pa'),
    'temperature': [('ctd', 'temperature'),
                     ('ctdo', 'temperature')],
    'conductivity': [('ctd', 'conductivity'),
                     ('ctdo', 'conductivity')],
    'salinity': ('ctd', 'salinity'),
    'density': ('ctdo', 'density'),
    'ph': ('wph', "PH CORRECTION") , #COMPUTATION NEEDED
    'fluorescence': ('triplet', 'fluo'),
    'co2_a': ('co2_a', 'co2_ppm'), # COMPUTATION NEEDED
    'co2_w': ('co2_w', 'co2_ppm'), # COMPUTATION NEEDED,
    'wave_mean_height': [('wave_m', 'averaged_height'),
                        ('wave_s', 'averaged_height')],
    'wave_maximal_height': [('wave_m', 'maximal_height'),
                       ('wave_s', 'Hmax')],
    'wave_period': [('wave_m', 'period'),
                    ('wave_s', 'dominant_period')],
}


def load_viking_dat(viking_data: VikingData) -> xr.Dataset:
    """
    Deals with duplicate Time in NOM.

    Notes
    -----
    WXT only output Th, Vh, Vs, Vr data and I have no Idea what they are.
    """
    datasets = {}

    nom_coords = {'time': np.asarray(viking_data.time)}
    nom_data = {'lon': (['time'], viking_data.longitude.filled(np.nan)),
                'lat': (['time'], viking_data.latitude.filled(np.nan))}
    datasets['nom'] = xr.Dataset(
        nom_data,
        coords=nom_coords,
        attrs={'firmware': viking_data.firmware, 'controller_sn': viking_data.controller_sn}).dropna('time')

    for tag in VARIABLES_NAMES.keys():
        if viking_data.__dict__[tag] is not None:
            datasets[tag] = _load_tag_data_to_dataset(tag, tag_data=viking_data.__dict__[tag], coords=nom_coords)

    for key in datasets.keys():
        datasets[key] = _average_duplicates(datasets[key], 'time')

    return datasets


def _load_tag_data_to_dataset(tag: str, tag_data: dict, coords: dict) -> xr.Dataset:
    data_vars = {}
    vars_units = VARIABLES_UNITS[tag] if tag in VARIABLES_UNITS else {}
    for var, name in VARIABLES_NAMES[tag].items():
        values = tag_data[var]

        units = vars_units[var] if var in vars_units else None
        if isinstance(values, pint.Quantity) and units is not None:
            values = values.to(units)
        if var == 'time':
            data_vars[name] = (['time'], values.filled(np.datetime64('NaT')).astype('datetime64[s]'))
        elif np.issubdtype(values.dtype, str):
            data_vars[name] = (['time'], values.filled("NA"))
        else:
            data_vars[name] = (['time'], values.filled(np.nan))

    _global_attrs = {}
    if tag in GLOBAL_ATTRS:
        for var, name in GLOBAL_ATTRS[tag].items():
            index = np.where(tag_data[var].mask == False)[0]
            _global_attrs[name] = str(tag_data[var].data[index][0])

    return xr.Dataset(data_vars, coords=coords, attrs=_global_attrs)


def _average_duplicates(dataset: xr.Dataset, coord: str) -> xr.Dataset:
    """Average data_array values of duplicates time coords index.
    """

    df = dataset.to_dataframe()
    df = df.groupby(coord).mean(numeric_only=False)

    _dataset = dataset[{coord: np.unique(dataset[coord], return_index=True)[1]}]
    for var in _dataset.keys():
        _dataset[var].values[:] = df[var][:]

    return _dataset


if __name__ == "__main__":
    import matplotlib.pyplot as plt


    def find_duplicates(array: np.ndarray):
        index = np.where(array[:-1] == array[1:])[0]
        return sorted(list(set(list(index) + list(index + 1))))


    # viking_data = main()
    vr = VikingReader().read('/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat')

    viking_data = vr._buoys_data['pmza_riki']

    datasets = load_viking_dat(viking_data)
