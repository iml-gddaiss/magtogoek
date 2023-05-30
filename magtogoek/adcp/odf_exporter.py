"""
module to map xarray dataset to Odf
"""
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import xarray as xr
from typing import List, Union, Tuple, Dict, Optional
from magtogoek import CONFIGURATION_PATH
from magtogoek.odf_format import Odf, odf_time_format, ODF_PARAMETERS_TYPES
from magtogoek.platforms import PlatformMetadata, Sensor
from magtogoek.utils import json2dict

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

ADCP_SENSORS_COMMENTS = {
    'pres': {'sensor': 'PRESSURE_SENSOR_01', 'comments': {'CODE': 'DEPH_01', 'Name': 'pressure'}},
    'heading': {'sensor': 'COMPAS_SENSOR_01', 'comments': {'CODE': 'HEAD_01', 'Name': 'compas'}},
    'roll_': {'sensor': 'INCLINOMETER_SENSOR_01', 'comments': {'CODE': 'ROLL_01', 'Name': 'tilt'}},
    'temperature': {'sensor': 'TEMPERATURE_SENSOR_01', 'comments': {'CODE': 'TE90_01', 'Name': 'temperature'}}
}


BEAM_PARAMETERS = ("time", "depth", "v1", "v2", "v3", "v4")
VEL_PARAMTERS = ("time", "depth", "u", "v", "w", "e")
ANC_PARAMTERS = ('time', 'pitch', 'roll_', 'heading', 'pres', 'temperature', 'lon', 'lat')
QC_PARAMETERS = ('u', 'v', 'w', 'pres', 'temperature')

PARAMETERS_METADATA_PATH = CONFIGURATION_PATH.joinpath("odf_parameters_metadata.json")
PARAMETERS_METADATA = json2dict(PARAMETERS_METADATA_PATH)


def make_odf(
        dataset: xr.Dataset,
        platform_metadata: PlatformMetadata,
        sensor_id: str,
        #sensors_id: Dict[str, str],
        #sensors_to_parameters_map: Dict[str, List[str]],  # could be changed to sensors_id {'adcp': `sensor_id`}
        config_attrs: dict,
        p01_codes_map: dict,
        #generic_variables_name: List[str],
        bodc_name: bool = True,
        event_qualifier2: str = 'VEL',
        output_path: Optional[str] = None, ):
    """

    FIXME:
    - generic variable names could be change for `sensor_to_parameters_map`
    - then change sensor_id for a dict of sensor_id_to_sensor_type map
    - then have a more general make_odf function


    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    platform_metadata :
        Metadata from the platform file.
    sensor_id :

    config_attrs :
        Global attributes parameter from the configFile.
    generic_variables_name :
        List of the generic name fo the variables. Python variables used in the code.
    bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    event_qualifier2:
        Either `'VEL'` or `'ANC'`.
    output_path:
        If a path(str) is provided, there is two possibilities: if the path is only a directory, the file name
        will be made from the odf['file_specification']. If a file name is also provided, the 'event_qualifier2'
        will be appended to it if it's not present in the `output_path`.

    """
    odf = Odf()

    _make_cruise_header(odf, platform_metadata, config_attrs)
    _make_event_header(odf, dataset, config_attrs, event_qualifier2, p01_codes_map)
    _make_odf_header(odf)

    if platform_metadata.platform.platform_type == "buoy":
        _add_buoy_instrument_headers(odf, platform_metadata)
        _make_adcp_buoy_instrument_comments(odf, sensor_id, dataset, platform_metadata)
        #_make_buoy_header(odf, platform_metadata)
        #_make_adcp_buoy_instrument_header(odf, dataset, platform_metadata, sensor_id, generic_variables_name)
        #_make_other_buoy_instrument_header(odf, platform_metadata)
    else:
        _make_instrument_header(odf, dataset)

    _make_quality_header(odf, dataset)
    _make_history_header(odf, dataset)

    if event_qualifier2 == 'VEL':
        if dataset.attrs['coord_system'] == 'beam':
            parameters = BEAM_PARAMETERS
        else:
            parameters = VEL_PARAMTERS
    else:
        parameters = ANC_PARAMTERS

    _make_parameter_headers(odf, dataset, parameters, bodc_name)

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path.joinpath(odf.odf["file_specification"])
        else:
            if event_qualifier2 not in output_path.name:
                output_path = Path(str(output_path.with_suffix('')) + f'_{event_qualifier2}')
            odf.odf["file_specification"] = output_path.name

        output_path = Path(output_path).with_suffix(".ODF")
        odf.save(output_path)
        print(f"odf {event_qualifier2.upper()} file made -> {output_path}")

    return odf


