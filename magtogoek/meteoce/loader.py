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

from magtogoek.meteoce.viking_dat_reader import RawVikingDatReader, VikingData
import numpy as np
import xarray as xr
from typing import *

import magtogoek.logger as l
from magtogoek.exceptions import MagtogoekExit
from magtogoek.utils import format_filenames_for_print
from magtogoek.tools import is_unique, nan_unique

import pint_xarray # pint_xarray modify the xr.Dataset Object


KNOTS_TO_METER_PER_SECONDS = 1 / 1.944   # 1 kt = (1/1.944) m/s
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
    l.section('Loading meteoce data')

    if data_format == "viking":
        dataset = load_viking_data(filenames=filenames, buoy_name=buoy_name)
    else:
        l.warning(f'Invalid data_format: {data_format}')
        raise MagtogoekExit("Invalid meteoce data format. Exiting")
    l.log('Data Loaded.')

    return dataset


def load_viking_data(
        filenames: Union[str, List[str]],
        buoy_name: str = None,
        ) -> xr.Dataset:

    l.log(format_filenames_for_print('raw_data', filenames))

    viking_data = RawVikingDatReader().read(filenames)

    if isinstance(viking_data, Dict):
        l.warning(f'More than one buoy name was found in the file {filenames}.\n Buoy names fround: {list(viking_data.keys())} \n Specify a buoy_name\n Exiting')
        raise MagtogoekExit(f'More than one buoy was found in the file {filenames}. Exiting')

    if buoy_name is not None and viking_data.buoy_name != buoy_name:
        l.log(f'Buoy Name found in files is different from the one provided.')

    meteoce_data, global_attrs = _load_viking_meteoce_data(viking_data)

    meteoce_data = _fill_data(meteoce_data)

    coords = {'time': np.asarray(viking_data.time)}

    global_attrs.update({
        'platform': viking_data.buoy_name,
        'buoy_controller_firmware_version': viking_data.firmware,
        'buoy_controller_serial_number': list(set(viking_data.controller_sn))
    })

    dataset = xr.Dataset(meteoce_data, coords=coords, attrs=global_attrs)

    dataset = _average_duplicates(dataset, 'time')

    if is_unique(dataset['magnetic_declination']):
        dataset.attrs["magnetic_declination"] = nan_unique(dataset['magnetic_declination'])[0]
        dataset.attrs["magnetic_declination_units"] = "degree east"
        dataset = dataset.drop_vars('magnetic_declination')

    dataset.attrs['logbook'] = l.logbook

    return dataset


def _load_viking_meteoce_data(viking_data: VikingData) -> Tuple[Dict[str, Tuple[np.ma.MaskedArray, dict]], Dict]:
    """

    Parameters
    ----------
    viking_data

    Returns
    -------
        {variable_name: str -> (data: np.ma.MaskedArray, attributes: Dict)}

    """
    global_attrs = {}
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
                'ph_temperature': (viking_data.wph['ext_ph'], _attrs)}
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
        data.update({'co2_a': (viking_data.co2_a['cell_gas_pressure_mbar'] * viking_data.co2_a['co2_ppm'] / 1e6, {})})
        l.log('Co2_a data loaded.')

    if viking_data.co2_w is not None: # co2 partial pressure = (ppm / 1e6)* cell gas pressure
        data.update({'co2_w': (viking_data.co2_w['cell_gas_pressure_mbar'] * viking_data.co2_w['co2_ppm'] / 1e6, {})})
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

            # NOTES should be added as a global attributes by the user
            # _bin = viking_data.rti['bin'][~viking_data.rti['bin'].mask]
            # _bin_position_cm = viking_data.rti['position_cm'][~viking_data.rti['position_cm'].mask] * CENTIMETER_TO_METER
            #
            # _bin = np.nanmean(_bin)
            # _bin_position_cm = np.round(np.nanmean(_bin_position_cm), 2)
            #_attrs = {'bin': _bin, 'bin_position_cm': _bin_position_cm}
            #global_attrs.update({'adcp_bin': _bin, 'adcp_bin_position_cm': _bin_position_cm})

            for _name in ['u', 'v', 'w', 'e']:
                data[_name] = (viking_data.rti[_name] * MILLIMETER_TO_METER, {"units": "m/s"})
            l.log('Rti data loaded.')

    return data, global_attrs


def _fill_data(data: Dict[str, Tuple[np.ma.MaskedArray, dict]]) -> Dict[str, Tuple[List[str], np.ndarray, dict]]:
    """
    Fill the masked_array missing values with the predefined np.ma.MaskedArray filled value.

    Should be np.nan or 'nan'.

    See magtogoek.meteoce.viking_dat_reader.py for the filled value.
    """
    _data = {}
    for key, item in data.items():
        _data[key] = (['time'], item[0].filled(), item[1])

    l.log('Missing data filled.')

    return _data


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
    #vr = RawVikingDatReader()
    #_buoys_data = vr.read(['/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'])

    #v_data = _buoys_data['pmza_riki']

    #ds = load_meteoce_data(['/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'])
    #ds.to_netcdf('/home/jeromejguay/ImlSpace/Data/iml4_2021/meteoce_riki_2021.nc')

    # ds = xr.open_dataset('/home/jeromejguay/ImlSpace/Data/iml4_2021/meteoce_riki_2021.nc')
    pass
