"""
author: Jérôme Guay
date: Feb. 12, 2021

Script:
Use the adcp_template.nc to make a to make the .csv fileo to store the variables and
coords attributes.
Variables are stored with their BODC name.

TODO:
- write out de conventions for time
- write out conventions for coords
- csv exporter.
- accillary variables as a function to add it.
- make a second script for all the set something ...
"""
import typing as tp
import numpy as np
import xarray as xr


def L_AP01(s0: str, s1: str, s2: str, s3: str) -> tp.Dict[str, str]:
    """skeleton for L(--)AP01 attributes dictionnary"""
    return dict(
        standard_name=f'{s0}ward_sea_water_velocity',
        units='m s-1',
        long_name=f'{s0}ward_sea_water_velocity',
        # ancillary_variables = f'{s1}_QC',
        sdn_parameter_urn=f'SDN:P01::{s1}',
        sdn_parameter_name=(f'{s2}ward current velocity '
                            + '(Eulerian measurement) in the water body '
                            + 'by moored  acoustic doppler current profiler '
                            + '(ADCP)'),
        sdn_uom_urn='SDN:P06::UVAA',
        sdn_uom_name='Metres per second',
        legacy_GF3_code=f'SDN:GF3::{s3}'
    )


def TNIHCE(s0: str) -> tp.Dict[str, str]:
    """skeleton for TNIHCE(-) attributes dictionnary"""
    return dict(
        units='counts',
        long_name=f'ADCP_echo_intensity_beam_{s0}',
        sdn_parameter_urn=f'SDN:P01::TNIHCE0{s0}',
        sdn_parameter_name=('Echo intensity from the water body by moored '
                            + f'acoustic doppler current profiler (ADCP) beam {s0}'),
        sdn_uom_urn='SDN:P06::UCNT',
        sdn_uom_name='Counts',
        legacy_GF3_code=f'SDN:GF3::BEAM_0{s0}'
    )


def CMAGZZ(s0: str) -> tp.Dict[str, str]:
    """skeleton for CMAGZZ(-) attributes dictionnary"""
    return dict(
        units='counts',
        long_name=f'ADCP_correlation_magnitude_beam_{s0}',
        sdn_parameter_urn=f'SDN:P01::CMAGZZ0{s0}',
        sdn_parameter_name=('Correlation magnitude of acoustic signal returns '
                            + 'from the water body by moored acoustic doppler '
                            + f'current profiler (ADCP) beam {s0}'),
        legacy_GF3_code=f'SDN:GF3::CMAG_0{s0}'
    )


def PCGDAP(s0: str, s1: str) -> tp.Dict[str, str]:
    """skeleton for PCGDAP(-) attributes dictionnary"""
    return dict(
        units='percent',
        long_name=f'percent_good_beam_{s0}',
        sdn_parameter_urn=f'SDN:P01::{s1}',
        sdn_parameter_name=('Acceptable proportion of signal returns '
                            + 'by moored acoustic doppler current profiler '
                            + f'(ADCP) beam {s0}'),
        sdn_uom_urn='SDN:P06::UPCT',
        sdn_uom_name='Percent',
        legacy_GF3_code=f'SDN:GF3::PGDP_0{s0}'
    )


def A_ZZ01(s0: str, s1: str, s2: str,
           s3: str, s4: str, s5: str) -> tp.Dict[str, str]:
    """skeleton for A(---)ZZ01 attributes dictionnary"""
    return dict(
        standard_name=f'{s0}',
        units=f'degrees_{s1}',
        long_name=f'{s0}',
        sdn_parameter_urn=f'SDN:P01::A{s2}ZZ01',
        sdn_parameter_name=f'{s3} {s1}',
        sdn_uom_urn=f'SDN:P06::{s4}',
        sdn_uom_name=f'Degrees {s1}',
        legacy_GF3_code=f'SDN:GF3::{s5}'
    )


"""--- Varaibles attributes are define below ---"""

LCEWAP01 = L_AP01('east', 'LCEWAP01', 'East', 'EWCT')
LCNSAP01 = L_AP01('north', 'LCNSAP01', 'North', 'NWCT')
LRZAAP01 = L_AP01('up', 'LRZAAP01', 'Up', 'VCSP')

