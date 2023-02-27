"""
Date April 6 2022
Made by jeromejguay

Module that contains function to load meteoc variable into a dataset.

Data That Need Processing
-------------------------
    co2_a and co2_w: ppm values are divided by 1e6 and multiplied byt the cell_gas_pressure.

    - BODC NAMES: https://vocab.nerc.ac.uk/search_nvs/P01/

    - VARIABLES NOT IN METEOCE odf.
      PAR
      chlorophyle
      fdom
      do

    - DO computation:
        https://github.com/TEOS-10/python-gsw/blob/master/gsw/gibbs/conversions.py
        https://github.com/ooici/ion-functions/blob/master/ion_functions/data/do2_functions.py

Notes
-----
Load more data ? wind min ?
"""

from magtogoek.viking.dat_reader import RawDatReader, VikingData
import matplotlib
import numpy as np
import xarray as xr
from typing import *
import magtogoek.logger as l
from magtogoek.utils import format_filenames_for_print

matplotlib.use('Qt5Agg')

KNOTS_TO_METER_PER_SECONDS = 1 / 1.944   # 1 kt = (1/1.944) m/s
MILLIMETER_TO_METER = 1 / 1000
CENTIMETER_TO_METER = 1 / 100
#MILLIBAR_TO_DECIBAR = 1 / 100


def load_meteoce_data(
        filenames: Tuple[str, List[str]],
        buoy_name: str = None,
        data_format: str = 'raw_dat',
) -> xr.Dataset:
    """

    Parameters
    ----------
    filenames
    buoy_name
    data_format :
        One of [raw_dat]

    Returns
    -------

    """
    l.section('Loading viking data', t=True)
    if data_format == "raw_dat":
        l.log(format_filenames_for_print('raw_data', filenames))
        buoys_data = RawDatReader().read(filenames)

    else:
        l.warning('Invalid data_format.')
        raise ValueError

    if buoy_name is None:
        if len(buoys_data.keys()) == 1:
            buoy_name = list(buoys_data.keys())[0]
            l.log(f'Data from {buoy_name} buoy selected.')
        else:
            l.warning(f'More than one buoy was found in the file {filenames}. Exiting')
            raise ValueError
    elif buoy_name in buoys_data:
        pass
    else:
        l.warning(f'Buoy Name was not found in the file {filenames}. Exiting')
        raise ValueError

    viking_data = buoys_data[buoy_name]

    meteoce_data = get_meteoce_data(viking_data)

    coords = {'time': np.asarray(viking_data.time)}

    global_attrs = {
        'buoy_name': viking_data.buoy_name,
        'firmware': viking_data.firmware,
        'controller_serial_number': viking_data.controller_sn
    }

    meteoce_data = _fill_data(meteoce_data)

    dataset = xr.Dataset(meteoce_data, coords=coords, attrs=global_attrs)

    dataset = _average_duplicates(dataset, 'time')

    dataset.attrs['logbook'] = l.logbook

    l.log('Data Loaded.')

    return dataset


