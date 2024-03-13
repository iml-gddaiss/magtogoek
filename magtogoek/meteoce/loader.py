"""
Date: April 2022
Made by jeromejguay

Module that contains function to load meteoc variable into a dataset.


Notes
-----
[March 2023] JeromeJGuay
    The WXT wind measurements are less accurate than the wmt700. Furthermore, the WXT520
    is more likely to malfunction and not send data while the WMT700 always work.

[March 2023] JeromeJGuay
    GPS bearing and course data seem to be bad. We believe that the bearing and course data are instant measurements.
    Thus wave induced rapid horizontal oscillation and the rocking of the buoy, the GPS being located about ~2-3 meters
    above the floating line, result in higher oscillation and amplitude in the speed values. Since speed dependent values
    are average over ~ 1 minutes, we need at least ~1 minutes average values from the gps.
[January 2024] JeromeJGuay
    Wind direction max is the max value (angle) not the direction of wind gust.
"""

import numpy as np
import xarray as xr
from typing import *

import magtogoek.logger as l
from magtogoek.exceptions import MagtogoekExit
from magtogoek.utils import get_files_from_expression, format_filenames_for_print
from magtogoek.tools import is_unique, nan_unique

from magtogoek.meteoce.viking_dat_reader import RawVikingDatReader, VikingData
from magtogoek.meteoce.mitis_dat_reader import RawMitisDatReader, MitisData

import pint_xarray # pint_xarray modify the xr.Dataset Object


KNOTS_TO_METER_PER_SECONDS = 0.5144444444 # mps/knots
MILLIMETER_TO_METER = 1 / 1000
CENTIMETER_TO_METER = 1 / 100