def _make_cruise_header(odf: Odf, platform_metadata: PlatformMetadata, config_attrs: dict):
    odf.cruise["country_institute_code"] = config_attrs["country_institute_code"]
    odf.cruise["organization"] = config_attrs["organization"]
    odf.cruise["chief_scientist"] = config_attrs["chief_scientist"]
    odf.cruise["start_date"] = odf_time_format(config_attrs["start_date"])
    odf.cruise["end_date"] = odf_time_format(config_attrs["end_date"])
    odf.cruise["cruise_number"] = config_attrs["cruise_number"]
    odf.cruise["cruise_name"] = config_attrs["cruise_name"]
    odf.cruise["cruise_description"] = config_attrs["cruise_description"]

    odf.cruise["platform"] = platform_metadata.platform.platform_name
    if platform_metadata.platform.platform_type == "buoy":
        odf.cruise["platform"] = "Oceanographic Buoy"


def _make_event_header(odf, dataset, config_attrs, event_qualifier2, p01_codes_map: dict):
    """
    Make the event header.

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    odf.event['data_type'] = dataset.attrs['data_type'].upper()
    odf.event["creation_date"] = odf_time_format(datetime.now())
    odf.event['orig_creation_date'] = odf_time_format(dataset.attrs['date_created'])
    if 'delta_t_sec' in dataset.attrs:
        odf.event['sampling_interval'] = dataset.attrs['delta_t_sec']
    odf.event["event_number"] = config_attrs["event_number"]
    odf.event["event_qualifier1"] = config_attrs["event_qualifier1"]
    odf.event["event_qualifier2"] = event_qualifier2
    if 'sounding' in dataset.attrs:
        odf.event['sounding'] = dataset.attrs['sounding']
    odf.event["event_comments"] = config_attrs["event_comments"]
    _set_event_header_geospatials(odf, dataset, p01_codes_map)


def _set_event_header_geospatials(odf: Odf, dataset: xr.Dataset, p01_codes_map: dict) -> None:
    """ Set geospatial metadata from dataset.

    Sets :
     - initial_latitude, end_latitude
     - initial_latitude, end_longitude
     - depth_off_bottom

    Parameters
    ----------
    odf :
    dataset :
    """
    odf.event['start_date_time'] = odf_time_format(dataset.time.values.min())
    odf.event['end_date_time'] = odf_time_format(dataset.time.values.max())

    if odf.event['event_qualifier2'] == 'ANC':
        if 'xducer_depth' in dataset:
            odf.event['min_depth'] = dataset['xducer_depth'].values.min()
            odf.event['max_depth'] = dataset['xducer_depth'].values.max()
        elif p01_codes_map['xducer_depth'] in dataset:
            odf.event['min_depth'] = dataset[p01_codes_map['xducer_depth']].values.min()
            odf.event['max_depth'] = dataset[p01_codes_map['xducer_depth']].values.max()
        else:
            odf.event['min_depth'] = dataset.attrs['sensor_depth']
            odf.event['max_depth'] = dataset.attrs['sensor_depth']
    else:
        odf.event['min_depth'] = dataset.depth.values.min()
        odf.event['max_depth'] = dataset.depth.values.max()

    if "lat" in dataset and "lon" in dataset:
        odf.event["initial_latitude"] = dataset.lat.values[0]
        odf.event["end_latitude"] = dataset.lat.values[-1]
        odf.event["initial_longitude"] = dataset.lon.values[0]
        odf.event["end_longitude"] = dataset.lon.values[-1]
    elif "latitude" in dataset.attrs and "longitude" in dataset.attrs:
        odf.event["initial_latitude"] = dataset.attrs["latitude"]
        odf.event["end_latitude"] = dataset.attrs["latitude"]
        odf.event["initial_longitude"] = dataset.attrs["longitude"]
        odf.event["end_longitude"] = dataset.attrs["longitude"]

    odf.event["depth_off_bottom"] = 0
    if odf.event["sounding"] is not None:
        odf.event["depth_off_bottom"] = odf.event['sounding'] - odf.event['max_depth']


def _make_odf_header(odf):
    """
    Make field specification with:
    data_type, cruise_number, event_number, event_qualifier1, event_qualifier2
    Joins with `_` and add the extension `.ODF`.
    """
    name_part = [
        odf.event["data_type"],
        odf.cruise["cruise_number"],
        odf.event["event_number"],
        odf.event["event_qualifier1"],
        odf.event["event_qualifier2"],
    ]

    odf.odf["file_specification"] = "_".join(name_part).strip("_").upper() + ".ODF"


def _make_instrument_header(odf, dataset):
    """
    inst_type
    model
    serial_number
    description
    """
    key_map = [
        ("inst_type", "manufacturer"),
        ("description", "comments"),
        ("model", "model"),
        ("serial_number", "serial_number")
    ]

    for (odf_key, netcdf_key) in key_map:
        if netcdf_key in dataset.attrs:
            odf.instrument[odf_key] = dataset.attrs[netcdf_key]


def _make_buoy_header(odf: Odf, platform_metadata: PlatformMetadata):
    """
    Uses values in the Buoy_Specs section of the platform_file.
    """
    odf.buoy["name"] = platform_metadata.platform.platform_name or ''
    odf.buoy['type'] = platform_metadata.buoy_specs.type or ''
    odf.buoy['model'] = platform_metadata.buoy_specs.model or ''
    odf.buoy['height'] = platform_metadata.buoy_specs.height or ''
    odf.buoy['diameter'] = platform_metadata.buoy_specs.diameter or ''
    odf.buoy['weight'] = platform_metadata.buoy_specs.weight or ''
    odf.buoy['description'] = platform_metadata.buoy_specs.description or ''


def _make_adcp_buoy_instrument_header(
        odf: Odf, dataset: xr.Dataset,
        platform_metadata: PlatformMetadata,
        sensor_id: str,
        generic_variables_name: List[str]
):
    """

    Parameters
    ----------
    odf
    dataset
    platform_metadata
    sensor_id
    generic_variables_name :
        List of the generic name fo the variables. Python variables used in the code.

    Returns
    -------

    """

    if sensor_id not in odf.buoy_instrument:
        odf.add_buoy_instrument(sensor_id)

    key_map = [
        ('type', 'manufacturer'),
        ('model', 'model'),
        ('serial_number', 'serial_number'),
        ('description', 'description')
    ]

    for (odf_key, netcdf_key) in key_map:
        if netcdf_key in dataset.attrs:
            odf.buoy_instrument[sensor_id][odf_key] = dataset.attrs[netcdf_key]

    #odf.buoy_instrument[sensor_id]["inst_start_date_time"] = odf_time_format(dataset.time.values.min())
    #odf.buoy_instrument[sensor_id]["inst_end_date_time"] = odf_time_format(dataset.time.values.max())

    _make_adcp_buoy_instrument_comments(odf, sensor_id, dataset, platform_metadata)
    #_make_adcp_buoy_instrument_sensor_comments(odf, sensor_id, dataset, generic_variables_name) # TEST


def _make_adcp_buoy_instrument_comments(
        odf: Odf,
        sensor_id: str,
        dataset: xr.Dataset,
        platform_metadata: PlatformMetadata
):
    """

    BUOY_INSTRUMENT_HEADER
      .
      .
      BUOY_INSTRUMENT_COMMENTS= '',
      .
      .

    Note
    ----
    LagLength was removed from the original ODF adcp format.
    """
    configuration = "CONFIGURATION_01"
    buoy_instrument_comments = []
    key_map = [
        ("Mode", "orientation"),
        ("Ping_Type", "ping_type"),
        ("Frequency", "frequency"),
        ("Firmware_Version", "firmware_version"),
        ("Ping_per_Ensemble", "ping_per_ensemble"),
        ("Ensemble_Length_s", "delta_t_sec"),
        ("ADCP_Depth_m", "sensor_depth"),
        ("Distance_ADCP_to_First_Bin_Center_m", "bin1dist"),
        ("Bin_Size_m", "bin_size"),
        ("Blank_m", "blank"),
        ("Transmit_Pulse_Length_m", "transmit_pulse_length_m")
    ]

    for odf_key, netcdf_key in key_map:
        if netcdf_key in dataset.attrs:
            buoy_instrument_comments.append((odf_key, dataset.attrs[netcdf_key]))

    if "ping_per_ensemble" in dataset.attrs and "delta_t_sec" in dataset.attrs:
        if dataset.attrs["ping_per_ensemble"] and dataset.attrs["delta_t_sec"]:
            ping_interval_s = dataset.attrs["ping_per_ensemble"] /  dataset.attrs["delta_t_sec"]
            buoy_instrument_comments.append(("Ping_Interval_s", round(ping_interval_s, 2)))

    if "magnetic_declination" in dataset.attrs and "magnetic_declination_units" in dataset.attrs:
        magnetic_declination = f"{dataset.attrs['magnetic_declination']} {dataset.attrs['magnetic_declination_units']}"

        buoy_instrument_comments.append(("Magnetic_Declination", magnetic_declination))

    buoy_instrument_comments += [
        ("Bin_Count", len(dataset.depth)),
        ("Comments", platform_metadata.sensors[sensor_id].comments or "")
    ]

    odf.buoy_instrument[sensor_id]["buoy_instrument_comments"] = []
    for (key, value) in buoy_instrument_comments:
        odf.buoy_instrument[sensor_id]["buoy_instrument_comments"].append(
            _build_comments_string([configuration, key], value)
        )


def _make_adcp_buoy_instrument_sensor_comments(odf: Odf, sensor_id: str, dataset: xr.Dataset, generic_variables_name: List[str]):
    """
    Parameters
    ----------
    odf

    sensor_id

    dataset

    generic_variables_name :
      List of the generic name fo the variables. Python variables used in the code.

    Returns
    -------
    """
    dataset_attrs_map = {
        'Manufacturer': 'manufacturer',
        'Depth': 'sensor_depth',
        'Serial_Number': 'serial_number'}

    adcp_sensors_comments = []

    for var, sensor_comment in ADCP_SENSORS_COMMENTS.items():
        if var in generic_variables_name:
            sensor_name = sensor_comment['sensor']

            for comment_key, comment_value in sensor_comment['comments'].items():
                adcp_sensors_comments.append(([sensor_name, comment_key], comment_value))

            for odf_key, nc_key in dataset_attrs_map.items():
                if nc_key in dataset.attrs:
                    if dataset.attrs[nc_key] is not None:
                        adcp_sensors_comments.append(([sensor_name, odf_key], str(dataset.attrs[nc_key])))

    for comments in adcp_sensors_comments:
        odf.buoy_instrument[sensor_id]["sensors"].append(
            _build_comments_string(comments[0], comments[1])
            )


def _make_other_buoy_instrument_header(odf: Odf, platform_metadata: PlatformMetadata):
    """

    Parameters
    ----------
    odf
    platform_metadata

    Returns
    -------
    """
    configuration = "CONFIGURATION_01"

    for sensor_id, sensor in platform_metadata.sensors.items():
        if sensor_id in ['platform', 'buoy_specs']:
            continue
        odf.add_buoy_instrument(sensor_id)
        odf.buoy_instrument[sensor_id]['type'] = sensor.manufacturer
        odf.buoy_instrument[sensor_id]['model'] = sensor.model
        odf.buoy_instrument[sensor_id]['serial_number'] = sensor.serial_number
        odf.buoy_instrument[sensor_id]['description'] = sensor.description
        comments = {
            "Firmware_Version": sensor.firmware_version,
            "depth_m": sensor.sensor_depth,
            "Comments": sensor.comments
        }

        for key, value in comments.items():
            odf.buoy_instrument[sensor_id]["buoy_instrument_comments"].append(
                configuration + "." + key + ": " + str(value)
            )


def _add_buoy_instrument_headers(
        odf: Odf,
        platform_metadata: PlatformMetadata
):
    """
    FIXME test
    Uses the data from the platform metadata
    """
    for sensor_id, sensor_metadata in platform_metadata.sensors.items():
        _make_buoy_instrument_header(
            odf=odf,
            sensor_id=sensor_id,
            sensor_metadata=sensor_metadata
        )

    # Do only those in the sensors_id list:
    # for sensor_id, sensor_type in sensors_id.items():
    #     if sensor_type in sensors_to_parameters_map:
    #         parameters = sensors_to_parameters_map[sensor_type]
    #
    #         _make_buoy_instrument_header(
    #             odf=odf,
    #             sensor_id=sensor_id,
    #             parameters=parameters,
    #             platform_metadata=platform_metadata
    #         )


def _make_buoy_instrument_header(
        odf: Odf,
        sensor_id: str,
        # parameters: List[str],
        # platform_metadata: PlatformMetadata
        sensor_metadata: Sensor
):
    """
    FIXME test
    Uses the data from the platform metadata
    """

    odf.add_buoy_instrument(sensor_id)

    odf.buoy_instrument[sensor_id]['inst_start_date_time'] = odf.event['start_date_time']
    odf.buoy_instrument[sensor_id]['inst_end_date_time'] = odf.event['end_date_time']

    #if sensor_id in platform_metadata.sensors:
    #sensor_metadata = platform_metadata.sensors[sensor_id]

    odf.buoy_instrument[sensor_id]['type'] = sensor_metadata.manufacturer
    odf.buoy_instrument[sensor_id]['model'] = sensor_metadata.model
    odf.buoy_instrument[sensor_id]['serial_number'] = sensor_metadata.serial_number
    odf.buoy_instrument[sensor_id]['description'] = sensor_metadata.description

    _make_buoy_instrument_comments(odf, sensor_id, sensor_metadata)

    for parameter, parameter_metadata in sensor_metadata.parameters.items():
        #if parameter in parameters:
        _make_parameter_sensor_comments(parameter, odf, sensor_id, sensor_metadata)


def _make_buoy_instrument_comments(odf: Odf, sensor_id: str, sensor_metadata: Sensor):
    """
    TODO TEST but this should work
    """
    buoy_instruments_comments = [
        (["Firmware_Version"], sensor_metadata.firmware_version or ""),
        (["Comments"], sensor_metadata.comments or "")
    ]

    if sensor_metadata.sensor_depth is not None:
        buoy_instruments_comments.append((["Depth_m"], sensor_metadata.sensor_depth))

    if sensor_metadata.sensor_height is not None:
        buoy_instruments_comments.append((["Height_m"], sensor_metadata.sensor_depth))

    for (key, value) in buoy_instruments_comments:
        odf.buoy_instrument[sensor_id]["buoy_instrument_comments"].append(
            _build_comments_string(["CONFIGURATION_01"] + key, value)
        )


def _make_parameter_sensor_comments(parameter: str, odf: Odf, sensor_id: str, sensor_metadata: Sensor):
    """
    TODO TEST but this should work
    """
    parameter_name = PARAMETERS_METADATA[parameter]['name']

    prefixes = ['SENSOR_' + parameter_name.upper() + "_01"]

    sensor_comments = [
        ("CODE", PARAMETERS_METADATA[parameter]['code']),
        ("Name", parameter_name),
        ("Manufacturer", odf.buoy_instrument[sensor_id]['type']),
        ("Model", odf.buoy_instrument[sensor_id]['model']),
        ("Serial_number", odf.buoy_instrument[sensor_id]['serial_number']),
        ("Description", sensor_metadata[[parameter_name]]['descriptions']),
        ("Start_date", odf.buoy_instrument[sensor_id]['inst_start_date_time']),
        ("End_date", odf.buoy_instrument[sensor_id]['inst_end_date_time']),
        ("Comments", sensor_metadata[parameter_name]['comments'])
    ]

    for (key, value) in sensor_comments:
        odf.buoy_instrument[sensor_id]["sensors"].append(
            _build_comments_string(prefixes + [key], value)
        )

    calibration = sensor_metadata.parameters[parameter].calibration

    calibration_comments = {
        'date': odf_time_format(calibration.date) if calibration.date else "",
        'number_of_coefficients': calibration.number_of_coefficients or "",
        'coefficients': calibration.coefficients or "",
        'calibration_equation': calibration.calibration_equation or "",
        'calibration_units': calibration.calibration_units or "",
        'archiving_units': calibration.archiving_units or "",
        'conversion_factor': calibration.conversion_factor or "",
        'comments': calibration.comments or "",
    }

    for key, value in calibration_comments.items():
        odf.buoy_instrument[sensor_id]["sensors"].append(
            _build_comments_string(prefixes + ["CALIBRATION_01", key], value)
        )


def _build_comments_string(keys: List, value: Union[int, float, str]):
    """Build the comments string

    >>> ".".join(keys) + f": {value}"
    """
    return ".".join(keys) + f": {value}"


def _make_quality_header(odf: Odf, dataset):
    """
    """
    comments = dataset.attrs['quality_comments'].strip("\n").split("\n")
    time_stamp = _find_section_timestamp(comments.pop())

    odf.quality["quality_date"] = odf_time_format(datetime.now())
    if time_stamp:
        odf.quality["quality_date"] = odf_time_format(time_stamp)

    odf.quality["quality_tests"] = comments
    keys = ['flag_reference', 'flag_values', 'flag_meanings']
    for key in keys:
        odf.quality["quality_comments"].append(key + ': ' + str(dataset.attrs[key]))


def _make_history_header(odf, dataset):
    """Make one or more history_header.
    1 - Default process comments is added with a Timestamp (datetime.now()).
    2 - Looks for log section `[Loading adcp data], [Data transformation]` in
        dataset.attrs['history'] and add the log messages that follow.
    3 - New history_header are made for each TimeStamp found with the log section.
    """
    processing = ["Data processed by Magtogoek Processing Software. More at " + REPOSITORY_ADDRESS]
    creation_date = odf_time_format(datetime.now())

    iter_logbook = iter(re.split(r"(\[.*])", dataset.attrs["history"]))
    for log_entry in iter_logbook:
        if log_entry in ["[Loading adcp data]", "[Data transformation]"]:
            logs = next(iter_logbook).strip("\n").split("\n")
            time_stamp = _find_section_timestamp(logs[0])
            if time_stamp is not None:
                del logs[0]
                odf.add_history({"creation_date": creation_date, "process": processing})
                creation_date = odf_time_format(pd.Timestamp(time_stamp))
                processing = []
            processing += logs
    odf.add_history({"creation_date": creation_date, "process": processing})


def _make_parameter_headers(odf, dataset, variables: List[str], bodc_name=False):
    """
    Parameters
    ----------
    odf:
    dataset:
        Dataset to which add the navigation data.
    variables:
       variables to put in the ODF.
    bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    Notes
    -----
    The variable order in the ODF will be the same as in the variables list parameter.
    """

    parameters_metadata = {}
    parameters = []
    qc_parameters = []

    for var in variables:
        if bodc_name is True and not var in ('time', 'depth'):
            dataset_variable_name = dataset.attrs["P01_CODES_MAP"][var]
        else:
            dataset_variable_name = var

        if dataset_variable_name in dataset.variables:
            parameters.append(dataset_variable_name)
            parameters_metadata[dataset_variable_name] = PARAMETERS_METADATA[var]
            if var in QC_PARAMETERS and dataset_variable_name + '_QC' in dataset.variables:
                qc_parameters.append(dataset_variable_name + '_QC')

    dims = ['time', 'depth'] if 'depth' in variables else ['time']
    data = dataset[parameters + qc_parameters].to_dataframe().reset_index().sort_values(dims)

    qc_increment = 1
    for var in parameters:
        add_qc_var = var + '_QC' in qc_parameters

        items = {"depth": dataset.attrs["sensor_depth"],
                 'magnetic_variation': dataset.attrs["magnetic_declination"],
                 "type": ODF_PARAMETERS_TYPES[str(dataset[var].data.dtype)]}
        items.update(parameters_metadata[var])

        qc_mask = data[var + '_QC'].values <= 2 if add_qc_var is True else None

        null_value = items["null_value"] if "null_value" in items else dataset[var].encoding["_FillValue"]

        odf.add_parameter(code=items["code"],
                          data=data[var].values,
                          null_value=null_value,
                          items=items,
                          qc_mask=qc_mask)

        if add_qc_var is True:
            qc_items = {
                "code": "QQQQ_" + str(qc_increment).zfill(2),
                "name": "Quality flag: " + items['name'],
                "units": "none",
                "print_field_width": 1,
                "print_decimal_places": 0,
                "null_value": 9,
                "type": ODF_PARAMETERS_TYPES[str(dataset[var + '_QC'].data.dtype)]
            }
            odf.add_parameter(code=qc_items["code"],
                              data=data[var + '_QC'].values,
                              null_value=9,
                              items=qc_items,
                              qc_mask=None)
            qc_increment += 1


def _find_section_timestamp(s: str) -> str:
    r""" String of Section - Timestamp

    regex : ([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})'
    """
    regex = r"([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
    match = re.findall(regex, s)
    if match:
        return match[0]
    return None


if __name__ == "__main__":
    #    from magtogoek.adcp.process import _get_config, _load_platform
    #    from magtogoek.configfile import load_configfile

    _nc_file = "../../test/files/iml6_2017_wh.nc"
    _platform_files = "../../test/files/iml_platforms.json"
    _config_file = "../../test/files/adcp_iml6_2017.ini"

    #    _dataset = xr.open_dataset(_nc_file)
    #    _params, _global_attrs = _get_config(load_configfile(_config_file))
    #    _params["platform_file"] = _platform_files
    #    _sensor_metadata = _load_platform(_params)

    _p01_to_generic_name = {
        "u": "LCEWAP01",
        "u_QC": "LCEWAP01_QC",
        "v": "LCNSAP01",
        "v_QC": "LCNSAP01_QC",
        "w": "LRZAAP01",
        "w_QC": "LRZAAP01_QC",
        "e": "LERRAP01",
    }

#    _odf = make_odf(_dataset, _sensor_metadata, _global_attrs, _p01_to_generic_name)