def get_meteoce_data(viking_data: VikingData) -> Dict[str, Tuple[np.ma.MaskedArray, dict]]:
    _data = {'lon': (viking_data.longitude, {}),
             'lat': (viking_data.latitude, {}),
             }

    if viking_data.gps is not None:
        _data.update(
            {'speed': (viking_data.gps['speed'] * KNOTS_TO_METER_PER_SECONDS, {"units": "m/s"}),
             'course': (viking_data.gps['course'], {}),
             'magnetic_declination': (viking_data.gps['variation_E'], {})}
        )
        l.log('Gps data loaded.')

    if viking_data.comp is not None:
        _data.update(
            {'heading': (viking_data.comp['heading'], {}),
             'pitch': (viking_data.comp['pitch'], {}),
             'roll_': (viking_data.comp['roll'], {})}
        )
        l.log('Comp data loaded.')

    if viking_data.wmt700 is not None:
        _data.update(
            {'wind_mean': (viking_data.wmt700['Sm'] * KNOTS_TO_METER_PER_SECONDS, {'units': 'm/s'}),
             'wind_direction_mean': (viking_data.wmt700['Dm'], {}),
             'wind_max': (viking_data.wmt700['Sx'] * KNOTS_TO_METER_PER_SECONDS , {'units': 'm/s'}),
             'wind_direction_max': (viking_data.wmt700['Dx'], {})}
        )
        l.log('wmt700 data loaded.')

    if viking_data.wxt520 is not None:
        _data.update(
            {'atm_temperature': (viking_data.wxt520['Ta'], {}),
             'atm_humidity': (viking_data.wxt520['Ua'], {}),
             'atm_pressure': (viking_data.wxt520['Pa'], {"units": "mbar"})}
        )
        # A parameter could be added to choose where to load wind data from. TODO
        # wind data from wxt520 are not loaded at the moment.
        # for nc_name, viking_name, scale, unit in zip(
        #         ('wind_mean', 'wind_direction_mean', 'wind_max', 'wind_direction_max'),
        #         ('Sm', 'Dm', 'Sx', 'Dx'),
        #         (KNOTS_TO_METER_PER_SECONDS, 1, KNOTS_TO_METER_PER_SECONDS, 1),
        #         ('m/s', '', 'm/s', '')
        # ):
        #     if nc_name in _data:
        #         print(_data[nc_name], type(_data[nc_name]))
        #         if not (~_data[nc_name][0].mask).any():
        #             _data[nc_name] = (viking_data.wxt520[viking_name] * scale, {'units': unit})
        #     else:
        #         _data[nc_name] = (viking_data.wxt520[viking_name] * scale, {'units': unit})
        l.log('wxt520 data loaded.')

    if viking_data.ctd is not None:
        _data.update(
            {'temperature': (viking_data.ctd['temperature'], {}),
             'conductivity': (viking_data.ctd['conductivity'], {'units': 'S/m'}),
             'salinity': (viking_data.ctd['salinity'], {}),
             'density': (viking_data.ctd['density'], {})}
        )
        l.log('Ctd data loaded.')

    elif viking_data.ctdo is not None:
        _data.update(
            {'temperature': (viking_data.ctdo['temperature'], {}),
             'conductivity': (viking_data.ctdo['conductivity'], {'units': 'S/m'}),
             'salinity': (viking_data.ctdo['salinity'], {}),
             'dissolved_oxygen': (viking_data.ctdo['dissolved_oxygen'], {'units': 'umol/L'})}
        )
        l.log('Ctdo data loaded.')

    if viking_data.wph is not None:
        _attrs = {
            'serial_number': viking_data.wph['serial_number'][~viking_data.wph['serial_number'].mask][0],
            'model_number': viking_data.wph['model'][~viking_data.wph['model'].mask][0]
        }
        _data.update(
            {
                'ph': (viking_data.wph['ext_ph'], _attrs),
                'ph_temperature': (viking_data.wph['ext_ph'], _attrs)}
        )
        l.log('Wph data loaded.')

    if viking_data.triplet is not None:
        _attrs = {'serial_number': viking_data.triplet['serial_number'][~viking_data.triplet['serial_number'].mask][0],
                  'model_number': viking_data.triplet['model_number'][~viking_data.triplet['model_number'].mask][0]}
        _data.update(
            {
                'fluorescence': (viking_data.triplet['fluo_calculated'], {**_attrs, **{"units": "mg/m**3"}}),
                'chlorophyll': (viking_data.triplet['chloro_calculated'], {**_attrs, **{"units": "mg/m**3"}}),
                'fdom': (viking_data.triplet['fdom_calculated'], {**_attrs, **{"units": "mg/m**3"}})
            }
        )
        l.log('Triplet data loaded.')

    if viking_data.par_digi is not None:
        _attrs = {
            'serial_number': viking_data.par_digi['serial_number'][~viking_data.par_digi['serial_number'].mask][0],
            'model_number': viking_data.par_digi['model_number'][~viking_data.par_digi['model_number'].mask][0]
        }
        _data['par'] = (viking_data.par_digi['PAR'], {**_attrs, **{"units": "umol/m**2/s"}})
        l.log('Par Digi data loaded.')

    if viking_data.co2_a is not None: # co2 partial pressure = (ppm / 1e6)* cell gas pressure
        _data.update({'co2_a': (viking_data.co2_a['cell_gas_pressure_mbar'] * viking_data.co2_a['co2_ppm'] / 1e6, {})})
        l.log('Co2_a data loaded.')

    if viking_data.co2_w is not None: # co2 partial pressure = (ppm / 1e6)* cell gas pressure
        _data.update({'co2_w': (viking_data.co2_w['cell_gas_pressure_mbar'] * viking_data.co2_w['co2_ppm'] / 1e6, {})})
        l.log('Co2_w data loaded.')

    if viking_data.wave_m is not None:
        _data.update(
            {'wave_mean_height': (viking_data.wave_m['average_height'], {}),
             'wave_maximal_height': (viking_data.wave_m['maximal_height'], {}),
             'wave_period': (viking_data.wave_m['period'], {})}
        )
        l.log('Wave_m data loaded.')

    elif viking_data.wave_s is not None:
        _data.update(
            {'wave_mean_height': (viking_data.wave_s['average_height'], {}),
             'wave_maximal_height': (viking_data.wave_s['Hmax'], {}),
             'wave_period': (viking_data.wave_s['dominant_period'], {})}
        )
        l.log('Wave_s data loaded.')

    if viking_data.rdi is not None:
        for _name in ['u', 'v', 'w', 'e']:
            _data[_name] = (viking_data.rdi[_name] * MILLIMETER_TO_METER, {"units": "m/s"})
        l.log('Rdi data loaded.')

    elif viking_data.rti is not None:
        _attrs = {'bin': viking_data.rti['bin'][~viking_data.rti['bin'].mask],
                  'position': viking_data.rti['position_cm'][~viking_data.rti['position_cm'].mask] * CENTIMETER_TO_METER}
        for _name in ['u', 'v', 'w', 'e']:
            _data[_name] = (viking_data.rti[_name] * MILLIMETER_TO_METER, {**_attrs, **{"units": "m/s"}})
            _data["bt_" + _name] = (viking_data.rti["bt_" + _name] * MILLIMETER_TO_METER, {**_attrs, **{"units": "m/s"}})
        for _name in ['corr1', 'corr2', 'corr3', 'corr4', 'amp1', 'amp2', 'amp3', 'amp4']:
            _data[_name] = (viking_data.rti[_name], _attrs)
            _data["bt_"+_name] = (viking_data.rti["bt_"+_name], _attrs)
        l.log('Rti data loaded.')

    return _data


def _fill_data(data: Dict[str, Tuple[np.ma.MaskedArray, dict]]) -> Dict[str, Tuple[List[str], np.ndarray, dict]]:
    """
    """
    for key, item in data.items():
        data[key] = ('time', item[0].filled(), item[1])

    l.log('Missing data filled.')

    return data


def _average_duplicates(dataset: xr.Dataset, coord: str) -> xr.Dataset:
    """Average data_array values of duplicates time coords index.
    """

    df = dataset.to_dataframe()
    df = df.groupby(coord).mean(numeric_only=False)

    _dataset = dataset[{coord: np.unique(dataset[coord], return_index=True)[1]}]
    for var in _dataset.keys():
        _dataset[var].values[:] = df[var][:]

    l.log('Duplicate timestamp data averaged.')
    return _dataset


if __name__ == "__main__":
    vr = RawDatReader()
    _buoys_data = vr.read(['/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'])

    v_data = _buoys_data['pmza_riki']

    ds = load_meteoce_data(['/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'])

    ds.to_netcdf('/home/jeromejguay/Desktop/viking_test.nc')