def load_meteoce_data(
        filenames: Union[str, List[str]],
        buoy_name: str = None,
        data_format: str = 'viking',
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
    l.section('Loading meteoce data', t=True)

    filenames = get_files_from_expression(filenames)

    l.log(format_filenames_for_print('raw_data', filenames))

    if data_format == "viking":
        buoy_data = RawVikingDatReader().read(filenames)
    elif data_format == "mitis":
        buoy_data = RawMitisDatReader().read(filenames)
    else:
        l.warning(f'Invalid data_format: {data_format}')
        raise MagtogoekExit("Invalid meteoce data format. Exiting")

    if isinstance(buoy_data, Dict):
        l.warning(f'More than one buoy name was found in the file {filenames}.\n'
                  f' Buoy names fround: {list(buoy_data.keys())}\n'
                  f' Specify a buoy_name\n Exiting')
        raise MagtogoekExit(f'More than one buoy (buoy_name) was found in the file {filenames}. Exiting')

    if buoy_name is not None and buoy_data.buoy_name != buoy_name:
        l.log(f'Buoy Name found in files is different from the one provided.')

    if data_format == "viking":
        meteoce_data, global_attrs = _load_viking_meteoce_data(buoy_data)
        buoy_data = RawVikingDatReader().read(filenames)
    else: #if data_format == "mitis": # not required. Also remove a variable reference warning.
        meteoce_data, global_attrs = _load_mitis_meteoce_data(buoy_data)

    _add_time_coords(meteoce_data)

    coords = {'time': np.asarray(buoy_data.time)}

    dataset = xr.Dataset(meteoce_data, coords=coords, attrs=global_attrs)

    if data_format == "viking":
        dataset = _average_duplicates(dataset, 'time')

    if is_unique(dataset['magnetic_declination']):
        dataset.attrs["magnetic_declination"] = nan_unique(dataset['magnetic_declination'])[0]
        dataset.attrs["magnetic_declination_units"] = "degree east"
        dataset = dataset.drop_vars('magnetic_declination')

    l.log('Data Loaded.')

    return dataset


# def load_viking_data(
#         filenames: Union[str, List[str]],
#         buoy_name: str = None,
#         ) -> xr.Dataset:
#
#     viking_data = RawVikingDatReader().read(filenames)
#
#     if isinstance(viking_data, Dict):
#         l.warning(f'More than one buoy name was found in the file {filenames}.\n'
#                   f' Buoy names fround: {list(viking_data.keys())}\n'
#                   f' Specify a buoy_name\n Exiting')
#         raise MagtogoekExit(f'More than one buoy (buoy_name) was found in the file {filenames}. Exiting')
#
#     if buoy_name is not None and viking_data.buoy_name != buoy_name:
#         l.log(f'Buoy Name found in files is different from the one provided.')
#
#     meteoce_data, global_attrs = _load_viking_meteoce_data(viking_data)
#
#     _add_time_coords(meteoce_data)
#
#     coords = {'time': np.asarray(viking_data.time)}
#
#     dataset = xr.Dataset(meteoce_data, coords=coords, attrs=global_attrs)
#
#     dataset = _average_duplicates(dataset, 'time')
#
#     return dataset


def _load_viking_meteoce_data(viking_data: VikingData) -> Tuple[Dict[str, Tuple[np.ma.MaskedArray, dict]], Dict]:
    """

    Parameters
    ----------
    viking_data

    Returns
    -------
        {variable_name: str -> (data: np.ma.MaskedArray, attributes: Dict)}

    """
    global_attrs = {
        'platform': viking_data.buoy_name,
        'buoy_controller_firmware_version': viking_data.firmware,
        'buoy_controller_serial_number': list(set(viking_data.controller_sn))
    }

    data = {'lon': (viking_data.longitude, {}),
             'lat': (viking_data.latitude, {}),
             }

    if viking_data.gps is not None:
        data.update(
            {'speed': (np.round(viking_data.gps['speed'] * KNOTS_TO_METER_PER_SECONDS, 3), {"units": "m/s"}),
             'course': (viking_data.gps['course'], {}),
             'magnetic_declination': (viking_data.gps['variation_E'], {})}
        )
        l.log('Gps data loaded.')

    if viking_data.comp is not None:
        data.update(
            {'heading': (viking_data.comp['heading'], {}),
             'pitch': (viking_data.comp['pitch'], {}),
             'roll_': (viking_data.comp['roll'], {}),
             'pitch_std': (viking_data.comp['pitch_std'], {}),
             'roll_std': (viking_data.comp['roll_std'], {})}
        )
        l.log('Comp data loaded.')

    if viking_data.wmt700 is not None:
        """
        Sm: wind speed average
        Sn: wind speed min
        Sx: wind speed max
        
        Dm: wind direction average
        Dn: wind direction min
        Dx: wind direction max        
        """
        data.update(
            {

                'wind_speed': (np.round(viking_data.wmt700['Sm'] * KNOTS_TO_METER_PER_SECONDS, 3), {'units': 'm/s'}),
                'wind_direction': (viking_data.wmt700['Dm'], {}),
                'wind_gust': (np.round(viking_data.wmt700['Sx'] * KNOTS_TO_METER_PER_SECONDS, 3), {'units': 'm/s'}),
            }
        )
        l.log('wmt700 data loaded.')

    if viking_data.wxt520 is not None:
        data.update(
            {'atm_temperature': (viking_data.wxt520['Ta'], {"units": "degree_C"}),
             'atm_humidity': (viking_data.wxt520['Ua'], {"units": "percent"}),
             'atm_pressure': (viking_data.wxt520['Pa'], {"units": "mbar"}),
             }
        )

        l.log('wxt520 data loaded.')

    if viking_data.ctd is not None:
        data.update(
            {'temperature': (viking_data.ctd['temperature'], {"units": "degree_C"}),
             'conductivity': (viking_data.ctd['conductivity'], {'units': 'S/m'}),
             'salinity': (viking_data.ctd['salinity'], {'units': 'PSU'}),
             'density': (viking_data.ctd['density'], {'units': 'kg/m**3'})}
        )
        l.log('Ctd data loaded.')

    elif viking_data.ctdo is not None:
        data.update(
            {'temperature': (viking_data.ctdo['temperature'], {"units": "degree_C"}),
             'conductivity': (viking_data.ctdo['conductivity'], {'units': 'S/m'}),
             'salinity': (viking_data.ctdo['salinity'], {'units': 'PSU'}),
             'dissolved_oxygen': (viking_data.ctdo['dissolved_oxygen'], {'units': 'umol/L'})}
        )
        l.log('Ctdo data loaded.')

    if viking_data.wph is not None:
        _serial_number = viking_data.wph['serial_number'][~viking_data.wph['serial_number'].mask][0]
        _model = viking_data.wph['model'][~viking_data.wph['model'].mask][0]
        _attrs = {'serial_number': _serial_number, 'model': _model}
        global_attrs.update({'ph_serial_number': _serial_number, 'ph_model': _model})
        data.update(
            {
                'ph': (viking_data.wph['ext_ph'], {**_attrs, **{"units": "NBS_scale"}}),
                'ph_temperature': (viking_data.wph['ph_temperature'], {**_attrs, **{"units": "degree_C"}})}
        )
        l.log('Wph data loaded.')

    if viking_data.triplet is not None:
        _serial_number = viking_data.triplet['serial_number'][~viking_data.triplet['serial_number'].mask][0]
        _model = viking_data.triplet['model_number'][~viking_data.triplet['model_number'].mask][0]
        _attrs = {'serial_number': _serial_number, 'model': _model}
        global_attrs.update({'triplet_serial_number': _serial_number, 'triplet_model': _model})

        data.update(
            {
                'scattering': (viking_data.triplet['scatter_calculated'], {**_attrs, **{"units": "/m", "wavelength": "700nm"}}), #ppb ?
                'chlorophyll': (viking_data.triplet['chloro_calculated'], {**_attrs, **{"units": "mg/m**3", "wavelength": "695nm"}}), #ug/L -> mg/m**3
                'fdom': (viking_data.triplet['fdom_calculated'], {**_attrs, **{"units": "ppb", "wavelength": "460nm"}}) #ppb
            }
        )
        l.log('Triplet data loaded.')

    if viking_data.par_digi is not None:
        _serial_number = viking_data.par_digi['serial_number'][~viking_data.par_digi['serial_number'].mask][0]
        _model = viking_data.par_digi['model_number'][~viking_data.par_digi['model_number'].mask][0]

        _attrs = {'serial_number': _serial_number, 'model': _model}
        global_attrs.update({'par_serial_number': _serial_number, 'par_triplet_model': _model})

        data['par'] = (viking_data.par_digi['PAR'], {**_attrs, **{"units": "umol/m**2/s"}})
        l.log('Par Digi data loaded.')

    if viking_data.co2_a is not None: # co2 partial pressure = (ppm / 1e6)* cell gas pressure
        data.update({'co2_air': (viking_data.co2_a['cell_gas_pressure_mbar'] * viking_data.co2_a['co2_ppm'] / 1e6,
                                 {'units': 'uatm'})})
        l.log('Co2_a data loaded.')

    if viking_data.co2_w is not None: # co2 partial pressure = (ppm / 1e6)* cell gas pressure
        data.update({'co2_water': (viking_data.co2_w['cell_gas_pressure_mbar'] * viking_data.co2_w['co2_ppm'] / 1e6,
                                   {'units': 'uatm'})})
        l.log('Co2_w data loaded.')

    if viking_data.wave_m is not None:
        data.update(
            {'wave_mean_height': (viking_data.wave_m['average_height'], {}),
             'wave_maximal_height': (viking_data.wave_m['maximal_height'], {}),
             'wave_period': (viking_data.wave_m['period'], {})}
        )
        l.log('Wave_m data loaded.')

    elif viking_data.wave_s is not None:
        _attrs = {'comments': 'Height values were truncated at the first decimal.\n'}
        data.update(
            {'wave_mean_height': (viking_data.wave_s['average_height'], _attrs),
             'wave_maximal_height': (viking_data.wave_s['Hmax'], _attrs),
             'wave_period': (viking_data.wave_s['dominant_period'], {}),
             'wave_direction': (viking_data.wave_s['direction'], {})}
        )
        l.log('Wave_s data loaded.')

    if viking_data.rdi is not None and viking_data.rti is not None:
        l.warning('Both RDI and RTI tag found in dataset.')
        _adcp_data = dict()
        # load RDI data
        for _name in ['u', 'v', 'w', 'e']:
            _adcp_data[_name] = viking_data.rdi[_name]

        if not any(~viking_data.rti['u'].mask & ~viking_data.rdi['u'].mask):
            l.warning('Merging RDI and RTI data')
            # load RTI data
            for _name in ['u', 'v', 'w', 'e']:
                _adcp_data[_name][~viking_data.rti[_name].mask] = viking_data.rti[_name][~viking_data.rti[_name].mask]

        else:
            l.warning('There is a time overlap between RDI and RTI data. RTI data were discarded.')


        for _name in ['u', 'v', 'w', 'e']:
            _adcp_data[_name].mask = viking_data.rti[_name].mask & viking_data.rdi[_name].mask
            data[_name] = (_adcp_data[_name] * MILLIMETER_TO_METER, {"units": "m/s"})

    else:
        if viking_data.rdi is not None:
            for _name in ['u', 'v', 'w', 'e']:
                data[_name] = (viking_data.rdi[_name] * MILLIMETER_TO_METER, {"units": "m/s"})
            l.log('Rdi data loaded.')

        if viking_data.rti is not None:
            for _name in ['u', 'v', 'w', 'e']:
                data[_name] = (viking_data.rti[_name] * MILLIMETER_TO_METER, {"units": "m/s"})
            l.log('Rti data loaded.')

    data = _fill_data(data)

    return data, global_attrs


def _load_mitis_meteoce_data(mitis_data: MitisData) -> Tuple[Dict[str, Tuple[np.ma.MaskedArray, dict]], Dict]:
    global_attrs = {}
    data = {
        'lon': (mitis_data.init['longitude'], {}),
        'lat': (mitis_data.init['latitude'], {}),
        'speed': (mitis_data.init['sog'] * KNOTS_TO_METER_PER_SECONDS, {}),
        'course': (mitis_data.init['cog'], {}),
        'magnetic_declination': (mitis_data.init['magnetic_declination'], {}),
        'heading': (mitis_data.init['heading'], {'corrections':'Corrected for magnetic declination at sampling.\n'}),
        'pitch': (mitis_data.init['pitch'], {}),
        'roll_': (mitis_data.init['roll'], {}),
        'pitch_std': (mitis_data.init['pitch_std'], {}),
        'roll_std': (mitis_data.init['roll_std'], {})
        }

    if mitis_data.eco1 is not None:
        data.update(
            {
                'scattering': (mitis_data.eco1['scattering'], {"units": "/m", "wavelength": "700nm"}),
                'chlorophyll': (mitis_data.eco1['chlorophyll'], {"units": "mg/m**3", "wavelength": "695nm"}), # ug/L -> mg/m**3
                'fdom': (mitis_data.eco1['fdom'], {"units": "ppb", "wavelength": "460nm"})# ppb
            }
        )
        l.log('Eco1 data loaded.')

    if mitis_data.ctd is not None:
        data.update(
                {'temperature': (mitis_data.ctd['temperature'], {"units": "degree_C"}),
                 'conductivity': (mitis_data.ctd['conductivity'], {'units': 'S/m'}),
                 'salinity': (mitis_data.ctd['salinity'], {'units': 'PSU'}),
                 'density': (mitis_data.ctd['density'], {'units': 'kg/m**3'})
             }
        )
        l.log('ctd data loaded.')

    if mitis_data.ph is not None:
        _ph_attrs ={
            "units": "NBS_scale",
            'corrections': 'pH values corrected at sampling using in-situ salinity.\n'
        }
        data.update({
            'ph': (mitis_data.ph['ext_ph'], _ph_attrs)
        })
        l.log('pH data loaded.')

    # if mitis_data.no3 is not None:
      # Nitrate Data are not loaded since the correction algorithm are not yet implemented.

    if mitis_data.wind is not None:
        mitis_data.wind['source'][:100] = '5'
        mitis_data.wind['source'][112:140] = 'nan'
        _s, _c = np.unique(mitis_data.wind['source'], return_counts=True)
        _counts = {k: round(100 * v/len(mitis_data.wind['source']),2) for k, v in zip(_s, _c)}

        if '5' in _counts and '7' in _counts: # 'nan could also be there a source. Meaning no data was sampled.
            _msg = f"Wind data were sampled by both the wmt700 ({_counts['7']}%), wxt536 ({_counts['5']}%)"
            if 'nan' in _s:
                _msg += f" (missing: {_counts['nan']}%)"
            l.warning(_msg +'.')

        data.update(
            {
                'wind_speed': (np.round(mitis_data.wind['wind_spd_ave'] * KNOTS_TO_METER_PER_SECONDS, 3), {'units': 'm/s'}),
                'wind_direction': (mitis_data.wind['wind_dir_ave'], {'corrections':'Corrected for magnetic declination at sampling.\n'}),
                'wind_gust': (np.round(mitis_data.wind['wind_spd_max'] * KNOTS_TO_METER_PER_SECONDS, 3), {'units': 'm/s'}),
            }
        )

        l.log('Wind Data Loaded')

    if mitis_data.atms is not None:
        data.update(
            {
                'atm_temperature': (mitis_data.atms['air_temperature'], {"units": "degree_C"}),
                'atm_humidity': (mitis_data.atms['air_humidity'], {"units": "percent"}),
                'atm_pressure': (mitis_data.atms['air_pressure'], {"units": "mbar"}),
             }
        )
        l.log('Atmospheric Data Loaded')

    if mitis_data.wave is not None:
        data.update(
            {
                'wave_mean_height': (mitis_data.wave['hm0'], {}), #CHECK IF THIS IS OK FIXME
                'wave_maximal_height': (mitis_data.wave['hmax'], {}),
                'wave_period': (mitis_data.wave['period'], {})
             }
        )
        l.log("Wave Data Loaded")

    if mitis_data.adcp is not None:
        data.update(
            {
                'u': (mitis_data.adcp['u'] * MILLIMETER_TO_METER, {"units": "m/s"}),
                'v': (mitis_data.adcp['v'] * MILLIMETER_TO_METER, {"units": "m/s"}),
                'w': (mitis_data.adcp['w'] * MILLIMETER_TO_METER, {"units": "m/s"}),
                'e': (mitis_data.adcp['e'] * MILLIMETER_TO_METER, {"units": "m/s"}),
            }
        )
        l.log('ADCP Data Loaded')


    if mitis_data.pco2 is not None:
        data.update(
            {
                'co2_air': (mitis_data.pco2['gas_pressure_air'] * mitis_data.pco2['co2_ppm_air'] / 1e6,
                            {{'units': 'uatm'}}),
                'co2_water': (mitis_data.pco2['gas_pressure_water'] * mitis_data.pco2['co2_ppm_water'] / 1e6,
                              {{'units': 'uatm'}})
             }
        )
        l.log('PCO2 Data Loaded')

    return data, global_attrs


def _add_time_coords(data: Dict[str, Tuple[np.ndarray, Dict]]) -> Dict[str, Tuple[List[str], np.ndarray, dict]]:
    """Add the time coords according to the Xarray data format."""
    for var, (_data, _attrs) in data.items():
        data[var] = (['time'], _data, _attrs)


def _fill_data(data: Dict[str, Tuple[np.ma.MaskedArray, dict]]) -> Dict[str, Tuple[List[str], np.ndarray, dict]]:
    """
    Fill the masked_array missing values with the predefined np.ma.MaskedArray filled value.

    Should be np.nan or 'nan'.

    See magtogoek.meteoce.viking_dat_reader.py for the filled value.
    """
    for var, (_data, _attrs) in data.items():
        data[var] = (_data.filled(), _attrs)

    l.log('Missing data filled.')


def _average_duplicates(dataset: xr.Dataset, coord: str) -> xr.Dataset:
    """Average data_array values of duplicates time coords index.
    """

    # average any duplicate value along coord by groupping according to coord value.
    df = dataset.to_dataframe()
    df = df.groupby(coord).mean(numeric_only=False)

    # get the subset of the dataset with all unique coord value.
    _dataset = dataset[{coord: np.unique(dataset[coord], return_index=True)[1]}]

    # replace values by the averaged (if duplicated coord index) values.
    for var in _dataset.keys():
        _dataset[var].values[:] = df[var][:]

    l.log('Duplicate timestamp data averaged.')
    return _dataset


if __name__ == "__main__":
    #filename = "/home/jeromejguay/ImlSpace/Projects/mitis-buoy-controller/tests/PMZA-RIKI_FileTAGS.dat"
    #filename = "/home/jeromejguay/ImlSpace/Projects/magtogoek/tests/data/mitis_raw/PMZA-RIKI_FileTAGS.dat"
    filename = "/home/jeromejguay/ImlSpace/Data/pmza_2023/IML-4/PMZA-RIKI_FileTAGS_2023.dat"
    ds = load_meteoce_data(filenames=filename, data_format='mitis')
