"""
Date: April 2022
Made by jeromejguay

Module that contains function to load meteoc variable into a dataset.


Notes
-----
[1] .. [March 2023] JeromeJGuay
    The function `_wind_and_wave_direction_correction' made to correct for a possible error in
    the Viking Buoy internal processing. That is, using a single heading measurements instead
    of a time average to set the wind and wave directions. The MO tag has this single heading
    measurements and thus needs to be loaded to make this correction.
    However, I'm not sure if this is actually the case at this point.

[2] .. [March 2023] JeromeJGuay
    The WXT wind measurements are less accurate than the wmt700. Furthermore, the WXT520
    is more likely to malfunction and not send data while the WMT700 always work.

[3] .. [March 2023] JeromeJGuay
    GPS bearing and course data seem to be bad. We believe that the bearing and course data are instant measurements.
    Thus wave induced rapid horizontal oscillation and the rocking of the buoy, the GPS being located about ~2-3 meters
    above the floating line, result in higher oscillation and amplitude in the speed values. Since speed dependent values
    are average over ~ 1 minutes, we need at least ~1 minutes average values from the gps.


"""

from magtogoek.meteoce.viking_dat_reader import RawVikingDatReader, VikingData
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
        data_format: str = 'viking_dat',
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

    if data_format == "viking_dat":
        dataset = load_viking_data(filenames=filenames, buoy_name=buoy_name)
    else:
        l.warning('Invalid data_format.')
        raise ValueError

    l.log('Data Loaded.')

    return dataset


def load_viking_data(
        filenames: Tuple[str, List[str]],
        buoy_name: str = None,
        ) -> xr.Dataset:

    l.log(format_filenames_for_print('raw_data', filenames))

    buoys_data = RawVikingDatReader().read(filenames)

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

    meteoce_data = get_viking_meteoce_data(viking_data)

    coords = {'time': np.asarray(viking_data.time)}

    global_attrs = {
        'buoy_name': viking_data.buoy_name,
        'firmware': viking_data.firmware,
        'controller_serial_number': viking_data.controller_sn
    }

    meteoce_data = _fill_data(meteoce_data)

    dataset = xr.Dataset(meteoce_data, coords=coords, attrs=global_attrs)

    dataset = _average_duplicates(dataset, 'time')

    # See note 1 in module docstring
    #
    #_wind_and_wave_direction_correction(dataset=meteoce_data) # Seem to be already using the average heading afterall

    dataset.attrs['logbook'] = l.logbook

    return dataset


def get_viking_meteoce_data(viking_data: VikingData) -> Dict[str, Tuple[np.ma.MaskedArray, dict]]:
    _data = {'lon': (viking_data.longitude, {}),
             'lat': (viking_data.latitude, {}),
             }

    if viking_data.gps is not None:
        _data.update(
            {'speed': (np.round(viking_data.gps['speed'] * KNOTS_TO_METER_PER_SECONDS, 3), {"units": "m/s"}),
             'course': (viking_data.gps['course'], {}),
             'gps_magnetic_declination': (viking_data.gps['variation_E'], {})}
        )
        l.log('Gps data loaded.')

    if viking_data.comp is not None:
        _data.update(
            {'heading': (viking_data.comp['heading'], {}),
             'pitch': (viking_data.comp['pitch'], {}),
             'roll_': (viking_data.comp['roll'], {}),
             'pitch_std': (viking_data.comp['pitch_std'], {}),
             'roll_std': (viking_data.comp['roll_std'], {})}
        )
        l.log('Comp data loaded.')

    if viking_data.wmt700 is not None:
        _data.update(
            {'mean_wind_speed': (np.round(viking_data.wmt700['Sm'] * KNOTS_TO_METER_PER_SECONDS, 3), {'units': 'm/s'}),
             'mean_wind_direction': (viking_data.wmt700['Dm'], {}),
             'max_wind_speed': (np.round(viking_data.wmt700['Sx'] * KNOTS_TO_METER_PER_SECONDS, 3), {'units': 'm/s'}),
             'max_wind_direction': (viking_data.wmt700['Dx'], {})}
        )
        l.log('wmt700 data loaded.')

    if viking_data.wxt520 is not None:
        _data.update(
            {'atm_temperature': (viking_data.wxt520['Ta'], {}),
             'atm_humidity': (viking_data.wxt520['Ua'], {}),
             'atm_pressure': (viking_data.wxt520['Pa'], {"units": "mbar"}),
             #'wxt_mean_wind': (np.round(viking_data.wxt520['Sm'] * KNOTS_TO_METER_PER_SECONDS, 3), {'units': 'm/s'}), # For test
             #'wxt_mean_wind_direction': (viking_data.wxt520['Dm'], {}),
             }
        )

        # See note 2 in the module docstring.
        #
        # A parameter could be added to choose where to load wind data from.
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
                'ph': (viking_data.wph['ext_ph'], {**_attrs, **{"units": "pH_NBS_scale"}}),
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
        _attrs = {'comments': 'Height values were truncated at the first decimal.\n'}
        _data.update(
            {'wave_mean_height': (viking_data.wave_s['average_height'], _attrs),
             'wave_maximal_height': (viking_data.wave_s['Hmax'], _attrs),
             'wave_period': (viking_data.wave_s['dominant_period'], {}),
             'wave_direction': (viking_data.wave_s['direction'], {})}
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

    # Useless since it returns only the amplitude of the current along the heading axis.
    #
    # if viking_data.debit is not None:
    #     _data.update(
    #         {'surface_current': (viking_data.debit['flow'], {})}
    #     )

    # See note [1] in module docstring.
    #
    # if viking_data.mo is not None:
    #     _data['last_heading'] = (viking_data.mo['heading'], {})
    #     l.log('Mo heading loaded.')

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


# See note [1] in module docstring.
#
# def _wind_and_wave_direction_correction(dataset: xr.Dataset):
#     """Fix direction for Wind and Wave.
#
#     The Viking Buoy V1 uses the last measured heading value to compute the
#     wind and wave direction instead of the average value of the measurement period.
#
#     The last measured heading value is sent in the `MO` tag and are used to get the
#     raw directions values from the Wind and Wave.
#
#     The correct Wave and Wind directions are then computed using the average heading value.
#     """
#     direction_to_correct = ['wave_direction', 'mean_wind_direction', 'max_wind_direction']
#     if all(var in dataset.variables for var in ['last_heading', 'heading']):
#         heading = (dataset['heading'] + 360) % 360 # [-180, 180[ -> [0, 360[
#         for variable in set(dataset.variables).intersection(set(direction_to_correct)):
#             dataset[variable].values = (dataset[variable] - dataset['last_heading'] + heading).values % 360
#             l.log(f'{variable} data corrected using the average heading.')


if __name__ == "__main__":
    #vr = RawVikingDatReader()
    #_buoys_data = vr.read(['/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'])

    #v_data = _buoys_data['pmza_riki']

    #ds = load_meteoce_data(['/home/jeromejguay/ImlSpace/Data/iml4_2021/dat/PMZA-RIKI_RAW_all.dat'])
    #ds.to_netcdf('/home/jeromejguay/ImlSpace/Data/iml4_2021/meteoce_riki_2021.nc')

    ds = xr.open_dataset('/home/jeromejguay/ImlSpace/Data/iml4_2021/meteoce_riki_2021.nc')