LERRAP01 = dict(
    units='m s-1',
    long_name='error_velocity_in_sea_water',
    # ancillary_variables='LERRAP01_QC',
    sdn_parameter_urn='SDN:P01::LERRAP01',
    sdn_parameter_name=('Current velocity error in the water '
                        + 'body by moored acoustic doppler current profiler (ADCP)'),
    sdn_uom_urn='SDN:P06::UVAA',
    sdn_uom_name='Metres per second',
    legacy_GF3_code='SDN:GF3::ERRV'
)


TNIHCE01 = TNIHCE('1')
TNIHCE02 = TNIHCE('2')
TNIHCE03 = TNIHCE('3')
TNIHCE04 = TNIHCE('4')

CMAGZZ01 = CMAGZZ('1')
CMAGZZ02 = CMAGZZ('2')
CMAGZZ03 = CMAGZZ('3')
CMAGZZ04 = CMAGZZ('4')

PCGDAP00 = PCGDAP('1', 'PCGDAP00')
PCGDAP02 = PCGDAP('2', 'PCGDAP02')
PCGDAP03 = PCGDAP('3', 'PCGDAP03')
PCGDAP04 = PCGDAP('4', 'PCGDAP04')

ALATZZ01 = A_ZZ01('latitude', 'north', 'LAT', 'Latitude', 'DEGN', 'lat')
ALONZZ01 = A_ZZ01('longitude', 'east', 'LON', 'Longitude', 'DEGE', 'lon')

PTCHGP01 = dict(
    standard_name='platform_pitch',
    units='degree',
    long_name='pitch',
    sdn_parameter_urn='SDN:P01::PTCHGP01',
    sdn_parameter_name='Orientation (pitch) of measurement platform by inclinometer',
    sdn_uom_urn='SDN:P06::UAAA',
    sdn_uom_name='Degrees',
    legacy_GF3_code='SDN:GF3::PTCH'
)
HEADCM01 = dict(
    standard_name='platform_orientation',
    units='degree',
    long_name='heading',
    sdn_parameter_urn='SDN:P01::HEADCM01',
    sdn_parameter_name=('Orientation (horizontal relative to true north) of '
                        + 'measurement device {heading}'),
    sdn_uom_urn='SDN:P06::UAAA',
    sdn_uom_name='Degrees',
    legacy_GF3_code='SDN:GF3::HEAD'
)
ROLLGP01 = dict(
    standard_name='platform_roll',
    units='degree',
    long_name='roll',
    sdn_parameter_urn='SDN:P01::ROLLGP01',
    sdn_parameter_name=('Orientation (roll angle) of measurement platform '
                        + 'by inclinometer (second sensor)'),
    sdn_uom_urn='SDN:P06::UAAA',
    sdn_uom_name='Degrees',
    legacy_GF3_code='SDN:GF3::ROLL'
)
SVELCV01 = dict(
    standard_name='speed_of_sound_in_sea_water',
    units='m s-1',
    long_name='speed of sound',
    sdn_parameter_urn='SDN:P01::SVELCV01',
    sdn_parameter_name=('Sound velocity in the water body by computation from '
                        + 'temperature nd salinity by unspecified algorithm'),
    sdn_uom_urn='SDN:P06::UVAA',
    sdn_uom_name='Metres per second',
    legacy_GF3_code='SDN:GF3::SVEL'
)
TEMPPR01 = dict(
    units='degree_C',
    long_name='ADCP Transducer Temp.',
    sdn_parameter_urn='SDN:P01::TEMPPR01',
    sdn_parameter_name='Temperature of the water body',
    sdn_uom_urn='SDN:P06::UPAA',
    sdn_uom_name='Celsius degree',
    legacy_GF3_code='SDN:GF3::te90'
)
DISTTRAN = dict(
standard_name': 'None',
units': 'm',
long_name': 'height of sea surface',
ancillary_variables': 'None',
sdn_parameter_urn': 'SDN:P01::DISTTRAN',
sdn_parameter_name': 'None',
sdn_uom_urn': 'SDN:P06::ULAA',
sdn_uom_name': 'Metres',
legacy_GF3_code': 'SDN:GF3::HGHT'}
)
PPSAADCP = dict()
DTUT8601 = dict()

