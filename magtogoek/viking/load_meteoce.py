"""
Date April 6 2022
Made by jeromejguay

Module that contains function to load meteoc variable into a dataset.

Data That Need Processing
-------------------------
    co2_a and co2_w: ppm values are divided by 1e6 and multiplied byt the cell_gas_pressure.

    WpH -> Algorithm in magtogoek/viking/tools.py


    - BODC NAMES: https://vocab.nerc.ac.uk/search_nvs/P01/

METEOCE BODC:
        Time                                                 : SYTM_01 : SDN:P01::
        Longitude (East +ve)                                 : LOND_01 : SDN:P01::
        Latitude (North +ve)                                 : LATD_01 : SDN:P01::
        Horizontal Wind Speed                                : WSPD_01 : SDN:P01::EWSBZZ01
        Gust Wind Speed                                      : GSPD_01 : SDN:P01::EGTSZZ01
        Wind Direction relative to North (T)                 : WDIR_01 : SDN:P01::EWDAZZ01
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
        Wave mean height                                     : VRMS_01 : SDN:P01::GAVHZZ01
        Wave maximum height                                  : VMXL_01 : SDN:P01::GCMXZZ01
        Wave period                                          : VTCA_01 : SDN:P01::GTAMZZ01

    - VARIABLES NOT IN METEOCE odf.
      PAR
      chlorophyle
      fdom

    - DO computation:
        https://github.com/TEOS-10/python-gsw/blob/master/gsw/gibbs/conversions.py
        https://github.com/ooici/ion-functions/blob/master/ion_functions/data/do2_functions.py

"""
from magtogoek.viking.raw_dat_reader import VikingReader, VikingData
import matplotlib
import numpy as np
import xarray as xr
#import pint

