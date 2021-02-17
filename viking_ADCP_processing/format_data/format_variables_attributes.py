"
author: Jérôme Guay
date: Feb. 16, 2021

var:
-serial_number: if sensor_type == 'adcp'.
- data_min, data_max
- sensor_depth,
- ancillary_variables (in _QC function)

time:
-units = seconds since 1992-10-8 15:15:42.5 -6:00


"""

"""
"""
import typing as tp

def make_QCvar_attrs(P01_var_name: str,
                     comments: str) -> tp.Dict[str, tp.Tuple[str, tp.List]]:
    """Returns attributes for QC variables.

    Parameters:
    -----------

        P01_var_name:
            long_name = 'Quality flag for ' + P01_var_name

        comments:
            Something like: 'Quality flag resulting from ...'
    """
    return dict(long_name=f'Quality flag for {P01_var_name}',
                comments=comments,
                flag_meanings=('no_quality_control, '
                               'good_value, '
                               'probably_good_value, '
                               'probably_bad_value, '
                               'bad_value, '
                               'changed_value,'
                               'value_below_detection, '
                               'value_in_excess, '
                               'interpolated_value, '
                               'missing_value'),
                flag_values='0, 1, 2, 3, 4, 5, 6, 7, 8, 9',
                References='BODC SeaDataNet')