# ADEPZZ01 #BIO

dependant_attrs = dict(data_min=None,
                       data_max=None,
                       sensor_type='',
                       sensor_depth=None,
                       generic_name='',
                       serial_number='')

flags_attrs = dict(long_name='Quality flag for ',
                   comments='Quality flag resulting from ',
                   flag_meanings=':'.join(['no_quality_control',
                                           'good_value',
                                           'probably_good_value',
                                           'probably_bad_value',
                                           'bad_value',
                                           'changed_value',
                                           'value_below_detection',
                                           'value_in_excess',
                                           'interpolated_value',
                                           'missing_value']),
                   flag_values=':'.join(np.arange(10).astype(str)),
                   References='BODC SeaDataNet',)

vertical_coords_attrs = dict(positive='')

time_coords_attrs = dict(calendar='gregorian',
                         cf_role='profile_id')

P01_var_name = ['LCEWAP01', 'LCNSAP01', 'LRZAAP01', 'LERRAP01',
                'TNIHCE01', 'TNIHCE02', 'TNIHCE03', 'TNIHCE04',
                'CMAGZZ01', 'CMAGZZ02', 'CMAGZZ03', 'CMAGZZ04',
                'PCGDAP00', 'PCGDAP02', 'PCGDAP03', 'PCGDAP04',
                'ALATZZ01', 'ALONZZ01',
                'PTCHGP01', 'HEADCM01', 'ROLLGP01',
                'PRESPR01',
                'DTUT8601',
                'SVELCV01', 'TEMPPR01', 'DISTTRAN', 'PPSAADCP'
                # ADEPZZ01, # bottom track depth ? in BIO nc.]


P01_flags_name = ['LCEWAP01_QC', 'LCNSAP01_QC', 'LRZAAP01_QC', 'PRESPR01_QC']

attrs_list = ['standard_name',
              'units',
              'long_name',
              'ancillary_variables',
              'sdn_parameter_urn', #P01, BODC
              'sdn_parameter_name',
              'sdn_uom_urn', #P06
              'sdn_uom_name',
              'legacy_GF3_code']
# platform_speed_wrt_ground : standard_name
# APEWGP01 APNSGP01


def get_vars_attrs(dataset, attrs_list):
    """
    """
    vars_attrs = dict()
    for attr in attrs_list:
        vars_attrs[attr] = get_attr(dataset, attr)

    return vars_attrs


def get_attr(dataset, attr):
    """
    """
    var_attr = dict()
    for var in dataset.var():
        try:
            var_attr[var] = dataset[var].attrs[attr]
        except KeyError:
            var_attr[var] = 'None'

    return var_attr

def parameter_urn_attr(P01_var_name):
    """
    """
    sdn_parameter_urn = dict()
    for var in P01_var_name:
        sdn_parameter_urn[var] = 'SDN:P01::'+var

    return sdn_parameter_urn



if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    import xarray as xr

    fn_IOS = '/home/jeromejguay/ImlSpace/Projects/' +\
        'pycurrents_ADCP_processing/' +\
        'ncdata/a1_20050503_20050504_0221m.adcp.L1.nc'

    fn_BIO = '/home/jeromejguay/ImlSpace/Data/BIO/' +\
        'MADCPS_HUD2013037_1854_14074_1800.nc'


    ds = xr.open_dataset(fn_IOS)
    var_attrs = get_vars_attrs(ds, attrs_list)
    var_attrs['sdn_parameter_urn'] = parameter_urn_attr(P01_var_name)

    df = pd.DataFrame(var_attrs).fillna('None').T
    var_attrs = df.to_dict()

    for flag in P01_flags_name:
        var_attrs[flag] = {**var_attrs[flag], **flags_attrs}
        var_attrs[flag]['long_name'] += flag.split('_')[0]

    df = pd.DataFrame(var_attrs).fillna('None')

    df.to_csv('viking_adcp_attributes.csv')
