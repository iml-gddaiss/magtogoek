"""
DateL April 6 2022
Made by jeromejguay
This script is used to decode the data send by Viking as of February 2022 format version.

Data That Need Processing
-------------------------
    WpH -> Algorithm in magtogoek/viking/tools.py


    - BODC NAMES: https://vocab.nerc.ac.uk/search_nvs/P01/

    - METEOCE BODC:

      meteoc_variables = ['lon', 'lat',
                          'wind_mean', 'wind_direction_mean', 'wind_max', 'wind_direction_max',
                          'atm_temperature', 'atm_humidity', 'atm_pressure',
                          'temperature', 'conductivity', 'salinity', 'density',
                          'ph', 'fluorescence', 'co2_a', 'co2_w',
                          'averaged_height', 'maximal_height', 'wave_period']

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
        Partial pressure of carbon dioxide in the water boby : PCO2_01 : SDN:P01::PCO2XXXX
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
#import struct
#from datetime import datetime, timedelta
#from math import atan2, sqrt, pi
from typing import List, Dict, Union

from magtogoek.viking.raw_dat_reader import VikingReader, VikingData
import matplotlib
import numpy as np
import xarray as xr

from magtogoek.utils import get_files_from_expression, nans

matplotlib.use('Qt5Agg')

#FILL_VALUE = -32768  # Reusing the same fill value as teledyne (RDI) -(2**15)

KNOTS_PER_METER_S = 1.94384  # knots per meter/per

DAT_TAGS =['comp', 'triplet', 'par_digi', 'suna', 'gps', 'ctd', 'ctdo', 'rti', 'rdi',
           'wave_m', 'wave_s', 'wxt520', 'wmt700', 'wph', 'co2_w', 'co2_a', 'debit', 'vemco']

variables_names = {
    'comp': {'heading': 'heading', 'pitch': 'pitch', 'roll': '_roll', 'tilt': 'tilt',
             'pitch_std': 'pitch_std', 'roll_std': 'roll_std', 'tilt_std': 'tilt_std'},
    'triplet': {'time':'_time', 'scatter_calculated': 'scatter', 'chloro_calculated': 'chloro', 'fdom_calculated': 'fdom'},
    'par_digi': {'time':'_time','timer_s': 'timer', 'PAR': 'PAR', 'intern_temperature': 'intern_temperature'},
    'suna': {'time':'_time', 'nitrate': 'nitrate', 'nitrogen': 'nitrogen', 'absorbance_254_31': 'absorbance_254_31',
             'absorbance_350_16': 'absorbance_350_16', 'bromide': 'bromide',
             'spectrum_average': 'spectrum_average'},
    'gps': {'time':'_time', 'longitude_E': 'lon', 'latitude_N': 'lat', 'speed': 'speed', 'course': 'course',
            'variation_E': 'magnetic_variation'},
    'ctd': {'temperature': 'temperature', 'conductivity': 'conductivity',
            'salinity': 'salinity', 'density': 'density'},
    'ctdo': {'temperature': 'temperature', 'conductivity': 'conductivity',
             'salinity': 'salinity', 'oxygen': 'oxygen'},
    'rti': {'bin': 'bin', 'position_cm': 'position',
            'beam1': 'beam1', 'beam2': 'beam2', 'beam3': 'beam3', 'beam4': 'beam4',
            'u': 'u', 'v': 'v', 'w': 'w', 'e': 'e',
            'corr1': 'corr1', 'corr2': 'corr2', 'corr3': 'corr3', 'corr4': 'corr4',
            'amp1': 'amp1', 'amp2': 'amp2', 'amp3': 'amp3', 'amp4': 'amp4',
            'bt_beam1': 'bt_beam1', 'bt_beam2': 'bt_beam2', 'bt_beam3': 'bt_beam3', 'bt_beam4': 'bt_beam4',
            'bt_u': 'bt_u', 'bt_v': 'bt_v', 'bt_w': 'bt_w', 'bt_e': 'bt_e',
            'bt_corr1': 'bt_corr1', 'bt_corr2': 'bt_corr2', 'bt_corr3': 'bt_corr3', 'bt_corr4': 'bt_corr4',
            'bt_amp1': 'bt_amp1', 'bt_amp2': 'bt_amp2', 'bt_amp3': 'bt_amp3', 'bt_amp4': 'bt_amp4'},
    'rdi': {'time':'_time', 'u': 'u', 'v': 'v', 'w': 'w', 'e': 'e'},
    'wave_m': {'time':'_time', 'period': 'period', 'average_height': 'average_height',
               'significant_height': 'significant_height', 'maximal_height': 'maximal_height'},
    'wave_s': {'time':'_time', 'dominant_period': 'period', 'pmax2': 'period_max', 'wave_direction': 'direction',
               'average_height': 'average_height', 'Hmax': 'maximal_height', 'Hmax2': 'maximal2_height'},
    'wxt520': {'Dm': 'wind_direction', 'Sn': 'wind_min', 'Sx': 'wind_max', 'Sm': 'wind_mean',
               'Ta': 'temperature', 'Ua': 'humidity', 'Pa': 'pressure'},
    'wmt700': {'Dm': 'wind_direction', 'Sn': 'wind_min', 'Sx': 'wind_max', 'Sm': 'wind_mean'},
    'wph': {'time':'_time', 'ext_ph': 'ext_ph', 'ext_volt': 'ext_volt', 'ph_temperature': 'temperature',
            'error_flag': 'error_flag'},
    'co2_w': {'time':'_time', 'auto_zero': 'auto_zero', 'current': 'current', 'co2_ppm': 'co2',
              'irga_temperature': 'irga_temperature', 'humidity_mbar': 'humidity',
              'humidity_sensor_temperature': 'humidity_sensor_temperature',
              'cell_gas_pressure_mbar': 'cell_gas_pressure'},
    'co2_a': {'time':'_time', 'auto_zero': 'auto_zero', 'current': 'current', 'co2_ppm': 'co2',
              'irga_temperature': 'irga_temperature', 'humidity_mbar': 'humidity',
              'humidity_sensor_temperature': 'humidity_sensor_temperature',
              'cell_gas_pressure_mbar': 'cell_gas_pressure'},
    'debit': {'flow_ms': 'flow'},
    'vemco': {'time':'_time', 'protocol': 'protocol', 'serial_number': 'serial_number'}
}
variables_attrs = {
    'suna': {'nitrate': {'units': 'uMol'}, 'nitrogen': {'units': 'mgN/L'}, 'bromide': {'units': 'mg/L'}},
    'gps': {'speed': {'units': 'meters per second'}},
    'rti': {'position_cm': {'units': 'meters'},
            'u': {'units': 'meters per second'}, 'v': {'units': 'meters per second'},
            'w': {'units': 'meters per second'}, 'e': {'units': 'meters per second'},
            'bt_u': {'units': 'meters per second'}, 'bt_v': {'units': 'meters per second'},
            'bt_w': {'units': 'meters per second'}, 'bt_e': {'units': 'meters per second'}},
    'rdi': {'u': {'units': 'meters per second'}, 'v': {'units': 'meters per second'},
            'w': {'units': 'meters per second'}, 'e': {'units': 'meters per second'}},
    'wxt': {'Sn': {'units': 'meters per second'}, 'Sx': {'units': 'meters per second'},
            'Sm': {'units': 'meters per second'}},
    'wmt': {'Sn': {'units': 'meters per second'}, 'Sx': {'units': 'meters per second'},
            'Sm': {'units': 'meters per second'}},
    'co2_w': {'current': {'units': 'counts'}, 'co2_ppm': {'units': 'ppm'},
              'humidity_mbar': {'units': 'mbar'}, 'cell_gas_pressure_mbar': {'units': 'mbar'}},
    'co2_a': {'current': {'units': 'counts'}, 'co2_ppm': {'units': 'ppm'},
              'humidity_mbar': {'units': 'mbar'}, 'cell_gas_pressure_mbar': {'units': 'mbar'}},
    'debit': {'flow_ms': {'units': 'meter per second'}}
}
variables_scales = {
    'rti': {'position_cm': 1 / 100,
            'u': 1 / 1000, 'v': 1 / 1000, 'w': 1 / 1000, 'e': 1 / 1000,
            'bt_u': 1 / 1000, 'bt_v': 1 / 1000, 'bt_w': 1 / 1000, 'bt_e': 1 / 1000},
    'rdi': {'u': 1 / 1000, 'v': 1 / 1000, 'w': 1 / 1000, 'e': 1 / 1000},
    'wxt': {'Sn': 1 / KNOTS_PER_METER_S, 'Sx': 1 / KNOTS_PER_METER_S, 'Sm': 1 / KNOTS_PER_METER_S},
    'wmt': {'Sn': 1 / KNOTS_PER_METER_S, 'Sx': 1 / KNOTS_PER_METER_S, 'Sm': 1 / KNOTS_PER_METER_S}

}
global_attrs = {'triplet': {'model_number': 'model_number', 'serial_number': 'serial_number'},
                'par_digi': {'model_number': 'model_number', 'serial_number': 'serial_number'},
                'wph': {'serial_number': 'serial_number'},
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

    for tag in variables_names.keys():
        if viking_data.__dict__[tag] is not None:
            v_attrs = variables_attrs[tag] if tag in variables_attrs else {}
            v_scales = variables_scales[tag] if tag in variables_scales else {}

            data_vars = {}
            for var, name in variables_names[tag].items():
                values = viking_data.__dict__[tag][var]
                var_attrs = v_attrs[var] if var in v_attrs else None
                var_scale = v_scales[var] if var in v_scales else 1
                if var == 'time':
                    data_vars[name] = (['time'], values.filled(np.datetime64('NaT')).astype('datetime64[s]'), var_attrs)
                elif np.issubdtype(values.dtype, str):
                    data_vars[name] = (['time'], values.filled("NA"), var_attrs)
                else:
                    data_vars[name] = (['time'], values.filled(np.nan) * var_scale, var_attrs)

            g_attrs = {}
            if tag in global_attrs:
                for var, name in global_attrs[tag].items():
                    index = np.where(viking_data.__dict__[tag][var].mask == False)[0]
                    g_attrs[name] = str(viking_data.__dict__[tag][var].data[index][0])

            datasets[tag] = xr.Dataset(data_vars, coords=nom_coords, attrs = g_attrs)

    for key in datasets.keys():
        datasets[key] = _average_duplicates(datasets[key], 'time')

    return datasets


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
        return sorted(list(set(list(index) + list(index+1))))

    # viking_data = main()
    vr = VikingReader().read('/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat')

    viking_data = vr._buoys_data['pmza_riki']

    datasets = load_viking_dat(viking_data)

