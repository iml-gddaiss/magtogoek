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
"""
#import typing as tp
import numpy as np
import xarray as xr


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
                'PTCHGP01', 'HEADCM01', 'ROLLGP01',
                'TEMPPR01', 'DISTTRAN', 'PPSAADCP',
                'ALATZZ01', 'ALONZZ01',
                'PRESPR01',
                'SVELCV01',
                'PCGDAP00', 'PCGDAP02', 'PCGDAP03', 'PCGDAP04']

P01_flags_name = ['LCEWAP01_QC', 'LCNSAP01_QC', 'LRZAAP01_QC', 'PRESPR01_QC']

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

    attrs_list = ['standard_name',
                  'units',
                  'long_name',
                  'ancillary_variables',
                  'sdn_parameter_urn', #P01, BODC
                  'sdn_parameter_name',
                  'sdn_uom_urn', #P06
                  'sdn_uom_name',
                  'legacy_GF3_code']

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
