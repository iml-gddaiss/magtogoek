"""
Date April 6 2022
Made by jeromejguay

Module that contains function to load meteoc variable into a dataset.

Data That Need Processing
-------------------------
    co2_a and co2_w: ppm values are divided by 1e6 and multiplied byt the cell_gas_pressure.

    WpH -> Algorithm in magtogoek/viking/tools.py

    - BODC NAMES: https://vocab.nerc.ac.uk/search_nvs/P01/

    - VARIABLES NOT IN METEOCE odf.
      PAR
      chlorophyle
      fdom
      do

    - DO computation:
        https://github.com/TEOS-10/python-gsw/blob/master/gsw/gibbs/conversions.py
        https://github.com/ooici/ion-functions/blob/master/ion_functions/data/do2_functions.py

TODOS
-----
TODO DO SOME LOGGINGS
TODO make it choose a file format.
"""
from magtogoek.viking.dat_reader import RawDatReader, VikingData
import matplotlib
import numpy as np
import xarray as xr
from typing import *
from magtogoek.utils import Logger

matplotlib.use('Qt5Agg')

l = Logger()


def load_meteoce_data(
        filenames: Tuple[str, List[str]],
        buoy_name: str,
        data_format: str,
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
    l.reset()
    if data_format == "raw_dat":
        dat_reader = RawDatReader()
    else:
        l.warning('Invalid data_format.')
        raise ValueError

    buoys_data = dat_reader.read(filenames)

    if buoy_name is None:
        if len(buoys_data.keys()) == 1:
            buoy_name = buoys_data.keys()[0]
        else:
            l.warning(f'More than one buoy was found in the file {filenames}. Exiting')
            raise ValueError

    elif buoy_name in buoys_data:
        pass
    else:
        l.warning(f'Buoy Name was not found in the file {filenames}. Exiting')
        raise ValueError

    viking_data = buoys_data[buoy_name]

    data = get_meteoce_data(viking_data)

    coords = {'time': np.asarray(viking_data.time)}

    global_attrs = {
        'buoy_name': viking_data.buoy_name,
        'firmware': viking_data.firmware,
        'controller_serial_number': viking_data.controller_sn
    }

    data = _fill_data(data)

    dataset = xr.Dataset(data, coords=coords, attrs=global_attrs)

    dataset = _average_duplicates(dataset, 'time')

    dataset.attrs['logbook'] = l.logbook

    return dataset


def get_meteoce_data(viking_data: VikingData) -> Dict[str, Tuple[np.ma.MaskedArray, dict]]:
    _data = {'lon': (viking_data.longitude, {}),
             'lat': (viking_data.latitude, {}),
             }
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
         # TODO Oxygen Correction ?

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

    return _data


def _fill_data(data: Dict[str, Tuple[np.ma.MaskedArray, dict]]) -> Dict[str, Tuple[List[str], np.ndarray, dict]]:
    """
    """
    for key, item in data.items():
        data[key] = ('time', item[0].filled(), item[1])

    return data


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
    vr = RawDatReader()
    _buoys_data = vr.read('/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat')

    v_data = _buoys_data['pmza_riki']

    ds = load_meteoce_data(v_data)

    ds.to_netcdf('/home/jeromejguay/Desktop/viking_test.nc')