# data_variable : (tag, name)
meteoc_variables = {
    'lon': ('nom', 'lon'),
    'lat': ('nom', 'lat'),
    'wind_mean': [('wxt520', 'Sm'),
                  ('wmt700', 'Sm')],
    'wind_direction_mean': [('wxt520', 'Dm'),
                            ('wmt700', 'Dm')],
    'wind_max': [('wxt520', 'Sx'),
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
    'ph': ('wph', "PH CORRECTION"), #COMPUTATION NEEDED TODO
    'fluorescence': ('triplet', 'fluo'),
    'co2_a': ('co2_a', 'co2_ppm'), # COMPUTATION NEEDED TODO
    'co2_w': ('co2_w', 'co2_ppm'), # COMPUTATION NEEDED, TODO
    'wave_mean_height': [('wave_m', 'mean_height'),
                        ('wave_s', 'mean_height')],
    'wave_maximal_height': [('wave_m', 'maximal_height'),
                       ('wave_s', 'Hmax')],
    'wave_period': [('wave_m', 'period'),
                    ('wave_s', 'dominant_period')],
}

VARIABLES_UNITS = {
    'par_digi': {'PAR': 'micromoles photons per meter squared per second'},
    'triplet': {'fluo': 'milligramme per meter squared'},
    'gps': {'speed': 'meters per second'},
    'rti': {'position': 'meters',
            'u': 'meters per second', 'v': 'meters per second', 'w': 'meters per second', 'e': 'meters per second',
            'bt_u': 'meters per second', 'bt_v': 'meters per second',
            'bt_w': 'meters per second', 'bt_e': 'meters per second'},
    'rdi': {'u': 'meters per second', 'v': 'meters per second', 'w': 'meters per second', 'e': 'meters per second'},
    'wxt': {'Sn': 'meters per second', 'Sx': 'meters per second', 'Sm': 'meters per second'},
    'wmt': {'Sn': 'meters per second', 'Sx': 'meters per second', 'Sm': 'meters per second'}
}


def load_meteoce_data(viking_data: VikingData) -> xr.Dataset:
    _coords = {'time': np.asarray(viking_data.time)}
    _data = {'lon': (viking_data.longitude, {}),
             'lat': (viking_data.latitude, {}),
             }
    _global_attrs = {'buoy_name': viking_data.buoy_name,
                     'firmware': viking_data.firmware,
                     'controller_serial_number': viking_data.controller_sn}

    if viking_data.comp is not None:
        _data.update(
            {'heading': (viking_data.comp['heading'], {}),
             'pitch': (viking_data.comp['pitch'], {}),
             '_roll': (viking_data.comp['roll'], {}),
             'tilt': (viking_data.comp['tilt'], {})}
        )

    if viking_data.wmt700 is not None:
        _data.update(
            {'wind_mean': (viking_data.wmt700['Sm'], {}),
             'wind_direction_mean': (viking_data.wmt700['Dm'], {}),
             'wind_max': (viking_data.wmt700['Sx'], {}),
             'wind_direction_max': (viking_data.wmt700['Dx'], {})}
        )
    if viking_data.wxt520 is not None:
        _data.update(
            {'atm_temperature': (viking_data.wxt520['Ta'], {}),
             'atm_humidity': (viking_data.wxt520['Ua'], {}),
             'atm_pressure': (viking_data.wxt520['Pa'], {})}
        )
        for nc_name, viking_name in zip(('wind_mean', 'wind_direction_mean', 'wind_max', 'wind_direction_max'),
                                        ('Sm', 'Dm', 'Sx', 'Dx')):
            if nc_name in _data:
                if not (~_data[nc_name][0].mask).any():
                    _data[nc_name] = (viking_data.wxt520[viking_name], {})
            else:
                _data[nc_name] = (viking_data.wxt520[viking_name], {})

    if viking_data.ctd is not None:
        _data.update(
            {'temperature': (viking_data.ctd['temperature'], {}),
             'salinity': (viking_data.ctd['salinity'], {}),
             'density': (viking_data.ctd['density'], {})}
        )

    elif viking_data.ctdo is not None:
        _data.update(
            {'temperature': (viking_data.ctdo['temperature'], {}),
             'salinity': (viking_data.ctdo['salinity'], {}),
             'oxygen': (viking_data.ctd['oxygen'], {})}
        )
         # TODO 'density' needs to be computed

    if viking_data.wph is not None:
        _attrs = {
            'serial_number': viking_data.wph['serial_number'][~viking_data.wph['serial_number'].mask][0],
            'model_number': viking_data.wph['model'][~viking_data.wph['model'].mask][0]
        }
        _data.update(
            {'ph': (viking_data.wph['ext_ph'], _attrs)}
        )# TODO needs to be corrected

    if viking_data.triplet is not None:
        _attrs = {'serial_number': viking_data.triplet['serial_number'][~viking_data.triplet['serial_number'].mask][0],
                  'model_number': viking_data.triplet['model_number'][~viking_data.triplet['model_number'].mask][0]}
        _data.update(
            {'fluo': (viking_data.triplet['fluo_calculated'], _attrs),
             'chloro': (viking_data.triplet['chloro_calculated'], _attrs),
             'fdom': (viking_data.triplet['fdom_calculated'], _attrs)}
        )

    if viking_data.par_digi is not None:
        _attrs = {
            'serial_number': viking_data.par_digi['serial_number'][~viking_data.par_digi['serial_number'].mask][0],
            'model_number': viking_data.par_digi['model_number'][~viking_data.par_digi['model_number'].mask][0]
        }
        _data['par'] = (viking_data.par_digi['PAR'], _attrs)

    if viking_data.co2_a is not None:
        _data.update({'co2_a': (viking_data.co2_a['cell_gas_pressure_mbar'] * viking_data.co2_a['co2_ppm'] / 1e6, {})})

    if viking_data.co2_w is not None:
        _data.update({'co2_w': (viking_data.co2_w['cell_gas_pressure_mbar'] * viking_data.co2_w['co2_ppm'] / 1e6 ,{})})

    if viking_data.wave_m is not None:
        _data.update(
            {'wave_mean_height': (viking_data.wave_m['average_height'], {}),
             'wave_maximal_height': (viking_data.wave_m['maximal_height'], {}),
             'wave_period': (viking_data.wave_m['period'], {})}
        )

    elif viking_data.wave_s is not None:
        _data.update(
            {'wave_mean_height': (viking_data.wave_s['average_height'], {}),
             'wave_maximal_height': (viking_data.wave_s['Hmax'], {}),
             'wave_period': (viking_data.wave_s['dominant_period'], {})}
        )

    if viking_data.rdi is not None:
        # TODO carry one quality control
        for _name in ['u', 'v', 'w', 'e']:
            _data[_name] = (viking_data.rdi[_name], {})

    elif viking_data.rti is not None:
        # TODO carry one quality control
        _attrs = {'bin': viking_data.rti['bin'][~viking_data.rti['bin'].mask],
                  'position': viking_data.rti['position_cm'][~viking_data.rti['position_cm'].mask].to('m')}
        for _name in ['u', 'v', 'w', 'e', 'corr1', 'corr2', 'corr3', 'corr4', 'amp1', 'amp2', 'amp3', 'amp4']:
            _data[_name] = (viking_data.rti[_name], _attrs)
            _data["bt_"+_name] = (viking_data.rti["bt_"+_name], _attrs)

    return xr.Dataset(_data, coords=_coords, attrs=_global_attrs)


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
    vr = VikingReader()
    buoys_data = vr.read('/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat')

    v_data = buoys_data['pmza_riki']

    dataset = load_meteoce_data(v_data)
