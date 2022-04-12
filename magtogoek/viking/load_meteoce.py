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
from magtogoek.viking.raw_dat_reader import VikingReader, VikingData
import matplotlib
import numpy as np
import xarray as xr
#import pint

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
    'averaged_height': [('wave_m', 'averaged_height'),
                        ('wave_s', 'averaged_height')],
    'maximal_height': [('wave_m', 'maximal_height'),
                       ('wave_s', 'Hmax')],
    'wave_period': [('wave_m', 'period'),
                    ('wave_s', 'dominant_period')],
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


def make_meteoce_dataset(viking_data: VikingData) -> xr.Dataset:
    _coords = {'time': np.asarray(viking_data.time)}
    _data = {'lon': (['time'], viking_data.longitude.filled(np.nan)),
             'lat': (['time'], viking_data.latitude.filled(np.nan))}



def _average_duplicates(dataset: xr.Dataset, coord: str) -> xr.Dataset:
    """Average data_array values of duplicates time coords index.
    """

    df = dataset.to_dataframe()
    df = df.groupby(coord).mean(numeric_only=False)

    _dataset = dataset[{coord: np.unique(dataset[coord], return_index=True)[1]}]
    for var in _dataset.keys():
        _dataset[var].values[:] = df[var][:]

    return _dataset