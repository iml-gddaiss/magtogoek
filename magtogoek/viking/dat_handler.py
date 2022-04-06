"""
DateL April 6 2022
Made by jeromejguay
This script is used to decode the data send by Viking as of February 2022 format version.

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

from magtogoek.viking.raw_dat_decoder import VikingReader
import matplotlib
import numpy as np
import xarray as xr

from magtogoek.utils import get_files_from_expression, nans

matplotlib.use('Qt5Agg')

#FILL_VALUE = -32768  # Reusing the same fill value as teledyne (RDI) -(2**15)

KNOTS_PER_METER_S = 1.94384  # knots per meter/per

TAGS = ["NOM", "COMP", "Triplet", "Par_digi", "SUNA", "GPS",
        "CTD", "CTDO", "RTI", "RDI", "WAVE_M", "WAVE_S", "WXT520",
        "WMT700", "WpH", "CO2_W", "CO2_A", "Debit", "VEMCO"]  # "OCR", "MO", "FIN"]

# ODF
meteoc_variables = ['lon', 'lat',
                    'wind_mean', 'wind_direction_mean', 'wind_max', 'wind_direction_max',
                    'atm_temperature', 'atm_humidity', 'atm_pressure',
                    'temperature', 'conductivity', 'salinity', 'density',
                    'ph', 'fluorescence', 'co2_a', 'co2_w',
                    'averaged_height', 'maximal_height', 'wave_period']


def to_netcdf(viking_data: VikingData) -> xr.Dataset:
    """FIXME Make it a method of VikingData
    Deals with duplicate Time in NOM.

    Notes
    -----
    WXT only output Th, Vh, Vs, Vr data and I have no Idea what they are.
    """
    _datasets = dict().fromkeys(['nom', 'comp', 'trip','par', 'suna', 'gps', 'ctd', 'adcp', 'wave',
                                 'wxt', 'wmt', 'wph', 'co2w', 'co2a', 'debit', 'vemco'])

    nom_coords = {'time': np.asarray(viking_data.time)}
    nom_data = {'lon': (['time'], viking_data.longitude.filled(np.nan)),
                'lat': (['time'], viking_data.latitude.filled(np.nan))}
    _datasets['nom'] = xr.Dataset(
        nom_data,
        coords=nom_coords,
        attrs={'firmware': viking_data.firmware, 'controller_sn': viking_data.controller_sn}).dropna('time')
    variables_names = {
        'comp': {'heading': 'heading', 'pitch': 'pitch', 'roll': '_roll', 'tilt': 'tilt',
                 'pitch_std': 'pitch_std', 'roll_std': 'roll_std', 'tilt_std': 'tilt_std'},
        'par_digi': {'timer_s': 'timer', 'PAR': 'PAR', 'intern_temperature': 'intern_temperature'},
        'suna': {'nitrate': 'nitrate', 'nitrogen': 'nitrogen', 'absorbance_254_31': 'absorbance_254_31',
                 'absorbance_350_16': 'absorbance_350_16', 'bromide': 'bromide',
                 'spectrum_average': 'spectrum_average'},
        'gps': {'longitude_E': 'lon', 'latitude_N': 'lat', 'speed': 'speed', 'course': 'course',
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
        'rdi': {'u': 'u', 'v': 'v', 'w': 'w', 'e': 'e'},
        'wave_m': {'period': 'period', 'average_height': 'average_height',
                   'significant_height': 'significant_height', 'maximal_height': 'maximal_height'},
        'wave_s': {'dominant_period': 'period', 'pmax2': 'period_max', 'wave_direction': 'direction',
                   'average_height': 'average_height', 'Hmax': 'maximal_height', 'Hmax2': 'maximal2_height'},
        'wxt': {'Dm': 'wind_direction', 'Sn': 'wind_min', 'Sx': 'wind_max', 'Sm': 'wind_mean',
                'Ta': 'temperature', 'Ua': 'humidity', 'Pa': 'pressure'}
        'wmt': {'Dm': 'wind_direction', 'Sn': 'wind_min', 'Sx': 'wind_max', 'Sm': 'wind_mean'},
        'wph': {'ext_ph': 'ext_ph', 'ext_volt': 'ext_volt', 'ph_temperature': 'temperature',
                'error_flag': 'error_flag'},
        'co2_w': {'auto_zero': 'auto_zero', 'current': 'current', 'co2_ppm': 'co2',
                  'irga_temperature': 'irga_temperature', 'humidity_mbar': 'humidity',
                  'humidity_sensor_temperature': 'humidity_sensor_temperature',
                  'cell_gas_pressure_mbar': 'cell_gas_pressure'},
        'co2_a': {'auto_zero': 'auto_zero', 'current': 'current', 'co2_ppm': 'co2',
                  'irga_temperature': 'irga_temperature', 'humidity_mbar': 'humidity',
                  'humidity_sensor_temperature': 'humidity_sensor_temperature',
                  'cell_gas_pressure_mbar': 'cell_gas_pressure'},
        'debit': {'flow_ms': 'flow'},
        'vemco': {'protocol': 'protocol', 'serial_number': 'serial_number'}
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
    if viking_data.comp is not None:
        _datasets['comp'] = xr.Dataset(_make_data_vars(viking_data, 'comp', comp_variables),
                                       coords=nom_coords,
                                       attrs={'time': 'nom'})

    if viking_data.triplet is not None:
        triplet_dataset = _sort_triplet_wavelength(viking_data.triplet) # fix function names

    if viking_data.par_digi is not None:
        par_digi_index = ~viking_data.par_digi['time'].mask
        _datasets['par_digi'] = xr.Dataset(
            _make_data_vars(viking_data, 'par_digi', par_digi_variables, index=par_digi_index),
            coords={'time': np.asarray(viking_data.par_digi['time'][par_digi_index].astype('datetime64[s]'))},
            attrs={'model_number': viking_data.par_digi['model_number'][par_digi_index][0],
                   'serial_number': viking_data.par_digi['serial_number'][par_digi_index][0]}
        )

    if viking_data.suna is not None:
        suna_index = ~viking_data.suna['time'].mask
        _datasets['suna'] = xr.Dataset(
            _make_data_vars(viking_data, 'suna', variables=suna_variables, index=suna_index, attrs=suna_attrs),
            coords={'time': np.asarray(viking_data.suna['time'][suna_index].astype('datetime64[s]'))},
            attrs={'model_number': viking_data.suna['model_number'][suna_index][0],
                   'serial_number': viking_data.suna['serial_number'][suna_index][0]}
        )

    if viking_data.gps is not None:
        gps_index = ~viking_data.gps['time'].mask
        gps_scale = {'speed': 1 / KNOTS_PER_METER_S}
        _datasets['gps'] = xr.Dataset(
            _make_data_vars(viking_data, 'gps', variables=gps_variables,
                            index=gps_index, attrs=gps_attrs, scales=gps_scale),
            coords={'time': np.asarray(viking_data.gps['time'][gps_index].astype('datetime64[s]'))}
        )

    if viking_data.ctd is not None:
        _datasets['ctd'] = xr.Dataset(
            _make_data_vars(viking_data, 'ctd', variables=ctd_variables),
            coords=nom_coords,
            attrs={'time': 'nom'})

    elif viking_data.ctdo is not None:
        _datasets['ctd'] = xr.Dataset(
            _make_data_vars(viking_data, 'ctdo', variables=ctdo_variables),
            coords=nom_coords,
            attrs={'time': 'nom'})

    if viking_data.rti is not None:
        _datasets['adcp'] = xr.Dataset(
            _make_data_vars(viking_data, 'rti', variables=rti_variables, scales=rti_scales, attrs=rti_attrs),
            coords=nom_coords,
            attrs={'time': 'nom', 'manufacturer': 'rti'})

    elif viking_data.rdi is not None:
        rdi_index = ~viking_data.rdi['time'].mask
        _datasets['adcp'] = xr.Dataset(
            _make_data_vars(viking_data, 'rdi', variables=rdi_variables,
                            index=rdi_index, scales=rdi_scales, attrs=rdi_attrs),
            coords={'time': np.asarray(viking_data.rdi['time'][rdi_index].astype('datetime64[s]'))},
            attrs={'time': 'nom', 'manufacturer': 'rdi'})

    if viking_data.wave_m is not None:
        wave_m_index = ~viking_data.wave_m['time'].mask
        _datasets['wave'] = xr.Dataset(
            _make_data_vars(viking_data, 'wave_m', variables=wave_m_variables, index=wave_m_index),
            coords={'time': np.asarray(viking_data.wave_m['time'][wave_m_index]).astype('datetime64[s]')})

    elif viking_data.wave_s is not None:
        wave_s_index = ~viking_data.wave_s['time'].mask
        _datasets['wave'] = xr.Dataset(
            _make_data_vars(viking_data, 'wave_s', variables=wave_s_variables, index=wave_s_index),
            coords={'time': np.asarray(viking_data.wave_s['time'][wave_s_index]).astype('datetime64[s]')})

    if viking_data.wxt520 is not None:
        _datasets['wxt'] = xr.Dataset(
            _make_data_vars(viking_data, 'wxt520', variables=wxt_variables, scales=wxt_scales, attrs=wxt_attrs),
            coords=nom_coords,
            attrs={'time': 'nom'})

    if viking_data.wmt700 is not None:
        _datasets['wmt'] = xr.Dataset(
            _make_data_vars(viking_data, 'wmt700', variables=wmt_variables, scales=wmt_scales, attrs=wmt_attrs),
            coords=nom_coords,
            attrs={'time': 'nom'})

    if viking_data.wph is not None:
        wph_index = ~viking_data.wph['time'].mask
        _datasets['wph'] = xr.Dataset(
            _make_data_vars(viking_data, 'wph', variables=wph_variables, index=wph_index),
            coords={'time': np.asarray(viking_data.wph['time'][wph_index]).astype('datetime64[s]')},
            attrs={'model': viking_data.wph['model'][wph_index][0],
                   'serial_number': viking_data.wph['serial_number'][wph_index][0]})

    if viking_data.co2_w:
        co2_w_index = ~viking_data.co2_w['time'].mask
        _datasets['co2_w'] = xr.Dataset(
            _make_data_vars(viking_data, 'co2_w', variables=co2_w_variables, attrs=co2_w_attrs, index=co2_w_index),
            coords={'time': viking_data.co2_w['time'][co2_w_index].astype('datetime64[s]')})

    if viking_data.co2_a:
        co2_a_index = ~viking_data.co2_a['time'].mask
        _datasets['co2_a'] = xr.Dataset(
            _make_data_vars(viking_data, 'co2_a', variables=co2_a_variables, attrs=co2_a_attrs, index=co2_a_index),
            coords={'time': viking_data.co2_a['time'][co2_a_index].astype('datetime64[s]')})

    if viking_data.debit:
        _datasets['debit'] = xr.Dataset(
            _make_data_vars(viking_data, 'debit', variables=debit_variables, attrs=debit_attrs),
            coords=nom_coords,
            attrs={'time': 'nom'})

    if viking_data.vemco:
        vemco_index = ~viking_data.vemco['time'].mask
        _datasets['vemco'] = xr.Dataset(
            _make_data_vars(viking_data, 'vemco', variables=vemco_variables, index=vemco_index),
            coords={'time': np.asarray(viking_data.vemco['time'][vemco_index].astype('datetime64[s]'))})

    for key in _datasets.keys():
        if _datasets[key] is not None:
            _datasets[key] = _average_duplicates(_datasets[key], 'time')

    return _datasets


def _make_data_vars(viking_data: VikingData,
                    tag: str, variables: dict,
                    index: np.ndarray = None,
                    attrs: dict = None,
                    scales: dict = None,
                    ):
    """Return parameters data_var for xarray.Dataset.
    """
    if attrs is None:
        attrs = {}
    if scales is None:
        scales = {}

    data_vars = {}
    for key, value in variables.items():
        values = viking_data.__dict__[tag][key][index] if index is not None else viking_data.__dict__[tag][key]
        key_attrs = attrs[key] if key in attrs else None
        key_scale = scales[key] if key in scales else 1
        if np.issubdtype(values.dtype, str):
            data_vars[key] = (['time'], values.filled("NA" ), key_attrs)
        else:
            data_vars[key] = (['time'], values.filled(np.nan) * key_scale, key_attrs)

    return data_vars


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

    datasets = to_netcdf(viking_data)

